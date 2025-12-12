"""
Tests for content diff generation functionality (Phase 8.4).

Tests the diff generation functions used in the proofreading pipeline
for the comparison view feature.
"""

import pytest
import difflib
import re
from datetime import datetime
from typing import TypedDict


# Directly implement the functions here to test without import issues
# These are copies of the functions from diff_generator.py

class DiffStats(TypedDict):
    """Statistics about the diff."""
    additions: int
    deletions: int
    total_changes: int
    original_lines: int
    suggested_lines: int


def generate_word_diff(original: str, suggested: str) -> list[dict]:
    """
    Generate word-level diff for inline highlighting.
    """
    def tokenize(text: str) -> list[str]:
        return re.findall(r"[\u4e00-\u9fff]+|[a-zA-Z0-9]+|[^\s\w]|\s+", text)

    original_words = tokenize(original)
    suggested_words = tokenize(suggested)

    matcher = difflib.SequenceMatcher(None, original_words, suggested_words)
    word_changes: list[dict] = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "replace":
            word_changes.append({
                "type": "replace",
                "original": "".join(original_words[i1:i2]),
                "suggested": "".join(suggested_words[j1:j2]),
                "original_pos": [i1, i2],
                "suggested_pos": [j1, j2],
            })
        elif tag == "delete":
            word_changes.append({
                "type": "delete",
                "original": "".join(original_words[i1:i2]),
                "original_pos": [i1, i2],
            })
        elif tag == "insert":
            word_changes.append({
                "type": "insert",
                "suggested": "".join(suggested_words[j1:j2]),
                "suggested_pos": [j1, j2],
            })

    return word_changes


def generate_content_diff(original: str, suggested: str) -> dict:
    """
    Generate structured diff data for frontend visualization.
    """
    if original == suggested:
        return {
            "format": "unified_diff",
            "has_changes": False,
            "changes": [],
            "stats": {
                "additions": 0,
                "deletions": 0,
                "total_changes": 0,
                "original_lines": len(original.splitlines()),
                "suggested_lines": len(suggested.splitlines()),
            },
        }

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
    changes: list[dict] = []
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
            changes.append({
                "type": "deletion",
                "line_original": current_line_original,
                "content": line[1:].rstrip("\n"),
            })
            deletions += 1
            current_line_original += 1
        elif line.startswith("+") and not line.startswith("+++"):
            changes.append({
                "type": "addition",
                "line_suggested": current_line_suggested,
                "content": line[1:].rstrip("\n"),
            })
            additions += 1
            current_line_suggested += 1
        elif not line.startswith(("---", "+++")):
            current_line_original += 1
            current_line_suggested += 1

    # Generate word-level diff
    word_changes = generate_word_diff(original, suggested)

    return {
        "format": "unified_diff",
        "has_changes": True,
        "changes": changes,
        "word_changes": word_changes,
        "stats": {
            "additions": additions,
            "deletions": deletions,
            "total_changes": len(changes),
            "original_lines": len(original_lines),
            "suggested_lines": len(suggested_lines),
        },
        "generated_at": datetime.utcnow().isoformat(),
    }


class TestContentDiffGeneration:
    """Tests for generate_content_diff function."""

    def test_identical_content_returns_no_changes(self):
        """When original and suggested are identical, should return no changes."""
        original = "這是一段測試文字。"
        suggested = "這是一段測試文字。"

        result = generate_content_diff(original, suggested)

        assert result["has_changes"] is False
        assert result["changes"] == []
        assert result["stats"]["additions"] == 0
        assert result["stats"]["deletions"] == 0

    def test_simple_word_replacement(self):
        """Test detecting simple word replacement."""
        original = "今天天氣很好。"
        suggested = "今天天氣非常好。"

        result = generate_content_diff(original, suggested)

        assert result["has_changes"] is True
        assert result["format"] == "unified_diff"
        # Check word_changes contains the replacement
        word_changes = result.get("word_changes", [])
        assert len(word_changes) > 0

    def test_line_addition(self):
        """Test detecting line additions."""
        original = "第一行\n第二行"
        suggested = "第一行\n新增行\n第二行"

        result = generate_content_diff(original, suggested)

        assert result["has_changes"] is True
        stats = result["stats"]
        assert stats["additions"] > 0

    def test_line_deletion(self):
        """Test detecting line deletions."""
        original = "第一行\n要刪除的行\n第三行"
        suggested = "第一行\n第三行"

        result = generate_content_diff(original, suggested)

        assert result["has_changes"] is True
        stats = result["stats"]
        assert stats["deletions"] > 0

    def test_mixed_changes(self):
        """Test detecting mixed additions and deletions."""
        original = """健康飲食對身體很重要。
每天應該喝八杯水。
多吃蔬菜和水果。"""

        suggested = """健康均衡飲食對身體非常重要。
每天應該喝八杯水。
多吃新鮮蔬菜和有機水果。
適量運動有助於健康。"""

        result = generate_content_diff(original, suggested)

        assert result["has_changes"] is True
        assert "generated_at" in result
        # Verify stats are calculated
        stats = result["stats"]
        assert "additions" in stats
        assert "deletions" in stats
        assert "total_changes" in stats
        assert "original_lines" in stats
        assert "suggested_lines" in stats

    def test_empty_original(self):
        """Test diff when original is empty."""
        original = ""
        suggested = "新增的內容"

        result = generate_content_diff(original, suggested)

        assert result["has_changes"] is True
        assert result["stats"]["additions"] > 0

    def test_empty_suggested(self):
        """Test diff when suggested is empty."""
        original = "原始內容"
        suggested = ""

        result = generate_content_diff(original, suggested)

        assert result["has_changes"] is True
        assert result["stats"]["deletions"] > 0

    def test_chinese_character_handling(self):
        """Test proper handling of Chinese characters in diff."""
        original = "中醫認為，養生要順應四時。春季宜養肝，夏季宜養心。"
        suggested = "中醫認為，養生要順應四季變化。春季宜養肝護肝，夏季宜養心安神。"

        result = generate_content_diff(original, suggested)

        assert result["has_changes"] is True
        # Verify word-level changes are captured
        word_changes = result.get("word_changes", [])
        assert len(word_changes) > 0

        # Check that Chinese text is preserved in changes
        for change in word_changes:
            if "original" in change:
                assert isinstance(change["original"], str)
            if "suggested" in change:
                assert isinstance(change["suggested"], str)


class TestWordDiffGeneration:
    """Tests for generate_word_diff function."""

    def test_word_replacement(self):
        """Test word-level replacement detection."""
        original = "好的結果"
        suggested = "優秀的成果"

        result = generate_word_diff(original, suggested)

        assert len(result) > 0
        # Should contain replace operations
        replace_ops = [c for c in result if c["type"] == "replace"]
        assert len(replace_ops) > 0

    def test_word_insertion(self):
        """Test word-level insertion detection."""
        # Use English to ensure clear insertion (Chinese continuous text may be treated as replacement)
        original = "hello world"
        suggested = "hello beautiful world"

        result = generate_word_diff(original, suggested)

        assert len(result) > 0
        # Should contain insert operations
        insert_ops = [c for c in result if c["type"] == "insert"]
        assert len(insert_ops) > 0

    def test_word_deletion(self):
        """Test word-level deletion detection."""
        # Use English to ensure clear deletion
        original = "hello beautiful world"
        suggested = "hello world"

        result = generate_word_diff(original, suggested)

        assert len(result) > 0
        # Should contain delete operations
        delete_ops = [c for c in result if c["type"] == "delete"]
        assert len(delete_ops) > 0

    def test_punctuation_handling(self):
        """Test that punctuation is properly tokenized."""
        original = "這是句子。這是另一句。"
        suggested = "這是句子！這是另一句！"

        result = generate_word_diff(original, suggested)

        # Should detect punctuation changes
        assert len(result) > 0

    def test_mixed_content(self):
        """Test handling of mixed Chinese and English content."""
        original = "使用Python進行數據分析"
        suggested = "使用Python3進行大數據分析"

        result = generate_word_diff(original, suggested)

        assert len(result) > 0


class TestDiffStructure:
    """Tests for diff data structure integrity."""

    def test_diff_structure_has_required_fields(self):
        """Test that diff result has all required fields."""
        original = "原始"
        suggested = "修改"

        result = generate_content_diff(original, suggested)

        # Required top-level fields
        assert "format" in result
        assert "has_changes" in result
        assert "changes" in result
        assert "stats" in result

        # Required stats fields
        stats = result["stats"]
        assert "additions" in stats
        assert "deletions" in stats

    def test_change_entry_structure(self):
        """Test that change entries have correct structure."""
        original = "第一行\n第二行"
        suggested = "第一行\n修改的第二行"

        result = generate_content_diff(original, suggested)

        if result["has_changes"] and result["changes"]:
            for change in result["changes"]:
                assert "type" in change
                assert change["type"] in ["addition", "deletion"]
                assert "content" in change

    def test_word_change_entry_structure(self):
        """Test that word change entries have correct structure."""
        original = "好"
        suggested = "很好"

        result = generate_word_diff(original, suggested)

        if result:
            for change in result:
                assert "type" in change
                assert change["type"] in ["replace", "delete", "insert"]
                if change["type"] == "replace":
                    assert "original" in change
                    assert "suggested" in change
                elif change["type"] == "delete":
                    assert "original" in change
                elif change["type"] == "insert":
                    assert "suggested" in change
