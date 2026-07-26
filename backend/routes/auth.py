from datetime import datetime

from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
)

from extensions import db
from models import User, ActivityLog

auth_bp = Blueprint("auth", __name__)


def log_activity(user_id, activity, ip):
    log = ActivityLog(
        user_id=user_id,
        activity=activity,
        ip_address=ip
    )

    db.session.add(log)
    db.session.commit()


# -------------------------------------------------
# Register
# -------------------------------------------------

@auth_bp.route("/register", methods=["POST"])
def register():

    data = request.get_json()

    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    username = data.get("username", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not username or not email or not password:
        return jsonify({
            "error": "All fields are required"
        }), 400

    if User.query.filter_by(username=username).first():
        return jsonify({
            "error": "Username already exists"
        }), 409

    if User.query.filter_by(email=email).first():
        return jsonify({
            "error": "Email already exists"
        }), 409

    user = User(
        username=username,
        email=email
    )

    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    log_activity(
        user.id,
        "Account Created",
        request.remote_addr
    )

    return jsonify({
        "message": "Registration successful"
    }), 201


# -------------------------------------------------
# Login
# -------------------------------------------------

@auth_bp.route("/login", methods=["POST"])
def login():

    data = request.get_json()

    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify({
            "error": "Invalid credentials"
        }), 401

    if not user.check_password(password):
        return jsonify({
            "error": "Invalid credentials"
        }), 401

    user.last_login = datetime.utcnow()

    db.session.commit()

    access = create_access_token(identity=str(user.id))
    refresh = create_refresh_token(identity=str(user.id))

    log_activity(
        user.id,
        "User Logged In",
        request.remote_addr
    )

    return jsonify({
        "access_token": access,
        "refresh_token": refresh,
        "user": user.to_dict()
    })


# -------------------------------------------------
# Current User
# -------------------------------------------------

@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():

    uid = int(get_jwt_identity())

    user = User.query.get(uid)

    if not user:
        return jsonify({
            "error": "User not found"
        }), 404

    return jsonify(user.to_dict())


# -------------------------------------------------
# Refresh Token
# -------------------------------------------------

@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():

    uid = get_jwt_identity()

    access = create_access_token(identity=uid)

    return jsonify({
        "access_token": access
    })


# -------------------------------------------------
# Logout
# -------------------------------------------------

@auth_bp.route("/logout", methods=["POST"])
@jwt_required()
def logout():

    uid = int(get_jwt_identity())

    log_activity(
        uid,
        "User Logged Out",
        request.remote_addr
    )

    return jsonify({
        "message": "Logout successful"
    })