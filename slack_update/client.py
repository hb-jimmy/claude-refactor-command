"""Slack API client for posting messages.

This module provides an HTTP adapter for the Slack Web API, encapsulating
all HTTP interactions with Slack.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import requests

from .config import SlackCredentials


# Slack API base URL
SLACK_API_BASE = "https://slack.com/api"


@dataclass
class SlackChannel:
    """Represents a Slack channel."""
    id: str
    name: str
    is_private: bool


@dataclass
class SlackUser:
    """Represents a Slack user."""
    id: str
    display_name: str
    real_name: str
    email: Optional[str]


@dataclass
class SlackMessage:
    """Represents a posted Slack message."""
    channel_id: str
    channel_name: Optional[str]
    timestamp: str
    text: str


class SlackApiError(Exception):
    """Raised when a Slack API call fails.

    Attributes:
        message: Human-readable error message.
        error_code: Slack error code (e.g., 'channel_not_found').
        response_data: Full response data from Slack.
    """

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        response_data: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.error_code = error_code
        self.response_data = response_data


class SlackClient:
    """HTTP adapter for Slack Web API.

    This class encapsulates all HTTP interactions with Slack, providing
    a clean interface for posting messages and listing channels/users.
    """

    def __init__(self, credentials: SlackCredentials):
        """Initialize the Slack client.

        Args:
            credentials: Slack credentials containing the user token.
        """
        self._credentials = credentials
        self._session = self._create_session()
        self._channel_cache: Dict[str, SlackChannel] = {}

    def _create_session(self) -> requests.Session:
        """Create a configured requests session.

        Returns:
            Session with auth headers set.
        """
        session = requests.Session()
        session.headers.update({
            "Authorization": f"Bearer {self._credentials.user_token}",
            "Content-Type": "application/json; charset=utf-8",
        })
        return session

    def _request(
        self,
        method: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make a request to the Slack API.

        Args:
            method: Slack API method name (e.g., 'chat.postMessage').
            params: Query parameters for GET requests.
            json_data: JSON body for POST requests.

        Returns:
            Response data from Slack.

        Raises:
            SlackApiError: If the request fails or Slack returns an error.
        """
        url = f"{SLACK_API_BASE}/{method}"

        try:
            if json_data:
                response = self._session.post(url, json=json_data, params=params)
            else:
                response = self._session.get(url, params=params)
        except requests.RequestException as e:
            raise SlackApiError(f"Network error: {e}")

        # Handle HTTP 429 rate limiting
        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After", "unknown")
            raise SlackApiError(
                message=f"Rate limited. Retry after {retry_after} seconds.",
                error_code="ratelimited",
            )

        # Handle other HTTP errors
        if not response.ok:
            raise SlackApiError(
                message=f"HTTP error: {response.status_code} {response.reason}",
                error_code=f"http_{response.status_code}",
            )

        data = response.json()

        if not data.get("ok"):
            error_code = data.get("error", "unknown_error")
            error_msg = self._format_error_message(error_code)
            raise SlackApiError(
                message=error_msg,
                error_code=error_code,
                response_data=data,
            )

        return data

    def _format_error_message(self, error_code: str) -> str:
        """Format a human-readable error message for Slack error codes.

        Args:
            error_code: Slack API error code.

        Returns:
            Human-readable error message.
        """
        error_messages = {
            "channel_not_found": "Channel not found. Check the channel name or ensure you have access.",
            "not_in_channel": "Not in channel. The user must be a member of the channel to post.",
            "is_archived": "Channel is archived and cannot receive messages.",
            "msg_too_long": "Message text is too long.",
            "no_text": "No message text provided.",
            "restricted_action": "Action restricted. Check workspace permissions.",
            "invalid_auth": "Invalid authentication token.",
            "token_revoked": "Token has been revoked. Re-authenticate with --auth.",
            "account_inactive": "Account is inactive.",
            "missing_scope": "Token missing required OAuth scopes.",
            "ratelimited": "Rate limited by Slack. Try again later.",
        }
        return error_messages.get(error_code, f"Slack API error: {error_code}")

    def post_message(
        self,
        channel_id: str,
        text: str,
        thread_ts: Optional[str] = None,
    ) -> SlackMessage:
        """Post a message to a Slack channel.

        Args:
            channel_id: Slack channel ID (e.g., 'C01234567').
            text: Message text (supports Slack mrkdwn formatting).
            thread_ts: Optional thread timestamp to reply in thread.

        Returns:
            SlackMessage with details of the posted message.

        Raises:
            SlackApiError: If posting fails.
        """
        payload: Dict[str, Any] = {
            "channel": channel_id,
            "text": text,
        }

        if thread_ts:
            payload["thread_ts"] = thread_ts

        response = self._request("chat.postMessage", json_data=payload)

        return SlackMessage(
            channel_id=response["channel"],
            channel_name=None,
            timestamp=response["ts"],
            text=text,
        )

    def _resolve_channel(self, channel: str) -> str:
        """Resolve a channel name to its ID.

        Args:
            channel: Channel name (with or without #) or channel ID.

        Returns:
            Channel ID.

        Raises:
            SlackApiError: If channel cannot be found.
        """
        # Strip leading # if present
        channel = channel.lstrip("#")

        # If it looks like a channel ID already, return it
        if channel.startswith("C") and len(channel) == 11:
            return channel

        # Check cache first
        for ch in self._channel_cache.values():
            if ch.name == channel:
                return ch.id

        # Search public channels
        channels = self.list_channels(include_private=True)
        for ch in channels:
            if ch.name == channel:
                return ch.id

        raise SlackApiError(
            f"Channel '{channel}' not found",
            error_code="channel_not_found",
        )

    def list_channels(self, include_private: bool = True) -> List[SlackChannel]:
        """List channels the user has access to.

        Args:
            include_private: Include private channels.

        Returns:
            List of SlackChannel objects.

        Raises:
            SlackApiError: If listing fails.
        """
        channels: List[SlackChannel] = []
        cursor = None

        # Fetch public channels
        while True:
            params: Dict[str, Any] = {
                "types": "public_channel,private_channel" if include_private else "public_channel",
                "limit": 200,
                "exclude_archived": True,
            }
            if cursor:
                params["cursor"] = cursor

            response = self._request("conversations.list", params=params)

            for ch in response.get("channels", []):
                channel = SlackChannel(
                    id=ch["id"],
                    name=ch["name"],
                    is_private=ch.get("is_private", False),
                )
                channels.append(channel)
                self._channel_cache[channel.id] = channel

            # Check for pagination
            cursor = response.get("response_metadata", {}).get("next_cursor")
            if not cursor:
                break

        return channels

    def list_users(self) -> List[SlackUser]:
        """List all users in the workspace.

        Returns:
            List of SlackUser objects.

        Raises:
            SlackApiError: If listing fails.
        """
        users: List[SlackUser] = []
        cursor = None

        while True:
            params: Dict[str, Any] = {"limit": 200}
            if cursor:
                params["cursor"] = cursor

            response = self._request("users.list", params=params)

            for member in response.get("members", []):
                # Skip bots and deleted users
                if member.get("is_bot") or member.get("deleted"):
                    continue

                profile = member.get("profile", {})
                user = SlackUser(
                    id=member["id"],
                    display_name=profile.get("display_name") or profile.get("real_name", ""),
                    real_name=profile.get("real_name", ""),
                    email=profile.get("email"),
                )
                users.append(user)

            cursor = response.get("response_metadata", {}).get("next_cursor")
            if not cursor:
                break

        return users

    def get_current_user(self) -> SlackUser:
        """Get the authenticated user's information.

        Returns:
            SlackUser for the current user.

        Raises:
            SlackApiError: If request fails.
        """
        response = self._request("auth.test")

        # Get full user info
        user_response = self._request("users.info", params={"user": response["user_id"]})
        member = user_response["user"]
        profile = member.get("profile", {})

        return SlackUser(
            id=member["id"],
            display_name=profile.get("display_name") or profile.get("real_name", ""),
            real_name=profile.get("real_name", ""),
            email=profile.get("email"),
        )
