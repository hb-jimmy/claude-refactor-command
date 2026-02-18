"""Convert canvas content to clean markdown."""

import re


def convert_to_markdown(content: str) -> str:
    """Convert canvas content to markdown.

    If content starts with '<', treats it as HTML and converts via markdownify.
    Otherwise assumes it's already markdown.

    Args:
        content: Raw canvas content (HTML or markdown).

    Returns:
        Clean markdown string.
    """
    if content.strip().startswith("<"):
        content = _html_to_markdown(content)

    return _clean_markdown(content)


def _html_to_markdown(html: str) -> str:
    """Convert HTML to markdown using markdownify."""
    from markdownify import markdownify
    return markdownify(html, heading_style="ATX", strip=["img"])


def _clean_markdown(text: str) -> str:
    """Clean up excessive blank lines in markdown."""
    # Collapse 3+ consecutive newlines to 2
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip() + "\n"
