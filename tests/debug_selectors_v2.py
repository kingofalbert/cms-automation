"""
调试脚本 v2：测试正确的菜单导航流程
"""

import asyncio
from playwright.async_api import async_playwright


async def test_navigation():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()

        try:
            print("1. 登录...")
            await page.goto("http://localhost:8001/wp-login.php")
            await page.fill("#user_login", "admin")
            await page.fill("#user_pass", "password")
            await page.click("#wp-submit")
            await page.wait_for_load_state('networkidle')
            print(f"   ✅ 登录成功: {page.url}")

            # 方法 1：先悬停展开菜单，再点击
            print("\n2. 方法 1 - 悬停展开菜单...")
            try:
                # 悬停在 Posts 菜单上
                await page.hover('#menu-posts')
                await asyncio.sleep(0.5)

                # 点击 Add New
                await page.click('a[href="post-new.php"]', timeout=10000)
                await page.wait_for_load_state('networkidle')
                print(f"   ✅ 成功: {page.url}")

                if 'post-new.php' in page.url:
                    print("   ✅ 方法 1 成功!")
                    return 'a[href="post-new.php"]', "先 hover #menu-posts，再点击"
            except Exception as e:
                print(f"   ❌ 方法 1 失败: {e}")

            # 方法 2：直接访问 URL
            print("\n3. 方法 2 - 直接访问 URL...")
            try:
                await page.goto("http://localhost:8001/wp-admin/post-new.php")
                await page.wait_for_load_state('networkidle')
                print(f"   ✅ 成功: {page.url}")

                if 'post-new.php' in page.url:
                    print("   ✅ 方法 2 成功!")
                    return None, "直接 goto URL"
            except Exception as e:
                print(f"   ❌ 方法 2 失败: {e}")

            # 方法 3：使用更具体的选择器
            print("\n4. 方法 3 - 使用子菜单选择器...")
            try:
                await page.goto("http://localhost:8001/wp-admin/")
                await page.wait_for_load_state('networkidle')

                # 点击 Posts 菜单项本身
                await page.click('#menu-posts a.wp-has-submenu')
                await asyncio.sleep(0.5)

                # 然后点击 Add New
                await page.click('#menu-posts .wp-submenu a[href="post-new.php"]', timeout=10000)
                await page.wait_for_load_state('networkidle')
                print(f"   ✅ 成功: {page.url}")

                if 'post-new.php' in page.url:
                    print("   ✅ 方法 3 成功!")
                    return '#menu-posts .wp-submenu a[href="post-new.php"]', "先点击主菜单展开"
            except Exception as e:
                print(f"   ❌ 方法 3 失败: {e}")

        finally:
            await browser.close()

        return None, "所有方法都失败"


if __name__ == "__main__":
    selector, method = asyncio.run(test_navigation())
    print("\n" + "=" * 60)
    print("结果:")
    print("=" * 60)
    if selector:
        print(f"推荐选择器: {selector}")
        print(f"使用方法: {method}")
    else:
        print(f"推荐方法: {method}")
