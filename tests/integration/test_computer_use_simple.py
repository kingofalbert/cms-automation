"""
Computer Use Provider 简化集成测试

使用 Mock 测试关键功能，避免实际 API 调用
"""

import pytest
from unittest.mock import patch, AsyncMock
from pathlib import Path
import tempfile

from src.providers.computer_use_provider import ComputerUseProvider
from src.config.computer_use_loader import load_instruction_templates
from src.models import (
    Article,
    ImageAsset,
    ArticleMetadata,
    SEOData,
    WordPressCredentials
)


@pytest.fixture
def provider(mock_api_key="test-key", instructions=None):
    """创建测试 Provider"""
    if instructions is None:
        instructions = load_instruction_templates()
    return ComputerUseProvider(
        api_key=mock_api_key,
        instructions=instructions
    )


@pytest.fixture
async def initialized_provider():
    """创建并初始化 Provider"""
    instructions = load_instruction_templates()
    provider = ComputerUseProvider(
        api_key="test-key",
        instructions=instructions
    )
    await provider.initialize()
    return provider


@pytest.mark.asyncio
class TestBasicFunctionality:
    """测试基本功能"""

    async def test_initialization(self):
        """测试初始化"""
        instructions = load_instruction_templates()
        provider = ComputerUseProvider(
            api_key="test-key",
            instructions=instructions
        )
        
        await provider.initialize()
        
        assert provider.client is not None
        assert provider.session is not None
        assert provider.session.screenshot_count == 0

    async def test_login_with_mock(self, initialized_provider):
        """测试登录（使用 Mock）"""
        provider = initialized_provider
        
        async def mock_execute(instruction, expect_screenshot=True):
            # 简单返回成功标志
            if "驗證" in instruction or "確認" in instruction:
                return {"content": "成功，wp-admin", "screenshot": None}
            return {"content": "操作完成", "screenshot": None}
        
        with patch.object(provider, '_execute_instruction', new=mock_execute):
            credentials = WordPressCredentials(
                username="test",
                password="test123456"
            )
            
            result = await provider.login(
                "https://example.com",
                credentials
            )
            
            assert result is True

    async def test_screenshot_tracking(self, initialized_provider):
        """测试截图追踪"""
        provider = initialized_provider
        
        initial_count = provider.session.screenshot_count
        
        await provider.take_screenshot("test", "测试")
        
        assert provider.session.screenshot_count == initial_count + 1


@pytest.mark.asyncio
class TestInstructionRendering:
    """测试指令渲染"""

    async def test_login_instruction_rendering(self):
        """测试登录指令渲染"""
        instructions = load_instruction_templates()
        
        result = instructions.get(
            'login_to_wordpress',
            username='testuser',
            password='testpass'
        )
        
        assert 'testuser' in result
        assert 'testpass' in result
        assert '使用者名稱' in result or '用户名' in result

    async def test_fill_title_rendering(self):
        """测试标题填写指令渲染"""
        instructions = load_instruction_templates()
        
        result = instructions.get(
            'fill_title',
            value='测试标题'
        )
        
        assert '测试标题' in result

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
