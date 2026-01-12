"""CLI entry point for slack-channels command.

Fetches all Slack channels the user can see and saves them to
~/.slack-channels.json for reference when posting messages.
"""

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from .client import SlackApiError, SlackClient
from .config import ConfigError, load_credentials


# Output file location
CHANNELS_FILE_PATH = Path.home() / ".slack-channels.json"

# Rate limiting: 20 requests/minute = 1 request per 3 seconds
REQUEST_INTERVAL_SECONDS = 3.0


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser for slack-channels command.

    Returns:
        Configured ArgumentParser.
    """
    parser = argparse.ArgumentParser(
        prog="slack-channels",
        description="Fetch Slack channels and save to ~/.slack-channels.json",
    )
    parser.add_argument(
        "--cursor",
        metavar="CURSOR",
        help="Resume from a pagination cursor (provided after a 429 error).",
    )
    return parser


def load_existing_channels() -> List[Dict[str, Any]]:
    """Load existing channels from file if it exists.

    Returns:
        List of existing channel dictionaries, or empty list.
    """
    if not CHANNELS_FILE_PATH.exists():
        return []

    try:
        with open(CHANNELS_FILE_PATH, "r") as f:
            data = json.load(f)
            return data.get("channels", [])
    except (json.JSONDecodeError, OSError):
        return []


def save_channels(channels: List[Dict[str, Any]]) -> None:
    """Save channels to JSON file.

    Args:
        channels: List of channel dictionaries.
    """
    output = {
        "description": "Slack channels for posting messages",
        "usage": "Find channel by name, use id with slack-update command",
        "channels": channels,
    }

    with open(CHANNELS_FILE_PATH, "w") as f:
        json.dump(output, f, indent=2)


def fetch_and_save_channels(
    client: SlackClient,
    start_cursor: Optional[str] = None,
) -> None:
    """Fetch all channels from Slack with rate limiting, saving after each page.

    Args:
        client: Initialized Slack client.
        start_cursor: Optional cursor to resume from.

    Raises:
        SlackApiError: If API call fails (includes cursor info for 429 errors).
    """
    # If resuming, load existing channels; otherwise start fresh
    if start_cursor:
        channels = load_existing_channels()
    else:
        channels = []

    cursor = start_cursor
    request_count = 0

    while True:
        # Rate limiting: wait between requests (skip first request)
        if request_count > 0:
            time.sleep(REQUEST_INTERVAL_SECONDS)

        params: Dict[str, Any] = {
            "types": "public_channel,private_channel",
            "limit": 200,
            "exclude_archived": True,
        }
        if cursor:
            params["cursor"] = cursor

        try:
            response = client._request("conversations.list", params=params)
        except SlackApiError as e:
            if e.error_code == "ratelimited":
                # Save progress and report cursor for resume
                save_channels(channels)
                cursor_msg = f" Resume with: --cursor \"{cursor}\"" if cursor else ""
                raise SlackApiError(
                    f"Rate limited. Progress saved ({len(channels)} channels).{cursor_msg}",
                    error_code="ratelimited",
                )
            raise

        request_count += 1

        for channel in response.get("channels", []):
            channel_data = {
                "id": channel["id"],
                "name": channel["name"],
                "is_private": channel.get("is_private", False),
                "topic": channel.get("topic", {}).get("value", ""),
                "description": channel.get("purpose", {}).get("value", ""),
            }
            channels.append(channel_data)

        # Save after each page
        save_channels(channels)

        cursor = response.get("response_metadata", {}).get("next_cursor")
        if not cursor:
            break


def main() -> int:
    """Main entry point for slack-channels command.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    parser = create_parser()
    args = parser.parse_args()

    # Load credentials
    try:
        credentials = load_credentials()
    except ConfigError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    # Fetch and save channels
    try:
        client = SlackClient(credentials)
        fetch_and_save_channels(client, start_cursor=args.cursor)
    except SlackApiError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except OSError as e:
        print(f"Error writing {CHANNELS_FILE_PATH}: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
