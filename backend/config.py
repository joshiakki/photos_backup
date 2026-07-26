import os


class Config:


    SECRET_KEY = os.getenv(
        "SECRET_KEY",
        "default-secret-key"
    )


    JWT_SECRET_KEY = os.getenv(
        "JWT_SECRET_KEY",
        "default-jwt-secret"
    )


    # -----------------------------
    # MySQL Configuration
    # -----------------------------

    MYSQL_HOST = os.getenv(
        "MYSQL_HOST",
        "mysql"
    )

    MYSQL_PORT = os.getenv(
        "MYSQL_PORT",
        "3306"
    )

    MYSQL_DATABASE = os.getenv(
        "MYSQL_DATABASE",
        "media_gallery"
    )

    MYSQL_USER = os.getenv(
        "MYSQL_USER",
        "mediauser"
    )

    MYSQL_PASSWORD = os.getenv(
        "MYSQL_PASSWORD",
        "mediapassword"
    )


    # -----------------------------
    # SQLAlchemy Connection
    # -----------------------------

    SQLALCHEMY_DATABASE_URI = (
        "mysql+pymysql://"
        + MYSQL_USER
        + ":"
        + MYSQL_PASSWORD
        + "@"
        + MYSQL_HOST
        + ":"
        + MYSQL_PORT
        + "/"
        + MYSQL_DATABASE
    )


    SQLALCHEMY_TRACK_MODIFICATIONS = False


    # -----------------------------
    # Upload Storage
    # -----------------------------

    UPLOAD_FOLDER = os.getenv(
        "UPLOAD_FOLDER",
        "/app/uploads"
    )


    MAX_CONTENT_LENGTH = int(
        os.getenv(
            "MAX_UPLOAD_SIZE",
            5368709120
        )
    )


    @staticmethod
    def create_directories():

        os.makedirs(
            Config.UPLOAD_FOLDER,
            exist_ok=True
        )