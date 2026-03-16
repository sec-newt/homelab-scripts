#!/usr/bin/env python3

import subprocess

# Get current zoom factor directly without shell pipes
result = subprocess.run(["hyprctl", "getoption", "cursor:zoom_factor"], 
                       text=True, capture_output=True)

# Parse the output to extract the float value
for line in result.stdout.strip().split('\n'):
    if 'float' in line:
        zoom_level = float(line.split()[1])
        break

# Only decrease zoom if it's greater than 1
if zoom_level > 1:
    subprocess.run(["hyprctl", "keyword", "cursor:zoom_factor", str(zoom_level - 1)], 
                   capture_output=True)
