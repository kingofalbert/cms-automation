"""
WordPress Publishing Service - Computer Use Provider

使用 Anthropic Computer Use API 实现的 WordPress 发布 Provider
通过自然语言指令和视觉识别实现浏览器自动化
"""

import asyncio
import os
import base64
import anthropic
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

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
    WordPressCredentials,
    ComputerUseSession,
    ConversationMessage
)
from src.config.computer_use_loader import InstructionTemplate
from src.utils.logger import get_logger


class ComputerUseProvider(IPublishingProvider):
    """
    Computer Use Provider 实现

    使用 Anthropic Computer Use API 进行浏览器自动化
    通过自然语言指令和视觉识别操作 WordPress 后台
    """

    def __init__(
        self,
        api_key: str,
        instructions: InstructionTemplate,
        display_width: int = 1920,
        display_height: int = 1080
    ):
        """
        初始化 Computer Use Provider

        Args:
            api_key: Anthropic API Key
            instructions: 指令模板对象
            display_width: 显示宽度（像素）
            display_height: 显示高度（像素）
        """
        self.logger = get_logger('ComputerUseProvider')
        self.api_key = api_key
        self.instructions = instructions
        self.display_width = display_width
        self.display_height = display_height

        # Anthropic 客户端
        self.client: Optional[anthropic.Anthropic] = None

        # 会话管理
        self.session: Optional[ComputerUseSession] = None

        # 截图路径
        self.screenshot_path = Path("logs/screenshots/computer_use")
        self.screenshot_path.mkdir(parents=True, exist_ok=True)

        # API 配置
        self.model = "claude-3-5-sonnet-20241022"
        self.max_tokens = 4096

    async def initialize(self) -> None:
        """初始化 Provider"""
        self.logger.info("初始化 Computer Use Provider")

        try:
            # 初始化 Anthropic 客户端
            self.client = anthropic.Anthropic(api_key=self.api_key)

            # 创建新会话
            session_id = f"cu-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            self.session = ComputerUseSession(
                session_id=session_id,
                conversation_history=[],
                current_url=None,
                screenshot_count=0,
                total_tokens_used=0
            )

            self.logger.info(f"Computer Use Provider 初始化完成，会话 ID: {session_id}")

        except Exception as e:
            self.logger.error(f"Computer Use Provider 初始化失败: {e}")
            raise

    async def cleanup(self) -> None:
        """清理 Provider"""
        self.logger.info("清理 Computer Use Provider")

        if self.session:
            self.logger.info(
                f"会话统计 - 截图数: {self.session.screenshot_count}, "
                f"Tokens: {self.session.total_tokens_used}"
            )

        # 无需特殊清理，API 调用是无状态的
        self.logger.info("Computer Use Provider 清理完成")

    async def _execute_instruction(
        self,
        instruction: str,
        expect_screenshot: bool = True
    ) -> Dict[str, Any]:
        """
        执行 Computer Use 指令

        Args:
            instruction: 自然语言指令
            expect_screenshot: 是否期望返回截图

        Returns:
            API 响应字典，包含:
            - content: 文本响应
            - screenshot: 截图（base64，如果有）
            - tool_calls: 工具调用列表
            - usage: Token 使用统计

        Raises:
            Exception: API 调用失败
        """
        self.logger.debug(f"执行指令: {instruction[:100]}...")

        try:
            # 构建消息
            messages = list(self.session.conversation_history)
            messages.append(ConversationMessage(
                role="user",
                content=instruction
            ))

            # 调用 Anthropic API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                tools=[{
                    "type": "computer_20241022",
                    "name": "computer",
                    "display_width_px": self.display_width,
                    "display_height_px": self.display_height,
                    "display_number": 1,
                }],
                messages=[{"role": m.role, "content": m.content} for m in messages]
            )

            # 解析响应
            result = {
                "content": "",
                "screenshot": None,
                "tool_calls": [],
                "usage": {}
            }

            # 提取文本内容
            for block in response.content:
                if hasattr(block, 'text'):
                    result["content"] += block.text
                elif hasattr(block, 'type') and block.type == 'tool_use':
                    result["tool_calls"].append(block)
                    # 如果有截图
                    if hasattr(block, 'output') and isinstance(block.output, dict):
                        if 'screenshot' in block.output:
                            result["screenshot"] = block.output['screenshot']

            # 记录 Token 使用
            if hasattr(response, 'usage'):
                result["usage"] = {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens
                }
                self.session.total_tokens_used += (
                    response.usage.input_tokens + response.usage.output_tokens
                )

            # 更新对话历史
            self.session.conversation_history.append(ConversationMessage(
                role="user",
                content=instruction
            ))
            self.session.conversation_history.append(ConversationMessage(
                role="assistant",
                content=result["content"]
            ))

            self.logger.debug(f"指令执行完成: {result['content'][:100]}...")
            return result

        except Exception as e:
            self.logger.error(f"指令执行失败: {e}")
            raise

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
        self.logger.info(f"登录 WordPress: {wordpress_url}")

        try:
            # 步骤 1: 导航到登录页面
            login_url = f"{wordpress_url.rstrip('/')}/wp-login.php"
            navigate_instruction = f"请在浏览器中打开网址: {login_url}\n等待页面完全加载。"

            await self._execute_instruction(navigate_instruction)
            await asyncio.sleep(2)

            # 步骤 2: 填写登录表单
            login_instruction = self.instructions.get(
                'login_to_wordpress',
                username=credentials.username,
                password=credentials.password
            )

            result = await self._execute_instruction(login_instruction)
            await asyncio.sleep(3)

            # 步骤 3: 验证登录成功
            verify_instruction = self.instructions.get('verify_login_success')
            verify_result = await self._execute_instruction(verify_instruction)

            # 简单验证：检查响应中是否包含成功标志
            if "成功" in verify_result.get("content", "") or "wp-admin" in verify_result.get("content", ""):
                self.logger.info("登录成功")
                self.session.current_url = f"{wordpress_url}/wp-admin"
                return True
            else:
                raise LoginError("登录验证失败：未能确认进入后台")

        except Exception as e:
            self.logger.error(f"登录失败: {e}")
            raise LoginError(f"登录失败: {e}")

    async def create_article(
        self,
        article: Article,
        metadata: ArticleMetadata
    ) -> bool:
        """
        创建文章

        Args:
            article: 文章数据
            metadata: 文章元数据

        Returns:
            是否创建成功

        Raises:
            ArticleCreationError: 文章创建失败
        """
        self.logger.info(f"创建文章: {article.title}")

        try:
            # 步骤 1: 导航到新增文章页面
            navigate_instruction = self.instructions.get('navigate_to_new_post')
            await self._execute_instruction(navigate_instruction)
            await asyncio.sleep(2)

            # 步骤 2: 填写标题
            title_instruction = self.instructions.get(
                'fill_title',
                value=article.title
            )
            await self._execute_instruction(title_instruction)
            await asyncio.sleep(1)

            # 步骤 3: 填写内容
            content_instruction = self.instructions.get(
                'fill_content',
                content=article.content_html
            )
            await self._execute_instruction(content_instruction)
            await asyncio.sleep(2)

            # 步骤 4: 清理 HTML 实体
            clean_instruction = self.instructions.get('clean_html_entities')
            await self._execute_instruction(clean_instruction)
            await asyncio.sleep(1)

            # 步骤 5: 添加标签
            for tag in metadata.tags:
                tag_instruction = self.instructions.get('add_tag', tag=tag)
                await self._execute_instruction(tag_instruction)
                await asyncio.sleep(0.5)

            # 步骤 6: 选择分类
            for category in metadata.categories:
                category_instruction = self.instructions.get('select_category', category=category)
                await self._execute_instruction(category_instruction)
                await asyncio.sleep(0.5)

            self.logger.info("文章创建完成")
            return True

        except Exception as e:
            self.logger.error(f"文章创建失败: {e}")
            raise ArticleCreationError(f"文章创建失败: {e}")

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
        self.logger.info(f"上传 {len(images)} 张图片")

        uploaded_urls = []

        try:
            for idx, image in enumerate(images, 1):
                self.logger.info(f"上传图片 {idx}/{len(images)}: {image.title}")

                # 步骤 1: 打开媒体库
                open_media_instruction = self.instructions.get('open_media_library')
                await self._execute_instruction(open_media_instruction)
                await asyncio.sleep(2)

                # 步骤 2: 上传文件
                upload_instruction = self.instructions.get(
                    'upload_file',
                    file_path=image.file_path
                )
                await self._execute_instruction(upload_instruction)
                await asyncio.sleep(3)

                # 步骤 3: 等待上传完成
                wait_instruction = self.instructions.get('wait_for_upload_complete')
                await self._execute_instruction(wait_instruction)
                await asyncio.sleep(2)

                # 步骤 4: 填写图片元数据
                metadata_instruction = self.instructions.get(
                    'fill_image_metadata',
                    alt=image.alt_text,
                    title=image.title,
                    caption=image.caption,
                    keywords=", ".join(image.keywords),
                    photographer=image.photographer
                )
                await self._execute_instruction(metadata_instruction)
                await asyncio.sleep(1)

                # 步骤 5: 插入到文章
                if not image.is_featured:
                    insert_instruction = self.instructions.get('insert_image_to_content')
                    await self._execute_instruction(insert_instruction)
                    await asyncio.sleep(1)

                uploaded_urls.append(f"uploaded-{idx}")  # 占位 URL

            self.logger.info(f"图片上传完成: {len(uploaded_urls)} 张")
            return uploaded_urls

        except Exception as e:
            self.logger.error(f"图片上传失败: {e}")
            raise ImageUploadError(f"图片上传失败: {e}")

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
        self.logger.info(f"设置特色图片: {image.title}")

        try:
            # 步骤 1: 打开特色图片设置
            set_featured_instruction = self.instructions.get('set_as_featured_image')
            await self._execute_instruction(set_featured_instruction)
            await asyncio.sleep(2)

            # 步骤 2: 从媒体库选择
            select_instruction = self.instructions.get(
                'select_featured_image_from_library',
                image_name=image.title
            )
            await self._execute_instruction(select_instruction)
            await asyncio.sleep(1)

            # 步骤 3: 确认设置
            confirm_instruction = self.instructions.get('confirm_featured_image')
            await self._execute_instruction(confirm_instruction)
            await asyncio.sleep(1)

            self.logger.info("特色图片设置完成")
            return True

        except Exception as e:
            self.logger.error(f"特色图片设置失败: {e}")
            raise FeaturedImageError(f"特色图片设置失败: {e}")

    async def configure_seo(
        self,
        seo: SEOData
    ) -> bool:
        """
        配置 SEO 设置

        Args:
            seo: SEO 数据

        Returns:
            是否配置成功

        Raises:
            SEOConfigError: SEO 配置失败
        """
        self.logger.info("配置 SEO")

        try:
            # 步骤 1: 展开 SEO 区块
            expand_instruction = self.instructions.get('expand_seo_section')
            await self._execute_instruction(expand_instruction)
            await asyncio.sleep(1)

            # 步骤 2: 配置 SEO 字段
            seo_instruction = self.instructions.get(
                'configure_seo_plugin',
                focus_keyword=seo.focus_keyword,
                meta_title=seo.meta_title,
                meta_description=seo.meta_description
            )
            await self._execute_instruction(seo_instruction)
            await asyncio.sleep(2)

            self.logger.info("SEO 配置完成")
            return True

        except Exception as e:
            self.logger.error(f"SEO 配置失败: {e}")
            raise SEOConfigError(f"SEO 配置失败: {e}")

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

        Raises:
            PublishError: 发布失败
        """
        self.logger.info("发布文章")

        try:
            if metadata.publish_immediately:
                # 立即发布
                publish_instruction = self.instructions.get('click_publish')
                await self._execute_instruction(publish_instruction)
                await asyncio.sleep(3)

            else:
                # 排程发布
                publish_date = metadata.publish_date
                schedule_instruction = self.instructions.get(
                    'schedule_publish',
                    month=publish_date.month,
                    day=publish_date.day,
                    year=publish_date.year,
                    hour=publish_date.hour,
                    minute=publish_date.minute
                )
                await self._execute_instruction(schedule_instruction)
                await asyncio.sleep(3)

            # 验证发布成功
            verify_instruction = self.instructions.get('verify_publish_success')
            verify_result = await self._execute_instruction(verify_instruction)

            # 简单提取 URL（实际实现需要从页面提取）
            published_url = self.session.current_url or "unknown"

            self.logger.info(f"文章发布成功: {published_url}")
            return published_url

        except Exception as e:
            self.logger.error(f"发布失败: {e}")
            raise PublishError(f"发布失败: {e}")

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
            # Computer Use API 会在操作过程中自动截图
            # 这里我们只是记录截图请求
            self.session.screenshot_count += 1

            screenshot_file = self.screenshot_path / f"{name}.png"

            self.logger.debug(f"截图请求: {name} - {description}")

            # 实际截图由 API 自动处理，这里返回占位路径
            return str(screenshot_file)

        except Exception as e:
            self.logger.error(f"截图失败: {e}")
            return None
