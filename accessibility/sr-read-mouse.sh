#!/bin/bash
# sr-read-mouse.sh - OCR Screen Reader (Under Mouse)
#
# Usage: Run this script. It captures a region around the mouse cursor
# and speaks any text found. Good for quickly checking UI elements.

set -e

# Configuration
WIDTH=600
HEIGHT=200

# Ensure environment is set (for PIPER_MODEL, PATH, etc.)
source "$HOME/.bashrc" || true
export PATH="$HOME/Scripts/.venvs/tts/bin:$PATH"
export PIPER_MODEL="${PIPER_MODEL:-$HOME/.local/share/piper/voices/en_US/en_US-amy-medium.onnx}"
export PIPER_CONFIG="${PIPER_CONFIG:-$HOME/.local/share/piper/voices/en_US/en_US-amy-medium.onnx.json}"

# Temp files
IMG_FILE=$(mktemp --suffix=.png)
trap "rm -f $IMG_FILE" EXIT

# 1. Get Mouse Position
# hyprctl cursorpos returns "X, Y" (e.g., "37, 837")
# We remove the comma and read into variables
read X Y <<< $(hyprctl cursorpos | tr -d ',')

# Debug
echo "Mouse at X=$X Y=$Y" >> /tmp/ocr-debug.log

# Calculate geometry centered on mouse
# Ensure we don't have negative coordinates (grim handles off-screen right/bottom usually, but left/top needs care)
X_START=$((X - WIDTH / 2))
Y_START=$((Y - HEIGHT / 2))

if [ "$X_START" -lt 0 ]; then X_START=0; fi
if [ "$Y_START" -lt 0 ]; then Y_START=0; fi

GEOM="${X_START},${Y_START} ${WIDTH}x${HEIGHT}"
echo "Geometry: $GEOM" >> /tmp/ocr-debug.log

# 2. Capture
if ! grim -g "$GEOM" "$IMG_FILE"; then
    echo "Grim failed" >> /tmp/ocr-debug.log
    exit 1
fi

# 3. Extract text
# Pre-process image (remove alpha, grayscale, negate for dark mode, resize) to improve accuracy
TEXT=$(convert "$IMG_FILE" -alpha off -colorspace gray -negate -resize 200% -contrast-stretch 0 tiff:- | tesseract stdin stdout -l eng --psm 6 2>>/tmp/ocr-debug.log)
echo "OCR Text: $TEXT" >> /tmp/ocr-debug.log

TEXT=$(echo "$TEXT" | tr '\n' ' ' | sed 's/  */ /g')

# 4. Speak
if [ -n "$TEXT" ] && [ "$TEXT" != " " ]; then
    ~/Scripts/Accessibility/sr-term-stop.sh >/dev/null 2>&1 || true
    notify-send "OCR Mouse" "$(echo "$TEXT" | cut -c1-50)..."
    
    # Use tts_wrapper.py for better quality (Piper/OpenAI)
    # Log output to /tmp/tts-debug.log for troubleshooting
    echo "Speaking: $TEXT" >> /tmp/tts-debug.log
    ( echo "$TEXT" | ~/Scripts/bin/tts_wrapper.py >> /tmp/tts-debug.log 2>&1 ) &
else
    notify-send "OCR" "No text under mouse."
fi
