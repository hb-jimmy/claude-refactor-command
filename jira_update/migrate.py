#!/usr/bin/env python3
"""
Migrate child issues between Jira projects by epic.

For each child issue of each source epic:
1. Create issue in target project under corresponding target epic
2. Set reporter and assignee to match original
3. Transition to matching status
4. Create Cloners link back to original
5. Recreate cross-reference links (PMR, Blocks, Relates, etc.)
6. Copy comments with attribution headers

Usage:
    jira-migrate --config migration.yaml --dry-run
    jira-migrate --config migration.yaml
    jira-migrate --config migration.yaml --epics HA-1 HA-3

Config file format (YAML):
    epic_map:
      HB-7405: HA-1    # source -> target
      HB-4240: HA-2

    status_map:
      To Do: To Do
      In Progress: In Progress
      QA: In Progress
      Done: Done

    transitions:
      To Do: "11"
      In Progress: "21"
      Blocked: "2"
      Done: "31"

    # Statuses that require going through In Progress first
    needs_intermediate:
      - Blocked

    link_types_to_copy:
      - "Polaris work item link"
      - "Blocks"
      - "Relates"
"""

import argparse
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import yaml

from .client import JiraApiError, JiraClient
from .config import ConfigError, load_credentials


@dataclass
class MigrationResult:
    """Track results for one issue."""
    source_key: str
    target_key: str = ""
    success: bool = False
    errors: List[str] = field(default_factory=list)


@dataclass
class MigrationConfig:
    """Configuration for a migration run."""
    epic_map: Dict[str, str]
    status_map: Dict[str, str]
    transitions: Dict[str, str]
    needs_intermediate: List[str]
    link_types_to_copy: Set[str]


def load_migration_config(config_path: str) -> MigrationConfig:
    """Load migration config from YAML file."""
    path = Path(config_path)
    if not path.exists():
        raise ConfigError(f"Migration config not found: {config_path}")

    with open(path) as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        raise ConfigError(f"Invalid migration config: {config_path}")

    return MigrationConfig(
        epic_map=data.get("epic_map", {}),
        status_map=data.get("status_map", {}),
        transitions=data.get("transitions", {}),
        needs_intermediate=data.get("needs_intermediate", []),
        link_types_to_copy=set(data.get("link_types_to_copy", [])),
    )


def strip_media_from_adf(adf: Dict[str, Any]) -> Dict[str, Any]:
    """Remove mediaSingle/mediaGroup/media nodes from ADF to avoid attachment errors."""
    if not adf or not isinstance(adf, dict):
        return adf

    media_types = {"mediaSingle", "mediaGroup", "media", "mediaInline"}

    def filter_content(nodes: List) -> List:
        filtered = []
        for node in nodes:
            if isinstance(node, dict):
                node_type = node.get("type", "")
                if node_type in media_types:
                    continue
                if "content" in node:
                    node = dict(node)
                    node["content"] = filter_content(node["content"])
                filtered.append(node)
            else:
                filtered.append(node)
        return filtered

    result = dict(adf)
    if "content" in result:
        result["content"] = filter_content(result["content"])
    return result


def build_comment_adf(author_name: str, date_str: str, original_body_adf: Dict) -> Dict:
    """Build ADF comment with attribution header + original body content."""
    header = {
        "type": "paragraph",
        "content": [
            {
                "type": "text",
                "text": f"Originally posted by {author_name} on {date_str}:",
                "marks": [{"type": "strong"}],
            }
        ],
    }

    original_content = original_body_adf.get("content", []) if isinstance(original_body_adf, dict) else []

    return {
        "type": "doc",
        "version": 1,
        "content": [header] + original_content,
    }


class EpicMigrator:
    """Handles migrating all children of one source epic to a target epic."""

    def __init__(self, client: JiraClient, config: MigrationConfig,
                 source_epic: str, target_epic: str, dry_run: bool = False):
        self.client = client
        self.config = config
        self.source_epic = source_epic
        self.target_epic = target_epic
        self.target_project = target_epic.split("-")[0]
        self.dry_run = dry_run
        self.results: List[MigrationResult] = []

    def fetch_children(self) -> List[Dict]:
        """Fetch all children of the source epic via JQL search."""
        all_issues = []
        next_page_token = None

        while True:
            endpoint = "/rest/api/3/search/jql"
            params = {
                "jql": f"parent = {self.source_epic} ORDER BY key ASC",
                "fields": "summary,status,issuetype,labels,reporter,assignee,issuelinks,comment,description",
                "maxResults": 50,
            }
            if next_page_token:
                params["nextPageToken"] = next_page_token

            data = self.client._request("GET", endpoint, params=params)
            if not data:
                break

            issues = data.get("issues", [])
            all_issues.extend(issues)

            next_page_token = data.get("nextPageToken")
            if not next_page_token:
                break

        return all_issues

    def create_target_issue(self, source_issue: Dict) -> Optional[str]:
        """Create an issue in the target project. Returns new issue key."""
        fields = source_issue["fields"]
        issue_type = fields["issuetype"]["name"]
        summary = fields["summary"]
        description_adf = fields.get("description")
        labels = fields.get("labels", [])

        create_fields = {
            "project": {"key": self.target_project},
            "issuetype": {"name": issue_type},
            "summary": summary,
            "labels": labels,
            "parent": {"key": self.target_epic},
        }

        if description_adf:
            if isinstance(description_adf, dict):
                create_fields["description"] = strip_media_from_adf(description_adf)
            elif isinstance(description_adf, str):
                create_fields["description"] = {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [{"type": "text", "text": description_adf}],
                        }
                    ],
                }

        payload = {"fields": create_fields}

        if self.dry_run:
            print(f"  [DRY RUN] Would create {issue_type} '{summary}' under {self.target_epic}")
            return None

        try:
            data = self.client._request("POST", "/rest/api/3/issue", json_data=payload)
        except JiraApiError:
            print(f"    WARNING: Create failed with description, retrying without...")
            create_fields.pop("description", None)
            payload = {"fields": create_fields}
            data = self.client._request("POST", "/rest/api/3/issue", json_data=payload)

        if data:
            return data.get("key", "")
        return None

    def set_reporter(self, target_key: str, reporter_id: str):
        """Set the reporter on a target issue."""
        if not reporter_id:
            return
        endpoint = f"/rest/api/3/issue/{target_key}"
        payload = {"fields": {"reporter": {"accountId": reporter_id}}}
        self.client._request("PUT", endpoint, json_data=payload)

    def set_assignee(self, target_key: str, assignee_id: str):
        """Set the assignee on a target issue."""
        if not assignee_id:
            return
        self.client.assign_issue(target_key, assignee_id)

    def transition_status(self, target_key: str, target_status: str):
        """Transition a target issue to the desired status."""
        if target_status not in self.config.transitions:
            return

        # Check if current status is already the default (To Do)
        default_statuses = {"To Do", "Open", "New"}
        if target_status in default_statuses:
            return

        transition_id = self.config.transitions[target_status]

        # Some statuses require going through an intermediate status first
        if target_status in self.config.needs_intermediate:
            intermediate_id = self.config.transitions.get("In Progress")
            if intermediate_id:
                self.client.transition_issue(target_key, intermediate_id)
                time.sleep(0.2)

        self.client.transition_issue(target_key, transition_id)

    def create_links(self, target_key: str, source_key: str, source_links: List[Dict]):
        """Create Cloners link and recreate other links."""
        # Always create Cloners link: target clones source
        try:
            self.client.create_issue_link("Cloners", target_key, source_key)
        except JiraApiError as e:
            print(f"    WARNING: Failed to create Cloners link {target_key} -> {source_key}: {e}")

        source_project = source_key.split("-")[0]

        for link in source_links:
            link_type = link["type"]["name"]

            if link_type == "Cloners":
                if "outwardIssue" in link:
                    target = link["outwardIssue"]["key"]
                    if target.startswith(f"{source_project}-"):
                        try:
                            self.client.create_issue_link("Cloners", target_key, target)
                        except JiraApiError as e:
                            print(f"    WARNING: Failed Cloners link {target_key} -> {target}: {e}")
                elif "inwardIssue" in link:
                    target = link["inwardIssue"]["key"]
                    if target == source_key:
                        continue
                    if target.startswith(f"{source_project}-"):
                        try:
                            self.client.create_issue_link("Cloners", target_key, target)
                        except JiraApiError as e:
                            print(f"    WARNING: Failed Cloners link {target_key} -> {target}: {e}")
                continue

            if link_type not in self.config.link_types_to_copy:
                continue

            try:
                if "outwardIssue" in link:
                    target = link["outwardIssue"]["key"]
                    self.client.create_issue_link(link_type, target_key, target)
                elif "inwardIssue" in link:
                    target = link["inwardIssue"]["key"]
                    self.client.create_issue_link(link_type, target_key, target)
            except JiraApiError as e:
                print(f"    WARNING: Failed {link_type} link for {target_key}: {e}")

    def copy_comments(self, target_key: str, source_key: str, comments_data: Dict):
        """Copy comments from source issue to target issue with attribution."""
        comments = comments_data.get("comments", [])
        total = comments_data.get("total", 0)

        if total == 0:
            return

        if total > len(comments):
            endpoint = f"/rest/api/3/issue/{source_key}/comment"
            params = {"maxResults": 100, "orderBy": "created"}
            data = self.client._request("GET", endpoint, params=params)
            if data:
                comments = data.get("comments", [])

        for comment in comments:
            author_name = comment.get("author", {}).get("displayName", "Unknown")
            created = comment.get("created", "")
            date_str = created[:16].replace("T", " ") if created else "unknown date"

            body_adf = comment.get("body", {})
            attributed_adf = build_comment_adf(author_name, date_str, body_adf)

            try:
                endpoint = f"/rest/api/3/issue/{target_key}/comment"
                self.client._request("POST", endpoint, json_data={"body": attributed_adf})
            except JiraApiError as e:
                print(f"    WARNING: Failed to copy comment to {target_key}: {e}")

            time.sleep(0.1)

    def migrate_all(self):
        """Run the full migration for this epic."""
        print(f"\n{'='*60}")
        print(f"Migrating children of {self.source_epic} -> {self.target_epic}")
        print(f"{'='*60}")

        children = self.fetch_children()
        print(f"Found {len(children)} children")

        for i, source_issue in enumerate(children, 1):
            source_key = source_issue["key"]
            fields = source_issue["fields"]
            summary = fields.get("summary", "")[:60]
            source_status = fields.get("status", {}).get("name", "To Do")
            issue_type = fields.get("issuetype", {}).get("name", "Task")
            reporter = fields.get("reporter")
            assignee = fields.get("assignee")
            labels = fields.get("labels", [])
            links = fields.get("issuelinks", [])
            comments = fields.get("comment", {})
            comment_count = comments.get("total", 0)

            reporter_name = reporter.get("displayName", "") if reporter else "None"
            reporter_id = reporter.get("accountId", "") if reporter else ""
            assignee_name = assignee.get("displayName", "") if assignee else "None"
            assignee_id = assignee.get("accountId", "") if assignee else ""

            target_status = self.config.status_map.get(source_status, "To Do")

            print(f"\n  [{i}/{len(children)}] {source_key} ({issue_type}) - {summary}")
            print(f"    Status: {source_status} -> {target_status} | Reporter: {reporter_name} | Assignee: {assignee_name}")
            print(f"    Labels: {labels} | Links: {len(links)} | Comments: {comment_count}")

            result = MigrationResult(source_key=source_key)

            try:
                target_key = self.create_target_issue(source_issue)
                if not target_key:
                    if self.dry_run:
                        continue
                    result.errors.append("Failed to create issue")
                    self.results.append(result)
                    continue

                result.target_key = target_key
                print(f"    Created: {target_key}")

                if reporter_id:
                    try:
                        self.set_reporter(target_key, reporter_id)
                    except JiraApiError as e:
                        result.errors.append(f"Reporter: {e}")
                        print(f"    WARNING: Reporter failed: {e}")

                if assignee_id:
                    try:
                        self.set_assignee(target_key, assignee_id)
                    except JiraApiError as e:
                        result.errors.append(f"Assignee: {e}")
                        print(f"    WARNING: Assignee failed: {e}")

                try:
                    self.transition_status(target_key, target_status)
                except JiraApiError as e:
                    result.errors.append(f"Transition: {e}")
                    print(f"    WARNING: Transition to {target_status} failed: {e}")

                self.create_links(target_key, source_key, links)

                if comment_count > 0:
                    self.copy_comments(target_key, source_key, comments)
                    print(f"    Copied {comment_count} comments")

                result.success = True
                print(f"    DONE: {target_key}")

            except Exception as e:
                result.errors.append(str(e))
                print(f"    ERROR: {e}")

            self.results.append(result)
            time.sleep(0.2)

        return self.results


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        prog="jira-migrate",
        description="Migrate child issues between Jira projects by epic.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  Dry run (preview only):
    jira-migrate --config migration.yaml --dry-run

  Full migration:
    jira-migrate --config migration.yaml

  Migrate specific epics only:
    jira-migrate --config migration.yaml --epics HA-1 HA-3
""",
    )

    parser.add_argument(
        "--config",
        required=True,
        help="Path to migration config YAML file.",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what would be migrated without making changes.",
    )

    parser.add_argument(
        "--epics",
        nargs="+",
        metavar="KEY",
        help="Only migrate specific epics (source or target keys).",
    )

    return parser


def main() -> int:
    """Main entry point for the CLI."""
    parser = create_parser()
    args = parser.parse_args()

    if args.dry_run:
        print("*** DRY RUN MODE - No changes will be made ***\n")

    try:
        credentials = load_credentials()
    except ConfigError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    try:
        config = load_migration_config(args.config)
    except ConfigError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    client = JiraClient(credentials)
    all_results = []

    for source_epic, target_epic in config.epic_map.items():
        if args.epics:
            if target_epic not in args.epics and source_epic not in args.epics:
                continue

        migrator = EpicMigrator(client, config, source_epic, target_epic, dry_run=args.dry_run)
        results = migrator.migrate_all()
        all_results.extend(results)

    # Summary
    print(f"\n{'='*60}")
    print("MIGRATION SUMMARY")
    print(f"{'='*60}")

    success = sum(1 for r in all_results if r.success)
    failed = sum(1 for r in all_results if not r.success and r.target_key)
    skipped = sum(1 for r in all_results if not r.success and not r.target_key)

    print(f"Total: {len(all_results)} | Success: {success} | Failed: {failed} | Skipped: {skipped}")

    if any(r.errors for r in all_results):
        print("\nIssues with errors:")
        for r in all_results:
            if r.errors:
                print(f"  {r.source_key} -> {r.target_key or 'N/A'}: {'; '.join(r.errors)}")

    print("\nIssue mapping:")
    for r in all_results:
        if r.target_key:
            status = "OK" if r.success else "ERRORS"
            print(f"  {r.source_key} -> {r.target_key} [{status}]")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
