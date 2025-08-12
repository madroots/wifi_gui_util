#!/bin/bash

# Check if the script is being run with sudo
if [ "$EUID" -eq 0 ]; then
  echo "Error: This script should not be run with sudo directly."
  echo "It will handle running the application with elevated privileges internally."
  exit 1
fi

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"

# Run the application with pkexec, preserving environment variables for theme
pkexec env DISPLAY=$DISPLAY XAUTHORITY=$XAUTHORITY QT_QPA_PLATFORMTHEME=$QT_QPA_PLATFORMTHEME GTK_THEME=$GTK_THEME python3 "$SCRIPT_DIR/main.py"