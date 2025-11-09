"""Integration tests for article parsing API endpoints (Phase 7).

Tests the complete parsing workflow:
1. Parse article (AI or heuristic)
2. Retrieve parsing results
3. Review images
4. Confirm parsing
"""

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.article import Article
from src.models.article_image import ArticleImage


class TestArticleParsingAPI:
    """Integration tests for article parsing endpoints."""

    @pytest.fixture
    async def sample_article(self, db_session: AsyncSession) -> Article:
        """Create a sample article with raw HTML."""
        article = Article(
            title="Test Article",
            raw_html="""
            <html>
                <body>
                    <h1>【測試】這是標題：副標題</h1>
                    <p>文／張三</p>
                    <p>這是第一段正文內容，足夠長以便不會被當作元數據處理，超過五十個字符的長度要求。</p>
                    <p>這是第二段正文內容。</p>
                    <img src="https://example.com/test.jpg" alt="測試圖片">
                </body>
            </html>
            """,
            status="imported",
        )
        db_session.add(article)
        await db_session.commit()
        await db_session.refresh(article)
        return article

    @pytest.mark.asyncio
    async def test_parse_article_heuristic(
        self,
        client: AsyncClient,
        sample_article: Article,
        db_session: AsyncSession,
    ):
        """Test parsing an article with heuristic mode."""
        response = await client.post(
            f"/v1/articles/{sample_article.id}/parse",
            json={
                "use_ai": False,  # Use heuristic parsing
                "download_images": False,  # Skip image download for test
                "fallback_to_heuristic": True,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["success"] is True
        assert data["article_id"] == sample_article.id
        assert data["parsing_method"] == "heuristic"
        assert data["parsing_confidence"] > 0

        # Verify database was updated
        await db_session.refresh(sample_article)
        assert sample_article.title_prefix == "【測試】"
        assert "這是標題" in sample_article.title_main
        assert sample_article.title_suffix == "副標題"
        assert sample_article.author_name == "張三"

    @pytest.mark.asyncio
    async def test_parse_article_not_found(self, client: AsyncClient):
        """Test parsing non-existent article returns 404."""
        response = await client.post(
            "/v1/articles/99999/parse",
            json={"use_ai": False, "download_images": False},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_parse_article_no_raw_html(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """Test parsing article without raw HTML returns 400."""
        # Create article without raw HTML
        article = Article(title="No HTML", status="draft")
        db_session.add(article)
        await db_session.commit()

        response = await client.post(
            f"/v1/articles/{article.id}/parse",
            json={"use_ai": False, "download_images": False},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "no raw html" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_parsing_result(
        self,
        client: AsyncClient,
        sample_article: Article,
        db_session: AsyncSession,
    ):
        """Test retrieving parsed article data."""
        # First parse the article
        await client.post(
            f"/v1/articles/{sample_article.id}/parse",
            json={"use_ai": False, "download_images": False},
        )

        # Then get parsing result
        response = await client.get(f"/v1/articles/{sample_article.id}/parsing-result")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["title_prefix"] == "【測試】"
        assert "這是標題" in data["title_main"]
        assert data["title_suffix"] == "副標題"
        assert data["author_name"] == "張三"
        assert data["parsing_confirmed"] is False
        assert "full_title" in data
        assert "【測試】" in data["full_title"]

    @pytest.mark.asyncio
    async def test_get_parsing_result_not_parsed(
        self,
        client: AsyncClient,
        sample_article: Article,
    ):
        """Test getting parsing result for unparsed article returns 400."""
        response = await client.get(f"/v1/articles/{sample_article.id}/parsing-result")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "not been parsed" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_confirm_parsing(
        self,
        client: AsyncClient,
        sample_article: Article,
        db_session: AsyncSession,
    ):
        """Test confirming parsed article data."""
        # First parse the article
        await client.post(
            f"/v1/articles/{sample_article.id}/parse",
            json={"use_ai": False, "download_images": False},
        )

        # Confirm parsing
        response = await client.post(
            f"/v1/articles/{sample_article.id}/confirm-parsing",
            json={
                "confirmed_by": "test_user",
                "feedback": "Looks good!",
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["success"] is True
        assert data["article_id"] == sample_article.id
        assert "confirmed_at" in data
        assert data["confirmed_by"] == "test_user"

        # Verify database
        await db_session.refresh(sample_article)
        assert sample_article.parsing_confirmed is True
        assert sample_article.parsing_confirmed_by == "test_user"
        assert sample_article.parsing_feedback == "Looks good!"

    @pytest.mark.asyncio
    async def test_confirm_parsing_not_parsed(
        self,
        client: AsyncClient,
        sample_article: Article,
    ):
        """Test confirming unparsed article returns 400."""
        response = await client.post(
            f"/v1/articles/{sample_article.id}/confirm-parsing",
            json={"confirmed_by": "test_user"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "not been parsed" in response.json()["detail"].lower()


class TestImageReviewAPI:
    """Integration tests for image review endpoints."""

    @pytest.fixture
    async def article_with_images(self, db_session: AsyncSession) -> tuple[Article, list[ArticleImage]]:
        """Create article with parsed images."""
        article = Article(
            title="Article with Images",
            raw_html="<html><body><p>Test</p></body></html>",
            title_main="Test Article",
            body_html="<p>Test content</p>",
            status="imported",
        )
        db_session.add(article)
        await db_session.flush()

        images = [
            ArticleImage(
                article_id=article.id,
                position=0,
                source_url="https://example.com/img1.jpg",
                caption="Image 1",
                image_metadata={
                    "_schema_version": "1.0",
                    "image_technical_specs": {
                        "width": 800,
                        "height": 600,
                        "format": "JPEG",
                        "mime_type": "image/jpeg",
                        "file_size_bytes": 50000,
                    },
                },
            ),
            ArticleImage(
                article_id=article.id,
                position=1,
                source_url="https://example.com/img2.jpg",
                caption="Image 2",
                image_metadata={
                    "_schema_version": "1.0",
                    "image_technical_specs": {
                        "width": 1920,
                        "height": 1080,
                        "format": "PNG",
                        "mime_type": "image/png",
                        "file_size_bytes": 120000,
                    },
                },
            ),
        ]

        for img in images:
            db_session.add(img)

        await db_session.commit()
        return article, images

    @pytest.mark.asyncio
    async def test_list_article_images(
        self,
        client: AsyncClient,
        article_with_images: tuple[Article, list[ArticleImage]],
    ):
        """Test listing all images for an article."""
        article, images = article_with_images

        response = await client.get(f"/v1/articles/{article.id}/images")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert len(data) == 2
        assert data[0]["position"] == 0
        assert data[0]["source_url"] == "https://example.com/img1.jpg"
        assert data[0]["width"] == 800
        assert data[0]["format"] == "JPEG"

        assert data[1]["position"] == 1
        assert data[1]["source_url"] == "https://example.com/img2.jpg"
        assert data[1]["width"] == 1920
        assert data[1]["format"] == "PNG"

    @pytest.mark.asyncio
    async def test_review_image_keep(
        self,
        client: AsyncClient,
        article_with_images: tuple[Article, list[ArticleImage]],
        db_session: AsyncSession,
    ):
        """Test reviewing image with 'keep' action."""
        article, images = article_with_images
        image = images[0]

        response = await client.post(
            f"/v1/articles/{article.id}/images/{image.id}/review",
            json={"action": "keep"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["success"] is True
        assert data["image_id"] == image.id
        assert data["action"] == "keep"

        # Image should still exist
        await db_session.refresh(image)
        assert image.id is not None

    @pytest.mark.asyncio
    async def test_review_image_remove(
        self,
        client: AsyncClient,
        article_with_images: tuple[Article, list[ArticleImage]],
        db_session: AsyncSession,
    ):
        """Test removing an image."""
        article, images = article_with_images
        image = images[0]
        image_id = image.id

        response = await client.post(
            f"/v1/articles/{article.id}/images/{image_id}/review",
            json={"action": "remove"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["success"] is True
        assert data["action"] == "remove"

        # Image should be deleted
        deleted_image = await db_session.get(ArticleImage, image_id)
        assert deleted_image is None

    @pytest.mark.asyncio
    async def test_review_image_replace_caption(
        self,
        client: AsyncClient,
        article_with_images: tuple[Article, list[ArticleImage]],
        db_session: AsyncSession,
    ):
        """Test replacing image caption."""
        article, images = article_with_images
        image = images[0]

        response = await client.post(
            f"/v1/articles/{article.id}/images/{image.id}/review",
            json={
                "action": "replace_caption",
                "new_caption": "Updated Caption",
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["success"] is True

        # Verify caption updated
        await db_session.refresh(image)
        assert image.caption == "Updated Caption"

    @pytest.mark.asyncio
    async def test_review_image_replace_caption_missing_param(
        self,
        client: AsyncClient,
        article_with_images: tuple[Article, list[ArticleImage]],
    ):
        """Test replace_caption without new_caption returns 400."""
        article, images = article_with_images
        image = images[0]

        response = await client.post(
            f"/v1/articles/{article.id}/images/{image.id}/review",
            json={"action": "replace_caption"},  # Missing new_caption
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "new_caption is required" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_review_image_not_found(self, client: AsyncClient):
        """Test reviewing non-existent image returns 404."""
        response = await client.post(
            "/v1/articles/1/images/99999/review",
            json={"action": "keep"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestParsingWorkflow:
    """Integration tests for complete parsing workflow."""

    @pytest.mark.asyncio
    async def test_complete_parsing_workflow(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """Test complete workflow: parse → review → confirm."""
        # Step 1: Create article
        article = Article(
            title="Workflow Test",
            raw_html="""
            <html>
                <body>
                    <h1>完整工作流程測試</h1>
                    <p>文／測試作者</p>
                    <p>這是測試文章的正文內容，用於驗證完整的解析工作流程。這段內容需要足夠長以通過驗證。</p>
                </body>
            </html>
            """,
            status="imported",
        )
        db_session.add(article)
        await db_session.commit()

        # Step 2: Parse article
        parse_response = await client.post(
            f"/v1/articles/{article.id}/parse",
            json={"use_ai": False, "download_images": False},
        )
        assert parse_response.status_code == status.HTTP_200_OK
        assert parse_response.json()["success"] is True

        # Step 3: Get parsing result
        result_response = await client.get(f"/v1/articles/{article.id}/parsing-result")
        assert result_response.status_code == status.HTTP_200_OK
        result_data = result_response.json()
        assert result_data["title_main"] == "完整工作流程測試"
        assert result_data["author_name"] == "測試作者"
        assert result_data["parsing_confirmed"] is False

        # Step 4: Confirm parsing
        confirm_response = await client.post(
            f"/v1/articles/{article.id}/confirm-parsing",
            json={
                "confirmed_by": "integration_test",
                "feedback": "All checks passed",
            },
        )
        assert confirm_response.status_code == status.HTTP_200_OK

        # Step 5: Verify final state
        await db_session.refresh(article)
        assert article.parsing_confirmed is True
        assert article.parsing_confirmed_by == "integration_test"
        assert article.title_main == "完整工作流程測試"
        assert article.author_name == "測試作者"
