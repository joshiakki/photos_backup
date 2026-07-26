import uuid

from flask import Blueprint, jsonify, request

from flask_jwt_extended import (
    jwt_required,
    get_jwt_identity
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from extensions import db

from models import User

from utils.storage import (
    save_uploaded_file,
    delete_file
)

from config import Config


users_bp = Blueprint(
    "users",
    __name__
)


# ---------------------------------------------------------
# Get Profile
# ---------------------------------------------------------

@users_bp.route(
    "/profile",
    methods=["GET"]
)
@jwt_required()
def get_profile():

    user_id = uuid.UUID(
        get_jwt_identity()
    )

    user = db.session.get(
        User,
        user_id
    )

    if not user:

        return jsonify({

            "message": "User not found"

        }), 404


    return jsonify({

        "user": user.to_dict()

    })


# ---------------------------------------------------------
# Update Profile
# ---------------------------------------------------------

@users_bp.route(
    "/profile",
    methods=["PUT"]
)
@jwt_required()
def update_profile():

    user_id = uuid.UUID(
        get_jwt_identity()
    )

    user = db.session.get(
        User,
        user_id
    )

    if not user:

        return jsonify({

            "message": "User not found"

        }), 404


    data = request.get_json()


    username = data.get(
        "username"
    )


    if username:

        user.username = username.strip()


    db.session.commit()


    return jsonify({

        "message": "Profile updated",

        "user": user.to_dict()

    })


# ---------------------------------------------------------
# Change Password
# ---------------------------------------------------------

@users_bp.route(
    "/change-password",
    methods=["POST"]
)
@jwt_required()
def change_password():

    user_id = uuid.UUID(
        get_jwt_identity()
    )

    user = db.session.get(
        User,
        user_id
    )


    if not user:

        return jsonify({

            "message": "User not found"

        }), 404


    data = request.get_json()


    old_password = data.get(
        "old_password"
    )

    new_password = data.get(
        "new_password"
    )


    if not check_password_hash(

        user.password_hash,

        old_password

    ):

        return jsonify({

            "message": "Old password incorrect"

        }), 401


    user.password_hash = generate_password_hash(

        new_password

    )


    db.session.commit()


    return jsonify({

        "message": "Password changed successfully"

    })


# ---------------------------------------------------------
# Upload Profile Picture
# ---------------------------------------------------------

@users_bp.route(
    "/profile-picture",
    methods=["POST"]
)
@jwt_required()
def upload_profile_picture():

    user_id = uuid.UUID(
        get_jwt_identity()
    )


    user = db.session.get(
        User,
        user_id
    )


    if not user:

        return jsonify({

            "message": "User not found"

        }), 404


    if "file" not in request.files:

        return jsonify({

            "message": "No image uploaded"

        }),400


    file = request.files["file"]


    if user.profile_picture:

        delete_file(

            user.profile_picture

        )


    Config.create_user_directories(

        str(user.id)

    )


    filename = (
        uuid.uuid4().hex
        +
        ".jpg"
    )


    path = (

        Config.get_profile_directory(

            str(user.id)

        )
        +
        "/"
        +
        filename

    )


    file.save(path)


    user.profile_picture = path


    db.session.commit()


    return jsonify({

        "message": "Profile picture updated",

        "profile_picture": path

    })