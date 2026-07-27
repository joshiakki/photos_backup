"""
Run this INSIDE the photobackup container to reset the admin password
to whatever ADMIN_PASSWORD is currently set to in the container's environment.

Usage (from the host, in the photobackup-server folder):
    docker cp reset_admin_password.py photobackup:/app/reset_admin_password.py
    docker compose exec photobackup python3 /app/reset_admin_password.py
"""
import sqlite3
import os
from werkzeug.security import generate_password_hash

db_path = os.environ.get("DB_PATH", "/data/db/backup.db")
username = os.environ.get("ADMIN_USERNAME", "admin")
password = os.environ.get("ADMIN_PASSWORD")

if not password:
    raise SystemExit("ADMIN_PASSWORD is not set in this container's environment - check .env")

print(f"DB path: {db_path}")
print(f"Resetting password for username: {username}")

conn = sqlite3.connect(db_path)
cursor = conn.execute("SELECT id FROM users WHERE username = ?", (username,))
row = cursor.fetchone()

if not row:
    print(f"No user found with username '{username}'. Existing users:")
    for r in conn.execute("SELECT username, role, status FROM users"):
        print(" -", r)
    raise SystemExit(1)

conn.execute(
    "UPDATE users SET password_hash = ? WHERE username = ?",
    (generate_password_hash(password), username),
)
conn.commit()
conn.close()
print("Done. Admin password now matches ADMIN_PASSWORD in .env")
