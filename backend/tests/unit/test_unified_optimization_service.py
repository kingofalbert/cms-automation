"""Unit tests for UnifiedOptimizationService (Phase 7).

Tests the unified AI optimization service that generates:
- Title optimization suggestions
- SEO keywords and meta description
- Tags
- FAQ questions
"""

import json
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Any

from src.services.parser.unified_optimization_service import UnifiedOptimizationService
from src.models.article import Article


class TestUnifiedOptimizationServiceInitialization:
    """Test suite for service initialization."""

    def test_service_initialization(self):
        """Test service initializes with required parameters."""
        service = UnifiedOptimizationService(
            anthropic_api_key="sk-test-key",
            db_session=MagicMock(),
        )

        assert service.anthropic_api_key == "sk-test-key"
        assert service.db_session is not None
        assert service.model == "claude-3-5-sonnet-20241022"  # Default model

    def test_service_initialization_with_custom_model(self):
        """Test service initializes with custom model."""
        service = UnifiedOptimizationService(
            anthropic_api_key="sk-test-key",
            db_session=MagicMock(),
            model="claude-3-opus-20240229",
        )

        assert service.model == "claude-3-opus-20240229"

    def test_service_initialization_without_api_key_raises_error(self):
        """Test service raises error when API key is missing."""
        with pytest.raises(ValueError, match="anthropic_api_key is required"):
            UnifiedOptimizationService(
                anthropic_api_key="",
                db_session=MagicMock(),
            )

    def test_service_initialization_without_db_session_raises_error(self):
        """Test service raises error when db_session is missing."""
        with pytest.raises(ValueError, match="db_session is required"):
            UnifiedOptimizationService(
                anthropic_api_key="sk-test-key",
                db_session=None,
            )


class TestPromptBuilding:
    """Test suite for prompt building methods."""

    @pytest.fixture
    def sample_article(self):
        """Create a sample article for testing."""
        article = Article(
            id=123,
            title_main="Python编程入门",
            title_prefix="技术教程",
            title_suffix="2024最新版",
            body_html="<p>Python是一种强大的编程语言。</p>" * 10,
            meta_description="学习Python编程的完整指南",
            seo_keywords=["Python", "编程", "入门"],
        )
        return article

    def test_build_unified_prompt(self, sample_article):
        """Test unified prompt generation includes all sections."""
        service = UnifiedOptimizationService(
            anthropic_api_key="sk-test-key",
            db_session=MagicMock(),
        )

        prompt = service._build_unified_prompt(sample_article)

        # Check prompt contains essential sections
        assert "标题优化" in prompt
        assert "SEO关键词" in prompt
        assert "Meta Description" in prompt
        assert "标签建议" in prompt
        assert "FAQ问题" in prompt

        # Check article content is included
        assert sample_article.title_main in prompt
        assert "Python" in prompt

    def test_build_unified_prompt_handles_missing_optional_fields(self):
        """Test prompt building handles articles with missing optional fields."""
        article = Article(
            id=456,
            title_main="Simple Title",
            body_html="<p>Simple content.</p>",
        )

        service = UnifiedOptimizationService(
            anthropic_api_key="sk-test-key",
            db_session=MagicMock(),
        )

        prompt = service._build_unified_prompt(article)

        # Should not crash and should contain basic structure
        assert "标题优化" in prompt
        assert "Simple Title" in prompt

    def test_build_unified_prompt_includes_body_preview(self, sample_article):
        """Test prompt includes a preview of the body content."""
        service = UnifiedOptimizationService(
            anthropic_api_key="sk-test-key",
            db_session=MagicMock(),
        )

        prompt = service._build_unified_prompt(sample_article)

        # Should include body preview (truncated if too long)
        assert "正文内容" in prompt or "Body" in prompt
        assert "Python" in prompt


class TestResponseParsing:
    """Test suite for Claude API response parsing."""

    @pytest.fixture
    def sample_claude_response(self) -> str:
        """Sample Claude API response in expected JSON format."""
        return json.dumps({
            "title_suggestions": {
                "suggested_title_sets": [
                    {
                        "id": "option_1",
                        "title_prefix": "技术教程",
                        "title_main": "Python编程完全指南",
                        "title_suffix": "从入门到精通",
                        "full_title": "技术教程 | Python编程完全指南 | 从入门到精通",
                        "score": 9.5,
                        "strengths": ["清晰明确", "SEO友好"],
                        "type": "balanced",
                        "recommendation": "推荐使用",
                        "character_count": {
                            "prefix": 4,
                            "main": 10,
                            "suffix": 6,
                            "total": 20
                        }
                    }
                ],
                "optimization_notes": ["标题长度适中", "关键词覆盖完整"]
            },
            "seo_suggestions": {
                "seo_keywords": {
                    "focus_keyword": "Python编程",
                    "focus_keyword_rationale": "主题核心词",
                    "primary_keywords": ["Python", "编程入门", "教程"],
                    "secondary_keywords": ["Python语法", "编程基础", "代码示例"]
                },
                "meta_description": {
                    "original_meta_description": "学习Python",
                    "suggested_meta_description": "完整的Python编程入门教程，涵盖基础语法、实战案例等内容。",
                    "meta_description_improvements": ["增加关键词", "提升吸引力"],
                    "meta_description_score": 8.5
                },
                "tags": {
                    "suggested_tags": [
                        {"tag": "Python", "relevance": 0.95, "type": "primary"},
                        {"tag": "编程", "relevance": 0.90, "type": "primary"}
                    ],
                    "recommended_tag_count": "6-8",
                    "tag_strategy": "覆盖核心主题"
                }
            },
            "faqs": [
                {
                    "question": "什么是Python？",
                    "answer": "Python是一种高级编程语言。",
                    "question_type": "definition",
                    "search_intent": "informational",
                    "keywords_covered": ["Python", "编程语言"],
                    "confidence": 0.92
                }
            ]
        }, ensure_ascii=False)

    def test_parse_unified_response_success(self, sample_claude_response):
        """Test successful parsing of Claude response."""
        service = UnifiedOptimizationService(
            anthropic_api_key="sk-test-key",
            db_session=MagicMock(),
        )

        result = service._parse_unified_response(sample_claude_response)

        # Check structure
        assert "title_suggestions" in result
        assert "seo_suggestions" in result
        assert "faqs" in result

        # Check title suggestions
        assert len(result["title_suggestions"]["suggested_title_sets"]) > 0
        first_title = result["title_suggestions"]["suggested_title_sets"][0]
        assert first_title["title_main"] == "Python编程完全指南"
        assert first_title["score"] == 9.5

        # Check SEO suggestions
        assert result["seo_suggestions"]["seo_keywords"]["focus_keyword"] == "Python编程"
        assert len(result["seo_suggestions"]["seo_keywords"]["primary_keywords"]) == 3

        # Check FAQs
        assert len(result["faqs"]) == 1
        assert result["faqs"][0]["question"] == "什么是Python？"

    def test_parse_unified_response_handles_malformed_json(self):
        """Test parsing handles malformed JSON gracefully."""
        service = UnifiedOptimizationService(
            anthropic_api_key="sk-test-key",
            db_session=MagicMock(),
        )

        malformed_json = "{ invalid json"

        with pytest.raises(ValueError, match="Failed to parse JSON"):
            service._parse_unified_response(malformed_json)

    def test_parse_unified_response_handles_missing_required_fields(self):
        """Test parsing handles missing required fields."""
        service = UnifiedOptimizationService(
            anthropic_api_key="sk-test-key",
            db_session=MagicMock(),
        )

        incomplete_response = json.dumps({
            "title_suggestions": {},
            # Missing seo_suggestions and faqs
        })

        with pytest.raises(ValueError, match="Missing required field"):
            service._parse_unified_response(incomplete_response)

    def test_parse_unified_response_extracts_json_from_markdown(self):
        """Test parsing extracts JSON from markdown code blocks."""
        service = UnifiedOptimizationService(
            anthropic_api_key="sk-test-key",
            db_session=MagicMock(),
        )

        # Claude sometimes returns JSON wrapped in markdown
        markdown_response = """Here's the optimization data:

```json
{
  "title_suggestions": {"suggested_title_sets": []},
  "seo_suggestions": {
    "seo_keywords": {"focus_keyword": "test", "primary_keywords": [], "secondary_keywords": []},
    "meta_description": {"meta_description_improvements": []},
    "tags": {"suggested_tags": []}
  },
  "faqs": []
}
```

That's all!
"""

        result = service._parse_unified_response(markdown_response)

        assert "title_suggestions" in result
        assert "seo_suggestions" in result


class TestStorageMethods:
    """Test suite for database storage methods."""

    @pytest.fixture
    def sample_optimization_result(self) -> dict[str, Any]:
        """Sample optimization result for storage testing."""
        return {
            "title_suggestions": {
                "suggested_title_sets": [
                    {
                        "id": "option_1",
                        "title_main": "Test Title",
                        "score": 9.0,
                        "strengths": ["clear"],
                        "type": "balanced",
                        "recommendation": "good",
                        "character_count": {"total": 10}
                    }
                ],
                "optimization_notes": ["Note 1"]
            },
            "seo_suggestions": {
                "seo_keywords": {
                    "focus_keyword": "test",
                    "primary_keywords": ["keyword1"],
                    "secondary_keywords": ["keyword2"]
                },
                "meta_description": {
                    "suggested_meta_description": "Test description",
                    "meta_description_improvements": ["improvement1"],
                    "meta_description_score": 8.0
                },
                "tags": {
                    "suggested_tags": [
                        {"tag": "tag1", "relevance": 0.9, "type": "primary"}
                    ]
                }
            },
            "faqs": [
                {
                    "question": "Q1?",
                    "answer": "A1",
                    "keywords_covered": ["k1"]
                }
            ]
        }

    @pytest.mark.asyncio
    async def test_store_optimizations_creates_records(self, sample_optimization_result):
        """Test storage creates database records correctly."""
        mock_db = AsyncMock()

        service = UnifiedOptimizationService(
            anthropic_api_key="sk-test-key",
            db_session=mock_db,
        )

        article_id = 123
        await service._store_optimizations(article_id, sample_optimization_result)

        # Verify database operations were called
        assert mock_db.add.call_count >= 3  # TitleSuggestion + SEOSuggestion + FAQs
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_store_optimizations_handles_empty_faqs(self, sample_optimization_result):
        """Test storage handles empty FAQ list."""
        mock_db = AsyncMock()

        service = UnifiedOptimizationService(
            anthropic_api_key="sk-test-key",
            db_session=mock_db,
        )

        # Remove FAQs
        sample_optimization_result["faqs"] = []

        article_id = 456
        await service._store_optimizations(article_id, sample_optimization_result)

        # Should still work without errors
        assert mock_db.commit.called


class TestGenerateAllOptimizations:
    """Test suite for the main optimization generation method."""

    @pytest.fixture
    def sample_article(self):
        """Create a sample article for testing."""
        return Article(
            id=789,
            title_main="测试文章标题",
            body_html="<p>测试内容。</p>" * 20,
        )

    @pytest.mark.asyncio
    async def test_generate_all_optimizations_success(self, sample_article):
        """Test successful optimization generation."""
        mock_db = AsyncMock()

        # Mock Claude API response
        mock_claude_response = MagicMock()
        mock_claude_response.content = [
            MagicMock(text=json.dumps({
                "title_suggestions": {
                    "suggested_title_sets": [],
                    "optimization_notes": []
                },
                "seo_suggestions": {
                    "seo_keywords": {
                        "focus_keyword": "test",
                        "primary_keywords": [],
                        "secondary_keywords": []
                    },
                    "meta_description": {
                        "meta_description_improvements": []
                    },
                    "tags": {"suggested_tags": []}
                },
                "faqs": []
            }, ensure_ascii=False))
        ]
        mock_claude_response.usage.input_tokens = 1000
        mock_claude_response.usage.output_tokens = 500
        mock_claude_response.model = "claude-3-5-sonnet-20241022"

        with patch('anthropic.AsyncAnthropic') as mock_anthropic:
            mock_client = AsyncMock()
            mock_client.messages.create = AsyncMock(return_value=mock_claude_response)
            mock_anthropic.return_value = mock_client

            service = UnifiedOptimizationService(
                anthropic_api_key="sk-test-key",
                db_session=mock_db,
            )
            service.client = mock_client

            result = await service.generate_all_optimizations(
                article=sample_article,
                regenerate=False
            )

            # Check result structure
            assert "title_suggestions" in result
            assert "seo_suggestions" in result
            assert "faqs" in result
            assert "generation_metadata" in result

            # Check metadata
            metadata = result["generation_metadata"]
            assert metadata["total_tokens"] == 1500
            assert metadata["input_tokens"] == 1000
            assert metadata["output_tokens"] == 500
            assert not metadata["cached"]

    @pytest.mark.asyncio
    async def test_generate_all_optimizations_returns_cached_result(self, sample_article):
        """Test that existing optimizations are returned when regenerate=False."""
        mock_db = AsyncMock()

        # Mock existing optimization records
        from src.models.title_suggestions import TitleSuggestion
        from src.models.seo_suggestions import SEOSuggestion

        mock_title_suggestion = MagicMock(spec=TitleSuggestion)
        mock_title_suggestion.suggested_title_sets = []
        mock_title_suggestion.optimization_notes = []

        mock_seo_suggestion = MagicMock(spec=SEOSuggestion)
        mock_seo_suggestion.seo_keywords = {"focus_keyword": "cached"}
        mock_seo_suggestion.meta_description = {}
        mock_seo_suggestion.tags = {"suggested_tags": []}

        # Mock database query results
        mock_db.execute = AsyncMock()
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = AsyncMock(side_effect=[
            mock_title_suggestion,
            mock_seo_suggestion
        ])
        mock_result.scalars = AsyncMock(return_value=AsyncMock(all=AsyncMock(return_value=[])))
        mock_db.execute.return_value = mock_result

        service = UnifiedOptimizationService(
            anthropic_api_key="sk-test-key",
            db_session=mock_db,
        )

        result = await service.generate_all_optimizations(
            article=sample_article,
            regenerate=False
        )

        # Should return cached result without calling Claude API
        assert result["generation_metadata"]["cached"] is True
        assert "seo_keywords" in result["seo_suggestions"]

    @pytest.mark.asyncio
    async def test_generate_all_optimizations_handles_api_error(self, sample_article):
        """Test error handling when Claude API fails."""
        mock_db = AsyncMock()

        with patch('anthropic.AsyncAnthropic') as mock_anthropic:
            mock_client = AsyncMock()
            mock_client.messages.create = AsyncMock(
                side_effect=Exception("API Error")
            )
            mock_anthropic.return_value = mock_client

            service = UnifiedOptimizationService(
                anthropic_api_key="sk-test-key",
                db_session=mock_db,
            )
            service.client = mock_client

            with pytest.raises(Exception, match="API Error"):
                await service.generate_all_optimizations(
                    article=sample_article,
                    regenerate=True
                )


class TestCostCalculation:
    """Test suite for cost calculation methods."""

    def test_calculate_cost_for_claude_sonnet(self):
        """Test cost calculation for Claude Sonnet model."""
        service = UnifiedOptimizationService(
            anthropic_api_key="sk-test-key",
            db_session=MagicMock(),
            model="claude-3-5-sonnet-20241022",
        )

        input_tokens = 1000
        output_tokens = 500

        cost = service._calculate_cost(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model="claude-3-5-sonnet-20241022"
        )

        # Claude 3.5 Sonnet pricing: $3/MTok input, $15/MTok output
        expected_cost = (1000 * 3 / 1_000_000) + (500 * 15 / 1_000_000)
        assert abs(cost - expected_cost) < 0.000001

    def test_calculate_cost_for_unknown_model_uses_default(self):
        """Test cost calculation uses default pricing for unknown models."""
        service = UnifiedOptimizationService(
            anthropic_api_key="sk-test-key",
            db_session=MagicMock(),
        )

        cost = service._calculate_cost(
            input_tokens=1000,
            output_tokens=500,
            model="unknown-model"
        )

        # Should use default pricing without crashing
        assert cost > 0
