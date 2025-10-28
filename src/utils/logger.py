"""
WordPress Publishing Service - Logging System

此模块提供统一的日志记录功能，支持：
- 控制台和文件日志
- 结构化日志 (JSON)
- 审计追踪
- 按模块分类的日志
"""

import logging
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler


class JSONFormatter(logging.Formatter):
    """JSON 格式化器"""

    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录为 JSON"""
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }

        # 添加异常信息
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        # 添加额外的上下文数据
        if hasattr(record, 'extra_data'):
            log_data['extra'] = record.extra_data

        return json.dumps(log_data, ensure_ascii=False)


class StructuredLogger:
    """结构化日志记录器"""

    def __init__(
        self,
        name: str,
        log_file: Optional[str] = None,
        log_level: str = "INFO",
        enable_console: bool = True,
        enable_json: bool = False,
    ):
        """
        初始化日志记录器

        Args:
            name: 日志记录器名称
            log_file: 日志文件路径
            log_level: 日志级别
            enable_console: 是否启用控制台输出
            enable_json: 是否使用 JSON 格式
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, log_level.upper()))
        self.logger.propagate = False

        # 清除现有的 handlers
        self.logger.handlers.clear()

        # 控制台 Handler
        if enable_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.DEBUG)

            if enable_json:
                console_handler.setFormatter(JSONFormatter())
            else:
                console_format = logging.Formatter(
                    '[%(asctime)s] [%(levelname)8s] [%(name)s] %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                )
                console_handler.setFormatter(console_format)

            self.logger.addHandler(console_handler)

        # 文件 Handler
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            # 使用 Rotating File Handler (按大小轮转)
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=10 * 1024 * 1024,  # 10 MB
                backupCount=5,
                encoding='utf-8'
            )
            file_handler.setLevel(logging.DEBUG)

            if enable_json:
                file_handler.setFormatter(JSONFormatter())
            else:
                file_format = logging.Formatter(
                    '[%(asctime)s] [%(levelname)8s] [%(name)s] [%(module)s:%(funcName)s:%(lineno)d] %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                )
                file_handler.setFormatter(file_format)

            self.logger.addHandler(file_handler)

    def debug(self, message: str, **kwargs):
        """记录 DEBUG 级别日志"""
        self._log(logging.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs):
        """记录 INFO 级别日志"""
        self._log(logging.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs):
        """记录 WARNING 级别日志"""
        self._log(logging.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs):
        """记录 ERROR 级别日志"""
        self._log(logging.ERROR, message, **kwargs)

    def critical(self, message: str, **kwargs):
        """记录 CRITICAL 级别日志"""
        self._log(logging.CRITICAL, message, **kwargs)

    def exception(self, message: str, **kwargs):
        """记录异常信息"""
        self._log(logging.ERROR, message, exc_info=True, **kwargs)

    def _log(self, level: int, message: str, exc_info: bool = False, **kwargs):
        """内部日志记录方法"""
        extra = {'extra_data': kwargs} if kwargs else {}
        self.logger.log(level, message, exc_info=exc_info, extra=extra)


class AuditLogger:
    """审计日志记录器 - 用于记录重要操作"""

    def __init__(self, audit_file: str = "logs/audit.json"):
        """
        初始化审计日志记录器

        Args:
            audit_file: 审计日志文件路径
        """
        self.audit_file = Path(audit_file)
        self.audit_file.parent.mkdir(parents=True, exist_ok=True)

        # 创建专门的审计日志记录器
        self.logger = logging.getLogger('audit')
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False
        self.logger.handlers.clear()

        # 使用 Timed Rotating File Handler (按天轮转)
        audit_handler = TimedRotatingFileHandler(
            audit_file,
            when='midnight',
            interval=1,
            backupCount=30,  # 保留 30 天
            encoding='utf-8'
        )
        audit_handler.setFormatter(JSONFormatter())
        self.logger.addHandler(audit_handler)

    def log_action(
        self,
        action: str,
        task_id: str,
        status: str,
        details: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ):
        """
        记录操作

        Args:
            action: 操作类型 (如 'login', 'create_article', 'upload_image')
            task_id: 任务 ID
            status: 状态 ('success', 'failure', 'pending')
            details: 详细信息
            error: 错误信息 (如果有)
        """
        audit_entry = {
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'task_id': task_id,
            'status': status,
        }

        if details:
            audit_entry['details'] = details

        if error:
            audit_entry['error'] = error

        # 使用 extra_data 传递结构化数据
        extra = {'extra_data': audit_entry}
        self.logger.info(f"Audit: {action} - {status}", extra=extra)


# ==================== 全局日志实例 ====================

def get_logger(
    name: str,
    log_file: Optional[str] = None,
    log_level: Optional[str] = None
) -> StructuredLogger:
    """
    获取日志记录器实例

    Args:
        name: 日志记录器名称
        log_file: 日志文件路径 (可选，默认从配置读取)
        log_level: 日志级别 (可选，默认从配置读取)

    Returns:
        StructuredLogger 实例

    Example:
        >>> logger = get_logger('publisher')
        >>> logger.info('开始发布文章', task_id='123', article_id=456)
    """
    # 尝试从配置加载默认值
    if log_file is None or log_level is None:
        try:
            from src.config.loader import settings
            log_file = log_file or settings.log_file
            log_level = log_level or settings.log_level
        except ImportError:
            # 如果配置未加载，使用默认值
            log_file = log_file or "logs/app.log"
            log_level = log_level or "INFO"

    return StructuredLogger(
        name=name,
        log_file=log_file,
        log_level=log_level,
        enable_console=True,
        enable_json=False
    )


def get_audit_logger(audit_file: Optional[str] = None) -> AuditLogger:
    """
    获取审计日志记录器

    Args:
        audit_file: 审计日志文件路径 (可选，默认从配置读取)

    Returns:
        AuditLogger 实例

    Example:
        >>> audit = get_audit_logger()
        >>> audit.log_action('publish', 'task-123', 'success', details={'url': 'http://...'})
    """
    if audit_file is None:
        try:
            from src.config.loader import settings
            audit_file = settings.audit_log_path
        except ImportError:
            audit_file = "logs/audit.json"

    return AuditLogger(audit_file=audit_file)


# ==================== 模块级日志实例 ====================

# 创建默认的应用日志记录器
app_logger = get_logger('app')

# 创建默认的审计日志记录器
audit_logger = get_audit_logger()


# ==================== 便捷函数 ====================

def debug(message: str, **kwargs):
    """全局 DEBUG 日志"""
    app_logger.debug(message, **kwargs)


def info(message: str, **kwargs):
    """全局 INFO 日志"""
    app_logger.info(message, **kwargs)


def warning(message: str, **kwargs):
    """全局 WARNING 日志"""
    app_logger.warning(message, **kwargs)


def error(message: str, **kwargs):
    """全局 ERROR 日志"""
    app_logger.error(message, **kwargs)


def critical(message: str, **kwargs):
    """全局 CRITICAL 日志"""
    app_logger.critical(message, **kwargs)


def exception(message: str, **kwargs):
    """全局异常日志"""
    app_logger.exception(message, **kwargs)
