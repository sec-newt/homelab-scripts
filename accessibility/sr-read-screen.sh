#!/bin/bash
# sr-read-screen.sh - OCR Screen Reader (Interactive Selection)
# 
# Usage: Run this script (bound to a key). Select an area on screen.
# The script will OCR the text and speak it using tts_wrapper.py.
#
# Dependencies: grim, slurp, tesseract, tts_wrapper.py

set -e

# Ensure environment is set
source "$HOME/.bashrc" || true
export PATH="$HOME/Scripts/.venvs/tts/bin:$PATH"
export PIPER_MODEL="${PIPER_MODEL:-$HOME/.local/share/piper/voices/en_US/en_US-amy-medium.onnx}"
export PIPER_CONFIG="${PIPER_CONFIG:-$HOME/.local/share/piper/voices/en_US/en_US-amy-medium.onnx.json}"

# Temp files
IMG_FILE=$(mktemp --suffix=.png)
trap "rm -f $IMG_FILE" EXIT

# 1. Select area (slurp) and capture (grim)
# We use notify-send to give feedback
# notify-send -t 1000 "OCR" "Select area to read..."

if ! grim -g "$(slurp)" "$IMG_FILE"; then
    # User cancelled
    exit 0
fi

# 2. Extract text with Tesseract
# -l eng (English)
# psm 6 (Assume a single uniform block of text)
# 3. Pre-process image to improve accuracy
# First, remove alpha (transparency) and convert to grayscale
# This ensures we are analyzing the actual visible brightness
convert "$IMG_FILE" -alpha off -colorspace gray "$IMG_FILE"

# Detect background brightness (0.0 to 1.0)
MEAN=$(convert "$IMG_FILE" -format "%[fx:mean]" info:)

# If mean < 0.5 (dark background), negate to get black text on white
if [ "$(echo "$MEAN < 0.5" | bc)" -eq 1 ]; then
    PARAM_NEGATE="-negate"
else
    PARAM_NEGATE=""
fi

# Process: Negate (if needed) -> Resize -> Threshold -> Add Border
TEXT=$(convert "$IMG_FILE" $PARAM_NEGATE -resize 300% -contrast-stretch 0 -bordercolor White -border 20x20 tiff:- | tesseract stdin stdout -l eng --psm 6 2>>/tmp/ocr-debug.log)
echo "Screen OCR Text: $TEXT" >> /tmp/ocr-debug.log

# Clean up text (remove excessive newlines/garbage)
TEXT=$(echo "$TEXT" | tr '\n' ' ' | sed 's/  */ /g')

# 3. Speak
if [ -n "$TEXT" ] && [ "$TEXT" != " " ]; then
    # Stop previous speech
    ~/Scripts/Accessibility/sr-term-stop.sh >/dev/null 2>&1 || true
    
    notify-send "OCR Reading" "$(echo "$TEXT" | cut -c1-50)..."
    
    # Use tts_wrapper.py for better quality (Piper/OpenAI)
    # Log output to /tmp/tts-debug.log for troubleshooting
    echo "Speaking: $TEXT" >> /tmp/tts-debug.log
    ( echo "$TEXT" | ~/Scripts/bin/tts_wrapper.py >> /tmp/tts-debug.log 2>&1 ) &
else
    notify-send "OCR" "No text detected."
fi
