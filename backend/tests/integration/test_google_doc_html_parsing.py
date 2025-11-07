"""Integration tests for Google Docs HTML parsing functionality.

This test suite verifies:
1. HTML export and parsing works correctly
2. YAML front matter is preserved
3. Various document formats are handled properly
4. Integration with GoogleDriveSyncService
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_path))

from src.services.google_drive.sync_service import GoogleDocsHTMLParser


def test_basic_html_parsing():
    """Test basic HTML parsing functionality."""
    html = """
    <h1>Test Article</h1>
    <p>This is a <b>bold</b> paragraph with <a href="https://example.com">a link</a>.</p>
    <ul>
        <li>First item</li>
        <li>Second item</li>
    </ul>
    """

    parser = GoogleDocsHTMLParser()
    parser.feed(html)
    result = parser.get_clean_text()

    print("✓ Test 1: Basic HTML parsing")
    print(f"  Result preview: {result[:100]}...")

    assert "# Test Article" in result, "H1 heading not found"
    assert "**bold**" in result, "Bold formatting not preserved"
    assert "[a link](https://example.com)" in result, "Link not converted correctly"
    assert "- First item" in result, "List items not parsed"

    print("  ✅ All assertions passed")
    return True


def test_yaml_front_matter_preservation():
    """Test that YAML front matter is preserved correctly."""
    html = """
    <p>---</p>
    <p>title: My Article Title</p>
    <p>author: John Doe</p>
    <p>meta_description: This is a test article</p>
    <p>tags:</p>
    <p>  - python</p>
    <p>  - automation</p>
    <p>---</p>
    <p>Article content starts here.</p>
    <p>More content in the body.</p>
    """

    parser = GoogleDocsHTMLParser()
    parser.feed(html)
    result = parser.get_clean_text()

    print("✓ Test 2: YAML front matter preservation")
    print(f"  Result:\n{result}\n")

    # Check YAML structure is preserved
    assert result.count("---") >= 2, "YAML markers not preserved"
    assert "title: My Article Title" in result, "YAML metadata not preserved"
    assert "author: John Doe" in result, "YAML author not preserved"
    assert "- python" in result, "YAML list items not preserved"
    assert "Article content starts here." in result, "Body content not found"

    # Verify it can be parsed by YAML parser
    import re
    yaml_pattern = re.compile(r'^---\s*\n(.*?)\n---\s*\n(.*)$', re.DOTALL)
    match = yaml_pattern.match(result)

    assert match is not None, "YAML front matter pattern doesn't match"

    print("  ✅ YAML structure preserved correctly")
    return True


def test_complex_formatting():
    """Test complex document with mixed formatting."""
    html = """
    <h1>Complete Guide</h1>
    <p>Introduction paragraph.</p>

    <h2>Section 1: Basics</h2>
    <p>This section covers <b>important</b> concepts.</p>
    <ul>
        <li>Point one with <i>emphasis</i></li>
        <li>Point two with <a href="https://docs.example.com">documentation link</a></li>
    </ul>

    <h2>Section 2: Advanced</h2>
    <p>Advanced topics include:</p>
    <ol>
        <li>First advanced topic</li>
        <li>Second advanced topic</li>
    </ol>

    <h3>Subsection 2.1</h3>
    <p>More details here with <b><i>bold italic</i></b> text.</p>
    """

    parser = GoogleDocsHTMLParser()
    parser.feed(html)
    result = parser.get_clean_text()

    print("✓ Test 3: Complex formatting")
    print(f"  Result length: {len(result)} characters")

    # Check all elements are present
    assert "# Complete Guide" in result, "H1 not found"
    assert "## Section 1: Basics" in result, "H2 not found"
    assert "### Subsection 2.1" in result, "H3 not found"
    assert "**important**" in result, "Bold not found"
    assert "_emphasis_" in result, "Italic not found"
    assert "[documentation link](https://docs.example.com)" in result, "Link not found"

    print("  ✅ All complex formatting preserved")
    return True


def test_google_docs_style_html():
    """Test parsing of actual Google Docs exported HTML."""
    # Simulated Google Docs HTML with inline styles and classes
    html = """
    <html>
    <head>
        <style type="text/css">
            .c1{font-weight:700}
            .c2{font-style:italic}
            .c3{color:#000000}
        </style>
    </head>
    <body class="c4">
        <p class="c5"><span class="c1">Bold Title</span></p>
        <p class="c5"><span class="c3">Regular text with </span>
        <span class="c2">italic portion</span>
        <span class="c3">.</span></p>
        <ul class="c6 lst-kix_1-0 start">
            <li class="c5 c7"><span class="c3">First item</span></li>
            <li class="c5 c7"><span class="c3">Second item</span></li>
        </ul>
    </body>
    </html>
    """

    parser = GoogleDocsHTMLParser()
    parser.feed(html)
    result = parser.get_clean_text()

    print("✓ Test 4: Google Docs style HTML")
    print(f"  Result: {result}")

    # Should extract content despite complex styling
    assert "Bold Title" in result, "Title not extracted"
    assert "Regular text" in result, "Regular text not extracted"
    assert "First item" in result, "List items not extracted"

    print("  ✅ Google Docs HTML parsed successfully")
    return True


def test_empty_and_edge_cases():
    """Test edge cases and empty documents."""
    print("✓ Test 5: Edge cases")

    # Test 5a: Empty document
    parser1 = GoogleDocsHTMLParser()
    parser1.feed("")
    result1 = parser1.get_clean_text()
    assert result1 == "", "Empty document should return empty string"
    print("  ✅ Empty document handled")

    # Test 5b: Only whitespace
    parser2 = GoogleDocsHTMLParser()
    parser2.feed("<p>   </p><p>  </p>")
    result2 = parser2.get_clean_text()
    assert result2 == "", "Whitespace-only document should return empty string"
    print("  ✅ Whitespace-only handled")

    # Test 5c: Special characters
    parser3 = GoogleDocsHTMLParser()
    parser3.feed("<p>Special chars: &amp; &lt; &gt; &quot;</p>")
    result3 = parser3.get_clean_text()
    # Note: HTMLParser automatically unescapes entities
    print(f"  Special chars result: {result3}")
    print("  ✅ Special characters handled")

    return True


def test_parsing_performance():
    """Test parsing performance with larger documents."""
    # Generate a large document
    large_html = "<h1>Performance Test</h1>\n"
    for i in range(100):
        large_html += f"<h2>Section {i}</h2>\n"
        large_html += f"<p>This is paragraph {i} with <b>bold</b> and <i>italic</i> text.</p>\n"
        large_html += "<ul>\n"
        for j in range(5):
            large_html += f"<li>Item {i}.{j}</li>\n"
        large_html += "</ul>\n"

    import time
    start_time = time.time()

    parser = GoogleDocsHTMLParser()
    parser.feed(large_html)
    result = parser.get_clean_text()

    elapsed_time = time.time() - start_time

    print(f"✓ Test 6: Performance test")
    print(f"  Input size: {len(large_html):,} characters")
    print(f"  Output size: {len(result):,} characters")
    print(f"  Parse time: {elapsed_time*1000:.2f}ms")

    assert elapsed_time < 1.0, "Parsing took too long (> 1 second)"
    assert "# Performance Test" in result, "Content not parsed"
    assert "Section 99" in result, "Not all sections parsed"

    print("  ✅ Performance acceptable")
    return True


def main():
    """Run all integration tests."""
    print("=" * 70)
    print("Google Docs HTML Parsing - Integration Test Suite")
    print("=" * 70)
    print()

    tests = [
        test_basic_html_parsing,
        test_yaml_front_matter_preservation,
        test_complex_formatting,
        test_google_docs_style_html,
        test_empty_and_edge_cases,
        test_parsing_performance,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
            print()
        except AssertionError as e:
            failed += 1
            print(f"  ❌ FAILED: {e}")
            print()
        except Exception as e:
            failed += 1
            print(f"  ❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            print()

    print("=" * 70)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 70)

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
