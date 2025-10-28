"""
发布安全验证机制
防止意外发布或错误操作
"""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class PublishingIntent(Enum):
    """发布意图"""
    SAVE_DRAFT = "save_draft"  # 仅保存草稿
    PUBLISH_NOW = "publish_now"  # 立即发布
    SCHEDULE = "schedule"  # 排程发布


class ArticleStatus(Enum):
    """文章状态"""
    DRAFT = "draft"
    PENDING = "pending"
    PUBLISHED = "published"
    SCHEDULED = "scheduled"
    UNKNOWN = "unknown"


@dataclass
class PreflightCheck:
    """发布前检查项"""
    name: str
    passed: bool
    message: str
    critical: bool  # 是否为关键检查（失败则阻止发布）


@dataclass
class PublishingSafetyResult:
    """安全验证结果"""
    safe_to_publish: bool
    checks: List[PreflightCheck]
    warnings: List[str]
    errors: List[str]

    def get_failed_critical_checks(self) -> List[PreflightCheck]:
        """获取失败的关键检查"""
        return [c for c in self.checks if c.critical and not c.passed]

    def get_summary(self) -> str:
        """生成摘要"""
        total = len(self.checks)
        passed = sum(1 for c in self.checks if c.passed)
        failed = total - passed
        
        summary = f"安全检查: {passed}/{total} 通过"
        if failed > 0:
            summary += f", {failed} 失败"
        if self.warnings:
            summary += f", {len(self.warnings)} 警告"
        if self.errors:
            summary += f", {len(self.errors)} 错误"
        
        return summary


class PublishingSafetyValidator:
    """
    发布安全验证器
    
    核心功能：
    1. 发布前检查（Preflight checks）
    2. 状态验证
    3. 意图确认
    4. 错误降级（失败时保存为草稿）
    """

    def __init__(self):
        """初始化安全验证器"""
        self.checks: List[PreflightCheck] = []

    async def validate_before_publish(
        self,
        provider,
        intent: PublishingIntent,
        article_data: Dict,
        metadata: Dict
    ) -> PublishingSafetyResult:
        """
        发布前完整验证
        
        Args:
            provider: Provider 实例
            intent: 发布意图
            article_data: 文章数据
            metadata: 元数据
        
        Returns:
            安全验证结果
        """
        logger.info(f"🔒 开始发布安全验证 (Intent: {intent.value})")
        
        self.checks = []
        warnings = []
        errors = []

        # 1. 验证内容完整性
        await self._check_content_completeness(article_data)

        # 2. 验证草稿状态
        await self._check_draft_status(provider)

        # 3. 验证内容已保存
        await self._check_content_saved(provider)

        # 4. 验证发布意图匹配
        await self._check_intent_match(provider, intent)

        # 5. 验证必填元数据
        await self._check_required_metadata(metadata)

        # 6. 如果是排程发布，验证时间
        if intent == PublishingIntent.SCHEDULE:
            await self._check_schedule_time(metadata.get('publish_date'))

        # 汇总结果
        failed_critical = self.get_failed_critical_checks()
        
        if failed_critical:
            errors.append(f"关键检查失败: {[c.name for c in failed_critical]}")
            safe_to_publish = False
        else:
            safe_to_publish = True

        result = PublishingSafetyResult(
            safe_to_publish=safe_to_publish,
            checks=self.checks,
            warnings=warnings,
            errors=errors
        )

        logger.info(f"✅ 安全验证完成: {result.get_summary()}")
        
        if not safe_to_publish:
            logger.error(f"❌ 发布被阻止: {result.errors}")
        
        return result

    async def _check_content_completeness(self, article_data: Dict):
        """检查内容完整性"""
        title = article_data.get('title', '')
        content = article_data.get('content', '')

        # 检查标题
        if not title or len(title.strip()) == 0:
            self.checks.append(PreflightCheck(
                name="标题检查",
                passed=False,
                message="标题为空",
                critical=True
            ))
        elif len(title) < 5:
            self.checks.append(PreflightCheck(
                name="标题检查",
                passed=False,
                message=f"标题过短（{len(title)}字符）",
                critical=True
            ))
        else:
            self.checks.append(PreflightCheck(
                name="标题检查",
                passed=True,
                message=f"标题正常（{len(title)}字符）",
                critical=True
            ))

        # 检查内容
        if not content or len(content.strip()) == 0:
            self.checks.append(PreflightCheck(
                name="内容检查",
                passed=False,
                message="内容为空",
                critical=True
            ))
        elif len(content) < 50:
            self.checks.append(PreflightCheck(
                name="内容检查",
                passed=False,
                message=f"内容过短（{len(content)}字符）",
                critical=True
            ))
        else:
            self.checks.append(PreflightCheck(
                name="内容检查",
                passed=True,
                message=f"内容正常（{len(content)}字符）",
                critical=True
            ))

    async def _check_draft_status(self, provider):
        """检查草稿状态"""
        try:
            is_draft = await provider.verify_draft_status()
            
            self.checks.append(PreflightCheck(
                name="草稿状态",
                passed=is_draft,
                message="文章为草稿状态" if is_draft else "文章已发布或非草稿",
                critical=True
            ))
        except Exception as e:
            logger.warning(f"无法验证草稿状态: {e}")
            self.checks.append(PreflightCheck(
                name="草稿状态",
                passed=False,
                message=f"无法验证: {str(e)}",
                critical=True
            ))

    async def _check_content_saved(self, provider):
        """检查内容已保存"""
        try:
            is_saved = await provider.verify_content_saved()
            
            self.checks.append(PreflightCheck(
                name="内容保存",
                passed=is_saved,
                message="内容已保存" if is_saved else "内容未保存",
                critical=True
            ))
        except Exception as e:
            logger.warning(f"无法验证保存状态: {e}")
            self.checks.append(PreflightCheck(
                name="内容保存",
                passed=False,
                message=f"无法验证: {str(e)}",
                critical=False  # 非关键
            ))

    async def _check_intent_match(self, provider, intent: PublishingIntent):
        """检查意图匹配"""
        # 如果意图是保存草稿，总是通过
        if intent == PublishingIntent.SAVE_DRAFT:
            self.checks.append(PreflightCheck(
                name="发布意图",
                passed=True,
                message="仅保存草稿，安全",
                critical=False
            ))
            return

        # 如果意图是发布，需要额外确认
        self.checks.append(PreflightCheck(
            name="发布意图",
            passed=True,
            message=f"意图: {intent.value}",
            critical=False
        ))

    async def _check_required_metadata(self, metadata: Dict):
        """检查必填元数据"""
        # 检查分类
        categories = metadata.get('categories', [])
        if not categories:
            self.checks.append(PreflightCheck(
                name="分类设置",
                passed=False,
                message="未设置分类",
                critical=False  # 警告，不阻止发布
            ))
        else:
            self.checks.append(PreflightCheck(
                name="分类设置",
                passed=True,
                message=f"分类: {', '.join(categories)}",
                critical=False
            ))

    async def _check_schedule_time(self, publish_date: Optional[datetime]):
        """检查排程时间"""
        if not publish_date:
            self.checks.append(PreflightCheck(
                name="排程时间",
                passed=False,
                message="未设置排程时间",
                critical=True
            ))
            return

        now = datetime.now()
        if publish_date <= now:
            self.checks.append(PreflightCheck(
                name="排程时间",
                passed=False,
                message=f"排程时间（{publish_date}）早于当前时间",
                critical=True
            ))
        else:
            self.checks.append(PreflightCheck(
                name="排程时间",
                passed=True,
                message=f"排程时间: {publish_date}",
                critical=False
            ))

    def get_failed_critical_checks(self) -> List[PreflightCheck]:
        """获取失败的关键检查"""
        return [c for c in self.checks if c.critical and not c.passed]

    def get_all_checks(self) -> List[PreflightCheck]:
        """获取所有检查"""
        return self.checks


# ==================== 错误恢复策略 ====================

class ErrorRecoveryStrategy:
    """
    错误恢复策略
    
    当发布操作失败时的恢复方案
    """

    @staticmethod
    async def save_as_draft_on_error(provider, article_data: Dict):
        """
        失败时保存为草稿
        
        Args:
            provider: Provider 实例
            article_data: 文章数据
        
        Returns:
            是否成功保存
        """
        logger.warning("⚠️ 发布失败，尝试保存为草稿")
        
        try:
            # 确保内容已填充
            if article_data.get('title'):
                await provider.fill_input('new_post_title', article_data['title'])
            
            if article_data.get('content'):
                await provider.fill_textarea('content', article_data['content'])
            
            # 点击保存草稿
            await provider.click_button('save_draft')
            await provider.wait_for_success_message('草稿')
            
            logger.info("✅ 成功保存为草稿")
            return True
        except Exception as e:
            logger.error(f"❌ 保存草稿失败: {e}")
            return False

    @staticmethod
    async def capture_error_state(provider, error: Exception) -> Dict:
        """
        捕获错误时的状态
        
        Args:
            provider: Provider 实例
            error: 错误对象
        
        Returns:
            状态信息字典
        """
        state = {
            'timestamp': datetime.now().isoformat(),
            'error': str(error),
            'error_type': type(error).__name__,
            'screenshot': None,
            'post_id': None
        }
        
        try:
            state['screenshot'] = await provider.capture_screenshot()
        except Exception as e:
            logger.warning(f"无法捕获截图: {e}")
        
        try:
            state['post_id'] = await provider.get_current_post_id()
        except Exception as e:
            logger.warning(f"无法获取文章ID: {e}")
        
        return state
