"""
WordPress Publishing Service - Publishing Orchestrator

协调多个 Provider 的发布流程，实现：
- 智能重试机制
- Provider 降级（Playwright -> Computer Use）
- 状态保存和恢复
- 审计追踪
"""

import asyncio
from typing import Optional, Callable, Any
from datetime import datetime
import traceback

from src.providers.base import (
    IPublishingProvider,
    ProviderError,
    LoginError,
    ArticleCreationError,
    ImageUploadError,
    FeaturedImageError,
    SEOConfigError,
    PublishError
)
from src.models import PublishingContext, PublishResult
from src.config.loader import settings
from src.utils.logger import get_logger, audit_logger


class PublishingOrchestrator:
    """
    发布流程协调器

    负责协调整个发布流程，包括：
    - 执行 5 个阶段（登录、创建文章、上传图片、配置 SEO、发布）
    - 每个阶段的重试机制
    - Provider 失败时的智能降级
    - 状态保存和恢复
    - 完整的审计追踪
    """

    def __init__(
        self,
        primary_provider: IPublishingProvider,
        fallback_provider: Optional[IPublishingProvider] = None,
        max_retries: int = None,
        enable_fallback: bool = None
    ):
        """
        初始化 Orchestrator

        Args:
            primary_provider: 主要的 Provider (Playwright)
            fallback_provider: 备用的 Provider (Computer Use)
            max_retries: 最大重试次数，默认从配置读取
            enable_fallback: 是否启用降级机制，默认从配置读取
        """
        self.primary_provider = primary_provider
        self.fallback_provider = fallback_provider
        self.current_provider = primary_provider

        # 从配置或参数获取设置
        self.max_retries = max_retries or settings.playwright_max_retries
        self.enable_fallback = enable_fallback if enable_fallback is not None else settings.enable_fallback

        self.logger = get_logger('PublishingOrchestrator')

        # 状态追踪
        self.completed_phases = []
        self.retry_count = 0
        self.fallback_triggered = False

    async def publish_article(
        self,
        context: PublishingContext
    ) -> PublishResult:
        """
        执行完整的文章发布流程

        Args:
            context: 发布上下文

        Returns:
            发布结果
        """
        start_time = datetime.now()
        self.logger.info(f"开始发布文章: {context.article.title}", task_id=context.task_id)

        try:
            # Phase 0: 初始化
            await self._execute_phase(
                context,
                "initialize",
                self._phase_initialize,
                "初始化 Provider"
            )

            # Phase 1: 登录
            await self._execute_phase(
                context,
                "login",
                self._phase_login,
                "登录 WordPress"
            )

            # Phase 2: 创建文章
            await self._execute_phase(
                context,
                "article",
                self._phase_create_article,
                "创建文章"
            )

            # Phase 3: 上传图片（如果有）
            if context.images:
                await self._execute_phase(
                    context,
                    "images",
                    self._phase_upload_images,
                    "上传图片"
                )

            # Phase 4: 配置 SEO
            await self._execute_phase(
                context,
                "seo",
                self._phase_configure_seo,
                "配置 SEO"
            )

            # Phase 5: 发布
            await self._execute_phase(
                context,
                "publish",
                self._phase_publish,
                "发布文章"
            )

            # 计算耗时
            duration = (datetime.now() - start_time).total_seconds()

            # 记录审计日志
            audit_logger.log_action(
                action="publish_article_complete",
                task_id=context.task_id,
                status="success",
                details={
                    "article_id": context.article.id,
                    "article_title": context.article.title,
                    "url": context.published_url,
                    "provider": self.current_provider.__class__.__name__,
                    "duration_seconds": duration,
                    "retry_count": self.retry_count,
                    "fallback_triggered": self.fallback_triggered,
                    "completed_phases": self.completed_phases
                }
            )

            self.logger.info(
                f"文章发布成功: {context.published_url} (耗时: {duration:.2f}秒)",
                task_id=context.task_id
            )

            # 返回成功结果
            return PublishResult(
                success=True,
                task_id=context.task_id,
                url=context.published_url,
                duration_seconds=duration,
                provider_used=self.current_provider.__class__.__name__,
                fallback_triggered=self.fallback_triggered,
                retry_count=self.retry_count
            )

        except Exception as e:
            # 计算耗时
            duration = (datetime.now() - start_time).total_seconds()
            error_msg = f"{str(e)}\n{traceback.format_exc()}"

            self.logger.error(
                f"文章发布失败: {error_msg}",
                task_id=context.task_id
            )

            # 记录审计日志
            audit_logger.log_action(
                action="publish_article_failed",
                task_id=context.task_id,
                status="failure",
                details={
                    "article_id": context.article.id,
                    "article_title": context.article.title,
                    "provider": self.current_provider.__class__.__name__,
                    "duration_seconds": duration,
                    "retry_count": self.retry_count,
                    "fallback_triggered": self.fallback_triggered,
                    "completed_phases": self.completed_phases,
                    "failed_phase": self.completed_phases[-1] if self.completed_phases else "initialize"
                },
                error=error_msg
            )

            # 返回失败结果
            return PublishResult(
                success=False,
                task_id=context.task_id,
                error=str(e),
                duration_seconds=duration,
                provider_used=self.current_provider.__class__.__name__,
                fallback_triggered=self.fallback_triggered,
                retry_count=self.retry_count
            )

        finally:
            # 清理资源
            try:
                await self.current_provider.cleanup()
            except Exception as e:
                self.logger.error(f"清理资源失败: {e}", task_id=context.task_id)

    async def _execute_phase(
        self,
        context: PublishingContext,
        phase_name: str,
        phase_func: Callable,
        phase_description: str
    ) -> None:
        """
        执行单个阶段（带重试和降级）

        Args:
            context: 发布上下文
            phase_name: 阶段名称
            phase_func: 阶段执行函数
            phase_description: 阶段描述

        Raises:
            ProviderError: 如果重试和降级都失败
        """
        self.logger.info(f"Phase: {phase_description}", task_id=context.task_id)

        retry_count = 0

        while retry_count <= self.max_retries:
            try:
                # 执行前截图
                await self.current_provider.take_screenshot(
                    f"{context.task_id}_{phase_name}_before",
                    f"{phase_description} - 执行前"
                )

                # 执行阶段
                await phase_func(context)

                # 执行后截图
                await self.current_provider.take_screenshot(
                    f"{context.task_id}_{phase_name}_after",
                    f"{phase_description} - 执行后"
                )

                # 记录成功
                self.completed_phases.append(phase_name)
                audit_logger.log_action(
                    action=f"phase_{phase_name}_success",
                    task_id=context.task_id,
                    status="success",
                    details={
                        "phase": phase_name,
                        "description": phase_description,
                        "retry_count": retry_count,
                        "provider": self.current_provider.__class__.__name__
                    }
                )

                self.logger.info(
                    f"✓ {phase_description} 完成 (重试次数: {retry_count})",
                    task_id=context.task_id
                )
                return

            except ProviderError as e:
                retry_count += 1
                self.retry_count += 1

                self.logger.warning(
                    f"✗ {phase_description} 失败 (尝试 {retry_count}/{self.max_retries + 1}): {e}",
                    task_id=context.task_id
                )

                # 记录失败
                audit_logger.log_action(
                    action=f"phase_{phase_name}_retry",
                    task_id=context.task_id,
                    status="retry",
                    details={
                        "phase": phase_name,
                        "description": phase_description,
                        "retry_count": retry_count,
                        "error": str(e),
                        "provider": self.current_provider.__class__.__name__
                    },
                    error=str(e)
                )

                # 错误截图
                await self.current_provider.take_screenshot(
                    f"{context.task_id}_{phase_name}_error_{retry_count}",
                    f"{phase_description} - 错误: {str(e)[:100]}"
                )

                # 如果已达到最大重试次数，考虑降级
                if retry_count > self.max_retries:
                    if self.enable_fallback and self.fallback_provider and not self.fallback_triggered:
                        self.logger.warning(
                            f"Playwright 失败，切换到 Computer Use Provider",
                            task_id=context.task_id
                        )
                        await self._switch_to_fallback(context)
                        retry_count = 0  # 重置重试计数
                    else:
                        # 无法降级或降级已失败，抛出异常
                        raise

                # 等待后重试
                await asyncio.sleep(2 * retry_count)  # 指数退避

    async def _switch_to_fallback(self, context: PublishingContext) -> None:
        """
        切换到备用 Provider

        Args:
            context: 发布上下文
        """
        self.fallback_triggered = True

        # 清理当前 Provider
        try:
            await self.current_provider.cleanup()
        except:
            pass

        # 切换到备用 Provider
        self.current_provider = self.fallback_provider

        # 初始化备用 Provider
        await self.current_provider.initialize()

        # 如果有 cookies，传递给备用 Provider（尝试恢复会话）
        # 注意：Computer Use 可能不支持 cookies
        if hasattr(context, 'browser_cookies') and context.browser_cookies:
            self.logger.debug("尝试使用 cookies 恢复会话", task_id=context.task_id)
            # 实现取决于 Provider

        audit_logger.log_action(
            action="provider_switch",
            task_id=context.task_id,
            status="info",
            details={
                "from_provider": "PlaywrightProvider",
                "to_provider": self.current_provider.__class__.__name__,
                "completed_phases": self.completed_phases
            }
        )

    # ==================== 阶段实现 ====================

    async def _phase_initialize(self, context: PublishingContext) -> None:
        """Phase 0: 初始化"""
        await self.current_provider.initialize()

    async def _phase_login(self, context: PublishingContext) -> None:
        """Phase 1: 登录"""
        success = await self.current_provider.login(
            context.wordpress_url,
            context.credentials
        )
        if not success:
            raise LoginError("登录失败")

    async def _phase_create_article(self, context: PublishingContext) -> None:
        """Phase 2: 创建文章"""
        success = await self.current_provider.create_article(
            context.article,
            context.metadata
        )
        if not success:
            raise ArticleCreationError("文章创建失败")

    async def _phase_upload_images(self, context: PublishingContext) -> None:
        """Phase 3: 上传图片"""
        # 上传所有图片
        uploaded_urls = await self.current_provider.upload_images(context.images)

        if not uploaded_urls:
            raise ImageUploadError("图片上传失败")

        self.logger.info(f"已上传 {len(uploaded_urls)} 张图片", task_id=context.task_id)

        # 设置特色图片（如果有）
        featured_image = next((img for img in context.images if img.is_featured), None)
        if featured_image:
            try:
                success = await self.current_provider.set_featured_image(featured_image)
                if not success:
                    self.logger.warning("特色图片设置失败", task_id=context.task_id)
            except Exception as e:
                self.logger.warning(f"特色图片设置失败: {e}", task_id=context.task_id)

    async def _phase_configure_seo(self, context: PublishingContext) -> None:
        """Phase 4: 配置 SEO"""
        success = await self.current_provider.configure_seo(context.article.seo)
        if not success:
            # SEO 配置失败不应该阻止发布，只是警告
            self.logger.warning("SEO 配置失败", task_id=context.task_id)

    async def _phase_publish(self, context: PublishingContext) -> None:
        """Phase 5: 发布"""
        published_url = await self.current_provider.publish(context.metadata)
        if not published_url:
            raise PublishError("发布失败：未获取到文章 URL")

        context.published_url = published_url
        self.logger.info(f"文章已发布: {published_url}", task_id=context.task_id)
