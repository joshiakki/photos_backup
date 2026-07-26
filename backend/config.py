import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """
    Main Application Configuration
    """

    # ---------------------------------------------------------
    # Flask
    # ---------------------------------------------------------
    SECRET_KEY = os.getenv(
        "SECRET_KEY",
        "change-this-in-production"
    )

    # ---------------------------------------------------------
    # Database
    # ---------------------------------------------------------
    DB_USER = os.getenv("DB_USER", "mediauser")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "mediapassword")
    DB_HOST = os.getenv("DB_HOST", "mysql")
    DB_PORT = os.getenv("DB_PORT", "3306")
    DB_NAME = os.getenv("DB_NAME", "media_gallery")

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}"
        f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ---------------------------------------------------------
    # JWT
    # ---------------------------------------------------------
    JWT_SECRET_KEY = os.getenv(
        "JWT_SECRET_KEY",
        "change-this-jwt-secret"
    )

    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=2)

    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

    # ---------------------------------------------------------
    # Upload Settings
    # ---------------------------------------------------------
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))

    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")

    IMAGE_FOLDER = os.path.join(UPLOAD_FOLDER, "images")

    VIDEO_FOLDER = os.path.join(UPLOAD_FOLDER, "videos")

    PROFILE_FOLDER = os.path.join(UPLOAD_FOLDER, "profiles")

    # Maximum Upload Size (500 MB)
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024

    # ---------------------------------------------------------
    # Allowed Extensions
    # ---------------------------------------------------------
    ALLOWED_IMAGE_EXTENSIONS = {
        "jpg",
        "jpeg",
        "png",
        "gif",
        "bmp",
        "webp"
    }

    ALLOWED_VIDEO_EXTENSIONS = {
        "mp4",
        "mov",
        "avi",
        "mkv",
        "webm"
    }

    # ---------------------------------------------------------
    # Pagination
    # ---------------------------------------------------------
    MEDIA_PER_PAGE = 20

    # ---------------------------------------------------------
    # Logging
    # ---------------------------------------------------------
    LOG_LEVEL = "INFO"

    # ---------------------------------------------------------
    # CORS
    # ---------------------------------------------------------
    CORS_HEADERS = "Content-Type"

    # ---------------------------------------------------------
    # Cloudflare
    # ---------------------------------------------------------
    PREFERRED_URL_SCHEME = "https"

    # ---------------------------------------------------------
    # Ensure folders exist
    # ---------------------------------------------------------
    @staticmethod
    def create_directories():
        folders = [
            Config.UPLOAD_FOLDER,
            Config.IMAGE_FOLDER,
            Config.VIDEO_FOLDER,
            Config.PROFILE_FOLDER,
        ]

        for folder in folders:
            os.makedirs(folder, exist_ok=True)