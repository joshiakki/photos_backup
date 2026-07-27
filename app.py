"""
Photo/Video Backup Server
--------------------------
Receives camera photos/videos from an Android app and stores them on disk
(intended to be a bind-mounted external hard disk), with a SQLite ledger
to prevent duplicate uploads and support per-device auth tokens.

Run directly:      python app.py
Run in production:  gunicorn -w 2 -b 0.0.0.0:5000 app:app
"""

import os
import sqlite3
import hashlib
import secrets
import shutil
import uuid
from datetime import datetime, timezone
from flask import Flask, request, jsonify, g, render_template
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_requests

# ---------------------------------------------------------------------------
# Configuration (all overridable via environment variables / .env)
# ---------------------------------------------------------------------------
BACKUP_ROOT = os.environ.get("BACKUP_ROOT", "/data/backups")
DB_PATH = os.environ.get("DB_PATH", "/data/db/backup.db")
MAX_CONTENT_LENGTH_MB = int(os.environ.get("MAX_CONTENT_LENGTH_MB", "2048"))  # 2GB default, for large videos

# Bootstrap admin account, created automatically on first run if it doesn't exist yet.
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")  # required — see .env.example

# The OAuth "Web client" ID from Google Cloud Console. Used to verify Google ID tokens
# from BOTH the browser (Google Identity Services JS) and the Android app (Credential Manager
# with setServerClientId) — Android does not need its own separate client ID for this purpose.
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")

if not ADMIN_PASSWORD:
    raise RuntimeError(
        "ADMIN_PASSWORD environment variable is not set. "
        "Set it in your .env / docker-compose environment before starting the server."
    )

os.makedirs(BACKUP_ROOT, exist_ok=True)
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH_MB * 1024 * 1024


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id            TEXT PRIMARY KEY,
            username      TEXT NOT NULL UNIQUE,
            email         TEXT UNIQUE,
            password_hash TEXT,
            google_sub    TEXT UNIQUE,
            role          TEXT NOT NULL DEFAULT 'user',    -- 'admin' or 'user'
            status        TEXT NOT NULL DEFAULT 'pending', -- 'pending', 'approved', 'rejected'
            created_at    TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS api_tokens (
            token_hash   TEXT PRIMARY KEY,
            user_id      TEXT NOT NULL REFERENCES users(id),
            created_at   TEXT NOT NULL,
            last_seen_at TEXT
        );

        CREATE TABLE IF NOT EXISTS media (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id       TEXT NOT NULL REFERENCES users(id),
            sha256        TEXT NOT NULL,
            media_type    TEXT NOT NULL,
            original_name TEXT,
            captured_at   TEXT,
            stored_path   TEXT NOT NULL,
            size_bytes    INTEGER NOT NULL,
            uploaded_at   TEXT NOT NULL,
            UNIQUE(user_id, sha256)
        );

        CREATE INDEX IF NOT EXISTS idx_media_user ON media(user_id);
        CREATE INDEX IF NOT EXISTS idx_media_hash ON media(sha256);
        CREATE INDEX IF NOT EXISTS idx_tokens_user ON api_tokens(user_id);
        """
    )
    conn.commit()

    # Bootstrap the default admin account if no admin exists yet.
    existing_admin = conn.execute(
        "SELECT id FROM users WHERE role = 'admin' LIMIT 1"
    ).fetchone()
    if not existing_admin:
        conn.execute(
            """INSERT INTO users (id, username, password_hash, role, status, created_at)
               VALUES (?, ?, ?, 'admin', 'approved', ?)""",
            (
                str(uuid.uuid4()),
                ADMIN_USERNAME,
                generate_password_hash(ADMIN_PASSWORD),
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        conn.commit()
        print(f"[photobackup] Created default admin account: username='{ADMIN_USERNAME}'")

    conn.close()


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------
def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def issue_api_token(user_id: str) -> str:
    token = secrets.token_urlsafe(32)
    db = get_db()
    db.execute(
        "INSERT INTO api_tokens (token_hash, user_id, created_at) VALUES (?, ?, ?)",
        (hash_token(token), user_id, datetime.now(timezone.utc).isoformat()),
    )
    db.commit()
    return token


def authenticate_user():
    """Resolve the calling user from the Bearer token. Returns a users row or None."""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    token = auth[len("Bearer "):].strip()
    if not token:
        return None
    db = get_db()
    row = db.execute(
        """SELECT users.* FROM users
           JOIN api_tokens ON api_tokens.user_id = users.id
           WHERE api_tokens.token_hash = ?""",
        (hash_token(token),),
    ).fetchone()
    if row:
        db.execute(
            "UPDATE api_tokens SET last_seen_at = ? WHERE token_hash = ?",
            (datetime.now(timezone.utc).isoformat(), hash_token(token)),
        )
        db.commit()
    return row


def require_admin_user():
    """Returns the admin user row if the caller is an authenticated admin, else None."""
    user = authenticate_user()
    if user and user["role"] == "admin":
        return user
    return None


def public_user_dict(row):
    return {
        "id": row["id"],
        "username": row["username"],
        "email": row["email"],
        "role": row["role"],
        "status": row["status"],
        "created_at": row["created_at"],
    }


# ---------------------------------------------------------------------------
# Auth endpoints — registration, login, and Google Sign-In
# ---------------------------------------------------------------------------
@app.post("/api/auth/register")
def register():
    body = request.get_json(silent=True) or {}
    username = body.get("username", "").strip()
    password = body.get("password", "")
    email = body.get("email", "").strip() or None

    if not username or not password:
        return jsonify(error="'username' and 'password' are required"), 400
    if len(password) < 8:
        return jsonify(error="password must be at least 8 characters"), 400

    db = get_db()
    existing = db.execute("SELECT 1 FROM users WHERE username = ?", (username,)).fetchone()
    if existing:
        return jsonify(error="username already taken"), 409

    user_id = str(uuid.uuid4())
    try:
        db.execute(
            """INSERT INTO users (id, username, email, password_hash, role, status, created_at)
               VALUES (?, ?, ?, ?, 'user', 'pending', ?)""",
            (user_id, username, email, generate_password_hash(password), datetime.now(timezone.utc).isoformat()),
        )
        db.commit()
    except sqlite3.IntegrityError:
        return jsonify(error="username or email already in use"), 409

    return jsonify(message="Registered. An admin needs to approve your account before you can upload."), 201


@app.post("/api/auth/login")
def login():
    body = request.get_json(silent=True) or {}
    username = body.get("username", "").strip()
    password = body.get("password", "")

    db = get_db()
    row = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    if not row or not row["password_hash"] or not check_password_hash(row["password_hash"], password):
        return jsonify(error="invalid username or password"), 401

    if row["status"] != "approved":
        return jsonify(error="account not yet approved by an admin", status=row["status"]), 403

    token = issue_api_token(row["id"])
    return jsonify(token=token, user=public_user_dict(row))


@app.post("/api/auth/google")
def google_login():
    if not GOOGLE_CLIENT_ID:
        return jsonify(error="Google Sign-In is not configured on this server"), 500

    body = request.get_json(silent=True) or {}
    id_token_str = body.get("id_token", "")
    if not id_token_str:
        return jsonify(error="'id_token' is required"), 400

    try:
        payload = google_id_token.verify_oauth2_token(
            id_token_str, google_requests.Request(), GOOGLE_CLIENT_ID
        )
    except ValueError:
        return jsonify(error="invalid Google ID token"), 401

    google_sub = payload["sub"]
    email = payload.get("email")
    name = payload.get("name") or (email.split("@")[0] if email else google_sub[:8])

    db = get_db()
    row = db.execute("SELECT * FROM users WHERE google_sub = ?", (google_sub,)).fetchone()

    if not row and email:
        # Link to an existing password account with the same email, if any.
        row = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if row:
            db.execute("UPDATE users SET google_sub = ? WHERE id = ?", (google_sub, row["id"]))
            db.commit()

    if not row:
        user_id = str(uuid.uuid4())
        base_username = name.replace(" ", "_").lower()
        username = base_username
        suffix = 0
        while db.execute("SELECT 1 FROM users WHERE username = ?", (username,)).fetchone():
            suffix += 1
            username = f"{base_username}{suffix}"

        db.execute(
            """INSERT INTO users (id, username, email, google_sub, role, status, created_at)
               VALUES (?, ?, ?, ?, 'user', 'pending', ?)""",
            (user_id, username, email, google_sub, datetime.now(timezone.utc).isoformat()),
        )
        db.commit()
        row = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

    if row["status"] != "approved":
        return jsonify(error="account not yet approved by an admin", status=row["status"]), 403

    token = issue_api_token(row["id"])
    return jsonify(token=token, user=public_user_dict(row))


@app.get("/api/auth/me")
def whoami():
    user = authenticate_user()
    if not user:
        return jsonify(error="unauthorized"), 401
    return jsonify(user=public_user_dict(user))


# ---------------------------------------------------------------------------
# Admin endpoints — approve/reject pending accounts (admin logs in like any user;
# these routes just additionally require role == 'admin')
# ---------------------------------------------------------------------------
@app.get("/api/admin/users")
def list_users():
    if not require_admin_user():
        return jsonify(error="unauthorized"), 401
    db = get_db()
    rows = db.execute("SELECT * FROM users ORDER BY created_at").fetchall()
    return jsonify([public_user_dict(r) for r in rows])


@app.post("/api/admin/users/<user_id>/approve")
def approve_user(user_id):
    if not require_admin_user():
        return jsonify(error="unauthorized"), 401
    db = get_db()
    db.execute("UPDATE users SET status = 'approved' WHERE id = ?", (user_id,))
    db.commit()
    return jsonify(status="approved")


@app.post("/api/admin/users/<user_id>/reject")
def reject_user(user_id):
    if not require_admin_user():
        return jsonify(error="unauthorized"), 401
    db = get_db()
    db.execute("UPDATE users SET status = 'rejected' WHERE id = ?", (user_id,))
    db.commit()
    return jsonify(status="rejected")


# ---------------------------------------------------------------------------
# Device-facing endpoints — used by the Android app
# ---------------------------------------------------------------------------
@app.get("/api/media/check")
def check_media():
    user = authenticate_user()
    if not user:
        return jsonify(error="unauthorized"), 401
    if user["status"] != "approved":
        return jsonify(error="account not approved"), 403

    sha256 = request.args.get("sha256", "")
    if not sha256:
        return jsonify(error="'sha256' query param is required"), 400

    db = get_db()
    row = db.execute(
        "SELECT 1 FROM media WHERE user_id = ? AND sha256 = ?",
        (user["id"], sha256),
    ).fetchone()
    return jsonify(exists=row is not None)


@app.post("/api/media/upload")
def upload_media():
    user = authenticate_user()
    if not user:
        return jsonify(error="unauthorized"), 401
    if user["status"] != "approved":
        return jsonify(error="account not approved"), 403

    if "file" not in request.files:
        return jsonify(error="'file' part is required"), 400

    file = request.files["file"]
    media_type = request.form.get("media_type", "").strip()  # "image" or "video"
    original_name = request.form.get("original_name", "").strip() or "unnamed"
    captured_at = request.form.get("captured_at", "").strip()
    claimed_sha256 = request.form.get("sha256", "").strip().lower()

    if media_type not in ("image", "video"):
        return jsonify(error="'media_type' must be 'image' or 'video'"), 400
    if not claimed_sha256:
        return jsonify(error="'sha256' form field is required"), 400

    # Organize as BACKUP_ROOT/<username>/<yyyy>/<mm>/<safe_original_name>
    try:
        captured_dt = datetime.fromisoformat(captured_at) if captured_at else datetime.now(timezone.utc)
    except ValueError:
        captured_dt = datetime.now(timezone.utc)

    safe_username = secure_filename(user["username"]) or user["id"]
    year_month_dir = os.path.join(
        BACKUP_ROOT, safe_username, str(captured_dt.year), f"{captured_dt.month:02d}"
    )
    os.makedirs(year_month_dir, exist_ok=True)

    safe_name = secure_filename(original_name) or f"{claimed_sha256[:16]}"
    dest_path = os.path.join(year_month_dir, safe_name)

    # Avoid overwriting a different file that happens to share a filename
    if os.path.exists(dest_path):
        base, ext = os.path.splitext(safe_name)
        dest_path = os.path.join(year_month_dir, f"{base}_{claimed_sha256[:8]}{ext}")

    # Stream to disk while computing the real hash, so we never trust the client blindly
    hasher = hashlib.sha256()
    tmp_path = dest_path + ".part"
    size_bytes = 0
    with open(tmp_path, "wb") as f:
        while True:
            chunk = file.stream.read(1024 * 1024)
            if not chunk:
                break
            hasher.update(chunk)
            size_bytes += len(chunk)
            f.write(chunk)

    actual_sha256 = hasher.hexdigest()
    if actual_sha256 != claimed_sha256:
        os.remove(tmp_path)
        return jsonify(error="sha256 mismatch, upload rejected"), 400

    db = get_db()
    try:
        os.rename(tmp_path, dest_path)
        db.execute(
            """INSERT INTO media
               (user_id, sha256, media_type, original_name, captured_at, stored_path, size_bytes, uploaded_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                user["id"],
                actual_sha256,
                media_type,
                original_name,
                captured_at,
                dest_path,
                size_bytes,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        db.commit()
    except sqlite3.IntegrityError:
        # Already backed up previously (race or retry) — clean up and report as duplicate
        if os.path.exists(dest_path):
            os.remove(dest_path)
        elif os.path.exists(tmp_path):
            os.remove(tmp_path)
        return jsonify(status="duplicate"), 409

    return jsonify(status="stored", path=dest_path, sha256=actual_sha256), 201


@app.get("/api/media/stats")
def media_stats():
    user = authenticate_user()
    if not user:
        return jsonify(error="unauthorized"), 401
    db = get_db()
    row = db.execute(
        "SELECT COUNT(*) as count, COALESCE(SUM(size_bytes),0) as total_bytes FROM media WHERE user_id = ?",
        (user["id"],),
    ).fetchone()
    return jsonify(count=row["count"], total_bytes=row["total_bytes"])


# ---------------------------------------------------------------------------
# Browser pages
# ---------------------------------------------------------------------------
@app.get("/login")
def login_page():
    return render_template("login.html", google_client_id=GOOGLE_CLIENT_ID or "")


@app.get("/admin")
def admin_page():
    return render_template("admin.html")


@app.get("/upload")
def upload_page():
    return render_template("upload.html")


# ---------------------------------------------------------------------------
# Health check — verify the server is up and the external HDD is actually mounted
# ---------------------------------------------------------------------------
@app.get("/health")
def health():
    try:
        usage = shutil.disk_usage(BACKUP_ROOT)
        disk_info = {
            "total_gb": round(usage.total / (1024 ** 3), 1),
            "free_gb": round(usage.free / (1024 ** 3), 1),
        }
    except OSError:
        disk_info = None

    return jsonify(status="ok", backup_root=BACKUP_ROOT, disk=disk_info)


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)
else:
    # Also init when run under gunicorn
    init_db()
