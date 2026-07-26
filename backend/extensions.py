from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_cors import CORS

# SQLAlchemy Database
db = SQLAlchemy()

# JWT Authentication
jwt = JWTManager()

# Database Migration
migrate = Migrate()

# Cross-Origin Resource Sharing
cors = CORS()


def init_extensions(app):
    """
    Initialize all Flask extensions.
    """

    # Database
    db.init_app(app)

    # JWT
    jwt.init_app(app)

    # Database Migration
    migrate.init_app(app, db)

    # Enable CORS
    cors.init_app(
        app,
        resources={
            r"/api/*": {
                "origins": "*"
            }
        }
    )