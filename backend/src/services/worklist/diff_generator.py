"""
Content diff generation utilities for proofreading comparison view.

Phase 8.4: Provides structured diff generation for the frontend visualization
of original vs suggested content changes.
"""

import difflib
import re
from datetime import datetime
from typing import TypedDict


class DiffStats(TypedDict):
    """Statistics about the diff."""
    additions: int
    deletions: int
    total_changes: int
    original_lines: int
    suggested_lines: int


class LineChange(TypedDict, total=False):
    """A single line change entry."""
    type: str  # "addition" or "deletion"
    line_original: int
    line_suggested: int
    content: str


class WordChange(TypedDict, total=False):
    """A single word-level change entry."""
    type: str  # "replace", "delete", or "insert"
    original: str
    suggested: str
    original_pos: list[int]
    suggested_pos: list[int]


class ContentDiffResult(TypedDict, total=False):
    """Result of content diff generation."""
    format: str
    has_changes: bool
    changes: list[LineChange]
    word_changes: list[WordChange]
    stats: DiffStats
    generated_at: str
    migrated: bool


def generate_content_diff(original: str, suggested: str) -> ContentDiffResult:
    """
    Generate structured diff data for frontend visualization.

    Args:
        original: The original content text
        suggested: The suggested/proofread content text

    Returns:
        ContentDiffResult with diff information
    """
    if original == suggested:
        return ContentDiffResult(
            format="unified_diff",
            has_changes=False,
            changes=[],
            stats=DiffStats(
                additions=0,
                deletions=0,
                total_changes=0,
                original_lines=len(original.splitlines()),
                suggested_lines=len(suggested.splitlines()),
            ),
        )

    # Split into lines for line-by-line comparison
    original_lines = original.splitlines(keepends=True)
    suggested_lines = suggested.splitlines(keepends=True)

    # Generate unified diff
    diff = list(difflib.unified_diff(
        original_lines,
        suggested_lines,
        fromfile="original",
        tofile="suggested",
        lineterm=""
    ))

    # Parse diff into structured changes
    changes: list[LineChange] = []
    additions = 0
    deletions = 0
    current_line_original = 0
    current_line_suggested = 0

    for line in diff:
        if line.startswith("@@"):
            match = re.match(r"@@ -(\d+),?\d* \+(\d+),?\d* @@", line)
            if match:
                current_line_original = int(match.group(1))
                current_line_suggested = int(match.group(2))
        elif line.startswith("-") and not line.startswith("---"):
            changes.append(LineChange(
                type="deletion",
                line_original=current_line_original,
                content=line[1:].rstrip("\n"),
            ))
            deletions += 1
            current_line_original += 1
        elif line.startswith("+") and not line.startswith("+++"):
            changes.append(LineChange(
                type="addition",
                line_suggested=current_line_suggested,
                content=line[1:].rstrip("\n"),
            ))
            additions += 1
            current_line_suggested += 1
        elif not line.startswith(("---", "+++")):
            current_line_original += 1
            current_line_suggested += 1

    # Generate word-level diff
    word_changes = generate_word_diff(original, suggested)

    return ContentDiffResult(
        format="unified_diff",
        has_changes=True,
        changes=changes,
        word_changes=word_changes,
        stats=DiffStats(
            additions=additions,
            deletions=deletions,
            total_changes=len(changes),
            original_lines=len(original_lines),
            suggested_lines=len(suggested_lines),
        ),
        generated_at=datetime.utcnow().isoformat(),
    )


def generate_word_diff(original: str, suggested: str) -> list[WordChange]:
    """
    Generate word-level diff for inline highlighting.

    Tokenizes text into Chinese characters, English words, numbers,
    punctuation, and whitespace for precise diff detection.

    Args:
        original: The original content text
        suggested: The suggested/proofread content text

    Returns:
        List of WordChange entries describing modifications
    """
    def tokenize(text: str) -> list[str]:
        """Tokenize text into meaningful units."""
        # Match Chinese characters, English words/numbers, punctuation, whitespace
        return re.findall(r"[\u4e00-\u9fff]+|[a-zA-Z0-9]+|[^\s\w]|\s+", text)

    original_words = tokenize(original)
    suggested_words = tokenize(suggested)

    matcher = difflib.SequenceMatcher(None, original_words, suggested_words)
    word_changes: list[WordChange] = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "replace":
            word_changes.append(WordChange(
                type="replace",
                original="".join(original_words[i1:i2]),
                suggested="".join(suggested_words[j1:j2]),
                original_pos=[i1, i2],
                suggested_pos=[j1, j2],
            ))
        elif tag == "delete":
            word_changes.append(WordChange(
                type="delete",
                original="".join(original_words[i1:i2]),
                original_pos=[i1, i2],
            ))
        elif tag == "insert":
            word_changes.append(WordChange(
                type="insert",
                suggested="".join(suggested_words[j1:j2]),
                suggested_pos=[j1, j2],
            ))

    return word_changes
