"""Tests for GoogleDocsHTMLParser."""

import pytest

from src.services.google_drive.sync_service import GoogleDocsHTMLParser


class TestGoogleDocsHTMLParser:
    """Test cases for HTML parsing from Google Docs exports."""

    def test_basic_paragraphs(self):
        """Test parsing basic paragraph content."""
        html = """
        <p>First paragraph.</p>
        <p>Second paragraph.</p>
        """
        parser = GoogleDocsHTMLParser()
        parser.feed(html)
        result = parser.get_clean_text()

        assert "First paragraph." in result
        assert "Second paragraph." in result

    def test_bold_and_italic(self):
        """Test parsing bold and italic formatting."""
        html = """
        <p>This is <b>bold</b> and this is <i>italic</i>.</p>
        """
        parser = GoogleDocsHTMLParser()
        parser.feed(html)
        result = parser.get_clean_text()

        assert "**bold**" in result
        assert "_italic_" in result

    def test_links(self):
        """Test parsing hyperlinks."""
        html = """
        <p>Check out <a href="https://example.com">this link</a>.</p>
        """
        parser = GoogleDocsHTMLParser()
        parser.feed(html)
        result = parser.get_clean_text()

        assert "[this link](https://example.com)" in result

    def test_headings(self):
        """Test parsing heading tags."""
        html = """
        <h1>Main Title</h1>
        <h2>Subtitle</h2>
        <p>Content here.</p>
        """
        parser = GoogleDocsHTMLParser()
        parser.feed(html)
        result = parser.get_clean_text()

        assert "# Main Title" in result
        assert "## Subtitle" in result

    def test_unordered_list(self):
        """Test parsing unordered lists."""
        html = """
        <ul>
            <li>First item</li>
            <li>Second item</li>
            <li>Third item</li>
        </ul>
        """
        parser = GoogleDocsHTMLParser()
        parser.feed(html)
        result = parser.get_clean_text()

        assert "- First item" in result
        assert "- Second item" in result
        assert "- Third item" in result

    def test_nested_lists(self):
        """Test parsing nested lists."""
        html = """
        <ul>
            <li>Parent item
                <ul>
                    <li>Child item</li>
                </ul>
            </li>
        </ul>
        """
        parser = GoogleDocsHTMLParser()
        parser.feed(html)
        result = parser.get_clean_text()

        assert "- Parent item" in result
        assert "  - Child item" in result  # Indented

    def test_complex_document(self):
        """Test parsing a complex document with multiple elements."""
        html = """
        <h1>Article Title</h1>
        <p>This is an <b>introduction</b> paragraph with a <a href="https://example.com">link</a>.</p>
        <h2>Section 1</h2>
        <p>First section content.</p>
        <ul>
            <li>Point one</li>
            <li>Point two</li>
        </ul>
        <h2>Section 2</h2>
        <p>Second section with <i>emphasis</i>.</p>
        """
        parser = GoogleDocsHTMLParser()
        parser.feed(html)
        result = parser.get_clean_text()

        # Check all major elements are present
        assert "# Article Title" in result
        assert "**introduction**" in result
        assert "[link](https://example.com)" in result
        assert "## Section 1" in result
        assert "- Point one" in result
        assert "- Point two" in result
        assert "_emphasis_" in result

    def test_empty_document(self):
        """Test parsing empty document."""
        html = ""
        parser = GoogleDocsHTMLParser()
        parser.feed(html)
        result = parser.get_clean_text()

        assert result == ""

    def test_whitespace_handling(self):
        """Test proper whitespace handling."""
        html = """
        <p>  Text with   extra   spaces  </p>
        """
        parser = GoogleDocsHTMLParser()
        parser.feed(html)
        result = parser.get_clean_text()

        # Should clean up excessive whitespace
        assert "Text with extra spaces" in result

    def test_google_docs_style_html(self):
        """Test parsing actual Google Docs-style HTML with inline styles."""
        html = """
        <html>
        <body class="c0">
            <p class="c1"><span class="c2">Title Text</span></p>
            <p class="c1"><span class="c3">Regular paragraph with </span>
            <span class="c4">bold text</span><span class="c3"> and </span>
            <span class="c5">italic text</span><span class="c3">.</span></p>
            <ul class="c6 lst-kix_list1-0 start">
                <li class="c1 c7"><span class="c3">List item 1</span></li>
                <li class="c1 c7"><span class="c3">List item 2</span></li>
            </ul>
        </body>
        </html>
        """
        parser = GoogleDocsHTMLParser()
        parser.feed(html)
        result = parser.get_clean_text()

        # Should extract content despite complex styling
        assert "Title Text" in result
        assert "Regular paragraph" in result
        # Note: Without actual <b>/<i> tags, we won't get markdown formatting
        # This tests that we at least extract the text content

    def test_br_tag_handling(self):
        """Test handling of <br> tags."""
        html = """
        <p>Line one<br>Line two<br>Line three</p>
        """
        parser = GoogleDocsHTMLParser()
        parser.feed(html)
        result = parser.get_clean_text()

        assert "Line one" in result
        assert "Line two" in result
        assert "Line three" in result

    def test_mixed_formatting(self):
        """Test mixed bold and italic formatting."""
        html = """
        <p>Text with <b><i>bold italic</i></b> formatting.</p>
        """
        parser = GoogleDocsHTMLParser()
        parser.feed(html)
        result = parser.get_clean_text()

        # Should have both markers
        assert "**_bold italic_**" in result or "_**bold italic**_" in result


@pytest.mark.parametrize("html,expected_in_result", [
    ("<p>Simple text</p>", "Simple text"),
    ("<p><strong>Bold</strong></p>", "**Bold**"),
    ("<p><em>Italic</em></p>", "_Italic_"),
    ("<h3>Heading 3</h3>", "### Heading 3"),
    ("<div>Div content</div>", "Div content"),
])
def test_various_html_inputs(html, expected_in_result):
    """Parameterized test for various HTML inputs."""
    parser = GoogleDocsHTMLParser()
    parser.feed(html)
    result = parser.get_clean_text()
    assert expected_in_result in result
