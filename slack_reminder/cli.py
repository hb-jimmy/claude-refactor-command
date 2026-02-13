"""CLI entry point for slack-scan-reminders.

Scans a Slack channel for action-item messages and creates Slack reminders.

Usage:
    slack-scan-reminders              # Scan and create reminders
    slack-scan-reminders --dry-run    # Show what would be done
    slack-scan-reminders --json       # JSON output
    slack-scan-reminders --channel X  # Override channel
"""

import argparse
import json
import sys

from .config import ConfigError, load_reminder_config, load_slack_token
from .scanner import ReminderScanner, ScannerError


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="slack-scan-reminders",
        description="Scan a Slack channel for action items and create reminders.",
    )
    parser.add_argument(
        "--channel", "-c",
        help="Slack channel ID to scan (overrides config).",
    )
    parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="Show what would be done without making changes.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output results as JSON.",
    )

    args = parser.parse_args()

    # Load config and token
    try:
        config = load_reminder_config()
        token = load_slack_token()
    except ConfigError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    # Determine channel
    channel_id = args.channel or config.channel_id
    if not channel_id:
        print(
            "Error: No channel ID configured.\n"
            "Either pass --channel or set channel_id in ~/.slack-reminder.yaml",
            file=sys.stderr,
        )
        return 1

    # Scan and process
    scanner = ReminderScanner(token)
    try:
        stats = scanner.process_channel(channel_id, dry_run=args.dry_run)
    except ScannerError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    # Output results
    if args.json_output:
        print(json.dumps({
            "channel_id": channel_id,
            "dry_run": args.dry_run,
            "messages_scanned": stats.messages_scanned,
            "action_messages_found": stats.action_messages_found,
            "already_processed": stats.already_processed,
            "reminders_created": stats.reminders_created,
            "errors": stats.errors,
        }, indent=2))
    else:
        mode = " (dry run)" if args.dry_run else ""
        print(f"\nDone{mode}:")
        print(f"  Action messages found: {stats.action_messages_found}")
        print(f"  Already processed:     {stats.already_processed}")
        print(f"  Reminders created:     {stats.reminders_created}")
        if stats.errors:
            print(f"  Errors:                {stats.errors}")

    return 1 if stats.errors else 0


if __name__ == "__main__":
    sys.exit(main())
