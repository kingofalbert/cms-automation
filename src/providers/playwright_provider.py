"""
Playwright Provider 实现
使用 DOM 选择器精确控制 WordPress 后台
Phase 2: 低成本、高性能方案
"""

from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from typing import Dict, List, Optional
from datetime import datetime
import logging
import asyncio

from src.providers.base_provider import IPublishingProvider
from src.config.loader import SelectorConfig

logger = logging.getLogger(__name__)


class PlaywrightProvider(IPublishingProvider):
    """
    基于 Playwright 的发布提供者
    使用 DOM 选择器精确控制 WordPress 后台
    
    成本: ~$0.02/文章 (Playwright 本地执行，仅浏览器资源)
    性能: 1.5-3 分钟/文章
    可靠性: 95% (需要选择器准确)
    """

    def __init__(self, selectors: SelectorConfig):
        """
        Args:
            selectors: 选择器配置对象（从 YAML 加载）
        """
        self.selectors = selectors
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.playwright = None
        self.base_url: str = ""

    async def initialize(self, base_url: str, **kwargs) -> None:
        """
        初始化 Playwright 浏览器
        
        Args:
            base_url: WordPress 站点 URL
            **kwargs: 可选参数
                - cookies: List[Dict] 恢复会话的 cookies
                - headless: bool 是否无头模式 (默认 True)
        """
        logger.info("Initializing Playwright provider")

        self.playwright = await async_playwright().start()

        # 启动浏览器（优先 Chrome）
        headless = kwargs.get('headless', True)
        self.browser = await self.playwright.chromium.launch(
            headless=headless,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-blink-features=AutomationControlled'
            ]
        )

        # 创建页面上下文
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            locale='zh-TW',
            timezone_id='Asia/Taipei'
        )

        # 如果提供了 cookies，则恢复会话
        if 'cookies' in kwargs and kwargs['cookies']:
            await self.context.add_cookies(kwargs['cookies'])
            logger.info(f"Restored {len(kwargs['cookies'])} cookies")

        self.page = await self.context.new_page()

        # 设置默认超时
        self.page.set_default_timeout(30000)  # 30 秒

        # 导航到基础 URL
        self.base_url = base_url

        logger.info(f"Playwright initialized for: {base_url}")

    async def close(self) -> None:
        """关闭浏览器"""
        logger.info("Closing Playwright browser")
        
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def capture_screenshot(self) -> bytes:
        """捕获当前屏幕截图"""
        if not self.page:
            raise RuntimeError("Page not initialized")
        
        screenshot = await self.page.screenshot(full_page=True)
        logger.debug(f"Captured screenshot: {len(screenshot)} bytes")
        return screenshot

    async def get_cookies(self) -> List[Dict]:
        """获取当前浏览器 cookies"""
        if not self.context:
            raise RuntimeError("Context not initialized")
        
        cookies = await self.context.cookies()
        logger.debug(f"Retrieved {len(cookies)} cookies")
        return cookies

    # ==================== 导航类操作 ====================

    async def navigate_to(self, url: str) -> None:
        """导航到指定 URL"""
        logger.info(f"Navigating to: {url}")
        await self.page.goto(url, wait_until='networkidle')

    async def navigate_to_new_post(self) -> None:
        """导航到「新增文章」页面"""
        logger.info("Navigating to new post page")
        
        # 直接导航（更快）
        await self.navigate_to(f"{self.base_url}/wp-admin/post-new.php")
        
        # 等待页面加载完成
        await self.wait_for_element("new_post_title")

    # ==================== 元素交互操作 ====================

    async def fill_input(self, field_name: str, value: str) -> None:
        """
        填充输入框
        
        Args:
            field_name: 字段名称（如 "new_post_title", "login_username"）
            value: 要填充的值
        """
        logger.info(f"Filling input: {field_name}")
        
        selector = self.selectors.get(field_name)
        await self._fill_by_selector(selector, value)

    async def fill_textarea(self, field_name: str, value: str) -> None:
        """
        填充文本区域
        
        Args:
            field_name: 字段名称（如 "content"）
            value: 要填充的值
        """
        logger.info(f"Filling textarea: {field_name}")
        
        if field_name == "content":
            # WordPress 内容编辑器在 textarea 中（文字模式）
            selector = self.selectors.get("content_textarea")
        else:
            selector = self.selectors.get(field_name)
        
        await self._fill_by_selector(selector, value)

    async def click_button(self, button_name: str) -> None:
        """
        点击按钮
        
        Args:
            button_name: 按钮名称（如 "save_draft", "publish"）
        """
        logger.info(f"Clicking button: {button_name}")
        
        selector = self.selectors.get(button_name)
        await self._click_by_selector(selector)

    async def wait_for_element(self, element_name: str, timeout: int = 30) -> None:
        """
        等待元素出现
        
        Args:
            element_name: 元素名称
            timeout: 超时时间（秒）
        """
        logger.debug(f"Waiting for element: {element_name}")
        
        selector = self.selectors.get(element_name)
        selectors = selector if isinstance(selector, list) else [selector]
        
        # 尝试每个选择器
        for sel in selectors:
            try:
                await self.page.wait_for_selector(sel, timeout=timeout * 1000)
                logger.debug(f"Found element with selector: {sel}")
                return
            except Exception:
                continue
        
        raise ElementNotFoundError(f"Element not found: {element_name} with selectors: {selectors}")

    async def wait_for_success_message(self, message_text: str) -> None:
        """
        等待成功提示消息出现
        
        Args:
            message_text: 消息文本（部分匹配）
        """
        logger.info(f"Waiting for success message: {message_text}")
        
        selector = self.selectors.get("success_message")
        selectors = selector if isinstance(selector, list) else [selector]
        
        # 等待成功消息出现
        for sel in selectors:
            try:
                element = self.page.locator(sel)
                await element.wait_for(state='visible', timeout=10000)
                
                # 验证消息文本
                text = await element.text_content()
                if message_text in text:
                    logger.info(f"Success message found: {text}")
                    return
            except Exception:
                continue
        
        logger.warning(f"Success message not found: {message_text}")

    # ==================== 内容编辑操作 ====================

    async def clean_html_entities(self) -> None:
        """清理内容中的 HTML 实体（如 &nbsp;）"""
        logger.info("Cleaning HTML entities")
        
        selector = self.selectors.get("content_textarea")
        selectors = selector if isinstance(selector, list) else [selector]
        
        for sel in selectors:
            try:
                element = self.page.locator(sel).first
                content = await element.input_value()
                
                # 清理常见的 HTML 实体
                cleaned = content.replace('&nbsp;', ' ')
                cleaned = cleaned.replace('&amp;', '&')
                cleaned = cleaned.replace('&lt;', '<')
                cleaned = cleaned.replace('&gt;', '>')
                
                await element.fill(cleaned)
                logger.debug("HTML entities cleaned")
                return
            except Exception:
                continue
        
        logger.warning("Could not clean HTML entities")

    # ==================== 媒体库操作 ====================

    async def open_media_library(self) -> None:
        """打开媒体库弹窗"""
        logger.info("Opening media library")

        await self._click_by_selector(self.selectors.get("add_media_button"))
        await self.page.wait_for_selector(self.selectors.get("media_modal"), state='visible')

    async def upload_file(self, file_path: str) -> None:
        """
        上传文件

        Args:
            file_path: 本地文件路径
        """
        logger.info(f"Uploading file: {file_path}")

        # 点击「上传文件」标签（如果需要）
        try:
            await self._click_by_selector(self.selectors.get("upload_files_tab"))
        except ElementNotFoundError:
            pass  # 可能已经在上传标签页

        # 等待文件选择器事件
        async with self.page.expect_file_chooser() as fc_info:
            try:
                await self._click_by_selector(self.selectors.get("select_files_button"))
            except ElementNotFoundError:
                # 可能是拖放区域，使用隐藏的文件输入
                await self.page.evaluate("document.querySelector('input[type=file]').click()")

        file_chooser = await fc_info.value
        await file_chooser.set_files(file_path)

        logger.info("File uploaded, waiting for processing...")

    async def wait_for_upload_complete(self) -> None:
        """等待文件上传完成"""
        logger.info("Waiting for upload to complete")

        # 等待上传的图片被自动选中（有 .selected class）
        attachment_selector = self.selectors.get("media_attachment")
        selectors = attachment_selector if isinstance(attachment_selector, list) else [attachment_selector]

        for sel in selectors:
            try:
                await self.page.wait_for_selector(
                    f"{sel}.selected",
                    state='visible',
                    timeout=120000  # 2 分钟超时
                )
                logger.info("Upload completed successfully")
                return
            except Exception:
                continue

        logger.warning("Upload may not have completed successfully")

    async def fill_image_metadata(self, metadata: Dict[str, str]) -> None:
        """
        填写图片元数据

        Args:
            metadata: 元数据字典 {"alt": "...", "title": "...", "caption": "...", ...}
        """
        logger.info("Filling image metadata")

        # 等待右侧详细信息面板出现
        await self.page.wait_for_selector(
            self.selectors.get("attachment_details"),
            state='visible'
        )

        # 填写各个字段
        for field, value in metadata.items():
            if not value:
                continue

            selector_key = f"image_{field}"
            try:
                selector = self.selectors.get(selector_key)
                await self._fill_by_selector(selector, value)
                logger.debug(f"Filled {field}: {value[:50]}...")
            except (KeyError, ElementNotFoundError):
                logger.warning(f"No selector found for image field: {field}")

    async def configure_image_display(
        self,
        align: str,
        link_to: str,
        size: str
    ) -> None:
        """
        配置图片显示设置

        Args:
            align: 对齐方式（"none", "left", "center", "right"）
            link_to: 连结至（"none", "media", "attachment", "custom"）
            size: 尺寸（"thumbnail", "medium", "large", "full"）
        """
        logger.info(f"Configuring image display: align={align}, link={link_to}, size={size}")

        # 对齐
        try:
            align_selector = self.selectors.get("image_align_select")
            await self._select_option_by_label(align_selector, align)
        except Exception as e:
            logger.warning(f"Could not set align: {e}")

        # 连结至
        try:
            link_selector = self.selectors.get("image_link_select")
            await self._select_option_by_label(link_selector, link_to)
        except Exception as e:
            logger.warning(f"Could not set link_to: {e}")

        # 尺寸
        try:
            size_selector = self.selectors.get("image_size_select")
            await self._select_option_by_label(size_selector, size)
        except Exception as e:
            logger.warning(f"Could not set size: {e}")

    async def insert_image_to_content(self) -> None:
        """将图片插入到文章内容"""
        logger.info("Inserting image to content")

        await self._click_by_selector(self.selectors.get("insert_into_post_button"))
        await self.page.wait_for_selector(
            self.selectors.get("media_modal"),
            state='hidden',
            timeout=10000
        )

    async def close_media_library(self) -> None:
        """关闭媒体库弹窗"""
        logger.info("Closing media library")

        close_selector = self.selectors.get("media_modal_close")
        try:
            if await self.page.locator(close_selector).is_visible():
                await self._click_by_selector(close_selector)
        except Exception:
            pass  # 可能已经关闭

    # ==================== 特色图片操作 ====================

    async def set_as_featured_image(self) -> None:
        """将当前选中的图片设为特色图片"""
        logger.info("Setting featured image")

        await self._click_by_selector(self.selectors.get("set_featured_image_button"))

        # 等待模态框关闭
        await self.page.wait_for_selector(
            self.selectors.get("media_modal"),
            state='hidden',
            timeout=10000
        )

        # 验证特色图片已设置（右侧栏显示缩略图）
        await self.page.wait_for_selector(
            self.selectors.get("featured_image_thumbnail"),
            state='visible',
            timeout=10000
        )

    async def edit_image(self) -> None:
        """进入图片编辑模式"""
        logger.info("Entering image edit mode")

        await self._click_by_selector(self.selectors.get("edit_image_link"))
        await self.page.wait_for_selector(
            self.selectors.get("image_editor"),
            state='visible'
        )

    async def crop_image(self, size_name: str) -> None:
        """
        裁切图片到指定尺寸

        Args:
            size_name: 尺寸名称（如 "thumbnail", "facebook_700_359"）
        """
        logger.info(f"Cropping image to: {size_name}")

        # 选择裁切尺寸
        size_selector = f'input[value="{size_name}"]'
        await self.page.locator(size_selector).click()

        # 等待裁切框出现
        await self.page.wait_for_selector('.imgareaselect-outer', state='visible')

        # 点击裁切按钮
        await self._click_by_selector(self.selectors.get("crop_button"))

    async def save_crop(self) -> None:
        """保存裁切"""
        logger.info("Saving crop")

        await self._click_by_selector(self.selectors.get("save_crop_button"))

        # 等待 AJAX 请求完成
        try:
            await self.page.wait_for_response(
                lambda resp: 'admin-ajax.php' in resp.url and resp.status == 200,
                timeout=30000
            )
            logger.info("Crop saved successfully")
        except Exception as e:
            logger.warning(f"Could not confirm crop save: {e}")

    async def confirm_featured_image(self) -> None:
        """确认设置特色图片"""
        logger.info("Confirming featured image")

        # 如果在编辑器中，先返回
        # 然后点击设置特色图片按钮
        await self._click_by_selector(self.selectors.get("set_featured_image_button"))

        # 等待模态框关闭
        await self.page.wait_for_selector(
            self.selectors.get("media_modal"),
            state='hidden'
        )

    # ==================== 元数据操作 ====================

    async def add_tag(self, tag: str) -> None:
        """
        添加标签

        Args:
            tag: 标签文本
        """
        logger.info(f"Adding tag: {tag}")

        # 输入标签
        await self._fill_by_selector(self.selectors.get("new_tag_input"), tag)

        # 点击「新增」按钮
        await self._click_by_selector(self.selectors.get("add_tag_button"))

        # 等待标签出现在列表中
        tag_list = self.page.locator(self.selectors.get("tag_checklist"))
        await tag_list.locator(f'text="{tag}"').wait_for(state='visible', timeout=5000)

    async def select_category(self, category: str) -> None:
        """
        选择分类

        Args:
            category: 分类名称
        """
        logger.info(f"Selecting category: {category}")

        # 使用包含文本的标签定位复选框
        checkbox_selector = f'label:has-text("{category}") input[type="checkbox"]'
        await self.page.locator(checkbox_selector).check()

    async def configure_seo_plugin(self, seo_data: Dict[str, str]) -> None:
        """
        配置 SEO 插件（Yoast SEO）

        Args:
            seo_data: SEO 数据 {"focus_keyword": "...", "meta_title": "...", "meta_description": "..."}
        """
        logger.info("Configuring SEO plugin")

        # 滚动到 Yoast SEO 区域
        yoast_section = self.page.locator(self.selectors.get("yoast_section"))
        await yoast_section.scroll_into_view_if_needed()

        # 填写焦点关键字
        if "focus_keyword" in seo_data:
            await self._fill_by_selector(
                self.selectors.get("yoast_focus_keyword"),
                seo_data["focus_keyword"]
            )

        # 点击「编辑摘要」（如果需要）
        try:
            edit_snippet = self.selectors.get("yoast_edit_snippet")
            if await self.page.locator(edit_snippet).is_visible(timeout=2000):
                await self._click_by_selector(edit_snippet)
                await asyncio.sleep(1)  # 等待编辑器展开
        except Exception:
            pass  # 可能已经展开

        # 填写 SEO 标题
        if "meta_title" in seo_data:
            await self._fill_by_selector(
                self.selectors.get("yoast_meta_title"),
                seo_data["meta_title"]
            )

        # 填写 Meta 描述
        if "meta_description" in seo_data:
            await self._fill_by_selector(
                self.selectors.get("yoast_meta_description"),
                seo_data["meta_description"]
            )

    # ==================== 发布操作 ====================

    async def schedule_publish(self, publish_date: datetime) -> None:
        """
        设置排程发布时间

        Args:
            publish_date: 发布日期时间
        """
        logger.info(f"Scheduling publish for: {publish_date}")

        # 点击「编辑」发布时间
        await self._click_by_selector(self.selectors.get("edit_timestamp_link"))

        # 填写日期时间
        await self.page.select_option(
            self.selectors.get("publish_month"),
            value=str(publish_date.month)
        )
        await self._fill_by_selector(
            self.selectors.get("publish_day"),
            str(publish_date.day)
        )
        await self._fill_by_selector(
            self.selectors.get("publish_year"),
            str(publish_date.year)
        )
        await self._fill_by_selector(
            self.selectors.get("publish_hour"),
            str(publish_date.hour)
        )
        await self._fill_by_selector(
            self.selectors.get("publish_minute"),
            str(publish_date.minute).zfill(2)
        )

        # 点击「确定」
        await self._click_by_selector(self.selectors.get("save_timestamp_link"))

    async def get_published_url(self) -> str:
        """获取已发布文章的 URL"""
        logger.info("Getting published URL")

        # 从固定链接获取 URL
        try:
            permalink_link = self.page.locator(self.selectors.get("post_permalink"))
            url = await permalink_link.get_attribute('href', timeout=10000)
            logger.info(f"Got URL from permalink: {url}")
            return url
        except Exception:
            pass

        # 从成功消息中提取链接
        try:
            message_link_selector = f"{self.selectors.get('success_message')} a"
            message_link = self.page.locator(message_link_selector)
            url = await message_link.get_attribute('href', timeout=10000)
            logger.info(f"Got URL from success message: {url}")
            return url
        except Exception as e:
            logger.error(f"Could not get published URL: {e}")
            return ""

    # ==================== 辅助方法 ====================

    async def _select_option_by_label(self, selector: str | List[str], label: str) -> None:
        """
        通过标签选择下拉选项

        Args:
            selector: 选择器
            label: 选项标签
        """
        selectors = selector if isinstance(selector, list) else [selector]

        for sel in selectors:
            try:
                await self.page.select_option(sel, label=label)
                logger.debug(f"Selected option '{label}' in selector: {sel}")
                return
            except Exception as e:
                logger.debug(f"Could not select option with selector '{sel}': {e}")
                continue

        raise ElementNotFoundError(f"Could not select option '{label}' with selectors: {selectors}")

    async def _click_by_selector(self, selector: str | List[str]) -> None:
        """
        通过选择器点击元素（处理多选择器）
        
        Args:
            selector: 单个选择器或选择器列表
        
        Raises:
            ElementNotFoundError: 所有选择器都未找到元素
        """
        selectors = selector if isinstance(selector, list) else [selector]

        for sel in selectors:
            try:
                element = self.page.locator(sel).first
                if await element.is_visible(timeout=5000):
                    await element.click()
                    logger.debug(f"Clicked element with selector: {sel}")
                    return
            except Exception as e:
                logger.debug(f"Could not click with selector '{sel}': {e}")
                continue

        raise ElementNotFoundError(f"Could not find clickable element with selectors: {selectors}")

    async def _fill_by_selector(self, selector: str | List[str], value: str) -> None:
        """
        通过选择器填充元素（处理多选择器）
        
        Args:
            selector: 单个选择器或选择器列表
            value: 要填充的值
        
        Raises:
            ElementNotFoundError: 所有选择器都未找到元素
        """
        selectors = selector if isinstance(selector, list) else [selector]

        for sel in selectors:
            try:
                element = self.page.locator(sel).first
                if await element.is_visible(timeout=5000):
                    await element.fill(value)
                    logger.debug(f"Filled element with selector: {sel}")
                    return
            except Exception as e:
                logger.debug(f"Could not fill with selector '{sel}': {e}")
                continue

        raise ElementNotFoundError(f"Could not find fillable element with selectors: {selectors}")


class ElementNotFoundError(Exception):
    """元素未找到错误"""
    pass
