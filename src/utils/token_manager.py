"""
Token 使用管理和优化

提供 Token 追踪、监控和优化建议
"""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class TokenUsage:
    """Token 使用记录"""
    timestamp: datetime
    operation: str  # 操作名称
    input_tokens: int
    output_tokens: int
    total_tokens: int

    @property
    def cost_estimate(self) -> float:
        """
        估算成本（美元）

        Claude 3.5 Sonnet 定价（2024年10月）:
        - Input: $3 / 1M tokens
        - Output: $15 / 1M tokens
        """
        input_cost = (self.input_tokens / 1_000_000) * 3.0
        output_cost = (self.output_tokens / 1_000_000) * 15.0
        return input_cost + output_cost


@dataclass
class TokenBudget:
    """Token 预算配置"""
    daily_limit: int = 1_000_000  # 每日限额
    per_session_limit: int = 100_000  # 每会话限额
    per_operation_limit: int = 10_000  # 每操作限额
    warning_threshold: float = 0.8  # 预警阈值（80%）


class TokenManager:
    """Token 使用管理器"""

    def __init__(self, budget: Optional[TokenBudget] = None):
        """
        初始化 Token 管理器

        Args:
            budget: Token 预算配置
        """
        self.budget = budget or TokenBudget()
        self.usage_history: List[TokenUsage] = []
        self.operation_stats: Dict[str, dict] = defaultdict(lambda: {
            'count': 0,
            'total_tokens': 0,
            'total_cost': 0.0
        })

        # 当前会话统计
        self.session_tokens = 0
        self.session_cost = 0.0
        self.session_start = datetime.now()

    def record_usage(
        self,
        operation: str,
        input_tokens: int,
        output_tokens: int
    ) -> TokenUsage:
        """
        记录 Token 使用

        Args:
            operation: 操作名称
            input_tokens: 输入 Token 数
            output_tokens: 输出 Token 数

        Returns:
            TokenUsage 记录
        """
        total_tokens = input_tokens + output_tokens

        usage = TokenUsage(
            timestamp=datetime.now(),
            operation=operation,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens
        )

        # 记录到历史
        self.usage_history.append(usage)

        # 更新会话统计
        self.session_tokens += total_tokens
        self.session_cost += usage.cost_estimate

        # 更新操作统计
        stats = self.operation_stats[operation]
        stats['count'] += 1
        stats['total_tokens'] += total_tokens
        stats['total_cost'] += usage.cost_estimate

        # 检查预警
        self._check_warnings(usage)

        logger.debug(
            f"Token 使用: {operation} - "
            f"输入:{input_tokens}, 输出:{output_tokens}, "
            f"总计:{total_tokens}, 成本:${usage.cost_estimate:.4f}"
        )

        return usage

    def _check_warnings(self, usage: TokenUsage):
        """检查预警条件"""
        warnings = []

        # 检查会话限额
        session_usage_percent = self.session_tokens / self.budget.per_session_limit
        if session_usage_percent >= self.budget.warning_threshold:
            warnings.append(
                f"会话 Token 使用已达 {session_usage_percent * 100:.1f}% "
                f"({self.session_tokens}/{self.budget.per_session_limit})"
            )

        # 检查单次操作限额
        if usage.total_tokens > self.budget.per_operation_limit:
            warnings.append(
                f"操作 '{usage.operation}' Token 使用过高: "
                f"{usage.total_tokens} (限额: {self.budget.per_operation_limit})"
            )

        # 发出警告
        for warning in warnings:
            logger.warning(f"⚠️ Token 预警: {warning}")

    def get_session_stats(self) -> dict:
        """
        获取当前会话统计

        Returns:
            会话统计信息字典
        """
        duration = (datetime.now() - self.session_start).total_seconds()

        return {
            'duration_seconds': duration,
            'total_tokens': self.session_tokens,
            'total_cost': self.session_cost,
            'average_tokens_per_minute': (
                (self.session_tokens / duration * 60) if duration > 0 else 0
            ),
            'budget_usage_percent': (
                (self.session_tokens / self.budget.per_session_limit * 100)
                if self.budget.per_session_limit > 0 else 0
            ),
            'estimated_daily_cost': (
                self.session_cost / duration * 86400 if duration > 0 else 0
            )
        }

    def get_operation_stats(self) -> Dict[str, dict]:
        """
        获取各操作的统计信息

        Returns:
            操作统计字典
        """
        result = {}

        for operation, stats in self.operation_stats.items():
            result[operation] = {
                'count': stats['count'],
                'total_tokens': stats['total_tokens'],
                'total_cost': stats['total_cost'],
                'avg_tokens_per_call': (
                    stats['total_tokens'] / stats['count']
                    if stats['count'] > 0 else 0
                ),
                'avg_cost_per_call': (
                    stats['total_cost'] / stats['count']
                    if stats['count'] > 0 else 0
                )
            }

        return result

    def get_optimization_recommendations(self) -> List[str]:
        """
        获取优化建议

        Returns:
            优化建议列表
        """
        recommendations = []
        operation_stats = self.get_operation_stats()

        # 检查高成本操作
        for operation, stats in operation_stats.items():
            if stats['avg_tokens_per_call'] > 5000:
                recommendations.append(
                    f"⚠️ 操作 '{operation}' 平均使用 {stats['avg_tokens_per_call']:.0f} tokens，"
                    "建议优化指令或拆分为更小的操作"
                )

        # 检查频繁操作
        total_calls = sum(s['count'] for s in operation_stats.values())
        for operation, stats in operation_stats.items():
            if stats['count'] / total_calls > 0.3:  # 超过30%的调用
                recommendations.append(
                    f"💡 操作 '{operation}' 调用频繁 ({stats['count']} 次，"
                    f"{stats['count']/total_calls*100:.1f}%)，考虑缓存或批量处理"
                )

        # 检查会话总成本
        session_stats = self.get_session_stats()
        if session_stats['total_cost'] > 1.0:  # 超过 $1
            recommendations.append(
                f"💰 当前会话成本较高: ${session_stats['total_cost']:.2f}，"
                "建议优化指令长度或减少重试次数"
            )

        # 如果没有建议
        if not recommendations:
            recommendations.append("✅ Token 使用合理，无需优化")

        return recommendations

    def generate_report(self) -> str:
        """
        生成详细的使用报告

        Returns:
            格式化的报告字符串
        """
        session_stats = self.get_session_stats()
        operation_stats = self.get_operation_stats()
        recommendations = self.get_optimization_recommendations()

        report = []
        report.append("=" * 60)
        report.append("Token 使用报告")
        report.append("=" * 60)
        report.append("")

        # 会话概览
        report.append("📊 会话概览:")
        report.append(f"  运行时长: {session_stats['duration_seconds']:.1f} 秒")
        report.append(f"  总 Token 数: {session_stats['total_tokens']:,}")
        report.append(f"  总成本: ${session_stats['total_cost']:.4f}")
        report.append(f"  预算使用率: {session_stats['budget_usage_percent']:.1f}%")
        report.append(f"  预计日成本: ${session_stats['estimated_daily_cost']:.2f}")
        report.append("")

        # 操作统计
        if operation_stats:
            report.append("📈 操作统计:")
            for operation, stats in sorted(
                operation_stats.items(),
                key=lambda x: x[1]['total_tokens'],
                reverse=True
            ):
                report.append(f"\n  {operation}:")
                report.append(f"    调用次数: {stats['count']}")
                report.append(f"    总 Token 数: {stats['total_tokens']:,}")
                report.append(f"    平均 Token/次: {stats['avg_tokens_per_call']:.0f}")
                report.append(f"    总成本: ${stats['total_cost']:.4f}")
            report.append("")

        # 优化建议
        report.append("💡 优化建议:")
        for rec in recommendations:
            report.append(f"  {rec}")
        report.append("")

        report.append("=" * 60)

        return "\n".join(report)

    def reset_session(self):
        """重置当前会话统计"""
        self.session_tokens = 0
        self.session_cost = 0.0
        self.session_start = datetime.now()
        logger.info("会话统计已重置")

    def clear_history(self):
        """清空使用历史"""
        self.usage_history.clear()
        self.operation_stats.clear()
        self.reset_session()
        logger.info("使用历史已清空")
