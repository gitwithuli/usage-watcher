#!/usr/bin/env python3
"""
Claude Code Usage Monitor - Menu Bar App
A simple macOS menu bar app to track Claude Code Pro/Max usage limits.
"""

import rumps
import subprocess
import requests
import json
import logging
import time
from datetime import datetime
from pathlib import Path

# Configuration
POLL_INTERVAL = 120  # seconds (2 minutes)
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds between retries
THRESHOLDS = {
    'warning': 0.70,
    'danger': 0.85,
    'critical': 0.95
}

# Setup logging
LOG_PATH = Path.home() / "Library/Logs/claude-usage-monitor.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_PATH),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)


class ClaudeUsageApp(rumps.App):
    def __init__(self):
        super().__init__("⏳", quit_button=None)

        # Menu items
        self.five_hour_item = rumps.MenuItem("5h Limit: --")
        self.weekly_item = rumps.MenuItem("Weekly: --")
        self.status_item = rumps.MenuItem("Status: Starting...")
        self.updated_item = rumps.MenuItem("Updated: --")

        self.menu = [
            self.five_hour_item,
            self.weekly_item,
            None,
            self.status_item,
            self.updated_item,
            None,
            rumps.MenuItem("Refresh Now", callback=self.manual_refresh),
            rumps.MenuItem("Quit", callback=rumps.quit_application),
        ]

        # State
        self.token = None
        self.notified_levels = set()
        self.consecutive_failures = 0
        self.last_known_usage = None  # Cache for graceful degradation
        self.token_refresh_attempts = 0

        log.info("Claude Usage Monitor starting...")

        # Start polling timer
        self.timer = rumps.Timer(self.safe_refresh, POLL_INTERVAL)
        self.timer.start()

        # Initial fetch
        self.safe_refresh(None)

    def get_token(self, force_refresh=False):
        """Read OAuth token from macOS Keychain with retry logic."""
        if self.token and not force_refresh:
            return self.token

        for attempt in range(MAX_RETRIES):
            try:
                result = subprocess.run(
                    ['security', 'find-generic-password',
                     '-s', 'Claude Code-credentials', '-w'],
                    capture_output=True, text=True, check=True, timeout=10
                )
                creds = json.loads(result.stdout.strip())
                oauth = creds.get('claudeAiOauth', {})
                token = oauth.get('accessToken')

                if token:
                    self.token = token
                    self.token_refresh_attempts = 0
                    log.info("Token retrieved successfully")
                    return self.token
                else:
                    log.warning("Token not found in credentials")

            except subprocess.TimeoutExpired:
                log.warning(f"Keychain access timeout (attempt {attempt + 1})")
            except subprocess.CalledProcessError as e:
                log.warning(f"Keychain access failed: {e}")
            except json.JSONDecodeError as e:
                log.warning(f"Failed to parse credentials: {e}")
            except Exception as e:
                log.error(f"Unexpected error getting token: {e}")

            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)

        # Only notify once per session about auth issues
        if self.token_refresh_attempts == 0:
            self.token_refresh_attempts += 1
            rumps.notification(
                "Claude Usage Monitor",
                "Authentication Required",
                "Run 'claude' in terminal first to authenticate."
            )
        return None

    def fetch_usage(self):
        """Fetch usage from Anthropic OAuth API with retry logic."""
        token = self.get_token()
        if not token:
            return None

        for attempt in range(MAX_RETRIES):
            try:
                resp = requests.get(
                    'https://api.anthropic.com/api/oauth/usage',
                    headers={
                        'Authorization': f'Bearer {token}',
                        'anthropic-beta': 'oauth-2025-04-20'
                    },
                    timeout=15
                )

                if resp.status_code == 401:
                    log.warning("Token expired, refreshing...")
                    self.token = None
                    token = self.get_token(force_refresh=True)
                    if not token:
                        return None
                    continue

                resp.raise_for_status()
                data = resp.json()

                # Cache successful response
                self.last_known_usage = data
                self.consecutive_failures = 0
                log.info(f"Usage fetched: 5h={data.get('five_hour', {}).get('utilization')}%, "
                        f"weekly={data.get('seven_day', {}).get('utilization')}%")
                return data

            except requests.exceptions.Timeout:
                log.warning(f"API timeout (attempt {attempt + 1})")
            except requests.exceptions.ConnectionError:
                log.warning(f"Connection error (attempt {attempt + 1})")
            except requests.exceptions.HTTPError as e:
                log.error(f"HTTP error: {e}")
                if e.response.status_code >= 500:
                    pass  # Server error, retry
                else:
                    return None  # Client error, don't retry
            except Exception as e:
                log.error(f"Unexpected error fetching usage: {e}")

            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)

        self.consecutive_failures += 1
        return None

    def safe_refresh(self, _):
        """Wrapper around refresh with exception handling."""
        try:
            self.refresh()
        except Exception as e:
            log.error(f"Refresh failed with exception: {e}")
            self.show_error_state(f"Error: {str(e)[:30]}")

    def refresh(self):
        """Update display and check thresholds."""
        usage = self.fetch_usage()

        if not usage:
            # Use cached data if available
            if self.last_known_usage and self.consecutive_failures < 5:
                log.info("Using cached usage data")
                usage = self.last_known_usage
                self.status_item.title = f"Status: Cached (retry {self.consecutive_failures})"
            else:
                self.show_error_state("Connection failed")
                return

        five_hour = usage.get('five_hour', {})
        weekly = usage.get('seven_day', {})

        five_pct = five_hour.get('utilization', 0) / 100
        week_pct = weekly.get('utilization', 0) / 100

        five_reset = self.format_reset(five_hour.get('resets_at'))
        week_reset = self.format_reset(weekly.get('resets_at'))

        # Update menu items
        self.five_hour_item.title = f"5h: {five_pct:.0%} used • resets {five_reset}"
        self.weekly_item.title = f"Weekly: {week_pct:.0%} used • resets {week_reset}"
        self.status_item.title = "Status: Connected"
        self.updated_item.title = f"Updated: {datetime.now().strftime('%H:%M')}"

        # Update menu bar
        self.title = self.get_title(five_pct, week_pct)

        # Check thresholds
        self.check_thresholds(five_pct, "5h limit")
        self.check_thresholds(week_pct, "Weekly limit")

    def show_error_state(self, message):
        """Show error state but keep last known values visible."""
        self.status_item.title = f"Status: {message}"
        self.updated_item.title = f"Last attempt: {datetime.now().strftime('%H:%M')}"

        if self.last_known_usage:
            # Keep showing last known values with warning indicator
            five_hour = self.last_known_usage.get('five_hour', {})
            weekly = self.last_known_usage.get('seven_day', {})
            five_pct = five_hour.get('utilization', 0) / 100
            week_pct = weekly.get('utilization', 0) / 100
            self.title = f"⚠️{int(five_pct*100)} {int(week_pct*100)}"
        else:
            self.title = "⚠️"

    def manual_refresh(self, _):
        """Manual refresh triggered by menu click."""
        self.title = "⏳"
        self.status_item.title = "Status: Refreshing..."
        self.consecutive_failures = 0  # Reset failure count on manual refresh
        self.safe_refresh(None)

    def get_icon(self, pct):
        """Return emoji icon based on usage percentage."""
        if pct >= THRESHOLDS['critical']:
            return "🔴"
        elif pct >= THRESHOLDS['danger']:
            return "🟠"
        elif pct >= THRESHOLDS['warning']:
            return "🟡"
        else:
            return "🟢"

    def get_title(self, five_pct, week_pct):
        """Return compact menu bar title with both indicators."""
        five_icon = self.get_icon(five_pct)
        week_icon = self.get_icon(week_pct)
        five_num = int(five_pct * 100)
        week_num = int(week_pct * 100)
        return f"{five_icon}{five_num} {week_icon}{week_num}"

    def check_thresholds(self, pct, label):
        """Send notifications at threshold crossings."""
        for level, threshold in THRESHOLDS.items():
            key = f"{label}_{level}"
            if pct >= threshold and key not in self.notified_levels:
                self.notified_levels.add(key)

                if level == 'critical':
                    title = "Usage Critical!"
                    message = f"You've used {pct:.0%} of your {label}. Consider pausing."
                elif level == 'danger':
                    title = "Usage High"
                    message = f"You've used {pct:.0%} of your {label}."
                else:
                    title = "Usage Warning"
                    message = f"You've reached {pct:.0%} of your {label}."

                rumps.notification("Claude Usage Monitor", title, message)
                log.info(f"Notification sent: {title} - {message}")

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
        except Exception as e:
            log.warning(f"Failed to parse reset time: {e}")
            return iso_time[:16] if len(iso_time) > 16 else iso_time


if __name__ == "__main__":
    try:
        ClaudeUsageApp().run()
    except Exception as e:
        log.critical(f"App crashed: {e}")
        raise
