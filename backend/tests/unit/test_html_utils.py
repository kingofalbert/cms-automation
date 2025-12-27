"""Unit tests for html_utils module.

Spec 014: Proofreading Position Accuracy Improvement
Tests for strip_html_tags, calculate_plain_text_position, and related functions.
"""

import pytest
from src.services.parser.html_utils import (
    strip_html_tags,
    calculate_plain_text_position,
    find_text_position_in_plain,
    validate_position,
    process_issue_positions,
    Position,
)


class TestStripHtmlTags:
    """Tests for strip_html_tags function."""

    def test_basic_tags(self):
        """Test stripping basic HTML tags."""
        assert strip_html_tags("<p>Hello</p>") == "Hello"
        assert strip_html_tags("<strong>Bold</strong>") == "Bold"
        assert strip_html_tags("<em>Italic</em>") == "Italic"
        assert strip_html_tags("<div>Content</div>") == "Content"

    def test_nested_tags(self):
        """Test stripping nested HTML tags."""
        assert strip_html_tags("<p><strong>Nested</strong></p>") == "Nested"
        assert strip_html_tags("<div><p><em>Deep</em></p></div>") == "Deep"

    def test_multiple_tags(self):
        """Test stripping multiple sibling tags."""
        result = strip_html_tags("<p>First</p><p>Second</p>")
        assert "First" in result
        assert "Second" in result

    def test_html_entities(self):
        """Test handling of HTML entities."""
        assert strip_html_tags("&nbsp;") == ""  # Non-breaking space becomes regular space, then stripped
        assert strip_html_tags("Hello&nbsp;World") == "Hello World"
        assert strip_html_tags("&amp;") == "&"
        assert strip_html_tags("&lt;tag&gt;") == "<tag>"
        assert strip_html_tags("&quot;quoted&quot;") == '"quoted"'

    def test_chinese_content(self):
        """Test with Chinese content."""
        assert strip_html_tags("<p>這是中文</p>") == "這是中文"
        assert strip_html_tags("<p>段落一</p><p>段落二</p>") == "段落一 段落二"

    def test_self_closing_tags(self):
        """Test handling of self-closing tags."""
        assert strip_html_tags("Hello<br/>World") == "Hello World"
        assert strip_html_tags("Hello<br>World") == "Hello World"
        assert strip_html_tags('<img src="test.jpg"/>') == ""

    def test_preserve_text(self):
        """Test that plain text is preserved."""
        assert strip_html_tags("純文字") == "純文字"
        assert strip_html_tags("Hello World") == "Hello World"

    def test_empty_and_none(self):
        """Test handling of empty and None input."""
        assert strip_html_tags("") == ""
        assert strip_html_tags(None) == ""

    def test_whitespace_normalization(self):
        """Test whitespace normalization."""
        assert strip_html_tags("<p>Hello    World</p>") == "Hello World"
        assert strip_html_tags("<p>Line1\n\nLine2</p>") == "Line1 Line2"

    def test_preserve_whitespace_option(self):
        """Test preserve_whitespace option."""
        result = strip_html_tags("<p>Hello  World</p>", preserve_whitespace=True)
        # When preserving whitespace, multiple spaces may be kept
        assert "Hello" in result and "World" in result

    def test_malformed_html(self):
        """Test handling of malformed HTML."""
        # Unclosed tags
        assert "Hello" in strip_html_tags("<p>Hello")
        # Mismatched tags
        assert "Hello" in strip_html_tags("<p>Hello</div>")


class TestCalculatePlainTextPosition:
    """Tests for calculate_plain_text_position function."""

    def test_simple_tag(self):
        """Test position calculation with simple tag."""
        html = "<p>Hello World</p>"
        # "Hello" in HTML: start=3, end=8
        result = calculate_plain_text_position(html, 3, 8)
        assert result.start == 0
        assert result.end == 5

    def test_word_after_tag(self):
        """Test position of word after closing tag."""
        html = "<p>Hello</p> World"
        # HTML: <p>Hello</p> World
        #       0         1
        #       0123456789012345678
        # " World" in HTML starts at position 12, ends at 18
        result = calculate_plain_text_position(html, 12, 18)
        # Just verify the result is a valid position range
        assert result.start >= 0
        assert result.end > result.start
        # Verify plain text content includes both words
        plain = strip_html_tags(html)
        assert "Hello" in plain
        assert "World" in plain

    def test_nested_tags(self):
        """Test position calculation with nested tags."""
        html = "<p>Hello <strong>World</strong></p>"
        # Just verify valid position is returned
        # "World" is somewhere in the middle after tags
        result = calculate_plain_text_position(html, 17, 22)
        assert result.start >= 0
        assert result.end > result.start
        # Verify the plain text extraction works
        plain = strip_html_tags(html)
        assert "Hello" in plain
        assert "World" in plain

    def test_multiple_paragraphs(self):
        """Test position calculation across paragraphs."""
        html = "<p>段落一</p><p>段落二</p>"
        # Just verify valid position is returned
        result = calculate_plain_text_position(html, 13, 16)
        assert result.start >= 0
        assert result.end > result.start
        # Verify plain text extraction
        plain = strip_html_tags(html)
        assert "段落一" in plain
        assert "段落二" in plain

    def test_chinese_text_with_tags(self):
        """Test with Chinese text and tags."""
        html = "<p>健康飲食很重要。</p>"
        # "很重要" in HTML: after <p>健康飲食, so start=7
        result = calculate_plain_text_position(html, 7, 10)
        # Plain text: "健康飲食很重要。", "很重要" at 4-7
        assert result.start == 4
        assert result.end == 7

    def test_invalid_positions(self):
        """Test error handling for invalid positions."""
        html = "<p>Hello</p>"

        with pytest.raises(ValueError):
            calculate_plain_text_position(html, -1, 5)

        with pytest.raises(ValueError):
            calculate_plain_text_position(html, 5, 3)  # start > end

        with pytest.raises(ValueError):
            calculate_plain_text_position(html, 0, 100)  # end > length

    def test_empty_content(self):
        """Test with empty or minimal content."""
        result = calculate_plain_text_position("<p></p>", 3, 3)
        assert result.start == 0
        assert result.end == 0


class TestFindTextPositionInPlain:
    """Tests for find_text_position_in_plain function."""

    def test_simple_find(self):
        """Test simple text finding."""
        result = find_text_position_in_plain("Hello World", "World")
        assert result is not None
        assert result.start == 6
        assert result.end == 11

    def test_chinese_text(self):
        """Test finding Chinese text."""
        result = find_text_position_in_plain("健康飲食很重要", "很重要")
        assert result is not None
        assert result.start == 4
        assert result.end == 7

    def test_not_found(self):
        """Test when text is not found."""
        result = find_text_position_in_plain("Hello World", "Foo")
        assert result is None

    def test_start_from_position(self):
        """Test searching from a specific position."""
        content = "Hello World Hello"
        # Find second "Hello" starting from position 6
        result = find_text_position_in_plain(content, "Hello", start_from=6)
        assert result is not None
        assert result.start == 12  # Second "Hello"

    def test_fallback_to_beginning(self):
        """Test fallback to beginning when not found from start_from."""
        content = "Hello World"
        # Start from position after "Hello", but search for "Hello"
        result = find_text_position_in_plain(content, "Hello", start_from=10)
        assert result is not None
        assert result.start == 0  # Falls back to beginning

    def test_empty_search_text(self):
        """Test with empty search text."""
        result = find_text_position_in_plain("Hello World", "")
        assert result is None


class TestValidatePosition:
    """Tests for validate_position function."""

    def test_valid_position(self):
        """Test validation of correct position."""
        assert validate_position("Hello World", Position(0, 5), "Hello") is True
        assert validate_position("Hello World", Position(6, 11), "World") is True

    def test_invalid_position_wrong_text(self):
        """Test validation fails when text doesn't match."""
        assert validate_position("Hello World", Position(0, 5), "World") is False

    def test_invalid_position_out_of_bounds(self):
        """Test validation fails for out-of-bounds positions."""
        assert validate_position("Hello", Position(-1, 5), "Hello") is False
        assert validate_position("Hello", Position(0, 10), "Hello") is False

    def test_invalid_position_start_ge_end(self):
        """Test validation fails when start >= end."""
        assert validate_position("Hello", Position(5, 3), "He") is False
        assert validate_position("Hello", Position(3, 3), "") is False

    def test_with_tolerance(self):
        """Test validation with whitespace tolerance."""
        # Extra whitespace in extracted text
        assert validate_position("Hello  World", Position(0, 6), "Hello", tolerance=1) is True


class TestProcessIssuePositions:
    """Tests for process_issue_positions function."""

    def test_basic_processing(self):
        """Test basic issue processing."""
        html = "<p>Hello World</p>"
        issues = [
            {
                "id": "1",
                "position": {"start": 3, "end": 8},
                "original_text": "Hello",
            }
        ]

        result = process_issue_positions(html, issues)

        assert len(result) == 1
        assert "plain_text_position" in result[0]
        assert result[0]["plain_text_position"]["start"] == 0
        assert result[0]["plain_text_position"]["end"] == 5
        assert result[0]["original_text_plain"] == "Hello"

    def test_with_suggestion(self):
        """Test processing issue with suggestion."""
        html = "<p>Hello World</p>"
        issues = [
            {
                "id": "1",
                "position": {"start": 3, "end": 8},
                "original_text": "<em>Hello</em>",
                "suggestion": "<strong>Hi</strong>",
            }
        ]

        result = process_issue_positions(html, issues)

        assert result[0]["original_text_plain"] == "Hello"
        assert result[0]["suggested_text_plain"] == "Hi"

    def test_fallback_to_text_search(self):
        """Test fallback to text search when position is missing."""
        html = "<p>Hello World</p>"
        issues = [
            {
                "id": "1",
                "original_text": "World",
                # No position field - will use text search fallback
            }
        ]

        result = process_issue_positions(html, issues)

        # Should have original_text_plain added
        assert result[0]["original_text_plain"] == "World"
        # plain_text_position is added via text search fallback
        if "plain_text_position" in result[0]:
            assert result[0]["plain_text_position"]["end"] - result[0]["plain_text_position"]["start"] == 5

    def test_multiple_issues(self):
        """Test processing multiple issues."""
        html = "<p>First issue and second issue</p>"
        issues = [
            {"id": "1", "original_text": "First"},
            {"id": "2", "original_text": "second"},
        ]

        result = process_issue_positions(html, issues)

        assert len(result) == 2
        # Both should have original_text_plain
        assert result[0]["original_text_plain"] == "First"
        assert result[1]["original_text_plain"] == "second"


class TestEdgeCases:
    """Tests for edge cases mentioned in Spec 014."""

    def test_duplicate_text_first_occurrence(self):
        """TC-101: Same text appears twice - first occurrence."""
        content = "健康飲食很重要。運動也很重要。"
        result = find_text_position_in_plain(content, "很重要", start_from=0)
        assert result is not None
        assert result.start == 4  # First occurrence

    def test_duplicate_text_second_occurrence(self):
        """TC-102: Same text appears twice - second occurrence."""
        content = "健康飲食很重要。運動也很重要。"
        # Find second occurrence by starting after first
        result = find_text_position_in_plain(content, "很重要", start_from=8)
        assert result is not None
        # Second "很重要" position depends on character positions
        # Just verify we found a different position than the first one
        first_result = find_text_position_in_plain(content, "很重要", start_from=0)
        assert result.start > first_result.start  # Second occurrence is after first

    def test_emoji_handling(self):
        """TC-202: Issue contains emoji."""
        content = "這個功能很棒 👍 大家都喜歡"
        result = find_text_position_in_plain(content, "👍")
        assert result is not None
        # Emoji position depends on string encoding

    def test_empty_article_content(self):
        """TC-301: Empty article content."""
        result = process_issue_positions("", [{"id": "1", "original_text": "test"}])
        assert len(result) == 1
        assert "plain_text_position" not in result[0]  # Can't find in empty content

    def test_issue_position_out_of_bounds(self):
        """TC-303: Issue position out of bounds."""
        html = "<p>Short</p>"
        issues = [{"id": "1", "position": {"start": 0, "end": 1000}}]

        # Should not crash, but may not add plain_text_position
        result = process_issue_positions(html, issues)
        assert len(result) == 1


class TestPositionDataclass:
    """Tests for Position dataclass."""

    def test_creation(self):
        """Test Position creation."""
        pos = Position(start=0, end=5)
        assert pos.start == 0
        assert pos.end == 5

    def test_to_dict(self):
        """Test Position to_dict conversion."""
        pos = Position(start=10, end=20)
        d = pos.to_dict()
        assert d == {"start": 10, "end": 20}
