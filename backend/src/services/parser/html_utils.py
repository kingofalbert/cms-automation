"""HTML utility functions for text extraction and position calculation.

This module provides utilities for:
- Stripping HTML tags while preserving text content
- Calculating plain text positions from HTML positions
- Handling HTML entities and special characters

Part of Spec 014: Proofreading Position Accuracy Improvement
"""

from __future__ import annotations

import html
import re
from dataclasses import dataclass
from typing import Optional

from bs4 import BeautifulSoup


@dataclass
class Position:
    """Represents a text position range."""

    start: int
    end: int

    def to_dict(self) -> dict[str, int]:
        """Convert to dictionary for JSON serialization."""
        return {"start": self.start, "end": self.end}


def strip_html_tags(
    html_content: str | None,
    preserve_whitespace: bool = False,
    decode_entities: bool = True,
) -> str:
    """Strip HTML tags from content, returning plain text.

    This function handles:
    - Standard HTML tags (<p>, <strong>, <div>, etc.)
    - Self-closing tags (<br/>, <img/>, etc.)
    - HTML entities (&nbsp;, &amp;, &lt;, etc.)
    - Nested tags
    - Malformed HTML

    Args:
        html_content: HTML string to process. Can be None or empty.
        preserve_whitespace: If True, preserve original whitespace.
                            If False (default), normalize to single spaces.
        decode_entities: If True (default), decode HTML entities.
                        If False, leave entities encoded.

    Returns:
        Plain text string with HTML tags removed.

    Examples:
        >>> strip_html_tags("<p>Hello</p>")
        'Hello'
        >>> strip_html_tags("<p>Hello <strong>World</strong></p>")
        'Hello World'
        >>> strip_html_tags("&nbsp;&amp;")
        ' &'
        >>> strip_html_tags(None)
        ''
    """
    if not html_content:
        return ""

    # Use BeautifulSoup for robust HTML parsing
    # 'html.parser' is the built-in parser, no external dependencies
    soup = BeautifulSoup(html_content, "html.parser")

    # Get text content, preserving some structure with separator
    if preserve_whitespace:
        text = soup.get_text()
    else:
        text = soup.get_text(separator=" ")

    # Decode HTML entities if requested
    if decode_entities:
        text = html.unescape(text)

    # Normalize whitespace unless preserving
    if not preserve_whitespace:
        # Collapse multiple whitespace characters into single space
        text = re.sub(r"\s+", " ", text)
        text = text.strip()

    return text


def calculate_plain_text_position(
    html_content: str,
    html_start: int,
    html_end: int,
) -> Position:
    """Convert HTML-based positions to plain text positions.

    This is the core algorithm for Spec 014. When AI analyzes HTML content,
    it returns positions based on the HTML string. But the frontend displays
    plain text (without HTML tags). This function converts HTML positions
    to their equivalent plain text positions.

    Algorithm:
    1. Take the HTML content up to html_start, strip tags → plain_start
    2. Take the HTML content up to html_end, strip tags → plain_end

    Args:
        html_content: The full HTML content string.
        html_start: Start position in HTML content.
        html_end: End position in HTML content.

    Returns:
        Position object with start and end in plain text coordinates.

    Raises:
        ValueError: If positions are invalid (negative, out of bounds, start > end).

    Examples:
        >>> html = "<p>Hello World</p>"
        >>> calculate_plain_text_position(html, 3, 8)  # "Hello" in HTML
        Position(start=0, end=5)  # "Hello" in plain text

        >>> html = "<p>段落一</p><p>段落二</p>"
        >>> calculate_plain_text_position(html, 12, 15)  # "段落二" in HTML
        Position(start=4, end=7)  # "段落二" in plain text (with space separator)
    """
    # Validate inputs
    if html_start < 0:
        raise ValueError(f"html_start cannot be negative: {html_start}")
    if html_end < 0:
        raise ValueError(f"html_end cannot be negative: {html_end}")
    if html_start > html_end:
        raise ValueError(
            f"html_start ({html_start}) cannot be greater than html_end ({html_end})"
        )
    if html_end > len(html_content):
        raise ValueError(
            f"html_end ({html_end}) exceeds content length ({len(html_content)})"
        )

    # Calculate plain text length up to html_start
    content_before_start = html_content[:html_start]
    plain_before_start = strip_html_tags(content_before_start)
    plain_start = len(plain_before_start)

    # Calculate plain text length up to html_end
    content_before_end = html_content[:html_end]
    plain_before_end = strip_html_tags(content_before_end)
    plain_end = len(plain_before_end)

    return Position(start=plain_start, end=plain_end)


def find_text_position_in_plain(
    plain_content: str,
    search_text: str,
    start_from: int = 0,
) -> Optional[Position]:
    """Find text position in plain content using text search.

    This is the fallback mechanism when plain_text_position is not available.
    Used for backward compatibility with legacy data.

    Args:
        plain_content: The plain text content to search in.
        search_text: The text to find.
        start_from: Position to start searching from (for sequential issues).

    Returns:
        Position if found, None if not found.

    Examples:
        >>> find_text_position_in_plain("Hello World", "World")
        Position(start=6, end=11)
        >>> find_text_position_in_plain("Hello World", "Foo")
        None
    """
    if not search_text:
        return None

    # Try from start_from position first
    index = plain_content.find(search_text, start_from)

    # If not found, try from beginning (for out-of-order issues)
    if index == -1 and start_from > 0:
        index = plain_content.find(search_text)

    if index == -1:
        return None

    return Position(start=index, end=index + len(search_text))


def validate_position(
    content: str,
    position: Position,
    expected_text: str,
    tolerance: int = 0,
) -> bool:
    """Validate that a position points to the expected text.

    Used by the frontend to verify positions before highlighting.
    If validation fails, the frontend should fall back to text search.

    Args:
        content: The content string to validate against.
        position: The position to validate.
        expected_text: The text expected at this position.
        tolerance: Allow minor differences (e.g., whitespace).

    Returns:
        True if position points to expected text, False otherwise.

    Examples:
        >>> validate_position("Hello World", Position(0, 5), "Hello")
        True
        >>> validate_position("Hello World", Position(0, 5), "World")
        False
    """
    if position.start < 0 or position.end > len(content):
        return False

    if position.start >= position.end:
        return False

    extracted = content[position.start : position.end]

    if tolerance == 0:
        return extracted == expected_text

    # With tolerance, compare normalized versions
    normalized_extracted = re.sub(r"\s+", " ", extracted).strip()
    normalized_expected = re.sub(r"\s+", " ", expected_text).strip()

    return normalized_extracted == normalized_expected


# Convenience function for batch processing
def process_issue_positions(
    html_content: str,
    issues: list[dict],
) -> list[dict]:
    """Process a list of issues, adding plain text positions.

    This is a convenience function for batch processing issues
    returned by the AI proofreading analyzer.

    Args:
        html_content: The full HTML content.
        issues: List of issue dicts with 'position' field containing
                {'start': int, 'end': int} for HTML positions.

    Returns:
        Same list with 'plain_text_position' added to each issue.

    Example:
        >>> html = "<p>Hello World</p>"
        >>> issues = [{"id": "1", "position": {"start": 3, "end": 8}}]
        >>> process_issue_positions(html, issues)
        [{"id": "1", "position": {"start": 3, "end": 8},
          "plain_text_position": {"start": 0, "end": 5}}]
    """
    plain_content = strip_html_tags(html_content)

    for issue in issues:
        html_position = issue.get("position")
        original_text = issue.get("original_text")

        if html_position:
            try:
                plain_pos = calculate_plain_text_position(
                    html_content,
                    html_position["start"],
                    html_position["end"],
                )
                issue["plain_text_position"] = plain_pos.to_dict()
            except ValueError:
                # If position calculation fails, try text search
                if original_text:
                    plain_text = strip_html_tags(original_text)
                    found_pos = find_text_position_in_plain(plain_content, plain_text)
                    if found_pos:
                        issue["plain_text_position"] = found_pos.to_dict()

        # Add plain text versions of text fields
        if original_text:
            issue["original_text_plain"] = strip_html_tags(original_text)

        suggested_text = issue.get("suggestion") or issue.get("suggested_text")
        if suggested_text:
            issue["suggested_text_plain"] = strip_html_tags(suggested_text)

    return issues
