"""CLI entry point for slack-update command.

Post messages to Slack channels from the command line.

Usage:
    slack-update "#channel" "message"
    slack-update --auth  # One-time OAuth setup
"""

import argparse
import json
import sys
from dataclasses import dataclass
from typing import Optional

from .auth import run_oauth_flow
from .client import SlackApiError, SlackClient, SlackMessage
from .config import (
    ConfigError,
    load_credentials,
    load_oauth_config,
)


@dataclass
class PostResult:
    """Result of posting a message."""
    success: bool
    channel_id: Optional[str] = None
    channel_name: Optional[str] = None
    timestamp: Optional[str] = None
    message: Optional[str] = None
    error: Optional[str] = None
    error_code: Optional[str] = None


# Epilog with usage examples
EPILOG = """
Examples:
  # Post a message to a channel
  slack-update C01234567 "Build completed successfully"

  # Post with user mention (pre-resolved ID)
  slack-update C01234567 "Hey <@U12345678>, the fix is ready for review"

  # Post with formatting (Slack mrkdwn)
  slack-update C01234567 "*Bold* and _italic_ and `code`"

  # Human-readable output
  slack-update C01234567 "Hello team" --pretty

  # First-time authentication
  slack-update --auth

Finding Channel IDs:
  In Slack, right-click a channel -> "View channel details" -> scroll to bottom
  to find the Channel ID (starts with 'C').

Setup:
  1. Create a Slack App at https://api.slack.com/apps
  2. Add OAuth scopes: chat:write, channels:read, groups:read, users:read, users:read.email
  3. Add redirect URL: https://localhost:8765/oauth/callback
  4. Run: slack-update --auth
  5. Store client_id and client_secret in ~/.slack-config.yaml or env vars
"""


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser for slack-update command.

    Returns:
        Configured ArgumentParser.
    """
    parser = argparse.ArgumentParser(
        prog="slack-update",
        description="Post messages to Slack channels.",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "channel",
        metavar="CHANNEL_ID",
        nargs="?",
        help="Slack channel ID to post to (e.g., 'C01234567').",
    )

    parser.add_argument(
        "message",
        metavar="MESSAGE",
        nargs="?",
        help="Message text to post. Supports Slack mrkdwn formatting.",
    )

    parser.add_argument(
        "--auth",
        action="store_true",
        help="Run OAuth flow to authenticate and save token.",
    )

    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Output human-readable format instead of JSON.",
    )

    return parser


def run_post(client: SlackClient, channel: str, message: str) -> PostResult:
    """Post a message to a Slack channel.

    Args:
        client: Initialized Slack client.
        channel: Channel name or ID.
        message: Message text.

    Returns:
        PostResult with outcome details.
    """
    try:
        result = client.post_message(channel, message)
        return PostResult(
            success=True,
            channel_id=result.channel_id,
            channel_name=result.channel_name,
            timestamp=result.timestamp,
            message=result.text,
        )
    except SlackApiError as e:
        return PostResult(
            success=False,
            error=str(e),
            error_code=e.error_code,
        )


def print_result(result: PostResult, use_pretty: bool) -> None:
    """Print the result of a post operation.

    Args:
        result: PostResult to print.
        use_pretty: If True, use human-readable format; otherwise JSON.
    """
    if use_pretty:
        if result.success:
            channel_display = result.channel_name or result.channel_id
            print(f"Message posted to #{channel_display}")
            print(f"Timestamp: {result.timestamp}")
        else:
            print(f"Failed to post message: {result.error}", file=sys.stderr)
    else:
        output = {
            "success": result.success,
            "channel_id": result.channel_id,
            "channel_name": result.channel_name,
            "timestamp": result.timestamp,
            "message": result.message,
            "error": result.error,
            "error_code": result.error_code,
        }
        # Remove None values for cleaner output
        output = {k: v for k, v in output.items() if v is not None}
        print(json.dumps(output, indent=2))


def run_auth() -> int:
    """Run OAuth authentication flow.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    try:
        oauth_config = load_oauth_config()
    except ConfigError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    result = run_oauth_flow(oauth_config)

    if result.success:
        print(f"\nAuthentication successful!")
        if result.team_name:
            print(f"Workspace: {result.team_name}")
        if result.user_id:
            print(f"User ID: {result.user_id}")
        return 0
    else:
        print(f"\nAuthentication failed: {result.error}", file=sys.stderr)
        return 1


def main() -> int:
    """Main entry point for slack-update command.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    parser = create_parser()
    args = parser.parse_args()

    # Handle auth flow
    if args.auth:
        return run_auth()

    # Validate required arguments for posting
    if not args.channel or not args.message:
        parser.print_help()
        print("\nError: CHANNEL_ID and MESSAGE are required (unless using --auth).", file=sys.stderr)
        return 1

    # Load credentials
    try:
        credentials = load_credentials()
    except ConfigError as e:
        if not args.pretty:
            print(json.dumps({
                "success": False,
                "error": str(e),
                "error_code": "config_error",
            }, indent=2))
        else:
            print(f"Error: {e}", file=sys.stderr)
        return 1

    # Create client and post message
    client = SlackClient(credentials)
    result = run_post(client, args.channel, args.message)

    print_result(result, args.pretty)

    return 0 if result.success else 1


if __name__ == "__main__":
    sys.exit(main())
