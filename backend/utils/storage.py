import os
import uuid
from pathlib import Path
from werkzeug.utils import secure_filename

from config import Config


IMAGE_EXTENSIONS = Config.ALLOWED_IMAGE_EXTENSIONS
VIDEO_EXTENSIONS = Config.ALLOWED_VIDEO_EXTENSIONS


def get_media_type(filename):

    extension = filename.rsplit(".", 1)[1].lower()

    if extension in IMAGE_EXTENSIONS:
        return "image"

    if extension in VIDEO_EXTENSIONS:
        return "video"

    return None


def generate_filename(filename):

    extension = filename.rsplit(".", 1)[1].lower()

    return f"{uuid.uuid4().hex}.{extension}"


def ensure_user_directories(user_id):

    Config.create_user_directories(user_id)


def save_uploaded_file(file, user_id):

    media_type = get_media_type(file.filename)

    if media_type is None:
        raise ValueError("Unsupported file type")

    ensure_user_directories(user_id)

    filename = generate_filename(file.filename)

    if media_type == "image":

        directory = Config.get_image_directory(user_id)

    else:

        directory = Config.get_video_directory(user_id)

    save_path = os.path.join(directory, filename)

    file.save(save_path)

    return {

        "original_filename": secure_filename(file.filename),

        "stored_filename": filename,

        "media_type": media_type,

        "mime_type": file.content_type,

        "file_size": os.path.getsize(save_path),

        "file_path": save_path

    }


def delete_file(path):

    if os.path.exists(path):

        os.remove(path)


def file_exists(path):

    return os.path.exists(path)


def create_thumbnail_path(user_id, filename):

    return os.path.join(

        Config.get_thumbnail_directory(user_id),

        filename

    )