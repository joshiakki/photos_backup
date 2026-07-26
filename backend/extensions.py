from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_cors import CORS

# ---------------------------------------------------------
# Database
# ---------------------------------------------------------

db = SQLAlchemy()

# ---------------------------------------------------------
# JWT Authentication
# ---------------------------------------------------------

jwt = JWTManager()

# ---------------------------------------------------------
# Database Migrations
# ---------------------------------------------------------

migrate = Migrate()

# ---------------------------------------------------------
# Cross-Origin Resource Sharing
# ---------------------------------------------------------

cors = CORS()


def init_extensions(app):
    """
    Initialize all Flask extensions.
    """

    # Database
    db.init_app(app)

    # JWT
    jwt.init_app(app)

    # Flask-Migrate
    migrate.init_app(app, db)

    # CORS
    cors.init_app(
        app,
        resources={
            r"/api/*": {
                "origins": "*"
            }
        },
        supports_credentials=True
    )