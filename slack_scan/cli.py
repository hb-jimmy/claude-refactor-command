"""CLI entry point for slack-history.

Fetches messages from a Slack channel and outputs JSON for analysis.

Usage:
    slack-history C01234567 --days 2
    slack-history C01234567 --oldest 2026-02-14
    slack-history --all --days 1
"""

import argparse
import json
import sys

from .config import ConfigError, load_scan_config, load_slack_token
from .client import HistoryClient, ScanError


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="slack-history",
        description="Fetch Slack channel history as JSON.",
    )
    parser.add_argument(
        "channel",
        nargs="?",
        help="Channel ID to fetch history from.",
    )
    parser.add_argument(
        "--all", "-a",
        action="store_true",
        dest="all_channels",
        help="Scan all channels from ~/.slack-scan.yaml.",
    )
    parser.add_argument(
        "--days", "-d",
        type=int,
        default=1,
        help="Number of days to look back (default: 1).",
    )
    parser.add_argument(
        "--oldest",
        help="Start date (YYYY-MM-DD) instead of --days.",
    )
    parser.add_argument(
        "--no-threads",
        action="store_true",
        help="Skip fetching thread replies.",
    )
    parser.add_argument(
        "--include-bots",
        action="store_true",
        help="Include bot/system messages.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=200,
        help="Max messages per channel (default: 200).",
    )

    args = parser.parse_args()

    if not args.channel and not args.all_channels:
        parser.error(
            "Provide a channel ID or use --all to scan configured channels."
        )

    try:
        token = load_slack_token()
    except ConfigError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    client = HistoryClient(token)

    channels = []
    if args.all_channels:
        try:
            config = load_scan_config()
            channels = [(c.id, c.name) for c in config.channels]
        except ConfigError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
    else:
        channels = [(args.channel, "")]

    results = []
    for channel_id, channel_name in channels:
        try:
            if not channel_name:
                info = client.get_channel_info(channel_id)
                channel_name = info["name"]

            print(
                f"Scanning #{channel_name} ({channel_id})...",
                file=sys.stderr,
                flush=True,
            )

            messages = client.get_history(
                channel_id=channel_id,
                days=args.days,
                oldest=args.oldest,
                limit=args.limit,
                with_threads=not args.no_threads,
                skip_bots=not args.include_bots,
            )

            results.append({
                "channel_id": channel_id,
                "channel_name": channel_name,
                "message_count": len(messages),
                "messages": messages,
            })

            print(
                f"  Found {len(messages)} messages.",
                file=sys.stderr,
                flush=True,
            )
        except ScanError as e:
            print(
                f"Error scanning #{channel_name or channel_id}: {e}",
                file=sys.stderr,
            )

    json.dump(results, sys.stdout, indent=2)
    print()  # trailing newline
    return 0


if __name__ == "__main__":
    sys.exit(main())
