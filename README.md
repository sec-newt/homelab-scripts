# homelab-scripts

A collection of automation scripts for an Arch Linux / Wayland homelab. Covers
system setup, accessibility tooling, Hyprland integration, network monitoring,
and cloud infrastructure.

## Contents

### `setup/` — Full System Bootstrap

`install.sh` is an idempotent Arch Linux bootstrap script that reproduces a full
Hyprland desktop environment on a fresh machine. Run it once, or safely re-run it
anytime.

**What it does:**
- Full system update, yay AUR helper install
- Batch pacman, AUR, and Flatpak installs (skip already-installed packages)
- Git clone of dotfiles + scripts repos; GNU Stow to symlink everything into place
- Python venv creation for TTS and monitoring tools
- systemd user service enablement
- Prints a post-install checklist of manual steps

**Skills shown:** bash, error handling tiers (fatal vs soft-fail), idempotency patterns, stow, systemd, pipx, pacman/AUR/flatpak

---

### `sprint-hub/` — Coursework Workflow Tool

Textual TUI + CLI for capturing labeled text from any source (terminal, browser,
clipboard) and pushing it to the correct Google Docs/Sheets cell in one action.
Built to solve copy-paste errors and window-switching friction at high magnification
(4–5× zoom). Each sprint unlocks documents progressively — `sprint-add` merges new
docs into the existing config without losing prior work.

| Command | What it does |
|---------|-------------|
| `sprint-init`    | Creates a sprint config from a Google Doc/Sheet URL; maps headings/cells interactively |
| `sprint-add`     | Adds a newly-unlocked document mid-sprint; merges into existing YAML |
| `sprint-capture` | Captures piped or clipboard text with auto-suggested label (editable before saving) |
| `sprint-hub`     | Textual TUI scratchpad: buffer panel, section picker, one-key Push All to Google |

Installed via pipx. Hyprland special workspace integration (`$mainMod+F12` scratchpad
toggle, `$mainMod+Shift+X` clipboard capture). 51 tests.

Also includes standalone Google API CLI utilities in `bin/`: `gdoc-read` (full doc
text extraction across all tabs), `gsheet-read`, and `gdoc-edit` (batch text
replacement via `replaceAllText` in one API call).

→ **[Full setup and usage docs](sprint-hub/README.md)**

**Skills shown:** Python, Textual TUI, Google Docs/Sheets API, OAuth2, Wayland clipboard
(wl-paste), Hyprland scratchpad integration, pipx packaging, YAML config, Click CLI,
pytest + unittest.mock, accessible UI design (high-zoom workflow)

---

### `accessibility/` — Notification Speaking & OCR Screen Reader

Tools for spoken feedback and on-screen text reading using open-source TTS.

| Script | What it does |
|--------|-------------|
| `dbus-speak-notify.sh` | Monitors D-Bus for desktop notifications and speaks them via speech-dispatcher |
| `hp-speak-notify` | HyprPanel variant — listens on the Notifications interface and speaks summaries |
| `sr-read-mouse.sh` | OCR reader: captures a region around the mouse cursor, runs Tesseract, speaks result via Piper TTS |
| `sr-read-screen.sh` | OCR reader: interactive area selection (slurp), auto-detects dark/light mode for image pre-processing, speaks result |

The OCR scripts pre-process images before Tesseract (grayscale → detect brightness
→ conditional negate → resize → contrast stretch) to handle both dark and light
UI themes without manual configuration.

**Skills shown:** D-Bus monitoring, image processing (ImageMagick), OCR (Tesseract), TTS pipeline, Wayland tooling (grim, slurp, hyprctl)

---

### `hyprland/` — Hyprland / Wayland Desktop Integration

| Script | What it does |
|--------|-------------|
| `audioswitch.py` | Cycles through PipeWire audio sinks via wpctl; sends a desktop notification with the new sink name |
| `waybar-audio-sink.py` | Waybar custom module — outputs current audio sink as JSON |
| `zoomup.py` | Increases Hyprland's `cursor:zoom_factor` by 1 — bound to `Super+ScrollUp` |
| `zoomdown.py` | Decreases Hyprland's `cursor:zoom_factor` by 1 (floor at 1) — bound to `Super+ScrollDown` |

**Skills shown:** Python, PipeWire/wpctl parsing, Waybar JSON module format, Wayland compositor integration, Hyprland IPC (`hyprctl keyword`)

---

### `network/` — Home Network Status Monitor

`home-network-status.sh` checks the health of a self-hosted homelab at a glance.
Designed to be readable by non-technical users (written for a spouse/family member).

- Polls local services (dashboard, media server, cloud storage, password manager) via HTTP
- Tests SSH connectivity to the main server
- Checks disk usage per mount point with colour-coded thresholds (80% warn / 90% critical)
- Checks Docker container health, lists any stopped containers by name
- Prints a clear summary with actionable next steps

All hostnames and URLs are variables at the top of the file — no hardcoded values.

**Skills shown:** bash, curl health checks, SSH remote commands, Docker status parsing, user-friendly output design

---

### `cloud/` — Linode Bastion for Reverse SSH

`linode-bastion.sh` spins up a cheap Linode VPS as a temporary reverse-SSH jump
host, then destroys it when done (pay only for what you use).

```
./linode-bastion.sh up    # provision server, print systemd unit for target VM
./linode-bastion.sh down  # destroy all bastion instances
```

- Reads `$LINODE_TOKEN` from environment (never hardcoded)
- Imports SSH key to Linode if not already present; offers to generate one
- Polls until the instance reaches `running` state
- Prints a ready-to-paste systemd unit for the target machine plus step-by-step
  connection instructions
- Verbose output designed for screen-reader narration

**Skills shown:** Linode API via linode-cli, bash, cloud infrastructure, reverse SSH tunnelling, systemd unit generation

---

### `security/` — Security Tool Installer (Debian/Ubuntu)

`install_security_tools.sh` batch-installs a common penetration testing toolkit:
nmap, Wireshark, SQLmap, Hydra, John the Ripper, Aircrack-ng, Gobuster, Bettercap,
Metasploit Framework, and SecLists.

Note: targets Debian/Ubuntu (`apt`). For Arch Linux equivalents use the pacman/AUR
packages in `setup/packages/`.

---

### `docker/calibre-import/` — Calibre Ebook Auto-Importer

Imports downloaded ebooks into a Calibre Docker container automatically.
Uses `docker cp` to stage files into the container and `calibredb add` to import them —
no shared volume mount required, works with any Calibre Docker setup.

- Scans a downloads directory for new book folders and loose ebook files
- Tracks imported items to prevent duplicates across runs
- Handles `.epub`, `.mobi`, `.azw3`, `.pdf`, and `.zip` (scene release archives)
- Optional JSON status file for dashboard integration (Homepage `customapi` widget)
- Fully configured via environment variables — drop a `.env` file next to the script
- Includes systemd service + timer for hourly unattended runs

**Design notes:**
- Container name validated against a character allowlist before use in `docker exec` — no injection
- Status values validated against a fixed set before writing to JSON
- Status HTTP server runs as `nobody` bound to LAN IP only — never root, never `0.0.0.0`
- `find -print0` + `read -d ''` throughout — handles filenames with spaces and special characters
- Processed items log prevents re-import on every run without needing a database

→ **[Full setup and usage docs](docker/calibre-import/README.md)**

**Skills shown:** bash, Docker (`docker exec`, `docker cp`), `calibredb`, systemd services and timers, input validation, environment-variable-driven configuration, security hardening

---

### `lib/python/` — Shared Python Modules

`email_sender.py` — reusable ProtonMail SMTP module.

- Reads credentials from `~/.config/scripts/email.conf` (see `email.conf.example`)
- `EmailSender` class with `send_email()` and `send_notification()` methods
- Convenience module-level functions for easy import
- Used by the torrent monitor and docker update scripts

---

## Requirements

Most scripts target **Arch Linux + Hyprland + Wayland**. Specific dependencies:

| Category | Dependencies |
|----------|-------------|
| Accessibility | `speech-dispatcher`, `spd-say`, `grim`, `slurp`, `tesseract`, `imagemagick`, `piper-tts` |
| Hyprland scripts | `pipewire`, `wpctl`, `waybar`, `swww`, `fuzzel`, `hyprctl` |
| Network monitor | `curl`, `ping`, `ssh`, `docker` (on target server) |
| Docker stacks | `docker`, `docker compose`, `tailscale` |
| Cloud/bastion | `linode-cli`, `jq`, `ssh` |
| Bootstrap | `git`, `stow`, `yay` (bootstrapped by install.sh itself) |

## Setup — Arch Bootstrap

```bash
# Copy to new machine and run
scp -r user@oldmachine:~/Scripts/setup ~/setup-tmp
bash ~/setup-tmp/install.sh
```

See the header comments in `setup/install.sh` for full usage notes.
