"""Performance and cost monitoring for unified optimization service (Phase 7).

Provides:
1. Structured logging for all optimization operations
2. Performance metrics collection
3. Cost tracking and analysis
4. Optimization recommendations
"""

import json
import logging
import structlog
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Optional
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.article import Article
from src.models.title_suggestions import TitleSuggestion
from src.models.seo_suggestions import SEOSuggestion
from src.models.article_faq import ArticleFAQ


logger = structlog.get_logger(__name__)


class OptimizationMonitor:
    """Monitor performance and cost of optimization operations."""

    # Cost constants (Claude Opus 4.5)
    INPUT_COST_PER_MILLION = 5.0  # $5 per million input tokens
    OUTPUT_COST_PER_MILLION = 25.0  # $25 per million output tokens

    # Performance thresholds
    SLOW_RESPONSE_THRESHOLD_MS = 35000  # 35 seconds
    HIGH_TOKEN_THRESHOLD = 8000  # Total tokens
    HIGH_COST_THRESHOLD_USD = 0.15  # $0.15 per article

    def __init__(self, db_session: AsyncSession):
        """Initialize monitor.

        Args:
            db_session: Database session for querying metrics
        """
        self.db = db_session

    async def log_optimization_start(
        self,
        article_id: int,
        regenerate: bool,
        context: dict[str, Any],
    ) -> None:
        """Log optimization operation start.

        Args:
            article_id: Article being optimized
            regenerate: Whether forcing regeneration
            context: Additional context (e.g., user_id, source)
        """
        logger.info(
            "optimization_started",
            article_id=article_id,
            regenerate=regenerate,
            timestamp=datetime.utcnow().isoformat(),
            **context,
        )

    async def log_optimization_success(
        self,
        article_id: int,
        metrics: dict[str, Any],
        context: dict[str, Any],
    ) -> None:
        """Log successful optimization with metrics.

        Args:
            article_id: Article ID
            metrics: Performance metrics (tokens, cost, duration)
            context: Additional context
        """
        # Calculate performance indicators
        is_slow = metrics.get("duration_ms", 0) > self.SLOW_RESPONSE_THRESHOLD_MS
        is_expensive = metrics.get("total_cost_usd", 0) > self.HIGH_COST_THRESHOLD_USD
        is_high_tokens = metrics.get("total_tokens", 0) > self.HIGH_TOKEN_THRESHOLD

        # Calculate cost efficiency (tokens per dollar)
        cost = metrics.get("total_cost_usd", 0)
        tokens = metrics.get("total_tokens", 0)
        tokens_per_dollar = tokens / cost if cost > 0 else 0

        logger.info(
            "optimization_completed",
            article_id=article_id,
            input_tokens=metrics.get("input_tokens"),
            output_tokens=metrics.get("output_tokens"),
            total_tokens=tokens,
            cost_usd=metrics.get("total_cost_usd"),
            duration_ms=metrics.get("duration_ms"),
            cached=metrics.get("cached", False),
            is_slow=is_slow,
            is_expensive=is_expensive,
            is_high_tokens=is_high_tokens,
            tokens_per_dollar=round(tokens_per_dollar, 2),
            timestamp=datetime.utcnow().isoformat(),
            **context,
        )

        # Log warnings for performance issues
        if is_slow:
            logger.warning(
                "slow_optimization_detected",
                article_id=article_id,
                duration_ms=metrics.get("duration_ms"),
                threshold_ms=self.SLOW_RESPONSE_THRESHOLD_MS,
            )

        if is_expensive:
            logger.warning(
                "expensive_optimization_detected",
                article_id=article_id,
                cost_usd=metrics.get("total_cost_usd"),
                threshold_usd=self.HIGH_COST_THRESHOLD_USD,
            )

    async def log_optimization_error(
        self,
        article_id: int,
        error: Exception,
        error_stage: str,
        context: dict[str, Any],
    ) -> None:
        """Log optimization failure.

        Args:
            article_id: Article ID
            error: Exception that occurred
            error_stage: Stage where error occurred (api_call, parsing, storage)
            context: Additional context
        """
        logger.error(
            "optimization_failed",
            article_id=article_id,
            error_type=type(error).__name__,
            error_message=str(error),
            error_stage=error_stage,
            timestamp=datetime.utcnow().isoformat(),
            **context,
        )

    async def get_cost_statistics(
        self,
        days: int = 30,
        limit: int = 100,
    ) -> dict[str, Any]:
        """Get cost statistics for recent optimizations.

        Args:
            days: Number of days to analyze
            limit: Max number of articles to analyze

        Returns:
            Statistics including total cost, average cost, cost trends
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Query articles with optimization cost data
        stmt = (
            select(Article)
            .where(
                Article.unified_optimization_generated == True,  # noqa: E712
                Article.unified_optimization_generated_at >= cutoff_date,
            )
            .order_by(Article.unified_optimization_generated_at.desc())
            .limit(limit)
        )

        result = await self.db.execute(stmt)
        articles = result.scalars().all()

        if not articles:
            return {
                "period_days": days,
                "article_count": 0,
                "total_cost_usd": 0.0,
                "average_cost_usd": 0.0,
                "min_cost_usd": 0.0,
                "max_cost_usd": 0.0,
            }

        costs = [float(a.unified_optimization_cost) for a in articles if a.unified_optimization_cost]

        return {
            "period_days": days,
            "article_count": len(articles),
            "total_cost_usd": round(sum(costs), 4),
            "average_cost_usd": round(sum(costs) / len(costs), 4) if costs else 0.0,
            "min_cost_usd": round(min(costs), 4) if costs else 0.0,
            "max_cost_usd": round(max(costs), 4) if costs else 0.0,
            "median_cost_usd": round(sorted(costs)[len(costs) // 2], 4) if costs else 0.0,
            "estimated_monthly_cost_usd": round(sum(costs) / days * 30, 2) if days > 0 else 0.0,
        }

    async def get_performance_statistics(
        self,
        days: int = 7,
    ) -> dict[str, Any]:
        """Get performance statistics.

        Args:
            days: Number of days to analyze

        Returns:
            Performance metrics including average response time, cache hit rate
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Query optimizations
        stmt = (
            select(Article)
            .where(
                Article.unified_optimization_generated == True,  # noqa: E712
                Article.unified_optimization_generated_at >= cutoff_date,
            )
            .order_by(Article.unified_optimization_generated_at.desc())
        )

        result = await self.db.execute(stmt)
        articles = result.scalars().all()

        if not articles:
            return {
                "period_days": days,
                "total_optimizations": 0,
                "cache_hit_rate": 0.0,
            }

        # Calculate cache hit rate (rough estimate based on cost = 0)
        cached_count = sum(1 for a in articles if a.unified_optimization_cost == Decimal("0"))
        cache_hit_rate = cached_count / len(articles) if articles else 0.0

        return {
            "period_days": days,
            "total_optimizations": len(articles),
            "cache_hit_rate": round(cache_hit_rate * 100, 2),
            "recent_optimizations": [
                {
                    "article_id": a.id,
                    "generated_at": a.unified_optimization_generated_at.isoformat() if a.unified_optimization_generated_at else None,
                    "cost_usd": float(a.unified_optimization_cost) if a.unified_optimization_cost else 0.0,
                }
                for a in articles[:10]  # Latest 10
            ],
        }

    async def get_optimization_recommendations(
        self,
        article_id: int,
        metrics: dict[str, Any],
    ) -> list[str]:
        """Generate optimization recommendations based on metrics.

        Args:
            article_id: Article ID
            metrics: Performance metrics

        Returns:
            List of recommendations
        """
        recommendations = []

        duration_ms = metrics.get("duration_ms", 0)
        total_cost = metrics.get("total_cost_usd", 0)
        total_tokens = metrics.get("total_tokens", 0)
        input_tokens = metrics.get("input_tokens", 0)
        output_tokens = metrics.get("output_tokens", 0)

        # Response time recommendations
        if duration_ms > self.SLOW_RESPONSE_THRESHOLD_MS:
            recommendations.append(
                f"⚠️ 响应时间过长 ({duration_ms}ms > {self.SLOW_RESPONSE_THRESHOLD_MS}ms)。"
                f"建议检查网络连接或考虑异步处理。"
            )

        # Cost recommendations
        if total_cost > self.HIGH_COST_THRESHOLD_USD:
            recommendations.append(
                f"💰 单次成本较高 (${total_cost:.4f} > ${self.HIGH_COST_THRESHOLD_USD:.2f})。"
                f"建议优化Prompt长度或降低max_tokens限制。"
            )

        # Token usage recommendations
        if total_tokens > self.HIGH_TOKEN_THRESHOLD:
            recommendations.append(
                f"📊 Token使用量较高 ({total_tokens} > {self.HIGH_TOKEN_THRESHOLD})。"
                f"建议精简文章内容或Prompt模板。"
            )

        # Input/output ratio analysis
        if input_tokens > 0:
            io_ratio = output_tokens / input_tokens
            if io_ratio > 2.0:
                recommendations.append(
                    f"📈 输出Token占比过高 (输出/输入 = {io_ratio:.2f})。"
                    f"可能表示生成内容过于详细，考虑调整temperature或约束输出长度。"
                )

        # Cost efficiency
        if total_cost > 0:
            tokens_per_dollar = total_tokens / total_cost
            if tokens_per_dollar < 40000:  # Less than 40k tokens per dollar is expensive
                recommendations.append(
                    f"⚡ 成本效率偏低 ({tokens_per_dollar:.0f} tokens/$)。"
                    f"建议使用缓存或批量处理降低成本。"
                )

        # Positive feedback
        if not recommendations:
            recommendations.append(
                f"✅ 性能表现良好！成本: ${total_cost:.4f}, "
                f"耗时: {duration_ms}ms, Tokens: {total_tokens}"
            )

        return recommendations

    async def get_top_expensive_articles(
        self,
        days: int = 30,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Get most expensive optimization operations.

        Args:
            days: Number of days to look back
            limit: Max number of results

        Returns:
            List of articles with highest optimization costs
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        stmt = (
            select(Article)
            .where(
                Article.unified_optimization_generated == True,  # noqa: E712
                Article.unified_optimization_generated_at >= cutoff_date,
                Article.unified_optimization_cost > 0,
            )
            .order_by(Article.unified_optimization_cost.desc())
            .limit(limit)
        )

        result = await self.db.execute(stmt)
        articles = result.scalars().all()

        return [
            {
                "article_id": a.id,
                "title": a.title_main or a.title,
                "cost_usd": float(a.unified_optimization_cost),
                "generated_at": a.unified_optimization_generated_at.isoformat() if a.unified_optimization_generated_at else None,
                "body_length": len(a.body_html or a.body or ""),
            }
            for a in articles
        ]

    async def generate_monitoring_report(
        self,
        days: int = 7,
    ) -> dict[str, Any]:
        """Generate comprehensive monitoring report.

        Args:
            days: Number of days to analyze

        Returns:
            Complete monitoring report with all metrics
        """
        cost_stats = await self.get_cost_statistics(days=days)
        perf_stats = await self.get_performance_statistics(days=days)
        expensive_articles = await self.get_top_expensive_articles(days=days, limit=5)

        return {
            "report_generated_at": datetime.utcnow().isoformat(),
            "period_days": days,
            "cost_statistics": cost_stats,
            "performance_statistics": perf_stats,
            "top_expensive_articles": expensive_articles,
            "summary": {
                "total_articles_optimized": cost_stats["article_count"],
                "total_cost_usd": cost_stats["total_cost_usd"],
                "average_cost_per_article": cost_stats["average_cost_usd"],
                "estimated_monthly_cost": cost_stats.get("estimated_monthly_cost_usd", 0.0),
                "cache_hit_rate": perf_stats.get("cache_hit_rate", 0.0),
            },
        }


def calculate_cost(
    input_tokens: int,
    output_tokens: int,
    model: str = "claude-opus-4-5-20251101",
) -> float:
    """Calculate cost for token usage.

    Args:
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        model: Model name (determines pricing)

    Returns:
        Cost in USD
    """
    # Pricing for Claude Opus 4.5 ($5/$25 per million tokens)
    if "opus-4-5" in model or "sonnet-4-5" in model or "claude-3-5-sonnet" in model:
        input_cost = input_tokens / 1_000_000 * OptimizationMonitor.INPUT_COST_PER_MILLION
        output_cost = output_tokens / 1_000_000 * OptimizationMonitor.OUTPUT_COST_PER_MILLION
        return input_cost + output_cost

    # Default fallback pricing
    return (input_tokens / 1_000_000 * 3.0) + (output_tokens / 1_000_000 * 15.0)


def format_cost_report(cost_stats: dict[str, Any]) -> str:
    """Format cost statistics as human-readable report.

    Args:
        cost_stats: Cost statistics from get_cost_statistics()

    Returns:
        Formatted report string
    """
    return f"""
📊 Cost Statistics Report ({cost_stats['period_days']} days)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📈 Article Count: {cost_stats['article_count']}

💰 Cost Metrics:
   • Total Cost:    ${cost_stats['total_cost_usd']:.4f}
   • Average Cost:  ${cost_stats['average_cost_usd']:.4f} per article
   • Min Cost:      ${cost_stats['min_cost_usd']:.4f}
   • Max Cost:      ${cost_stats['max_cost_usd']:.4f}
   • Median Cost:   ${cost_stats.get('median_cost_usd', 0):.4f}

📅 Projection:
   • Est. Monthly Cost: ${cost_stats.get('estimated_monthly_cost_usd', 0):.2f}
   • (Based on {cost_stats['period_days']}-day trend)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""".strip()
