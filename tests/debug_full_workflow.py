"""
调试脚本：模拟完整工作流
1. 创建文章
2. 上传图片
3. 设置特色图片
"""

import asyncio
from playwright.async_api import async_playwright
import tempfile
from PIL import Image


async def test_full_workflow():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=300)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()

        try:
            print("1. 登录...")
            await page.goto("http://localhost:8001/wp-login.php")
            await page.fill("#user_login", "admin")
            await page.fill("#user_pass", "password")
            await page.click("#wp-submit")
            await page.wait_for_load_state('networkidle')
            print("   ✅ 登录成功")

            print("\n2. 导航到新文章...")
            await page.hover('#menu-posts')
            await asyncio.sleep(0.3)
            await page.click('a[href="post-new.php"]')
            await page.wait_for_load_state('networkidle')
            print("   ✅ 成功")

            print("\n3. 填写文章标题...")
            await page.fill("#title", "完整工作流测试")
            print("   ✅ 标题已填写")

            print("\n4. 上传图片到媒体库...")
            # 创建测试图片
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
                test_image_path = tmp.name
                img = Image.new('RGB', (800, 600), color='green')
                img.save(test_image_path)

            # 点击"添加媒体"按钮
            add_media_button = await page.query_selector("button.insert-media.add_media")
            if add_media_button:
                print("   找到 '添加媒体' 按钮")
                await add_media_button.click()
                await page.wait_for_selector(".media-modal", timeout=5000)
                print("   ✅ 媒体模态框已打开")

                # 切换到上传标签
                upload_tab = await page.query_selector("button.media-menu-item:has-text('Upload files')")
                if upload_tab:
                    await upload_tab.click()
                    await asyncio.sleep(0.5)

                # 上传文件
                file_input = await page.query_selector("input[type='file']")
                await file_input.set_input_files(test_image_path)
                print("   ✅ 文件已上传")

                # 等待处理完成
                await page.wait_for_selector(".attachment.save-ready", timeout=15000)
                print("   ✅ 图片处理完成")

                # 关闭模态框
                try:
                    close_button = await page.query_selector(".media-modal-close")
                    if close_button:
                        await close_button.click()
                        print("   ✅ 模态框已关闭")
                except:
                    await page.keyboard.press('Escape')
                    print("   ✅ 模态框已关闭 (ESC)")

                await asyncio.sleep(1)
            else:
                print("   ❌ 未找到 '添加媒体' 按钮")

            print("\n5. 检查 '#set-post-thumbnail' 元素...")
            set_thumbnail_link = await page.query_selector("#set-post-thumbnail")
            if set_thumbnail_link:
                is_visible = await set_thumbnail_link.is_visible()
                text = await set_thumbnail_link.inner_text()
                print(f"   ✅ 找到元素")
                print(f"   - 可见: {is_visible}")
                print(f"   - 文本: {text}")
            else:
                print("   ❌ 未找到 #set-post-thumbnail 元素")
                # 尝试其他选择器
                alt_selectors = [
                    "#postimagediv a",
                    ".editor-post-featured-image__toggle",
                    "a:has-text('Set featured image')",
                ]
                for selector in alt_selectors:
                    elem = await page.query_selector(selector)
                    if elem:
                        print(f"   找到替代元素: {selector}")

            print("\n6. 检查是否有打开的模态框...")
            modal = await page.query_selector(".media-modal")
            if modal:
                is_visible = await modal.is_visible()
                print(f"   模态框存在，可见: {is_visible}")
                if is_visible:
                    print("   关闭模态框...")
                    await page.keyboard.press('Escape')
                    await asyncio.sleep(1)
            else:
                print("   ✅ 没有打开的模态框")

            print("\n7. 点击 '设置特色图片'...")
            try:
                # 等待元素可见
                await page.wait_for_selector("#set-post-thumbnail", state='visible', timeout=5000)
                await page.click("#set-post-thumbnail")
                print("   ✅ 已点击")

                # 等待媒体模态框
                await page.wait_for_selector(".media-modal", state='visible', timeout=10000)
                print("   ✅ 媒体模态框已打开")

                print("\n8. 切换到媒体库...")
                library_tab = await page.query_selector("button.media-menu-item:has-text('Media Library')")
                if library_tab:
                    await library_tab.click()
                    await asyncio.sleep(0.5)
                    print("   ✅ 已切换到媒体库")

                print("\n9. 选择图片...")
                await page.wait_for_selector(".attachments-browser .attachment", timeout=5000)
                first_attachment = await page.query_selector(".attachments-browser .attachment")
                if first_attachment:
                    await first_attachment.click()
                    await asyncio.sleep(0.5)
                    print("   ✅ 已选择图片")

                print("\n10. 等待按钮启用并点击...")
                await page.wait_for_selector(".media-button-select:not([disabled])", timeout=10000)
                await page.click(".media-button-select")
                print("   ✅ 已点击设置按钮")

                await asyncio.sleep(2)

                print("\n11. 检查特色图片预览...")
                preview = await page.query_selector("#postimagediv img")
                if preview:
                    src = await preview.get_attribute("src")
                    print(f"   ✅ 特色图片设置成功!")
                    print(f"   图片 URL: {src}")
                    return True
                else:
                    print("   ❌ 未找到特色图片预览")
                    return False

            except Exception as e:
                print(f"   ❌ 设置特色图片失败: {e}")
                import traceback
                traceback.print_exc()
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
    success = asyncio.run(test_full_workflow())
    print("\n" + "=" * 60)
    print("结果:")
    print("=" * 60)
    if success:
        print("✅ 完整工作流成功")
    else:
        print("❌ 完整工作流失败")
