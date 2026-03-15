# calibre-import

Automatically imports downloaded ebooks into a [Calibre](https://calibre-ebook.com/)
library running inside Docker — no shared volume mount required.

## The Problem

When books are downloaded via a torrent or NZB client, they land in a downloads
directory as subdirectories (scene releases) or loose ebook files. Getting them
into Calibre normally means opening the GUI and importing manually.

This script automates that: run it on a schedule and any new books are imported,
deduplicated, and logged.

## How It Works

1. Scans `DOWNLOAD_DIR` for new book subdirectories and loose ebook files
2. Tracks what's already been imported in a log file — skips duplicates
3. Uses `docker cp` to stage new items into the Calibre container (no volume mount needed)
4. Runs `calibredb add --automerge ignore` inside the container
5. Cleans up the staging directory and logs the result
6. Optionally writes a JSON status file for dashboard integration

Handles: `.epub`, `.mobi`, `.azw3`, `.pdf`, `.zip` (scene release archives).

## Requirements

- Docker with a running Calibre container ([linuxserver/calibre](https://hub.docker.com/r/linuxserver/calibre) recommended)
- `calibredb` available inside the container (included in linuxserver/calibre)
- The user running the script must be in the `docker` group

## Setup

```bash
# 1. Copy and configure
cp .env.example .env
$EDITOR .env          # set DOWNLOAD_DIR at minimum

# 2. Make executable
chmod +x calibre-import.sh

# 3. Test run
./calibre-import.sh

# 4. Check the log
cat ~/.local/share/calibre-import/import.log
```

## Running on a Schedule (systemd)

```bash
# Edit the service file — set User= and the EnvironmentFile/ExecStart paths
$EDITOR systemd/calibre-import.service

# Install and enable
sudo cp systemd/calibre-import.service systemd/calibre-import.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now calibre-import.timer

# Trigger manually
sudo systemctl start calibre-import.service
sudo journalctl -u calibre-import.service -n 30
```

## Homepage Dashboard Widget (optional)

The script can write a JSON status file after each run, served by a minimal HTTP
server for use with [Homepage](https://gethomepage.dev/)'s `customapi` widget.

```bash
# 1. Set STATUS_FILE in .env
STATUS_FILE=/var/lib/calibre-import/status.json

# 2. Create the directory with correct ownership
sudo mkdir -p /var/lib/calibre-import
sudo chown <YOUR_USER>:<YOUR_USER> /var/lib/calibre-import

# 3. Install the status server (edit <SERVER_LAN_IP> first)
sudo cp systemd/calibre-status-server.service /etc/systemd/system/
sudo systemctl enable --now calibre-status-server
```

Add to `services.yaml` in Homepage:

```yaml
widget:
  type: customapi
  url: http://<SERVER_LAN_IP>:8999/status.json
  mappings:
    - field: status
      label: Import Status
    - field: last_count
      label: Last Import
      suffix: " books"
    - field: total_imported
      label: Total Imported
      suffix: " books"
    - field: last_run
      label: Last Run
```

## Configuration Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DOWNLOAD_DIR` | Yes | — | Directory to scan for new books |
| `CALIBRE_CONTAINER` | No | `calibre` | Docker container name |
| `CALIBRE_LIBRARY_PATH` | No | `/config/Calibre Library` | Library path inside container |
| `PROCESSED_LOG` | No | `~/.local/share/calibre-import/processed.log` | Tracks imported items |
| `LOG_FILE` | No | `~/.local/share/calibre-import/import.log` | Human-readable run log |
| `STATUS_FILE` | No | unset (disabled) | JSON status output path |

## Security Notes

- The script validates `CALIBRE_CONTAINER` against an allowlist of safe characters
  before passing it to `docker exec`, preventing command injection
- `STATUS_FILE` status values are validated against a fixed set (`ok`, `idle`, `error`)
- The status HTTP server should be bound to a LAN IP only — never `0.0.0.0`
- The status server runs as `nobody` (not root)
- No credentials are handled by this script; keep your `.env` out of version control
