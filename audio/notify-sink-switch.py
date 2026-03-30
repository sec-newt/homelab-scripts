#!/usr/bin/env python3
"""
notify-sink-switch.py — Pick which audio sink a systemd user service uses.

Uses fuzzel (or any dmenu-compatible launcher) to select from available
PipeWire/PulseAudio sinks, updates the PULSE_SINK environment variable in
a systemd user service file, then restarts the service.

Designed for services that need a fixed audio output independent of the
system default sink (e.g. a TTS notification service that should stay on
headphones while other audio switches to speakers).

Usage:
  notify-sink-switch.py [--service NAME] [--service-file PATH] [--launcher CMD]

Options:
  --service      Systemd user service name (default: dbus-notify-speak.service)
  --service-file Path to the .service file
                 (default: ~/.config/systemd/user/<service>)
  --launcher     dmenu-compatible launcher command (default: fuzzel --dmenu)

Requirements:
  - pactl (PipeWire or PulseAudio)
  - systemctl --user
  - fuzzel or another dmenu-compatible launcher
"""

import argparse
import subprocess as sp
import sys
import re
from pathlib import Path


def get_sinks() -> list[dict]:
    """Return list of sinks with alsa name and friendly description from pactl."""
    output = sp.check_output(["pactl", "list", "sinks"], encoding="utf-8")
    sinks = []
    current_name = None
    for line in output.splitlines():
        stripped = line.strip()
        if stripped.startswith("Name:"):
            current_name = stripped.split(":", 1)[1].strip()
        elif stripped.startswith("Description:") and current_name:
            label = stripped.split(":", 1)[1].strip()
            sinks.append({"name": current_name, "label": label})
            current_name = None
    return sinks


def get_current_sink(service_file: Path) -> str:
    """Return the current PULSE_SINK value from the service file."""
    if not service_file.exists():
        return ""
    for line in service_file.read_text().splitlines():
        if line.strip().startswith("Environment=PULSE_SINK="):
            return line.strip().split("=", 2)[-1]
    return ""


def pick_sink(sinks: list[dict], current: str, launcher: list[str]) -> dict | None:
    """Show dmenu picker and return chosen sink, or None if cancelled."""
    lines = []
    for s in sinks:
        marker = " [current]" if s["name"] == current else ""
        lines.append(f"{s['label']}{marker}")

    result = sp.run(
        launcher + ["--prompt=Notification Sink: "],
        input="\n".join(lines),
        capture_output=True,
        encoding="utf-8",
    )

    if result.returncode != 0 or not result.stdout.strip():
        return None

    chosen_label = result.stdout.strip().replace(" [current]", "")
    for s in sinks:
        if s["label"] == chosen_label:
            return s
    return None


def update_service(service_file: Path, sink_name: str) -> None:
    """Update or insert PULSE_SINK in the service file."""
    text = service_file.read_text()
    new_line = f"Environment=PULSE_SINK={sink_name}"

    if "Environment=PULSE_SINK=" in text:
        text = re.sub(r"Environment=PULSE_SINK=\S*", new_line, text)
    else:
        # Insert after the last Environment= line in the [Service] section
        text = re.sub(r"(Environment=[^\n]+\n)(?!Environment=)", rf"\1{new_line}\n", text, count=1)

    service_file.write_text(text)


def restart_service(service_name: str) -> None:
    sp.run(["systemctl", "--user", "daemon-reload"], check=True)
    sp.run(["systemctl", "--user", "restart", service_name], check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--service", default="dbus-notify-speak.service",
                        help="Systemd user service name (default: dbus-notify-speak.service)")
    parser.add_argument("--service-file", default=None,
                        help="Path to .service file (default: ~/.config/systemd/user/<service>)")
    parser.add_argument("--launcher", default="fuzzel --dmenu",
                        help="dmenu-compatible launcher command (default: 'fuzzel --dmenu')")
    args = parser.parse_args()

    service_name = args.service
    service_file = Path(args.service_file) if args.service_file else \
        Path.home() / ".config/systemd/user" / service_name
    launcher = args.launcher.split()

    sinks = get_sinks()
    if not sinks:
        sp.run(["notify-send", "-u", "critical", "Notify Sink", "No audio sinks found"])
        sys.exit(1)

    current = get_current_sink(service_file)
    chosen = pick_sink(sinks, current, launcher)

    if chosen is None:
        sys.exit(0)

    update_service(service_file, chosen["name"])
    restart_service(service_name)

    sp.run([
        "notify-send", "-t", "2000", "-u", "normal",
        "Notification Sink", f"Now using: {chosen['label']}"
    ])


if __name__ == "__main__":
    main()
