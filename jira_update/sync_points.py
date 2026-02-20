"""
Sync story points from HB issues to their HA clones.

For each non-epic issue in HA that has a Cloners link to an HB issue:
- If HB has story points and HA does not, copy the value to HA.
- If both have story points and they differ, report the mismatch.
- If multiple Cloners links exist, match by summary.

Usage:
    jira-sync-points
"""

import argparse
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

from .client import JiraApiError, JiraClient
from .config import ConfigError, load_credentials

HA_STORY_POINTS_FIELD = "customfield_10043"  # "Story point estimate" (HA project)
HB_STORY_POINTS_FIELD = "customfield_10274"  # "Story Points" (HB project)


def search_issues(client: JiraClient, jql: str, fields: List[str]) -> List[Dict[str, Any]]:
    """Fetch all issues matching a JQL query, handling pagination."""
    all_issues = []
    next_page_token = None

    while True:
        params: Dict[str, Any] = {
            "jql": jql,
            "fields": fields,
            "maxResults": 100,
        }
        if next_page_token:
            params["nextPageToken"] = next_page_token

        data = client._request("GET", "/rest/api/3/search/jql", params=params)
        if not data:
            break

        all_issues.extend(data.get("issues", []))

        next_page_token = data.get("nextPageToken")
        if not next_page_token:
            break

    return all_issues


def get_cloner_hb_keys(issue: Dict[str, Any]) -> List[Dict[str, str]]:
    """Extract HB issue keys and summaries from Cloners links."""
    links = issue.get("fields", {}).get("issuelinks", [])
    cloners = []
    for link in links:
        if link.get("type", {}).get("name") != "Cloners":
            continue
        for direction in ("inwardIssue", "outwardIssue"):
            linked = link.get(direction)
            if linked and linked.get("key", "").startswith("HB-"):
                cloners.append({
                    "key": linked["key"],
                    "summary": linked.get("fields", {}).get("summary", ""),
                })
    return cloners


def resolve_hb_key(ha_summary: str, cloners: List[Dict[str, str]]) -> Optional[str]:
    """Pick the correct HB key from cloners links, matching by summary if multiple."""
    if not cloners:
        return None
    if len(cloners) == 1:
        return cloners[0]["key"]
    # Multiple cloners: match by exact summary
    for c in cloners:
        if c["summary"] == ha_summary:
            return c["key"]
    return None


def update_story_points(client: JiraClient, issue_key: str, points: float) -> None:
    """Set the story point estimate on an HA issue."""
    endpoint = f"/rest/api/3/issue/{issue_key}"
    payload = {"fields": {HA_STORY_POINTS_FIELD: points}}
    client._request("PUT", endpoint, json_data=payload)


def print_table(headers: List[str], rows: List[List[str]]) -> None:
    """Print a formatted table."""
    if not rows:
        return
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(cell))

    header_line = "  ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
    separator = "  ".join("-" * w for w in col_widths)
    print(header_line)
    print(separator)
    for row in rows:
        print("  ".join(cell.ljust(col_widths[i]) for i, cell in enumerate(row)))


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    return argparse.ArgumentParser(
        prog="jira-sync-points",
        description="Sync story points from HB issues to their HA clones via Cloners links.",
        epilog="""\
Examples:
  jira-sync-points

Scans all non-epic HA issues. For each with a Cloners link to HB,
copies the HB story points to HA if HA has none. Reports mismatches
where both issues have differing point values.""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )


def main() -> int:
    """Main entry point for the CLI."""
    parser = create_parser()
    parser.parse_args()

    try:
        credentials = load_credentials()
    except ConfigError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    client = JiraClient(credentials)

    # Fetch all non-epic HA issues with story points, summary, and issue links
    print("Fetching HA issues...")
    ha_issues = search_issues(
        client,
        'project = HA AND issuetype != Epic ORDER BY key ASC',
        ["summary", "issuelinks", HA_STORY_POINTS_FIELD],
    )
    print(f"Found {len(ha_issues)} non-epic HA issues")

    # Build list of HA issues with Cloners links to HB
    pairs: List[Tuple[Dict[str, Any], str]] = []  # (ha_issue, hb_key)
    skipped_no_link = 0
    skipped_no_match = 0

    for ha_issue in ha_issues:
        ha_summary = ha_issue.get("fields", {}).get("summary", "")
        cloners = get_cloner_hb_keys(ha_issue)
        if not cloners:
            skipped_no_link += 1
            continue
        hb_key = resolve_hb_key(ha_summary, cloners)
        if not hb_key:
            skipped_no_match += 1
            continue
        pairs.append((ha_issue, hb_key))

    print(f"Found {len(pairs)} HA issues with Cloners links to HB")
    if skipped_no_match > 0:
        print(f"Skipped {skipped_no_match} issues with multiple Cloners links and no summary match")

    # Fetch story points for all linked HB issues
    hb_keys = list(set(hb_key for _, hb_key in pairs))
    print(f"Fetching story points for {len(hb_keys)} HB issues...")

    hb_points: Dict[str, Optional[float]] = {}
    # Batch fetch in groups of 50 to avoid JQL length limits
    for i in range(0, len(hb_keys), 50):
        batch = hb_keys[i:i + 50]
        jql = f'key in ({",".join(batch)})'
        issues = search_issues(client, jql, [HB_STORY_POINTS_FIELD])
        for issue in issues:
            key = issue.get("key", "")
            hb_points[key] = issue.get("fields", {}).get(HB_STORY_POINTS_FIELD)
        time.sleep(0.1)

    # Compare and sync
    updated_rows: List[List[str]] = []
    mismatch_rows: List[List[str]] = []

    for ha_issue, hb_key in pairs:
        ha_key = ha_issue.get("key", "")
        ha_summary = ha_issue.get("fields", {}).get("summary", "")
        ha_pts = ha_issue.get("fields", {}).get(HA_STORY_POINTS_FIELD)
        hb_pts = hb_points.get(hb_key)

        # HB has no story points — nothing to do
        if hb_pts is None:
            continue

        # HA already has story points
        if ha_pts is not None and ha_pts != 0:
            # Check for mismatch
            if ha_pts != hb_pts:
                mismatch_rows.append([
                    ha_key,
                    hb_key,
                    str(ha_pts),
                    str(hb_pts),
                    ha_summary[:60],
                ])
            continue

        # HA has no story points but HB does — sync it
        try:
            update_story_points(client, ha_key, hb_pts)
            updated_rows.append([
                ha_key,
                hb_key,
                str(hb_pts),
                ha_summary[:60],
            ])
        except JiraApiError as e:
            print(f"  ERROR updating {ha_key}: {e}", file=sys.stderr)

        time.sleep(0.1)

    # Print results
    print()
    if updated_rows:
        print(f"Updated {len(updated_rows)} issue(s):\n")
        print_table(["HA Issue", "HB Source", "Points", "Summary"], updated_rows)
    else:
        print("No issues needed story point updates.")

    if mismatch_rows:
        print(f"\n{len(mismatch_rows)} issue(s) with differing story points:\n")
        print_table(
            ["HA Issue", "HB Source", "HA Points", "HB Points", "Summary"],
            mismatch_rows,
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
