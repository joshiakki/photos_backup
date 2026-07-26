from flask import Flask, jsonify
from werkzeug.middleware.proxy_fix import ProxyFix

from config import Config
from extensions import init_extensions

# Blueprints
from routes.auth import auth_bp
from routes.media import media_bp
from routes.users import users_bp


def create_app():
    app = Flask(__name__)

    # -----------------------------
    # Load Configuration
    # -----------------------------
    app.config.from_object(Config)

    # -----------------------------
    # Reverse Proxy Support
    # (Cloudflare / Nginx)
    # -----------------------------
    app.wsgi_app = ProxyFix(
        app.wsgi_app,
        x_for=1,
        x_proto=1,
        x_host=1,
        x_port=1,
        x_prefix=1
    )

    # -----------------------------
    # Create Required Directories
    # -----------------------------
    Config.create_directories()

    # -----------------------------
    # Initialize Extensions
    # -----------------------------
    init_extensions(app)

    # -----------------------------
    # Register Blueprints
    # -----------------------------
    app.register_blueprint(
        auth_bp,
        url_prefix="/api/auth"
    )

    app.register_blueprint(
        media_bp,
        url_prefix="/api/media"
    )

    app.register_blueprint(
        users_bp,
        url_prefix="/api/users"
    )

    # -----------------------------
    # Health Check
    # -----------------------------
    @app.route("/")
    def home():
        return jsonify({
            "application": "Photo Backup",
            "status": "running",
            "version": "1.0.0"
        })

    @app.route("/health")
    def health():
        return jsonify({
            "status": "healthy"
        })

    # -----------------------------
    # Error Handlers
    # -----------------------------
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            "success": False,
            "message": "Bad Request"
        }), 400

    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({
            "success": False,
            "message": "Unauthorized"
        }), 401

    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({
            "success": False,
            "message": "Forbidden"
        }), 403

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False,
            "message": "Resource Not Found"
        }), 404

    @app.errorhandler(413)
    def file_too_large(error):
        return jsonify({
            "success": False,
            "message": "File Too Large"
        }), 413

    @app.errorhandler(500)
    def internal_server_error(error):
        return jsonify({
            "success": False,
            "message": "Internal Server Error"
        }), 500

    return app


app = create_app()


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )