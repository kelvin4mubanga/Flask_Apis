"""Proxy weather endpoint + CRUD for saved locations."""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from extensions import db, limiter
from models import QueryLog, SavedLocation
from weather_service import WeatherServiceError, get_weather

bp = Blueprint("api_weather", __name__)


def _current_user_id() -> int:
    return int(get_jwt_identity())


def _weather_response():
    city = request.args.get("city", "")
    try:
        data = get_weather(city)
    except WeatherServiceError as exc:
        return jsonify({"error": exc.message}), exc.status_code

    log = QueryLog(
        user_id=_current_user_id(),
        city=data["location"]["name"],
        ip_address=request.remote_addr,
        cached=bool(data.get("cached")),
    )
    db.session.add(log)
    db.session.commit()

    return jsonify(data), 200


# ---------------------------------------------------------------------------
# THE endpoint
# ---------------------------------------------------------------------------
@bp.get("/Weather")
@limiter.limit("30 per minute")
@jwt_required()
def weather_proxy():
    """GET /Weather?city=kitwe"""
    return _weather_response()


@bp.get("/api/v1/weather")
@limiter.limit("30 per minute")
@jwt_required()
def weather_v1():
    """Alias for /Weather."""
    return _weather_response()


# ---------------------------------------------------------------------------
# CRUD: /api/v1/locations
# ---------------------------------------------------------------------------
@bp.get("/api/v1/locations")
@jwt_required()
def list_locations():
    items = (
        SavedLocation.query.filter_by(user_id=_current_user_id())
        .order_by(SavedLocation.created_at.desc())
        .all()
    )
    return jsonify({"count": len(items), "locations": [i.to_dict() for i in items]}), 200


@bp.post("/api/v1/locations")
@jwt_required()
@limiter.limit("30 per hour")
def create_location():
    payload = request.get_json(silent=True) or {}
    city = (payload.get("city") or "").strip()
    if not city:
        return jsonify({"error": "Field 'city' is required."}), 400

    user_id = _current_user_id()
    if SavedLocation.query.filter_by(user_id=user_id, city=city).first():
        return jsonify({"error": f"'{city}' is already saved."}), 409

    location = SavedLocation(
        user_id=user_id,
        city=city,
        country=(payload.get("country") or "").strip() or None,
        notes=(payload.get("notes") or "").strip() or None,
    )
    db.session.add(location)
    db.session.commit()
    return jsonify({"message": "Location saved.", "location": location.to_dict()}), 201


@bp.get("/api/v1/locations/<int:location_id>")
@jwt_required()
def get_location(location_id: int):
    location = SavedLocation.query.filter_by(
        id=location_id, user_id=_current_user_id()
    ).first()
    if not location:
        return jsonify({"error": "Location not found."}), 404
    return jsonify({"location": location.to_dict()}), 200


@bp.route("/api/v1/locations/<int:location_id>", methods=["PUT", "PATCH"])
@jwt_required()
def update_location(location_id: int):
    location = SavedLocation.query.filter_by(
        id=location_id, user_id=_current_user_id()
    ).first()
    if not location:
        return jsonify({"error": "Location not found."}), 404

    payload = request.get_json(silent=True) or {}

    if "city" in payload:
        city = (payload.get("city") or "").strip()
        if not city:
            return jsonify({"error": "Field 'city' cannot be empty."}), 400
        clash = SavedLocation.query.filter(
            SavedLocation.user_id == _current_user_id(),
            SavedLocation.city == city,
            SavedLocation.id != location.id,
        ).first()
        if clash:
            return jsonify({"error": f"'{city}' is already saved."}), 409
        location.city = city

    if "country" in payload:
        location.country = (payload.get("country") or "").strip() or None
    if "notes" in payload:
        location.notes = (payload.get("notes") or "").strip() or None

    db.session.commit()
    return jsonify({"message": "Location updated.", "location": location.to_dict()}), 200


@bp.delete("/api/v1/locations/<int:location_id>")
@jwt_required()
def delete_location(location_id: int):
    location = SavedLocation.query.filter_by(
        id=location_id, user_id=_current_user_id()
    ).first()
    if not location:
        return jsonify({"error": "Location not found."}), 404
    db.session.delete(location)
    db.session.commit()
    return jsonify({"message": "Location deleted."}), 200