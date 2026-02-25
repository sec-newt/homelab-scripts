#!/usr/bin/env python3
"""
Waybar custom module to display current audio sink
Returns JSON format for Waybar custom module
"""
import subprocess as sp
import json
import sys

def get_current_sink():
    try:
        output = str(sp.check_output("wpctl status", shell=True, encoding='utf-8'))
        lines = output.replace("├", "").replace("─", "").replace("│", "").replace("└", "").splitlines()

        # Get the index of the Sinks line as a starting point
        sinks_index = None
        for index, line in enumerate(lines):
            if "Sinks:" in line:
                sinks_index = index
                break

        # Find the default sink (marked with *)
        for line in lines[sinks_index + 1:]:
            if not line.strip():
                break
            if line.strip().startswith("*"):
                # Clean up the sink name - remove * and volume info
                sink_name = line.strip().replace("*", "").split("[vol:")[0].strip()
                # Remove ID number and clean up
                if "." in sink_name:
                    sink_name = sink_name.split(".", 1)[1].strip()
                # Remove "Analog" for cleaner display and truncate
                sink_name = sink_name.replace("Analog", "").strip()
                
                # Truncate for Waybar display
                if len(sink_name) > 20:
                    sink_name = sink_name[:17] + "..."
                
                return sink_name
        
        return "No Default"
    except:
        return "Error"

def main():
    sink_name = get_current_sink()
    
    # Waybar JSON format
    waybar_output = {
        "text": f"🔊 {sink_name}",
        "tooltip": f"Current Audio Sink: {sink_name}\nClick: Switch sink\nRight-click: Show current",
        "class": "audio-sink"
    }
    
    print(json.dumps(waybar_output))

if __name__ == "__main__":
    main()
