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
from flask import Flask, request, jsonify, g
from werkzeug.utils import secure_filename

# ---------------------------------------------------------------------------
# Configuration (all overridable via environment variables / .env)
# ---------------------------------------------------------------------------
BACKUP_ROOT = os.environ.get("BACKUP_ROOT", "/data/backups")
DB_PATH = os.environ.get("DB_PATH", "/data/db/backup.db")
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN")  # required to create/list devices
MAX_CONTENT_LENGTH_MB = int(os.environ.get("MAX_CONTENT_LENGTH_MB", "2048"))  # 2GB default, for large videos

if not ADMIN_TOKEN:
    raise RuntimeError(
        "ADMIN_TOKEN environment variable is not set. "
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
        CREATE TABLE IF NOT EXISTS devices (
            id           TEXT PRIMARY KEY,
            name         TEXT NOT NULL,
            token_hash   TEXT NOT NULL UNIQUE,
            created_at   TEXT NOT NULL,
            last_seen_at TEXT
        );

        CREATE TABLE IF NOT EXISTS media (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id    TEXT NOT NULL REFERENCES devices(id),
            sha256       TEXT NOT NULL,
            media_type   TEXT NOT NULL,
            original_name TEXT,
            captured_at  TEXT,
            stored_path  TEXT NOT NULL,
            size_bytes   INTEGER NOT NULL,
            uploaded_at  TEXT NOT NULL,
            UNIQUE(device_id, sha256)
        );

        CREATE INDEX IF NOT EXISTS idx_media_device ON media(device_id);
        CREATE INDEX IF NOT EXISTS idx_media_hash ON media(sha256);
        """
    )
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------
def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def require_admin():
    supplied = request.headers.get("X-Admin-Token", "")
    if not secrets.compare_digest(supplied, ADMIN_TOKEN):
        return False
    return True


def authenticate_device():
    """Resolve the calling device from the Bearer token. Returns a devices row or None."""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    token = auth[len("Bearer "):].strip()
    if not token:
        return None
    db = get_db()
    row = db.execute(
        "SELECT * FROM devices WHERE token_hash = ?", (hash_token(token),)
    ).fetchone()
    if row:
        db.execute(
            "UPDATE devices SET last_seen_at = ? WHERE id = ?",
            (datetime.now(timezone.utc).isoformat(), row["id"]),
        )
        db.commit()
    return row


# ---------------------------------------------------------------------------
# Admin endpoints — used once per phone to set it up, not called by the app itself
# ---------------------------------------------------------------------------
@app.post("/api/admin/devices")
def create_device():
    if not require_admin():
        return jsonify(error="unauthorized"), 401

    body = request.get_json(silent=True) or {}
    name = body.get("name", "").strip()
    if not name:
        return jsonify(error="'name' is required"), 400

    device_id = str(uuid.uuid4())
    token = secrets.token_urlsafe(32)  # shown once, never stored in plaintext

    db = get_db()
    db.execute(
        "INSERT INTO devices (id, name, token_hash, created_at) VALUES (?, ?, ?, ?)",
        (device_id, name, hash_token(token), datetime.now(timezone.utc).isoformat()),
    )
    db.commit()

    return jsonify(device_id=device_id, name=name, token=token), 201


@app.get("/api/admin/devices")
def list_devices():
    if not require_admin():
        return jsonify(error="unauthorized"), 401
    db = get_db()
    rows = db.execute(
        "SELECT id, name, created_at, last_seen_at FROM devices ORDER BY created_at"
    ).fetchall()
    return jsonify([dict(r) for r in rows])


# ---------------------------------------------------------------------------
# Device-facing endpoints — used by the Android app
# ---------------------------------------------------------------------------
@app.get("/api/media/check")
def check_media():
    device = authenticate_device()
    if not device:
        return jsonify(error="unauthorized"), 401

    sha256 = request.args.get("sha256", "")
    if not sha256:
        return jsonify(error="'sha256' query param is required"), 400

    db = get_db()
    row = db.execute(
        "SELECT 1 FROM media WHERE device_id = ? AND sha256 = ?",
        (device["id"], sha256),
    ).fetchone()
    return jsonify(exists=row is not None)


@app.post("/api/media/upload")
def upload_media():
    device = authenticate_device()
    if not device:
        return jsonify(error="unauthorized"), 401

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

    # Organize as BACKUP_ROOT/<device_name>/<yyyy>/<mm>/<safe_original_name>
    try:
        captured_dt = datetime.fromisoformat(captured_at) if captured_at else datetime.now(timezone.utc)
    except ValueError:
        captured_dt = datetime.now(timezone.utc)

    safe_device_name = secure_filename(device["name"]) or device["id"]
    year_month_dir = os.path.join(
        BACKUP_ROOT, safe_device_name, str(captured_dt.year), f"{captured_dt.month:02d}"
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
               (device_id, sha256, media_type, original_name, captured_at, stored_path, size_bytes, uploaded_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                device["id"],
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
    device = authenticate_device()
    if not device:
        return jsonify(error="unauthorized"), 401
    db = get_db()
    row = db.execute(
        "SELECT COUNT(*) as count, COALESCE(SUM(size_bytes),0) as total_bytes FROM media WHERE device_id = ?",
        (device["id"],),
    ).fetchone()
    return jsonify(count=row["count"], total_bytes=row["total_bytes"])


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
