from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

from extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(
        db.String(50),
        unique=True,
        nullable=False,
        index=True
    )

    email = db.Column(
        db.String(120),
        unique=True,
        nullable=False,
        index=True
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    profile_picture = db.Column(
        db.String(255),
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    last_login = db.Column(
        db.DateTime,
        nullable=True
    )

    is_active = db.Column(
        db.Boolean,
        default=True
    )

    media = db.relationship(
        "Media",
        backref="owner",
        lazy=True,
        cascade="all, delete-orphan"
    )

    logs = db.relationship(
        "ActivityLog",
        backref="user",
        lazy=True,
        cascade="all, delete-orphan"
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(
            self.password_hash,
            password
        )

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "profile_picture": self.profile_picture,
            "created_at": self.created_at.isoformat(),
            "last_login": (
                self.last_login.isoformat()
                if self.last_login
                else None
            )
        }


class Media(db.Model):
    __tablename__ = "media"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    original_filename = db.Column(
        db.String(255),
        nullable=False
    )

    stored_filename = db.Column(
        db.String(255),
        nullable=False,
        unique=True
    )

    media_type = db.Column(
        db.String(20),
        nullable=False
    )

    file_size = db.Column(
        db.BigInteger,
        nullable=False
    )

    mime_type = db.Column(
        db.String(100),
        nullable=False
    )

    file_path = db.Column(
        db.String(255),
        nullable=False
    )

    uploaded_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    is_deleted = db.Column(
        db.Boolean,
        default=False
    )

    def to_dict(self):
        return {
            "id": self.id,
            "filename": self.original_filename,
            "stored_filename": self.stored_filename,
            "media_type": self.media_type,
            "file_size": self.file_size,
            "mime_type": self.mime_type,
            "uploaded_at": self.uploaded_at.isoformat()
        }


class ActivityLog(db.Model):
    __tablename__ = "activity_logs"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    activity = db.Column(
        db.String(255),
        nullable=False
    )

    ip_address = db.Column(
        db.String(100)
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    def to_dict(self):
        return {
            "activity": self.activity,
            "ip_address": self.ip_address,
            "created_at": self.created_at.isoformat()
        }