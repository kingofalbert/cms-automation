"""
Integration Tests Configuration

配置集成测试的 fixtures 和设置
"""

import pytest
import asyncio


def pytest_configure(config):
    """配置 pytest markers"""
    config.addinivalue_line(
        "markers", "integration: 集成测试标记（需要真实 WordPress 环境）"
    )
    config.addinivalue_line(
        "markers", "validator: 选择器验证测试标记"
    )
    config.addinivalue_line(
        "markers", "performance: 性能测试标记"
    )
    config.addinivalue_line(
        "markers", "slow: 慢速测试标记（运行时间较长）"
    )


@pytest.fixture(scope="session")
def event_loop():
    """创建 event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
def setup_test_environment():
    """在每个测试前设置环境"""
    # 可以在这里添加测试前的设置
    yield
    # 可以在这里添加测试后的清理
