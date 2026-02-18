"""CLI entry point for slack-postmortem command.

Extract Slack channel canvases and save as markdown files.

Usage:
    slack-postmortem --all [--output-dir DIR] [--pretty] [--json]
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from .client import PostmortemClient, SlackApiError
from .config import ConfigError, ChannelEntry, load_config
from .converter import convert_to_markdown


DEFAULT_OUTPUT_DIR = Path.home() / "postmortems"


@dataclass
class ChannelResult:
    """Result of processing a single channel."""
    channel_name: str
    success: bool
    file_path: Optional[str] = None
    error: Optional[str] = None
    skipped: bool = False


@dataclass
class RunResult:
    """Result of processing all channels."""
    results: List[ChannelResult] = field(default_factory=list)

    @property
    def success_count(self) -> int:
        return sum(1 for r in self.results if r.success)

    @property
    def error_count(self) -> int:
        return sum(1 for r in self.results if not r.success and not r.skipped)

    @property
    def skipped_count(self) -> int:
        return sum(1 for r in self.results if r.skipped)


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="slack-postmortem",
        description="Extract Slack channel canvases and save as markdown files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  slack-postmortem --all\n"
            "  slack-postmortem --all --output-dir /tmp/postmortems\n"
            "  slack-postmortem --all --json\n"
            "\n"
            "Config file: ~/.slack-postmortem.yaml\n"
            "  channels:\n"
            '    - name: "incident-2026-02-01"\n'
            '    - name: "incident-2026-01-15"'
        ),
    )

    parser.add_argument(
        "--all",
        action="store_true",
        dest="process_all",
        help="Process all channels from config (required).",
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help=f"Output directory (default: {DEFAULT_OUTPUT_DIR}).",
    )

    parser.add_argument(
        "--pretty",
        action="store_true",
        default=True,
        help="Human-readable output (default).",
    )

    parser.add_argument(
        "--json",
        action="store_true",
        dest="use_json",
        help="JSON output.",
    )

    return parser


def process_channel(
    client: PostmortemClient,
    channel: ChannelEntry,
    output_dir: Path,
) -> ChannelResult:
    """Process a single channel: resolve, extract canvas, convert, write."""
    name = channel.name

    # Resolve channel ID
    channel_id = channel.id
    if not channel_id:
        channel_id = client.resolve_channel(name)
        if not channel_id:
            return ChannelResult(
                channel_name=name,
                success=False,
                error=f"Channel '{name}' not found",
            )

    # Extract canvas
    try:
        content = client.extract_canvas(channel_id)
    except SlackApiError as e:
        return ChannelResult(
            channel_name=name,
            success=False,
            error=str(e),
        )

    if content is None:
        return ChannelResult(
            channel_name=name,
            success=False,
            skipped=True,
            error="No canvas found",
        )

    # Convert to markdown
    markdown = convert_to_markdown(content)

    # Parse filename from first line "# Post-Mortem: <name>"
    filename = name
    first_line = markdown.split("\n", 1)[0]
    match = re.match(r"^#\s*Post-?Mortem:\s*(.+)", first_line, re.IGNORECASE)
    if match:
        parsed = match.group(1).strip().replace("\\_", "_")
        if parsed:
            # Sanitize for filesystem
            filename = re.sub(r"[^\w\-.]", "_", parsed)

    # Write file
    output_path = output_dir / f"{filename}.md"
    try:
        output_path.write_text(markdown)
    except OSError as e:
        return ChannelResult(
            channel_name=name,
            success=False,
            error=f"Failed to write file: {e}",
        )

    return ChannelResult(
        channel_name=name,
        success=True,
        file_path=str(output_path),
    )


def print_result(run_result: RunResult, use_json: bool) -> None:
    """Print results to stdout."""
    if use_json:
        output = {
            "results": [
                {k: v for k, v in {
                    "channel": r.channel_name,
                    "success": r.success,
                    "file": r.file_path,
                    "error": r.error,
                    "skipped": r.skipped if r.skipped else None,
                }.items() if v is not None}
                for r in run_result.results
            ],
            "summary": {
                "total": len(run_result.results),
                "success": run_result.success_count,
                "errors": run_result.error_count,
                "skipped": run_result.skipped_count,
            },
        }
        print(json.dumps(output, indent=2))
    else:
        for r in run_result.results:
            if r.success:
                print(f"  {r.channel_name} -> {r.file_path}")
            elif r.skipped:
                print(f"  {r.channel_name} - No canvas found", file=sys.stderr)
            else:
                print(f"  {r.channel_name} - Error: {r.error}", file=sys.stderr)

        print()
        total = len(run_result.results)
        print(
            f"Done: {run_result.success_count}/{total} saved"
            + (f", {run_result.skipped_count} skipped" if run_result.skipped_count else "")
            + (f", {run_result.error_count} errors" if run_result.error_count else "")
        )


def main() -> int:
    """Main entry point for slack-postmortem command."""
    parser = create_parser()
    args = parser.parse_args()

    if not args.process_all:
        parser.print_help()
        print("\nError: --all is required.", file=sys.stderr)
        return 1

    # Load config
    try:
        config = load_config()
    except ConfigError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    # Set up output directory
    output_dir = Path(args.output_dir) if args.output_dir else DEFAULT_OUTPUT_DIR
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        print(f"Error creating output directory: {e}", file=sys.stderr)
        return 1

    use_json = args.use_json

    if not use_json:
        print(f"Processing {len(config.channels)} channel(s)...", file=sys.stderr)
        print(f"Output: {output_dir}\n", file=sys.stderr)

    # Process channels
    client = PostmortemClient(config.token)
    run_result = RunResult()

    for channel in config.channels:
        if not use_json:
            print(f"  Extracting: {channel.name}...", file=sys.stderr)

        result = process_channel(client, channel, output_dir)
        run_result.results.append(result)

    if not use_json:
        print(file=sys.stderr)

    print_result(run_result, use_json)

    # Return non-zero only if all channels failed
    if run_result.success_count == 0 and run_result.error_count > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
