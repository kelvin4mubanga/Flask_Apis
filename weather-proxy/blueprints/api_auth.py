"""JSON authentication API: register, login, refresh, me, change-password."""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    jwt_required,
)

from extensions import db, limiter
from models import User
from utils import validate_password, validate_registration

bp = Blueprint("api_auth", __name__, url_prefix="/api/auth")


@bp.post("/register")
@limiter.limit("10 per hour")
def register():
    payload = request.get_json(silent=True) or {}
    errors, data = validate_registration(payload)
    if errors:
        return jsonify({"error": "Validation failed", "details": errors}), 400

    existing = User.query.filter(
        (User.username == data["username"]) | (User.email == data["email"])
    ).first()
    if existing:
        return jsonify({"error": "Username or email already registered."}), 409

    user = User(username=data["username"], email=data["email"])
    user.set_password(data["password"])
    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "User registered successfully.", "user": user.to_dict()}), 201


@bp.post("/login")
@limiter.limit("15 per minute")
def login():
    payload = request.get_json(silent=True) or {}
    identifier = (payload.get("username") or payload.get("email") or "").strip()
    password = payload.get("password") or ""

    if not identifier or not password:
        return jsonify({"error": "username/email and password are required."}), 400

    user = User.query.filter(
        (User.username == identifier) | (User.email == identifier.lower())
    ).first()

    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid credentials."}), 401

    if not user.is_active:
        return jsonify({"error": "Account is disabled."}), 403

    identity = str(user.id)
    access_token = create_access_token(identity=identity, additional_claims={"role": user.role})
    refresh_token = create_refresh_token(identity=identity)

    return jsonify(
        {
            "message": "Login successful.",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
            "user": user.to_dict(),
        }
    ), 200


@bp.post("/refresh")
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    user = db.session.get(User, int(identity))
    if not user or not user.is_active:
        return jsonify({"error": "User no longer valid."}), 401

    access_token = create_access_token(
        identity=identity, additional_claims={"role": user.role}
    )
    return jsonify({"access_token": access_token, "token_type": "Bearer"}), 200


@bp.get("/me")
@jwt_required()
def me():
    user = db.session.get(User, int(get_jwt_identity()))
    if not user:
        return jsonify({"error": "User not found."}), 404
    return jsonify({"user": user.to_dict()}), 200


@bp.post("/change-password")
@jwt_required()
@limiter.limit("5 per hour")
def change_password():
    user = db.session.get(User, int(get_jwt_identity()))
    if not user:
        return jsonify({"error": "User not found."}), 404

    payload = request.get_json(silent=True) or {}
    current_password = payload.get("current_password") or ""
    new_password = payload.get("new_password") or ""

    if not user.check_password(current_password):
        return jsonify({"error": "Current password is incorrect."}), 401

    errors = validate_password(new_password)
    if errors:
        return jsonify({"error": "Validation failed", "details": errors}), 400

    user.set_password(new_password)
    db.session.commit()
    return jsonify({"message": "Password updated successfully."}), 200


@bp.delete("/account")
@jwt_required()
def delete_account():
    user = db.session.get(User, int(get_jwt_identity()))
    if not user:
        return jsonify({"error": "User not found."}), 404
    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": "Account deleted."}), 200