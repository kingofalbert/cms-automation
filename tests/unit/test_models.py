"""
Unit Tests for Core Data Models

Tests all validation logic and data model behavior.
"""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
from pydantic import ValidationError

from src.models import (
    SEOData,
    Article,
    ImageAsset,
    ArticleMetadata,
    WordPressCredentials,
    PublishingContext,
    PublishResult
)


class TestSEOData:
    """测试 SEOData 模型"""

    def test_valid_seo_data(self):
        """测试有效的 SEO 数据"""
        seo = SEOData(
            focus_keyword="测试关键字",
            meta_title="这是一个非常详细且完整符合长度要求的搜索引擎优化标题文本内容示例，字符数量必须精确控制在五十到六十个字符之间范围内",
            meta_description="这是一个完整符合搜索引擎优化最佳实践严格要求的网页元描述文本内容详细示例信息数据资料材料。本描述文本非常详细地说明了文章页面的核心主题内容和实际价值作用效果，能够帮助各大搜索引擎系统准确理解和索引页面主题内容，同时有效吸引目标用户主动点击访问浏览查看阅读使用网站系统平台产品服务功能特性优势亮点价值意义。"
        )

        assert seo.focus_keyword == "测试关键字"
        assert len(seo.meta_title) >= 50
        assert len(seo.meta_title) <= 60
        assert len(seo.meta_description) >= 150
        assert len(seo.meta_description) <= 160

    def test_meta_title_too_short(self):
        """测试 Meta Title 太短"""
        with pytest.raises(ValidationError) as exc_info:
            SEOData(
                focus_keyword="测试",
                meta_title="太短的标题",  # 远少于 50 个字符
                meta_description="这是一个完整符合搜索引擎优化最佳实践严格要求的网页元描述文本内容详细示例信息数据资料材料。本描述文本非常详细地说明了文章页面的核心主题内容和实际价值作用效果，能够帮助各大搜索引擎系统准确理解和索引页面主题内容，同时有效吸引目标用户主动点击访问浏览查看阅读使用网站系统平台产品服务功能特性优势亮点价值意义。"
            )

        assert "太短" in str(exc_info.value)

    def test_meta_title_too_long(self):
        """测试 Meta Title 太长"""
        with pytest.raises(ValidationError) as exc_info:
            SEOData(
                focus_keyword="测试",
                meta_title="这是一个非常非常详细冗长复杂的搜索引擎优化标题文本内容示例信息数据，显然字符数量已经明显远远超过了规定的六十个字符的严格上限限制要求标准规范条件",
                meta_description="这是一个完整符合搜索引擎优化最佳实践严格要求的网页元描述文本内容详细示例信息数据资料材料。本描述文本非常详细地说明了文章页面的核心主题内容和实际价值作用效果，能够帮助各大搜索引擎系统准确理解和索引页面主题内容，同时有效吸引目标用户主动点击访问浏览查看阅读使用网站系统平台产品服务功能特性优势亮点价值意义。"
            )

        # Pydantic base validator runs first, producing English error message
        assert ("太长" in str(exc_info.value) or "at most 60 characters" in str(exc_info.value))

    def test_meta_description_validation(self):
        """测试 Meta Description 验证"""
        # 太短
        with pytest.raises(ValidationError) as exc_info:
            SEOData(
                focus_keyword="测试",
                meta_title="这是一个非常详细且完整符合长度要求的搜索引擎优化标题文本内容示例，字符数量必须精确控制在五十到六十个字符之间范围内",
                meta_description="太短了"
            )
        assert "太短" in str(exc_info.value)

        # 太长
        with pytest.raises(ValidationError) as exc_info:
            SEOData(
                focus_keyword="测试",
                meta_title="这是一个非常详细且完整符合长度要求的搜索引擎优化标题文本内容示例，字符数量必须精确控制在五十到六十个字符之间范围内",
                meta_description="这是一个非常非常非常详细冗长复杂的网页元描述文本内容示例信息数据资料。本描述文本非常非常详细地说明了文章页面的核心主题内容和实际应用价值意义作用效果影响，能够帮助各大搜索引擎系统准确理解和索引分析页面主题内容信息数据资料，同时有效吸引目标用户主动积极点击访问浏览阅读查看。描述文本长度显然已经明显远远超过了规定的一百六十个字符的严格上限限制要求标准规范条件，这样的超长描述在搜索结果页面中会被强制截断处理，严重影响用户的浏览体验和实际点击转化率效果。"
            )
        # Pydantic base validator runs first, producing English error message
        assert ("太长" in str(exc_info.value) or "at most 160 characters" in str(exc_info.value))


class TestArticle:
    """测试 Article 模型"""

    @pytest.fixture
    def valid_seo_data(self):
        """有效的 SEO 数据 fixture"""
        return SEOData(
            focus_keyword="测试关键字",
            meta_title="这是一个非常详细且完整符合长度要求的搜索引擎优化标题文本内容示例，字符数量必须精确控制在五十到六十个字符之间范围内",
            meta_description="这是一个完整符合搜索引擎优化最佳实践严格要求的网页元描述文本内容详细示例信息数据资料材料。本描述文本非常详细地说明了文章页面的核心主题内容和实际价值作用效果，能够帮助各大搜索引擎系统准确理解和索引页面主题内容，同时有效吸引目标用户主动点击访问浏览查看阅读使用网站系统平台产品服务功能特性优势亮点价值意义。"
        )

    def test_valid_article(self, valid_seo_data):
        """测试有效的文章数据"""
        article = Article(
            id=1,
            title="这是一个测试文章标题示例",
            content_html="<p>这是测试文章的内容。</p>" * 10,  # 确保足够长
            excerpt="这是文章摘要",
            seo=valid_seo_data
        )

        assert article.id == 1
        assert article.title == "这是一个测试文章标题示例"
        assert "<p>" in article.content_html

    def test_html_sanitization(self, valid_seo_data):
        """测试 HTML 清理"""
        dangerous_html = """
        <p>正常内容</p>
        <script>alert('XSS')</script>
        <p onclick="malicious()">带事件的内容</p>
        <iframe src="evil.com"></iframe>
        """ + "<p>更多内容</p>" * 10

        article = Article(
            id=1,
            title="这是一个测试文章标题示例",
            content_html=dangerous_html,
            seo=valid_seo_data
        )

        # 验证危险标签被移除
        assert "<script>" not in article.content_html
        assert "<iframe>" not in article.content_html
        assert "onclick=" not in article.content_html

        # 正常内容保留
        assert "<p>正常内容</p>" in article.content_html

    def test_content_too_short(self, valid_seo_data):
        """测试内容太短"""
        with pytest.raises(ValidationError) as exc_info:
            Article(
                id=1,
                title="测试文章",
                content_html="<p>太短</p>",  # 去除 HTML 后不足 50 字符
                seo=valid_seo_data
            )

        assert "太短" in str(exc_info.value)

    def test_title_validation(self, valid_seo_data):
        """测试标题验证"""
        # 空标题
        with pytest.raises(ValidationError):
            Article(
                id=1,
                title="   ",  # 只有空格
                content_html="<p>内容</p>" * 20,
                seo=valid_seo_data
            )

        # 太短的标题
        with pytest.raises(ValidationError):
            Article(
                id=1,
                title="短",  # 少于 10 个字符
                content_html="<p>内容</p>" * 20,
                seo=valid_seo_data
            )


class TestImageAsset:
    """测试 ImageAsset 模型"""

    @pytest.fixture
    def test_image_path(self, tmp_path):
        """创建测试图片文件"""
        image_file = tmp_path / "test_image.jpg"
        image_file.write_bytes(b"fake image content")
        return str(image_file)

    def test_valid_image_asset(self, test_image_path):
        """测试有效的图片资源"""
        image = ImageAsset(
            file_path=test_image_path,
            alt_text="测试图片替代文字",
            title="测试图片",
            caption="这是测试图片的说明",
            keywords=["测试", "图片"],
            photographer="测试摄影师"
        )

        assert image.alt_text == "测试图片替代文字"
        assert len(image.keywords) == 2
        assert Path(image.file_path).exists()

    def test_file_not_found(self):
        """测试文件不存在"""
        with pytest.raises(ValidationError) as exc_info:
            ImageAsset(
                file_path="/nonexistent/path/image.jpg",
                alt_text="测试图片",
                title="测试"
            )

        assert "不存在" in str(exc_info.value)

    def test_invalid_file_extension(self, tmp_path):
        """测试不支持的文件格式"""
        invalid_file = tmp_path / "test.txt"
        invalid_file.write_text("not an image")

        with pytest.raises(ValidationError) as exc_info:
            ImageAsset(
                file_path=str(invalid_file),
                alt_text="测试",
                title="测试"
            )

        assert "不支持的图片格式" in str(exc_info.value)

    def test_keywords_deduplication(self, test_image_path):
        """测试关键字去重"""
        image = ImageAsset(
            file_path=test_image_path,
            alt_text="测试示例图片",
            title="测试",
            keywords=["测试", "图片", "测试", "图片"]  # 有重复
        )

        # 重复项应该被移除
        assert len(image.keywords) == 2
        assert set(image.keywords) == {"测试", "图片"}


class TestArticleMetadata:
    """测试 ArticleMetadata 模型"""

    def test_immediate_publish(self):
        """测试立即发布"""
        metadata = ArticleMetadata(
            tags=["标签1", "标签2"],
            categories=["分类1"],
            publish_immediately=True
        )

        assert metadata.publish_immediately is True
        assert metadata.publish_date is None
        assert metadata.status == "draft"

    def test_scheduled_publish(self):
        """测试排程发布"""
        future_date = datetime.now() + timedelta(days=1)

        metadata = ArticleMetadata(
            tags=["标签1"],
            categories=["分类1"],
            publish_immediately=False,
            publish_date=future_date,
            status="scheduled"
        )

        assert metadata.publish_immediately is False
        assert metadata.publish_date is not None

    def test_scheduled_without_date(self):
        """测试排程发布但未设置日期"""
        with pytest.raises(ValidationError) as exc_info:
            ArticleMetadata(
                tags=["标签1"],
                categories=["分类1"],
                publish_immediately=False,
                # 缺少 publish_date
                status="scheduled"
            )

        assert "必须设置 publish_date" in str(exc_info.value)

    def test_immediate_with_date(self):
        """测试立即发布但设置了日期"""
        future_date = datetime.now() + timedelta(days=1)

        with pytest.raises(ValidationError) as exc_info:
            ArticleMetadata(
                tags=["标签1"],
                categories=["分类1"],
                publish_immediately=True,
                publish_date=future_date  # 不应该设置
            )

        assert "不应设置 publish_date" in str(exc_info.value)

    def test_past_publish_date(self):
        """测试过去的发布日期"""
        past_date = datetime.now() - timedelta(days=1)

        with pytest.raises(ValidationError) as exc_info:
            ArticleMetadata(
                tags=["标签1"],
                categories=["分类1"],
                publish_immediately=False,
                publish_date=past_date
            )

        assert "不能是过去的时间" in str(exc_info.value)

    def test_tags_deduplication(self):
        """测试标签去重"""
        metadata = ArticleMetadata(
            tags=["标签1", "标签2", "标签1", "  ", "标签3"],  # 有重复和空白
            categories=["分类1"]
        )

        # 应该去重并移除空白
        assert len(metadata.tags) == 3
        assert "标签1" in metadata.tags
        assert "" not in metadata.tags


class TestWordPressCredentials:
    """测试 WordPressCredentials 模型"""

    def test_valid_credentials(self):
        """测试有效的凭证"""
        creds = WordPressCredentials(
            username="admin",
            password="secure_password_123"
        )

        assert creds.username == "admin"
        assert creds.password == "secure_password_123"

    def test_username_with_special_chars(self):
        """测试包含特殊字符的用户名"""
        # 有效的特殊字符
        creds = WordPressCredentials(
            username="user@example.com",
            password="password123"
        )
        assert creds.username == "user@example.com"

        # 无效的特殊字符
        with pytest.raises(ValidationError) as exc_info:
            WordPressCredentials(
                username="user#invalid",
                password="password123"
            )

        assert "只能包含" in str(exc_info.value)

    def test_short_password(self):
        """测试密码太短"""
        with pytest.raises(ValidationError):
            WordPressCredentials(
                username="admin",
                password="short"  # 少于 8 个字符
            )


class TestPublishingContext:
    """测试 PublishingContext 模型"""

    @pytest.fixture
    def sample_context_data(self, tmp_path):
        """示例上下文数据"""
        # 创建测试图片
        image_file = tmp_path / "test.jpg"
        image_file.write_bytes(b"fake image")

        return {
            "task_id": "test-task-123",
            "article": Article(
                id=1,
                title="这是一个测试文章标题示例",
                content_html="<p>测试内容</p>" * 20,
                seo=SEOData(
                    focus_keyword="测试关键字",
                    meta_title="这是一个非常详细且完整符合长度要求的搜索引擎优化标题文本内容示例，字符数量必须精确控制在五十到六十个字符之间范围内",
                    meta_description="这是一个完整符合搜索引擎优化最佳实践严格要求的网页元描述文本内容详细示例信息数据资料材料。本描述文本非常详细地说明了文章页面的核心主题内容和实际价值作用效果，能够帮助各大搜索引擎系统准确理解和索引页面主题内容，同时有效吸引目标用户主动点击访问浏览查看阅读使用网站系统平台产品服务功能特性优势亮点价值意义。"
                )
            ),
            "images": [
                ImageAsset(
                    file_path=str(image_file),
                    alt_text="测试示例图片",
                    title="测试"
                )
            ],
            "metadata": ArticleMetadata(
                tags=["测试"],
                categories=["技术"]
            ),
            "wordpress_url": "https://example.com",
            "credentials": WordPressCredentials(
                username="admin",
                password="password123"
            )
        }

    def test_valid_context(self, sample_context_data):
        """测试有效的上下文"""
        context = PublishingContext(**sample_context_data)

        assert context.task_id == "test-task-123"
        assert context.wordpress_url == "https://example.com"
        assert len(context.images) == 1

    def test_url_validation(self, sample_context_data):
        """测试 URL 验证"""
        # 无效的 URL
        sample_context_data["wordpress_url"] = "not-a-url"

        with pytest.raises(ValidationError) as exc_info:
            PublishingContext(**sample_context_data)

        assert "必须以 http" in str(exc_info.value)

    def test_url_trailing_slash_removal(self, sample_context_data):
        """测试 URL 末尾斜杠移除"""
        sample_context_data["wordpress_url"] = "https://example.com/"

        context = PublishingContext(**sample_context_data)

        # 末尾斜杠应该被移除
        assert context.wordpress_url == "https://example.com"


class TestPublishResult:
    """测试 PublishResult 模型"""

    def test_successful_result(self):
        """测试成功的结果"""
        result = PublishResult(
            success=True,
            task_id="test-123",
            url="https://example.com/article",
            duration_seconds=120.5,
            provider_used="playwright"
        )

        assert result.success is True
        assert result.error is None
        assert result.duration_seconds == 120.5

    def test_failed_result(self):
        """测试失败的结果"""
        result = PublishResult(
            success=False,
            task_id="test-123",
            error="发布失败: 元素未找到",
            duration_seconds=30.0,
            provider_used="playwright",
            retry_count=3
        )

        assert result.success is False
        assert result.url is None
        assert result.error is not None
        assert result.retry_count == 3

    def test_fallback_triggered(self):
        """测试降级触发"""
        result = PublishResult(
            success=True,
            task_id="test-123",
            url="https://example.com/article",
            provider_used="computer_use",
            fallback_triggered=True,
            retry_count=3
        )

        assert result.fallback_triggered is True
        assert result.provider_used == "computer_use"
