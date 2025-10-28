"""
WordPress Publishing Service - Core Data Models

This module defines all core data models using Pydantic for validation.
"""

from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Optional
from datetime import datetime
from pathlib import Path
import re


class SEOData(BaseModel):
    """SEO 数据模型"""

    focus_keyword: str = Field(..., min_length=1, max_length=100, description="焦点关键字")
    meta_title: str = Field(..., min_length=50, max_length=60, description="SEO 标题 (50-60 字符)")
    meta_description: str = Field(..., min_length=150, max_length=160, description="Meta 描述 (150-160 字符)")
    primary_keywords: List[str] = Field(default_factory=list, max_length=5, description="主要关键字 (最多 5 个)")
    secondary_keywords: List[str] = Field(default_factory=list, max_length=10, description="次要关键字 (最多 10 个)")

    @field_validator('meta_title')
    @classmethod
    def validate_meta_title_length(cls, v: str) -> str:
        """验证 Meta Title 长度"""
        length = len(v)
        if length < 50:
            raise ValueError(f'Meta title 太短 ({length} 字符)，应该在 50-60 字符之间')
        if length > 60:
            raise ValueError(f'Meta title 太长 ({length} 字符)，应该在 50-60 字符之间')
        return v

    @field_validator('meta_description')
    @classmethod
    def validate_meta_description_length(cls, v: str) -> str:
        """验证 Meta Description 长度"""
        length = len(v)
        if length < 150:
            raise ValueError(f'Meta description 太短 ({length} 字符)，应该在 150-160 字符之间')
        if length > 160:
            raise ValueError(f'Meta description 太长 ({length} 字符)，应该在 150-160 字符之间')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "focus_keyword": "WordPress自动化",
                "meta_title": "如何使用 Playwright 实现 WordPress 自动化发布 | 技术博客",
                "meta_description": "本文详细介绍如何使用 Playwright 和 Computer Use 实现 WordPress 后台自动化发布，包括文章创建、图片上传、SEO配置等完整流程。适合需要批量发布内容的开发者。"
            }
        }


class Article(BaseModel):
    """文章数据模型"""

    id: int = Field(..., gt=0, description="文章 ID")
    title: str = Field(..., min_length=10, max_length=200, description="文章标题")
    content_html: str = Field(..., min_length=100, description="文章内容 (HTML 格式)")
    excerpt: Optional[str] = Field(None, max_length=500, description="文章摘要")
    seo: SEOData = Field(..., description="SEO 数据")

    @field_validator('content_html')
    @classmethod
    def sanitize_html(cls, v: str) -> str:
        """清理和验证 HTML 内容"""
        # 移除危险的脚本标签
        v = re.sub(r'<script[^>]*>.*?</script>', '', v, flags=re.DOTALL | re.IGNORECASE)
        v = re.sub(r'<iframe[^>]*>.*?</iframe>', '', v, flags=re.DOTALL | re.IGNORECASE)

        # 移除事件处理属性
        v = re.sub(r'\son\w+\s*=\s*["\'][^"\']*["\']', '', v, flags=re.IGNORECASE)

        # 确保至少有一些内容
        text_content = re.sub(r'<[^>]+>', '', v).strip()
        if len(text_content) < 50:
            raise ValueError('文章内容太短（去除 HTML 标签后应至少 50 字符）')

        return v

    @field_validator('title')
    @classmethod
    def validate_title(cls, v: str) -> str:
        """验证标题"""
        # 移除前后空格
        v = v.strip()

        # 检查是否只包含空格
        if not v or v.isspace():
            raise ValueError('标题不能为空或只包含空格')

        return v

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "title": "使用 Playwright 实现浏览器自动化测试",
                "content_html": "<p>Playwright 是由微软开发的现代浏览器自动化框架...</p><h2>核心功能</h2><p>...</p>",
                "excerpt": "本文介绍 Playwright 的核心功能和使用方法。",
                "seo": {
                    "focus_keyword": "Playwright",
                    "meta_title": "使用 Playwright 实现浏览器自动化测试 | 技术教程",
                    "meta_description": "Playwright 是一个强大的浏览器自动化工具，本文详细介绍其核心功能、安装配置、实战应用等内容，帮助你快速上手并掌握这个现代化的测试框架。"
                }
            }
        }


class ImageAsset(BaseModel):
    """图片资源模型"""

    file_path: str = Field(..., description="图片文件路径")
    alt_text: str = Field(..., min_length=5, max_length=100, description="替代文字 (用于 SEO 和无障碍)")
    title: str = Field(..., min_length=1, max_length=100, description="图片标题")
    caption: str = Field(default="", max_length=500, description="图片说明")
    keywords: List[str] = Field(default_factory=list, max_length=10, description="图片关键字")
    photographer: str = Field(default="", max_length=100, description="摄影师/来源")
    is_featured: bool = Field(default=False, description="是否为特色图片")

    @field_validator('file_path')
    @classmethod
    def validate_file_exists(cls, v: str) -> str:
        """验证文件存在且为有效图片格式"""
        path = Path(v)

        if not path.exists():
            raise ValueError(f'图片文件不存在: {v}')

        if not path.is_file():
            raise ValueError(f'路径不是文件: {v}')

        # 验证文件扩展名
        valid_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}
        if path.suffix.lower() not in valid_extensions:
            raise ValueError(f'不支持的图片格式: {path.suffix}，支持的格式: {", ".join(valid_extensions)}')

        # 验证文件大小（不超过 10MB）
        max_size_mb = 10
        file_size_mb = path.stat().st_size / (1024 * 1024)
        if file_size_mb > max_size_mb:
            raise ValueError(f'图片文件过大: {file_size_mb:.2f}MB，最大支持 {max_size_mb}MB')

        return str(path.absolute())

    @field_validator('keywords')
    @classmethod
    def validate_keywords(cls, v: List[str]) -> List[str]:
        """验证关键字列表"""
        # 移除空字符串和重复项
        cleaned = list(set(k.strip() for k in v if k.strip()))

        if len(cleaned) > 10:
            raise ValueError(f'关键字数量过多 ({len(cleaned)} 个)，最多支持 10 个')

        return cleaned

    class Config:
        json_schema_extra = {
            "example": {
                "file_path": "/home/user/images/feature-image.jpg",
                "alt_text": "Playwright 浏览器自动化架构图",
                "title": "Playwright 架构",
                "caption": "Playwright 的核心架构组件示意图",
                "keywords": ["Playwright", "架构", "自动化", "浏览器"],
                "photographer": "技术团队",
                "is_featured": True
            }
        }


class ArticleMetadata(BaseModel):
    """文章元数据模型"""

    tags: List[str] = Field(default_factory=list, max_length=10, description="文章标签 (最多 10 个)")
    categories: List[str] = Field(default_factory=list, max_length=5, description="文章分类 (最多 5 个)")
    publish_immediately: bool = Field(default=True, description="是否立即发布")
    publish_date: Optional[datetime] = Field(None, description="排程发布时间")
    status: str = Field(default="draft", pattern="^(draft|publish|scheduled)$", description="文章状态")

    @model_validator(mode='after')
    def validate_publish_date_logic(self):
        """验证发布日期逻辑"""
        # 如果立即发布，不应该设置发布日期
        if self.publish_immediately and self.publish_date is not None:
            raise ValueError('立即发布时不应设置 publish_date')

        # 如果不立即发布，必须设置发布日期
        if not self.publish_immediately and self.publish_date is None:
            raise ValueError('排程发布时必须设置 publish_date')

        # 发布日期不能是过去的时间
        if self.publish_date and self.publish_date < datetime.now():
            raise ValueError('发布日期不能是过去的时间')

        return self

    @field_validator('tags', 'categories')
    @classmethod
    def validate_string_lists(cls, v: List[str]) -> List[str]:
        """验证标签和分类列表"""
        # 移除空字符串和重复项，保持顺序
        seen = set()
        cleaned = []
        for item in v:
            item_stripped = item.strip()
            if item_stripped and item_stripped not in seen:
                cleaned.append(item_stripped)
                seen.add(item_stripped)

        return cleaned

    class Config:
        json_schema_extra = {
            "example": {
                "tags": ["Playwright", "自动化", "测试", "教程"],
                "categories": ["技术", "教程"],
                "publish_immediately": True,
                "status": "publish"
            }
        }


class WordPressCredentials(BaseModel):
    """WordPress 登录凭证"""

    username: str = Field(..., min_length=3, max_length=60, description="WordPress 用户名")
    password: str = Field(..., min_length=8, description="WordPress 密码")

    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        """验证用户名格式"""
        v = v.strip()

        # 用户名不能包含特殊字符（WordPress 限制）
        if not re.match(r'^[a-zA-Z0-9_\-@.]+$', v):
            raise ValueError('用户名只能包含字母、数字、下划线、连字符、@ 和点')

        return v

    class Config:
        json_schema_extra = {
            "example": {
                "username": "admin",
                "password": "secure_password_123"
            }
        }


class PublishingContext(BaseModel):
    """发布上下文（在整个发布流程中传递的数据）"""

    task_id: str = Field(..., description="任务唯一标识符")
    article: Article = Field(..., description="文章数据")
    images: List[ImageAsset] = Field(default_factory=list, description="图片资源列表")
    metadata: ArticleMetadata = Field(..., description="文章元数据")
    wordpress_url: str = Field(..., description="WordPress 站点 URL")
    credentials: WordPressCredentials = Field(..., description="WordPress 登录凭证")
    browser_cookies: Optional[List[dict]] = Field(None, description="浏览器 Cookies (用于会话恢复)")
    published_url: Optional[str] = Field(None, description="文章发布后的 URL")
    completed_phases: List[str] = Field(default_factory=list, description="已完成的阶段列表")

    @field_validator('wordpress_url')
    @classmethod
    def validate_wordpress_url(cls, v: str) -> str:
        """验证 WordPress URL 格式"""
        v = v.strip().rstrip('/')

        if not v.startswith(('http://', 'https://')):
            raise ValueError('WordPress URL 必须以 http:// 或 https:// 开头')

        # 简单的 URL 格式验证
        url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        if not re.match(url_pattern, v):
            raise ValueError('WordPress URL 格式无效')

        return v

    class Config:
        arbitrary_types_allowed = True
        json_schema_extra = {
            "example": {
                "task_id": "pub-20251027-123456",
                "article": {"id": 1, "title": "测试文章", "...": "..."},
                "wordpress_url": "https://example.com",
                "credentials": {"username": "admin", "password": "password"}
            }
        }


class PublishResult(BaseModel):
    """发布结果"""

    success: bool = Field(..., description="是否发布成功")
    task_id: str = Field(..., description="任务 ID")
    url: Optional[str] = Field(None, description="发布后的文章 URL")
    audit_trail: Optional[dict] = Field(None, description="审计追踪日志")
    error: Optional[str] = Field(None, description="错误信息（如果失败）")
    duration_seconds: float = Field(default=0.0, ge=0, description="发布耗时（秒）")
    provider_used: str = Field(default="unknown", description="使用的 Provider (playwright/computer_use)")
    fallback_triggered: bool = Field(default=False, description="是否触发了降级机制")
    retry_count: int = Field(default=0, ge=0, description="重试次数")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "task_id": "pub-20251027-123456",
                "url": "https://example.com/2025/10/27/test-article/",
                "duration_seconds": 120.5,
                "provider_used": "playwright",
                "fallback_triggered": False,
                "retry_count": 0
            }
        }


# 类型别名（用于类型提示）
from typing import TypeAlias

ArticleInput: TypeAlias = Article
ImageInput: TypeAlias = ImageAsset
MetadataInput: TypeAlias = ArticleMetadata
