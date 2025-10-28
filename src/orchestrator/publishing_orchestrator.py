"""
Publishing Orchestrator - 混合架构发布协调器
Phase 2: Playwright (Primary) + Computer Use (Fallback)

核心功能：
1. 协调 Playwright 和 Computer Use 两个 Provider
2. 智能降级：Playwright 失败时自动切换到 Computer Use
3. Cookie 和状态传递：保持登录会话
4. 发布前安全检查：防止意外发布
5. 错误恢复：失败时保存为草稿
"""

import logging
import asyncio
from typing import Optional, Dict, List, Callable
from datetime import datetime
from dataclasses import dataclass
import uuid

from src.providers.base_provider import IPublishingProvider, ElementNotFoundError, ProviderError
from src.utils.publishing_safety import (
    PublishingSafetyValidator,
    PublishingIntent,
    ErrorRecoveryStrategy
)

logger = logging.getLogger(__name__)


@dataclass
class PublishingContext:
    """发布上下文（在整个发布流程中传递）"""
    task_id: str
    article: Dict  # Article data
    metadata: Dict  # Metadata
    wordpress_url: str
    credentials: Dict  # Credentials
    browser_cookies: Optional[List[Dict]] = None
    published_url: Optional[str] = None
    current_provider_name: str = "playwright"


@dataclass
class PublishResult:
    """发布结果"""
    success: bool
    task_id: str
    url: Optional[str]
    provider_used: str  # "playwright" or "computer_use"
    fallback_triggered: bool
    duration_seconds: float
    error: Optional[str] = None


class PublishingOrchestrator:
    """
    发布协调器 (Phase 2: Hybrid Architecture)
    
    架构：
    - Primary: Playwright Provider (低成本、高性能)
    - Fallback: Computer Use Provider (高可靠性)
    
    降级策略：
    - Playwright 失败3次 → 自动切换到 Computer Use
    - 保持登录状态（通过 Cookie 传递）
    - 保留已完成步骤的状态
    """

    def __init__(
        self,
        playwright_provider: IPublishingProvider,
        computer_use_provider: Optional[IPublishingProvider] = None,
        max_retries: int = 3,
        enable_safety_checks: bool = True
    ):
        """
        初始化发布协调器
        
        Args:
            playwright_provider: Playwright Provider（主要）
            computer_use_provider: Computer Use Provider（备用，可选）
            max_retries: 最大重试次数
            enable_safety_checks: 是否启用安全检查
        """
        self.primary = playwright_provider
        self.fallback = computer_use_provider
        self.current_provider = playwright_provider
        self.max_retries = max_retries
        self.enable_safety_checks = enable_safety_checks
        
        # 安全验证器
        self.safety_validator = PublishingSafetyValidator()
        
        # 统计信息
        self.fallback_triggered = False
        self.retry_count = 0

    async def publish_article(
        self,
        article: Dict,
        metadata: Dict,
        wordpress_url: str,
        credentials: Dict,
        intent: PublishingIntent = PublishingIntent.PUBLISH_NOW
    ) -> PublishResult:
        """
        发布文章的主入口
        
        Args:
            article: 文章数据 {"title": ..., "content": ..., "seo": ...}
            metadata: 元数据 {"tags": [...], "categories": [...], "images": [...]}
            wordpress_url: WordPress URL
            credentials: 登录凭证 {"username": ..., "password": ...}
            intent: 发布意图（默认：立即发布）
        
        Returns:
            发布结果
        
        安全保证：
        - 发布前进行完整性验证
        - 失败时自动保存为草稿
        - 错误时不会意外发布
        """
        start_time = datetime.now()
        task_id = self._generate_task_id()
        
        logger.info(f"🚀 开始发布任务: {task_id}")
        logger.info(f"   文章标题: {article.get('title', 'N/A')}")
        logger.info(f"   发布意图: {intent.value}")
        logger.info(f"   启用安全检查: {self.enable_safety_checks}")
        
        context = PublishingContext(
            task_id=task_id,
            article=article,
            metadata=metadata,
            wordpress_url=wordpress_url,
            credentials=credentials
        )

        try:
            # 阶段一：登录
            await self._execute_phase(
                "login",
                self._phase_login,
                context
            )

            # 阶段二：填充内容
            await self._execute_phase(
                "fill_content",
                self._phase_fill_content,
                context
            )

            # 阶段三：保存草稿（安全检查点）
            await self._execute_phase(
                "save_draft",
                self._phase_save_draft,
                context
            )

            # 阶段四：处理图片（如果有）
            if metadata.get('images'):
                await self._execute_phase(
                    "process_images",
                    self._phase_process_images,
                    context
                )

            # 阶段五：设置元数据
            await self._execute_phase(
                "set_metadata",
                self._phase_set_metadata,
                context
            )

            # 阶段六：发布前安全检查
            if self.enable_safety_checks and intent != PublishingIntent.SAVE_DRAFT:
                logger.info("🔒 执行发布前安全检查...")
                
                safety_result = await self.safety_validator.validate_before_publish(
                    provider=self.current_provider,
                    intent=intent,
                    article_data={'title': article.get('title'), 'content': article.get('content')},
                    metadata=metadata
                )
                
                logger.info(f"   {safety_result.get_summary()}")
                
                if not safety_result.safe_to_publish:
                    logger.error("❌ 安全检查失败，阻止发布")
                    raise ProviderError(f"安全检查失败: {safety_result.errors}")

            # 阶段七：发布/排程
            if intent == PublishingIntent.PUBLISH_NOW:
                await self._execute_phase(
                    "publish",
                    self._phase_publish_now,
                    context
                )
            elif intent == PublishingIntent.SCHEDULE:
                await self._execute_phase(
                    "schedule",
                    self._phase_schedule_publish,
                    context
                )
            # SAVE_DRAFT: 已在阶段三完成，无需额外操作

            # 获取发布URL
            context.published_url = await self.current_provider.get_published_url()

            duration = (datetime.now() - start_time).total_seconds()

            logger.info(f"✅ 发布成功: {task_id}")
            logger.info(f"   URL: {context.published_url}")
            logger.info(f"   耗时: {duration:.1f}秒")
            logger.info(f"   Provider: {context.current_provider_name}")

            return PublishResult(
                success=True,
                task_id=task_id,
                url=context.published_url,
                provider_used=context.current_provider_name,
                fallback_triggered=self.fallback_triggered,
                duration_seconds=duration
            )

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            
            logger.error(f"❌ 发布失败: {task_id}")
            logger.error(f"   错误: {str(e)}")
            
            # 错误恢复：尝试保存为草稿
            try:
                await ErrorRecoveryStrategy.save_as_draft_on_error(
                    self.current_provider,
                    {'title': article.get('title'), 'content': article.get('content')}
                )
            except Exception as recovery_error:
                logger.error(f"错误恢复失败: {recovery_error}")

            return PublishResult(
                success=False,
                task_id=task_id,
                url=None,
                provider_used=context.current_provider_name,
                fallback_triggered=self.fallback_triggered,
                duration_seconds=duration,
                error=str(e)
            )

    async def _execute_phase(
        self,
        phase_name: str,
        phase_func: Callable,
        context: PublishingContext
    ):
        """
        执行一个发布阶段，处理重试和降级逻辑
        
        Args:
            phase_name: 阶段名称
            phase_func: 阶段执行函数
            context: 发布上下文
        """
        logger.info(f"📍 阶段: {phase_name}")
        
        retry_count = 0
        
        while retry_count < self.max_retries:
            try:
                # 执行阶段
                await phase_func(self.current_provider, context)
                
                logger.info(f"   ✅ {phase_name} 完成")
                return
                
            except (ElementNotFoundError, TimeoutError, ProviderError) as e:
                retry_count += 1
                logger.warning(f"   ⚠️ {phase_name} 失败 (尝试 {retry_count}/{self.max_retries}): {e}")
                
                if retry_count >= self.max_retries:
                    # 尝试降级到 Computer Use
                    if self.fallback and self.current_provider != self.fallback:
                        logger.warning(f"   🔄 切换到 Computer Use Provider")
                        await self._switch_to_fallback(context)
                        retry_count = 0  # 重置重试计数
                    else:
                        logger.error(f"   ❌ {phase_name} 所有重试失败")
                        raise ProviderError(f"Phase '{phase_name}' failed after {self.max_retries} retries: {e}")
                
                # 等待后重试
                await asyncio.sleep(2.0)

    async def _switch_to_fallback(self, context: PublishingContext):
        """
        切换到备用 Provider（Computer Use）
        
        Args:
            context: 发布上下文
        """
        logger.info("🔄 执行 Provider 降级...")
        
        # 1. 保存当前 cookies（如果可能）
        try:
            context.browser_cookies = await self.current_provider.get_cookies()
            logger.info(f"   保存了 {len(context.browser_cookies)} 个 cookies")
        except Exception as e:
            logger.warning(f"   无法保存 cookies: {e}")
            context.browser_cookies = []
        
        # 2. 关闭当前 Provider
        try:
            await self.current_provider.close()
        except Exception as e:
            logger.warning(f"   关闭 Provider 失败: {e}")
        
        # 3. 切换到备用 Provider
        self.current_provider = self.fallback
        context.current_provider_name = "computer_use"
        self.fallback_triggered = True
        
        # 4. 初始化备用 Provider（传递 cookies）
        await self.current_provider.initialize(
            base_url=context.wordpress_url,
            cookies=context.browser_cookies
        )
        
        logger.info("   ✅ 已切换到 Computer Use Provider")

    # ==================== 阶段执行函数 ====================

    async def _phase_login(self, provider: IPublishingProvider, context: PublishingContext):
        """阶段一：登录 WordPress"""
        logger.info("   登录 WordPress...")
        
        await provider.navigate_to(f"{context.wordpress_url}/wp-admin")
        
        # 检查是否已登录（有 cookies）
        if context.browser_cookies:
            logger.info("   使用已有会话...")
            await provider.wait_for_element("dashboard", timeout=10)
        else:
            # 执行登录
            await provider.fill_input("login_username", context.credentials['username'])
            await provider.fill_input("login_password", context.credentials['password'])
            await provider.click_button("login_button")
            await provider.wait_for_element("dashboard")
            
            # 保存 cookies
            context.browser_cookies = await provider.get_cookies()

    async def _phase_fill_content(self, provider: IPublishingProvider, context: PublishingContext):
        """阶段二：填充文章内容"""
        logger.info("   填充文章内容...")
        
        # 导航到新增文章
        await provider.navigate_to_new_post()
        
        # 填写标题
        await provider.fill_input("new_post_title", context.article['title'])
        
        # 切换到文字模式
        try:
            await provider.click_button("content_text_mode_button")
        except Exception:
            pass  # 可能已经是文字模式
        
        # 填充内容
        await provider.fill_textarea("content", context.article['content'])
        
        # 清理 HTML 实体
        await provider.clean_html_entities()

    async def _phase_save_draft(self, provider: IPublishingProvider, context: PublishingContext):
        """阶段三：保存草稿（安全检查点）"""
        logger.info("   保存草稿...")
        
        await provider.click_button("save_draft")
        await provider.wait_for_success_message("草稿")

    async def _phase_process_images(self, provider: IPublishingProvider, context: PublishingContext):
        """阶段四：处理图片"""
        images = context.metadata.get('images', [])
        logger.info(f"   处理 {len(images)} 张图片...")
        
        for idx, image in enumerate(images):
            logger.info(f"      图片 {idx + 1}/{len(images)}")
            
            # 打开媒体库
            await provider.open_media_library()
            
            # 上传图片
            await provider.upload_file(image['file_path'])
            await provider.wait_for_upload_complete()
            
            # 填写元数据
            await provider.fill_image_metadata({
                "alt": image.get('alt_text', ''),
                "title": image.get('title', ''),
                "caption": image.get('caption', '')
            })
            
            # 第一张设为特色图片
            if idx == 0 and image.get('is_featured'):
                await provider.set_as_featured_image()
            else:
                # 配置显示
                await provider.configure_image_display(
                    align="center",
                    link_to="none",
                    size="large"
                )
                await provider.insert_image_to_content()
            
            await provider.close_media_library()

    async def _phase_set_metadata(self, provider: IPublishingProvider, context: PublishingContext):
        """阶段五：设置元数据"""
        logger.info("   设置元数据...")
        
        # 添加标签
        for tag in context.metadata.get('tags', []):
            await provider.add_tag(tag)
        
        # 选择分类
        for category in context.metadata.get('categories', []):
            await provider.select_category(category)
        
        # 配置 SEO
        seo = context.article.get('seo')
        if seo:
            await provider.configure_seo_plugin({
                "focus_keyword": seo.get('focus_keyword', ''),
                "meta_title": seo.get('meta_title', ''),
                "meta_description": seo.get('meta_description', '')
            })

    async def _phase_publish_now(self, provider: IPublishingProvider, context: PublishingContext):
        """阶段七：立即发布"""
        logger.info("   执行发布...")
        
        await provider.click_button("publish")
        await provider.wait_for_success_message("已發佈")

    async def _phase_schedule_publish(self, provider: IPublishingProvider, context: PublishingContext):
        """阶段七：排程发布"""
        logger.info("   设置排程发布...")
        
        await provider.schedule_publish(context.metadata.get('publish_date'))
        await provider.click_button("publish")  # 排程发布也需要点击发布按钮
        await provider.wait_for_success_message("已排程")

    def _generate_task_id(self) -> str:
        """生成任务 ID"""
        return f"publish-{uuid.uuid4().hex[:8]}"
