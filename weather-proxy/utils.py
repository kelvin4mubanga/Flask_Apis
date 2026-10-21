import re

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")


def validate_registration(data: dict):
    """Return (errors: dict, cleaned: dict)."""
    data = data or {}
    username = (data.get("username") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    errors = {}

    if not username:
        errors["username"] = "Username is required."
    elif not (3 <= len(username) <= 80):
        errors["username"] = "Username must be 3-80 characters."
    elif not re.match(r"^[A-Za-z0-9_.-]+$", username):
        errors["username"] = "Username may only contain letters, numbers, _ . -"

    if not email:
        errors["email"] = "Email is required."
    elif not EMAIL_RE.match(email):
        errors["email"] = "Email is not valid."

    if not password:
        errors["password"] = "Password is required."
    elif len(password) < 8:
        errors["password"] = "Password must be at least 8 characters."
    elif password.isdigit() or password.isalpha():
        errors["password"] = "Password must contain letters and numbers."

    return errors, {"username": username, "email": email, "password": password}


def validate_password(raw: str):
    errors = {}
    raw = raw or ""
    if len(raw) < 8:
        errors["new_password"] = "Password must be at least 8 characters."
    elif raw.isdigit() or raw.isalpha():
        errors["new_password"] = "Password must contain letters and numbers."
    return errors