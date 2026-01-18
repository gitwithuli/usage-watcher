#!/usr/bin/env python3
"""
Claude Code Usage Monitor - Menu Bar App
A simple macOS menu bar app to track Claude Code Pro/Max usage limits.
"""

import rumps
import subprocess
import requests
import json
from datetime import datetime
from pathlib import Path

# Configuration
POLL_INTERVAL = 120  # seconds (2 minutes)
THRESHOLDS = {
    'warning': 0.70,   # Yellow indicator
    'danger': 0.85,    # Orange + notification
    'critical': 0.95   # Red + urgent notification
}


class ClaudeUsageApp(rumps.App):
    def __init__(self):
        super().__init__("⏳", quit_button=None)

        # Menu items
        self.five_hour_item = rumps.MenuItem("5h Limit: --")
        self.weekly_item = rumps.MenuItem("Weekly: --")
        self.updated_item = rumps.MenuItem("Updated: --")

        self.menu = [
            self.five_hour_item,
            self.weekly_item,
            None,  # separator
            self.updated_item,
            None,  # separator
            rumps.MenuItem("Refresh Now", callback=self.manual_refresh),
            rumps.MenuItem("Quit", callback=rumps.quit_application),
        ]

        self.token = None
        self.notified_levels = set()

        # Start polling timer
        self.timer = rumps.Timer(self.refresh, POLL_INTERVAL)
        self.timer.start()

        # Initial fetch
        self.refresh(None)

    def get_token(self):
        """Read OAuth token from macOS Keychain."""
        if self.token:
            return self.token
        try:
            result = subprocess.run(
                ['security', 'find-generic-password',
                 '-s', 'Claude Code-credentials', '-w'],
                capture_output=True, text=True, check=True
            )
            creds = json.loads(result.stdout.strip())
            # Token is nested under claudeAiOauth
            oauth = creds.get('claudeAiOauth', {})
            self.token = oauth.get('accessToken')
            return self.token
        except subprocess.CalledProcessError:
            rumps.notification(
                "Claude Usage Monitor",
                "Authentication Required",
                "Run 'claude' in terminal first to authenticate."
            )
            return None
        except json.JSONDecodeError:
            rumps.notification(
                "Claude Usage Monitor",
                "Credential Error",
                "Could not parse credentials from keychain."
            )
            return None
        except Exception as e:
            return None

    def fetch_usage(self):
        """Fetch usage from Anthropic OAuth API."""
        token = self.get_token()
        if not token:
            return None
        try:
            resp = requests.get(
                'https://api.anthropic.com/api/oauth/usage',
                headers={
                    'Authorization': f'Bearer {token}',
                    'anthropic-beta': 'oauth-2025-04-20'
                },
                timeout=10
            )
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                # Token expired, clear cache to retry
                self.token = None
                rumps.notification(
                    "Claude Usage Monitor",
                    "Token Expired",
                    "Re-authenticate by running 'claude' in terminal."
                )
            return None
        except requests.exceptions.RequestException:
            return None

    def refresh(self, _):
        """Update display and check thresholds."""
        usage = self.fetch_usage()
        if not usage:
            self.title = "⚠️"
            return

        five_hour = usage.get('five_hour', {})
        weekly = usage.get('seven_day', {})

        # API returns 0-100, convert to 0-1 for display
        five_pct = five_hour.get('utilization', 0) / 100
        week_pct = weekly.get('utilization', 0) / 100

        # Format reset times
        five_reset = self.format_reset(five_hour.get('resets_at'))
        week_reset = self.format_reset(weekly.get('resets_at'))

        # Update menu items
        self.five_hour_item.title = f"5h: {five_pct:.0%} used • resets {five_reset}"
        self.weekly_item.title = f"Weekly: {week_pct:.0%} used • resets {week_reset}"
        self.updated_item.title = f"Updated: {datetime.now().strftime('%H:%M')}"

        # Update icon based on highest usage
        max_usage = max(five_pct, week_pct)
        self.title = self.get_icon(max_usage, five_pct)

        # Check thresholds and notify
        self.check_thresholds(five_pct, "5h limit")
        self.check_thresholds(week_pct, "Weekly limit")

    def manual_refresh(self, _):
        """Manual refresh triggered by menu click."""
        self.title = "⏳"
        self.refresh(None)

    def get_icon(self, max_pct, five_pct):
        """Return menu bar title based on usage percentage."""
        if max_pct >= THRESHOLDS['critical']:
            icon = "🔴"
        elif max_pct >= THRESHOLDS['danger']:
            icon = "🟠"
        elif max_pct >= THRESHOLDS['warning']:
            icon = "🟡"
        else:
            icon = "🟢"

        # Show percentage next to icon
        return f"{icon} {five_pct:.0%}"

    def check_thresholds(self, pct, label):
        """Send notifications at threshold crossings."""
        for level, threshold in THRESHOLDS.items():
            key = f"{label}_{level}"
            if pct >= threshold and key not in self.notified_levels:
                self.notified_levels.add(key)

                if level == 'critical':
                    title = "⚠️ Usage Critical!"
                    message = f"You've used {pct:.0%} of your {label}. Consider pausing."
                elif level == 'danger':
                    title = "Usage High"
                    message = f"You've used {pct:.0%} of your {label}."
                else:
                    title = "Usage Warning"
                    message = f"You've reached {pct:.0%} of your {label}."

                rumps.notification("Claude Usage Monitor", title, message)

        # Reset notifications when usage drops (after reset window)
        if pct < THRESHOLDS['warning']:
            self.notified_levels = {
                k for k in self.notified_levels
                if not k.startswith(label)
            }

    def format_reset(self, iso_time):
        """Format reset time as relative string."""
        if not iso_time:
            return "unknown"
        try:
            reset = datetime.fromisoformat(iso_time.replace('Z', '+00:00'))
            now = datetime.now(reset.tzinfo)
            diff = reset - now
            total_seconds = int(diff.total_seconds())

            if total_seconds < 0:
                return "soon"

            hours, remainder = divmod(total_seconds, 3600)
            minutes = remainder // 60

            if hours > 24:
                days = hours // 24
                return f"in {days}d"
            elif hours > 0:
                return f"in {hours}h {minutes}m"
            else:
                return f"in {minutes}m"
        except Exception:
            return iso_time[:16] if len(iso_time) > 16 else iso_time


if __name__ == "__main__":
    ClaudeUsageApp().run()
