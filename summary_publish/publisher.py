"""
Core logic for inserting summaries into markdown files.
"""

import re
import subprocess
from pathlib import Path


SECTION_HEADING = "## Conversation summaries"


def extract_date_from_filename(filepath: Path) -> str:
    """Extract a date string from a summary filename.

    Expects filenames like '2026-02-03.md' or '2026-02-03_2.md'.
    Returns the date portion (e.g., '2026-02-03').

    Raises:
        ValueError: If no date pattern is found in the filename.
    """
    match = re.search(r'(\d{4}-\d{2}-\d{2})', filepath.stem)
    if not match:
        raise ValueError(
            f"Cannot extract date from filename: {filepath.name}\n"
            "Expected a filename containing a date like '2026-02-03.md'."
        )
    return match.group(1)


def insert_summary(
    md_path: Path,
    date: str,
    summary_text: str,
    section_heading: str = SECTION_HEADING,
) -> None:
    """Insert a summary into a markdown file.

    Inserts under the given section heading in descending chronological order
    (most recent first). If the section heading is not found, falls back to
    inserting after the first line (the document title).

    Args:
        md_path: Path to the markdown file.
        date: Date string for the summary header (e.g., '2026-02-03').
        summary_text: The summary content to insert.
        section_heading: The heading to insert under. Defaults to
            '## Conversation summaries'. If not found, inserts after the
            first line.
    """
    content = md_path.read_text()

    # Find the section heading
    section_idx = content.find(section_heading)
    if section_idx == -1:
        # Fallback: insert after the first line (the title)
        first_newline = content.find("\n")
        if first_newline == -1:
            # File is a single line with no newline
            heading_end = len(content)
            content = content + "\n"
            heading_end = len(content)
        else:
            heading_end = first_newline + 1
    else:
        # Position after the section heading line
        heading_end = content.index("\n", section_idx) + 1

    # Build the new entry (summary already contains its own date heading)
    entry = f"\n{summary_text.rstrip()}\n"

    # Get everything after the insertion point
    after_heading = content[heading_end:]

    # Find existing date headings to determine insertion point
    # Summaries start with "## YYYY-MM-DD"
    date_pattern = re.compile(r'^## (\d{4}-\d{2}-\d{2})', re.MULTILINE)
    matches = list(date_pattern.finditer(after_heading))

    if not matches:
        # No existing entries — insert right after the heading
        new_content = content[:heading_end] + entry + content[heading_end:]
    else:
        # Find the right position (descending order, most recent first)
        insert_offset = None
        for m in matches:
            existing_date = m.group(1)
            if date > existing_date:
                # Insert before this entry
                insert_offset = m.start()
                break
            elif date == existing_date:
                # Duplicate date — insert before this one (will appear first)
                insert_offset = m.start()
                break

        if insert_offset is not None:
            abs_offset = heading_end + insert_offset
            new_content = content[:abs_offset] + entry + "\n" + content[abs_offset:]
        else:
            # Date is older than all existing entries — append at the end
            # Find the end of the last entry (next ## heading or end of file)
            next_section = re.search(r'^## ', after_heading[matches[-1].start() + 1:], re.MULTILINE)
            if next_section:
                abs_end = heading_end + matches[-1].start() + 1 + next_section.start()
                new_content = content[:abs_end] + entry + "\n" + content[abs_end:]
            else:
                new_content = content.rstrip() + "\n" + entry

    md_path.write_text(new_content)


def git_commit_and_push(repo_path: Path, date: str, filename: str = "one-on-one.md") -> None:
    """Commit changes and push.

    Args:
        repo_path: Path to the git repository.
        date: Date string used in the commit message.
        filename: The file to commit. Defaults to 'one-on-one.md'.
    """
    subprocess.run(
        ["git", "add", filename],
        cwd=repo_path,
        check=True,
        capture_output=True,
        text=True,
    )

    subprocess.run(
        ["git", "commit", "-m", f"Add summary for {date}"],
        cwd=repo_path,
        check=True,
        capture_output=True,
        text=True,
    )

    subprocess.run(
        ["git", "push"],
        cwd=repo_path,
        check=True,
        capture_output=True,
        text=True,
    )
