#!/usr/bin/env bash
# -------------------------------------------------
# Listen on org.freedesktop.Notifications and speak each toast.
# Parses D-Bus Notify args: app_name, app_icon, summary, body
# -------------------------------------------------

LOG="$HOME/.cache/dbus-notify-speak.log"
echo "=== dbus-notify-speak started $(date) ===" > "$LOG"

if ! pgrep -x speech-dispatcher >/dev/null; then
    speech-dispatcher -n >/dev/null 2>&1 &
    sleep 0.5
fi

parts=()
done=0

dbus-monitor --session "type='method_call',interface='org.freedesktop.Notifications'" |
while IFS= read -r line; do

    # New Notify call — reset state
    if [[ $line == *"member=Notify"* ]]; then
        parts=()
        done=0
        continue
    fi

    # Already processed this notification
    (( done )) && continue

    # array [ marks start of actions/hints — stop collecting strings
    if [[ $line == *"array ["* ]]; then
        done=1
        continue
    fi

    # Collect string arguments
    if [[ $line =~ string\ \"([^\"]*)\" ]]; then
        parts+=("${BASH_REMATCH[1]}")

        # Need 4 strings: app_name, app_icon, summary, body
        if (( ${#parts[@]} == 4 )); then
            app_name="${parts[0]}"
            summary="${parts[2]}"
            body="${parts[3]}"
            done=1

            # App-specific rules
            if [[ "${summary,,}" == "claude code" ]]; then
                if [[ "${body,,}" == *"permission"* || "${body,,}" == *"approval"* || "${body,,}" == *"waiting"* ]]; then
                    msg="Claude needs approval"
                else
                    msg="Claude"
                fi
            elif [[ "${app_name,,}" == *"proton"* || "${summary,,}" == *"proton"* ]]; then
                msg="Mail"
            else
                msg="$summary"
                [[ -n "$body" ]] && msg+=". $body"
            fi

            echo "Speaking: $msg" >> "$LOG"
            echo "  app=$app_name summary=$summary body=$body" >> "$LOG"
            spd-say "$msg"
        fi
    fi

done
