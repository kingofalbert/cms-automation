"""
WordPress Publishing Service - Playwright Provider

使用 Playwright 实现的 WordPress 发布 Provider
通过 CSS 选择器和 DOM 操作实现浏览器自动化
"""

import asyncio
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Playwright

from src.providers.base import (
    IPublishingProvider,
    LoginError,
    ArticleCreationError,
    ImageUploadError,
    FeaturedImageError,
    SEOConfigError,
    PublishError
)
from src.models import (
    Article,
    ImageAsset,
    ArticleMetadata,
    SEOData,
    WordPressCredentials
)
from src.config.loader import config, settings
from src.utils.logger import get_logger


class PlaywrightProvider(IPublishingProvider):
    """
    Playwright Provider 实现

    使用 Playwright 进行浏览器自动化，通过 CSS 选择器操作 WordPress 后台
    """

    def __init__(self):
        """初始化 Playwright Provider"""
        self.logger = get_logger('PlaywrightProvider')
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

        # 从配置加载设置
        self.headless = settings.playwright_headless
        self.timeout = settings.playwright_timeout
        self.screenshot_path = Path(settings.screenshot_path)
        self.screenshot_path.mkdir(parents=True, exist_ok=True)

        # 浏览器设置
        self.browser_type = settings.browser_type
        self.viewport_width = settings.browser_width
        self.viewport_height = settings.browser_height

    async def initialize(self) -> None:
        """初始化 Playwright 浏览器"""
        self.logger.info("初始化 Playwright")

        try:
            # 启动 Playwright
            self.playwright = await async_playwright().start()

            # 选择浏览器类型
            if self.browser_type == 'chromium':
                browser_engine = self.playwright.chromium
            elif self.browser_type == 'firefox':
                browser_engine = self.playwright.firefox
            elif self.browser_type == 'webkit':
                browser_engine = self.playwright.webkit
            else:
                browser_engine = self.playwright.chromium

            # 启动浏览器
            self.browser = await browser_engine.launch(
                headless=self.headless,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )

            # 创建浏览器上下文
            self.context = await self.browser.new_context(
                viewport={'width': self.viewport_width, 'height': self.viewport_height},
                accept_downloads=True
            )

            # 设置默认超时
            self.context.set_default_timeout(self.timeout)

            # 创建页面
            self.page = await self.context.new_page()

            self.logger.info("Playwright 初始化完成")

        except Exception as e:
            self.logger.error(f"Playwright 初始化失败: {e}")
            raise

    async def cleanup(self) -> None:
        """清理 Playwright 资源"""
        self.logger.info("清理 Playwright 资源")

        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()

            self.logger.info("Playwright 资源清理完成")

        except Exception as e:
            self.logger.error(f"Playwright 资源清理失败: {e}")

    # ==================== Phase 1: 登录 ====================

    async def login(
        self,
        wordpress_url: str,
        credentials: WordPressCredentials
    ) -> bool:
        """
        登录 WordPress 后台

        Args:
            wordpress_url: WordPress 站点 URL
            credentials: 登录凭证

        Returns:
            是否登录成功
        """
        self.logger.info(f"开始登录 WordPress: {wordpress_url}")

        try:
            # 导航到登录页面
            login_url = f"{wordpress_url}/wp-admin"
            await self.page.goto(login_url, wait_until='domcontentloaded')
            await self.page.wait_for_load_state('networkidle')

            # 获取选择器
            username_selector = config.get_selector('login', 'username_input')
            password_selector = config.get_selector('login', 'password_input')
            submit_selector = config.get_selector('login', 'submit_button')

            # 填写用户名
            self.logger.debug("填写用户名")
            await self.page.fill(username_selector, credentials.username)

            # 填写密码
            self.logger.debug("填写密码")
            await self.page.fill(password_selector, credentials.password)

            # 点击登录按钮
            self.logger.debug("点击登录按钮")
            await self.page.click(submit_selector)

            # 等待页面跳转
            await self.page.wait_for_load_state('networkidle')

            # 验证是否登录成功
            current_url = self.page.url
            if 'wp-admin' in current_url and 'wp-login.php' not in current_url:
                self.logger.info("登录成功")
                return True
            else:
                # 检查是否有错误消息
                error_selector = config.get_selector('login', 'error_message')
                try:
                    error_element = await self.page.wait_for_selector(error_selector, timeout=3000)
                    error_text = await error_element.text_content()
                    raise LoginError(f"登录失败: {error_text}")
                except:
                    raise LoginError("登录失败: 未能跳转到后台")

        except Exception as e:
            self.logger.error(f"登录失败: {e}")
            raise LoginError(str(e))

    # ==================== Phase 2: 文章创建 ====================

    async def create_article(
        self,
        article: Article,
        metadata: ArticleMetadata
    ) -> bool:
        """
        创建文章（标题、内容、摘要、分类、标签）

        Args:
            article: 文章数据
            metadata: 文章元数据

        Returns:
            是否创建成功
        """
        self.logger.info(f"开始创建文章: {article.title}")

        try:
            # 导航到新建文章页面
            await self._navigate_to_new_post()

            # 填写标题
            await self._fill_title(article.title)

            # 填写内容
            await self._fill_content(article.content_html)

            # 填写摘要（如果有）
            if article.excerpt:
                await self._fill_excerpt(article.excerpt)

            # 设置分类
            if metadata.categories:
                await self._set_categories(metadata.categories)

            # 设置标签
            if metadata.tags:
                await self._set_tags(metadata.tags)

            self.logger.info("文章创建完成")
            return True

        except Exception as e:
            self.logger.error(f"文章创建失败: {e}")
            raise ArticleCreationError(str(e))

    async def _navigate_to_new_post(self):
        """导航到新建文章页面"""
        self.logger.debug("导航到新建文章页面")

        # 先悬停在 Posts 菜单上展开子菜单
        posts_menu_selector = config.get_selector('navigation', 'posts_menu')
        await self.page.hover(posts_menu_selector)
        await self.page.wait_for_timeout(500)  # 等待子菜单展开

        # 然后点击"新建文章"
        new_post_selector = config.get_selector('navigation', 'new_post')
        await self.page.click(new_post_selector)
        await self.page.wait_for_load_state('networkidle')

        # 等待编辑器就绪
        editor_ready_selector = config.get_selector('wait_for', 'editor_ready')
        await self.page.wait_for_selector(editor_ready_selector, timeout=10000)

    async def _fill_title(self, title: str):
        """填写文章标题"""
        self.logger.debug(f"填写标题: {title}")

        title_selector = config.get_selector('editor', 'classic', 'title_input')
        await self.page.fill(title_selector, title)

    async def _fill_content(self, content_html: str):
        """填写文章内容"""
        self.logger.debug("填写文章内容")

        # 切换到文本编辑器模式 (更可靠)
        text_tab_selector = config.get_selector('editor', 'classic', 'text_tab')
        await self.page.click(text_tab_selector)
        await asyncio.sleep(0.5)

        # 填写 HTML 内容
        text_editor_selector = config.get_selector('editor', 'classic', 'text_editor')
        await self.page.fill(text_editor_selector, content_html)

    async def _fill_excerpt(self, excerpt: str):
        """填写文章摘要"""
        self.logger.debug(f"填写摘要: {excerpt}")

        try:
            excerpt_selector = config.get_selector('metadata', 'excerpt', 'textarea')
            # 可能需要先展开摘要面板
            if not await self.page.is_visible(excerpt_selector):
                # 尝试点击 Screen Options 启用摘要
                self.logger.debug("摘要输入框不可见，尝试启用")
                # WordPress 的 Screen Options 逻辑较复杂，这里简化处理
                pass

            await self.page.fill(excerpt_selector, excerpt)
        except Exception as e:
            self.logger.warning(f"摘要填写失败: {e}")
            # 摘要不是必需的，失败不影响整体流程

    async def _set_categories(self, categories: List[str]):
        """设置文章分类"""
        self.logger.debug(f"设置分类: {categories}")

        try:
            for category in categories:
                # 查找分类复选框
                # WordPress 分类 ID 是动态的，需要通过文本匹配
                category_panel = config.get_selector('metadata', 'categories', 'panel')
                await self.page.wait_for_selector(category_panel)

                # 在分类列表中查找对应的分类
                checklist_selector = config.get_selector('metadata', 'categories', 'checklist')
                checklist = await self.page.query_selector(checklist_selector)

                if checklist:
                    # 查找包含分类名称的标签
                    labels = await checklist.query_selector_all('label')
                    for label in labels:
                        text = await label.text_content()
                        if text and category in text:
                            checkbox = await label.query_selector('input[type="checkbox"]')
                            if checkbox:
                                is_checked = await checkbox.is_checked()
                                if not is_checked:
                                    await checkbox.check()
                                    self.logger.debug(f"已勾选分类: {category}")
                            break

        except Exception as e:
            self.logger.warning(f"分类设置失败: {e}")
            # 分类设置失败不影响主流程

    async def _set_tags(self, tags: List[str]):
        """设置文章标签"""
        self.logger.debug(f"设置标签: {tags}")

        try:
            tag_input_selector = config.get_selector('metadata', 'tags', 'input')
            add_button_selector = config.get_selector('metadata', 'tags', 'add_button')

            for tag in tags:
                # 输入标签
                await self.page.fill(tag_input_selector, tag)
                # 点击添加按钮
                await self.page.click(add_button_selector)
                await asyncio.sleep(0.3)  # 等待标签添加

                self.logger.debug(f"已添加标签: {tag}")

        except Exception as e:
            self.logger.warning(f"标签设置失败: {e}")
            # 标签设置失败不影响主流程

    # ==================== Phase 3: 图片上传 ====================

    async def upload_images(
        self,
        images: List[ImageAsset]
    ) -> List[str]:
        """
        上传图片到媒体库

        Args:
            images: 图片列表

        Returns:
            上传成功的图片 URL 列表
        """
        self.logger.info(f"开始上传 {len(images)} 张图片")

        uploaded_urls = []

        try:
            for i, image in enumerate(images):
                self.logger.debug(f"上传第 {i+1}/{len(images)} 张图片: {image.file_path}")

                # 打开媒体库模态框
                await self._open_media_modal()

                # 上传图片文件
                await self._upload_image_file(image.file_path)

                # 等待上传完成
                await self._wait_for_upload_complete()

                # 设置图片元数据
                await self._set_image_metadata(image)

                # 关闭模态框
                await self._close_media_modal()

                uploaded_urls.append(image.file_path)  # 实际应返回 WordPress URL
                self.logger.debug(f"图片上传成功: {image.file_path}")

            self.logger.info(f"所有图片上传完成: {len(uploaded_urls)} 张")
            return uploaded_urls

        except Exception as e:
            self.logger.error(f"图片上传失败: {e}")
            raise ImageUploadError(str(e))

    async def _open_media_modal(self):
        """打开添加媒体模态框"""
        # 这里简化处理，实际需要根据页面状态判断
        add_media_selector = "button.insert-media.add_media"
        try:
            await self.page.click(add_media_selector, timeout=5000)
            await self.page.wait_for_selector(config.get_selector('media', 'modal', 'container'), timeout=5000)
        except Exception as e:
            self.logger.debug(f"打开媒体模态框失败: {e}")

    async def _upload_image_file(self, file_path: str):
        """上传图片文件"""
        # 点击选择文件按钮
        select_files_selector = config.get_selector('media', 'upload', 'select_files')

        # 使用 Playwright 的文件选择 API
        async with self.page.expect_file_chooser() as fc_info:
            await self.page.click(select_files_selector)
        file_chooser = await fc_info.value
        await file_chooser.set_files(file_path)

    async def _wait_for_upload_complete(self):
        """等待上传完成"""
        # 等待进度条消失
        progress_selector = config.get_selector('media', 'upload', 'progress_bar')
        try:
            await self.page.wait_for_selector(progress_selector, state='hidden', timeout=30000)
        except:
            # 如果没有进度条或已经消失，继续
            pass

        await asyncio.sleep(1)  # 额外等待确保上传完成

    async def _set_image_metadata(self, image: ImageAsset):
        """设置图片元数据"""
        try:
            # 设置 Alt Text
            alt_input_selector = config.get_selector('media', 'details', 'alt_input')
            await self.page.fill(alt_input_selector, image.alt_text)

            # 设置 Title
            title_input_selector = config.get_selector('media', 'details', 'title_input')
            await self.page.fill(title_input_selector, image.title)

            # 设置 Caption
            if image.caption:
                caption_input_selector = config.get_selector('media', 'details', 'caption_input')
                await self.page.fill(caption_input_selector, image.caption)

            self.logger.debug("图片元数据设置完成")

        except Exception as e:
            self.logger.warning(f"图片元数据设置失败: {e}")

    async def _close_media_modal(self):
        """关闭媒体库模态框"""
        try:
            close_button_selector = config.get_selector('media', 'modal', 'close_button')
            await self.page.click(close_button_selector)
            await asyncio.sleep(0.5)
        except Exception as e:
            # 按 ESC 键关闭
            await self.page.keyboard.press('Escape')
            await asyncio.sleep(0.5)

    async def set_featured_image(
        self,
        image: ImageAsset
    ) -> bool:
        """
        设置特色图片

        Args:
            image: 特色图片

        Returns:
            是否设置成功
        """
        self.logger.info(f"设置特色图片: {image.file_path}")

        try:
            # 确保没有打开的媒体模态框
            try:
                modal = await self.page.query_selector(config.get_selector('media', 'modal', 'container'))
                if modal:
                    is_visible = await modal.is_visible()
                    if is_visible:
                        self.logger.debug("检测到打开的模态框，正在关闭...")
                        await self.page.keyboard.press('Escape')
                        await asyncio.sleep(1)
            except:
                pass

            # 点击"设置特色图片"
            set_link_selector = config.get_selector('metadata', 'featured_image', 'set_link')

            # 等待元素可见且可点击
            await self.page.wait_for_selector(set_link_selector, state='visible', timeout=10000)
            await self.page.click(set_link_selector)

            # 等待媒体库模态框打开
            await self.page.wait_for_selector(config.get_selector('media', 'modal', 'container'), timeout=10000)
            await asyncio.sleep(0.5)

            # 切换到媒体库标签（而不是上传标签）
            try:
                # 查找"Media Library"标签并点击
                library_tab = await self.page.query_selector("button.media-menu-item:has-text('Media Library')")
                if not library_tab:
                    # 尝试中文
                    library_tab = await self.page.query_selector("button.media-menu-item:has-text('媒体库')")

                if library_tab:
                    await library_tab.click()
                    await asyncio.sleep(0.5)
                    self.logger.debug("已切换到媒体库标签")
            except Exception as e:
                self.logger.warning(f"切换到媒体库标签失败，可能已在媒体库标签: {e}")

            # 等待附件加载完成
            await self.page.wait_for_selector(config.get_selector('media', 'library', 'items'), timeout=10000)

            # 选择刚上传的图片（通常是第一个）
            first_image_selector = f"{config.get_selector('media', 'library', 'items')}:first-child"
            await self.page.click(first_image_selector)
            await asyncio.sleep(0.5)

            # 等待"设置特色图片"按钮启用
            select_button_selector = config.get_selector('media', 'actions', 'select_button')
            await self.page.wait_for_selector(f"{select_button_selector}:not([disabled])", timeout=10000)

            # 点击"设置特色图片"按钮
            await self.page.click(select_button_selector)

            # 等待模态框关闭
            await asyncio.sleep(1)

            self.logger.info("特色图片设置完成")
            return True

        except Exception as e:
            self.logger.error(f"特色图片设置失败: {e}")
            raise FeaturedImageError(str(e))

    # ==================== Phase 4: SEO 配置 ====================

    async def configure_seo(
        self,
        seo: SEOData
    ) -> bool:
        """
        配置 SEO 设置 (Yoast SEO)

        Args:
            seo: SEO 数据

        Returns:
            是否配置成功
        """
        self.logger.info("开始配置 Yoast SEO")

        try:
            # 滚动到 Yoast SEO 面板
            yoast_panel_selector = config.get_selector('yoast_seo', 'panel')
            await self.page.evaluate(f"document.querySelector('{yoast_panel_selector}').scrollIntoView()")
            await asyncio.sleep(0.5)

            # 设置焦点关键字
            await self._set_focus_keyword(seo.focus_keyword)

            # 设置 SEO 标题
            await self._set_seo_title(seo.meta_title)

            # 设置 Meta 描述
            await self._set_meta_description(seo.meta_description)

            self.logger.info("Yoast SEO 配置完成")
            return True

        except Exception as e:
            self.logger.error(f"SEO 配置失败: {e}")
            raise SEOConfigError(str(e))

    async def _set_focus_keyword(self, keyword: str):
        """设置焦点关键字"""
        self.logger.debug(f"设置焦点关键字: {keyword}")

        try:
            keyword_input_selector = config.get_selector('yoast_seo', 'focus_keyword', 'input')
            await self.page.fill(keyword_input_selector, keyword)
        except Exception as e:
            self.logger.warning(f"焦点关键字设置失败: {e}")

    async def _set_seo_title(self, title: str):
        """设置 SEO 标题"""
        self.logger.debug(f"设置 SEO 标题: {title}")

        try:
            title_input_selector = config.get_selector('yoast_seo', 'meta_title', 'input')
            await self.page.fill(title_input_selector, title)
        except Exception as e:
            self.logger.warning(f"SEO 标题设置失败: {e}")

    async def _set_meta_description(self, description: str):
        """设置 Meta 描述"""
        self.logger.debug(f"设置 Meta 描述: {description}")

        try:
            description_textarea_selector = config.get_selector('yoast_seo', 'meta_description', 'textarea')
            await self.page.fill(description_textarea_selector, description)
        except Exception as e:
            self.logger.warning(f"Meta 描述设置失败: {e}")

    # ==================== Phase 5: 发布 ====================

    async def publish(
        self,
        metadata: ArticleMetadata
    ) -> str:
        """
        发布文章

        Args:
            metadata: 发布元数据

        Returns:
            发布后的文章 URL
        """
        self.logger.info("开始发布文章")

        try:
            # 根据配置选择发布方式
            if metadata.publish_immediately:
                # 立即发布
                await self._publish_immediately()
            else:
                # 排程发布
                await self._schedule_publish(metadata.publish_date)

            # 等待发布完成
            await self._wait_for_publish_complete()

            # 获取发布后的 URL
            published_url = await self._get_published_url()

            self.logger.info(f"文章发布成功: {published_url}")
            return published_url

        except Exception as e:
            self.logger.error(f"文章发布失败: {e}")
            raise PublishError(str(e))

    async def _publish_immediately(self):
        """立即发布"""
        self.logger.debug("点击发布按钮")

        publish_button_selector = config.get_selector('publish', 'publish_button')
        await self.page.click(publish_button_selector)

    async def _schedule_publish(self, publish_date):
        """排程发布"""
        self.logger.debug(f"设置排程发布: {publish_date}")

        # 点击编辑发布时间
        edit_link_selector = config.get_selector('publish', 'schedule', 'edit_link')
        await self.page.click(edit_link_selector)

        # 设置日期和时间
        # (这里简化处理，实际需要分别设置年月日时分)

        # 点击确定
        ok_button_selector = config.get_selector('publish', 'schedule', 'ok_button')
        await self.page.click(ok_button_selector)

        # 点击排程按钮
        publish_button_selector = config.get_selector('publish', 'publish_button')
        await self.page.click(publish_button_selector)

    async def _wait_for_publish_complete(self):
        """等待发布完成"""
        # 等待成功消息出现
        success_selector = config.get_selector('notices', 'success')
        await self.page.wait_for_selector(success_selector, timeout=10000)
        await asyncio.sleep(1)

    async def _get_published_url(self) -> str:
        """获取发布后的文章 URL"""
        try:
            # 尝试从成功消息中获取"查看文章"链接
            view_post_selector = f"{config.get_selector('notices', 'post_published', 'container')} a"
            view_link = await self.page.query_selector(view_post_selector)

            if view_link:
                url = await view_link.get_attribute('href')
                return url

            # 如果找不到，返回当前页面 URL (编辑页面)
            return self.page.url

        except Exception as e:
            self.logger.warning(f"获取发布 URL 失败: {e}")
            return self.page.url

    # ==================== 截图功能 ====================

    async def take_screenshot(
        self,
        name: str,
        description: str = ""
    ) -> Optional[str]:
        """
        截图（用于审计追踪）

        Args:
            name: 截图名称
            description: 截图描述

        Returns:
            截图文件路径
        """
        try:
            if not settings.enable_screenshots:
                return None

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{timestamp}_{name}.png"
            filepath = self.screenshot_path / filename

            await self.page.screenshot(
                path=str(filepath),
                full_page=True,
                type='png'
            )

            self.logger.debug(f"截图已保存: {filepath}")
            return str(filepath)

        except Exception as e:
            self.logger.warning(f"截图失败: {e}")
            return None
