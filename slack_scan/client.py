"""Slack API client for reading channel history.

Fetches messages, thread replies, resolves user names, and constructs
permalinks. Designed to output structured JSON for analysis by Claude.
"""

import json
import re
import time as time_module
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests


SLACK_API_BASE = "https://slack.com/api"
USERS_CACHE_PATH = Path.home() / ".slack-users.json"


class ScanError(Exception):
    """Raised when a Slack API call fails."""
    pass


class HistoryClient:
    """Reads Slack channel history with thread support."""

    def __init__(self, token: str):
        self._session = requests.Session()
        self._session.headers.update({
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8",
        })
        self._team_domain: Optional[str] = None
        self._user_cache: Dict[str, str] = {}

    def _request(
        self,
        method: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make a Slack API GET request with rate-limit handling."""
        url = f"{SLACK_API_BASE}/{method}"

        try:
            response = self._session.get(url, params=params)
        except requests.RequestException as e:
            raise ScanError(f"Network error: {e}")

        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", "5"))
            print(f"  Rate limited, waiting {retry_after}s...", flush=True)
            time_module.sleep(retry_after)
            return self._request(method, params)

        if not response.ok:
            raise ScanError(
                f"HTTP error: {response.status_code} {response.reason}"
            )

        data = response.json()
        if not data.get("ok"):
            error_code = data.get("error", "unknown_error")
            raise ScanError(f"Slack API error: {error_code}")

        return data

    # -- Team / permalink helpers ------------------------------------------

    def _get_team_domain(self) -> str:
        """Get the workspace domain for constructing permalinks."""
        if self._team_domain:
            return self._team_domain

        data = self._request("auth.test")
        url = data.get("url", "")
        if url:
            self._team_domain = url.replace("https://", "").rstrip("/")
        else:
            self._team_domain = "slack.com"
        return self._team_domain

    def _make_permalink(
        self,
        channel_id: str,
        ts: str,
        thread_ts: Optional[str] = None,
    ) -> str:
        """Construct a Slack permalink from channel ID and timestamp."""
        domain = self._get_team_domain()
        ts_clean = ts.replace(".", "")
        url = f"https://{domain}/archives/{channel_id}/p{ts_clean}"
        if thread_ts and thread_ts != ts:
            url += f"?thread_ts={thread_ts}&cid={channel_id}"
        return url

    # -- User resolution ---------------------------------------------------

    def _load_user_cache(self) -> None:
        """Load user display names from cached slack-users.json."""
        if self._user_cache:
            return

        if USERS_CACHE_PATH.exists():
            try:
                with open(USERS_CACHE_PATH, "r") as f:
                    raw = json.load(f)
                # Handle both {"users": [...]} wrapper and bare [...]
                if isinstance(raw, dict):
                    users = raw.get("users", [])
                elif isinstance(raw, list):
                    users = raw
                else:
                    users = []
                for user in users:
                    if not isinstance(user, dict):
                        continue
                    uid = user.get("id") or user.get("account_id", "")
                    name = (
                        user.get("real_name")
                        or user.get("display_name")
                        or user.get("name", "")
                    )
                    if uid and name:
                        self._user_cache[uid] = name
            except (json.JSONDecodeError, OSError):
                pass

    def _resolve_user(self, user_id: str) -> str:
        """Resolve a user ID to a display name."""
        self._load_user_cache()

        if user_id in self._user_cache:
            return self._user_cache[user_id]

        try:
            data = self._request("users.info", params={"user": user_id})
            user = data.get("user", {})
            name = (
                user.get("real_name")
                or user.get("profile", {}).get("display_name")
                or user.get("name", user_id)
            )
            self._user_cache[user_id] = name
            return name
        except ScanError:
            return user_id

    def _resolve_text(self, text: str) -> str:
        """Replace <@U123> mentions and <#C123|name> refs with readable text."""
        text = re.sub(
            r"<@(U[A-Z0-9]+)>",
            lambda m: f"@{self._resolve_user(m.group(1))}",
            text,
        )
        text = re.sub(r"<#[A-Z0-9]+\|([^>]+)>", r"#\1", text)
        return text

    # -- Channel info ------------------------------------------------------

    def get_channel_info(self, channel_id: str) -> Dict[str, str]:
        """Get channel name and basic info."""
        try:
            data = self._request(
                "conversations.info", params={"channel": channel_id}
            )
            channel = data.get("channel", {})
            return {
                "id": channel_id,
                "name": channel.get("name", channel_id),
            }
        except ScanError:
            return {"id": channel_id, "name": channel_id}

    # -- History fetching --------------------------------------------------

    def get_history(
        self,
        channel_id: str,
        days: int = 1,
        oldest: Optional[str] = None,
        limit: int = 200,
        with_threads: bool = True,
        skip_bots: bool = True,
    ) -> List[Dict[str, Any]]:
        """Fetch channel messages within the time range.

        Args:
            channel_id: Slack channel ID.
            days: Number of days to look back.
            oldest: ISO date (YYYY-MM-DD) override for start time.
            limit: Max top-level messages to fetch.
            with_threads: Whether to fetch thread replies.
            skip_bots: Whether to skip bot messages.

        Returns:
            List of message dicts with metadata.
        """
        if oldest:
            try:
                oldest_dt = datetime.strptime(oldest, "%Y-%m-%d").replace(
                    tzinfo=timezone.utc
                )
            except ValueError:
                raise ScanError(f"Invalid date format: {oldest}")
            oldest_ts = str(oldest_dt.timestamp())
        else:
            oldest_dt = datetime.now(timezone.utc) - timedelta(days=days)
            oldest_ts = str(oldest_dt.timestamp())

        all_messages: List[Dict[str, Any]] = []
        cursor = None

        while True:
            params: Dict[str, Any] = {
                "channel": channel_id,
                "oldest": oldest_ts,
                "limit": min(limit - len(all_messages), 200),
            }
            if cursor:
                params["cursor"] = cursor

            data = self._request("conversations.history", params=params)

            for msg in data.get("messages", []):
                if skip_bots and self._is_bot_message(msg):
                    continue
                all_messages.append(msg)

            if len(all_messages) >= limit:
                break

            metadata = data.get("response_metadata", {})
            cursor = metadata.get("next_cursor")
            if not cursor:
                break

        # Reverse to chronological order and process
        processed = []
        for msg in reversed(all_messages):
            entry = self._process_message(
                channel_id, msg, with_threads, skip_bots
            )
            if entry:
                processed.append(entry)

        return processed

    # -- Message processing ------------------------------------------------

    @staticmethod
    def _is_bot_message(msg: Dict[str, Any]) -> bool:
        """Check if a message is from a bot or system."""
        if msg.get("subtype") == "bot_message":
            return True
        if msg.get("bot_id"):
            return True
        if msg.get("subtype") in (
            "channel_join",
            "channel_leave",
            "channel_topic",
            "channel_purpose",
            "channel_name",
            "channel_archive",
            "channel_unarchive",
        ):
            return True
        return False

    def _process_message(
        self,
        channel_id: str,
        msg: Dict[str, Any],
        with_threads: bool,
        skip_bots: bool,
    ) -> Optional[Dict[str, Any]]:
        """Process a single message into output format."""
        ts = msg.get("ts", "")
        user_id = msg.get("user", "")
        text = msg.get("text", "")

        if not text.strip():
            return None

        entry: Dict[str, Any] = {
            "ts": ts,
            "user_id": user_id,
            "user_name": self._resolve_user(user_id) if user_id else "unknown",
            "text": self._resolve_text(text),
            "permalink": self._make_permalink(channel_id, ts),
        }

        reply_count = msg.get("reply_count", 0)
        if with_threads and reply_count > 0:
            thread_ts = msg.get("thread_ts", ts)
            replies = self._fetch_thread_replies(
                channel_id, thread_ts, skip_bots
            )
            entry["reply_count"] = reply_count
            entry["replies"] = replies
        else:
            entry["reply_count"] = 0
            entry["replies"] = []

        return entry

    def _fetch_thread_replies(
        self,
        channel_id: str,
        thread_ts: str,
        skip_bots: bool,
    ) -> List[Dict[str, Any]]:
        """Fetch all replies in a thread (excluding the parent)."""
        try:
            data = self._request("conversations.replies", params={
                "channel": channel_id,
                "ts": thread_ts,
                "limit": 200,
            })
        except ScanError:
            return []

        replies = []
        messages = data.get("messages", [])

        for msg in messages[1:]:  # Skip parent (first message)
            if skip_bots and self._is_bot_message(msg):
                continue

            ts = msg.get("ts", "")
            user_id = msg.get("user", "")
            text = msg.get("text", "")

            if not text.strip():
                continue

            replies.append({
                "ts": ts,
                "user_id": user_id,
                "user_name": (
                    self._resolve_user(user_id) if user_id else "unknown"
                ),
                "text": self._resolve_text(text),
                "permalink": self._make_permalink(
                    channel_id, ts, thread_ts
                ),
            })

        return replies
