"""
Publishing Provider 基类接口
定义所有 Provider 必须实现的方法
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from datetime import datetime


class IPublishingProvider(ABC):
    """
    发布提供者的抽象接口
    所有 Provider（Playwright、Computer Use）必须实现此接口
    
    安全原则：
    - 所有操作必须是幂等的
    - 发布操作必须经过明确确认
    - 错误时默认保存为草稿而非发布
    """

    @abstractmethod
    async def initialize(self, base_url: str, **kwargs) -> None:
        """
        初始化 Provider（启动浏览器、连接服务等）
        
        Args:
            base_url: WordPress 站点 URL
            **kwargs: 可选参数（如 cookies, headless 等）
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """关闭 Provider 并释放资源"""
        pass

    @abstractmethod
    async def capture_screenshot(self) -> bytes:
        """
        捕获当前屏幕截图
        
        Returns:
            截图字节数据
        """
        pass

    @abstractmethod
    async def get_cookies(self) -> List[Dict]:
        """
        获取当前浏览器 cookies
        
        Returns:
            Cookie 列表
        """
        pass

    # ==================== 导航类操作 ====================

    @abstractmethod
    async def navigate_to(self, url: str) -> None:
        """
        导航到指定 URL
        
        Args:
            url: 目标 URL
        """
        pass

    @abstractmethod
    async def navigate_to_new_post(self) -> None:
        """导航到「新增文章」页面"""
        pass

    # ==================== 元素交互操作 ====================

    @abstractmethod
    async def fill_input(self, field_name: str, value: str) -> None:
        """
        填充输入框
        
        Args:
            field_name: 字段名称（如 "new_post_title"）
            value: 要填充的值
        """
        pass

    @abstractmethod
    async def fill_textarea(self, field_name: str, value: str) -> None:
        """
        填充文本区域
        
        Args:
            field_name: 字段名称（如 "content"）
            value: 要填充的值
        """
        pass

    @abstractmethod
    async def click_button(self, button_name: str) -> None:
        """
        点击按钮
        
        Args:
            button_name: 按钮名称（如 "save_draft", "publish"）
        """
        pass

    @abstractmethod
    async def wait_for_element(self, element_name: str, timeout: int = 30) -> None:
        """
        等待元素出现
        
        Args:
            element_name: 元素名称
            timeout: 超时时间（秒）
        """
        pass

    @abstractmethod
    async def wait_for_success_message(self, message_text: str) -> None:
        """
        等待成功提示消息出现
        
        Args:
            message_text: 消息文本（部分匹配）
        """
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
        """
        上传文件
        
        Args:
            file_path: 本地文件路径
        """
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
            metadata: 元数据字典 {
                "alt": "替代文字",
                "title": "图片标题",
                "caption": "图片说明",
                ...
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
        """
        配置图片显示设置
        
        Args:
            align: 对齐方式
            link_to: 连结至
            size: 尺寸
        """
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
            size_name: 尺寸名称（如 "thumbnail"）
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
        """
        添加标签
        
        Args:
            tag: 标签文本
        """
        pass

    @abstractmethod
    async def select_category(self, category: str) -> None:
        """
        选择分类
        
        Args:
            category: 分类名称
        """
        pass

    @abstractmethod
    async def configure_seo_plugin(self, seo_data: Dict[str, str]) -> None:
        """
        配置 SEO 插件
        
        Args:
            seo_data: SEO 数据 {
                "focus_keyword": "焦点关键字",
                "meta_title": "SEO 标题",
                "meta_description": "Meta 描述"
            }
        """
        pass

    # ==================== 发布操作（需要额外安全检查）====================

    @abstractmethod
    async def schedule_publish(self, publish_date: datetime) -> None:
        """
        设置排程发布时间
        
        Args:
            publish_date: 发布日期时间
        """
        pass

    @abstractmethod
    async def get_published_url(self) -> str:
        """
        获取已发布文章的 URL
        
        Returns:
            文章 URL
        """
        pass

    # ==================== 安全验证方法 ====================

    async def verify_draft_status(self) -> bool:
        """
        验证当前文章状态是否为草稿
        
        Returns:
            是否为草稿状态
        
        重要：发布前必须调用此方法确认状态
        """
        # 默认实现返回 True（子类应该覆盖）
        return True

    async def verify_content_saved(self) -> bool:
        """
        验证内容是否已保存
        
        Returns:
            内容是否已保存
        """
        # 默认实现返回 True（子类应该覆盖）
        return True

    async def get_current_post_id(self) -> Optional[str]:
        """
        获取当前文章 ID
        
        Returns:
            文章 ID，如果无法获取则返回 None
        """
        # 默认实现（子类应该覆盖）
        return None


class ProviderError(Exception):
    """Provider 通用错误"""
    pass


class ElementNotFoundError(ProviderError):
    """元素未找到错误"""
    pass


class PublishingSafetyError(ProviderError):
    """发布安全检查失败错误"""
    pass
