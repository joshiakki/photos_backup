import os
import uuid
from utils.storage import get_user_directories

from flask import (
    Blueprint,
    jsonify,
    request,
    send_file,
    current_app
)

from flask_jwt_extended import (
    jwt_required,
    get_jwt_identity
)

from werkzeug.utils import secure_filename

from extensions import db
from models import Media

media_bp = Blueprint("media", __name__)


# ---------------------------------------------------------
# Helper
# ---------------------------------------------------------

def allowed_file(filename):

    if "." not in filename:
        return False

    extension = filename.rsplit(".", 1)[1].lower()

    if extension in current_app.config["ALLOWED_IMAGE_EXTENSIONS"]:
        return "image"

    if extension in current_app.config["ALLOWED_VIDEO_EXTENSIONS"]:
        return "video"

    return False


# ---------------------------------------------------------
# Upload
# ---------------------------------------------------------

@media_bp.route("/upload", methods=["POST"])
@jwt_required()
@media_bp.route("/upload", methods=["POST"])
@jwt_required()
def upload():

    uid = int(get_jwt_identity())

    if "file" not in request.files:
        return jsonify({
            "error": "No file uploaded"
        }), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({
            "error": "No file selected"
        }), 400

    media_type = allowed_file(file.filename)

    if not media_type:
        return jsonify({
            "error": "Unsupported file type"
        }), 400

    extension = file.filename.rsplit(".", 1)[1].lower()

    unique_name = f"{uuid.uuid4().hex}.{extension}"

    # -------------------------------------------------
    # Create user folders automatically
    # -------------------------------------------------

    folders = get_user_directories(uid)

    if media_type == "image":
        folder = folders["images"]
        relative_path = os.path.join(
            str(uid),
            "images",
            unique_name
        )
    else:
        folder = folders["videos"]
        relative_path = os.path.join(
            str(uid),
            "videos",
            unique_name
        )

    save_path = os.path.join(folder, unique_name)

    file.save(save_path)

    media = Media(
        user_id=uid,
        original_filename=secure_filename(file.filename),
        stored_filename=unique_name,
        media_type=media_type,
        file_size=os.path.getsize(save_path),
        mime_type=file.content_type,
        file_path=relative_path
    )

    db.session.add(media)
    db.session.commit()

    return jsonify({
        "message": "Upload successful",
        "media": media.to_dict()
    }), 201

# ---------------------------------------------------------
# List User Media
# ---------------------------------------------------------

@media_bp.route("/", methods=["GET"])
@jwt_required()
def list_media():

    uid = int(get_jwt_identity())

    media = Media.query.filter_by(
        user_id=uid,
        is_deleted=False
    ).order_by(
        Media.uploaded_at.desc()
    ).all()

    return jsonify([
        m.to_dict()
        for m in media
    ])


# ---------------------------------------------------------
# Download / View
# ---------------------------------------------------------

@media_bp.route("/<int:media_id>", methods=["GET"])
@jwt_required()
def get_media(media_id):

    uid = int(get_jwt_identity())

    media = Media.query.filter_by(
        id=media_id,
        user_id=uid,
        is_deleted=False
    ).first()

    if not media:
        return jsonify({
            "error": "Media not found"
        }), 404

    return send_file(
        media.file_path,
        mimetype=media.mime_type
    )


# ---------------------------------------------------------
# Delete
# ---------------------------------------------------------

@media_bp.route("/<int:media_id>", methods=["DELETE"])
@jwt_required()
def delete_media(media_id):

    uid = int(get_jwt_identity())

    media = Media.query.filter_by(
        id=media_id,
        user_id=uid,
        is_deleted=False
    ).first()

    if not media:
        return jsonify({
            "error": "Media not found"
        }), 404

    if os.path.exists(media.file_path):
        os.remove(media.file_path)

    media.is_deleted = True

    db.session.commit()

    return jsonify({
        "message": "Deleted successfully"
    })


# ---------------------------------------------------------
# Stream Video
# ---------------------------------------------------------

@media_bp.route("/stream/<int:media_id>", methods=["GET"])
@jwt_required()
def stream(media_id):

    uid = int(get_jwt_identity())

    media = Media.query.filter_by(
        id=media_id,
        user_id=uid,
        is_deleted=False
    ).first()

    if not media:
        return jsonify({
            "error": "Video not found"
        }), 404

    if media.media_type != "video":
        return jsonify({
            "error": "Requested media is not a video"
        }), 400

    return send_file(
        media.file_path,
        mimetype=media.mime_type
    )