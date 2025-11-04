"""Tests for JSON importer."""

from pathlib import Path

import pytest

from src.models import ArticleStatus
from src.services.article_importer.json_importer import JSONImporter


@pytest.fixture
def json_importer():
    """Create JSON importer instance."""
    return JSONImporter()


@pytest.fixture
def sample_json_path():
    """Path to sample JSON file."""
    return str(Path(__file__).parent.parent.parent / "fixtures/import_files/sample_articles.json")


@pytest.mark.asyncio
async def test_json_parse_file(json_importer, sample_json_path):
    """Test parsing JSON file."""
    articles = await json_importer.parse_file(sample_json_path)

    assert len(articles) == 2
    assert articles[0].title == "Getting Started with Docker Containers for Developers"
    assert articles[0].status == ArticleStatus.IMPORTED
    assert articles[0].source == "json_import"


@pytest.mark.asyncio
async def test_json_parse_with_seo(json_importer, sample_json_path):
    """Test JSON parsing with SEO metadata."""
    articles = await json_importer.parse_file(sample_json_path)

    article = articles[0]
    assert article.seo_metadata is not None
    assert article.seo_metadata["meta_title"] == "Docker Containers Tutorial Complete Developer Guide 2025"
    assert article.seo_metadata["focus_keyword"] == "docker containers tutorial"
    assert len(article.seo_metadata["primary_keywords"]) == 3
    assert len(article.seo_metadata["secondary_keywords"]) == 5
    assert article.seo_metadata["readability_score"] == 78.3
    assert article.seo_metadata["seo_score"] == 91.5


@pytest.mark.asyncio
async def test_json_author_id_normalization(json_importer, sample_json_path):
    """Test author ID normalization with prefix."""
    articles = await json_importer.parse_file(sample_json_path)

    # Author IDs should be normalized with json prefix
    assert isinstance(articles[0].author_id, int)
    assert articles[0].author_id > 0

    # Different raw author_ids should produce different normalized IDs
    assert articles[0].author_id != articles[1].author_id


@pytest.mark.asyncio
async def test_json_validate_article_success(json_importer, sample_json_path):
    """Test article validation success."""
    articles = await json_importer.parse_file(sample_json_path)

    is_valid, error = await json_importer.validate_article(articles[0])
    assert is_valid is True
    assert error is None


@pytest.mark.asyncio
async def test_json_file_not_found(json_importer):
    """Test error when JSON file doesn't exist."""
    with pytest.raises(FileNotFoundError):
        await json_importer.parse_file("/nonexistent/file.json")


@pytest.mark.asyncio
async def test_json_featured_image(json_importer, sample_json_path):
    """Test featured image parsing."""
    articles = await json_importer.parse_file(sample_json_path)

    assert articles[0].featured_image_path is None
    assert articles[1].featured_image_path == "/images/typescript-cover.jpg"


@pytest.mark.asyncio
async def test_json_status_mapping(json_importer, sample_json_path):
    """Test status value mapping."""
    articles = await json_importer.parse_file(sample_json_path)

    assert articles[0].status == ArticleStatus.IMPORTED
    assert articles[1].status == ArticleStatus.DRAFT
