"""
集成测试 02: 文章创建功能

测试 Playwright Provider 的文章创建功能
"""

import pytest


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_article_basic(
    playwright_provider,
    test_credentials,
    test_article,
    test_metadata
):
    """测试基本的文章创建功能"""

    # 先登录
    await playwright_provider.login("http://localhost:8000", test_credentials)

    # 创建文章
    result = await playwright_provider.create_article(test_article, test_metadata)

    # 验证结果
    assert result is True, "文章创建应该成功"

    # 验证页面 URL 包含 post-new.php 或 post.php
    current_url = playwright_provider.page.url
    assert ("post-new.php" in current_url or "post.php" in current_url), \
        f"应该在文章编辑页面，当前 URL: {current_url}"

    # 截图保存
    await playwright_provider.take_screenshot(
        "integration_test_article_created",
        "文章创建完成"
    )


@pytest.mark.asyncio
@pytest.mark.integration
async def test_article_title_filled(
    playwright_provider,
    test_credentials,
    test_article,
    test_metadata
):
    """测试文章标题是否正确填写"""

    # 登录并创建文章
    await playwright_provider.login("http://localhost:8000", test_credentials)
    await playwright_provider.create_article(test_article, test_metadata)

    # 获取标题输入框的值
    title_input = await playwright_provider.page.query_selector("#title")
    assert title_input is not None, "标题输入框应该存在"

    title_value = await title_input.input_value()
    assert title_value == test_article.title, \
        f"标题应该正确填写，期望: {test_article.title}, 实际: {title_value}"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_article_content_filled(
    playwright_provider,
    test_credentials,
    test_article,
    test_metadata
):
    """测试文章内容是否正确填写"""

    # 登录并创建文章
    await playwright_provider.login("http://localhost:8000", test_credentials)
    await playwright_provider.create_article(test_article, test_metadata)

    # 获取文本编辑器的内容
    content_textarea = await playwright_provider.page.query_selector("#content")
    assert content_textarea is not None, "内容编辑器应该存在"

    content_value = await content_textarea.input_value()
    assert len(content_value) > 0, "内容应该已填写"
    assert "测试文章第一段落" in content_value, "内容应该包含测试文本"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_article_categories_set(
    playwright_provider,
    test_credentials,
    test_article,
    test_metadata
):
    """测试文章分类是否正确设置"""

    # 登录并创建文章
    await playwright_provider.login("http://localhost:8000", test_credentials)
    await playwright_provider.create_article(test_article, test_metadata)

    # 等待分类面板加载
    await playwright_provider.page.wait_for_selector("#categorychecklist", timeout=5000)

    # 检查"技术"分类是否被勾选
    category_checklist = await playwright_provider.page.query_selector("#categorychecklist")
    assert category_checklist is not None, "分类列表应该存在"

    # 查找包含"技术"的标签
    labels = await category_checklist.query_selector_all("label")
    technology_found = False

    for label in labels:
        text = await label.text_content()
        if "技术" in text:
            # 检查对应的复选框是否被选中
            checkbox = await label.query_selector("input[type='checkbox']")
            if checkbox:
                is_checked = await checkbox.is_checked()
                technology_found = is_checked
                break

    assert technology_found, "分类'技术'应该被勾选"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_article_tags_added(
    playwright_provider,
    test_credentials,
    test_article,
    test_metadata
):
    """测试文章标签是否正确添加"""

    # 登录并创建文章
    await playwright_provider.login("http://localhost:8000", test_credentials)
    await playwright_provider.create_article(test_article, test_metadata)

    # 等待标签列表加载
    await playwright_provider.page.wait_for_selector(".tagchecklist", timeout=5000)

    # 获取已添加的标签列表
    tag_list = await playwright_provider.page.query_selector(".tagchecklist")
    assert tag_list is not None, "标签列表应该存在"

    tag_list_text = await tag_list.text_content()

    # 验证测试标签是否已添加
    for tag in test_metadata.tags:
        assert tag in tag_list_text, f"标签'{tag}'应该已添加"

    # 截图保存
    await playwright_provider.take_screenshot(
        "integration_test_article_with_tags",
        "文章包含标签"
    )
