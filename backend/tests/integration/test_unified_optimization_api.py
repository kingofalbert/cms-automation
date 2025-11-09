"""Integration tests for unified optimization API endpoints (Phase 7).

Tests the complete optimization workflow:
1. Generate all optimizations (title + SEO + FAQ) via API
2. Retrieve optimization results
3. Check optimization status
4. Auto-trigger optimization after parsing confirmation
5. Background task execution
"""

import json
import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, MagicMock, patch

from src.models.article import Article
from src.models.title_suggestions import TitleSuggestion
from src.models.seo_suggestions import SEOSuggestion
from src.models.article_faq import ArticleFAQ


class TestUnifiedOptimizationAPI:
    """Integration tests for unified optimization endpoints."""

    @pytest.fixture
    async def sample_article(self, db_session: AsyncSession) -> Article:
        """Create a sample article with parsed data."""
        article = Article(
            title_main="Python编程完全指南",
            title_prefix="技术教程",
            title_suffix="2024最新版",
            body_html="<p>Python是一种强大的编程语言，广泛应用于数据科学、Web开发等领域。</p>" * 20,
            meta_description="学习Python编程的完整指南",
            seo_keywords=["Python", "编程", "教程"],
            status="parsed",
            parsing_confirmed=True,
        )
        db_session.add(article)
        await db_session.commit()
        await db_session.refresh(article)
        return article

    @pytest.fixture
    def mock_claude_response(self) -> dict:
        """Mock Claude API response with complete optimization data."""
        return {
            "title_suggestions": {
                "suggested_title_sets": [
                    {
                        "id": "option_1",
                        "title_prefix": "技术教程",
                        "title_main": "Python编程从入门到精通",
                        "title_suffix": "2024实战指南",
                        "full_title": "技术教程 | Python编程从入门到精通 | 2024实战指南",
                        "score": 9.2,
                        "strengths": ["SEO优化", "吸引眼球", "长度适中"],
                        "type": "balanced",
                        "recommendation": "推荐使用，平衡了SEO和可读性",
                        "character_count": {
                            "prefix": 4,
                            "main": 12,
                            "suffix": 8,
                            "total": 24
                        }
                    },
                    {
                        "id": "option_2",
                        "title_prefix": "编程教学",
                        "title_main": "掌握Python核心技术",
                        "title_suffix": "完整教程",
                        "full_title": "编程教学 | 掌握Python核心技术 | 完整教程",
                        "score": 8.8,
                        "strengths": ["简洁明了", "技术导向"],
                        "type": "technical",
                        "recommendation": "适合技术型受众",
                        "character_count": {
                            "prefix": 4,
                            "main": 11,
                            "suffix": 4,
                            "total": 19
                        }
                    }
                ],
                "optimization_notes": [
                    "增加了更具吸引力的动词",
                    "加入了年份以体现时效性",
                    "优化了关键词分布"
                ]
            },
            "seo_suggestions": {
                "seo_keywords": {
                    "focus_keyword": "Python编程教程",
                    "focus_keyword_rationale": "综合搜索量和相关性，这是最佳核心关键词",
                    "primary_keywords": [
                        "Python入门",
                        "Python教程",
                        "编程学习",
                        "Python语法"
                    ],
                    "secondary_keywords": [
                        "Python开发",
                        "编程基础",
                        "数据科学",
                        "Web开发",
                        "Python实战",
                        "代码示例"
                    ]
                },
                "meta_description": {
                    "original_meta_description": "学习Python编程的完整指南",
                    "suggested_meta_description": "从零开始学习Python编程，包含基础语法、实战案例和最佳实践。适合初学者和进阶开发者的完整教程。",
                    "meta_description_improvements": [
                        "增加了具体内容描述",
                        "包含了目标受众信息",
                        "优化了字符长度（150-160字符）",
                        "添加了更多关键词"
                    ],
                    "meta_description_score": 9.0
                },
                "tags": {
                    "suggested_tags": [
                        {"tag": "Python", "relevance": 0.98, "type": "primary"},
                        {"tag": "编程教程", "relevance": 0.95, "type": "primary"},
                        {"tag": "入门指南", "relevance": 0.88, "type": "secondary"},
                        {"tag": "编程语言", "relevance": 0.85, "type": "secondary"},
                        {"tag": "软件开发", "relevance": 0.80, "type": "secondary"},
                        {"tag": "代码学习", "relevance": 0.75, "type": "tertiary"},
                        {"tag": "技术教程", "relevance": 0.72, "type": "tertiary"},
                        {"tag": "开发工具", "relevance": 0.68, "type": "tertiary"}
                    ],
                    "recommended_tag_count": "6-8个",
                    "tag_strategy": "覆盖核心主题、目标受众和相关技术领域"
                }
            },
            "faqs": [
                {
                    "question": "什么是Python？",
                    "answer": "Python是一种高级、通用型编程语言，以其简洁的语法和强大的功能而闻名。",
                    "question_type": "definition",
                    "search_intent": "informational",
                    "keywords_covered": ["Python", "编程语言"],
                    "confidence": 0.95
                },
                {
                    "question": "如何开始学习Python？",
                    "answer": "从安装Python环境开始，然后学习基础语法，通过实践项目来巩固知识。",
                    "question_type": "how_to",
                    "search_intent": "informational",
                    "keywords_covered": ["学习Python", "入门"],
                    "confidence": 0.92
                },
                {
                    "question": "Python适合初学者吗？",
                    "answer": "是的，Python以其简洁易读的语法非常适合编程初学者。",
                    "question_type": "factual",
                    "search_intent": "commercial",
                    "keywords_covered": ["Python", "初学者"],
                    "confidence": 0.90
                }
            ]
        }

    @pytest.mark.asyncio
    async def test_generate_all_optimizations_success(
        self,
        client: AsyncClient,
        sample_article: Article,
        mock_claude_response: dict,
        db_session: AsyncSession,
    ):
        """Test successful generation of all optimizations via API."""
        # Mock Claude API
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps(mock_claude_response, ensure_ascii=False))]
        mock_response.usage.input_tokens = 2000
        mock_response.usage.output_tokens = 1500
        mock_response.model = "claude-3-5-sonnet-20241022"

        with patch('anthropic.AsyncAnthropic') as mock_anthropic:
            mock_client = AsyncMock()
            mock_client.messages.create = AsyncMock(return_value=mock_response)
            mock_anthropic.return_value = mock_client

            # Make API request
            response = await client.post(
                f"/v1/articles/{sample_article.id}/generate-all-optimizations",
                json={"regenerate": False}
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            # Verify response structure
            assert "title_suggestions" in data
            assert "seo_suggestions" in data
            assert "faqs" in data
            assert "generation_metadata" in data

            # Verify title suggestions
            assert len(data["title_suggestions"]["suggested_title_sets"]) == 2
            first_title = data["title_suggestions"]["suggested_title_sets"][0]
            assert first_title["title_main"] == "Python编程从入门到精通"
            assert first_title["score"] == 9.2

            # Verify SEO suggestions
            assert data["seo_suggestions"]["seo_keywords"]["focus_keyword"] == "Python编程教程"
            assert len(data["seo_suggestions"]["seo_keywords"]["primary_keywords"]) == 4

            # Verify FAQs
            assert len(data["faqs"]) == 3
            assert data["faqs"][0]["question"] == "什么是Python？"

            # Verify metadata
            metadata = data["generation_metadata"]
            assert metadata["total_tokens"] == 3500
            assert metadata["cached"] is False

    @pytest.mark.asyncio
    async def test_generate_all_optimizations_database_storage(
        self,
        client: AsyncClient,
        sample_article: Article,
        mock_claude_response: dict,
        db_session: AsyncSession,
    ):
        """Test that generated optimizations are correctly stored in database."""
        # Mock Claude API
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps(mock_claude_response, ensure_ascii=False))]
        mock_response.usage.input_tokens = 2000
        mock_response.usage.output_tokens = 1500
        mock_response.model = "claude-3-5-sonnet-20241022"

        with patch('anthropic.AsyncAnthropic') as mock_anthropic:
            mock_client = AsyncMock()
            mock_client.messages.create = AsyncMock(return_value=mock_response)
            mock_anthropic.return_value = mock_client

            # Generate optimizations
            await client.post(
                f"/v1/articles/{sample_article.id}/generate-all-optimizations",
                json={"regenerate": False}
            )

            # Verify TitleSuggestion was created
            stmt = select(TitleSuggestion).where(TitleSuggestion.article_id == sample_article.id)
            result = await db_session.execute(stmt)
            title_suggestion = result.scalar_one_or_none()

            assert title_suggestion is not None
            assert len(title_suggestion.suggested_title_sets) == 2
            assert len(title_suggestion.optimization_notes) == 3

            # Verify SEOSuggestion was created
            stmt = select(SEOSuggestion).where(SEOSuggestion.article_id == sample_article.id)
            result = await db_session.execute(stmt)
            seo_suggestion = result.scalar_one_or_none()

            assert seo_suggestion is not None
            assert seo_suggestion.seo_keywords["focus_keyword"] == "Python编程教程"
            assert len(seo_suggestion.tags["suggested_tags"]) == 8

            # Verify ArticleFAQs were created
            stmt = select(ArticleFAQ).where(ArticleFAQ.article_id == sample_article.id)
            result = await db_session.execute(stmt)
            faqs = result.scalars().all()

            assert len(faqs) == 3
            assert faqs[0].question == "什么是Python？"
            assert faqs[0].question_type == "definition"

    @pytest.mark.asyncio
    async def test_get_optimizations_returns_cached_result(
        self,
        client: AsyncClient,
        sample_article: Article,
        mock_claude_response: dict,
        db_session: AsyncSession,
    ):
        """Test that GET endpoint returns cached optimization results."""
        # First, generate optimizations
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps(mock_claude_response, ensure_ascii=False))]
        mock_response.usage.input_tokens = 2000
        mock_response.usage.output_tokens = 1500
        mock_response.model = "claude-3-5-sonnet-20241022"

        with patch('anthropic.AsyncAnthropic') as mock_anthropic:
            mock_client = AsyncMock()
            mock_client.messages.create = AsyncMock(return_value=mock_response)
            mock_anthropic.return_value = mock_client

            await client.post(
                f"/v1/articles/{sample_article.id}/generate-all-optimizations",
                json={"regenerate": False}
            )

        # Now retrieve cached results without mocking Claude (should not call API)
        response = await client.get(f"/v1/articles/{sample_article.id}/optimizations")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify cached flag
        assert data["generation_metadata"]["cached"] is True

        # Verify data matches what was stored
        assert len(data["title_suggestions"]["suggested_title_sets"]) == 2
        assert data["seo_suggestions"]["seo_keywords"]["focus_keyword"] == "Python编程教程"
        assert len(data["faqs"]) == 3

    @pytest.mark.asyncio
    async def test_get_optimization_status(
        self,
        client: AsyncClient,
        sample_article: Article,
        mock_claude_response: dict,
        db_session: AsyncSession,
    ):
        """Test optimization status endpoint."""
        # Before generation
        response = await client.get(f"/v1/articles/{sample_article.id}/optimization-status")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["generated"] is False
        assert data["has_title_suggestions"] is False
        assert data["has_seo_suggestions"] is False
        assert data["has_faqs"] is False
        assert data["faq_count"] == 0

        # Generate optimizations
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps(mock_claude_response, ensure_ascii=False))]
        mock_response.usage.input_tokens = 2000
        mock_response.usage.output_tokens = 1500
        mock_response.model = "claude-3-5-sonnet-20241022"

        with patch('anthropic.AsyncAnthropic') as mock_anthropic:
            mock_client = AsyncMock()
            mock_client.messages.create = AsyncMock(return_value=mock_response)
            mock_anthropic.return_value = mock_client

            await client.post(
                f"/v1/articles/{sample_article.id}/generate-all-optimizations",
                json={"regenerate": False}
            )

        # After generation
        response = await client.get(f"/v1/articles/{sample_article.id}/optimization-status")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["generated"] is True
        assert data["has_title_suggestions"] is True
        assert data["has_seo_suggestions"] is True
        assert data["has_faqs"] is True
        assert data["faq_count"] == 3
        assert "generated_at" in data
        assert "cost_usd" in data

    @pytest.mark.asyncio
    async def test_delete_optimizations(
        self,
        client: AsyncClient,
        sample_article: Article,
        mock_claude_response: dict,
        db_session: AsyncSession,
    ):
        """Test deleting optimization data."""
        # First generate optimizations
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps(mock_claude_response, ensure_ascii=False))]
        mock_response.usage.input_tokens = 2000
        mock_response.usage.output_tokens = 1500
        mock_response.model = "claude-3-5-sonnet-20241022"

        with patch('anthropic.AsyncAnthropic') as mock_anthropic:
            mock_client = AsyncMock()
            mock_client.messages.create = AsyncMock(return_value=mock_response)
            mock_anthropic.return_value = mock_client

            await client.post(
                f"/v1/articles/{sample_article.id}/generate-all-optimizations",
                json={"regenerate": False}
            )

        # Verify data exists
        stmt = select(TitleSuggestion).where(TitleSuggestion.article_id == sample_article.id)
        result = await db_session.execute(stmt)
        assert result.scalar_one_or_none() is not None

        # Delete optimizations
        response = await client.delete(f"/v1/articles/{sample_article.id}/optimizations")
        assert response.status_code == status.HTTP_200_OK

        # Verify data was deleted
        await db_session.expire_all()
        stmt = select(TitleSuggestion).where(TitleSuggestion.article_id == sample_article.id)
        result = await db_session.execute(stmt)
        assert result.scalar_one_or_none() is None

        stmt = select(SEOSuggestion).where(SEOSuggestion.article_id == sample_article.id)
        result = await db_session.execute(stmt)
        assert result.scalar_one_or_none() is None

        stmt = select(ArticleFAQ).where(ArticleFAQ.article_id == sample_article.id)
        result = await db_session.execute(stmt)
        assert len(result.scalars().all()) == 0

    @pytest.mark.asyncio
    async def test_regenerate_optimizations(
        self,
        client: AsyncClient,
        sample_article: Article,
        mock_claude_response: dict,
        db_session: AsyncSession,
    ):
        """Test regenerating optimizations with regenerate=True flag."""
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps(mock_claude_response, ensure_ascii=False))]
        mock_response.usage.input_tokens = 2000
        mock_response.usage.output_tokens = 1500
        mock_response.model = "claude-3-5-sonnet-20241022"

        with patch('anthropic.AsyncAnthropic') as mock_anthropic:
            mock_client = AsyncMock()
            mock_client.messages.create = AsyncMock(return_value=mock_response)
            mock_anthropic.return_value = mock_client

            # First generation
            response1 = await client.post(
                f"/v1/articles/{sample_article.id}/generate-all-optimizations",
                json={"regenerate": False}
            )
            assert response1.status_code == status.HTTP_200_OK

            # Second generation with regenerate=True (should call API again)
            response2 = await client.post(
                f"/v1/articles/{sample_article.id}/generate-all-optimizations",
                json={"regenerate": True}
            )
            assert response2.status_code == status.HTTP_200_OK

            # Verify Claude API was called twice
            assert mock_client.messages.create.call_count == 2

    @pytest.mark.asyncio
    async def test_auto_trigger_on_parsing_confirmation(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        mock_claude_response: dict,
    ):
        """Test that optimization generation is auto-triggered after parsing confirmation."""
        # Create unparsed article
        article = Article(
            title_main="测试文章",
            body_html="<p>内容</p>" * 10,
            status="parsed",
            parsing_confirmed=False,
        )
        db_session.add(article)
        await db_session.commit()
        await db_session.refresh(article)

        # Mock Claude API for background task
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps(mock_claude_response, ensure_ascii=False))]
        mock_response.usage.input_tokens = 2000
        mock_response.usage.output_tokens = 1500
        mock_response.model = "claude-3-5-sonnet-20241022"

        with patch('anthropic.AsyncAnthropic') as mock_anthropic:
            mock_client = AsyncMock()
            mock_client.messages.create = AsyncMock(return_value=mock_response)
            mock_anthropic.return_value = mock_client

            # Confirm parsing (should trigger background optimization)
            response = await client.post(
                f"/v1/articles/{article.id}/confirm-parsing",
                json={
                    "confirmed_by": "test_user",
                    "feedback": "Looks good"
                }
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["optimization_scheduled"] is True

            # Note: In real scenario, background task would run asynchronously
            # For testing, we would need to wait or use a different approach
            # to verify the task actually executed

    @pytest.mark.asyncio
    async def test_optimization_not_found_returns_404(
        self,
        client: AsyncClient,
        sample_article: Article,
    ):
        """Test that GET optimization returns 404 when no data exists."""
        response = await client.get(f"/v1/articles/{sample_article.id}/optimizations")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "not found" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_article_not_found_returns_404(
        self,
        client: AsyncClient,
    ):
        """Test that non-existent article returns 404."""
        non_existent_id = 99999

        response = await client.post(
            f"/v1/articles/{non_existent_id}/generate-all-optimizations",
            json={"regenerate": False}
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
