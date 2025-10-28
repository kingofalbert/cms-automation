"""
调试脚本 v2：详细检查附件选择状态
"""

import asyncio
from playwright.async_api import async_playwright
import tempfile
from PIL import Image


async def test_featured_image_detailed():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=300)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()

        try:
            print("1. 登录并创建文章...")
            await page.goto("http://localhost:8001/wp-login.php")
            await page.fill("#user_login", "admin")
            await page.fill("#user_pass", "password")
            await page.click("#wp-submit")
            await page.wait_for_load_state('networkidle')

            # 导航到新文章
            await page.hover('#menu-posts')
            await asyncio.sleep(0.3)
            await page.click('a[href="post-new.php"]')
            await page.wait_for_load_state('networkidle')
            await page.fill("#title", "特色图片测试")
            print("   ✅ 文章创建完成")

            print("\n2. 打开特色图片设置...")
            await page.click("#set-post-thumbnail")
            await page.wait_for_selector(".media-modal", timeout=5000)
            print("   ✅ 媒体模态框已打开")

            print("\n3. 切换到上传标签...")
            await page.click("button.media-menu-item:has-text('Upload files')")
            await asyncio.sleep(0.5)

            print("\n4. 上传测试图片...")
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
                test_image_path = tmp.name
                img = Image.new('RGB', (800, 600), color='red')
                img.save(test_image_path)

            file_input = await page.query_selector("input[type='file']")
            await file_input.set_input_files(test_image_path)
            print("   ✅ 文件已上传")

            print("\n5. 等待图片处理...")
            await page.wait_for_selector(".attachment.save-ready", timeout=15000)
            print("   ✅ 图片处理完成")

            print("\n6. 检查附件状态...")
            attachments = await page.query_selector_all(".attachment.save-ready")
            print(f"   找到 {len(attachments)} 个附件")

            if attachments:
                attachment = attachments[0]

                # 检查附件属性
                classes = await attachment.get_attribute("class")
                aria_checked = await attachment.get_attribute("aria-checked")
                aria_label = await attachment.get_attribute("aria-label")

                print(f"   附件类: {classes}")
                print(f"   aria-checked: {aria_checked}")
                print(f"   aria-label: {aria_label}")

                print("\n7. 点击附件...")
                await attachment.click()
                await asyncio.sleep(0.5)

                # 再次检查状态
                classes_after = await attachment.get_attribute("class")
                aria_checked_after = await attachment.get_attribute("aria-checked")
                print(f"   点击后类: {classes_after}")
                print(f"   点击后 aria-checked: {aria_checked_after}")

                # 检查是否有 'selected' 类
                if 'selected' in classes_after:
                    print("   ✅ 附件已被标记为选中")
                else:
                    print("   ⚠️  附件未被标记为选中")

            print("\n8. 检查按钮状态...")
            button = await page.query_selector(".media-button-select")
            if button:
                is_disabled = await button.is_disabled()
                is_enabled = await button.is_enabled()
                has_disabled_attr = await button.get_attribute("disabled")

                print(f"   is_disabled(): {is_disabled}")
                print(f"   is_enabled(): {is_enabled}")
                print(f"   disabled 属性: {has_disabled_attr}")

            print("\n9. 尝试在媒体库中查找图片...")
            # 切换到媒体库标签
            try:
                library_tab = await page.query_selector("button.media-menu-item:has-text('Media Library')")
                if library_tab:
                    await library_tab.click()
                    await asyncio.sleep(1)
                    print("   ✅ 已切换到媒体库")

                    # 查找图片
                    library_attachments = await page.query_selector_all(".attachments-browser .attachment")
                    print(f"   媒体库中找到 {len(library_attachments)} 个附件")

                    if library_attachments:
                        # 点击第一个
                        await library_attachments[0].click()
                        await asyncio.sleep(0.5)
                        print("   ✅ 已选择媒体库中的图片")

                        # 检查按钮状态
                        button = await page.query_selector(".media-button-select")
                        is_enabled_now = await button.is_enabled()
                        print(f"   按钮启用状态: {is_enabled_now}")

                        if is_enabled_now:
                            await button.click()
                            print("   ✅ 成功点击设置按钮")
                            await asyncio.sleep(2)

                            # 检查特色图片预览
                            preview = await page.query_selector("#postimagediv img")
                            if preview:
                                print("   ✅ 特色图片设置成功!")
                                return True
                            else:
                                print("   ❌ 未找到特色图片预览")
                        else:
                            print("   ❌ 按钮仍然禁用")
            except Exception as e:
                print(f"   ❌ 媒体库流程失败: {e}")

            return False

        except Exception as e:
            print(f"\n❌ 错误: {e}")
            import traceback
            traceback.print_exc()
            return False

        finally:
            print("\n等待 3 秒后关闭...")
            await asyncio.sleep(3)
            await browser.close()


if __name__ == "__main__":
    success = asyncio.run(test_featured_image_detailed())
    print("\n" + "=" * 60)
    print("结果:")
    print("=" * 60)
    if success:
        print("✅ 特色图片设置成功")
    else:
        print("❌ 特色图片设置失败")
