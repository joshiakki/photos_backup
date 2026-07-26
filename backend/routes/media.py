import uuid

from flask import Blueprint
from flask import jsonify
from flask import request
from flask import send_file

from flask_jwt_extended import (
    jwt_required,
    get_jwt_identity
)

from extensions import db

from models import (
    User,
    Media
)

from utils.storage import (
    save_uploaded_file,
    delete_file
)

media_bp = Blueprint(
    "media",
    __name__
)


# ---------------------------------------------------------
# Upload Media
# ---------------------------------------------------------

@media_bp.route(
    "/upload",
    methods=["POST"]
)
@jwt_required()
def upload():

    user_id = uuid.UUID(
        get_jwt_identity()
    )

    user = db.session.get(
        User,
        user_id
    )

    if user is None:

        return jsonify({

            "message": "User not found"

        }), 404

    if "file" not in request.files:

        return jsonify({

            "message": "No file uploaded"

        }), 400

    file = request.files["file"]

    if file.filename == "":

        return jsonify({

            "message": "No file selected"

        }), 400

    try:

        uploaded = save_uploaded_file(

            file,

            str(user.id)

        )

    except ValueError as e:

        return jsonify({

            "message": str(e)

        }), 400

    media = Media(

        user_id=user.id,

        original_filename=uploaded["original_filename"],

        stored_filename=uploaded["stored_filename"],

        media_type=uploaded["media_type"],

        mime_type=uploaded["mime_type"],

        file_size=uploaded["file_size"],

        file_path=uploaded["file_path"]

    )

    db.session.add(media)

    user.storage_used += uploaded["file_size"]

    db.session.commit()

    return jsonify({

        "message": "Upload Successful",

        "media": media.to_dict()

    }), 201


# ---------------------------------------------------------
# List Media
# ---------------------------------------------------------

@media_bp.route(
    "/list",
    methods=["GET"]
)
@jwt_required()
def list_media():

    user_id = uuid.UUID(
        get_jwt_identity()
    )

    media = Media.query.filter_by(

        user_id=user_id,

        is_deleted=False

    ).order_by(

        Media.uploaded_at.desc()

    ).all()

    return jsonify([

        item.to_dict()

        for item in media

    ])


# ---------------------------------------------------------
# Download Media
# ---------------------------------------------------------

@media_bp.route(
    "/download/<string:media_id>",
    methods=["GET"]
)
@jwt_required()
def download(media_id):

    uid = uuid.UUID(
        get_jwt_identity()
    )

    media = db.session.get(

        Media,

        uuid.UUID(media_id)

    )

    if media is None:

        return jsonify({

            "message": "Media not found"

        }), 404

    if media.user_id != uid:

        return jsonify({

            "message": "Access denied"

        }), 403

    return send_file(

        media.file_path,

        as_attachment=True,

        download_name=media.original_filename

    )


# ---------------------------------------------------------
# Delete Media
# ---------------------------------------------------------

@media_bp.route(
    "/delete/<string:media_id>",
    methods=["DELETE"]
)
@jwt_required()
def delete(media_id):

    uid = uuid.UUID(
        get_jwt_identity()
    )

    media = db.session.get(

        Media,

        uuid.UUID(media_id)

    )

    if media is None:

        return jsonify({

            "message": "Media not found"

        }), 404

    if media.user_id != uid:

        return jsonify({

            "message": "Unauthorized"

        }), 403

    delete_file(

        media.file_path

    )

    user = db.session.get(

        User,

        uid

    )

    if user:

        user.storage_used -= media.file_size

        if user.storage_used < 0:

            user.storage_used = 0

    db.session.delete(

        media

    )

    db.session.commit()

    return jsonify({

        "message": "Media deleted successfully"

    })


# ---------------------------------------------------------
# Storage Information
# ---------------------------------------------------------

@media_bp.route(
    "/storage",
    methods=["GET"]
)
@jwt_required()
def storage_info():

    uid = uuid.UUID(
        get_jwt_identity()
    )

    user = db.session.get(

        User,

        uid

    )

    return jsonify({

        "used": user.storage_used,

        "limit": user.storage_limit,

        "remaining": user.storage_limit - user.storage_used

    })