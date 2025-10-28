# WordPress 视觉自动化发布 - 实施计划

**文档版本**: v1.0
**创建日期**: 2025-10-27
**状态**: 设计中
**关联文档**: [wordpress-publishing-spec.md](./wordpress-publishing-spec.md)

---

## 目录

1. [架构设计](#架构设计)
2. [核心组件](#核心组件)
3. [Playwright 实现方案](#playwright-实现方案)
4. [Computer Use 实现方案](#computer-use-实现方案)
5. [降级机制](#降级机制)
6. [数据流设计](#数据流设计)
7. [错误处理](#错误处理)
8. [配置管理](#配置管理)
9. [日志与监控](#日志与监控)
10. [部署方案](#部署方案)
11. [测试策略](#测试策略)
12. [性能优化](#性能优化)

---

## 架构设计

### 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                     WordPress Publishing Service                 │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Publishing Orchestrator                     │
│  • Task Management                                               │
│  • Provider Selection                                            │
│  • Fallback Logic                                                │
│  • Audit Trail                                                   │
└─────────────────────────────────────────────────────────────────┘
                    │                              │
          ┌─────────┴─────────┐         ┌─────────┴─────────┐
          ▼                   ▼         ▼                   ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│  Playwright      │  │  Computer Use    │  │  Gemini          │
│  Provider        │  │  Provider        │  │  Computer Use    │
│                  │  │  (Anthropic)     │  │  Provider        │
└──────────────────┘  └──────────────────┘  └──────────────────┘
          │                   │                       │
          └───────────────────┴───────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  Browser Layer   │
                    │  (Chrome/CDP)    │
                    └──────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  WordPress Site  │
                    └──────────────────┘
```

### 架构原则

1. **Provider Abstraction（提供者抽象）**:
   - 定义统一的 `IPublishingProvider` 接口
   - 各 Provider 实现相同的接口，支持热切换
   - 配置驱动选择，无需修改业务代码

2. **Fail-Fast with Graceful Degradation（快速失败 + 优雅降级）**:
   - Playwright 快速失败（3 次重试，每次 5 秒超时）
   - 自动切换到 Computer Use
   - 保持已完成步骤的状态，从失败点继续

3. **Idempotency（幂等性）**:
   - 每个步骤可重复执行而不产生副作用
   - 通过草稿状态管理避免重复发布
   - 使用唯一任务 ID 追踪执行历史

4. **Observability（可观测性）**:
   - 每步操作记录详细日志
   - 关键节点截图存档
   - 实时监控执行进度和健康状态

---

## 核心组件

### 1. Publishing Orchestrator（发布协调器）

**职责**:
- 管理发布任务的生命周期
- 协调各个 Provider 的调用
- 处理降级逻辑
- 生成审计日志

**接口设计**:

```python
class PublishingOrchestrator:
    """
    发布协调器 - 负责整个发布流程的编排
    """

    def __init__(
        self,
        primary_provider: IPublishingProvider,
        fallback_provider: Optional[IPublishingProvider] = None,
        config: PublishingConfig = None
    ):
        self.primary = primary_provider
        self.fallback = fallback_provider
        self.config = config or PublishingConfig()
        self.audit_logger = AuditLogger()
        self.current_provider = primary_provider

    async def publish_article(
        self,
        article: Article,
        images: List[ImageAsset],
        metadata: ArticleMetadata
    ) -> PublishResult:
        """
        发布文章的主入口

        Args:
            article: 文章对象（标题、内容、SEO数据）
            images: 图片资源列表
            metadata: 元数据（标签、分类、发布选项）

        Returns:
            PublishResult: 包含发布状态、URL、日志等

        Raises:
            PublishingError: 所有 Provider 都失败时抛出
        """
        task_id = self._generate_task_id()
        context = PublishingContext(task_id, article, images, metadata)

        try:
            # 阶段一：登录与导航
            await self._execute_phase("login", self._phase_login, context)

            # 阶段二：文章内容填充
            await self._execute_phase("content", self._phase_fill_content, context)

            # 阶段三：图片处理
            await self._execute_phase("images", self._phase_process_images, context)

            # 阶段四：元数据设置
            await self._execute_phase("metadata", self._phase_set_metadata, context)

            # 阶段五：发布/保存
            await self._execute_phase("publish", self._phase_publish, context)

            return PublishResult(
                success=True,
                task_id=task_id,
                url=context.published_url,
                audit_trail=self.audit_logger.get_trail(task_id)
            )

        except PublishingError as e:
            self.audit_logger.log_failure(task_id, str(e))
            raise

    async def _execute_phase(
        self,
        phase_name: str,
        phase_func: Callable,
        context: PublishingContext
    ):
        """
        执行一个发布阶段，处理重试和降级逻辑

        Args:
            phase_name: 阶段名称（用于日志）
            phase_func: 阶段执行函数
            context: 发布上下文
        """
        max_retries = self.config.max_retries
        retry_count = 0

        while retry_count < max_retries:
            try:
                # 截图：执行前
                screenshot_before = await self.current_provider.capture_screenshot()
                self.audit_logger.save_screenshot(
                    context.task_id, f"{phase_name}_before", screenshot_before
                )

                # 执行阶段
                await phase_func(self.current_provider, context)

                # 截图：执行后
                screenshot_after = await self.current_provider.capture_screenshot()
                self.audit_logger.save_screenshot(
                    context.task_id, f"{phase_name}_after", screenshot_after
                )

                # 成功，记录日志并返回
                self.audit_logger.log_phase_success(
                    context.task_id, phase_name, retry_count
                )
                return

            except (ElementNotFoundError, TimeoutError) as e:
                retry_count += 1
                self.audit_logger.log_phase_failure(
                    context.task_id, phase_name, retry_count, str(e)
                )

                if retry_count >= max_retries:
                    # 尝试降级
                    if self.fallback and self.current_provider != self.fallback:
                        logger.warning(
                            f"Phase {phase_name} failed {max_retries} times, "
                            "falling back to Computer Use"
                        )
                        await self._switch_to_fallback(context)
                        retry_count = 0  # 重置重试计数
                    else:
                        raise PublishingError(
                            f"Phase {phase_name} failed after {max_retries} retries"
                        )

                await asyncio.sleep(self.config.retry_delay)

    async def _switch_to_fallback(self, context: PublishingContext):
        """切换到备用 Provider（Computer Use）"""
        # 关闭当前 Provider
        await self.current_provider.close()

        # 切换到备用 Provider
        self.current_provider = self.fallback

        # 重新初始化浏览器会话（继承登录状态）
        await self.current_provider.initialize(
            context.wordpress_url,
            cookies=context.browser_cookies
        )

        self.audit_logger.log_provider_switch(context.task_id, "computer_use")

    # ==================== 阶段执行函数 ====================

    async def _phase_login(self, provider: IPublishingProvider, context: PublishingContext):
        """阶段一：登录 WordPress"""
        await provider.navigate_to(context.wordpress_url + "/wp-admin")
        await provider.fill_input("username", context.credentials.username)
        await provider.fill_input("password", context.credentials.password)
        await provider.click_button("login")
        await provider.wait_for_element("dashboard")
        # 保存 cookies 以便降级时复用
        context.browser_cookies = await provider.get_cookies()

    async def _phase_fill_content(self, provider: IPublishingProvider, context: PublishingContext):
        """阶段二：填充文章内容"""
        # 导航到新增文章
        await provider.navigate_to_new_post()

        # 填写标题
        await provider.fill_input("title", context.article.title)

        # 切换到文字模式
        await provider.click_button("text_mode")

        # 填充内容（HTML 格式）
        await provider.fill_textarea("content", context.article.content_html)

        # 清理多余的 HTML 实体
        await provider.clean_html_entities()

        # 保存草稿
        await provider.click_button("save_draft")
        await provider.wait_for_success_message("草稿已更新")

    async def _phase_process_images(self, provider: IPublishingProvider, context: PublishingContext):
        """阶段三：处理图片"""
        for idx, image in enumerate(context.images):
            # 打开媒体库
            await provider.open_media_library()

            # 上传图片
            await provider.upload_file(image.file_path)

            # 等待上传完成
            await provider.wait_for_upload_complete()

            # 填写图片元数据
            await provider.fill_image_metadata({
                "alt": image.alt_text,
                "title": image.title,
                "caption": image.caption,
                "keywords": ",".join(image.keywords),
                "photographer": image.photographer
            })

            # 如果是第一张图片，设为特色图片
            if idx == 0:
                await provider.set_as_featured_image()

                # 裁切特色图片
                await provider.edit_image()
                for crop_size in ["thumbnail", "facebook_700_359"]:
                    await provider.crop_image(crop_size)
                    await provider.save_crop()

                await provider.confirm_featured_image()
            else:
                # 其他图片插入到内容中
                await provider.configure_image_display(
                    align="center",
                    link_to="none",
                    size="large"
                )
                await provider.insert_image_to_content()

            # 关闭媒体库
            await provider.close_media_library()

    async def _phase_set_metadata(self, provider: IPublishingProvider, context: PublishingContext):
        """阶段四：设置元数据"""
        # 添加标签
        for tag in context.metadata.tags:
            await provider.add_tag(tag)

        # 选择分类
        for category in context.metadata.categories:
            await provider.select_category(category)

        # 配置 SEO 插件
        await provider.configure_seo_plugin({
            "focus_keyword": context.article.seo.focus_keyword,
            "meta_title": context.article.seo.meta_title,
            "meta_description": context.article.seo.meta_description
        })

    async def _phase_publish(self, provider: IPublishingProvider, context: PublishingContext):
        """阶段五：发布文章"""
        if context.metadata.publish_immediately:
            await provider.click_button("publish")
            await provider.wait_for_success_message("文章已發佈")
        else:
            # 排程发布
            await provider.schedule_publish(context.metadata.publish_date)
            await provider.click_button("schedule")
            await provider.wait_for_success_message("文章已排程")

        # 获取发布后的 URL
        context.published_url = await provider.get_published_url()
```

### 2. IPublishingProvider 接口

**统一的 Provider 接口定义**:

```python
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from datetime import datetime

class IPublishingProvider(ABC):
    """
    发布提供者的抽象接口
    所有 Provider（Playwright、Computer Use、Gemini）必须实现此接口
    """

    @abstractmethod
    async def initialize(self, base_url: str, **kwargs) -> None:
        """初始化 Provider（启动浏览器、连接服务等）"""
        pass

    @abstractmethod
    async def close(self) -> None:
        """关闭 Provider 并释放资源"""
        pass

    @abstractmethod
    async def capture_screenshot(self) -> bytes:
        """捕获当前屏幕截图"""
        pass

    @abstractmethod
    async def get_cookies(self) -> List[Dict]:
        """获取当前浏览器 cookies"""
        pass

    # ==================== 导航类操作 ====================

    @abstractmethod
    async def navigate_to(self, url: str) -> None:
        """导航到指定 URL"""
        pass

    @abstractmethod
    async def navigate_to_new_post(self) -> None:
        """导航到「新增文章」页面"""
        pass

    # ==================== 元素交互操作 ====================

    @abstractmethod
    async def fill_input(self, field_name: str, value: str) -> None:
        """填充输入框（如：标题、用户名、密码）"""
        pass

    @abstractmethod
    async def fill_textarea(self, field_name: str, value: str) -> None:
        """填充文本区域（如：文章内容）"""
        pass

    @abstractmethod
    async def click_button(self, button_name: str) -> None:
        """点击按钮（如：登录、保存草稿、发布）"""
        pass

    @abstractmethod
    async def wait_for_element(self, element_name: str, timeout: int = 30) -> None:
        """等待元素出现"""
        pass

    @abstractmethod
    async def wait_for_success_message(self, message_text: str) -> None:
        """等待成功提示消息出现"""
        pass

    # ==================== 内容编辑操作 ====================

    @abstractmethod
    async def clean_html_entities(self) -> None:
        """清理内容中的 HTML 实体（如 &nbsp;）"""
        pass

    # ==================== 媒体库操作 ====================

    @abstractmethod
    async def open_media_library(self) -> None:
        """打开媒体库弹窗"""
        pass

    @abstractmethod
    async def upload_file(self, file_path: str) -> None:
        """上传文件"""
        pass

    @abstractmethod
    async def wait_for_upload_complete(self) -> None:
        """等待文件上传完成"""
        pass

    @abstractmethod
    async def fill_image_metadata(self, metadata: Dict[str, str]) -> None:
        """
        填写图片元数据

        Args:
            metadata: {
                "alt": "替代文字",
                "title": "图片标题",
                "caption": "图片说明",
                "keywords": "关键字1,关键字2",
                "photographer": "摄影师"
            }
        """
        pass

    @abstractmethod
    async def configure_image_display(
        self,
        align: str,
        link_to: str,
        size: str
    ) -> None:
        """配置图片显示设置"""
        pass

    @abstractmethod
    async def insert_image_to_content(self) -> None:
        """将图片插入到文章内容"""
        pass

    @abstractmethod
    async def close_media_library(self) -> None:
        """关闭媒体库弹窗"""
        pass

    # ==================== 特色图片操作 ====================

    @abstractmethod
    async def set_as_featured_image(self) -> None:
        """将当前选中的图片设为特色图片"""
        pass

    @abstractmethod
    async def edit_image(self) -> None:
        """进入图片编辑模式"""
        pass

    @abstractmethod
    async def crop_image(self, size_name: str) -> None:
        """
        裁切图片到指定尺寸

        Args:
            size_name: 尺寸名称（如 "thumbnail", "facebook_700_359"）
        """
        pass

    @abstractmethod
    async def save_crop(self) -> None:
        """保存裁切"""
        pass

    @abstractmethod
    async def confirm_featured_image(self) -> None:
        """确认设置特色图片"""
        pass

    # ==================== 元数据操作 ====================

    @abstractmethod
    async def add_tag(self, tag: str) -> None:
        """添加标签"""
        pass

    @abstractmethod
    async def select_category(self, category: str) -> None:
        """选择分类"""
        pass

    @abstractmethod
    async def configure_seo_plugin(self, seo_data: Dict[str, str]) -> None:
        """
        配置 SEO 插件

        Args:
            seo_data: {
                "focus_keyword": "焦点关键字",
                "meta_title": "SEO 标题",
                "meta_description": "Meta 描述"
            }
        """
        pass

    # ==================== 发布操作 ====================

    @abstractmethod
    async def schedule_publish(self, publish_date: datetime) -> None:
        """设置排程发布时间"""
        pass

    @abstractmethod
    async def get_published_url(self) -> str:
        """获取已发布文章的 URL"""
        pass
```

---

## Playwright 实现方案

### 3. PlaywrightProvider 实现

```python
from playwright.async_api import async_playwright, Page, Browser
import asyncio
from typing import Dict, List, Optional
from datetime import datetime

class PlaywrightProvider(IPublishingProvider):
    """
    基于 Playwright 的发布提供者
    使用 DOM 选择器精确控制 WordPress 后台
    """

    def __init__(self, selectors: SelectorConfig):
        """
        Args:
            selectors: 选择器配置对象（从 YAML 加载）
        """
        self.selectors = selectors
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.playwright = None

    async def initialize(self, base_url: str, **kwargs) -> None:
        """初始化 Playwright 浏览器"""
        self.playwright = await async_playwright().start()

        # 启动浏览器（优先 Chrome）
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-blink-features=AutomationControlled'
            ]
        )

        # 创建页面上下文
        context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            locale='zh-TW',
            timezone_id='Asia/Taipei'
        )

        # 如果提供了 cookies，则恢复会话
        if 'cookies' in kwargs:
            await context.add_cookies(kwargs['cookies'])

        self.page = await context.new_page()

        # 设置默认超时
        self.page.set_default_timeout(30000)  # 30 秒

        # 导航到基础 URL
        self.base_url = base_url

    async def close(self) -> None:
        """关闭浏览器"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def capture_screenshot(self) -> bytes:
        """捕获当前屏幕截图"""
        if not self.page:
            raise RuntimeError("Page not initialized")
        return await self.page.screenshot(full_page=True)

    async def get_cookies(self) -> List[Dict]:
        """获取当前浏览器 cookies"""
        if not self.page:
            raise RuntimeError("Page not initialized")
        return await self.page.context.cookies()

    # ==================== 导航类操作 ====================

    async def navigate_to(self, url: str) -> None:
        """导航到指定 URL"""
        await self.page.goto(url, wait_until='networkidle')

    async def navigate_to_new_post(self) -> None:
        """导航到「新增文章」页面"""
        # 方案一：直接导航
        await self.navigate_to(f"{self.base_url}/wp-admin/post-new.php")

        # 方案二：点击菜单（更模拟真实用户）
        # await self._click_by_selector(self.selectors.get("menu_posts"))
        # await self._click_by_selector(self.selectors.get("menu_new_post"))

        # 等待页面加载完成
        await self.wait_for_element("new_post_title")

    # ==================== 元素交互操作 ====================

    async def fill_input(self, field_name: str, value: str) -> None:
        """填充输入框"""
        selector = self.selectors.get(field_name)
        await self._fill_by_selector(selector, value)

    async def fill_textarea(self, field_name: str, value: str) -> None:
        """填充文本区域"""
        if field_name == "content":
            # WordPress 内容编辑器在 iframe 中（文字模式）
            await self._fill_by_selector(self.selectors.get("content_textarea"), value)
        else:
            selector = self.selectors.get(field_name)
            await self._fill_by_selector(selector, value)

    async def click_button(self, button_name: str) -> None:
        """点击按钮"""
        selector = self.selectors.get(button_name)
        await self._click_by_selector(selector)

    async def wait_for_element(self, element_name: str, timeout: int = 30) -> None:
        """等待元素出现"""
        selector = self.selectors.get(element_name)
        await self.page.wait_for_selector(selector, timeout=timeout * 1000)

    async def wait_for_success_message(self, message_text: str) -> None:
        """等待成功提示消息出现"""
        selector = self.selectors.get("success_message")
        element = self.page.locator(selector)
        await element.wait_for(state='visible')

        # 验证消息文本
        text = await element.text_content()
        if message_text not in text:
            raise ValueError(f"Expected message '{message_text}', got '{text}'")

    # ==================== 内容编辑操作 ====================

    async def clean_html_entities(self) -> None:
        """清理内容中的 HTML 实体"""
        selector = self.selectors.get("content_textarea")
        content = await self.page.locator(selector).input_value()

        # 清理常见的 HTML 实体
        cleaned = content.replace('&nbsp;', ' ')
        cleaned = cleaned.replace('&amp;', '&')
        cleaned = cleaned.replace('&lt;', '<')
        cleaned = cleaned.replace('&gt;', '>')

        await self._fill_by_selector(selector, cleaned)

    # ==================== 媒体库操作 ====================

    async def open_media_library(self) -> None:
        """打开媒体库弹窗"""
        await self._click_by_selector(self.selectors.get("add_media_button"))
        await self.page.wait_for_selector(self.selectors.get("media_modal"), state='visible')

    async def upload_file(self, file_path: str) -> None:
        """上传文件"""
        # 点击「上传文件」标签
        await self._click_by_selector(self.selectors.get("upload_files_tab"))

        # 等待文件选择器事件
        async with self.page.expect_file_chooser() as fc_info:
            await self._click_by_selector(self.selectors.get("select_files_button"))

        file_chooser = await fc_info.value
        await file_chooser.set_files(file_path)

    async def wait_for_upload_complete(self) -> None:
        """等待文件上传完成"""
        # 等待上传的图片被自动选中（有 .selected class）
        await self.page.wait_for_selector(
            f"{self.selectors.get('media_attachment')}.selected",
            state='visible'
        )

    async def fill_image_metadata(self, metadata: Dict[str, str]) -> None:
        """填写图片元数据"""
        # 等待右侧详细信息面板出现
        await self.page.wait_for_selector(self.selectors.get("attachment_details"), state='visible')

        # 填写各个字段
        for field, value in metadata.items():
            selector = self.selectors.get(f"image_{field}")
            if selector:
                await self._fill_by_selector(selector, value)
            else:
                logger.warning(f"No selector found for image field: {field}")

    async def configure_image_display(
        self,
        align: str,
        link_to: str,
        size: str
    ) -> None:
        """配置图片显示设置"""
        # 对齐
        align_selector = self.selectors.get("image_align_select")
        await self.page.select_option(align_selector, label=align)

        # 连结至
        link_selector = self.selectors.get("image_link_select")
        await self.page.select_option(link_selector, label=link_to)

        # 尺寸
        size_selector = self.selectors.get("image_size_select")
        await self.page.select_option(size_selector, label=size)

    async def insert_image_to_content(self) -> None:
        """将图片插入到文章内容"""
        await self._click_by_selector(self.selectors.get("insert_into_post_button"))
        await self.page.wait_for_selector(self.selectors.get("media_modal"), state='hidden')

    async def close_media_library(self) -> None:
        """关闭媒体库弹窗"""
        # 通常插入图片后会自动关闭，此方法用于异常情况
        close_button = self.selectors.get("media_modal_close")
        if await self.page.locator(close_button).is_visible():
            await self._click_by_selector(close_button)

    # ==================== 特色图片操作 ====================

    async def set_as_featured_image(self) -> None:
        """将当前选中的图片设为特色图片"""
        # 点击右侧栏的「设置特色图片」
        await self._click_by_selector(self.selectors.get("set_featured_image_link"))
        await self.page.wait_for_selector(self.selectors.get("media_modal"), state='visible')

    async def edit_image(self) -> None:
        """进入图片编辑模式"""
        await self._click_by_selector(self.selectors.get("edit_image_link"))
        await self.page.wait_for_selector(self.selectors.get("image_editor"), state='visible')

    async def crop_image(self, size_name: str) -> None:
        """裁切图片到指定尺寸"""
        # 选择裁切尺寸（如 thumbnail、facebook_700_359）
        size_selector = f'input[value="{size_name}"]'
        await self.page.locator(size_selector).click()

        # 等待裁切框出现
        await self.page.wait_for_selector('.imgareaselect-outer', state='visible')

        # 点击裁切按钮
        await self._click_by_selector(self.selectors.get("crop_button"))

    async def save_crop(self) -> None:
        """保存裁切"""
        await self._click_by_selector(self.selectors.get("save_crop_button"))

        # 等待 AJAX 请求完成
        await self.page.wait_for_response(
            lambda resp: 'admin-ajax.php' in resp.url and resp.status == 200
        )

    async def confirm_featured_image(self) -> None:
        """确认设置特色图片"""
        await self._click_by_selector(self.selectors.get("set_featured_image_button"))
        await self.page.wait_for_selector(self.selectors.get("media_modal"), state='hidden')

        # 验证特色图片已设置（右侧栏显示缩略图）
        await self.page.wait_for_selector(
            self.selectors.get("featured_image_thumbnail"),
            state='visible'
        )

    # ==================== 元数据操作 ====================

    async def add_tag(self, tag: str) -> None:
        """添加标签"""
        # 输入标签
        await self._fill_by_selector(self.selectors.get("new_tag_input"), tag)

        # 点击「新增」按钮
        await self._click_by_selector(self.selectors.get("add_tag_button"))

        # 等待标签出现在列表中
        tag_list = self.page.locator(self.selectors.get("tag_checklist"))
        await tag_list.locator(f'text="{tag}"').wait_for(state='visible')

    async def select_category(self, category: str) -> None:
        """选择分类"""
        # 使用包含文本的标签定位复选框
        checkbox_selector = f'label:has-text("{category}") input[type="checkbox"]'
        await self.page.locator(checkbox_selector).check()

    async def configure_seo_plugin(self, seo_data: Dict[str, str]) -> None:
        """配置 SEO 插件（Yoast SEO）"""
        # 滚动到 Yoast SEO 区域
        yoast_section = self.page.locator(self.selectors.get("yoast_section"))
        await yoast_section.scroll_into_view_if_needed()

        # 填写焦点关键字
        await self._fill_by_selector(
            self.selectors.get("yoast_focus_keyword"),
            seo_data["focus_keyword"]
        )

        # 点击「编辑摘要」（如果需要）
        edit_snippet = self.selectors.get("yoast_edit_snippet")
        if await self.page.locator(edit_snippet).is_visible():
            await self._click_by_selector(edit_snippet)

        # 填写 SEO 标题
        await self._fill_by_selector(
            self.selectors.get("yoast_meta_title"),
            seo_data["meta_title"]
        )

        # 填写 Meta 描述
        await self._fill_by_selector(
            self.selectors.get("yoast_meta_description"),
            seo_data["meta_description"]
        )

    # ==================== 发布操作 ====================

    async def schedule_publish(self, publish_date: datetime) -> None:
        """设置排程发布时间"""
        # 点击「编辑」发布时间
        await self._click_by_selector(self.selectors.get("edit_timestamp_link"))

        # 填写日期时间
        await self.page.select_option(self.selectors.get("publish_month"), str(publish_date.month))
        await self._fill_by_selector(self.selectors.get("publish_day"), str(publish_date.day))
        await self._fill_by_selector(self.selectors.get("publish_year"), str(publish_date.year))
        await self._fill_by_selector(self.selectors.get("publish_hour"), str(publish_date.hour))
        await self._fill_by_selector(self.selectors.get("publish_minute"), str(publish_date.minute))

        # 点击「确定」
        await self._click_by_selector(self.selectors.get("save_timestamp_link"))

    async def get_published_url(self) -> str:
        """获取已发布文章的 URL"""
        # 从成功消息中提取链接
        message_link = self.page.locator(f"{self.selectors.get('success_message')} a")
        url = await message_link.get_attribute('href')
        return url

    # ==================== 辅助方法 ====================

    async def _click_by_selector(self, selector: str) -> None:
        """通过选择器点击元素（处理多选择器）"""
        selectors = selector if isinstance(selector, list) else [selector]

        for sel in selectors:
            try:
                element = self.page.locator(sel).first
                if await element.is_visible(timeout=5000):
                    await element.click()
                    return
            except Exception:
                continue

        raise ElementNotFoundError(f"Could not find clickable element with selectors: {selectors}")

    async def _fill_by_selector(self, selector: str, value: str) -> None:
        """通过选择器填充元素（处理多选择器）"""
        selectors = selector if isinstance(selector, list) else [selector]

        for sel in selectors:
            try:
                element = self.page.locator(sel).first
                if await element.is_visible(timeout=5000):
                    await element.fill(value)
                    return
            except Exception:
                continue

        raise ElementNotFoundError(f"Could not find fillable element with selectors: {selectors}")


class ElementNotFoundError(Exception):
    """元素未找到错误"""
    pass
```

### 选择器配置文件

**config/selectors.yaml**:

```yaml
# WordPress 后台选择器配置
# 支持多选择器（优先级从上到下）

# ==================== 菜单导航 ====================
menu_posts:
  - "#menu-posts > a"
  - "a[href='edit.php']"

menu_new_post:
  - "#menu-posts ul > li > a:has-text('新增文章')"
  - "a[href='post-new.php']"

# ==================== 文章编辑器 ====================
new_post_title:
  - "#title"
  - "input[name='post_title']"

content_text_mode_button:
  - "#content-html"
  - "a.wp-switch-editor[data-mode='html']"

content_visual_mode_button:
  - "#content-tmce"
  - "a.wp-switch-editor[data-mode='tmce']"

content_textarea:
  - "#content"
  - "textarea[name='content']"

content_iframe:
  - "#content_ifr"
  - "iframe.wp-editor-area"

# ==================== 按钮 ====================
save_draft:
  - "#save-post"
  - "input[name='save']"

publish:
  - "#publish"
  - "input[name='publish']"

preview:
  - "#post-preview"
  - "a#preview-action"

# ==================== 媒体库 ====================
add_media_button:
  - "#insert-media-button"
  - "button.insert-media"

media_modal:
  - ".media-modal"
  - ".media-frame"

upload_files_tab:
  - "button:has-text('上傳檔案')"
  - ".media-menu-item:has-text('上傳檔案')"

select_files_button:
  - "button:has-text('選擇檔案')"
  - ".browser button.button"

media_attachment:
  - ".media-modal .attachment"
  - "li.attachment"

attachment_details:
  - ".media-sidebar"
  - ".attachment-details"

# 图片元数据字段
image_alt:
  - ".media-modal .setting[data-setting='alt'] input"
  - "input[id*='alt-text']"

image_title:
  - ".media-modal .setting[data-setting='title'] input"
  - "input[id*='attachment-title']"

image_caption:
  - ".media-modal .setting[data-setting='caption'] textarea"
  - "textarea[id*='attachment-caption']"

image_keywords:
  - ".media-modal input[id*='keywords']"
  - "input[name='attachments[keywords]']"

image_photographer:
  - ".media-modal input[id*='photographer']"
  - "input[name='attachments[photographer]']"

# 图片显示设置
image_align_select:
  - ".media-modal .setting[data-setting='align'] select"

image_link_select:
  - ".media-modal .setting[data-setting='link'] select"

image_size_select:
  - ".media-modal .setting[data-setting='size'] select"

insert_into_post_button:
  - ".media-modal button.media-button-insert"
  - "button:has-text('插入至文章')"

media_modal_close:
  - ".media-modal button.media-modal-close"

# ==================== 特色图片 ====================
set_featured_image_link:
  - "#set-post-thumbnail"
  - "a[href='#set-post-thumbnail']"

set_featured_image_button:
  - ".media-modal button.media-button-select"
  - "button:has-text('設定特色圖片')"

featured_image_thumbnail:
  - "#postimagediv .inside img"

edit_image_link:
  - ".media-modal a.edit-attachment"
  - "button:has-text('編輯圖片')"

image_editor:
  - "#image-preview"
  - ".imgedit-wrap"

crop_button:
  - "button[aria-label='裁切']"
  - ".imgedit-crop"

save_crop_button:
  - "input[value='儲存']"
  - ".imgedit-submit-btn"

# ==================== 标签和分类 ====================
new_tag_input:
  - "#new-tag-post_tag"
  - "input.newtag"

add_tag_button:
  - "input.button[value='新增'][aria-label='新增標籤']"
  - ".tagsdiv input.button"

tag_checklist:
  - ".tagchecklist"

# ==================== SEO 插件（Yoast SEO） ====================
yoast_section:
  - "#wpseo_meta"
  - ".yoast-seo-metabox"

yoast_focus_keyword:
  - "#yoast-google-preview-focus-keyword"
  - "input[name='yoast_wpseo_focuskw']"

yoast_edit_snippet:
  - ".snippet-editor__button"
  - "button:has-text('編輯摘要')"

yoast_meta_title:
  - "#yoast-google-preview-title"
  - "input[name='yoast_wpseo_title']"

yoast_meta_description:
  - "#yoast-google-preview-description"
  - "textarea[name='yoast_wpseo_metadesc']"

# ==================== 发布时间 ====================
edit_timestamp_link:
  - "a[href='#edit_timestamp']"

publish_month:
  - "#mm"

publish_day:
  - "#jj"

publish_year:
  - "#aa"

publish_hour:
  - "#hh"

publish_minute:
  - "#mn"

save_timestamp_link:
  - "a.save-timestamp"

# ==================== 消息提示 ====================
success_message:
  - "#message.updated"
  - ".notice.notice-success"

error_message:
  - "#message.error"
  - ".notice.notice-error"

# ==================== 其他 ====================
dashboard:
  - "#dashboard-widgets"
  - ".wrap h1:has-text('儀表板')"
```

---

## Computer Use 实现方案

### 4. ComputerUseProvider 实现

```python
import anthropic
from typing import Dict, List, Optional
from datetime import datetime
import base64
import io
from PIL import Image

class ComputerUseProvider(IPublishingProvider):
    """
    基于 Anthropic Computer Use 的发布提供者
    使用 AI 视觉理解和自然语言指令控制浏览器
    """

    def __init__(
        self,
        api_key: str,
        instructions_template: InstructionTemplate
    ):
        """
        Args:
            api_key: Anthropic API Key
            instructions_template: 指令模板对象
        """
        self.client = anthropic.Anthropic(api_key=api_key)
        self.instructions = instructions_template
        self.session_id = None
        self.conversation_history = []

    async def initialize(self, base_url: str, **kwargs) -> None:
        """初始化 Computer Use 会话"""
        self.base_url = base_url
        self.session_id = self._generate_session_id()

        # 如果提供了 cookies，记录下来（Computer Use 会尝试复用会话）
        if 'cookies' in kwargs:
            self.cookies = kwargs['cookies']

    async def close(self) -> None:
        """关闭会话"""
        # Computer Use 无需显式关闭浏览器（由 Anthropic 管理）
        self.conversation_history = []

    async def capture_screenshot(self) -> bytes:
        """捕获当前屏幕截图"""
        # 通过 Computer Use API 获取当前屏幕
        response = await self._execute_instruction("截取当前屏幕截图")
        return response.screenshot

    async def get_cookies(self) -> List[Dict]:
        """获取当前浏览器 cookies"""
        # Computer Use 暂不支持直接获取 cookies，返回空列表
        return []

    # ==================== 导航类操作 ====================

    async def navigate_to(self, url: str) -> None:
        """导航到指定 URL"""
        instruction = f"在瀏覽器地址欄輸入 {url} 並按下 Enter，等待頁面載入完成。"
        await self._execute_instruction(instruction)

    async def navigate_to_new_post(self) -> None:
        """导航到「新增文章」页面"""
        instruction = self.instructions.get("navigate_to_new_post")
        await self._execute_instruction(instruction)

    # ==================== 元素交互操作 ====================

    async def fill_input(self, field_name: str, value: str) -> None:
        """填充输入框"""
        instruction = self.instructions.get(f"fill_{field_name}", value=value)
        await self._execute_instruction(instruction)

    async def fill_textarea(self, field_name: str, value: str) -> None:
        """填充文本区域"""
        if field_name == "content":
            instruction = self.instructions.get("fill_content", content=value)
        else:
            instruction = self.instructions.get(f"fill_{field_name}", value=value)

        await self._execute_instruction(instruction)

    async def click_button(self, button_name: str) -> None:
        """点击按钮"""
        instruction = self.instructions.get(f"click_{button_name}")
        await self._execute_instruction(instruction)

    async def wait_for_element(self, element_name: str, timeout: int = 30) -> None:
        """等待元素出现"""
        instruction = self.instructions.get(f"wait_for_{element_name}", timeout=timeout)
        await self._execute_instruction(instruction)

    async def wait_for_success_message(self, message_text: str) -> None:
        """等待成功提示消息出现"""
        instruction = f"等待頁面上出現包含文字『{message_text}』的成功提示消息。"
        await self._execute_instruction(instruction)

    # ==================== 内容编辑操作 ====================

    async def clean_html_entities(self) -> None:
        """清理内容中的 HTML 实体"""
        instruction = self.instructions.get("clean_html_entities")
        await self._execute_instruction(instruction)

    # ==================== 媒体库操作 ====================

    async def open_media_library(self) -> None:
        """打开媒体库弹窗"""
        instruction = self.instructions.get("open_media_library")
        await self._execute_instruction(instruction)

    async def upload_file(self, file_path: str) -> None:
        """上传文件"""
        instruction = self.instructions.get("upload_file", file_path=file_path)
        await self._execute_instruction(instruction)

    async def wait_for_upload_complete(self) -> None:
        """等待文件上传完成"""
        instruction = "等待圖片上傳完成，確認看到圖片縮圖並且進度條消失。"
        await self._execute_instruction(instruction)

    async def fill_image_metadata(self, metadata: Dict[str, str]) -> None:
        """填写图片元数据"""
        instruction = self.instructions.get("fill_image_metadata", **metadata)
        await self._execute_instruction(instruction)

    async def configure_image_display(
        self,
        align: str,
        link_to: str,
        size: str
    ) -> None:
        """配置图片显示设置"""
        instruction = self.instructions.get(
            "configure_image_display",
            align=align,
            link_to=link_to,
            size=size
        )
        await self._execute_instruction(instruction)

    async def insert_image_to_content(self) -> None:
        """将图片插入到文章内容"""
        instruction = self.instructions.get("insert_image_to_content")
        await self._execute_instruction(instruction)

    async def close_media_library(self) -> None:
        """关闭媒体库弹窗"""
        instruction = "如果媒體庫彈窗仍然打開，點擊關閉按鈕。"
        await self._execute_instruction(instruction)

    # ==================== 特色图片操作 ====================

    async def set_as_featured_image(self) -> None:
        """将当前选中的图片设为特色图片"""
        instruction = self.instructions.get("set_as_featured_image")
        await self._execute_instruction(instruction)

    async def edit_image(self) -> None:
        """进入图片编辑模式"""
        instruction = self.instructions.get("edit_image")
        await self._execute_instruction(instruction)

    async def crop_image(self, size_name: str) -> None:
        """裁切图片到指定尺寸"""
        instruction = self.instructions.get("crop_image", size_name=size_name)
        await self._execute_instruction(instruction)

    async def save_crop(self) -> None:
        """保存裁切"""
        instruction = self.instructions.get("save_crop")
        await self._execute_instruction(instruction)

    async def confirm_featured_image(self) -> None:
        """确认设置特色图片"""
        instruction = self.instructions.get("confirm_featured_image")
        await self._execute_instruction(instruction)

    # ==================== 元数据操作 ====================

    async def add_tag(self, tag: str) -> None:
        """添加标签"""
        instruction = self.instructions.get("add_tag", tag=tag)
        await self._execute_instruction(instruction)

    async def select_category(self, category: str) -> None:
        """选择分类"""
        instruction = self.instructions.get("select_category", category=category)
        await self._execute_instruction(instruction)

    async def configure_seo_plugin(self, seo_data: Dict[str, str]) -> None:
        """配置 SEO 插件"""
        instruction = self.instructions.get("configure_seo_plugin", **seo_data)
        await self._execute_instruction(instruction)

    # ==================== 发布操作 ====================

    async def schedule_publish(self, publish_date: datetime) -> None:
        """设置排程发布时间"""
        instruction = self.instructions.get(
            "schedule_publish",
            month=publish_date.month,
            day=publish_date.day,
            year=publish_date.year,
            hour=publish_date.hour,
            minute=publish_date.minute
        )
        await self._execute_instruction(instruction)

    async def get_published_url(self) -> str:
        """获取已发布文章的 URL"""
        instruction = "找到頁面上的成功消息中包含的文章連結，複製該 URL。"
        response = await self._execute_instruction(instruction)

        # 从响应中提取 URL（需要解析 Computer Use 的返回）
        return response.extracted_url

    # ==================== 核心执行方法 ====================

    async def _execute_instruction(self, instruction: str, **kwargs) -> ComputerUseResponse:
        """
        执行 Computer Use 指令

        Args:
            instruction: 自然语言指令

        Returns:
            ComputerUseResponse: 包含执行结果、截图等
        """
        # 构建消息
        message = {
            "role": "user",
            "content": instruction
        }

        self.conversation_history.append(message)

        # 调用 Anthropic Computer Use API
        response = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",  # 支持 Computer Use 的模型
            max_tokens=1024,
            tools=[
                {
                    "type": "computer_20241022",
                    "name": "computer",
                    "display_width_px": 1920,
                    "display_height_px": 1080,
                }
            ],
            messages=self.conversation_history
        )

        # 提取工具调用结果
        for block in response.content:
            if block.type == "tool_use" and block.name == "computer":
                # 记录响应到对话历史
                assistant_message = {
                    "role": "assistant",
                    "content": response.content
                }
                self.conversation_history.append(assistant_message)

                # 解析结果
                result = ComputerUseResponse(
                    success=True,
                    screenshot=block.output.get("screenshot"),
                    text_output=block.output.get("text"),
                    error=None
                )

                return result

        # 如果没有工具调用，可能是错误
        raise ComputerUseError(f"No computer tool use in response: {response}")

    def _generate_session_id(self) -> str:
        """生成会话 ID"""
        import uuid
        return str(uuid.uuid4())


class ComputerUseResponse:
    """Computer Use 执行响应"""

    def __init__(self, success: bool, screenshot: bytes, text_output: str, error: Optional[str]):
        self.success = success
        self.screenshot = screenshot
        self.text_output = text_output
        self.error = error
        self.extracted_url = self._extract_url(text_output)

    def _extract_url(self, text: str) -> Optional[str]:
        """从文本中提取 URL"""
        import re
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        match = re.search(url_pattern, text)
        return match.group(0) if match else None


class ComputerUseError(Exception):
    """Computer Use 执行错误"""
    pass
```

### Computer Use 指令模板

**config/instructions.yaml**:

```yaml
# Computer Use 自然语言指令模板
# 使用 Jinja2 模板语法

navigate_to_new_post: |
  找到左側選單中帶有圖釘圖示且標籤為『文章』的項目，點擊它。
  在展開的子選單中,找到並點擊標籤為『新增文章』的連結。
  等待頁面載入完成，確認頁面頂部出現文字『新增文章』。

fill_title: |
  找到標籤為『新增標題』或 ID 為 'title' 的大型文字輸入框。
  在此輸入框中輸入以下文字：『{{ value }}』。
  確認輸入框中已顯示輸入的標題文字。

fill_content: |
  找到主要內容編輯器右上方的『文字』(Text) 分頁標籤，點擊它。
  在主要內容編輯器的大型文字區域中，貼上以下內容：
  ---
  {{ content }}
  ---
  確認文字區域中已顯示貼上的內容。

clean_html_entities: |
  在『文字』編輯模式的內容區域中，查找並刪除所有的『&nbsp;』字串。
  如果有其他多餘的 HTML 標籤或實體字符，也一併清理。

open_media_library: |
  找到主要內容編輯器左上方的標籤為『新增媒體』的按鈕，點擊它。
  等待一個標題為『插入媒體』的彈出視窗出現。

upload_file: |
  在『插入媒體』視窗中，點擊標籤為『上傳檔案』的分頁。
  點擊標籤為『選擇檔案』的按鈕，在檔案選擇器中選擇圖片檔案『{{ file_path }}』。
  或者，直接將圖片檔案拖曳到標有『請將檔案拖曳到這裡上傳』的區域。

fill_image_metadata: |
  在上傳完成後，確保圖片已被選中（有藍色邊框）。
  在視窗右側的『附件詳細資料』區域：
  - 找到標籤為『替代文字』的輸入框，填入：『{{ alt }}』。
  - 找到標籤為『標題』的輸入框，填入：『{{ title }}』。
  - 找到標籤為『說明』的文字區域，填入：『{{ caption }}』。
  - 找到標籤為『關鍵字』的輸入框，填入：『{{ keywords }}』。
  - 找到標籤為『攝影師』的輸入框，填入：『{{ photographer }}』。
  確認所有欄位都已填寫。

configure_image_display: |
  在視窗右側下方的『附件顯示設定』區域：
  - 找到標籤為『對齊』的下拉選單，選擇『{{ align }}』。
  - 找到標籤為『連結至』的下拉選單，選擇『{{ link_to }}』。
  - 找到標籤為『尺寸』的下拉選單，選擇『{{ size }}』。

insert_image_to_content: |
  點擊『插入媒體』視窗右下角的標籤為『插入至文章』的按鈕。
  確認彈出視窗已關閉，且圖片已出現在主要內容編輯器的游標位置。

set_as_featured_image: |
  找到頁面右側標題為『特色圖片』的區塊。
  點擊該區塊內標籤為『設定特色圖片』的連結或按鈕。
  等待一個類似『插入媒體』的彈出視窗出現。

edit_image: |
  在圖片預覽下方，找到並點擊標籤為『編輯圖片』的連結。
  等待進入圖片編輯介面。

crop_image: |
  在圖片編輯介面右側，找到標籤為『縮圖設定』或類似名稱的區塊。
  找到標籤為『{{ size_name }}』的選項，點擊它。
  調整圖片上出現的裁切框，確保主要內容（例如人物面部、重要元素）完整出現在框內。
  點擊裁切按鈕（通常是一個方形圖示）。

save_crop: |
  點擊『儲存』或『更新』按鈕。
  等待裁切操作完成並保存。

confirm_featured_image: |
  返回到選擇特色圖片的視窗（如果進行了編輯）。
  確保目標圖片仍被選中。
  點擊視窗右下角的標籤為『設定特色圖片』的按鈕。
  確認彈出視窗已關閉，且右側『特色圖片』區塊已顯示選中的圖片縮圖。

add_tag: |
  找到頁面右側標題為『標籤』的區塊。
  找到該區塊內標籤為『新增標籤』的文字輸入框。
  在此輸入框中輸入標籤文字：『{{ tag }}』。
  點擊輸入框旁邊標籤為『新增』的按鈕。
  確認輸入的標籤已出現在輸入框下方或標籤列表中。

select_category: |
  找到頁面右側標題為『分類』的區塊。
  在分類列表中，找到並勾選名稱為『{{ category }}』的核取方塊。
  確認該分類旁邊的核取方塊已被勾選。

configure_seo_plugin: |
  向下滾動頁面，找到標題包含『Yoast SEO』的區塊。
  - 找到標籤為『焦點關鍵字』的輸入框，填入：『{{ focus_keyword }}』。
  - 找到標籤為『SEO 標題』的輸入框（可能需要點擊『編輯摘要』按鈕才出現），填入：『{{ meta_title }}』。
  - 找到標籤為『Meta 描述』的文字區域，填入：『{{ meta_description }}』。
  確認各欄位已填入內容。

click_save_draft: |
  找到頁面右上角『發表』區塊中的標籤為『儲存為草稿』的按鈕，點擊它。
  等待頁面提示『文章草稿已更新』或類似訊息。

click_publish: |
  找到頁面右上角『發表』區塊中藍色的『發表』按鈕，點擊它。
  等待頁面提示『文章已發佈』或類似訊息。

schedule_publish: |
  找到頁面右上角『發表』區塊。
  點擊『立即發表』旁邊的『編輯』連結。
  在彈出的日期時間選擇器中：
  - 選擇月份：{{ month }}
  - 選擇日期：{{ day }}
  - 選擇年份：{{ year }}
  - 選擇小時：{{ hour }}
  - 選擇分鐘：{{ minute }}
  點擊『確定』按鈕。
  點擊現在標籤為『排程』的按鈕（原本的『發表』按鈕）。
  等待頁面提示『文章已排程』或類似訊息。
```

---

## 降级机制

### 降级决策流程图

```
┌─────────────────────────┐
│  Execute Step (Playwright) │
└─────────────────────────┘
              │
              ▼
        [Success?]
         /        \
       Yes         No
        │           │
        │           ▼
        │    ┌──────────────┐
        │    │ Retry Count?  │
        │    └──────────────┘
        │      /          \
        │    < 3          ≥ 3
        │     │            │
        │     │            ▼
        │     │     ┌──────────────────┐
        │     │     │ Fallback Available?│
        │     │     └──────────────────┘
        │     │       /              \
        │     │     Yes               No
        │     │      │                 │
        │     │      ▼                 ▼
        │     │ ┌─────────────┐  ┌──────────┐
        │     │ │Switch to CU │  │  Raise    │
        │     │ └─────────────┘  │  Error   │
        │     │      │            └──────────┘
        │     │      ▼
        │     │ ┌─────────────────────┐
        │     │ │ Execute Step (CU)    │
        │     │ └─────────────────────┘
        │     │      │
        │     └──────┘
        │
        ▼
  [Continue Next Step]
```

### 降级策略配置

**config/fallback_config.yaml**:

```yaml
# 降级策略配置

# 主 Provider
primary_provider: "playwright"

# 备用 Provider
fallback_provider: "computer_use"

# 重试配置
retry:
  max_retries: 3
  retry_delay: 2  # 秒

# 超时配置（秒）
timeouts:
  navigation: 30
  element_wait: 30
  upload: 120
  ajax: 60

# 触发降级的错误类型
trigger_errors:
  - "ElementNotFoundError"
  - "TimeoutError"
  - "StaleElementReferenceError"

# 不触发降级的错误（直接失败）
fatal_errors:
  - "NetworkError"  # 网络错误，切换 Provider 也无法解决
  - "AuthenticationError"  # 认证错误
  - "InsufficientPermissionsError"  # 权限不足

# 特定步骤的降级配置
step_specific:
  crop_image:
    prefer_provider: "computer_use"  # 图片裁切优先使用 Computer Use
    max_retries: 1  # 只尝试 1 次 Playwright
  fill_content:
    max_retries: 2  # 内容填充最多重试 2 次
```

---

## 数据流设计

### 发布任务数据模型

```python
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

@dataclass
class Article:
    """文章数据"""
    id: int
    title: str
    content_html: str
    excerpt: Optional[str]
    seo: 'SEOData'

@dataclass
class SEOData:
    """SEO 数据"""
    focus_keyword: str
    meta_title: str
    meta_description: str
    primary_keywords: List[str]
    secondary_keywords: List[str]

@dataclass
class ImageAsset:
    """图片资源"""
    file_path: str
    alt_text: str
    title: str
    caption: str
    keywords: List[str]
    photographer: str
    is_featured: bool = False

@dataclass
class ArticleMetadata:
    """文章元数据"""
    tags: List[str]
    categories: List[str]
    publish_immediately: bool = True
    publish_date: Optional[datetime] = None
    status: str = "draft"  # draft, publish, scheduled

@dataclass
class PublishingContext:
    """发布上下文（在整个发布流程中传递）"""
    task_id: str
    article: Article
    images: List[ImageAsset]
    metadata: ArticleMetadata
    wordpress_url: str
    credentials: 'WordPressCredentials'
    browser_cookies: Optional[List[Dict]] = None
    published_url: Optional[str] = None

@dataclass
class WordPressCredentials:
    """WordPress 凭证"""
    username: str
    password: str

@dataclass
class PublishResult:
    """发布结果"""
    success: bool
    task_id: str
    url: Optional[str]
    audit_trail: 'AuditTrail'
    error: Optional[str] = None
```

---

## 错误处理

### 错误分类

1. **可恢复错误**（触发重试）:
   - 元素未找到
   - 操作超时
   - 元素状态异常（如未启用）

2. **需降级错误**（切换 Provider）:
   - 连续重试失败
   - 页面结构变化
   - 非预期的弹窗

3. **致命错误**（直接失败）:
   - 网络断开
   - 认证失败
   - 权限不足
   - 文件不存在

### 错误日志格式

```json
{
  "task_id": "publish-12345",
  "step_name": "upload_image",
  "error_type": "ElementNotFoundError",
  "error_message": "Could not find element with selector: .media-modal",
  "timestamp": "2025-10-27T10:32:15Z",
  "retry_count": 2,
  "provider": "playwright",
  "screenshot": "/logs/task-12345/error-step-upload_image-retry-2.png",
  "stack_trace": "..."
}
```

---

## 配置管理

### 配置文件结构

```
config/
├── selectors.yaml          # Playwright 选择器配置
├── instructions.yaml       # Computer Use 指令模板
├── fallback_config.yaml    # 降级策略配置
├── wordpress_sites.yaml    # WordPress 站点配置
└── providers.yaml          # Provider 配置
```

### WordPress 站点配置

**config/wordpress_sites.yaml**:

```yaml
sites:
  - id: "site_001"
    name: "主站"
    url: "https://example.com"
    admin_url: "https://example.com/wp-admin"
    credentials:
      username: "${WP_USERNAME}"
      password: "${WP_PASSWORD}"
    editor_type: "classic"  # classic | gutenberg
    seo_plugin: "yoast"  # yoast | rank_math | all_in_one
    theme: "astra"
    active_plugins:
      - "yoast-seo"
      - "classic-editor"
      - "wp-optimize"
    image_sizes:
      thumbnail: "150x150"
      medium: "300x300"
      large: "600x390"
      facebook: "700x359"
    upload_max_size: "10MB"

  - id: "site_002"
    name: "測試站"
    url: "https://test.example.com"
    admin_url: "https://test.example.com/wp-admin"
    credentials:
      username: "${WP_TEST_USERNAME}"
      password: "${WP_TEST_PASSWORD}"
    editor_type: "gutenberg"
    seo_plugin: "rank_math"
    theme: "generatepress"
    active_plugins:
      - "rank-math"
      - "gutenberg"
    image_sizes:
      thumbnail: "150x150"
      medium: "400x400"
      large: "800x600"
    upload_max_size: "5MB"
```

---

## 日志与监控

### 日志系统设计

```python
import logging
from pathlib import Path
from datetime import datetime
import json

class AuditLogger:
    """审计日志记录器"""

    def __init__(self, log_dir: str = "/logs"):
        self.log_dir = Path(log_dir)
        self.logger = logging.getLogger("publishing_audit")

    def log_phase_success(self, task_id: str, phase_name: str, retry_count: int):
        """记录阶段成功"""
        self._write_log(task_id, {
            "event": "phase_success",
            "phase": phase_name,
            "retry_count": retry_count,
            "timestamp": datetime.utcnow().isoformat()
        })

    def log_phase_failure(self, task_id: str, phase_name: str, retry_count: int, error: str):
        """记录阶段失败"""
        self._write_log(task_id, {
            "event": "phase_failure",
            "phase": phase_name,
            "retry_count": retry_count,
            "error": error,
            "timestamp": datetime.utcnow().isoformat()
        })

    def log_provider_switch(self, task_id: str, new_provider: str):
        """记录 Provider 切换"""
        self._write_log(task_id, {
            "event": "provider_switch",
            "new_provider": new_provider,
            "timestamp": datetime.utcnow().isoformat()
        })

    def save_screenshot(self, task_id: str, step_name: str, screenshot: bytes):
        """保存截图"""
        task_log_dir = self.log_dir / task_id
        task_log_dir.mkdir(parents=True, exist_ok=True)

        screenshot_path = task_log_dir / f"{step_name}.png"
        screenshot_path.write_bytes(screenshot)

        self._write_log(task_id, {
            "event": "screenshot_saved",
            "step_name": step_name,
            "path": str(screenshot_path),
            "timestamp": datetime.utcnow().isoformat()
        })

    def get_trail(self, task_id: str) -> dict:
        """获取完整审计追踪"""
        log_file = self.log_dir / task_id / "audit.jsonl"
        if not log_file.exists():
            return {}

        logs = []
        with open(log_file, 'r') as f:
            for line in f:
                logs.append(json.loads(line))

        return {
            "task_id": task_id,
            "events": logs,
            "summary": self._generate_summary(logs)
        }

    def _write_log(self, task_id: str, log_entry: dict):
        """写入日志"""
        task_log_dir = self.log_dir / task_id
        task_log_dir.mkdir(parents=True, exist_ok=True)

        log_file = task_log_dir / "audit.jsonl"
        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')

    def _generate_summary(self, logs: List[dict]) -> dict:
        """生成摘要"""
        total_phases = len([log for log in logs if log['event'] == 'phase_success'])
        failures = len([log for log in logs if log['event'] == 'phase_failure'])
        screenshots = len([log for log in logs if log['event'] == 'screenshot_saved'])
        provider_switches = len([log for log in logs if log['event'] == 'provider_switch'])

        return {
            "total_phases": total_phases,
            "failures": failures,
            "screenshots": screenshots,
            "provider_switches": provider_switches
        }
```

### 监控指标

```python
from prometheus_client import Counter, Histogram, Gauge

# 发布任务计数器
publish_tasks_total = Counter(
    'wordpress_publish_tasks_total',
    'Total number of publishing tasks',
    ['status', 'provider']
)

# 发布任务耗时
publish_task_duration = Histogram(
    'wordpress_publish_task_duration_seconds',
    'Time spent publishing articles',
    ['provider']
)

# 当前进行中的任务
publish_tasks_in_progress = Gauge(
    'wordpress_publish_tasks_in_progress',
    'Number of publishing tasks currently in progress'
)

# 降级事件计数器
fallback_events_total = Counter(
    'wordpress_publish_fallback_events_total',
    'Total number of fallback events',
    ['from_provider', 'to_provider', 'reason']
)

# 步骤失败计数器
step_failures_total = Counter(
    'wordpress_publish_step_failures_total',
    'Total number of step failures',
    ['step_name', 'error_type', 'provider']
)
```

---

## 部署方案

### Docker 容器化

**Dockerfile**:

```dockerfile
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

WORKDIR /app

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 安装 Playwright 浏览器
RUN playwright install chromium

# 复制应用代码
COPY . .

# 创建日志目录
RUN mkdir -p /logs

# 暴露 API 端口
EXPOSE 8000

# 启动服务
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**docker-compose.yml**:

```yaml
version: '3.8'

services:
  wordpress-publisher:
    build: .
    container_name: wordpress-publisher
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - WP_USERNAME=${WP_USERNAME}
      - WP_PASSWORD=${WP_PASSWORD}
    volumes:
      - ./logs:/logs
      - ./config:/app/config
      - ./uploads:/app/uploads
    ports:
      - "8000:8000"
    networks:
      - cms-network
    restart: unless-stopped

networks:
  cms-network:
    external: true
```

---

## 测试策略

### 单元测试

测试各 Provider 的独立方法：

```python
import pytest
from unittest.mock import Mock, AsyncMock

@pytest.mark.asyncio
async def test_playwright_fill_input():
    """测试 Playwright 填充输入框"""
    # 创建 Mock Page
    mock_page = Mock()
    mock_page.locator = Mock(return_value=Mock(fill=AsyncMock()))

    # 创建 Provider
    provider = PlaywrightProvider(selectors=Mock())
    provider.page = mock_page

    # 执行测试
    await provider.fill_input("title", "测试标题")

    # 验证调用
    mock_page.locator.assert_called()
```

### 集成测试

测试完整的发布流程：

```python
@pytest.mark.asyncio
async def test_full_publishing_workflow():
    """测试完整的发布流程"""
    # 准备测试数据
    article = Article(
        id=1,
        title="测试文章",
        content_html="<p>这是测试内容</p>",
        excerpt="摘要",
        seo=SEOData(
            focus_keyword="测试",
            meta_title="测试文章 | 网站名称",
            meta_description="这是一篇测试文章"
        )
    )

    images = [
        ImageAsset(
            file_path="/tmp/test-image.jpg",
            alt_text="测试图片",
            title="测试",
            caption="图片说明",
            keywords=["测试", "图片"],
            photographer="测试摄影师",
            is_featured=True
        )
    ]

    metadata = ArticleMetadata(
        tags=["测试", "自动化"],
        categories=["技术"],
        publish_immediately=False,
        publish_date=datetime(2025, 12, 31, 14, 30)
    )

    # 创建 Orchestrator
    orchestrator = PublishingOrchestrator(
        primary_provider=PlaywrightProvider(selectors_config),
        fallback_provider=ComputerUseProvider(api_key, instructions_config)
    )

    # 执行发布
    result = await orchestrator.publish_article(article, images, metadata)

    # 验证结果
    assert result.success == True
    assert result.url is not None
    assert "example.com" in result.url
```

### End-to-End 测试

在真实 WordPress 环境中测试：

```python
@pytest.mark.e2e
@pytest.mark.asyncio
async def test_publish_to_real_wordpress():
    """在真实 WordPress 环境中测试发布"""
    # 需要配置测试环境的 WordPress 站点
    # 使用测试数据发布文章
    # 验证文章确实出现在 WordPress 中
    pass
```

---

## 性能优化

### 并发处理

```python
import asyncio
from typing import List

class BatchPublisher:
    """批量发布器"""

    async def publish_batch(
        self,
        articles: List[Tuple[Article, List[ImageAsset], ArticleMetadata]],
        max_concurrent: int = 3
    ) -> List[PublishResult]:
        """
        批量发布文章

        Args:
            articles: 文章列表（每个元素是一个元组）
            max_concurrent: 最大并发数

        Returns:
            发布结果列表
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def publish_with_semaphore(article_data):
            async with semaphore:
                orchestrator = PublishingOrchestrator(...)
                return await orchestrator.publish_article(*article_data)

        tasks = [publish_with_semaphore(article_data) for article_data in articles]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        return results
```

### 图片预处理

```python
from PIL import Image
import io

def optimize_image(image_path: str, max_size_mb: int = 2) -> str:
    """优化图片大小"""
    img = Image.open(image_path)

    # 压缩质量
    quality = 85

    # 保存到临时文件
    output_path = f"/tmp/{Path(image_path).stem}_optimized.jpg"

    while True:
        img.save(output_path, format="JPEG", quality=quality, optimize=True)

        # 检查文件大小
        size_mb = Path(output_path).stat().st_size / (1024 * 1024)

        if size_mb <= max_size_mb or quality <= 50:
            break

        quality -= 5

    return output_path
```

---

**文档版本**: v1.0
**作者**: AI Architect
**审核**: Pending
**下一步**: 创建测试方案 (testing.md) 和任务清单 (tasks.md)
