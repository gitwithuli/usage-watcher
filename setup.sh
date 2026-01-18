#!/bin/bash
#
# Claude Code Usage Monitor - Setup Script
# This script installs dependencies and optionally sets up auto-start at login.
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLIST_NAME="com.claude.usage-monitor"
PLIST_PATH="$HOME/Library/LaunchAgents/${PLIST_NAME}.plist"

echo "=== Claude Code Usage Monitor Setup ==="
echo ""

# Check Python 3
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed."
    echo "Install it via: brew install python3"
    exit 1
fi

PYTHON_PATH=$(which python3)
echo "Using Python: $PYTHON_PATH"

# Create virtual environment
echo ""
echo "Creating virtual environment..."
python3 -m venv "$SCRIPT_DIR/venv"
source "$SCRIPT_DIR/venv/bin/activate"

# Install dependencies
echo "Installing dependencies..."
pip install --quiet --upgrade pip
pip install --quiet -r "$SCRIPT_DIR/requirements.txt"

echo "Dependencies installed."

# Make main script executable
chmod +x "$SCRIPT_DIR/claude_usage.py"

# Ask about auto-start
echo ""
read -p "Start automatically at login? (y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Create LaunchAgent plist
    cat > "$PLIST_PATH" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>${PLIST_NAME}</string>
    <key>ProgramArguments</key>
    <array>
        <string>${SCRIPT_DIR}/venv/bin/python</string>
        <string>${SCRIPT_DIR}/claude_usage.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
    <key>StandardOutPath</key>
    <string>${HOME}/Library/Logs/claude-usage-monitor.log</string>
    <key>StandardErrorPath</key>
    <string>${HOME}/Library/Logs/claude-usage-monitor.log</string>
</dict>
</plist>
EOF

    # Load the LaunchAgent
    launchctl unload "$PLIST_PATH" 2>/dev/null || true
    launchctl load "$PLIST_PATH"

    echo "Auto-start enabled. Will launch at login."
fi

echo ""
echo "=== Setup Complete ==="
echo ""
echo "To run now:  $SCRIPT_DIR/venv/bin/python $SCRIPT_DIR/claude_usage.py"
echo "To stop:     Click the menu bar icon → Quit"
echo ""

# Ask to start now
read -p "Start the app now? (y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Starting Claude Usage Monitor..."
    nohup "$SCRIPT_DIR/venv/bin/python" "$SCRIPT_DIR/claude_usage.py" > /dev/null 2>&1 &
    echo "Running! Check your menu bar for the indicator."
fi
