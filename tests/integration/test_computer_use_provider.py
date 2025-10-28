"""
Computer Use Provider 集成测试

测试 Computer Use Provider 在模拟环境下的完整功能
使用 Mock 来避免实际调用 Anthropic API
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from pathlib import Path
import tempfile

from src.providers.computer_use_provider import ComputerUseProvider
from src.config.computer_use_loader import load_instruction_templates
from src.models import (
    Article,
    ImageAsset,
    ArticleMetadata,
    SEOData,
    WordPressCredentials,
    PublishingContext
)


@pytest.fixture
def mock_api_key():
    """模拟 API Key"""
    return "test-api-key-12345"


@pytest.fixture
def instruction_templates():
    """加载真实的指令模板"""
    return load_instruction_templates()


@pytest.fixture
def test_credentials():
    """测试凭证"""
    return WordPressCredentials(
        username="test_user",
        password="test_password_123"
    )


@pytest.fixture
def test_seo_data():
    """测试 SEO 数据"""
    return SEOData(
        focus_keyword="测试关键字",
        meta_title="这是一个测试的SEO标题用于Computer Use Provider集成测试验证功能",  # 50字符
        meta_description="这是一个测试的Meta描述用于验证Computer Use Provider的SEO配置功能是否正常工作。描述长度需要在一百五十到一百六十个字符之间所以这里添加足够的文字来满足长度要求确保验证通过。这样应该够了吧好的完成了",  # 150字符
        primary_keywords=["测试", "Computer Use", "自动化"],
        secondary_keywords=["WordPress", "发布", "SEO"]
    )


@pytest.fixture
def test_article(test_seo_data):
    """测试文章"""
    return Article(
        id=1,
        title="Computer Use 集成测试文章",
        content_html="""
<h2>测试标题</h2>
<p>这是测试内容的第一段。包含足够的文字来满足最小长度要求。</p>
<h3>子标题</h3>
<p>这是测试内容的第二段。继续添加更多文字。</p>
<ul>
    <li>列表项 1</li>
    <li>列表项 2</li>
    <li>列表项 3</li>
</ul>
        """,
        excerpt="这是测试文章的摘要",
        seo=test_seo_data
    )


@pytest.fixture
def test_metadata():
    """测试元数据"""
    return ArticleMetadata(
        tags=["测试", "自动化", "Computer Use"],
        categories=["技术", "教程"],
        publish_immediately=True,
        status="publish"
    )


@pytest.fixture
def test_image():
    """创建测试图片"""
    # 创建临时图片文件
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
        # 写入一些数据（实际测试中是图片数据）
        f.write(b'fake image data')
        temp_path = f.name

    image = ImageAsset(
        file_path=temp_path,
        alt_text="测试图片替代文字",
        title="测试图片",
        caption="这是测试图片的说明",
        keywords=["测试", "图片", "Computer Use"],
        photographer="测试摄影师",
        is_featured=True
    )

    yield image

    # 清理临时文件
    Path(temp_path).unlink(missing_ok=True)


@pytest.fixture
def mock_anthropic_response():
    """模拟 Anthropic API 响应"""
    def create_response(content_text="操作已完成", tool_calls=None):
        """创建模拟响应"""
        response = Mock()

        # 模拟文本内容
        text_block = Mock()
        text_block.text = content_text
        text_block.type = 'text'

        # 模拟工具调用
        blocks = [text_block]
        if tool_calls:
            for tool_call in tool_calls:
                tool_block = Mock()
                tool_block.type = 'tool_use'
                tool_block.output = tool_call
                blocks.append(tool_block)

        response.content = blocks

        # 模拟 Token 使用统计
        usage = Mock()
        usage.input_tokens = 100
        usage.output_tokens = 50
        response.usage = usage

        return response

    return create_response


@pytest.mark.asyncio
class TestComputerUseProviderInitialization:
    """测试 Provider 初始化"""

    async def test_provider_initialization(self, mock_api_key, instruction_templates):
        """测试 Provider 初始化"""
        provider = ComputerUseProvider(
            api_key=mock_api_key,
            instructions=instruction_templates,
            display_width=1920,
            display_height=1080
        )

        assert provider.api_key == mock_api_key
        assert provider.instructions == instruction_templates
        assert provider.display_width == 1920
        assert provider.display_height == 1080
        assert provider.client is None  # 未初始化时为 None

    async def test_provider_initialize(self, mock_api_key, instruction_templates):
        """测试 initialize 方法"""
        provider = ComputerUseProvider(
            api_key=mock_api_key,
            instructions=instruction_templates
        )

        # 执行初始化
        await provider.initialize()

        assert provider.client is not None
        assert provider.session is not None
        assert provider.session.session_id.startswith('cu-')
        assert len(provider.session.conversation_history) == 0
        assert provider.session.screenshot_count == 0
        assert provider.session.total_tokens_used == 0

    async def test_provider_cleanup(self, mock_api_key, instruction_templates):
        """测试 cleanup 方法"""
        provider = ComputerUseProvider(
            api_key=mock_api_key,
            instructions=instruction_templates
        )

        await provider.initialize()
        session_id = provider.session.session_id

        # 执行清理
        await provider.cleanup()

        # 验证会话仍然存在（cleanup 不会删除会话）
        assert provider.session.session_id == session_id


@pytest.mark.asyncio
class TestComputerUseProviderLogin:
    """测试登录功能"""

    async def test_login_success(
        self,
        mock_api_key,
        instruction_templates,
        test_credentials
    ):
        """测试登录成功"""
        provider = ComputerUseProvider(
            api_key=mock_api_key,
            instructions=instruction_templates
        )

        await provider.initialize()

        # Mock _execute_instruction 方法
        call_count = 0
        async def mock_execute(instruction, expect_screenshot=True):
            nonlocal call_count
            call_count += 1
            if call_count == 3:  # 第三次调用是验证
                return {"content": "成功进入 wp-admin 后台", "screenshot": None}
            return {"content": "操作完成", "screenshot": None}

        with patch.object(provider, '_execute_instruction', new=mock_execute):
            # 执行登录
            result = await provider.login(
                wordpress_url="https://example.com",
                credentials=test_credentials
            )

            assert result is True
            assert provider.session.current_url == "https://example.com/wp-admin"
            assert call_count == 3

    async def test_login_failure(
        self,
        mock_api_key,
        instruction_templates,
        test_credentials
    ):
        """测试登录失败"""
        provider = ComputerUseProvider(
            api_key=mock_api_key,
            instructions=instruction_templates
        )

        await provider.initialize()

        # Mock _execute_instruction 方法 - 验证失败
        call_count = 0
        async def mock_execute(instruction, expect_screenshot=True):
            nonlocal call_count
            call_count += 1
            if call_count == 3:  # 第三次调用是验证，返回失败
                return {"content": "登录失败，仍在登录页面", "screenshot": None}
            return {"content": "操作完成", "screenshot": None}

        with patch.object(provider, '_execute_instruction', new=mock_execute):
            # 执行登录应该抛出异常
            from src.providers.base import LoginError
            with pytest.raises(LoginError):
                await provider.login(
                    wordpress_url="https://example.com",
                    credentials=test_credentials
                )


@pytest.mark.asyncio
class TestComputerUseProviderArticleCreation:
    """测试文章创建功能"""

    async def test_create_article_success(
        self,
        mock_api_key,
        instruction_templates,
        test_article,
        test_metadata,
        mock_anthropic_response
    ):
        """测试文章创建成功"""
        provider = ComputerUseProvider(
            api_key=mock_api_key,
            instructions=instruction_templates
        )

        await provider.initialize()

        # Mock Anthropic API 调用
        with patch.object(provider.client.messages, 'create') as mock_create:
            # 模拟文章创建流程的多次 API 调用
            mock_create.side_effect = [
                mock_anthropic_response("已导航到新增文章页面"),
                mock_anthropic_response("标题已填写"),
                mock_anthropic_response("内容已填写"),
                mock_anthropic_response("HTML 实体已清理"),
                # 标签添加
                *[mock_anthropic_response(f"标签 '{tag}' 已添加") for tag in test_metadata.tags],
                # 分类选择
                *[mock_anthropic_response(f"分类 '{cat}' 已选择") for cat in test_metadata.categories],
            ]

            # 执行文章创建
            result = await provider.create_article(test_article, test_metadata)

            assert result is True
            # 验证 API 调用次数：导航(1) + 标题(1) + 内容(1) + 清理(1) + 标签(3) + 分类(2) = 9
            assert mock_create.call_count == 9


@pytest.mark.asyncio
class TestComputerUseProviderImageUpload:
    """测试图片上传功能"""

    async def test_upload_single_image(
        self,
        mock_api_key,
        instruction_templates,
        test_image,
        mock_anthropic_response
    ):
        """测试上传单张图片"""
        provider = ComputerUseProvider(
            api_key=mock_api_key,
            instructions=instruction_templates
        )

        await provider.initialize()

        # Mock Anthropic API 调用
        with patch.object(provider.client.messages, 'create') as mock_create:
            # 模拟图片上传流程
            mock_create.side_effect = [
                mock_anthropic_response("媒体库已打开"),
                mock_anthropic_response("文件上传中"),
                mock_anthropic_response("上传完成"),
                mock_anthropic_response("元数据已填写"),
            ]

            # 由于是特色图片，不会插入到内容
            result = await provider.upload_images([test_image])

            assert len(result) == 1
            assert mock_create.call_count == 4

    async def test_upload_multiple_images(
        self,
        mock_api_key,
        instruction_templates,
        mock_anthropic_response
    ):
        """测试上传多张图片"""
        # 创建多个测试图片
        temp_files = []
        images = []

        for i in range(3):
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
                f.write(b'fake image data')
                temp_files.append(f.name)

                images.append(ImageAsset(
                    file_path=f.name,
                    alt_text=f"测试图片 {i+1}",
                    title=f"图片 {i+1}",
                    caption=f"说明 {i+1}",
                    is_featured=(i == 0)
                ))

        try:
            provider = ComputerUseProvider(
                api_key=mock_api_key,
                instructions=instruction_templates
            )

            await provider.initialize()

            # Mock Anthropic API 调用
            with patch.object(provider.client.messages, 'create') as mock_create:
                # 每张图片需要 4-5 次 API 调用
                responses = []
                for i in range(3):
                    responses.extend([
                        mock_anthropic_response("媒体库已打开"),
                        mock_anthropic_response("文件上传中"),
                        mock_anthropic_response("上传完成"),
                        mock_anthropic_response("元数据已填写"),
                    ])
                    if i > 0:  # 非特色图片需要插入
                        responses.append(mock_anthropic_response("图片已插入"))

                mock_create.side_effect = responses

                # 执行上传
                result = await provider.upload_images(images)

                assert len(result) == 3

        finally:
            # 清理临时文件
            for temp_file in temp_files:
                Path(temp_file).unlink(missing_ok=True)


@pytest.mark.asyncio
class TestComputerUseProviderSEO:
    """测试 SEO 配置功能"""

    async def test_configure_seo_success(
        self,
        mock_api_key,
        instruction_templates,
        test_seo_data,
        mock_anthropic_response
    ):
        """测试 SEO 配置成功"""
        provider = ComputerUseProvider(
            api_key=mock_api_key,
            instructions=instruction_templates
        )

        await provider.initialize()

        # Mock Anthropic API 调用
        with patch.object(provider.client.messages, 'create') as mock_create:
            mock_create.side_effect = [
                mock_anthropic_response("SEO 区块已展开"),
                mock_anthropic_response("SEO 字段已配置完成")
            ]

            # 执行 SEO 配置
            result = await provider.configure_seo(test_seo_data)

            assert result is True
            assert mock_create.call_count == 2


@pytest.mark.asyncio
class TestComputerUseProviderPublish:
    """测试发布功能"""

    async def test_publish_immediately(
        self,
        mock_api_key,
        instruction_templates,
        test_metadata,
        mock_anthropic_response
    ):
        """测试立即发布"""
        provider = ComputerUseProvider(
            api_key=mock_api_key,
            instructions=instruction_templates
        )

        await provider.initialize()
        provider.session.current_url = "https://example.com/wp-admin"

        # Mock Anthropic API 调用
        with patch.object(provider.client.messages, 'create') as mock_create:
            mock_create.side_effect = [
                mock_anthropic_response("发布按钮已点击"),
                mock_anthropic_response("文章已成功发布")
            ]

            # 执行发布
            result = await provider.publish(test_metadata)

            assert result == "https://example.com/wp-admin"
            assert mock_create.call_count == 2


@pytest.mark.asyncio
class TestComputerUseProviderScreenshot:
    """测试截图功能"""

    async def test_take_screenshot(
        self,
        mock_api_key,
        instruction_templates
    ):
        """测试截图"""
        provider = ComputerUseProvider(
            api_key=mock_api_key,
            instructions=instruction_templates
        )

        await provider.initialize()

        # 执行截图
        screenshot_path = await provider.take_screenshot(
            name="test_screenshot",
            description="测试截图"
        )

        assert screenshot_path is not None
        assert "test_screenshot.png" in screenshot_path
        assert provider.session.screenshot_count == 1


@pytest.mark.asyncio
class TestComputerUseProviderTokenTracking:
    """测试 Token 追踪"""

    async def test_token_tracking(
        self,
        mock_api_key,
        instruction_templates,
        mock_anthropic_response
    ):
        """测试 Token 使用统计"""
        provider = ComputerUseProvider(
            api_key=mock_api_key,
            instructions=instruction_templates
        )

        await provider.initialize()

        initial_tokens = provider.session.total_tokens_used
        assert initial_tokens == 0

        # Mock API 调用
        with patch.object(provider.client.messages, 'create') as mock_create:
            # 每次调用使用 150 tokens (100 input + 50 output)
            mock_create.return_value = mock_anthropic_response("操作完成")

            # 执行几次指令
            for _ in range(3):
                await provider._execute_instruction("测试指令")

            # 验证 Token 统计
            assert provider.session.total_tokens_used == 450  # 3 * 150


@pytest.mark.asyncio
class TestComputerUseProviderErrorHandling:
    """测试错误处理"""

    async def test_api_error_handling(
        self,
        mock_api_key,
        instruction_templates
    ):
        """测试 API 错误处理"""
        provider = ComputerUseProvider(
            api_key=mock_api_key,
            instructions=instruction_templates
        )

        await provider.initialize()

        # Mock API 抛出异常
        with patch.object(provider.client.messages, 'create') as mock_create:
            mock_create.side_effect = Exception("API Error")

            # 执行指令应该抛出异常
            with pytest.raises(Exception):
                await provider._execute_instruction("测试指令")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
