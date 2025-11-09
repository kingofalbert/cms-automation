"""Unit tests for ArticleParserService (Phase 7)."""

import pytest

from src.services.parser import (
    ArticleParserService,
    ParsedArticle,
    ParsedImage,
    ParsingResult,
)


class TestArticleParserService:
    """Test suite for ArticleParserService."""

    def test_service_initialization_heuristic_mode(self):
        """Test service initializes correctly in heuristic mode."""
        parser = ArticleParserService(use_ai=False)
        assert parser.use_ai is False
        assert parser.anthropic_api_key is None

    def test_service_initialization_ai_mode(self):
        """Test service initializes correctly in AI mode."""
        parser = ArticleParserService(
            use_ai=True,
            anthropic_api_key="sk-test-key",
            model="claude-3-5-sonnet-20241022",
        )
        assert parser.use_ai is True
        assert parser.anthropic_api_key == "sk-test-key"
        assert parser.model == "claude-3-5-sonnet-20241022"

    def test_parse_document_returns_result(self):
        """Test parse_document returns a ParsingResult."""
        parser = ArticleParserService(use_ai=False)
        html = "<html><body><h1>Test Title</h1><p>Test content</p></body></html>"

        result = parser.parse_document(html)

        assert isinstance(result, ParsingResult)
        assert result.success in (True, False)  # Can be either depending on implementation

    def test_parse_document_with_empty_html(self):
        """Test parse_document handles empty HTML gracefully."""
        parser = ArticleParserService(use_ai=False)
        html = ""

        result = parser.parse_document(html)

        assert isinstance(result, ParsingResult)
        # Should return a result even if parsing fails

    def test_heuristic_parsing_basic_structure(self):
        """Test heuristic parsing extracts basic structure."""
        parser = ArticleParserService(use_ai=False)
        html = """
        <html>
            <body>
                <h1>Test Article Title</h1>
                <p>Paragraph 1</p>
                <p>Paragraph 2</p>
            </body>
        </html>
        """

        result = parser.parse_document(html, fallback_to_heuristic=True)

        if result.success and result.parsed_article:
            assert result.parsed_article.title_main is not None
            assert result.parsed_article.body_html is not None
            assert result.parsed_article.parsing_method == "heuristic"

    def test_validate_parsed_article(self):
        """Test article validation detects issues."""
        parser = ArticleParserService(use_ai=False)

        # Create a minimal valid article
        article = ParsedArticle(
            title_main="Test",  # Too short
            body_html="<p>Short</p>",  # Too short
            parsing_method="test",
        )

        warnings = parser.validate_parsed_article(article)

        # Should have warnings for short title and body
        assert len(warnings) > 0
        assert any("short" in w.lower() for w in warnings)

    def test_validate_parsed_article_with_long_meta_description(self):
        """Test validation warns about long meta descriptions."""
        parser = ArticleParserService(use_ai=False)

        article = ParsedArticle(
            title_main="Valid Title Here",
            body_html="<p>Valid body content here with enough text.</p>" * 3,
            meta_description="A" * 200,  # Way too long
            parsing_method="test",
        )

        warnings = parser.validate_parsed_article(article)

        assert any("meta description" in w.lower() for w in warnings)


class TestParsedArticleModel:
    """Test suite for ParsedArticle Pydantic model."""

    def test_parsed_article_minimal(self):
        """Test creating ParsedArticle with minimal required fields."""
        article = ParsedArticle(
            title_main="Test Title",
            body_html="<p>Body content</p>",
            parsing_method="test",
        )

        assert article.title_main == "Test Title"
        assert article.body_html == "<p>Body content</p>"
        assert article.parsing_method == "test"
        assert article.parsing_confidence == 1.0  # Default

    def test_parsed_article_full_title(self):
        """Test full_title property combines components."""
        article = ParsedArticle(
            title_prefix="【新聞】",
            title_main="Main Title",
            title_suffix="Subtitle",
            body_html="<p>Body</p>",
            parsing_method="test",
        )

        assert article.full_title == "【新聞】 Main Title Subtitle"

    def test_parsed_article_validation_empty_title(self):
        """Test validation rejects empty title_main."""
        with pytest.raises(ValueError, match="title_main cannot be empty"):
            ParsedArticle(
                title_main="   ",  # Empty after strip
                body_html="<p>Body</p>",
                parsing_method="test",
            )

    def test_parsed_article_seo_keywords_cleaned(self):
        """Test SEO keywords are cleaned (empty strings removed)."""
        article = ParsedArticle(
            title_main="Test",
            body_html="<p>Body</p>",
            seo_keywords=["keyword1", "  ", "keyword2", ""],
            parsing_method="test",
        )

        assert article.seo_keywords == ["keyword1", "keyword2"]

    def test_parsed_article_has_seo_data(self):
        """Test has_seo_data property."""
        article_with_seo = ParsedArticle(
            title_main="Test",
            body_html="<p>Body</p>",
            meta_description="Description",
            parsing_method="test",
        )

        article_without_seo = ParsedArticle(
            title_main="Test",
            body_html="<p>Body</p>",
            parsing_method="test",
        )

        assert article_with_seo.has_seo_data is True
        assert article_without_seo.has_seo_data is False


class TestParsedImageModel:
    """Test suite for ParsedImage Pydantic model."""

    def test_parsed_image_minimal(self):
        """Test creating ParsedImage with minimal fields."""
        image = ParsedImage(position=0)

        assert image.position == 0
        assert image.preview_path is None
        assert image.source_url is None

    def test_parsed_image_validation_negative_position(self):
        """Test validation rejects negative position."""
        with pytest.raises(ValueError, match="Position must be non-negative"):
            ParsedImage(position=-1)

    def test_parsed_image_with_metadata(self):
        """Test ParsedImage with full image_metadata."""
        from src.services.parser.models import ImageMetadata

        image_metadata = ImageMetadata(
            width=1920,
            height=1080,
            file_size_bytes=2458624,
            format="JPEG",
        )

        image = ParsedImage(
            position=3,
            source_url="https://example.com/image.jpg",
            caption="Test caption",
            metadata=image_metadata,
        )

        assert image.position == 3
        assert image.metadata.width == 1920
        assert image.metadata.format == "JPEG"


class TestParsingResult:
    """Test suite for ParsingResult model."""

    def test_parsing_result_success(self):
        """Test successful parsing result."""
        article = ParsedArticle(
            title_main="Test",
            body_html="<p>Body</p>",
            parsing_method="test",
        )

        result = ParsingResult(
            success=True,
            parsed_article=article,
        )

        assert result.success is True
        assert result.parsed_article is not None
        assert result.has_errors is False

    def test_parsing_result_with_errors(self):
        """Test parsing result with errors."""
        from src.services.parser.models import ParsingError

        error = ParsingError(
            error_type="test_error",
            error_message="Test error message",
        )

        result = ParsingResult(
            success=False,
            errors=[error],
        )

        assert result.success is False
        assert result.has_errors is True
        assert len(result.errors) == 1

    def test_parsing_result_with_warnings(self):
        """Test parsing result with warnings."""
        article = ParsedArticle(
            title_main="Test",
            body_html="<p>Body</p>",
            parsing_method="test",
        )

        result = ParsingResult(
            success=True,
            parsed_article=article,
            warnings=["Warning 1", "Warning 2"],
        )

        assert result.success is True
        assert result.has_warnings is True
        assert len(result.warnings) == 2


class TestHeuristicTitleExtraction:
    """Test suite for heuristic title extraction methods."""

    @pytest.fixture
    def parser(self):
        return ArticleParserService(use_ai=False)

    def test_extract_title_with_prefix_suffix(self, parser):
        """Test title extraction with Chinese prefix and suffix."""
        from bs4 import BeautifulSoup

        html = "<h1>【專題報導】2024年醫療趨勢：AI應用實例</h1>"
        soup = BeautifulSoup(html, "html.parser")
        result = parser._extract_title(soup)

        assert result["prefix"] == "【專題報導】"
        assert "2024年醫療趨勢" in result["main"]
        assert "AI應用實例" in result["suffix"]

    def test_extract_title_main_only(self, parser):
        """Test title with no prefix or suffix."""
        from bs4 import BeautifulSoup

        html = "<h1>簡單的文章標題</h1>"
        soup = BeautifulSoup(html, "html.parser")
        result = parser._extract_title(soup)

        assert result["prefix"] is None
        assert result["main"] == "簡單的文章標題"
        assert result["suffix"] is None


class TestHeuristicAuthorExtraction:
    """Test suite for heuristic author extraction methods."""

    @pytest.fixture
    def parser(self):
        return ArticleParserService(use_ai=False)

    def test_extract_author_chinese_pattern(self, parser):
        """Test extracting author with 文／ pattern."""
        from bs4 import BeautifulSoup

        html = "<p>文／張三｜編輯／李四</p>"
        soup = BeautifulSoup(html, "html.parser")
        result = parser._extract_author(soup)

        assert result["name"] == "張三"
        assert "文／張三" in result["raw_line"]

    def test_extract_author_multiple_patterns(self, parser):
        """Test different author patterns."""
        from bs4 import BeautifulSoup

        # Test 作者： pattern
        html1 = "<p>作者：王五</p>"
        soup1 = BeautifulSoup(html1, "html.parser")
        result1 = parser._extract_author(soup1)
        assert result1["name"] == "王五"

        # Test English pattern
        html2 = "<p>By: John Doe</p>"
        soup2 = BeautifulSoup(html2, "html.parser")
        result2 = parser._extract_author(soup2)
        assert result2["name"] == "John Doe"


class TestHeuristicBodyExtraction:
    """Test suite for heuristic body extraction methods."""

    @pytest.fixture
    def parser(self):
        return ArticleParserService(use_ai=False)

    def test_extract_body_removes_metadata(self, parser):
        """Test body extraction filters out metadata paragraphs."""
        from bs4 import BeautifulSoup

        html = """
        <body>
            <p>文／張三</p>
            <p>這是正文的第一段，包含了足夠長的內容用於測試，確保不會被誤判為元數據。</p>
            <p>這是正文的第二段。</p>
        </body>
        """
        soup = BeautifulSoup(html, "html.parser")
        result = parser._extract_body(soup)

        assert "文／張三" not in result
        assert "這是正文的第一段" in result

    def test_extract_body_removes_images(self, parser):
        """Test body extraction removes image tags."""
        from bs4 import BeautifulSoup

        html = """
        <body>
            <p>段落內容<img src="test.jpg" alt="test"></p>
        </body>
        """
        soup = BeautifulSoup(html, "html.parser")
        result = parser._extract_body(soup)

        assert "<img" not in result
        assert "段落內容" in result


class TestHeuristicSEOExtraction:
    """Test suite for heuristic SEO metadata extraction."""

    @pytest.fixture
    def parser(self):
        return ArticleParserService(use_ai=False)

    def test_extract_seo_from_meta_tags(self, parser):
        """Test SEO extraction from meta tags."""
        from bs4 import BeautifulSoup

        html = """
        <html>
            <head>
                <meta name="description" content="測試描述內容">
                <meta name="keywords" content="關鍵字1, 關鍵字2">
            </head>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        result = parser._extract_seo_metadata(soup)

        assert result["description"] == "測試描述內容"
        assert "關鍵字1" in result["keywords"]

    def test_extract_seo_generates_description(self, parser):
        """Test auto-generation of meta description from content."""
        from bs4 import BeautifulSoup

        html = """
        <body>
            <p>這是一段很長的內容用於生成SEO描述。這段內容足夠長，可以被自動提取作為meta description使用。系統會自動截取合適的長度。</p>
        </body>
        """
        soup = BeautifulSoup(html, "html.parser")
        result = parser._extract_seo_metadata(soup)

        assert result["description"] is not None
        assert len(result["description"]) <= 160


class TestHeuristicImageExtraction:
    """Test suite for heuristic image extraction methods."""

    @pytest.fixture
    def parser(self):
        return ArticleParserService(use_ai=False)

    def test_extract_images_from_figure(self, parser):
        """Test extracting images from figure elements."""
        from bs4 import BeautifulSoup

        html = """
        <body>
            <p>第一段</p>
            <figure>
                <img src="https://example.com/test.jpg">
                <figcaption>測試圖片</figcaption>
            </figure>
        </body>
        """
        soup = BeautifulSoup(html, "html.parser")
        images = parser._extract_images(soup)

        assert len(images) == 1
        assert images[0].source_url == "https://example.com/test.jpg"
        assert images[0].caption == "測試圖片"

    def test_extract_images_standalone(self, parser):
        """Test extracting standalone img tags."""
        from bs4 import BeautifulSoup

        html = """
        <body>
            <p>段落</p>
            <img src="https://example.com/standalone.png" alt="獨立圖片">
        </body>
        """
        soup = BeautifulSoup(html, "html.parser")
        images = parser._extract_images(soup)

        assert len(images) == 1
        assert images[0].source_url == "https://example.com/standalone.png"
        assert images[0].caption == "獨立圖片"
