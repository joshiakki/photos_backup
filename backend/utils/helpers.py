import os
import uuid
from flask import current_app


def generate_filename(extension):
    """
    Generate a unique filename.
    """
    return f"{uuid.uuid4().hex}.{extension}"


def get_file_size(path):
    """
    Return file size in bytes.
    """
    return os.path.getsize(path)


def build_absolute_path(relative_path):
    """
    Convert a stored relative path to an absolute path.
    """
    return os.path.join(
        current_app.config["UPLOAD_FOLDER"],
        relative_path
    )


def remove_file(path):
    """
    Delete a file if it exists.
    """
    if os.path.exists(path):
        os.remove(path)