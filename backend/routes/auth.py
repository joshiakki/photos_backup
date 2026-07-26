from datetime import timedelta

from flask import Blueprint
from flask import jsonify
from flask import request

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from flask_jwt_extended import (
    create_access_token,
    create_refresh_token
)

from extensions import db
from models import User
from config import Config


auth_bp = Blueprint(
    "auth",
    __name__
)


# ----------------------------------------------------
# Register
# ----------------------------------------------------

@auth_bp.route(
    "/register",
    methods=["POST"]
)
def register():

    data = request.get_json()

    username = data.get("username", "").strip()

    email = data.get("email", "").lower().strip()

    password = data.get("password", "")

    if not username:

        return jsonify({
            "message": "Username required"
        }), 400

    if not email:

        return jsonify({
            "message": "Email required"
        }), 400

    if not password:

        return jsonify({
            "message": "Password required"
        }), 400

    existing = User.query.filter_by(
        email=email
    ).first()

    if existing:

        return jsonify({
            "message": "Email already exists"
        }), 409

    user = User(

        username=username,

        email=email,

        password_hash=generate_password_hash(
            password
        )

    )

    db.session.add(user)

    db.session.commit()

    Config.create_user_directories(
        user.id
    )

    return jsonify({

        "message": "Registration successful"

    }), 201


# ----------------------------------------------------
# Login
# ----------------------------------------------------

@auth_bp.route(
    "/login",
    methods=["POST"]
)
def login():

    data = request.get_json()

    email = data.get("email", "").lower()

    password = data.get("password", "")

    user = User.query.filter_by(
        email=email
    ).first()

    if user is None:

        return jsonify({

            "message": "Invalid credentials"

        }), 401

    if not check_password_hash(

        user.password_hash,

        password

    ):

        return jsonify({

            "message": "Invalid credentials"

        }), 401

    access_token = create_access_token(

        identity=str(user.id),

        expires_delta=timedelta(hours=1)

    )

    refresh_token = create_refresh_token(

        identity=str(user.id)

    )

    return jsonify({

        "access_token": access_token,

        "refresh_token": refresh_token,

        "user": user.to_dict()

    })


# ----------------------------------------------------
# Verify Token
# ----------------------------------------------------

from flask_jwt_extended import jwt_required
from flask_jwt_extended import get_jwt_identity


@auth_bp.route(
    "/me",
    methods=["GET"]
)
@jwt_required()
def me():

    uid = get_jwt_identity()

    user = User.query.get(uid)

    if not user:

        return jsonify({

            "message": "User not found"

        }), 404

    return jsonify(

        user.to_dict()

    )