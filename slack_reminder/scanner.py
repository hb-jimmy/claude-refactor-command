"""Slack reminder client — creates reminders via the Slack API.

Usage:
    slack-remind "Do the thing" --time 2026-02-16T08:00:00-05:00
"""

import time as time_module
from datetime import datetime
from typing import Any, Dict, Optional

import requests


SLACK_API_BASE = "https://slack.com/api"


class ReminderError(Exception):
    """Raised when a Slack API call fails."""
    pass


class ReminderClient:
    """Creates Slack reminders via the API."""

    def __init__(self, token: str):
        self._session = requests.Session()
        self._session.headers.update({
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8",
        })

    def _request(
        self,
        method: str,
        json_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make a Slack API request with rate-limit handling."""
        url = f"{SLACK_API_BASE}/{method}"

        try:
            response = self._session.post(url, json=json_data)
        except requests.RequestException as e:
            raise ReminderError(f"Network error: {e}")

        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", "5"))
            print(f"  Rate limited, waiting {retry_after}s...")
            time_module.sleep(retry_after)
            return self._request(method, json_data)

        if not response.ok:
            raise ReminderError(
                f"HTTP error: {response.status_code} {response.reason}"
            )

        data = response.json()
        if not data.get("ok"):
            error_code = data.get("error", "unknown_error")
            raise ReminderError(f"Slack API error: {error_code}")

        return data

    def create_reminder(self, text: str, time_iso: str) -> bool:
        """Create a Slack reminder.

        Args:
            text: Reminder text (supports Slack mrkdwn).
            time_iso: ISO 8601 timestamp (e.g., 2026-02-16T08:00:00-05:00).

        Returns:
            True if created successfully.
        """
        try:
            unix_ts = int(datetime.fromisoformat(time_iso).timestamp())
        except (ValueError, OSError) as e:
            raise ReminderError(f"Could not parse time '{time_iso}': {e}")

        self._request("reminders.add", json_data={
            "text": text,
            "time": unix_ts,
        })
        return True
