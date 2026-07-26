import uuid
from datetime import datetime

from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.types import TypeDecorator

from extensions import db


# ---------------------------------------------------------
# UUID Type
# ---------------------------------------------------------

class GUID(TypeDecorator):
    """
    Store UUID as CHAR(36) in MySQL.
    """

    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):

        if value is None:
            return None

        if isinstance(value, uuid.UUID):
            return str(value)

        return str(uuid.UUID(value))

    def process_result_value(self, value, dialect):

        if value is None:
            return None

        return uuid.UUID(value)


# ---------------------------------------------------------
# User
# ---------------------------------------------------------

class User(db.Model):

    __tablename__ = "users"

    id = db.Column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4
    )

    username = db.Column(
        db.String(100),
        nullable=False
    )

    email = db.Column(
        db.String(255),
        unique=True,
        nullable=False,
        index=True
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    profile_picture = db.Column(
        db.String(500)
    )

    storage_used = db.Column(
        db.BigInteger,
        default=0
    )

    storage_limit = db.Column(
        db.BigInteger,
        default=100 * 1024 * 1024 * 1024  # 100 GB
    )

    is_active = db.Column(
        db.Boolean,
        default=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    media = db.relationship(
        "Media",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    refresh_tokens = db.relationship(
        "RefreshToken",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    login_history = db.relationship(
        "LoginHistory",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    def to_dict(self):

        return {

            "id": str(self.id),
            "username": self.username,
            "email": self.email,
            "profile_picture": self.profile_picture,
            "storage_used": self.storage_used,
            "storage_limit": self.storage_limit,
            "created_at": self.created_at.isoformat()

        }


# ---------------------------------------------------------
# Media
# ---------------------------------------------------------

class Media(db.Model):

    __tablename__ = "media"

    id = db.Column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4
    )

    user_id = db.Column(
        GUID(),
        db.ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    original_filename = db.Column(
        db.String(255),
        nullable=False
    )

    stored_filename = db.Column(
        db.String(255),
        nullable=False
    )

    file_path = db.Column(
        db.String(500),
        nullable=False
    )

    media_type = db.Column(
        db.String(20),
        nullable=False
    )

    mime_type = db.Column(
        db.String(100)
    )

    file_size = db.Column(
        db.BigInteger,
        nullable=False
    )

    width = db.Column(
        db.Integer
    )

    height = db.Column(
        db.Integer
    )

    duration = db.Column(
        db.Float
    )

    thumbnail_path = db.Column(
        db.String(500)
    )

    checksum = db.Column(
        db.String(64)
    )

    is_deleted = db.Column(
        db.Boolean,
        default=False
    )

    uploaded_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    user = db.relationship(
        "User",
        back_populates="media"
    )

    def to_dict(self):

        return {

            "id": str(self.id),
            "user_id": str(self.user_id),
            "filename": self.original_filename,
            "media_type": self.media_type,
            "size": self.file_size,
            "uploaded_at": self.uploaded_at.isoformat()

        }


# ---------------------------------------------------------
# Refresh Tokens
# ---------------------------------------------------------

class RefreshToken(db.Model):

    __tablename__ = "refresh_tokens"

    id = db.Column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4
    )

    user_id = db.Column(
        GUID(),
        db.ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    token = db.Column(
        db.Text,
        nullable=False
    )

    expires_at = db.Column(
        db.DateTime,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    revoked = db.Column(
        db.Boolean,
        default=False
    )

    user = db.relationship(
        "User",
        back_populates="refresh_tokens"
    )


# ---------------------------------------------------------
# Login History
# ---------------------------------------------------------

class LoginHistory(db.Model):

    __tablename__ = "login_history"

    id = db.Column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4
    )

    user_id = db.Column(
        GUID(),
        db.ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    ip_address = db.Column(
        db.String(100)
    )

    user_agent = db.Column(
        db.Text
    )

    login_time = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    successful = db.Column(
        db.Boolean,
        default=True
    )

    user = db.relationship(
        "User",
        back_populates="login_history"
    )