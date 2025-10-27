"""Tests for CSV importer."""

import pytest
from pathlib import Path

from src.models import ArticleStatus
from src.services.article_importer.csv_importer import CSVImporter


@pytest.fixture
def csv_importer():
    """Create CSV importer instance."""
    return CSVImporter()


@pytest.fixture
def sample_csv_path():
    """Path to sample CSV file."""
    return str(Path(__file__).parent.parent.parent / "fixtures/import_files/sample_articles.csv")


@pytest.mark.asyncio
async def test_csv_parse_file(csv_importer, sample_csv_path):
    """Test parsing CSV file."""
    articles = await csv_importer.parse_file(sample_csv_path)

    assert len(articles) == 2
    assert articles[0].title == "Introduction to Machine Learning for Beginners Guide"
    assert articles[0].status == ArticleStatus.IMPORTED
    assert articles[0].source == "csv_import"


@pytest.mark.asyncio
async def test_csv_parse_with_seo(csv_importer, sample_csv_path):
    """Test CSV parsing with SEO metadata."""
    articles = await csv_importer.parse_file(sample_csv_path)

    article = articles[0]
    assert article.seo_metadata is not None
    assert article.seo_metadata["meta_title"] == "Complete Machine Learning Beginner's Tutorial 2025 Tech"
    assert article.seo_metadata["focus_keyword"] == "machine learning basics"
    assert len(article.seo_metadata["primary_keywords"]) == 3
    assert len(article.seo_metadata["secondary_keywords"]) == 5
    assert article.seo_metadata["readability_score"] == 75.5
    assert article.seo_metadata["seo_score"] == 89.2


@pytest.mark.asyncio
async def test_csv_author_id_normalization(csv_importer, sample_csv_path):
    """Test author ID normalization with prefix."""
    articles = await csv_importer.parse_file(sample_csv_path)

    # Author IDs should be normalized with csv prefix
    assert isinstance(articles[0].author_id, int)
    assert articles[0].author_id > 0

    # Same raw author_id should produce same normalized ID
    articles2 = await csv_importer.parse_file(sample_csv_path)
    assert articles[0].author_id == articles2[0].author_id


@pytest.mark.asyncio
async def test_csv_validate_article_success(csv_importer, sample_csv_path):
    """Test article validation success."""
    articles = await csv_importer.parse_file(sample_csv_path)

    is_valid, error = await csv_importer.validate_article(articles[0])
    if not is_valid:
        print(f"Validation failed: {error}")
    assert is_valid is True, f"Validation failed: {error}"
    assert error is None


@pytest.mark.asyncio
async def test_csv_file_not_found(csv_importer):
    """Test error when CSV file doesn't exist."""
    with pytest.raises(FileNotFoundError):
        await csv_importer.parse_file("/nonexistent/file.csv")


@pytest.mark.asyncio
async def test_csv_status_mapping(csv_importer, sample_csv_path):
    """Test status value mapping."""
    articles = await csv_importer.parse_file(sample_csv_path)

    assert articles[0].status == ArticleStatus.IMPORTED
    assert articles[1].status == ArticleStatus.DRAFT
