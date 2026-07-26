from flask import current_app


def allowed_extension(filename):

    if "." not in filename:
        return False

    extension = filename.rsplit(".", 1)[1].lower()

    if extension in current_app.config["ALLOWED_IMAGE_EXTENSIONS"]:
        return "image"

    if extension in current_app.config["ALLOWED_VIDEO_EXTENSIONS"]:
        return "video"

    return False


def validate_upload(file):

    if file.filename == "":
        return False, "No file selected"

    media_type = allowed_extension(file.filename)

    if not media_type:
        return False, "Unsupported file type"

    return True, media_type