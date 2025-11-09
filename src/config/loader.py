"""
WordPress Publishing Service - Configuration Loader

此模块负责加载和管理所有配置：
- 环境变量 (.env)
- Selectors 配置 (config/selectors.yaml)
- Instructions 配置 (config/instructions.yaml)
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator, ConfigDict


class Settings(BaseSettings):
    """应用程序设置 (从环境变量加载)"""

    model_config = ConfigDict(
        extra='ignore',
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False
    )

    # ==================== WordPress 配置 ====================
    wordpress_url: str = Field(default="http://localhost:8000", description="WordPress 站点 URL")
    wordpress_username: str = Field(default="admin", description="WordPress 用户名")
    wordpress_password: str = Field(default="password", description="WordPress 密码")

    # ==================== Anthropic API 配置 ====================
    anthropic_api_key: str = Field(default="", description="Anthropic API Key")
    anthropic_model: str = Field(default="claude-sonnet-4-5-20250929", description="使用的模型")
    anthropic_timeout: int = Field(default=300, description="API 超时时间 (秒)")

    # ==================== 应用配置 ====================
    environment: str = Field(default="development", description="运行环境")
    log_level: str = Field(default="INFO", description="日志级别")
    log_file: str = Field(default="logs/app.log", description="日志文件路径")
    debug_mode: bool = Field(default=True, description="是否启用调试模式")

    # ==================== Provider 配置 ====================
    default_provider: str = Field(default="playwright", description="默认 Provider")
    enable_fallback: bool = Field(default=True, description="是否启用降级机制")
    playwright_max_retries: int = Field(default=3, description="Playwright 重试次数")
    playwright_timeout: int = Field(default=30000, description="Playwright 超时时间 (毫秒)")
    playwright_headless: bool = Field(default=False, description="是否使用无头模式")
    computer_use_max_retries: int = Field(default=2, description="Computer Use 重试次数")

    # ==================== 浏览器配置 ====================
    browser_type: str = Field(default="chromium", description="浏览器类型")
    browser_width: int = Field(default=1920, description="浏览器窗口宽度")
    browser_height: int = Field(default=1080, description="浏览器窗口高度")
    browser_devtools: bool = Field(default=False, description="是否启用 DevTools")
    browser_download_path: str = Field(default="./downloads", description="下载路径")

    # ==================== 截图和审计配置 ====================
    enable_screenshots: bool = Field(default=True, description="是否启用截图")
    screenshot_path: str = Field(default="./screenshots", description="截图保存路径")
    screenshot_quality: int = Field(default=90, ge=0, le=100, description="截图质量")
    enable_audit_trail: bool = Field(default=True, description="是否启用审计追踪")
    audit_log_path: str = Field(default="logs/audit.json", description="审计日志路径")

    # ==================== 文件上传配置 ====================
    upload_temp_dir: str = Field(default="./uploads/temp", description="上传临时目录")
    upload_max_size_mb: int = Field(default=10, description="上传最大大小 (MB)")
    allowed_image_formats: str = Field(default="jpg,jpeg,png,gif,webp,bmp", description="允许的图片格式")

    # ==================== FastAPI 服务器配置 ====================
    api_host: str = Field(default="0.0.0.0", description="API 服务器主机")
    api_port: int = Field(default=8080, description="API 服务器端口")
    api_workers: int = Field(default=4, description="API Workers 数量")
    api_docs_enabled: bool = Field(default=True, description="是否启用 API 文档")
    api_docs_url: str = Field(default="/docs", description="API 文档路径")
    cors_origins: str = Field(default="http://localhost:3000,http://localhost:8080", description="CORS 允许的源")

    # ==================== Prometheus 监控配置 ====================
    enable_metrics: bool = Field(default=True, description="是否启用 Prometheus 指标")
    metrics_port: int = Field(default=9090, description="Prometheus 指标端口")
    metrics_path: str = Field(default="/metrics", description="Prometheus 指标路径")

    # ==================== 性能和限制配置 ====================
    max_concurrent_tasks: int = Field(default=3, description="最大并发任务数")
    task_timeout: int = Field(default=600, description="任务超时时间 (秒)")
    autosave_interval: int = Field(default=30, description="自动保存间隔 (秒)")
    page_load_timeout: int = Field(default=60, description="页面加载超时 (秒)")
    element_wait_timeout: int = Field(default=10, description="元素等待超时 (秒)")

    # ==================== 测试环境配置 ====================
    test_wordpress_url: str = Field(default="http://localhost:8000", description="测试 WordPress URL")
    test_wordpress_username: str = Field(default="admin", description="测试用户名")
    test_wordpress_password: str = Field(default="password", description="测试密码")
    test_cleanup: bool = Field(default=True, description="是否在测试后清理数据")

    # ==================== 选择器配置路径 ====================
    selectors_config_path: str = Field(default="config/selectors.yaml", description="Selectors 配置路径")
    instructions_config_path: str = Field(default="config/instructions.yaml", description="Instructions 配置路径")

    # ==================== 功能开关 ====================
    enable_computer_use: bool = Field(default=True, description="是否启用 Computer Use Provider")
    enable_playwright: bool = Field(default=True, description="是否启用 Playwright Provider")
    enable_image_optimization: bool = Field(default=False, description="是否启用图片优化")
    enable_auto_seo_suggestions: bool = Field(default=False, description="是否启用自动 SEO 建议")
    enable_content_proofreading: bool = Field(default=False, description="是否启用内容校对")

    @field_validator('wordpress_url', 'test_wordpress_url')
    @classmethod
    def validate_url(cls, v: str) -> str:
        """验证 URL 格式"""
        v = v.strip().rstrip('/')
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL 必须以 http:// 或 https:// 开头')
        return v

    @field_validator('default_provider')
    @classmethod
    def validate_provider(cls, v: str) -> str:
        """验证 Provider 类型"""
        valid_providers = {'playwright', 'computer_use'}
        if v not in valid_providers:
            raise ValueError(f'Provider 必须是 {valid_providers} 之一')
        return v

    @field_validator('browser_type')
    @classmethod
    def validate_browser(cls, v: str) -> str:
        """验证浏览器类型"""
        valid_browsers = {'chromium', 'firefox', 'webkit'}
        if v not in valid_browsers:
            raise ValueError(f'浏览器类型必须是 {valid_browsers} 之一')
        return v

    def get_allowed_image_formats(self) -> list[str]:
        """获取允许的图片格式列表"""
        return [fmt.strip().lower() for fmt in self.allowed_image_formats.split(',')]

    def get_cors_origins(self) -> list[str]:
        """获取 CORS 允许的源列表"""
        return [origin.strip() for origin in self.cors_origins.split(',')]


class SelectorConfig:
    """
    选择器配置封装类
    用于 Playwright Provider 访问选择器
    """

    def __init__(self, selectors: Dict[str, Any]):
        """
        Args:
            selectors: 选择器配置字典
        """
        self.selectors = selectors

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取选择器配置

        Args:
            key: 选择器键名
            default: 默认值

        Returns:
            选择器字符串或列表
        """
        return self.selectors.get(key, default)

    def get_all_selectors(self, key: str) -> list[str]:
        """
        获取所有备选选择器（支持多选择器）

        Args:
            key: 选择器键名

        Returns:
            选择器列表
        """
        value = self.get(key)
        if value is None:
            return []
        return value if isinstance(value, list) else [value]

    def validate(self) -> bool:
        """
        验证配置完整性

        Returns:
            是否验证通过
        """
        required_keys = [
            'new_post_title', 'content_textarea', 'add_media_button',
            'save_draft', 'publish'
        ]
        missing = [key for key in required_keys if key not in self.selectors]
        if missing:
            raise ValueError(f"Missing required selectors: {missing}")
        return True

    @classmethod
    def load_from_file(cls, file_path: str) -> 'SelectorConfig':
        """
        从 YAML 文件加载配置

        Args:
            file_path: 配置文件路径

        Returns:
            SelectorConfig 实例
        """
        full_path = Path(file_path)

        if not full_path.exists():
            raise FileNotFoundError(f'Selector config not found: {file_path}')

        with open(full_path, 'r', encoding='utf-8') as f:
            config_dict = yaml.safe_load(f)

        return cls(config_dict)


class ConfigLoader:
    """配置加载器"""

    def __init__(self, base_path: Optional[Path] = None):
        """
        初始化配置加载器

        Args:
            base_path: 项目根目录路径，默认为当前工作目录
        """
        self.base_path = base_path or Path.cwd()
        self._settings: Optional[Settings] = None
        self._selectors: Optional[Dict[str, Any]] = None
        self._instructions: Optional[Dict[str, Any]] = None
        self._selector_config: Optional[SelectorConfig] = None

    @property
    def settings(self) -> Settings:
        """获取应用程序设置 (懒加载)"""
        if self._settings is None:
            self._settings = Settings()
        return self._settings

    @property
    def selectors(self) -> Dict[str, Any]:
        """获取选择器配置 (懒加载)"""
        if self._selectors is None:
            self._selectors = self.load_yaml_config(self.settings.selectors_config_path)
        return self._selectors

    @property
    def selector_config(self) -> SelectorConfig:
        """获取选择器配置对象 (懒加载)"""
        if self._selector_config is None:
            self._selector_config = SelectorConfig(self.selectors)
        return self._selector_config

    @property
    def instructions(self) -> Dict[str, Any]:
        """获取指令配置 (懒加载)"""
        if self._instructions is None:
            self._instructions = self.load_yaml_config(self.settings.instructions_config_path)
        return self._instructions

    def load_yaml_config(self, config_path: str) -> Dict[str, Any]:
        """
        加载 YAML 配置文件

        Args:
            config_path: 配置文件路径 (相对于 base_path)

        Returns:
            配置字典

        Raises:
            FileNotFoundError: 配置文件不存在
            yaml.YAMLError: YAML 解析错误
        """
        full_path = self.base_path / config_path

        if not full_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {full_path}")

        with open(full_path, 'r', encoding='utf-8') as f:
            try:
                config = yaml.safe_load(f)
                return config or {}
            except yaml.YAMLError as e:
                raise yaml.YAMLError(f"YAML 解析错误 ({full_path}): {e}")

    def get_selector(self, *keys: str) -> Optional[str]:
        """
        获取选择器

        Args:
            *keys: 选择器路径，例如 ('login', 'username_input')

        Returns:
            选择器字符串，如果不存在则返回 None

        Example:
            >>> config.get_selector('login', 'username_input')
            '#user_login'
        """
        result = self.selectors
        for key in keys:
            if isinstance(result, dict) and key in result:
                result = result[key]
            else:
                return None
        return result if isinstance(result, str) else None

    def get_instruction(self, *keys: str) -> Optional[str]:
        """
        获取指令模板

        Args:
            *keys: 指令路径，例如 ('login', 'enter_credentials')

        Returns:
            指令字符串，如果不存在则返回 None

        Example:
            >>> config.get_instruction('login', 'enter_credentials')
            'On the WordPress login page: ...'
        """
        result = self.instructions
        for key in keys:
            if isinstance(result, dict) and key in result:
                result = result[key]
            else:
                return None

        # 如果结果是字典且包含 'instruction' 键，返回 instruction
        if isinstance(result, dict) and 'instruction' in result:
            return result['instruction'].strip()

        return result if isinstance(result, str) else None

    def format_instruction(self, *keys: str, **kwargs) -> Optional[str]:
        """
        获取并格式化指令模板

        Args:
            *keys: 指令路径
            **kwargs: 格式化参数

        Returns:
            格式化后的指令字符串

        Example:
            >>> config.format_instruction('article', 'enter_title', title='My Article')
            'On the post editor page: ... Type the article title: My Article'
        """
        template = self.get_instruction(*keys)
        if template is None:
            return None

        try:
            return template.format(**kwargs)
        except KeyError as e:
            raise KeyError(f"指令模板缺少参数 {e}")

    def validate_selectors(self) -> Dict[str, list[str]]:
        """
        验证选择器配置

        Returns:
            验证结果，包含 'missing_critical', 'missing_important', 'missing_optional'

        Example:
            >>> results = config.validate_selectors()
            >>> if results['missing_critical']:
            ...     print("缺少关键选择器:", results['missing_critical'])
        """
        validation_config = self.selectors.get('validation', {})
        results = {
            'missing_critical': [],
            'missing_important': [],
            'missing_optional': []
        }

        for level in ['critical', 'important', 'optional']:
            selector_paths = validation_config.get(level, [])
            for path in selector_paths:
                keys = path.split('.')
                if self.get_selector(*keys) is None:
                    results[f'missing_{level}'].append(path)

        return results

    def reload(self):
        """重新加载所有配置"""
        self._settings = None
        self._selectors = None
        self._instructions = None

    def __repr__(self) -> str:
        return f"ConfigLoader(base_path={self.base_path})"


# ==================== 全局配置实例 ====================

# 创建全局配置加载器实例
config = ConfigLoader()

# 导出常用对象
settings = config.settings


# ==================== 辅助函数 ====================

def get_selector(*keys: str) -> Optional[str]:
    """获取选择器 (全局快捷方式)"""
    return config.get_selector(*keys)


def get_instruction(*keys: str) -> Optional[str]:
    """获取指令 (全局快捷方式)"""
    return config.get_instruction(*keys)


def format_instruction(*keys: str, **kwargs) -> Optional[str]:
    """格式化指令 (全局快捷方式)"""
    return config.format_instruction(*keys, **kwargs)


def load_selector_config(config_path: Optional[str] = None) -> SelectorConfig:
    """
    加载选择器配置

    Args:
        config_path: 配置文件路径，默认使用 config/selectors.yaml

    Returns:
        SelectorConfig 实例
    """
    if config_path is None:
        return config.selector_config
    else:
        return SelectorConfig.load_from_file(config_path)
