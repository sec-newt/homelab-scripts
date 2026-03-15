#!/bin/bash
# calibre-import.sh — Import downloaded ebooks into a Calibre Docker container
#
# Uses `docker cp` to stage files into the container, then runs `calibredb add`
# inside it. No shared volume mount required — works with any Calibre Docker setup.
#
# Configuration via environment variables or a .env file in the same directory:
#
#   CALIBRE_CONTAINER     Name of the running Calibre Docker container
#                         Default: calibre
#
#   DOWNLOAD_DIR          Directory containing book subdirectories or loose ebook files
#                         Required — no default
#
#   CALIBRE_LIBRARY_PATH  Path to the Calibre library inside the container
#                         Default: /config/Calibre Library
#
#   PROCESSED_LOG         File tracking already-imported items (prevents re-import)
#                         Default: ~/.local/share/calibre-import/processed.log
#
#   LOG_FILE              Path for the human-readable run log
#                         Default: ~/.local/share/calibre-import/import.log
#
#   STATUS_FILE           Path for a JSON status file (optional)
#                         When set, written after each run for dashboard integration
#                         Default: unset (disabled)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Load .env file if present alongside the script
if [[ -f "$SCRIPT_DIR/.env" ]]; then
    # shellcheck disable=SC1091
    set -a
    source "$SCRIPT_DIR/.env"
    set +a
fi

# ── Configuration ────────────────────────────────────────────────────────────

CALIBRE_CONTAINER="${CALIBRE_CONTAINER:-calibre}"
CALIBRE_LIBRARY_PATH="${CALIBRE_LIBRARY_PATH:-/config/Calibre Library}"
CONTAINER_STAGING="/tmp/calibre-import-staging"

DATA_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/calibre-import"
PROCESSED_LOG="${PROCESSED_LOG:-$DATA_DIR/processed.log}"
LOG_FILE="${LOG_FILE:-$DATA_DIR/import.log}"
STATUS_FILE="${STATUS_FILE:-}"

# ── Validation ───────────────────────────────────────────────────────────────

if [[ -z "${DOWNLOAD_DIR:-}" ]]; then
    echo "ERROR: DOWNLOAD_DIR is not set. Copy .env.example to .env and fill it in." >&2
    exit 1
fi

if [[ ! -d "$DOWNLOAD_DIR" ]]; then
    echo "ERROR: DOWNLOAD_DIR '$DOWNLOAD_DIR' does not exist or is not a directory." >&2
    exit 1
fi

# Restrict container name to safe characters — prevents command injection
if [[ ! "$CALIBRE_CONTAINER" =~ ^[a-zA-Z0-9_.-]+$ ]]; then
    echo "ERROR: CALIBRE_CONTAINER '$CALIBRE_CONTAINER' contains invalid characters." >&2
    exit 1
fi

# Verify the container is actually running before doing any work
if ! docker inspect --format '{{.State.Running}}' "$CALIBRE_CONTAINER" 2>/dev/null | grep -q true; then
    echo "ERROR: Container '$CALIBRE_CONTAINER' is not running." >&2
    exit 1
fi

# ── Helpers ──────────────────────────────────────────────────────────────────

mkdir -p "$(dirname "$PROCESSED_LOG")" "$(dirname "$LOG_FILE")"
touch "$PROCESSED_LOG"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

write_status() {
    [[ -z "$STATUS_FILE" ]] && return

    local run_status="$1"
    local last_count="$2"
    local total
    total=$(wc -l < "$PROCESSED_LOG" 2>/dev/null || echo 0)

    # Validate status value against known-good set
    case "$run_status" in
        ok|idle|error) ;;
        *) run_status="error" ;;
    esac

    mkdir -p "$(dirname "$STATUS_FILE")"
    printf '{"status":"%s","last_run":"%s","last_count":%d,"total_imported":%d}\n' \
        "$run_status" \
        "$(date '+%Y-%m-%d %H:%M')" \
        "$last_count" \
        "$total" \
        > "$STATUS_FILE"
}

# ── Collect new items ─────────────────────────────────────────────────────────

new_count=0
staged_items=()

# Book subdirectories (each folder = one release)
while IFS= read -r -d '' bookdir; do
    dirname=$(basename "$bookdir")
    grep -qxF "$dirname" "$PROCESSED_LOG" 2>/dev/null && continue
    staged_items+=("$bookdir")
    new_count=$((new_count + 1))
done < <(find "$DOWNLOAD_DIR" -mindepth 1 -maxdepth 1 -type d -print0)

# Loose ebook/zip files at the top level
while IFS= read -r -d '' file; do
    filename=$(basename "$file")
    grep -qxF "$filename" "$PROCESSED_LOG" 2>/dev/null && continue
    staged_items+=("$file")
    new_count=$((new_count + 1))
done < <(find "$DOWNLOAD_DIR" -maxdepth 1 -type f \
    \( -iname "*.epub" -o -iname "*.mobi" -o -iname "*.azw3" \
       -o -iname "*.pdf" -o -iname "*.zip" \) -print0)

if [[ "$new_count" -eq 0 ]]; then
    log "No new books to import."
    write_status "idle" 0
    exit 0
fi

log "Found $new_count new item(s) to import."

# ── Stage and import ──────────────────────────────────────────────────────────

# Create staging directory inside the container
docker exec "$CALIBRE_CONTAINER" mkdir -p "$CONTAINER_STAGING"

# Copy each item into the container
for item in "${staged_items[@]}"; do
    log "Staging: $(basename "$item")"
    docker cp "$item" "$CALIBRE_CONTAINER:$CONTAINER_STAGING/"
done

log "Running calibredb add..."

if docker exec "$CALIBRE_CONTAINER" calibredb add \
    --with-library "$CALIBRE_LIBRARY_PATH" \
    --recurse \
    --automerge ignore \
    "$CONTAINER_STAGING"; then

    # Record everything that was processed
    for item in "${staged_items[@]}"; do
        basename "$item" >> "$PROCESSED_LOG"
    done

    log "Done. $new_count item(s) imported successfully."
    write_status "ok" "$new_count"

else
    log "ERROR: calibredb add failed. Nothing recorded as processed."
    write_status "error" 0
    docker exec "$CALIBRE_CONTAINER" rm -rf "$CONTAINER_STAGING"
    exit 1
fi

# Clean up staging directory inside the container
docker exec "$CALIBRE_CONTAINER" rm -rf "$CONTAINER_STAGING"
