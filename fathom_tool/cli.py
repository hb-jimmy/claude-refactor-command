"""
CLI entry points for fathom-tool.

Commands:
    fathom-transcripts fetch [--meeting PERSON] [--from-date DATE] [--to-date DATE]
    fathom-transcripts list
"""

import argparse
import json
import re
import sys
import time
from datetime import datetime, timedelta

from .client import FathomClient, FathomApiError
from .config import (
    ConfigError,
    MeetingConfig,
    load_config,
    transcript_dir_for_meeting,
)


def _date_from_created_at(created_at: str) -> str:
    """Extract YYYY-MM-DD from a Fathom created_at ISO timestamp."""
    return created_at[:10]


def _fetch_transcripts(
    client: FathomClient,
    meeting: MeetingConfig,
    from_date: str,
    to_date: str,
    force: bool = False,
) -> int:
    """
    Fetch and save new transcripts for a single meeting config.

    Returns the number of new transcripts saved.
    """
    out_dir = transcript_dir_for_meeting(meeting)
    out_dir.mkdir(parents=True, exist_ok=True)

    created_after = f"{from_date}T00:00:00Z"
    created_before = f"{to_date}T23:59:59Z"

    meetings = client.list_meetings(
        created_after=created_after,
        created_before=created_before,
    )

    # Client-side filter: only keep meetings matching the configured title
    # Normalize whitespace around '/' so "A / B" matches "A/B", "A/ B", etc.
    def _normalize_title(t: str) -> str:
        return re.sub(r'\s*/\s*', '/', t.lower().strip())

    norm_title = _normalize_title(meeting.title)
    matched = [m for m in meetings if _normalize_title(m.title) == norm_title]

    # Fallback: if exact title match finds nothing, try matching by just
    # the person's first name (e.g., title "Elias" matches person "Elias")
    if not matched:
        person_lower = meeting.person.lower().strip()
        matched = [m for m in meetings if m.title.lower().strip() == person_lower]
        if matched:
            print(f"  (matched {len(matched)} meeting(s) by person name fallback)")

    meetings = matched

    # Load manifest of previously downloaded recording IDs
    manifest_path = out_dir / ".downloaded_recordings.json"
    if manifest_path.exists():
        downloaded: dict = json.loads(manifest_path.read_text(encoding="utf-8"))
    else:
        downloaded: dict = {}

    saved = 0
    for i, mtg in enumerate(meetings):
        if not mtg.recording_id:
            continue

        rec_id_str = str(mtg.recording_id)

        # Skip if this exact recording was already downloaded
        if rec_id_str in downloaded and not force:
            print(f"  Skipped: recording {mtg.recording_id} already downloaded as {downloaded[rec_id_str]}")
            continue

        # Pace requests to stay under 60/min rate limit
        if i > 0:
            time.sleep(1.5)

        date_str = _date_from_created_at(mtg.created_at)
        filename = f"{date_str}.json"
        filepath = out_dir / filename

        # If a file for this date already exists, find next available suffix
        if filepath.exists():
            counter = 2
            while True:
                filename = f"{date_str}_{counter}.json"
                filepath = out_dir / filename
                if not filepath.exists():
                    break
                counter += 1

        try:
            transcript = client.get_transcript(mtg.recording_id)
        except FathomApiError as e:
            if e.status_code == 429:
                print(f"  Rate limited, waiting 60s...", file=sys.stderr)
                time.sleep(60)
                try:
                    transcript = client.get_transcript(mtg.recording_id)
                except FathomApiError as e2:
                    print(f"  Warning: Failed to get transcript for {mtg.title} ({date_str}): {e2}", file=sys.stderr)
                    continue
            else:
                print(f"  Warning: Failed to get transcript for {mtg.title} ({date_str}): {e}", file=sys.stderr)
                continue

        if not transcript:
            continue

        filepath.write_text(json.dumps(transcript, indent=2), encoding="utf-8")
        downloaded[rec_id_str] = filename
        manifest_path.write_text(json.dumps(downloaded, indent=2), encoding="utf-8")
        print(f"  Saved: {filepath}")
        saved += 1

    return saved


def cmd_fetch(args: argparse.Namespace) -> None:
    """Fetch new transcripts for configured meetings."""
    config = load_config()
    client = FathomClient(config.api_key)

    to_date = args.to_date or datetime.now().strftime("%Y-%m-%d")
    from_date = args.from_date or (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

    meetings = config.meetings
    if args.meeting:
        person_lower = args.meeting.lower()
        meetings = [m for m in meetings if m.person.lower() == person_lower]
        if not meetings:
            available = ", ".join(f'"{m.person}"' for m in config.meetings)
            print(f'Error: No meeting found for person "{args.meeting}"', file=sys.stderr)
            print(f"Available: {available}", file=sys.stderr)
            sys.exit(1)

    if not meetings:
        print("No meetings configured. Add meetings to ~/.one-on-one/config.yaml", file=sys.stderr)
        sys.exit(1)

    total_saved = 0
    for meeting in meetings:
        print(f"Fetching transcripts for: {meeting.person} (title: {meeting.title})")
        try:
            saved = _fetch_transcripts(client, meeting, from_date, to_date, force=args.force)
            if saved == 0:
                print("  No new transcripts found.")
            total_saved += saved
        except FathomApiError as e:
            print(f"  Error: {e}", file=sys.stderr)

    print(f"\nTotal new transcripts saved: {total_saved}")


def cmd_list(args: argparse.Namespace) -> None:
    """List configured meetings and their transcript counts."""
    config = load_config()

    if not config.meetings:
        print("No meetings configured. Add meetings to ~/.one-on-one/config.yaml")
        return

    print(f"{'Person':<20} {'Title':<30} {'Transcripts'}")
    print("-" * 65)

    for meeting in config.meetings:
        out_dir = transcript_dir_for_meeting(meeting)
        if out_dir.exists():
            count = len(list(out_dir.glob("*.json")))
        else:
            count = 0
        print(f"{meeting.person:<20} {meeting.title:<30} {count}")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="fathom-transcripts",
        description="Retrieve Fathom meeting transcripts.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # fetch command
    fetch_parser = subparsers.add_parser("fetch", help="Fetch new transcripts")
    fetch_parser.add_argument(
        "--meeting", "-m",
        help="Fetch only for a specific person name",
    )
    fetch_parser.add_argument(
        "--from-date", "-f",
        help="Start date (YYYY-MM-DD). Default: 30 days ago.",
    )
    fetch_parser.add_argument(
        "--to-date", "-t",
        help="End date (YYYY-MM-DD). Default: today.",
    )
    fetch_parser.add_argument(
        "--force",
        action="store_true",
        default=False,
        help="Re-download transcripts even if a file for that date already exists.",
    )
    fetch_parser.set_defaults(func=cmd_fetch)

    # list command
    list_parser = subparsers.add_parser("list", help="List configured meetings")
    list_parser.set_defaults(func=cmd_list)

    args = parser.parse_args()

    try:
        args.func(args)
    except ConfigError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        sys.exit(1)
