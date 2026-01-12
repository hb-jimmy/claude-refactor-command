"""CLI entry point for slack-users command.

Fetches all Slack users and saves them to ~/.slack-users.json for use
by slack-update when resolving @mentions.
"""

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

from .client import SlackApiError, SlackClient
from .config import ConfigError, load_credentials


# Output file location
USERS_FILE_PATH = Path.home() / ".slack-users.json"

# Rate limiting: 20 requests/minute = 1 request per 3 seconds
REQUEST_INTERVAL_SECONDS = 3.0


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser for slack-users command.

    Returns:
        Configured ArgumentParser.
    """
    parser = argparse.ArgumentParser(
        prog="slack-users",
        description="Fetch Slack users and save to ~/.slack-users.json",
    )
    return parser


def fetch_all_users(client: SlackClient) -> List[Dict[str, Any]]:
    """Fetch all users from Slack with rate limiting.

    Args:
        client: Initialized Slack client.

    Returns:
        List of user dictionaries.

    Raises:
        SlackApiError: If API call fails.
    """
    users: List[Dict[str, Any]] = []
    cursor = None
    request_count = 0

    while True:
        # Rate limiting: wait between requests (skip first request)
        if request_count > 0:
            time.sleep(REQUEST_INTERVAL_SECONDS)

        params: Dict[str, Any] = {"limit": 200}
        if cursor:
            params["cursor"] = cursor

        response = client._request("users.list", params=params)
        request_count += 1

        for member in response.get("members", []):
            # Skip bots and deleted users
            if member.get("is_bot") or member.get("deleted"):
                continue

            profile = member.get("profile", {})

            # Extract the @mention name - this is what users type to mention someone
            # Priority: display_name (custom @name) > real_name_normalized > real_name
            display_name = profile.get("display_name", "").strip()
            real_name = profile.get("real_name", "").strip()
            real_name_normalized = profile.get("real_name_normalized", "").strip()

            user_data = {
                "id": member["id"],
                "display_name": display_name or real_name,
                "real_name": real_name,
                "mention_name": display_name or real_name_normalized or real_name,
                "email": profile.get("email"),
            }
            users.append(user_data)

        cursor = response.get("response_metadata", {}).get("next_cursor")
        if not cursor:
            break

    return users


def save_users(users: List[Dict[str, Any]]) -> None:
    """Save users to JSON file.

    Args:
        users: List of user dictionaries.
    """
    output = {
        "description": "Slack users for @mention resolution",
        "usage": "Find user by mention_name or real_name, use id in <@ID> format",
        "users": users,
    }

    with open(USERS_FILE_PATH, "w") as f:
        json.dump(output, f, indent=2)


def main() -> int:
    """Main entry point for slack-users command.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    parser = create_parser()
    parser.parse_args()

    # Load credentials
    try:
        credentials = load_credentials()
    except ConfigError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    # Fetch users
    try:
        client = SlackClient(credentials)
        users = fetch_all_users(client)
    except SlackApiError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    # Save to file
    try:
        save_users(users)
    except OSError as e:
        print(f"Error writing {USERS_FILE_PATH}: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
