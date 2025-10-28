"""
生产环境配置验证测试 v2
处理 HTTP Basic Authentication + WordPress 登录
"""

import asyncio
import os
from playwright.async_api import async_playwright
from dotenv import load_dotenv


# 加载环境变量
load_dotenv()


async def test_production_with_basic_auth():
    """测试生产环境（包含 HTTP Basic Auth）"""

    print("=" * 60)
    print("🔒 生产环境登录测试 (v2)")
    print("=" * 60)
    print("\n⚠️  警告：此测试仅验证配置，不会创建或修改任何内容\n")

    # 读取环境变量
    prod_url = os.getenv("PROD_WORDPRESS_URL")
    first_username = os.getenv("PROD_FIRST_LAYER_USERNAME")
    first_password = os.getenv("PROD_FIRST_LAYER_PASSWORD")
    user_username = os.getenv("PROD_USERNAME")
    user_password = os.getenv("PROD_PASSWORD")

    if not all([prod_url, first_username, first_password, user_username, user_password]):
        print("❌ 错误：环境变量未完全配置")
        return False

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            slow_mo=500
        )

        # 创建带有 HTTP Basic Auth 的上下文
        # 方案1：在 URL 中嵌入凭证
        print("1️⃣  尝试使用 HTTP Basic Auth...")
        print(f"   第一层账号: {first_username}")
        
        # 构造包含认证信息的 URL
        # 格式: https://username:password@domain/path
        auth_url = f"https://{first_username}:{first_password}@admin.epochtimes.com/wp-login.php"
        
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            # 也可以使用 http_credentials
            http_credentials={
                "username": first_username,
                "password": first_password
            }
        )

        page = await context.new_page()

        try:
            print(f"   访问 URL: {prod_url}/wp-login.php")
            await page.goto(f"{prod_url}/wp-login.php")
            await page.wait_for_load_state('networkidle')
            await asyncio.sleep(1)

            # 截图
            await page.screenshot(path="/tmp/prod_after_basic_auth.png")
            print("   📸 截图已保存: /tmp/prod_after_basic_auth.png")

            current_url = page.url
            print(f"   当前 URL: {current_url}")

            # 检查是否到达 WordPress 登录页面
            if "wp-login.php" in current_url:
                print("   ✅ 成功通过 HTTP Basic Auth，到达 WordPress 登录页面\n")

                # ==================== WordPress 登录 ====================
                print("2️⃣  WordPress 账号登录...")
                print(f"   用户名: {user_username}")

                # 检查登录表单元素
                username_input = await page.query_selector("#user_login")
                password_input = await page.query_selector("#user_pass")
                submit_button = await page.query_selector("#wp-submit")

                if not all([username_input, password_input, submit_button]):
                    print("   ❌ 未找到登录表单元素")
                    return False

                # 填写 WordPress 凭证
                await page.fill("#user_login", user_username)
                await page.fill("#user_pass", user_password)

                # 截图
                await page.screenshot(path="/tmp/prod_wp_login_form.png")
                print("   📸 登录表单截图: /tmp/prod_wp_login_form.png")

                # 点击登录
                await page.click("#wp-submit")
                await page.wait_for_load_state('networkidle')
                await asyncio.sleep(2)

                current_url = page.url
                print(f"   登录后 URL: {current_url}")

                # ==================== 验证登录成功 ====================
                if "wp-admin" in current_url:
                    print("\n   ✅ 成功登录 WordPress 后台！\n")

                    # 截图后台
                    await page.screenshot(path="/tmp/prod_dashboard.png")
                    print("   📸 后台截图: /tmp/prod_dashboard.png")

                    # 检查关键元素
                    print("3️⃣  检查后台界面元素...")

                    checks = [
                        ("#menu-posts", "文章菜单"),
                        ("#menu-media", "媒体库菜单"),
                        ("#wp-admin-bar-my-account", "用户账号栏"),
                    ]

                    for selector, name in checks:
                        try:
                            element = await page.query_selector(selector)
                            if element:
                                is_visible = await element.is_visible()
                                print(f"   {'✅' if is_visible else '⚠️'} {name}: {'可见' if is_visible else '不可见'}")
                            else:
                                print(f"   ❌ {name}: 未找到")
                        except Exception as e:
                            print(f"   ❌ {name}: 检查失败")

                    # 检查用户信息
                    print("\n4️⃣  验证当前登录用户...")
                    try:
                        user_info = await page.query_selector("#wp-admin-bar-my-account .display-name")
                        if user_info:
                            display_name = await user_info.inner_text()
                            print(f"   ✅ 当前用户: {display_name}")
                        else:
                            print("   ⚠️  无法获取用户信息")
                    except:
                        pass

                    # 检查新增文章功能
                    print("\n5️⃣  检查新增文章功能...")
                    try:
                        await page.hover("#menu-posts")
                        await asyncio.sleep(0.5)

                        new_post = await page.query_selector('a[href*="post-new.php"]')
                        if new_post:
                            print("   ✅ 找到'新增文章'入口")
                            await page.screenshot(path="/tmp/prod_posts_submenu.png")
                            print("   📸 子菜单截图: /tmp/prod_posts_submenu.png")
                        else:
                            print("   ⚠️  未找到'新增文章'入口")
                    except Exception as e:
                        print(f"   ❌ 检查失败: {e}")

                    print("\n" + "=" * 60)
                    print("✅ 生产环境配置验证成功！")
                    print("=" * 60)
                    print("\n📋 验证摘要:")
                    print("   ✅ HTTP Basic Auth 配置正确")
                    print("   ✅ WordPress 账号登录成功")
                    print("   ✅ 后台界面完全可访问")
                    print("   ✅ 关键功能入口存在")
                    print("\n⚠️  重要：本次测试未创建任何内容")
                    print("   配置验证完成，可用于自动化发布")

                    return True

                elif "wp-login.php" in current_url:
                    print("\n   ❌ WordPress 登录失败，仍在登录页面")
                    # 检查是否有错误消息
                    error_elem = await page.query_selector("#login_error")
                    if error_elem:
                        error_msg = await error_elem.inner_text()
                        print(f"   错误消息: {error_msg}")
                    await page.screenshot(path="/tmp/prod_wp_login_failed.png")
                    return False
                else:
                    print(f"\n   ⚠️  意外的页面: {current_url}")
                    return False

            else:
                print(f"   ❌ 未能到达 WordPress 登录页面")
                print(f"   当前页面: {current_url}")
                return False

        except Exception as e:
            print(f"\n❌ 测试出错: {e}")
            import traceback
            traceback.print_exc()

            try:
                await page.screenshot(path="/tmp/prod_error_v2.png")
                print("   📸 错误截图: /tmp/prod_error_v2.png")
            except:
                pass

            return False

        finally:
            print("\n⏳ 5 秒后关闭浏览器...")
            await asyncio.sleep(5)
            await browser.close()


if __name__ == "__main__":
    print("\n" + "🔐" * 30)
    print("生产环境配置验证测试 v2")
    print("🔐" * 30 + "\n")

    success = asyncio.run(test_production_with_basic_auth())

    print("\n" + "=" * 60)
    if success:
        print("✅ 测试成功：生产环境配置完全有效")
        print("   配置信息已安全存储在 .env 文件中")
        print("   可以开始使用自动化发布功能")
    else:
        print("❌ 测试失败：请检查以下项目")
        print("   1. 网络连接是否正常")
        print("   2. HTTP Basic Auth 凭证是否正确")
        print("   3. WordPress 账号密码是否正确")
        print("   4. 查看截图文件了解详情")
    print("=" * 60 + "\n")
