"""
Fix reversed issue links on HA issues.

Scans all HA issues and checks cross-project links:
- Cloners links to HB: HA should "clone" HB (HA outward, HB inward).
- Polaris work item links to PMR: HA should "implement" PMR (HA outward, PMR inward).

If a link is reversed, deletes it and recreates it in the correct direction.
Other cross-project link types are reported but not modified.

Usage:
    jira-fix-links
"""

import argparse
import sys
import time
from typing import Any, Dict, List, Tuple

from .client import JiraApiError, JiraClient
from .config import ConfigError, load_credentials

# Link type name -> (target project prefix, expected direction for HA)
# "outward" means HA should be the outward issue (e.g., HA "clones" HB)
FIXABLE_LINKS: Dict[str, Tuple[str, str]] = {
    "Cloners": ("HB", "outward"),
    "Polaris work item link": ("PMR", "outward"),
}


def search_issues(client: JiraClient, jql: str, fields: List[str]) -> List[Dict[str, Any]]:
    """Fetch all issues matching a JQL query, handling pagination."""
    all_issues: List[Dict[str, Any]] = []
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


def get_ha_issue_project(key: str) -> str:
    """Extract project prefix from an issue key."""
    return key.split("-")[0] if "-" in key else ""


def classify_link(ha_key: str, link: Dict[str, Any]) -> Dict[str, Any]:
    """
    Classify a single issue link from an HA issue's perspective.

    When fetching issue X's links, the API returns:
    - inwardIssue: the OTHER issue when X is the outward side (X -> other)
    - outwardIssue: the OTHER issue when X is the inward side (other -> X)

    Returns a dict with: link_id, link_type_name, other_key, ha_direction,
    outward_desc, inward_desc.
    """
    link_type = link.get("type", {})
    link_type_name = link_type.get("name", "")
    link_id = link.get("id", "")
    outward_desc = link_type.get("outward", "")
    inward_desc = link_type.get("inward", "")

    # Determine which side HA is on
    inward_issue = link.get("inwardIssue")
    outward_issue = link.get("outwardIssue")

    if inward_issue:
        # Current issue (HA) is on the inward side
        other_key = inward_issue.get("key", "")
        ha_direction = "inward"
    elif outward_issue:
        # Current issue (HA) is on the outward side
        other_key = outward_issue.get("key", "")
        ha_direction = "outward"
    else:
        return {}

    other_project = get_ha_issue_project(other_key)

    return {
        "link_id": link_id,
        "link_type_name": link_type_name,
        "other_key": other_key,
        "other_project": other_project,
        "ha_direction": ha_direction,
        "outward_desc": outward_desc,
        "inward_desc": inward_desc,
    }


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
    return argparse.ArgumentParser(
        prog="jira-fix-links",
        description="Fix reversed cross-project links on HA issues.",
    )


def main() -> int:
    parser = create_parser()
    parser.parse_args()

    try:
        credentials = load_credentials()
    except ConfigError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    client = JiraClient(credentials)

    print("Fetching all HA issues...")
    ha_issues = search_issues(
        client,
        "project = HA ORDER BY key ASC",
        ["summary", "issuelinks"],
    )
    print(f"Found {len(ha_issues)} HA issues\n")

    fixed_rows: List[List[str]] = []
    error_rows: List[List[str]] = []
    other_rows: List[List[str]] = []

    for issue in ha_issues:
        ha_key = issue.get("key", "")
        links = issue.get("fields", {}).get("issuelinks", [])

        for link in links:
            info = classify_link(ha_key, link)
            if not info:
                continue

            other_project = info["other_project"]

            # Only care about cross-project links
            if other_project == "HA":
                continue

            link_type_name = info["link_type_name"]
            ha_direction = info["ha_direction"]
            other_key = info["other_key"]

            # Check if this is a fixable link type
            if link_type_name in FIXABLE_LINKS:
                expected_project, expected_direction = FIXABLE_LINKS[link_type_name]

                # Only fix links to the expected target project
                if other_project != expected_project:
                    ha_label = info["outward_desc"] if ha_direction == "outward" else info["inward_desc"]
                    other_rows.append([
                        ha_key, ha_label, other_key, link_type_name, ha_direction,
                    ])
                    continue

                if ha_direction == expected_direction:
                    # Already correct
                    continue

                # Direction is wrong — fix it
                link_id = info["link_id"]
                try:
                    client.delete_issue_link(link_id)
                    # Recreate with HA as outward (e.g., "clones", "implements")
                    client.create_issue_link(link_type_name, ha_key, other_key)
                    ha_label = info["outward_desc"]  # Now HA is outward
                    fixed_rows.append([ha_key, ha_label, other_key, link_type_name])
                except JiraApiError as e:
                    error_rows.append([ha_key, other_key, link_type_name, str(e)])
                time.sleep(0.1)
            else:
                # Other cross-project link type — report only
                ha_label = info["outward_desc"] if ha_direction == "outward" else info["inward_desc"]
                other_rows.append([
                    ha_key, ha_label, other_key, link_type_name, ha_direction,
                ])

    # Print results
    if fixed_rows:
        print(f"Fixed {len(fixed_rows)} reversed link(s):\n")
        print_table(["HA Issue", "Relationship", "Other Issue", "Link Type"], fixed_rows)
    else:
        print("No reversed links found.")

    if error_rows:
        print(f"\n{len(error_rows)} error(s) while fixing links:\n")
        print_table(["HA Issue", "Other Issue", "Link Type", "Error"], error_rows)

    if other_rows:
        print(f"\n{len(other_rows)} other cross-project link(s) (no action taken):\n")
        print_table(
            ["HA Issue", "HA Relationship", "Other Issue", "Link Type", "HA Direction"],
            other_rows,
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
