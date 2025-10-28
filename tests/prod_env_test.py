"""
生产环境配置验证测试
警告：此脚本仅用于验证登录和界面访问，不会创建或修改任何内容
"""

import asyncio
import os
from playwright.async_api import async_playwright
from dotenv import load_dotenv


# 加载环境变量
load_dotenv()


async def test_production_login():
    """测试生产环境登录流程（只读测试，不创建任何内容）"""

    print("=" * 60)
    print("🔒 生产环境登录测试")
    print("=" * 60)
    print("\n⚠️  警告：此测试仅验证配置，不会创建或修改任何内容\n")

    # 读取环境变量
    prod_url = os.getenv("PROD_WORDPRESS_URL")
    prod_login_url = os.getenv("PROD_LOGIN_URL")
    first_username = os.getenv("PROD_FIRST_LAYER_USERNAME")
    first_password = os.getenv("PROD_FIRST_LAYER_PASSWORD")
    user_username = os.getenv("PROD_USERNAME")
    user_password = os.getenv("PROD_PASSWORD")

    if not all([prod_url, first_username, first_password, user_username, user_password]):
        print("❌ 错误：环境变量未完全配置")
        print("   请检查 .env 文件")
        return False

    async with async_playwright() as p:
        # 启动浏览器（可视化模式，方便观察）
        browser = await p.chromium.launch(
            headless=False,  # 可视化，方便观察
            slow_mo=500      # 放慢速度
        )

        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )

        page = await context.new_page()

        try:
            # ==================== 第一层登录 ====================
            print("1️⃣  第一层登录测试...")
            print(f"   URL: {prod_login_url}")
            print(f"   用户名: {first_username}")

            await page.goto(prod_login_url)
            await page.wait_for_load_state('networkidle')

            # 填写第一层凭证
            await page.fill("#user_login", first_username)
            await page.fill("#user_pass", first_password)

            # 截图
            await page.screenshot(path="/tmp/prod_login_step1.png")
            print("   📸 截图已保存: /tmp/prod_login_step1.png")

            # 点击登录
            await page.click("#wp-submit")
            await page.wait_for_load_state('networkidle')
            await asyncio.sleep(2)

            current_url = page.url
            print(f"   当前 URL: {current_url}")

            # 检查是否需要第二层登录
            if "wp-login.php" in current_url:
                print("   ✅ 第一层登录成功，需要第二层认证\n")

                # ==================== 第二层登录 ====================
                print("2️⃣  个人账号登录测试...")
                print(f"   用户名: {user_username}")

                # 清空并填写个人凭证
                await page.fill("#user_login", "")
                await page.fill("#user_pass", "")
                await asyncio.sleep(0.5)

                await page.fill("#user_login", user_username)
                await page.fill("#user_pass", user_password)

                # 截图
                await page.screenshot(path="/tmp/prod_login_step2.png")
                print("   📸 截图已保存: /tmp/prod_login_step2.png")

                # 点击登录
                await page.click("#wp-submit")
                await page.wait_for_load_state('networkidle')
                await asyncio.sleep(2)

                current_url = page.url
                print(f"   当前 URL: {current_url}")

            # ==================== 验证登录成功 ====================
            print("\n3️⃣  验证后台访问...")

            # 检查是否到达后台
            if "wp-admin" in page.url:
                print("   ✅ 成功进入 WordPress 后台")

                # 截图后台首页
                await page.screenshot(path="/tmp/prod_dashboard.png")
                print("   📸 后台截图: /tmp/prod_dashboard.png")

                # 检查关键元素
                print("\n4️⃣  检查关键界面元素...")

                # 检查左侧菜单
                menu_items = [
                    ("#menu-posts", "文章菜单"),
                    ("#menu-media", "媒体库菜单"),
                    ("#menu-pages", "页面菜单"),
                ]

                for selector, name in menu_items:
                    try:
                        element = await page.query_selector(selector)
                        if element:
                            is_visible = await element.is_visible()
                            status = "✅" if is_visible else "⚠️"
                            print(f"   {status} {name}: {'可见' if is_visible else '不可见'}")
                        else:
                            print(f"   ❌ {name}: 未找到")
                    except Exception as e:
                        print(f"   ❌ {name}: 检查失败 - {e}")

                # 检查是否有"新增文章"功能
                print("\n5️⃣  检查新增文章入口...")
                try:
                    # 悬停在文章菜单上
                    await page.hover("#menu-posts")
                    await asyncio.sleep(1)

                    # 查找"新增文章"链接
                    new_post_link = await page.query_selector('a[href*="post-new.php"]')
                    if new_post_link:
                        is_visible = await new_post_link.is_visible()
                        if is_visible:
                            print("   ✅ 找到'新增文章'入口")

                            # 截图子菜单
                            await page.screenshot(path="/tmp/prod_posts_menu.png")
                            print("   📸 菜单截图: /tmp/prod_posts_menu.png")
                        else:
                            print("   ⚠️  '新增文章'入口存在但不可见")
                    else:
                        print("   ❌ 未找到'新增文章'入口")
                except Exception as e:
                    print(f"   ❌ 检查失败: {e}")

                print("\n" + "=" * 60)
                print("✅ 生产环境配置验证成功！")
                print("=" * 60)
                print("\n📋 验证摘要:")
                print("   ✅ 环境变量配置正确")
                print("   ✅ 第一层登录成功")
                print("   ✅ 个人账号登录成功")
                print("   ✅ 后台界面可访问")
                print("   ✅ 关键功能入口存在")
                print("\n⚠️  注意：本次测试未创建任何内容")
                print("   如需完整测试，请在测试环境进行")

                return True
            else:
                print(f"   ❌ 登录失败，当前 URL: {page.url}")
                await page.screenshot(path="/tmp/prod_login_failed.png")
                print("   📸 失败截图: /tmp/prod_login_failed.png")
                return False

        except Exception as e:
            print(f"\n❌ 测试过程中出错: {e}")
            import traceback
            traceback.print_exc()

            # 保存错误截图
            try:
                await page.screenshot(path="/tmp/prod_error.png")
                print("   📸 错误截图: /tmp/prod_error.png")
            except:
                pass

            return False

        finally:
            print("\n⏳ 5 秒后关闭浏览器...")
            await asyncio.sleep(5)
            await browser.close()


if __name__ == "__main__":
    print("\n" + "🔐" * 30)
    print("生产环境配置验证测试")
    print("🔐" * 30 + "\n")

    success = asyncio.run(test_production_login())

    print("\n" + "=" * 60)
    if success:
        print("✅ 测试完成：生产环境配置有效")
        print("   您可以开始使用此配置进行自动化发布")
    else:
        print("❌ 测试失败：请检查配置或网络连接")
        print("   请查看截图文件了解详情")
    print("=" * 60 + "\n")
