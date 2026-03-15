#!/bin/bash
# calibre-import.sh — Stage downloaded books and import into Calibre library

set -euo pipefail

DOWNLOAD_DIR="/library/docker/Downloads/complete/Books"
IMPORT_DIR="/library/Books/.import"
CALIBRE_LIBRARY="/config/Calibre Library"
PROCESSED_LOG="/library/Books/.imported.log"
LOG_FILE="/library/Books/.import.log"
STATUS_FILE="/var/lib/calibre-import/status.json"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

write_status() {
    local status="$1"
    local last_count="$2"
    local total
    total=$(wc -l < "$PROCESSED_LOG" 2>/dev/null || echo 0)

    mkdir -p "$(dirname "$STATUS_FILE")"
    printf '{"status":"%s","last_run":"%s","last_count":%d,"total_imported":%d}\n' \
        "$status" \
        "$(date '+%Y-%m-%d %H:%M')" \
        "$last_count" \
        "$total" \
        > "$STATUS_FILE"
}

mkdir -p "$IMPORT_DIR"
touch "$PROCESSED_LOG"

new_count=0

# Process each book subdirectory
while IFS= read -r -d '' bookdir; do
    dirname=$(basename "$bookdir")

    if grep -qxF "$dirname" "$PROCESSED_LOG" 2>/dev/null; then
        continue
    fi

    log "Staging: $dirname"
    cp -r "$bookdir" "$IMPORT_DIR/"
    new_count=$((new_count + 1))

done < <(find "$DOWNLOAD_DIR" -mindepth 1 -maxdepth 1 -type d -print0)

# Also handle loose ebook/zip files at the top level
while IFS= read -r -d '' file; do
    filename=$(basename "$file")

    if grep -qxF "$filename" "$PROCESSED_LOG" 2>/dev/null; then
        continue
    fi

    log "Staging loose file: $filename"
    cp "$file" "$IMPORT_DIR/"
    new_count=$((new_count + 1))

done < <(find "$DOWNLOAD_DIR" -maxdepth 1 -type f \
    \( -iname "*.epub" -o -iname "*.mobi" -o -iname "*.azw3" \
       -o -iname "*.pdf" -o -iname "*.zip" \) -print0)

if [ "$new_count" -eq 0 ]; then
    log "No new books to import."
    write_status "idle" 0
    exit 0
fi

log "Importing $new_count item(s) into Calibre..."

if docker exec calibre calibredb add \
    --with-library "$CALIBRE_LIBRARY" \
    --recurse \
    --automerge ignore \
    /config/.import/; then

    # Record what was processed
    find "$DOWNLOAD_DIR" -mindepth 1 -maxdepth 1 -type d -printf '%f\n' >> "$PROCESSED_LOG"
    find "$DOWNLOAD_DIR" -maxdepth 1 -type f \
        \( -iname "*.epub" -o -iname "*.mobi" -o -iname "*.azw3" \
           -o -iname "*.pdf" -o -iname "*.zip" \) -printf '%f\n' >> "$PROCESSED_LOG"

    log "Done. $new_count item(s) imported successfully."
    write_status "ok" "$new_count"
else
    log "ERROR: calibredb add failed. Import dir left in place for inspection."
    write_status "error" 0
    exit 1
fi

# Clean up staging area
rm -rf "${IMPORT_DIR:?}"/*
