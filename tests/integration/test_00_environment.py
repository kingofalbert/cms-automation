"""
集成测试 00: 环境验证

验证测试环境是否正确配置
"""

import pytest
import requests


@pytest.mark.integration
def test_wordpress_accessible():
    """测试 WordPress 是否可访问"""
    try:
        response = requests.get("http://localhost:8000", timeout=5)
        assert response.status_code in [200, 302], \
            f"WordPress 应该可访问，状态码: {response.status_code}"
    except requests.exceptions.ConnectionError:
        pytest.fail("无法连接到 WordPress。请先运行: ./tests/run_integration_tests.sh")


@pytest.mark.integration
def test_wordpress_admin_accessible():
    """测试 WordPress 后台是否可访问"""
    try:
        response = requests.get("http://localhost:8000/wp-admin", timeout=5, allow_redirects=True)
        assert response.status_code in [200, 302], \
            f"WordPress 后台应该可访问，状态码: {response.status_code}"
        assert "wp-login" in response.url or "wp-admin" in response.url, \
            "应该跳转到登录页或后台"
    except requests.exceptions.ConnectionError:
        pytest.fail("无法连接到 WordPress 后台")


@pytest.mark.integration
def test_mysql_accessible():
    """测试 MySQL 是否可访问"""
    import socket

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex(('localhost', 3307))
        sock.close()

        assert result == 0, "MySQL 应该在端口 3307 上可访问"
    except Exception as e:
        pytest.fail(f"无法连接到 MySQL: {e}")


@pytest.mark.integration
def test_docker_containers_running():
    """测试 Docker 容器是否正在运行"""
    import subprocess

    try:
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=cms-test", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
            timeout=5
        )

        containers = result.stdout.strip().split('\n')
        containers = [c for c in containers if c]  # 移除空行

        assert len(containers) >= 2, \
            f"应该至少有 2 个测试容器运行（WordPress + MySQL），实际: {len(containers)}"

        # 检查容器名称
        expected_containers = ['cms-test-wordpress', 'cms-test-mysql']
        for expected in expected_containers:
            assert any(expected in c for c in containers), \
                f"容器 {expected} 应该在运行"

    except FileNotFoundError:
        pytest.skip("Docker 命令不可用")
    except subprocess.TimeoutExpired:
        pytest.fail("Docker 命令执行超时")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_playwright_can_navigate():
    """测试 Playwright 可以导航到 WordPress"""
    from src.providers.playwright_provider import PlaywrightProvider

    provider = PlaywrightProvider()

    try:
        await provider.initialize()
        await provider.page.goto("http://localhost:8000", wait_until='domcontentloaded')

        # 验证页面标题
        title = await provider.page.title()
        assert len(title) > 0, "页面应该有标题"

        print(f"\n✓ Playwright 成功访问 WordPress")
        print(f"  页面标题: {title}")

    finally:
        await provider.cleanup()
