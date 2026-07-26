import os
from flask import current_app


def get_user_directories(user_id):
    """
    Create (if needed) and return all directories for a user.
    """

    user_root = os.path.join(
        current_app.config["UPLOAD_FOLDER"],
        str(user_id)
    )

    image_dir = os.path.join(user_root, "images")
    video_dir = os.path.join(user_root, "videos")
    profile_dir = os.path.join(user_root, "profiles")

    os.makedirs(image_dir, exist_ok=True)
    os.makedirs(video_dir, exist_ok=True)
    os.makedirs(profile_dir, exist_ok=True)

    return {
        "root": user_root,
        "images": image_dir,
        "videos": video_dir,
        "profiles": profile_dir
    }