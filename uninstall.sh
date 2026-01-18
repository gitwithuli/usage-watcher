#!/bin/bash
#
# Claude Code Usage Monitor - Uninstall Script
#

PLIST_NAME="com.claude.usage-monitor"
PLIST_PATH="$HOME/Library/LaunchAgents/${PLIST_NAME}.plist"

echo "=== Uninstalling Claude Usage Monitor ==="

# Stop the running app
pkill -f "claude_usage.py" 2>/dev/null || true

# Unload and remove LaunchAgent
if [ -f "$PLIST_PATH" ]; then
    launchctl unload "$PLIST_PATH" 2>/dev/null || true
    rm "$PLIST_PATH"
    echo "Removed auto-start configuration."
fi

echo ""
echo "Uninstall complete."
echo "You can delete the project folder manually if desired."
