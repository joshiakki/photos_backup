# Photo/Video Backup Server

Flask + SQLite server that receives camera photos/videos from your Android app
and stores them on an external hard disk attached to your Ubuntu machine.

## 1. Mount the external hard disk (if not already mounted)

Find the disk:
```bash
lsblk -f
```
You'll see something like `/dev/sdb1` with a label. Create a mount point and mount it:
```bash
sudo mkdir -p /mnt/external_hdd
sudo mount /dev/sdb1 /mnt/external_hdd
```

To make this survive a reboot, get the UUID and add it to `/etc/fstab`:
```bash
sudo blkid /dev/sdb1
# copy the UUID, then:
sudo nano /etc/fstab
# add a line like:
# UUID=xxxx-xxxx  /mnt/external_hdd  ext4  defaults  0  2
```

Create the folder the container will write into:
```bash
sudo mkdir -p /mnt/external_hdd/photobackup
sudo chown $USER:$USER /mnt/external_hdd/photobackup
```

## 2. Configure the admin account and (optionally) Google Sign-In

```bash
cp .env.example .env
```

Edit `.env` and set:
- `ADMIN_USERNAME` / `ADMIN_PASSWORD` — this account is created automatically the first time the server starts, with `role=admin` and pre-approved status. Use a real password here, not the placeholder.
- `GOOGLE_CLIENT_ID` — only needed if you want "Sign in with Google" to work (see step 6 below). Leave the placeholder if you don't want Google Sign-In; the Google button will simply not appear on the login page.

Also edit `docker-compose.yml` if your HDD mount path isn't `/mnt/external_hdd/photobackup`.

## 3. Build and run

```bash
docker compose up -d --build
```

Check it's alive and can see the disk:
```bash
curl http://localhost:5000/health
```
Expected:
```json
{"status": "ok", "backup_root": "/data/backups", "disk": {"total_gb": 931.5, "free_gb": 800.2}}
```
If `"disk"` is `null`, the volume mount isn't pointing at a real disk — check `docker-compose.yml`.

## 4. Create your own account and approve it

Register (as yourself, for your phone or browser):
```bash
curl -X POST https://photobackup.yourdomain.com/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "yourname", "password": "a-real-password"}'
```
This account starts out **pending** — nothing can upload until an admin approves it.

Log in as admin and approve it:
```bash
ADMIN_TOKEN=$(curl -s -X POST https://photobackup.yourdomain.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"username\": \"$ADMIN_USERNAME\", \"password\": \"$ADMIN_PASSWORD\"}" | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")

curl https://photobackup.yourdomain.com/api/admin/users -H "Authorization: Bearer $ADMIN_TOKEN"
# find your user's "id" in the output, then:
curl -X POST https://photobackup.yourdomain.com/api/admin/users/<your-user-id>/approve \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

Easier alternative: visit `https://photobackup.yourdomain.com/admin` in a browser, log in at `/login` as the admin account first (so a token is saved in the browser), then approve accounts with a click from the same browser (open `/admin` in the same browser session — it reuses the saved login token).

Once approved, log in to get the token your Android app / browser will use:
```bash
curl -X POST https://photobackup.yourdomain.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "yourname", "password": "a-real-password"}'
```
This returns a `token` — that's what goes into the Android app's login screen (or it happens automatically if you log in from within the app/browser directly, which is the normal flow — the curl above is just for testing).

## 5. Set up "Sign in with Google" (optional)

Skip this section entirely if you're fine with username/password only — everything else works without it.

1. Go to the [Google Cloud Console](https://console.cloud.google.com/) → create a project (or pick an existing one).
2. **APIs & Services → OAuth consent screen** → set it up as **External**, add your email as a test user (or publish it — for personal use, "Testing" mode is fine and avoids Google's review process).
3. **APIs & Services → Credentials → Create Credentials → OAuth client ID** → Application type: **Web application**.
   - Add an **Authorized JavaScript origin**: `https://photobackup.yourdomain.com`
   - You do **not** need a redirect URI for this flow.
4. Copy the generated **Client ID** (looks like `xxxx.apps.googleusercontent.com`) into `.env` as `GOOGLE_CLIENT_ID`.
5. This same Web Client ID is reused later for the Android app too — Android doesn't need its own separate OAuth client for this, just this one plus its SHA-1 fingerprint registered (covered in the Android setup).
6. Restart the server: `docker compose up -d --build`. The Google button will now appear on `/login`.

## 6. Expose it via Cloudflare Tunnel (free, no bandwidth cap, no ports opened)

You need a domain added to your Cloudflare account (Cloudflare's DNS must be authoritative for it — a cheap domain from any registrar works, just point its nameservers at Cloudflare).

1. Go to the [Cloudflare Zero Trust dashboard](https://one.dash.cloudflare.com/) → **Networks → Tunnels → Create a tunnel** → choose **Cloudflared** → name it (e.g. `photobackup`).
2. Copy the **tunnel token** it shows you (you won't see it again without regenerating).
3. On the same setup screen, add a **Public Hostname**:
   - Subdomain: `photobackup` (or anything)
   - Domain: your domain
   - Service: `HTTP` → `photobackup:5000` (the service name from `docker-compose.yml`, since `cloudflared` reaches it over the internal Docker network — not `localhost`)
4. Add `TUNNEL_TOKEN=<the token from step 2>` to your `.env` file.
5. Start everything:
   ```bash
   docker compose up -d --build
   ```

Your server is now reachable at `https://photobackup.yourdomain.com` — this URL is permanent and never changes across restarts, unlike a free ngrok URL. This becomes the `server_url` the Android app uses.

Check the tunnel came up:
```bash
docker compose logs -f cloudflared
# look for a line like: "Registered tunnel connection"
```

## 7. Test the upload flow manually before touching the Android app

```bash
SERVER=https://photobackup.yourdomain.com

# Log in as your approved account to get a token
TOKEN=$(curl -s -X POST "$SERVER/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "yourname", "password": "a-real-password"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")

# Check if a hash exists (should be false the first time)
curl "$SERVER/api/media/check?sha256=$(sha256sum test.jpg | cut -d' ' -f1)" \
  -H "Authorization: Bearer $TOKEN"

# Upload a test file
curl -X POST "$SERVER/api/media/upload" \
  -H "Authorization: Bearer $TOKEN" \
  -F "media_type=image" \
  -F "original_name=test.jpg" \
  -F "captured_at=2026-07-25T10:00:00" \
  -F "sha256=$(sha256sum test.jpg | cut -d' ' -f1)" \
  -F "file=@test.jpg"
```
Expected: `{"status": "stored", "path": "/data/backups/yourname/2026/07/test.jpg", ...}`.
Re-running the same command should now return `{"status": "duplicate"}` with HTTP 409 — this is the dedup logic working.

## 8. Web pages

- **`/login`** — username/password sign in, registration, and "Sign in with Google" (if configured).
- **`/upload`** — drag-and-drop browser upload, gated behind login. Uses the exact same `/api/media/check` and `/api/media/upload` endpoints the Android app uses — same dedup logic, same storage layout, same auth. Redirects to `/login` if you're not signed in, and shows a "waiting for approval" message if your account is still pending.
- **`/admin`** — approve or reject pending accounts. Paste in the admin account's token (or just log in at `/login` as the admin first in the same browser — `/admin` will pick up that saved token automatically).

Since file hashing happens in the browser via the Web Crypto API, `/upload` requires HTTPS (which you already have via the Cloudflare Tunnel) — it won't work over plain `http://`.

## API summary

| Endpoint | Method | Auth | Purpose |
|---|---|---|---|
| `/health` | GET | none | Confirm server + disk are up |
| `/api/auth/register` | POST | none | Create a new account (starts as `pending`) |
| `/api/auth/login` | POST | none | Username/password login → returns API token |
| `/api/auth/google` | POST | none | Google ID token login → returns API token |
| `/api/auth/me` | GET | `Bearer <token>` | Current user's info/status |
| `/api/admin/users` | GET | `Bearer <admin token>` | List all accounts |
| `/api/admin/users/<id>/approve` | POST | `Bearer <admin token>` | Approve a pending account |
| `/api/admin/users/<id>/reject` | POST | `Bearer <admin token>` | Reject a pending account |
| `/api/media/check?sha256=...` | GET | `Bearer <token>` | Check if a file was already backed up |
| `/api/media/upload` | POST multipart | `Bearer <token>` | Upload a new file (requires `approved` status) |
| `/api/media/stats` | GET | `Bearer <token>` | Count/size of files backed up for this account |

## Logs / troubleshooting

```bash
docker compose logs -f photobackup
```

## Notes on this v1

- Files are streamed to disk while hashing, so a partial/corrupt upload never gets recorded in the database.
- Re-uploading the same file (same sha256) is safely rejected as a duplicate instead of creating a second copy.
- Max upload size is 2GB by default (`MAX_CONTENT_LENGTH_MB` in docker-compose.yml) — raise it if you shoot long 4K video.
- Not yet included (fine for v1, worth adding later): resumable/chunked upload for very large videos on flaky connections. HTTPS is provided by the Cloudflare Tunnel (Cloudflare terminates TLS for you, so the Flask app itself only needs to speak plain HTTP internally — that's expected and fine).
