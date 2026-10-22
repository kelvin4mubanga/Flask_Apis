"""Upstream weather proxy logic with Redis caching."""
import copy
import logging
from datetime import datetime, timezone

import requests
from flask import current_app

from extensions import get_redis

log = logging.getLogger(__name__)

WMO_WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow fall",
    73: "Moderate snow fall",
    75: "Heavy snow fall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


class WeatherServiceError(Exception):
    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


# --------------------------------------------------------------------------
# Redis cache helpers
# --------------------------------------------------------------------------
def _cache_get(key: str):
    client = get_redis()
    if not client:
        return None
    try:
        import json

        raw = client.get(key)
        return json.loads(raw) if raw else None
    except Exception as exc:  # pragma: no cover
        log.warning("Cache GET failed for %s: %s", key, exc)
        return None


def _cache_set(key: str, value, ttl: int) -> None:
    client = get_redis()
    if not client:
        return
    try:
        import json

        client.setex(key, ttl, json.dumps(value))
    except Exception as exc:  # pragma: no cover
        log.warning("Cache SET failed for %s: %s", key, exc)


def clear_weather_cache(city: str) -> int:
    """Delete cached entries for a city. Returns number of keys removed."""
    client = get_redis()
    if not client:
        return 0
    try:
        keys = list(client.scan_iter(match=f"weather:{city.strip().lower()}*"))
        return client.delete(*keys) if keys else 0
    except Exception:  # pragma: no cover
        return 0


# --------------------------------------------------------------------------
# Upstream calls
# --------------------------------------------------------------------------
def geocode_city(city: str) -> dict:
    city = city.strip()
    cache_key = f"geo:{city.lower()}"

    cached = _cache_get(cache_key)
    if cached:
        return cached

    try:
        resp = requests.get(
            current_app.config["GEOCODING_API_BASE"],
            params={"name": city, "count": 1, "language": "en", "format": "json"},
            timeout=current_app.config["HTTP_TIMEOUT"],
        )
        resp.raise_for_status()
        payload = resp.json()
    except requests.Timeout:
        raise WeatherServiceError("Upstream geocoding service timed out.", 504)
    except requests.RequestException as exc:
        log.error("Geocoding failed: %s", exc)
        raise WeatherServiceError("Upstream geocoding service unavailable.", 502)

    results = payload.get("results") or []
    if not results:
        raise WeatherServiceError(f"City '{city}' not found.", 404)

    top = results[0]
    location = {
        "name": top.get("name"),
        "country": top.get("country"),
        "country_code": top.get("country_code"),
        "admin1": top.get("admin1"),
        "latitude": top.get("latitude"),
        "longitude": top.get("longitude"),
        "timezone": top.get("timezone"),
        "population": top.get("population"),
    }

    _cache_set(cache_key, location, current_app.config["GEO_CACHE_TTL"])
    return location


def fetch_forecast(latitude: float, longitude: float) -> dict:
    try:
        resp = requests.get(
            current_app.config["WEATHER_API_BASE"],
            params={
                "latitude": latitude,
                "longitude": longitude,
                "current": (
                    "temperature_2m,relative_humidity_2m,apparent_temperature,"
                    "precipitation,weather_code,wind_speed_10m,wind_direction_10m"
                ),
                "daily": (
                    "weather_code,temperature_2m_max,temperature_2m_min,"
                    "precipitation_sum,sunrise,sunset"
                ),
                "timezone": "auto",
                "forecast_days": 7,
            },
            timeout=current_app.config["HTTP_TIMEOUT"],
        )
        resp.raise_for_status()
        return resp.json()
    except requests.Timeout:
        raise WeatherServiceError("Upstream weather service timed out.", 504)
    except requests.RequestException as exc:
        log.error("Forecast fetch failed: %s", exc)
        raise WeatherServiceError("Upstream weather service unavailable.", 502)


# --------------------------------------------------------------------------
# Public API
# --------------------------------------------------------------------------
def get_weather(city: str) -> dict:
    city = (city or "").strip()

    if not city:
        raise WeatherServiceError("Query parameter 'city' is required.", 400)
    if len(city) > 100:
        raise WeatherServiceError("City name is too long (max 100 chars).", 400)
    if not all(c.isalnum() or c in " -'.," for c in city):
        raise WeatherServiceError("City name contains invalid characters.", 400)

    cache_key = f"weather:{city.lower()}"
    cached = _cache_get(cache_key)
    if cached:
        result = copy.deepcopy(cached)
        result["cached"] = True
        return result

    location = geocode_city(city)
    forecast = fetch_forecast(location["latitude"], location["longitude"])

    current_raw = forecast.get("current", {})
    daily_raw = forecast.get("daily", {})

    current = {
        "time": current_raw.get("time"),
        "temperature_c": current_raw.get("temperature_2m"),
        "apparent_temperature_c": current_raw.get("apparent_temperature"),
        "humidity_pct": current_raw.get("relative_humidity_2m"),
        "precipitation_mm": current_raw.get("precipitation"),
        "wind_speed_kmh": current_raw.get("wind_speed_10m"),
        "wind_direction_deg": current_raw.get("wind_direction_10m"),
        "weather_code": current_raw.get("weather_code"),
        "condition": WMO_WEATHER_CODES.get(current_raw.get("weather_code"), "Unknown"),
    }

    daily = []
    dates = daily_raw.get("time", []) or []
    for i, day in enumerate(dates):
        code = (daily_raw.get("weather_code") or [None])[i]
        daily.append(
            {
                "date": day,
                "weather_code": code,
                "condition": WMO_WEATHER_CODES.get(code, "Unknown"),
                "temp_max_c": (daily_raw.get("temperature_2m_max") or [None])[i],
                "temp_min_c": (daily_raw.get("temperature_2m_min") or [None])[i],
                "precipitation_sum_mm": (daily_raw.get("precipitation_sum") or [None])[i],
                "sunrise": (daily_raw.get("sunrise") or [None])[i],
                "sunset": (daily_raw.get("sunset") or [None])[i],
            }
        )

    payload = {
        "source": "open-meteo",
        "cached": False,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "location": {
            "query": city,
            "name": location["name"],
            "country": location["country"],
            "country_code": location["country_code"],
            "admin1": location["admin1"],
            "latitude": location["latitude"],
            "longitude": location["longitude"],
            "timezone": location["timezone"],
        },
        "units": {"temperature": "°C", "wind_speed": "km/h", "precipitation": "mm"},
        "current": current,
        "daily": daily,
    }

    _cache_set(cache_key, payload, current_app.config["WEATHER_CACHE_TTL"])
    return payload