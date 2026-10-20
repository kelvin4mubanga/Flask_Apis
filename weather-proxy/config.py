import os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    # --- Core ---
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-me")

    # --- JWT ---
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret-change-me")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=int(os.getenv("JWT_ACCESS_MINUTES", "60")))
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=int(os.getenv("JWT_REFRESH_DAYS", "30")))
    JWT_TOKEN_LOCATION = ["headers"]

    # --- Database ---
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'weather.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    # --- Redis / Cache ---
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    WEATHER_CACHE_TTL = int(os.getenv("WEATHER_CACHE_TTL", "600"))
    GEO_CACHE_TTL = int(os.getenv("GEO_CACHE_TTL", "86400"))

    # --- Rate limiting ---
    RATELIMIT_STORAGE_URI = REDIS_URL
    RATELIMIT_STORAGE_URL = REDIS_URL  # backwards compat
    RATELIMIT_DEFAULT = os.getenv("RATELIMIT_DEFAULT", "200 per day;50 per hour")
    RATELIMIT_HEADERS_ENABLED = True
    RATELIMIT_ENABLED = os.getenv("RATELIMIT_ENABLED", "true").lower() == "true"

    # --- Upstream weather API (Open-Meteo: no API key required) ---
    GEOCODING_API_BASE = os.getenv(
        "GEOCODING_API_BASE", "https://geocoding-api.open-meteo.com/v1/search"
    )
    WEATHER_API_BASE = os.getenv(
        "WEATHER_API_BASE", "https://api.open-meteo.com/v1/forecast"
    )
    HTTP_TIMEOUT = int(os.getenv("HTTP_TIMEOUT", "10"))

    AUTO_CREATE_DB = os.getenv("AUTO_CREATE_DB", "true").lower() == "true"