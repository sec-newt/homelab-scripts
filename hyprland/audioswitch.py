#!/usr/bin/env python3
import subprocess as sp

def parse_wpctl_status():
    output = str(sp.check_output("wpctl status", shell=True, encoding='utf-8'))
    lines = output.replace("├", "").replace("─", "").replace("│", "").replace("└", "").splitlines()

    sinks_index = None
    for index, line in enumerate(lines):
        if "Sinks:" in line:
            sinks_index = index
            break

    sinks = []
    for line in lines[sinks_index + 1:]:
        if not line.strip():
            break
        sinks.append(line.strip())

    for index, sink in enumerate(sinks):
        sinks[index] = sink.split("[vol:")[0].strip()

    for index, sink in enumerate(sinks):
        if sink.startswith("*"):
            sinks[index] = sink.strip().replace("*", "").strip() + " - Default"

    sinks_dict = [{"sink_id": int(sink.split(".")[0]), "sink_name": sink.split(".")[1].strip()} for sink in sinks]
    return sinks_dict

def find_current(list):
    for i in range(len(list)):
        if list[i]['sink_name'].find("Default") >= 0:
            return list[i]['sink_name']

def switch_current(list):
    current_index = 0
    for i in range(len(list)):
        if list[i]['sink_name'].find("Default") >= 0:
            current_index = i
            break
    next_index = (current_index + 1) % len(list)
    return list[next_index]['sink_id']

sources = parse_wpctl_status()
sp.run(f"wpctl set-default {str(switch_current(sources))}", shell=True)

sources = parse_wpctl_status()
current = find_current(sources)
# Strip "- Default" suffix and clean up for display
display_name = current.replace("- Default", "").replace("Analog", "").strip()
# Remove leading ID number if present
if "." in display_name:
    display_name = display_name.split(".", 1)[1].strip()

sp.run(["notify-send", "-t", "2000", "-u", "normal", "Audio Output", f"Switched to: {display_name}"])
