"""
调试脚本：检查 WordPress 实际的选择器
使用方法：python tests/debug_selectors.py
"""

import asyncio
from playwright.async_api import async_playwright


async def debug_wordpress_selectors():
    """检查 WordPress 后台的实际选择器"""

    async with async_playwright() as p:
        # 启动浏览器（非无头模式，可以看到界面）
        browser = await p.chromium.launch(headless=False, slow_mo=1000)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()

        try:
            print("=" * 60)
            print("WordPress 选择器调试工具")
            print("=" * 60)

            # 1. 访问登录页面
            print("\n1. 访问登录页面...")
            await page.goto("http://localhost:8001/wp-login.php")
            await page.wait_for_load_state('networkidle')

            # 2. 登录
            print("2. 登录...")
            await page.fill("#user_login", "admin")
            await page.fill("#user_pass", "password")
            await page.click("#wp-submit")
            await page.wait_for_load_state('networkidle')

            print("   ✅ 登录成功")
            print(f"   当前 URL: {page.url}")

            # 3. 检查侧边栏导航
            print("\n3. 检查侧边栏导航...")

            # 尝试多种可能的"新建文章"选择器
            possible_selectors = [
                'a[href="post-new.php"]',
                '#menu-posts a[href="post-new.php"]',
                'a.wp-first-item[href="post-new.php"]',
                '#menu-posts li.wp-first-item a',
                'a:has-text("写文章")',
                'a:has-text("新建文章")',
                'a:has-text("Add New")',
                '#menu-posts .wp-submenu a:first-child',
            ]

            print("\n   测试可能的选择器:")
            working_selector = None

            for selector in possible_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        text = await element.text_content()
                        href = await element.get_attribute('href')
                        is_visible = await element.is_visible()
                        print(f"   ✅ {selector}")
                        print(f"      文本: {text}")
                        print(f"      链接: {href}")
                        print(f"      可见: {is_visible}")
                        if is_visible and not working_selector:
                            working_selector = selector
                    else:
                        print(f"   ❌ {selector} - 未找到")
                except Exception as e:
                    print(f"   ❌ {selector} - 错误: {e}")

            # 4. 检查文章列表菜单
            print("\n4. 检查文章菜单...")
            posts_menu_selectors = [
                '#menu-posts',
                'a[href="edit.php"]',
                '#adminmenu .wp-menu-name:has-text("文章")',
                '#adminmenu .wp-menu-name:has-text("Posts")',
            ]

            for selector in posts_menu_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        print(f"   ✅ {selector} 存在")
                except Exception as e:
                    print(f"   ❌ {selector} - 错误: {e}")

            # 5. 尝试点击找到的工作选择器
            if working_selector:
                print(f"\n5. 尝试使用工作选择器: {working_selector}")
                await page.click(working_selector)
                await page.wait_for_load_state('networkidle')
                print(f"   ✅ 成功导航到: {page.url}")

                # 检查是否在新建文章页面
                if 'post-new.php' in page.url:
                    print("   ✅ 确认在新建文章页面")

                    # 检查编辑器选择器
                    print("\n6. 检查编辑器选择器...")

                    # 标题输入框
                    title_selector = "#title"
                    title_element = await page.query_selector(title_selector)
                    if title_element:
                        print(f"   ✅ 标题输入框: {title_selector}")
                    else:
                        print(f"   ❌ 标题输入框未找到")

                    # 内容编辑器
                    content_selectors = [
                        "#content_ifr",  # Classic Editor iframe
                        "#tinymce",      # TinyMCE 内部
                        "#content",      # 文本编辑器
                        ".editor-post-title",  # Gutenberg
                    ]

                    for selector in content_selectors:
                        try:
                            element = await page.query_selector(selector)
                            if element:
                                print(f"   ✅ 内容编辑器: {selector}")
                        except Exception as e:
                            print(f"   ❌ {selector} - 错误: {e}")
                else:
                    print(f"   ⚠️  不在新建文章页面: {page.url}")
            else:
                print("\n   ⚠️  未找到有效的选择器")

            # 6. 输出推荐的选择器配置
            print("\n" + "=" * 60)
            print("推荐的选择器配置:")
            print("=" * 60)
            if working_selector:
                print(f"""
navigation:
  new_post: "{working_selector}"
""")

            # 保持浏览器打开，方便手动检查
            print("\n浏览器将保持打开 60 秒，方便手动检查...")
            print("按 Ctrl+C 可以提前退出")
            await asyncio.sleep(60)

        except KeyboardInterrupt:
            print("\n\n用户中断")
        except Exception as e:
            print(f"\n错误: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await browser.close()
            print("\n浏览器已关闭")


if __name__ == "__main__":
    asyncio.run(debug_wordpress_selectors())
