import click
from flask import Flask, jsonify, render_template, request

from config import Config
from extensions import db, init_redis, jwt, limiter, login_manager
from models import User


def create_app(config_class=Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    # --- extensions ---
    db.init_app(app)
    login_manager.init_app(app)
    jwt.init_app(app)

    login_manager.login_view = "web.login"
    login_manager.login_message = "Please log in to continue."
    login_manager.login_message_category = "warning"

    @login_manager.user_loader
    def load_user(user_id: str):
        return db.session.get(User, int(user_id))

    # --- redis + rate limiter ---
    redis_ok = init_redis(app)
    app.config["RATELIMIT_STORAGE_URI"] = (
        app.config["REDIS_URL"] if redis_ok else "memory://"
    )
    limiter.init_app(app)

    # --- blueprints ---
    from blueprints.api_auth import bp as api_auth_bp
    from blueprints.api_weather import bp as api_weather_bp
    from blueprints.web import bp as web_bp

    app.register_blueprint(api_auth_bp)
    app.register_blueprint(api_weather_bp)
    app.register_blueprint(web_bp)

    # --- JWT error handlers (JSON) ---
    @jwt.unauthorized_loader
    def missing_token(reason):
        return jsonify({"error": "Authorization required.", "detail": reason}), 401

    @jwt.invalid_token_loader
    def invalid_token(reason):
        return jsonify({"error": "Invalid token.", "detail": reason}), 422

    @jwt.expired_token_loader
    def expired_token(jwt_header, jwt_payload):
        return jsonify({"error": "Token has expired."}), 401

    @jwt.revoked_token_loader
    def revoked_token(jwt_header, jwt_payload):
        return jsonify({"error": "Token has been revoked."}), 401

    # --- HTTP error handlers ---
    def _wants_json() -> bool:
        return (
            request.path.startswith("/api")
            or request.path.startswith("/Weather")
            or request.accept_mimetypes.best == "application/json"
        )

    @app.errorhandler(400)
    def bad_request(e):
        if _wants_json():
            return jsonify({"error": "Bad request."}), 400
        return render_template("404.html"), 400

    @app.errorhandler(404)
    def not_found(e):
        if _wants_json():
            return jsonify({"error": "Resource not found."}), 404
        return render_template("404.html"), 404

    @app.errorhandler(429)
    def ratelimited(e):
        return jsonify({"error": "Rate limit exceeded.", "detail": str(e.description)}), 429

    @app.errorhandler(500)
    def server_error(e):
        db.session.rollback()
        if _wants_json():
            return jsonify({"error": "Internal server error."}), 500
        return render_template("500.html"), 500

    # --- CLI ---
    @app.cli.command("init-db")
    def init_db():
        """Create all database tables."""
        db.create_all()
        click.echo("Database initialised.")

    @app.cli.command("create-admin")
    @click.option("--username", prompt=True)
    @click.option("--email", prompt=True)
    @click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True)
    def create_admin(username, email, password):
        """Create an admin user."""
        if User.query.filter((User.username == username) | (User.email == email)).first():
            click.echo("User already exists.")
            return
        user = User(username=username, email=email.lower(), role="admin")
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        click.echo(f"Admin '{username}' created.")

    # --- tables ---
    if app.config.get("AUTO_CREATE_DB"):
        with app.app_context():
            db.create_all()

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)