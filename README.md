# Claude Code Usage Monitor

A minimal macOS menu bar app to track your Claude Code Pro/Max usage limits.

![Menu Bar](https://img.shields.io/badge/macOS-Menu%20Bar-blue) ![Python](https://img.shields.io/badge/Python-3.8+-green) ![License](https://img.shields.io/badge/License-MIT-yellow)

## Features

- 🟢🟡🟠🔴 Color-coded usage indicator in menu bar
- Shows both 5-hour and weekly usage: `🟢4 🟢34`
- Displays reset times ("resets in 2h 34m")
- macOS notifications at 70%, 85%, and 95% usage
- Auto-retry on connection failures
- Caches last known values for reliability
- Auto-starts at login (optional)

## Prerequisites

**You must have Claude Code CLI installed and authenticated first.**

```bash
# Install Claude Code (if not already installed)
npm install -g @anthropic-ai/claude-code

# Authenticate (opens browser for OAuth)
claude
```

This creates the credentials in your macOS Keychain that the Usage Monitor reads.

## Installation

### Option 1: Download Pre-built App (Easiest)

1. Download `Claude.Usage.Monitor.app.zip` from [Releases](https://github.com/gitwithuli/usage-watcher/releases)
2. Unzip and drag to `/Applications`
3. Double-click to run

### Option 2: Build from Source

```bash
# Clone the repo
git clone https://github.com/gitwithuli/usage-watcher.git
cd usage-watcher

# Run setup (installs dependencies, optionally configures auto-start)
./setup.sh
```

### Option 3: Build Standalone App

```bash
# Clone and setup
git clone https://github.com/gitwithuli/usage-watcher.git
cd usage-watcher

# Create venv and install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt pyinstaller

# Build the app
pyinstaller "Claude Usage Monitor.spec" --noconfirm

# Install to Applications
cp -r "dist/Claude Usage Monitor.app" /Applications/
```

## First Run

1. Make sure you've authenticated Claude Code first: `claude`
2. Launch the app
3. Grant Keychain access when prompted (click "Allow" or "Always Allow")
4. Check your menu bar for the usage indicator

**If you see ⚠️**: Run `claude` in terminal to authenticate, then click "Refresh Now" in the app menu.

## Usage

| Icon | Meaning |
|------|---------|
| 🟢4 🟢12 | 5h: 4%, Weekly: 12% (healthy) |
| 🟡72 🟢15 | 5h: 72% warning, Weekly: 15% |
| 🟠88 🟡75 | 5h: 88% high, Weekly: 75% warning |
| 🔴96 🟠85 | Critical usage levels |
| ⚠️ | Not authenticated or connection error |

Click the menu bar icon to see:
- Exact percentages with reset times
- Connection status
- Last update time
- Manual refresh option

## Auto-Start at Login

**Option A: System Settings**
1. System Settings → General → Login Items
2. Click "+" under "Open at Login"
3. Select "Claude Usage Monitor" from Applications

**Option B: Command Line**
```bash
# Create LaunchAgent
cat > ~/Library/LaunchAgents/com.claude.usage-monitor.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.claude.usage-monitor</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/open</string>
        <string>-a</string>
        <string>/Applications/Claude Usage Monitor.app</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
EOF

# Enable it
launchctl load ~/Library/LaunchAgents/com.claude.usage-monitor.plist
```

## Configuration

Edit `claude_usage.py` to customize:

```python
POLL_INTERVAL = 120  # seconds between updates (default: 2 min)
THRESHOLDS = {
    'warning': 0.70,   # Yellow at 70%
    'danger': 0.85,    # Orange at 85%
    'critical': 0.95   # Red at 95%
}
```

## Troubleshooting

### "Authentication Required" notification
Run `claude` in terminal and complete the OAuth flow.

### Repeated Keychain prompts
Click "Always Allow" instead of just "Allow" when prompted.

### App shows ⚠️ constantly
1. Check internet connection
2. Re-authenticate: `claude`
3. Check logs: `cat ~/Library/Logs/claude-usage-monitor.log`

### Two instances running
Quit one from the menu bar (click icon → Quit).

## Uninstall

```bash
# Stop the app
pkill -f "Claude Usage Monitor"

# Remove auto-start
launchctl unload ~/Library/LaunchAgents/com.claude.usage-monitor.plist
rm ~/Library/LaunchAgents/com.claude.usage-monitor.plist

# Remove app
rm -rf "/Applications/Claude Usage Monitor.app"
```

## How It Works

1. Reads OAuth token from macOS Keychain (`Claude Code-credentials`)
2. Calls Anthropic's usage API every 2 minutes
3. Displays color-coded usage in menu bar
4. Sends macOS notifications at threshold crossings

The app uses the same authentication as Claude Code CLI - no separate login needed.

## Privacy

- No data is collected or sent anywhere except to Anthropic's API
- Credentials are read from your local Keychain (created by Claude Code)
- All processing happens locally on your machine

## Credits

Built as a lightweight alternative to [CodexBar](https://github.com/steipete/CodexBar) for those who only need Claude Code tracking.

## License

MIT
