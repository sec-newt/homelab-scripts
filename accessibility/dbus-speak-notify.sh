#!/usr/bin/env bash
# -------------------------------------------------
# Listen on org.freedesktop.Notifications and speak each toast.
# -------------------------------------------------

# Log file – handy for debugging with a screen‑reader
LOG="$HOME/.cache/dbus-notify-speak.log"
echo "=== dbus‑notify‑speak started $(date) ===" >"$LOG"

# Ensure the speech synthesiser is running
if ! pgrep -x speech-dispatcher >/dev/null; then
    speech-dispatcher -n >/dev/null 2>&1 &
    sleep 0.5
fi

# Monitor the D‑Bus for the "Notify" method call
dbus-monitor --session "type='method_call',interface='org.freedesktop.Notifications'" |
while IFS= read -r line; do
    # Collect the three string arguments: app name, summary, body
    if [[ $line =~ string\ \"([^\"]*)\" ]]; then
        parts+=("${BASH_REMATCH[1]}")
        if (( ${#parts[@]} == 3 )); then
            summary="${parts[1]}"   # second string = title
            body="${parts[2]}"      # third string = body (may be empty)

            # Build a concise spoken message
            msg="Notification: $summary"
            [[ -n $body ]] && msg+=". $body"

            echo "Speaking: $msg" >>"$LOG"
            spd-say "$msg"
            parts=()   # reset for the next notification
        fi
    fi
done