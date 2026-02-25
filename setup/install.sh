#!/usr/bin/env bash
# =============================================================================
# Hyprland New-Machine Bootstrap Script
# =============================================================================
# Usage: bash ~/setup-tmp/install.sh
# Safe to re-run — idempotent throughout.
# =============================================================================

set -euo pipefail

# --- Configuration (edit before running) -------------------------------------
DOTFILES_REPO=""   # e.g. git@github.com:nk/dotfiles.git
SCRIPTS_REPO=""    # e.g. git@github.com:nk/Scripts.git
WALLRIZZ_REPO=""   # e.g. git@github.com:nk/WallRizz.git
CURSOR_REPO=""     # e.g. git@github.com:nk/future-cyan-hyprcursor.git

# --- Derived paths -----------------------------------------------------------
SETUP_DIR="$(dirname "$(realpath "$0")")"
DOTFILES_DIR="$HOME/.dotfiles"
SCRIPTS_DEST="$DOTFILES_DIR/Scripts/Scripts"
GIT_DIR="$HOME/Git"

# --- Logging -----------------------------------------------------------------
LOG_FILE="$HOME/setup-install.log"
FAILURES=()

log()    { echo "[$(date '+%H:%M:%S')] $*" | tee -a "$LOG_FILE"; }
info()   { log "INFO  $*"; }
warn()   { log "WARN  $*"; }
fail()   { log "FAIL  $*"; FAILURES+=("$*"); }
section(){ echo; log "=== $* ==="; }

# =============================================================================
# Section 0: Preflight
# =============================================================================
section "0: Preflight"

if [[ $EUID -eq 0 ]]; then
    echo "ERROR: Do not run this script as root." >&2
    exit 1
fi

if ! sudo -v 2>/dev/null; then
    echo "ERROR: sudo access required." >&2
    exit 1
fi

if [[ -z "$DOTFILES_REPO" || -z "$SCRIPTS_REPO" ]]; then
    warn "DOTFILES_REPO and/or SCRIPTS_REPO are not set."
    warn "Repo clone steps will be skipped. Continuing in 5 seconds..."
    warn "Press Ctrl+C to abort and set them at the top of this script."
    sleep 5
fi

# Keep sudo alive for the duration of the script
( while true; do sudo -v; sleep 55; done ) &
SUDO_KEEP_ALIVE_PID=$!
trap 'kill "$SUDO_KEEP_ALIVE_PID" 2>/dev/null' EXIT

info "Preflight passed. Logging to $LOG_FILE"

# =============================================================================
# Section 1: System Update
# =============================================================================
section "1: System update"

sudo pacman -Syu --noconfirm

# =============================================================================
# Section 2: Install yay (AUR helper)
# =============================================================================
section "2: Install yay"

if command -v yay &>/dev/null; then
    info "yay already installed, skipping."
else
    info "Installing yay from AUR..."
    sudo pacman -S --needed --noconfirm base-devel git
    YAY_TMP=$(mktemp -d)
    git clone https://aur.archlinux.org/yay.git "$YAY_TMP/yay"
    ( cd "$YAY_TMP/yay" && makepkg -si --noconfirm )
    rm -rf "$YAY_TMP"
    info "yay installed."
fi

# =============================================================================
# Section 3: Pacman packages
# =============================================================================
section "3: Pacman packages"

PACMAN_LIST="$SETUP_DIR/packages/pacman.txt"

if [[ ! -f "$PACMAN_LIST" ]]; then
    warn "packages/pacman.txt not found, skipping pacman installs."
else
    # Collect packages: strip comments and blank lines
    mapfile -t PACMAN_PKGS < <(grep -v '^\s*#' "$PACMAN_LIST" | grep -v '^\s*$')
    TO_INSTALL=()
    for pkg in "${PACMAN_PKGS[@]}"; do
        if pacman -Qi "$pkg" &>/dev/null; then
            info "  [skip] $pkg (already installed)"
        else
            TO_INSTALL+=("$pkg")
        fi
    done
    if [[ ${#TO_INSTALL[@]} -gt 0 ]]; then
        info "Installing ${#TO_INSTALL[@]} pacman packages..."
        sudo pacman -S --needed --noconfirm "${TO_INSTALL[@]}"
    else
        info "All pacman packages already installed."
    fi
fi

# =============================================================================
# Section 4: AUR packages
# =============================================================================
section "4: AUR packages"

AUR_LIST="$SETUP_DIR/packages/aur.txt"

if [[ ! -f "$AUR_LIST" ]]; then
    warn "packages/aur.txt not found, skipping AUR installs."
else
    mapfile -t AUR_PKGS < <(grep -v '^\s*#' "$AUR_LIST" | grep -v '^\s*$')
    for pkg in "${AUR_PKGS[@]}"; do
        if pacman -Qi "$pkg" &>/dev/null; then
            info "  [skip] $pkg (already installed)"
        else
            info "  Installing AUR: $pkg"
            if ! yay -S --needed --noconfirm "$pkg"; then
                fail "AUR install failed: $pkg"
            fi
        fi
    done
fi

# =============================================================================
# Section 5: Flatpaks
# =============================================================================
section "5: Flatpaks"

FLATPAK_LIST="$SETUP_DIR/packages/flatpak.txt"

if ! command -v flatpak &>/dev/null; then
    warn "flatpak not found, skipping Flatpak installs."
else
    # Add Flathub if not already present
    if ! flatpak remotes | grep -q flathub; then
        info "Adding Flathub remote..."
        flatpak remote-add --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo
    fi

    if [[ ! -f "$FLATPAK_LIST" ]]; then
        warn "packages/flatpak.txt not found, skipping Flatpak installs."
    else
        mapfile -t FLATPAK_APPS < <(grep -v '^\s*#' "$FLATPAK_LIST" | grep -v '^\s*$')
        for app in "${FLATPAK_APPS[@]}"; do
            if flatpak list --app --columns=application | grep -qx "$app"; then
                info "  [skip] $app (already installed)"
            else
                info "  Installing Flatpak: $app"
                if ! flatpak install -y flathub "$app"; then
                    fail "Flatpak install failed: $app"
                fi
            fi
        done
    fi
fi

# =============================================================================
# Section 6: Clone repos
# =============================================================================
section "6: Clone repos"

clone_if_missing() {
    local repo="$1"
    local dest="$2"
    local label="${3:-$dest}"
    if [[ -z "$repo" ]]; then
        warn "  Repo URL not set for $label, skipping."
        return
    fi
    if [[ -d "$dest/.git" ]]; then
        info "  [skip] $label (already cloned)"
    else
        info "  Cloning $label -> $dest"
        mkdir -p "$(dirname "$dest")"
        if ! git clone "$repo" "$dest"; then
            fail "git clone failed: $label"
        fi
    fi
}

clone_if_missing "$DOTFILES_REPO"  "$DOTFILES_DIR"                          "dotfiles"
clone_if_missing "$SCRIPTS_REPO"   "$SCRIPTS_DEST"                          "Scripts"
clone_if_missing "$WALLRIZZ_REPO"  "$GIT_DIR/WallRizz"                      "WallRizz"
clone_if_missing "$CURSOR_REPO"    "$GIT_DIR/future-cyan-hyprcursor"        "future-cyan-hyprcursor"

# =============================================================================
# Section 7: Hyprcursor theme
# =============================================================================
section "7: Hyprcursor theme"

CURSOR_SRC="$GIT_DIR/future-cyan-hyprcursor"
CURSOR_DEST="$HOME/.local/share/icons"

if [[ -d "$CURSOR_SRC" ]]; then
    mkdir -p "$CURSOR_DEST"
    # Copy all cursor theme directories found inside the repo
    COPIED=0
    for theme_dir in "$CURSOR_SRC"/*/; do
        if [[ -d "$theme_dir" ]]; then
            dest_name="$(basename "$theme_dir")"
            if [[ -d "$CURSOR_DEST/$dest_name" ]]; then
                info "  [skip] cursor theme $dest_name (already exists)"
            else
                info "  Copying cursor theme: $dest_name"
                cp -r "$theme_dir" "$CURSOR_DEST/"
                COPIED=$((COPIED + 1))
            fi
        fi
    done
    [[ $COPIED -eq 0 ]] || info "Copied $COPIED cursor theme(s)."
else
    warn "future-cyan-hyprcursor repo not found at $CURSOR_SRC, skipping."
fi

# =============================================================================
# Section 8: Stow dotfiles
# =============================================================================
section "8: Stow dotfiles"

STOW_PACKAGES=(
    home
    alacritty kitty fuzzel gtk qt6ct starship
    hypr
    hyprpanel waybar
    systemd
    pim
    zed
    Scripts
)

if [[ ! -d "$DOTFILES_DIR" ]]; then
    warn "Dotfiles directory $DOTFILES_DIR not found, skipping stow."
else
    for pkg in "${STOW_PACKAGES[@]}"; do
        pkg_dir="$DOTFILES_DIR/$pkg"
        if [[ ! -d "$pkg_dir" ]]; then
            warn "  [skip] stow package '$pkg' — directory not found"
            continue
        fi
        info "  Stowing: $pkg"
        if ! stow --restow --dir="$DOTFILES_DIR" --target="$HOME" "$pkg" 2>>"$LOG_FILE"; then
            fail "stow failed: $pkg"
        fi
    done
fi

# =============================================================================
# Section 9: pipx packages
# =============================================================================
section "9: pipx packages"

if ! command -v pipx &>/dev/null; then
    warn "pipx not found, skipping pipx installs."
else
    pipx_install() {
        local pkg="$1"
        if pipx list | grep -q "$pkg"; then
            info "  [skip] $pkg (already installed via pipx)"
        else
            info "  Installing via pipx: $pkg"
            if ! pipx install "$pkg"; then
                fail "pipx install failed: $pkg"
            fi
        fi
    }

    pipx_install vdirsyncer
fi

# =============================================================================
# Section 10: Python venvs
# =============================================================================
section "10: Python venvs"

VENVS_DIR="$HOME/Scripts/.venvs"
mkdir -p "$VENVS_DIR"

# TTS venv
TTS_VENV="$VENVS_DIR/tts"
TTS_REQ="$HOME/Scripts/.venvs/tts-requirements.txt"
TTS_FALLBACK_PKGS="openai piper-tts onnxruntime numpy"

if [[ -d "$TTS_VENV" ]]; then
    info "  [skip] TTS venv (already exists at $TTS_VENV)"
else
    info "  Creating TTS venv..."
    python -m venv "$TTS_VENV"
    if [[ -f "$TTS_REQ" ]]; then
        info "  Installing TTS requirements from $TTS_REQ"
        "$TTS_VENV/bin/pip" install -r "$TTS_REQ"
    else
        warn "  tts-requirements.txt not found; installing fallback packages: $TTS_FALLBACK_PKGS"
        # shellcheck disable=SC2086
        "$TTS_VENV/bin/pip" install $TTS_FALLBACK_PKGS
    fi
fi

# Torrent-monitor venv (only if requirements.txt exists)
TORRENT_REQ="$HOME/Scripts/projects/torrent-monitor/requirements.txt"
TORRENT_VENV="$VENVS_DIR/torrent-monitor"

if [[ -f "$TORRENT_REQ" ]]; then
    if [[ -d "$TORRENT_VENV" ]]; then
        info "  [skip] torrent-monitor venv (already exists)"
    else
        info "  Creating torrent-monitor venv..."
        python -m venv "$TORRENT_VENV"
        "$TORRENT_VENV/bin/pip" install -r "$TORRENT_REQ"
    fi
else
    info "  [skip] torrent-monitor venv (no requirements.txt found)"
fi

# =============================================================================
# Section 11: System services
# =============================================================================
section "11: System services"

SYSTEM_SERVICES=(
    NetworkManager
    bluetooth
)

for svc in "${SYSTEM_SERVICES[@]}"; do
    if systemctl is-enabled "$svc" &>/dev/null; then
        info "  [skip] $svc (already enabled)"
    else
        info "  Enabling system service: $svc"
        sudo systemctl enable "$svc"
    fi
done

# =============================================================================
# Section 12: User services
# =============================================================================
section "12: User services"

USER_SERVICES=(
    hypridle.service
    syncthing.service
    dbus-notify-speak.service
    clawdbot-gateway-clean.service
)

USER_TIMERS=(
    vdirsyncer.timer
)

systemctl --user daemon-reload

for svc in "${USER_SERVICES[@]}" "${USER_TIMERS[@]}"; do
    if systemctl --user is-enabled "$svc" &>/dev/null; then
        info "  [skip] $svc (already enabled)"
    else
        info "  Enabling user service: $svc"
        if ! systemctl --user enable "$svc" 2>>"$LOG_FILE"; then
            fail "systemctl --user enable failed: $svc"
        fi
    fi
done

# =============================================================================
# Section 13: XDG directories
# =============================================================================
section "13: XDG dirs"

xdg-user-dirs-update
info "XDG user dirs updated."

# =============================================================================
# Section 14: Summary & Post-Install Checklist
# =============================================================================
section "14: Summary"

# Report failures
if [[ ${#FAILURES[@]} -gt 0 ]]; then
    echo
    echo "============================================================"
    echo "  SOFT FAILURES (${#FAILURES[@]}) — review and retry manually:"
    echo "============================================================"
    for f in "${FAILURES[@]}"; do
        echo "  - $f"
    done
    echo "Full log: $LOG_FILE"
    echo
fi

echo "============================================================"
echo "  POST-INSTALL CHECKLIST — complete these manually:"
echo "============================================================"
echo
echo "  1. Tailscale:"
echo "       sudo systemctl enable --now tailscaled"
echo "       sudo tailscale up"
echo
echo "  2. ProtonVPN:"
echo "       protonvpn-cli login"
echo "       systemctl --user enable --now protonvpn_reconnect"
echo
echo "  3. vdirsyncer:"
echo "       Edit ~/.config/vdirsyncer/config"
echo "       vdirsyncer discover"
echo
echo "  4. Syncthing:"
echo "       Open http://localhost:8384 and pair with Zeus"
echo
echo "  5. Piper TTS model:"
echo "       Download .onnx + .json files to expected path"
echo
echo "  6. speech-dispatcher:"
echo "       spd-conf"
echo
echo "  7. OpenRGB:"
echo "       Load 'personal_multicolor' profile"
echo
echo "  8. Browsers:"
echo "       Sign into Brave and Zen Browser"
echo
echo "  9. Warp Terminal:"
echo "       Sign in to account"
echo
echo " 10. Clawdbot:"
echo "       Verify token in ~/.clawdbot-clean/"
echo
echo " 11. Wallpaper:"
echo "       swww-daemon &"
echo "       ~/Scripts/bin/pick-wallpaper"
echo
echo " 12. Start Hyprland:"
echo "       uwsm start -- hyprland"
echo
echo "============================================================"
echo "  Setup complete! Log: $LOG_FILE"
echo "============================================================"
