"""
集成测试 01: 登录功能

测试 Playwright Provider 的 WordPress 登录功能
"""

import pytest


@pytest.mark.asyncio
@pytest.mark.integration
async def test_login_success(playwright_provider, test_credentials):
    """测试成功登录 WordPress"""

    # 执行登录
    result = await playwright_provider.login(
        "http://localhost:8000",
        test_credentials
    )

    # 验证登录成功
    assert result is True, "登录应该成功"

    # 验证当前 URL 包含 wp-admin
    assert "wp-admin" in playwright_provider.page.url, "应该跳转到 WordPress 后台"
    assert "wp-login.php" not in playwright_provider.page.url, "不应该停留在登录页面"

    # 截图保存
    await playwright_provider.take_screenshot("integration_test_login_success", "登录成功")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_login_failure_wrong_password(playwright_provider):
    """测试错误密码登录失败"""
    from src.providers.base import LoginError
    from src.models import WordPressCredentials

    wrong_credentials = WordPressCredentials(
        username="admin",
        password="wrong_password_123456"
    )

    # 执行登录，期待失败
    with pytest.raises(LoginError) as exc_info:
        await playwright_provider.login(
            "http://localhost:8000",
            wrong_credentials
        )

    # 验证错误消息
    assert "登录失败" in str(exc_info.value)

    # 截图保存错误状态
    await playwright_provider.take_screenshot("integration_test_login_failure", "登录失败")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_login_page_elements_visible(playwright_provider):
    """测试登录页面元素可见性"""

    # 导航到登录页面
    await playwright_provider.page.goto("http://localhost:8000/wp-admin", wait_until='networkidle')

    # 检查关键元素是否可见
    username_input = await playwright_provider.page.query_selector("#user_login")
    password_input = await playwright_provider.page.query_selector("#user_pass")
    submit_button = await playwright_provider.page.query_selector("#wp-submit")

    assert username_input is not None, "用户名输入框应该存在"
    assert password_input is not None, "密码输入框应该存在"
    assert submit_button is not None, "提交按钮应该存在"

    # 验证元素可见
    assert await username_input.is_visible(), "用户名输入框应该可见"
    assert await password_input.is_visible(), "密码输入框应该可见"
    assert await submit_button.is_visible(), "提交按钮应该可见"
