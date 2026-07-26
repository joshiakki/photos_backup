import os
import uuid

from flask import (
    Blueprint,
    jsonify,
    request,
    current_app
)

from flask_jwt_extended import (
    jwt_required,
    get_jwt_identity
)

from werkzeug.utils import secure_filename

from extensions import db
from models import User
from utils.storage import get_user_directories

users_bp = Blueprint("users", __name__)


# -------------------------------------------------
# Get Profile
# -------------------------------------------------

@users_bp.route("/profile", methods=["GET"])
@jwt_required()
def get_profile():

    uid = int(get_jwt_identity())

    user = User.query.get(uid)

    if not user:
        return jsonify({
            "error": "User not found"
        }), 404

    return jsonify(user.to_dict())


# -------------------------------------------------
# Update Profile
# -------------------------------------------------

@users_bp.route("/profile", methods=["PUT"])
@jwt_required()
def update_profile():

    uid = int(get_jwt_identity())

    user = User.query.get(uid)

    if not user:
        return jsonify({
            "error": "User not found"
        }), 404

    data = request.get_json()

    username = data.get("username", "").strip()

    if username:

        existing = User.query.filter(
            User.username == username,
            User.id != uid
        ).first()

        if existing:
            return jsonify({
                "error": "Username already exists"
            }), 409

        user.username = username

    db.session.commit()

    return jsonify({
        "message": "Profile updated",
        "user": user.to_dict()
    })


# -------------------------------------------------
# Upload Profile Picture
# -------------------------------------------------

@users_bp.route("/profile-picture", methods=["POST"])
@jwt_required()
def upload_profile_picture():

    uid = int(get_jwt_identity())

    user = User.query.get(uid)

    if not user:
        return jsonify({
            "error": "User not found"
        }), 404

    if "file" not in request.files:
        return jsonify({
            "error": "No file uploaded"
        }), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({
            "error": "No file selected"
        }), 400

    extension = file.filename.rsplit(".", 1)[1].lower()

    if extension not in current_app.config["ALLOWED_IMAGE_EXTENSIONS"]:
        return jsonify({
            "error": "Only image files are allowed"
        }), 400

    folders = get_user_directories(uid)

    unique_name = f"profile_{uuid.uuid4().hex}.{extension}"

    save_path = os.path.join(
        folders["profiles"],
        unique_name
    )

    file.save(save_path)

    user.profile_picture = os.path.join(
        str(uid),
        "profiles",
        unique_name
    )

    db.session.commit()

    return jsonify({
        "message": "Profile picture uploaded",
        "profile_picture": user.profile_picture
    })


# -------------------------------------------------
# Change Password
# -------------------------------------------------

@users_bp.route("/change-password", methods=["POST"])
@jwt_required()
def change_password():

    uid = int(get_jwt_identity())

    user = User.query.get(uid)

    if not user:
        return jsonify({
            "error": "User not found"
        }), 404

    data = request.get_json()

    current_password = data.get("current_password")
    new_password = data.get("new_password")

    if not user.check_password(current_password):
        return jsonify({
            "error": "Current password is incorrect"
        }), 400

    user.set_password(new_password)

    db.session.commit()

    return jsonify({
        "message": "Password changed successfully"
    })


# -------------------------------------------------
# Delete Account
# -------------------------------------------------

@users_bp.route("/delete-account", methods=["DELETE"])
@jwt_required()
def delete_account():

    uid = int(get_jwt_identity())

    user = User.query.get(uid)

    if not user:
        return jsonify({
            "error": "User not found"
        }), 404

    db.session.delete(user)

    db.session.commit()

    return jsonify({
        "message": "Account deleted successfully"
    })