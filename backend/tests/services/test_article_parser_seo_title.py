"""
Unit tests for Article Parser SEO Title extraction

Tests the SEO Title extraction functionality in ArticleParserService:
- Extracting marked SEO Title from original content
- Setting seo_title_extracted flag
- Setting seo_title_source to 'extracted'
- Handling articles without SEO Title markers
"""

import pytest
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import Mock, patch, AsyncMock

from src.models import Article, WorklistItem
from src.services.article_parser import ArticleParserService


@pytest.fixture
def mock_ai_service():
    """Mock AI service for testing."""
    mock = AsyncMock()
    mock.generate_structured_content = AsyncMock(return_value={
        "title_prefix": "",
        "title_main": "AI在醫療領域的創新應用",
        "title_suffix": "",
        "seo_title": None,  # Will be overridden if marked in content
        "meta_description": "本文探討AI技術在醫療領域的應用...",
    })
    return mock


@pytest.fixture
def parser_service(mock_ai_service):
    """Create ArticleParserService instance with mocked AI."""
    with patch('src.services.article_parser.ArticleParserService._get_ai_service', return_value=mock_ai_service):
        service = ArticleParserService()
        return service


class TestSEOTitleExtraction:
    """Test SEO Title extraction from marked content."""

    @pytest.mark.asyncio
    async def test_extract_seo_title_from_marked_content(self, parser_service):
        """Test extraction of SEO Title when marked in content."""
        # Arrange
        content = """
        這是 SEO title: 2024年AI醫療創新趨勢分析

        # AI在醫療領域的創新應用與未來展望

        本文深入探討AI技術在醫療領域的各種創新應用...
        """

        worklist_item = Mock(spec=WorklistItem)
        worklist_item.raw_html = content
        worklist_item.id = 1

        # Act
        result = await parser_service.parse_article(worklist_item)

        # Assert
        assert result["seo_title"] == "2024年AI醫療創新趨勢分析"
        assert result["seo_title_extracted"] is True
        assert result["seo_title_source"] == "extracted"
        assert result["title_main"] == "AI在醫療領域的創新應用與未來展望"

    @pytest.mark.asyncio
    async def test_extract_seo_title_variant_format(self, parser_service):
        """Test extraction with alternative marker format."""
        # Arrange
        content = """
        SEO title: 深度解析ChatGPT-4企業應用

        # ChatGPT-4在企業數位轉型中的創新應用

        本文探討...
        """

        worklist_item = Mock(spec=WorklistItem)
        worklist_item.raw_html = content
        worklist_item.id = 1

        # Act
        result = await parser_service.parse_article(worklist_item)

        # Assert
        assert result["seo_title"] == "深度解析ChatGPT-4企業應用"
        assert result["seo_title_extracted"] is True
        assert result["seo_title_source"] == "extracted"

    @pytest.mark.asyncio
    async def test_extract_seo_title_case_insensitive(self, parser_service):
        """Test extraction is case-insensitive."""
        # Arrange
        content = """
        seo_title: 區塊鏈金融應用完整指南

        # 區塊鏈技術在金融領域的應用

        內容...
        """

        worklist_item = Mock(spec=WorklistItem)
        worklist_item.raw_html = content
        worklist_item.id = 1

        # Act
        result = await parser_service.parse_article(worklist_item)

        # Assert
        assert result["seo_title"] == "區塊鏈金融應用完整指南"
        assert result["seo_title_extracted"] is True

    @pytest.mark.asyncio
    async def test_no_seo_title_marker(self, parser_service):
        """Test article without SEO Title marker."""
        # Arrange
        content = """
        # AI在醫療領域的創新應用

        本文探討AI技術在醫療領域的各種創新應用...
        """

        worklist_item = Mock(spec=WorklistItem)
        worklist_item.raw_html = content
        worklist_item.id = 1

        # Act
        result = await parser_service.parse_article(worklist_item)

        # Assert
        assert result.get("seo_title") is None
        assert result.get("seo_title_extracted") is False
        assert result.get("seo_title_source") is None

    @pytest.mark.asyncio
    async def test_extract_seo_title_with_colon_in_title(self, parser_service):
        """Test extraction when SEO Title itself contains colons."""
        # Arrange
        content = """
        這是 SEO title: AI醫療：從診斷到治療的創新

        # AI在醫療領域的應用

        內容...
        """

        worklist_item = Mock(spec=WorklistItem)
        worklist_item.raw_html = content
        worklist_item.id = 1

        # Act
        result = await parser_service.parse_article(worklist_item)

        # Assert
        assert result["seo_title"] == "AI醫療：從診斷到治療的創新"
        assert result["seo_title_extracted"] is True

    @pytest.mark.asyncio
    async def test_extract_seo_title_strips_whitespace(self, parser_service):
        """Test that extracted SEO Title has whitespace stripped."""
        # Arrange
        content = """
        這是 SEO title:   測試SEO標題帶有前後空格

        # 標題
        """

        worklist_item = Mock(spec=WorklistItem)
        worklist_item.raw_html = content
        worklist_item.id = 1

        # Act
        result = await parser_service.parse_article(worklist_item)

        # Assert
        assert result["seo_title"] == "測試SEO標題帶有前後空格"
        assert not result["seo_title"].startswith(" ")
        assert not result["seo_title"].endswith(" ")

    @pytest.mark.asyncio
    async def test_extract_seo_title_first_occurrence(self, parser_service):
        """Test that only first SEO Title marker is extracted."""
        # Arrange
        content = """
        這是 SEO title: 第一個SEO標題

        # 標題

        這是 SEO title: 第二個SEO標題
        """

        worklist_item = Mock(spec=WorklistItem)
        worklist_item.raw_html = content
        worklist_item.id = 1

        # Act
        result = await parser_service.parse_article(worklist_item)

        # Assert
        assert result["seo_title"] == "第一個SEO標題"

    @pytest.mark.asyncio
    async def test_extract_seo_title_length_validation(self, parser_service):
        """Test that SEO Title respects database length limit (200 chars)."""
        # Arrange
        long_title = "A" * 250  # Exceeds database limit
        content = f"""
        這是 SEO title: {long_title}

        # 標題
        """

        worklist_item = Mock(spec=WorklistItem)
        worklist_item.raw_html = content
        worklist_item.id = 1

        # Act
        result = await parser_service.parse_article(worklist_item)

        # Assert
        assert result["seo_title"] is not None
        assert len(result["seo_title"]) <= 200  # Database limit
        assert result["seo_title_extracted"] is True


class TestSEOTitleDatabasePersistence:
    """Test SEO Title persistence to database."""

    @pytest.mark.asyncio
    async def test_seo_title_saved_to_article(self, parser_service):
        """Test that extracted SEO Title is saved to Article model."""
        # Arrange
        content = """
        這是 SEO title: 測試SEO標題

        # 文章標題
        """

        worklist_item = Mock(spec=WorklistItem)
        worklist_item.raw_html = content
        worklist_item.id = 1
        worklist_item.article_id = 123

        # Mock database session
        mock_session = AsyncMock(spec=AsyncSession)
        mock_article = Mock(spec=Article)
        mock_session.get = AsyncMock(return_value=mock_article)

        # Act
        with patch.object(parser_service, '_get_session', return_value=mock_session):
            result = await parser_service.parse_and_save(worklist_item)

        # Assert
        assert mock_article.seo_title == "測試SEO標題"
        assert mock_article.seo_title_extracted is True
        assert mock_article.seo_title_source == "extracted"
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_article_without_seo_title_not_flagged(self, parser_service):
        """Test that articles without SEO Title are not flagged as extracted."""
        # Arrange
        content = """
        # 文章標題

        內容...
        """

        worklist_item = Mock(spec=WorklistItem)
        worklist_item.raw_html = content
        worklist_item.id = 1
        worklist_item.article_id = 123

        # Mock database session
        mock_session = AsyncMock(spec=AsyncSession)
        mock_article = Mock(spec=Article)
        mock_session.get = AsyncMock(return_value=mock_article)

        # Act
        with patch.object(parser_service, '_get_session', return_value=mock_session):
            result = await parser_service.parse_and_save(worklist_item)

        # Assert
        assert mock_article.seo_title is None
        assert mock_article.seo_title_extracted is False
        assert mock_article.seo_title_source is None


class TestSEOTitleEdgeCases:
    """Test edge cases for SEO Title extraction."""

    @pytest.mark.asyncio
    async def test_empty_seo_title_marker(self, parser_service):
        """Test handling of empty SEO Title marker."""
        # Arrange
        content = """
        這是 SEO title:

        # 標題
        """

        worklist_item = Mock(spec=WorklistItem)
        worklist_item.raw_html = content
        worklist_item.id = 1

        # Act
        result = await parser_service.parse_article(worklist_item)

        # Assert
        # Empty SEO Title should be treated as not provided
        assert result.get("seo_title") is None or result.get("seo_title") == ""
        assert result.get("seo_title_extracted") is False

    @pytest.mark.asyncio
    async def test_seo_title_with_special_characters(self, parser_service):
        """Test SEO Title with special characters."""
        # Arrange
        content = """
        這是 SEO title: AI醫療｜2024趨勢報告【完整版】

        # 標題
        """

        worklist_item = Mock(spec=WorklistItem)
        worklist_item.raw_html = content
        worklist_item.id = 1

        # Act
        result = await parser_service.parse_article(worklist_item)

        # Assert
        assert result["seo_title"] == "AI醫療｜2024趨勢報告【完整版】"
        assert result["seo_title_extracted"] is True

    @pytest.mark.asyncio
    async def test_seo_title_with_unicode_characters(self, parser_service):
        """Test SEO Title with various Unicode characters."""
        # Arrange
        content = """
        這是 SEO title: 🚀 AI醫療創新 → 2024趨勢 ✓

        # 標題
        """

        worklist_item = Mock(spec=WorklistItem)
        worklist_item.raw_html = content
        worklist_item.id = 1

        # Act
        result = await parser_service.parse_article(worklist_item)

        # Assert
        assert "AI醫療創新" in result["seo_title"]
        assert result["seo_title_extracted"] is True

    @pytest.mark.asyncio
    async def test_seo_title_multiline_content(self, parser_service):
        """Test that SEO Title marker must be on single line."""
        # Arrange
        content = """
        這是 SEO title: 第一行
        第二行應該被忽略

        # 標題
        """

        worklist_item = Mock(spec=WorklistItem)
        worklist_item.raw_html = content
        worklist_item.id = 1

        # Act
        result = await parser_service.parse_article(worklist_item)

        # Assert
        # Should only extract content from first line
        assert result["seo_title"] == "第一行"
        assert "第二行" not in result["seo_title"]


class TestSEOTitleIntegrationWithH1:
    """Test SEO Title extraction alongside H1 title extraction."""

    @pytest.mark.asyncio
    async def test_separate_seo_title_and_h1(self, parser_service):
        """Test that SEO Title and H1 are stored separately."""
        # Arrange
        content = """
        這是 SEO title: 2024年AI醫療趨勢

        # AI在醫療領域的創新應用與未來展望（完整報告）

        內容...
        """

        worklist_item = Mock(spec=WorklistItem)
        worklist_item.raw_html = content
        worklist_item.id = 1

        # Act
        result = await parser_service.parse_article(worklist_item)

        # Assert
        # SEO Title (short, keyword-focused)
        assert result["seo_title"] == "2024年AI醫療趨勢"
        assert len(result["seo_title"]) < 50

        # H1 Title (longer, descriptive)
        assert result["title_main"] == "AI在醫療領域的創新應用與未來展望（完整報告）"
        assert len(result["title_main"]) > len(result["seo_title"])

        # Both should be populated independently
        assert result["seo_title"] != result["title_main"]

    @pytest.mark.asyncio
    async def test_h1_not_affected_by_seo_title(self, parser_service):
        """Test that H1 extraction is not affected by SEO Title presence."""
        # Arrange - with SEO Title
        content_with_seo = """
        這是 SEO title: SEO標題

        # H1標題
        """

        # Arrange - without SEO Title
        content_without_seo = """
        # H1標題
        """

        worklist_item_1 = Mock(spec=WorklistItem)
        worklist_item_1.raw_html = content_with_seo
        worklist_item_1.id = 1

        worklist_item_2 = Mock(spec=WorklistItem)
        worklist_item_2.raw_html = content_without_seo
        worklist_item_2.id = 2

        # Act
        result_with = await parser_service.parse_article(worklist_item_1)
        result_without = await parser_service.parse_article(worklist_item_2)

        # Assert
        # H1 should be extracted correctly in both cases
        assert result_with["title_main"] == "H1標題"
        assert result_without["title_main"] == "H1標題"

        # Only first has SEO Title
        assert result_with["seo_title"] == "SEO標題"
        assert result_without.get("seo_title") is None
