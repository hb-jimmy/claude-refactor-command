"""Slack API client for canvas extraction.

Extracts channel canvases via:
  conversations.info → files.info → url_private_download
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests


SLACK_API_BASE = "https://slack.com/api"
CHANNELS_CACHE_PATH = Path.home() / ".slack-channels.json"


class SlackApiError(Exception):
    """Raised when a Slack API call fails."""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        response_data: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.error_code = error_code
        self.response_data = response_data


class PostmortemClient:
    """Slack client for extracting channel canvases."""

    def __init__(self, token: str):
        self._token = token
        self._session = self._create_session()

    def _create_session(self) -> requests.Session:
        session = requests.Session()
        session.headers.update({
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json; charset=utf-8",
        })
        return session

    def _request(
        self,
        method: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make a request to the Slack API."""
        url = f"{SLACK_API_BASE}/{method}"

        try:
            if json_data:
                response = self._session.post(url, json=json_data, params=params)
            else:
                response = self._session.get(url, params=params)
        except requests.RequestException as e:
            raise SlackApiError(f"Network error: {e}")

        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After", "unknown")
            raise SlackApiError(
                message=f"Rate limited. Retry after {retry_after} seconds.",
                error_code="ratelimited",
            )

        if not response.ok:
            raise SlackApiError(
                message=f"HTTP error: {response.status_code} {response.reason}",
                error_code=f"http_{response.status_code}",
            )

        data = response.json()

        if not data.get("ok"):
            error_code = data.get("error", "unknown_error")
            if error_code == "missing_scope":
                needed = data.get("needed", "unknown")
                raise SlackApiError(
                    message=(
                        f"Missing required OAuth scope: {needed}\n"
                        f"Add the '{needed}' scope to your Slack app and re-authenticate."
                    ),
                    error_code=error_code,
                    response_data=data,
                )
            raise SlackApiError(
                message=f"Slack API error: {error_code}",
                error_code=error_code,
                response_data=data,
            )

        return data

    def resolve_channel(self, name: str) -> Optional[str]:
        """Resolve a channel name to its ID.

        Checks ~/.slack-channels.json cache first, then falls back to
        conversations.list with pagination.

        Args:
            name: Channel name (with or without #).

        Returns:
            Channel ID, or None if not found.
        """
        name = name.lstrip("#")

        # If it looks like a channel ID already, return it
        if name.startswith("C") and len(name) >= 9:
            return name

        # Check cache first
        cached_id = self._check_channel_cache(name)
        if cached_id:
            return cached_id

        # Fall back to API with pagination
        cursor = None
        while True:
            params: Dict[str, Any] = {
                "types": "public_channel,private_channel",
                "limit": 200,
                "exclude_archived": False,
            }
            if cursor:
                params["cursor"] = cursor

            response = self._request("conversations.list", params=params)

            for ch in response.get("channels", []):
                if ch["name"] == name:
                    return ch["id"]

            cursor = response.get("response_metadata", {}).get("next_cursor")
            if not cursor:
                break

        return None

    def _check_channel_cache(self, name: str) -> Optional[str]:
        """Check ~/.slack-channels.json for a channel name."""
        if not CHANNELS_CACHE_PATH.exists():
            return None

        try:
            with open(CHANNELS_CACHE_PATH, "r") as f:
                channels = json.load(f)
        except (json.JSONDecodeError, OSError):
            return None

        for ch in channels:
            if ch.get("name") == name:
                return ch.get("id")

        return None

    def get_canvas_file_id(self, channel_id: str) -> Optional[str]:
        """Get the canvas file ID for a channel.

        Args:
            channel_id: Slack channel ID.

        Returns:
            File ID of the canvas, or None if no canvas exists.
        """
        response = self._request("conversations.info", params={"channel": channel_id})
        channel = response.get("channel", {})
        tabs = channel.get("properties", {}).get("tabs", [])
        for tab in tabs:
            if tab.get("type") == "canvas":
                return tab.get("data", {}).get("file_id")
        return None

    def get_download_url(self, file_id: str) -> Optional[str]:
        """Get the download URL for a file.

        Args:
            file_id: Slack file ID.

        Returns:
            Private download URL, or None if not available.
        """
        response = self._request("files.info", params={"file": file_id})
        file_info = response.get("file", {})
        return file_info.get("url_private_download")

    def download_content(self, url: str) -> str:
        """Download content from a private URL with authentication.

        Args:
            url: Slack private download URL.

        Returns:
            Raw content as string.
        """
        try:
            response = self._session.get(url)
        except requests.RequestException as e:
            raise SlackApiError(f"Download error: {e}")

        if not response.ok:
            raise SlackApiError(
                message=f"Download failed: {response.status_code} {response.reason}",
                error_code=f"http_{response.status_code}",
            )

        return response.text

    def extract_canvas(self, channel_id: str) -> Optional[str]:
        """Extract canvas content from a channel.

        Orchestrates: get_canvas_file_id → get_download_url → download_content.

        Args:
            channel_id: Slack channel ID.

        Returns:
            Canvas content as string, or None if no canvas exists.
        """
        file_id = self.get_canvas_file_id(channel_id)
        if not file_id:
            return None

        download_url = self.get_download_url(file_id)
        if not download_url:
            return None

        return self.download_content(download_url)
