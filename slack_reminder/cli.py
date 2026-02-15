"""CLI entry point for slack-remind.

Creates a Slack reminder directly via the API.

Usage:
    slack-remind "Order books for the team" --time 2026-02-16T08:00:00-05:00
    slack-remind "Talk to Angela" --time 2026-02-17T09:00:00-05:00 --json
"""

import argparse
import json
import sys

from .config import ConfigError, load_slack_token
from .scanner import ReminderClient, ReminderError


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="slack-remind",
        description="Create a Slack reminder.",
    )
    parser.add_argument(
        "text",
        help="Reminder text (supports Slack mrkdwn).",
    )
    parser.add_argument(
        "--time", "-t",
        required=True,
        dest="remind_time",
        help="ISO 8601 timestamp for when to trigger (e.g., 2026-02-16T08:00:00-05:00).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output result as JSON.",
    )

    args = parser.parse_args()

    try:
        token = load_slack_token()
    except ConfigError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    client = ReminderClient(token)

    try:
        client.create_reminder(args.text, args.remind_time)
    except ReminderError as e:
        if args.json_output:
            print(json.dumps({"success": False, "error": str(e)}))
        else:
            print(f"Error: {e}", file=sys.stderr)
        return 1

    if args.json_output:
        print(json.dumps({"success": True, "text": args.text, "time": args.remind_time}))
    else:
        print(f"Reminder created: {args.text}")
        print(f"  Time: {args.remind_time}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
