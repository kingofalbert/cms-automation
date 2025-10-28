"""
WordPress Publishing Service - Provider Base Interface

定义所有 Publishing Provider 必须实现的接口
"""

from abc import ABC, abstractmethod
from typing import Optional, List
from src.models import (
    PublishingContext,
    PublishResult,
    Article,
    ImageAsset,
    ArticleMetadata,
    SEOData,
    WordPressCredentials
)


class IPublishingProvider(ABC):
    """
    发布 Provider 接口

    所有 Provider (Playwright, Computer Use) 必须实现此接口
    """

    @abstractmethod
    async def initialize(self) -> None:
        """
        初始化 Provider

        在开始发布流程前调用，用于：
        - 启动浏览器 (Playwright)
        - 初始化 API 客户端 (Computer Use)
        - 加载配置
        """
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """
        清理 Provider

        在发布流程结束后调用，用于：
        - 关闭浏览器
        - 释放资源
        - 保存审计日志
        """
        pass

    @abstractmethod
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

        Raises:
            LoginError: 登录失败
        """
        pass

    @abstractmethod
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

        Raises:
            ArticleCreationError: 文章创建失败
        """
        pass

    @abstractmethod
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

        Raises:
            ImageUploadError: 图片上传失败
        """
        pass

    @abstractmethod
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

        Raises:
            FeaturedImageError: 特色图片设置失败
        """
        pass

    @abstractmethod
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

        Raises:
            SEOConfigError: SEO 配置失败
        """
        pass

    @abstractmethod
    async def publish(
        self,
        metadata: ArticleMetadata
    ) -> str:
        """
        发布文章

        Args:
            metadata: 发布元数据（立即发布/排程发布）

        Returns:
            发布后的文章 URL

        Raises:
            PublishError: 发布失败
        """
        pass

    @abstractmethod
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
            截图文件路径，如果失败则返回 None
        """
        pass

    # ==================== 完整发布流程 ====================

    async def publish_article(
        self,
        context: PublishingContext
    ) -> PublishResult:
        """
        完整的文章发布流程

        此方法协调所有阶段，实现完整的发布流程：
        1. 初始化
        2. 登录
        3. 创建文章
        4. 上传图片
        5. 设置特色图片
        6. 配置 SEO
        7. 发布
        8. 清理

        Args:
            context: 发布上下文

        Returns:
            发布结果
        """
        from datetime import datetime
        import traceback
        from src.utils.logger import get_logger, audit_logger

        logger = get_logger(f"{self.__class__.__name__}")
        start_time = datetime.now()

        try:
            # Phase 0: 初始化
            logger.info("开始发布流程", task_id=context.task_id)
            await self.initialize()
            await self.take_screenshot(f"{context.task_id}_00_init", "初始化完成")

            # Phase 1: 登录
            logger.info("Phase 1: 登录 WordPress", task_id=context.task_id)
            login_success = await self.login(
                context.wordpress_url,
                context.credentials
            )
            if not login_success:
                raise Exception("登录失败")
            await self.take_screenshot(f"{context.task_id}_01_login", "登录成功")

            # Phase 2: 创建文章
            logger.info("Phase 2: 创建文章", task_id=context.task_id)
            article_success = await self.create_article(
                context.article,
                context.metadata
            )
            if not article_success:
                raise Exception("文章创建失败")
            await self.take_screenshot(f"{context.task_id}_02_article", "文章创建完成")

            # Phase 3: 上传图片
            if context.images:
                logger.info(f"Phase 3: 上传 {len(context.images)} 张图片", task_id=context.task_id)
                image_urls = await self.upload_images(context.images)
                logger.info(f"图片上传完成: {len(image_urls)} 张", task_id=context.task_id)
                await self.take_screenshot(f"{context.task_id}_03_images", "图片上传完成")

                # 设置特色图片
                featured_image = next((img for img in context.images if img.is_featured), None)
                if featured_image:
                    logger.info("设置特色图片", task_id=context.task_id)
                    featured_success = await self.set_featured_image(featured_image)
                    if not featured_success:
                        logger.warning("特色图片设置失败", task_id=context.task_id)
                    await self.take_screenshot(f"{context.task_id}_03_featured", "特色图片设置完成")

            # Phase 4: 配置 SEO
            logger.info("Phase 4: 配置 SEO", task_id=context.task_id)
            seo_success = await self.configure_seo(context.article.seo)
            if not seo_success:
                logger.warning("SEO 配置失败", task_id=context.task_id)
            await self.take_screenshot(f"{context.task_id}_04_seo", "SEO 配置完成")

            # Phase 5: 发布
            logger.info("Phase 5: 发布文章", task_id=context.task_id)
            published_url = await self.publish(context.metadata)
            logger.info(f"文章发布成功: {published_url}", task_id=context.task_id)
            await self.take_screenshot(f"{context.task_id}_05_publish", "发布完成")

            # 计算耗时
            duration = (datetime.now() - start_time).total_seconds()

            # 记录审计日志
            audit_logger.log_action(
                action="publish_article",
                task_id=context.task_id,
                status="success",
                details={
                    "article_id": context.article.id,
                    "article_title": context.article.title,
                    "url": published_url,
                    "provider": self.__class__.__name__,
                    "duration_seconds": duration
                }
            )

            # 返回成功结果
            return PublishResult(
                success=True,
                task_id=context.task_id,
                url=published_url,
                duration_seconds=duration,
                provider_used=self.__class__.__name__,
                fallback_triggered=False,
                retry_count=0
            )

        except Exception as e:
            # 计算耗时
            duration = (datetime.now() - start_time).total_seconds()
            error_msg = f"{str(e)}\n{traceback.format_exc()}"

            logger.error(f"发布失败: {error_msg}", task_id=context.task_id)

            # 截图保存错误现场
            await self.take_screenshot(f"{context.task_id}_error", f"错误: {str(e)}")

            # 记录审计日志
            audit_logger.log_action(
                action="publish_article",
                task_id=context.task_id,
                status="failure",
                details={
                    "article_id": context.article.id,
                    "article_title": context.article.title,
                    "provider": self.__class__.__name__,
                    "duration_seconds": duration
                },
                error=error_msg
            )

            # 返回失败结果
            return PublishResult(
                success=False,
                task_id=context.task_id,
                error=str(e),
                duration_seconds=duration,
                provider_used=self.__class__.__name__,
                fallback_triggered=False,
                retry_count=0
            )

        finally:
            # 清理资源
            try:
                await self.cleanup()
            except Exception as e:
                logger.error(f"清理资源失败: {e}", task_id=context.task_id)


# ==================== 自定义异常 ====================

class ProviderError(Exception):
    """Provider 基础异常"""
    pass


class LoginError(ProviderError):
    """登录失败异常"""
    pass


class ArticleCreationError(ProviderError):
    """文章创建失败异常"""
    pass


class ImageUploadError(ProviderError):
    """图片上传失败异常"""
    pass


class FeaturedImageError(ProviderError):
    """特色图片设置失败异常"""
    pass


class SEOConfigError(ProviderError):
    """SEO 配置失败异常"""
    pass


class PublishError(ProviderError):
    """发布失败异常"""
    pass
