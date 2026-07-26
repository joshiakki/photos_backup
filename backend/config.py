import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:

    # ---------------------------------------------------------
    # Flask
    # ---------------------------------------------------------

    SECRET_KEY = os.getenv(
        "SECRET_KEY",
        "change-this-secret-key"
    )

    # ---------------------------------------------------------
    # Database
    # ---------------------------------------------------------

    DB_HOST = os.getenv("DB_HOST", "mysql")
    DB_PORT = os.getenv("DB_PORT", "3306")
    DB_NAME = os.getenv("DB_NAME", "media_gallery")
    DB_USER = os.getenv("DB_USER", "mediauser")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "mediapassword")

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

    JWT_ACCESS_TOKEN_EXPIRES = 3600          # 1 hour

    JWT_REFRESH_TOKEN_EXPIRES = 2592000      # 30 days

    # ---------------------------------------------------------
    # Upload Storage
    # ---------------------------------------------------------

    # Root upload directory
    # Docker volume will mount here

    UPLOAD_FOLDER = os.getenv(
        "UPLOAD_FOLDER",
        "/app/uploads"
    )

    PROFILE_FOLDER = "profiles"

    IMAGE_FOLDER = "images"

    VIDEO_FOLDER = "videos"

    THUMBNAIL_FOLDER = "thumbnails"

    # ---------------------------------------------------------
    # Upload Limits
    # ---------------------------------------------------------

    MAX_CONTENT_LENGTH = (
        5 * 1024 * 1024 * 1024
    )  # 5 GB

    # ---------------------------------------------------------
    # Allowed Extensions
    # ---------------------------------------------------------

    ALLOWED_IMAGE_EXTENSIONS = {

        "jpg",
        "jpeg",
        "png",
        "gif",
        "bmp",
        "webp",
        "heic"

    }

    ALLOWED_VIDEO_EXTENSIONS = {

        "mp4",
        "mov",
        "avi",
        "mkv",
        "webm",
        "m4v"

    }

    # ---------------------------------------------------------
    # User Folder Structure
    # ---------------------------------------------------------

    @staticmethod
    def get_user_directory(user_id):

        return os.path.join(

            Config.UPLOAD_FOLDER,

            str(user_id)

        )

    @staticmethod
    def get_profile_directory(user_id):

        return os.path.join(

            Config.get_user_directory(user_id),

            Config.PROFILE_FOLDER

        )

    @staticmethod
    def get_image_directory(user_id):

        return os.path.join(

            Config.get_user_directory(user_id),

            Config.IMAGE_FOLDER

        )

    @staticmethod
    def get_video_directory(user_id):

        return os.path.join(

            Config.get_user_directory(user_id),

            Config.VIDEO_FOLDER

        )

    @staticmethod
    def get_thumbnail_directory(user_id):

        return os.path.join(

            Config.get_user_directory(user_id),

            Config.THUMBNAIL_FOLDER

        )

    # ---------------------------------------------------------
    # Create Root Upload Directory
    # ---------------------------------------------------------

    @staticmethod
    def create_directories():

        os.makedirs(

            Config.UPLOAD_FOLDER,

            exist_ok=True

        )

    # ---------------------------------------------------------
    # Create User Folder Structure
    # ---------------------------------------------------------

    @staticmethod
    def create_user_directories(user_id):

        folders = [

            Config.get_profile_directory(user_id),

            Config.get_image_directory(user_id),

            Config.get_video_directory(user_id),

            Config.get_thumbnail_directory(user_id)

        ]

        for folder in folders:

            os.makedirs(

                folder,

                exist_ok=True

            )