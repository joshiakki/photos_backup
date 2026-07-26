import os

from flask import Flask, jsonify
from werkzeug.middleware.proxy_fix import ProxyFix

from config import Config
from extensions import init_extensions, db

# Import Blueprints (we will create these next)
from routes.auth import auth_bp
from routes.media import media_bp
from routes.users import users_bp


def create_app():
    app = Flask(__name__)

    # Load configuration
    app.config.from_object(Config)

    # Cloudflare / Reverse Proxy Support
    app.wsgi_app = ProxyFix(
        app.wsgi_app,
        x_for=1,
        x_proto=1,
        x_host=1,
        x_prefix=1
    )

    # Create upload directories
    Config.create_directories()

    # Initialize Flask extensions
    init_extensions(app)

    # Register Blueprints
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(media_bp, url_prefix="/api/media")
    app.register_blueprint(users_bp, url_prefix="/api/users")

    # -------------------------------------------------
    # Health Check
    # -------------------------------------------------
    @app.route("/")
    def home():
        return jsonify({
            "status": "running",
            "application": "Media Gallery",
            "version": "1.0"
        })

    @app.route("/health")
    def health():
        return jsonify({
            "status": "healthy"
        })

    # -------------------------------------------------
    # Error Handlers
    # -------------------------------------------------
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "error": "Resource not found"
        }), 404

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            "error": "Bad request"
        }), 400

    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({
            "error": "Unauthorized"
        }), 401

    @app.errorhandler(413)
    def file_too_large(error):
        return jsonify({
            "error": "File exceeds maximum upload size"
        }), 413

    @app.errorhandler(500)
    def server_error(error):
        db.session.rollback()

        return jsonify({
            "error": "Internal server error"
        }), 500

    return app


app = create_app()


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )