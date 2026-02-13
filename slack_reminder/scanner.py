"""Slack channel scanner — finds action-item messages and creates reminders.

Scans a Slack channel for messages formatted with action-item markers,
creates Slack reminders for unprocessed messages, and marks them with
a checkmark reaction.

Expected message format:
    📋 Action item text here
    👤 Person name
    ⏰ 2026-02-14T08:00:00-05:00
    📝 Source: ...
"""

import re
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests


SLACK_API_BASE = "https://slack.com/api"

CHECKMARK_EMOJI = "white_check_mark"


class ScannerError(Exception):
    """Raised when a Slack API call fails."""
    pass


@dataclass
class ActionMessage:
    """A parsed action-item message from Slack."""
    timestamp: str
    action_text: str
    person: str
    reminder_time_iso: str
    source: str
    raw_text: str


@dataclass
class ProcessingStats:
    """Results from processing a channel."""
    messages_scanned: int
    action_messages_found: int
    already_processed: int
    reminders_created: int
    errors: int


class ReminderScanner:
    """Scans a Slack channel for action items and creates reminders."""

    def __init__(self, token: str):
        self._session = self._create_session(token)

    def _create_session(self, token: str) -> requests.Session:
        session = requests.Session()
        session.headers.update({
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8",
        })
        return session

    def _request(
        self,
        method: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make a Slack API request with rate-limit handling."""
        url = f"{SLACK_API_BASE}/{method}"

        try:
            if json_data:
                response = self._session.post(url, json=json_data, params=params)
            else:
                response = self._session.get(url, params=params)
        except requests.RequestException as e:
            raise ScannerError(f"Network error: {e}")

        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", "5"))
            print(f"  Rate limited, waiting {retry_after}s...")
            time.sleep(retry_after)
            return self._request(method, params, json_data)

        if not response.ok:
            raise ScannerError(
                f"HTTP error: {response.status_code} {response.reason}"
            )

        data = response.json()
        if not data.get("ok"):
            error_code = data.get("error", "unknown_error")
            raise ScannerError(f"Slack API error: {error_code}")

        return data

    def get_channel_messages(self, channel_id: str) -> List[ActionMessage]:
        """Fetch messages from a channel and parse action items.

        Returns only messages that match the action-item format.
        """
        messages: List[ActionMessage] = []
        cursor = None

        while True:
            params: Dict[str, Any] = {
                "channel": channel_id,
                "limit": 100,
            }
            if cursor:
                params["cursor"] = cursor

            data = self._request("conversations.history", params=params)

            for msg in data.get("messages", []):
                parsed = self._parse_action_message(msg)
                if parsed:
                    messages.append(parsed)

            cursor = (
                data.get("response_metadata", {}).get("next_cursor")
            )
            if not cursor:
                break

            time.sleep(1)

        return messages

    def _parse_action_message(self, msg: Dict[str, Any]) -> Optional[ActionMessage]:
        """Parse a Slack message into an ActionMessage if it matches the format."""
        text = msg.get("text", "")
        ts = msg.get("ts", "")

        action_match = re.search(r"(?:📋|:clipboard:)\s*(.+)", text)
        time_match = re.search(r"(?:⏰|:alarm_clock:)\s*(\S+)", text)

        if not action_match or not time_match:
            return None

        person_match = re.search(r"(?:👤|:bust_in_silhouette:)\s*(.+)", text)
        source_match = re.search(r"(?:📝|:memo:)\s*(.+)", text)

        return ActionMessage(
            timestamp=ts,
            action_text=action_match.group(1).strip(),
            person=person_match.group(1).strip() if person_match else "",
            reminder_time_iso=time_match.group(1).strip(),
            source=source_match.group(1).strip() if source_match else "",
            raw_text=text,
        )

    def has_checkmark(self, channel_id: str, timestamp: str) -> bool:
        """Check if a message already has a checkmark reaction."""
        try:
            data = self._request("reactions.get", params={
                "channel": channel_id,
                "timestamp": timestamp,
                "full": True,
            })
        except ScannerError:
            return False

        for reaction in data.get("message", {}).get("reactions", []):
            if reaction.get("name") == CHECKMARK_EMOJI:
                return True

        return False

    def create_reminder(self, text: str, time_iso: str) -> bool:
        """Create a Slack reminder.

        Args:
            text: Reminder text.
            time_iso: ISO 8601 timestamp for when to trigger.

        Returns:
            True if created successfully.
        """
        try:
            unix_ts = int(datetime.fromisoformat(time_iso).timestamp())
        except (ValueError, OSError) as e:
            print(f"  Warning: Could not parse time '{time_iso}': {e}")
            return False

        try:
            self._request("reminders.add", json_data={
                "text": text,
                "time": unix_ts,
            })
            return True
        except ScannerError as e:
            print(f"  Warning: Failed to create reminder: {e}")
            return False

    def add_checkmark(self, channel_id: str, timestamp: str) -> bool:
        """Add a checkmark reaction to a message."""
        try:
            self._request("reactions.add", json_data={
                "channel": channel_id,
                "name": CHECKMARK_EMOJI,
                "timestamp": timestamp,
            })
            return True
        except ScannerError as e:
            # already_reacted is fine
            if "already_reacted" in str(e):
                return True
            print(f"  Warning: Failed to add checkmark: {e}")
            return False

    def process_channel(
        self, channel_id: str, dry_run: bool = False
    ) -> ProcessingStats:
        """Scan channel, create reminders for unprocessed messages, add checkmarks.

        Args:
            channel_id: Slack channel ID to scan.
            dry_run: If True, don't create reminders or add reactions.

        Returns:
            ProcessingStats with results.
        """
        print(f"Scanning channel {channel_id}...")

        messages = self.get_channel_messages(channel_id)
        stats = ProcessingStats(
            messages_scanned=len(messages),
            action_messages_found=len(messages),
            already_processed=0,
            reminders_created=0,
            errors=0,
        )

        for msg in messages:
            time.sleep(1)

            if self.has_checkmark(channel_id, msg.timestamp):
                stats.already_processed += 1
                if not dry_run:
                    print(f"  Skipped (already ✅): {msg.action_text[:60]}")
                continue

            reminder_text = f"{msg.action_text} (👤 {msg.person})" if msg.person else msg.action_text

            if dry_run:
                print(f"  Would create reminder: {reminder_text}")
                print(f"    Time: {msg.reminder_time_iso}")
                stats.reminders_created += 1
                continue

            print(f"  Creating reminder: {reminder_text}")
            if self.create_reminder(reminder_text, msg.reminder_time_iso):
                stats.reminders_created += 1
                time.sleep(1)
                self.add_checkmark(channel_id, msg.timestamp)
            else:
                stats.errors += 1

        return stats
