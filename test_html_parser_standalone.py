"""Standalone integration test for Google Docs HTML Parser.

This test verifies the HTML parsing functionality without requiring
full database/service dependencies.
"""

import re
from html.parser import HTMLParser


class GoogleDocsHTMLParser(HTMLParser):
    """Clean HTML parser for Google Docs exported content.

    Converts Google Docs HTML export to clean markdown-like text
    while preserving structure and basic formatting.
    """

    def __init__(self):
        super().__init__()
        self.content_parts = []
        self.current_list_level = 0
        self.in_paragraph = False
        self.current_text = []
        self.in_bold = False
        self.in_italic = False
        self.in_link = False
        self.link_url = None

    def handle_starttag(self, tag, attrs):
        """Handle opening HTML tags."""
        attrs_dict = dict(attrs)

        if tag in ('p', 'div'):
            self.in_paragraph = True
            self.current_text = []
        elif tag == 'br':
            self.current_text.append('\n')
        elif tag in ('b', 'strong'):
            self.in_bold = True
            if self.current_text and not self.current_text[-1].endswith((' ', '\n')):
                self.current_text.append(' ')
            self.current_text.append('**')
        elif tag in ('i', 'em'):
            self.in_italic = True
            if self.current_text and not self.current_text[-1].endswith((' ', '\n')):
                self.current_text.append(' ')
            self.current_text.append('_')
        elif tag == 'a':
            self.in_link = True
            self.link_url = attrs_dict.get('href', '')
            if self.current_text and not self.current_text[-1].endswith((' ', '\n')):
                self.current_text.append(' ')
            self.current_text.append('[')
        elif tag in ('ul', 'ol'):
            self.current_list_level += 1
        elif tag == 'li':
            indent = '  ' * (self.current_list_level - 1)
            self.current_text.append(f'\n{indent}- ')
        elif tag in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
            level = int(tag[1])
            self.current_text.append('\n' + '#' * level + ' ')
            self.in_paragraph = True

    def handle_endtag(self, tag):
        """Handle closing HTML tags."""
        if tag in ('p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
            if self.current_text:
                text = ''.join(self.current_text).strip()
                if text:
                    self.content_parts.append(text)
                self.current_text = []
            self.in_paragraph = False
        elif tag in ('b', 'strong'):
            self.current_text.append('**')
            self.current_text.append(' ')
            self.in_bold = False
        elif tag in ('i', 'em'):
            self.current_text.append('_')
            self.current_text.append(' ')
            self.in_italic = False
        elif tag == 'a':
            if self.link_url:
                self.current_text.append(f']({self.link_url})')
            else:
                self.current_text.append(']')
            self.current_text.append(' ')
            self.in_link = False
            self.link_url = None
        elif tag in ('ul', 'ol'):
            self.current_list_level = max(0, self.current_list_level - 1)

    def handle_data(self, data):
        """Handle text content."""
        if not data.strip():
            return
        self.current_text.append(data.strip())

    def get_clean_text(self) -> str:
        """Get the cleaned text content."""
        if self.current_text:
            text = ''.join(self.current_text).strip()
            if text:
                self.content_parts.append(text)

        result = '\n\n'.join(self.content_parts)
        result = re.sub(r'\n{3,}', '\n\n', result)
        return result.strip()


def test_basic_parsing():
    """Test 1: Basic HTML parsing."""
    print("Test 1: Basic HTML parsing")
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

    checks = [
        ("H1 heading", "# Test Article" in result),
        ("Bold formatting", "**bold**" in result),
        ("Link conversion", "[a link](https://example.com)" in result),
        ("List items", "- First item" in result and "- Second item" in result),
    ]

    for check_name, passed in checks:
        status = "✓" if passed else "✗"
        print(f"  {status} {check_name}")

    return all(passed for _, passed in checks)


def test_yaml_front_matter():
    """Test 2: YAML front matter preservation."""
    print("\nTest 2: YAML front matter preservation")
    html = """
    <p>---</p>
    <p>title: My Article Title</p>
    <p>author: John Doe</p>
    <p>meta_description: Test article</p>
    <p>tags:</p>
    <p>  - python</p>
    <p>  - automation</p>
    <p>---</p>
    <p>Article content starts here.</p>
    """
    parser = GoogleDocsHTMLParser()
    parser.feed(html)
    result = parser.get_clean_text()

    print(f"  Result:\n{result}\n")

    checks = [
        ("YAML markers", result.count("---") >= 2),
        ("Title metadata", "title: My Article Title" in result),
        ("Author metadata", "author: John Doe" in result),
        ("List items", "- python" in result),
        ("Body content", "Article content starts here." in result),
    ]

    for check_name, passed in checks:
        status = "✓" if passed else "✗"
        print(f"  {status} {check_name}")

    # Test YAML pattern matching
    yaml_pattern = re.compile(r'^---\s*\n(.*?)\n---\s*\n(.*)$', re.DOTALL)
    match = yaml_pattern.match(result)
    yaml_parseable = match is not None

    print(f"  {'✓' if yaml_parseable else '✗'} YAML pattern matches")

    return all(passed for _, passed in checks) and yaml_parseable


def test_complex_formatting():
    """Test 3: Complex formatting."""
    print("\nTest 3: Complex document formatting")
    html = """
    <h1>Complete Guide</h1>
    <p>Introduction.</p>
    <h2>Section 1</h2>
    <p>This section covers <b>important</b> concepts.</p>
    <ul>
        <li>Point one with <i>emphasis</i></li>
        <li>Point two with <a href="https://docs.example.com">docs link</a></li>
    </ul>
    <h3>Subsection 1.1</h3>
    <p>More details with <b><i>bold italic</i></b> text.</p>
    """
    parser = GoogleDocsHTMLParser()
    parser.feed(html)
    result = parser.get_clean_text()

    checks = [
        ("H1 heading", "# Complete Guide" in result),
        ("H2 heading", "## Section 1" in result),
        ("H3 heading", "### Subsection 1.1" in result),
        ("Bold text", "**important**" in result),
        ("Italic text", "_emphasis_" in result),
        ("Link", "[docs link](https://docs.example.com)" in result),
    ]

    for check_name, passed in checks:
        status = "✓" if passed else "✗"
        print(f"  {status} {check_name}")

    return all(passed for _, passed in checks)


def test_performance():
    """Test 4: Performance with large document."""
    print("\nTest 4: Performance test")
    import time

    # Generate large document
    large_html = "<h1>Performance Test</h1>\n"
    for i in range(100):
        large_html += f"<h2>Section {i}</h2>\n"
        large_html += f"<p>Paragraph {i} with <b>bold</b> and <i>italic</i>.</p>\n"
        large_html += "<ul>\n"
        for j in range(5):
            large_html += f"<li>Item {i}.{j}</li>\n"
        large_html += "</ul>\n"

    start_time = time.time()
    parser = GoogleDocsHTMLParser()
    parser.feed(large_html)
    result = parser.get_clean_text()
    elapsed_time = time.time() - start_time

    print(f"  Input size: {len(large_html):,} characters")
    print(f"  Output size: {len(result):,} characters")
    print(f"  Parse time: {elapsed_time*1000:.2f}ms")

    performance_ok = elapsed_time < 1.0
    content_ok = "# Performance Test" in result and "Section 99" in result

    print(f"  {'✓' if performance_ok else '✗'} Performance < 1 second")
    print(f"  {'✓' if content_ok else '✗'} Content parsed correctly")

    return performance_ok and content_ok


def main():
    """Run all tests."""
    print("=" * 70)
    print("Google Docs HTML Parser - Standalone Integration Tests")
    print("=" * 70)
    print()

    tests = [
        test_basic_parsing,
        test_yaml_front_matter,
        test_complex_formatting,
        test_performance,
    ]

    results = []
    for test_func in tests:
        try:
            passed = test_func()
            results.append((test_func.__name__, passed, None))
        except Exception as e:
            results.append((test_func.__name__, False, str(e)))
            print(f"  ✗ EXCEPTION: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)

    passed_count = sum(1 for _, passed, _ in results if passed)
    failed_count = len(results) - passed_count

    for test_name, passed, error in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
        if error:
            print(f"  Error: {error}")

    print("=" * 70)
    print(f"Results: {passed_count} passed, {failed_count} failed")
    print("=" * 70)

    return failed_count == 0


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
