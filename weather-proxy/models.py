from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="user")
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    locations = db.relationship(
        "SavedLocation",
        backref="owner",
        cascade="all, delete-orphan",
        lazy="select",
    )
    queries = db.relationship(
        "QueryLog",
        backref="owner",
        cascade="all, delete-orphan",
        lazy="select",
    )

    # --- password helpers ---
    def set_password(self, raw_password: str) -> None:
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return check_password_hash(self.password_hash, raw_password)

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() + "Z",
        }

    def __repr__(self) -> str:
        return f"<User {self.username}>"


class SavedLocation(db.Model):
    """CRUD resource: a user's saved city."""

    __tablename__ = "saved_locations"
    __table_args__ = (
        db.UniqueConstraint("user_id", "city", name="uq_user_city"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    city = db.Column(db.String(120), nullable=False)
    country = db.Column(db.String(120), nullable=True)
    notes = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "city": self.city,
            "country": self.country,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() + "Z",
            "updated_at": self.updated_at.isoformat() + "Z",
        }

    def __repr__(self) -> str:
        return f"<SavedLocation {self.city}>"


class QueryLog(db.Model):
    """Audit trail of proxied weather calls."""

    __tablename__ = "query_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    city = db.Column(db.String(120), nullable=False)
    ip_address = db.Column(db.String(64), nullable=True)
    cached = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "city": self.city,
            "cached": self.cached,
            "created_at": self.created_at.isoformat() + "Z",
        }

    def __repr__(self) -> str:
        return f"<QueryLog {self.city}>"