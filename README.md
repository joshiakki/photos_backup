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

## 2. Configure the secret

```bash
cp .env.example .env
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
# paste the output as ADMIN_TOKEN in .env
```

Also edit `docker-compose.yml` if your mount path isn't `/mnt/external_hdd/photobackup`.

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

## 4. Register your phone (do this once per device)

```bash
source .env
curl -X POST http://localhost:5000/api/admin/devices \
  -H "X-Admin-Token: $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "PixelPhone"}'
```
Response:
```json
{"device_id": "a1b2c3...", "name": "PixelPhone", "token": "kR8f...long-random-string"}
```
**Save the `token` value** — this is what goes into the Android app's settings. It's shown only once (only its hash is stored server-side).

List registered devices any time:
```bash
curl http://localhost:5000/api/admin/devices -H "X-Admin-Token: $ADMIN_TOKEN"
```

## 5. Expose it via ngrok

```bash
ngrok http 5000
```
Copy the `https://xxxx.ngrok-free.app` URL it gives you — that's the `server_url` the Android app will use.
(A paid ngrok plan with a reserved domain means this URL never changes between restarts — worth it if you'll restart the tunnel often.)

## 6. Test the upload flow manually before touching the Android app

```bash
SERVER=https://xxxx.ngrok-free.app
TOKEN=kR8f...long-random-string   # from step 4

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
Expected: `{"status": "stored", "path": "/data/backups/PixelPhone/2026/07/test.jpg", ...}`.
Re-running the same command should now return `{"status": "duplicate"}` with HTTP 409 — this is the dedup logic working.

## API summary (for the Android app)

| Endpoint | Method | Auth | Purpose |
|---|---|---|---|
| `/health` | GET | none | Confirm server + disk are up |
| `/api/media/check?sha256=...` | GET | `Bearer <device_token>` | Check if a file was already backed up |
| `/api/media/upload` | POST multipart | `Bearer <device_token>` | Upload a new file |
| `/api/media/stats` | GET | `Bearer <device_token>` | Count/size of files backed up for this device |
| `/api/admin/devices` | POST | `X-Admin-Token` | Register a new device (run manually, not from the app) |

## Logs / troubleshooting

```bash
docker compose logs -f photobackup
```

## Notes on this v1

- Files are streamed to disk while hashing, so a partial/corrupt upload never gets recorded in the database.
- Re-uploading the same file (same sha256) is safely rejected as a duplicate instead of creating a second copy.
- Max upload size is 2GB by default (`MAX_CONTENT_LENGTH_MB` in docker-compose.yml) — raise it if you shoot long 4K video.
- Not yet included (fine for v1, worth adding later): resumable/chunked upload for very large videos on flaky connections, and HTTPS is currently provided only via the ngrok tunnel (fine, since ngrok terminates TLS for you).
