"""
调试脚本：测试特色图片设置流程
找出正确的选择器和操作顺序
"""

import asyncio
from playwright.async_api import async_playwright
from pathlib import Path


async def test_featured_image():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=500)
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

            print("\n2. 导航到新建文章...")
            await page.hover('#menu-posts')
            await asyncio.sleep(0.5)
            await page.click('a[href="post-new.php"]')
            await page.wait_for_load_state('networkidle')
            print(f"   ✅ 成功: {page.url}")

            print("\n3. 填写文章标题...")
            await page.fill("#title", "特色图片测试文章")
            print("   ✅ 标题填写完成")

            print("\n4. 尝试打开特色图片面板...")
            # 检查特色图片容器是否存在
            featured_container = await page.query_selector("#postimagediv")
            if featured_container:
                print("   ✅ 找到特色图片容器")
            else:
                print("   ❌ 未找到特色图片容器")
                # 尝试其他可能的选择器
                alt_selectors = [
                    ".editor-post-featured-image",
                    "[data-label='Featured image']",
                    ".components-panel__body.editor-post-featured-image",
                ]
                for selector in alt_selectors:
                    element = await page.query_selector(selector)
                    if element:
                        print(f"   ✅ 找到替代选择器: {selector}")
                        break

            print("\n5. 点击 '设置特色图片' 链接...")
            # 尝试多个可能的选择器
            selectors_to_try = [
                "#set-post-thumbnail",
                "a[href='#'][id='set-post-thumbnail']",
                ".editor-post-featured-image__toggle",
                "#postimagediv .inside a",
            ]

            clicked = False
            for selector in selectors_to_try:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        print(f"   尝试选择器: {selector}")
                        is_visible = await element.is_visible()
                        print(f"   元素可见: {is_visible}")

                        if is_visible:
                            await element.click()
                            print(f"   ✅ 成功点击: {selector}")
                            clicked = True
                            break
                except Exception as e:
                    print(f"   选择器 {selector} 失败: {e}")

            if not clicked:
                print("   ❌ 无法点击设置特色图片链接")
                return

            print("\n6. 等待媒体模态框...")
            await asyncio.sleep(1)

            # 尝试多个可能的媒体模态框选择器
            modal_selectors = [
                ".media-modal",
                ".media-frame",
                "#wp-media-grid",
                ".media-modal-content",
            ]

            modal_found = False
            for selector in modal_selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=5000)
                    if element:
                        is_visible = await element.is_visible()
                        print(f"   找到模态框: {selector}, 可见: {is_visible}")
                        modal_found = True
                        break
                except Exception as e:
                    print(f"   选择器 {selector} 未找到")

            if not modal_found:
                print("   ❌ 未找到媒体模态框")
                print("\n   调试信息 - 当前页面所有 class 包含 'media' 的元素:")
                elements = await page.query_selector_all("[class*='media']")
                for i, elem in enumerate(elements[:10]):  # 只显示前10个
                    classes = await elem.get_attribute("class")
                    tag = await elem.evaluate("el => el.tagName")
                    print(f"   {i+1}. <{tag} class='{classes}'>")
                return

            print("\n7. 切换到 '上传文件' 标签...")
            upload_tab_selectors = [
                "button.media-menu-item:has-text('Upload files')",
                ".media-router a[href='#']:has-text('Upload')",
                "a.media-menu-item:has-text('上传文件')",
            ]

            for selector in upload_tab_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        await element.click()
                        print(f"   ✅ 成功点击上传标签: {selector}")
                        await asyncio.sleep(0.5)
                        break
                except Exception as e:
                    print(f"   选择器 {selector} 失败: {e}")

            print("\n8. 上传测试图片...")
            # 创建测试图片
            import tempfile
            from PIL import Image

            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
                test_image_path = tmp.name
                img = Image.new('RGB', (800, 600), color='blue')
                img.save(test_image_path)

            print(f"   测试图片: {test_image_path}")

            # 尝试查找文件上传输入框
            file_input_selectors = [
                "input[type='file']",
                ".media-modal input[type='file']",
                "#__wp-uploader-id-0",
            ]

            uploaded = False
            for selector in file_input_selectors:
                try:
                    input_element = await page.query_selector(selector)
                    if input_element:
                        await input_element.set_input_files(test_image_path)
                        print(f"   ✅ 文件已上传: {selector}")
                        uploaded = True
                        await asyncio.sleep(2)  # 等待上传完成
                        break
                except Exception as e:
                    print(f"   选择器 {selector} 失败: {e}")

            if not uploaded:
                print("   ❌ 无法上传文件")
                return

            print("\n9. 等待图片上传完成...")
            await asyncio.sleep(3)

            print("\n10. 等待图片处理完成...")
            # 等待附件完成处理 (save-ready class)
            try:
                await page.wait_for_selector(".attachment.save-ready", timeout=10000)
                print("   ✅ 图片处理完成")
            except Exception as e:
                print(f"   ⚠️  未检测到 save-ready 状态: {e}")

            print("\n11. 查找并选择上传的图片...")
            # 尝试多个可能的附件选择器
            attachment_selectors = [
                ".attachment.save-ready",
                ".attachments-browser .attachment",
                ".media-modal .attachment",
            ]

            for selector in attachment_selectors:
                try:
                    attachments = await page.query_selector_all(selector)
                    print(f"   找到 {len(attachments)} 个附件 (选择器: {selector})")
                    if attachments:
                        # 点击第一个
                        await attachments[0].click()
                        print(f"   ✅ 已选择第一个附件")
                        await asyncio.sleep(0.5)
                        break
                except Exception as e:
                    print(f"   选择器 {selector} 失败: {e}")

            print("\n12. 等待 '设置特色图片' 按钮启用...")
            # 等待按钮变为启用状态
            try:
                await page.wait_for_selector(".media-button-select:not([disabled])", timeout=10000)
                print("   ✅ 按钮已启用")
            except Exception as e:
                print(f"   ⚠️  等待按钮启用超时: {e}")

            print("\n13. 点击 '设置特色图片' 按钮...")
            button_selectors = [
                ".media-button-select",
                "button.media-button-select",
                ".media-toolbar-primary button",
                "button:has-text('Set featured image')",
                "button:has-text('设置特色图片')",
            ]

            clicked_button = False
            for selector in button_selectors:
                try:
                    button = await page.query_selector(selector)
                    if button:
                        is_visible = await button.is_visible()
                        is_enabled = await button.is_enabled()
                        text = await button.inner_text()
                        print(f"   找到按钮: {selector}")
                        print(f"   - 可见: {is_visible}, 启用: {is_enabled}, 文本: '{text}'")

                        if is_visible and is_enabled:
                            await button.click()
                            print(f"   ✅ 成功点击: {selector}")
                            clicked_button = True
                            await asyncio.sleep(1)
                            break
                except Exception as e:
                    print(f"   选择器 {selector} 失败: {e}")

            if not clicked_button:
                print("   ❌ 无法点击按钮")
                return False

            print("\n14. 检查特色图片是否设置成功...")
            await asyncio.sleep(1)

            # 检查特色图片预览
            preview_selectors = [
                "#postimagediv img",
                ".editor-post-featured-image img",
                "#set-post-thumbnail-desc img",
            ]

            for selector in preview_selectors:
                try:
                    img = await page.query_selector(selector)
                    if img:
                        src = await img.get_attribute("src")
                        print(f"   ✅ 特色图片设置成功: {selector}")
                        print(f"   图片 URL: {src}")
                        return True
                except Exception as e:
                    print(f"   选择器 {selector} 失败: {e}")

            print("   ❌ 未找到特色图片预览")
            return False

        except Exception as e:
            print(f"\n❌ 错误: {e}")
            import traceback
            traceback.print_exc()
            return False

        finally:
            print("\n等待 3 秒后关闭浏览器...")
            await asyncio.sleep(3)
            await browser.close()


if __name__ == "__main__":
    success = asyncio.run(test_featured_image())
    print("\n" + "=" * 60)
    print("结果:")
    print("=" * 60)
    if success:
        print("✅ 特色图片设置流程成功")
    else:
        print("❌ 特色图片设置流程失败")
