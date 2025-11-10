"""Workflow helpers that connect Worklist items to Article + Proofreading pipelines."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_logger, get_settings
from src.models import (
    Article,
    ArticleStatus,
    ArticleStatusHistory,
    WorklistItem,
    WorklistStatus,
)
from src.services.proofreading import (
    ArticlePayload,
    ArticleSection,
    ProofreadingAnalysisService,
    ProofreadingResult,
)

logger = get_logger(__name__)


class WorklistPipelineService:
    """Create articles from Worklist items and trigger automatic proofreading."""

    def __init__(
        self,
        session: AsyncSession,
        *,
        proofreading_service: ProofreadingAnalysisService | None = None,
    ) -> None:
        self.session = session
        self.settings = get_settings()
        self.proofreading_service = proofreading_service or ProofreadingAnalysisService()

    async def process_new_item(self, item: WorklistItem) -> None:
        """Ensure article exists for the worklist item and trigger proofreading."""
        article = await self._ensure_article(item)
        await self._run_proofreading(item, article)

    async def _ensure_article(self, item: WorklistItem) -> Article:
        """Create an article for the worklist item if needed."""
        if item.article_id:
            article = await self.session.get(Article, item.article_id)
            if article:
                return article

        metadata = dict(item.drive_metadata or {})
        metadata.setdefault("worklist_id", item.id)
        metadata.setdefault("google_drive", {})
        metadata["google_drive"]["file_id"] = item.drive_file_id

        article = Article(
            title=item.title,
            body=item.content,
            status=ArticleStatus.IMPORTED,
            author_id=self.settings.GOOGLE_DRIVE_DEFAULT_AUTHOR_ID,
            source="google_drive",
            article_metadata=metadata,
            formatting={},
        )
        self.session.add(article)
        await self.session.flush()

        item.article_id = article.id
        item.mark_status(WorklistStatus.PENDING)
        self.session.add(item)

        await self._record_status_history(
            article=article,
            old_status=None,
            new_status=ArticleStatus.IMPORTED,
            reason="google_drive_imported",
            metadata={"worklist_id": item.id},
        )
        return article

    async def _run_proofreading(self, item: WorklistItem, article: Article) -> None:
        """Invoke AI + deterministic proofreading and persist the results."""
        payload = self._build_payload(article, item)

        try:
            result = await self.proofreading_service.analyze_article(payload)
        except Exception as exc:
            logger.error(
                "worklist_auto_proofreading_failed",
                worklist_id=item.id,
                article_id=article.id,
                error=str(exc),
                exc_info=True,
            )
            item.mark_status(WorklistStatus.FAILED)
            item.add_note(
                {
                    "message": "自动校对失败，等待人工重试",
                    "level": "error",
                    "details": str(exc),
                }
            )
            await self._record_status_history(
                article=article,
                old_status=article.status,
                new_status=ArticleStatus.FAILED,
                reason="auto_proofreading_failed",
                metadata={"error": str(exc)},
            )
            article.status = ArticleStatus.FAILED
            self.session.add_all([article, item])
            return

        self._apply_proofreading_result(article, result)

        item.mark_status(WorklistStatus.PROOFREADING_REVIEW)
        item.add_note(
            {
                "message": "自动校对完成，等待人工审核校对问题",
                "level": "info",
                "metadata": {
                    "issue_count": len(result.issues),
                    "blocking_issues": result.statistics.blocking_issue_count,
                },
            }
        )
        await self._record_status_history(
            article=article,
            old_status=article.status,
            new_status=ArticleStatus.IN_REVIEW,
            reason="auto_proofreading_completed",
            metadata={
                "issues": len(result.issues),
                "blocking": result.statistics.blocking_issue_count,
            },
        )
        article.status = ArticleStatus.IN_REVIEW
        self.session.add_all([article, item])

    def _build_payload(self, article: Article, item: WorklistItem) -> ArticlePayload:
        """Construct the payload sent to the proofreading orchestrator."""
        sections = [
            ArticleSection(kind="body", content=article.body),
        ]

        metadata = dict(article.article_metadata or {})
        metadata.setdefault("worklist_id", item.id)
        metadata.setdefault("drive_metadata", item.drive_metadata or {})

        return ArticlePayload(
            article_id=article.id,
            title=article.title,
            original_content=article.body,
            html_content=metadata.get("html"),
            sections=sections,
            metadata=metadata,
            keywords=item.seo_keywords or [],
            meta_description=item.meta_description,
            seo_keywords=item.seo_keywords or [],
            tags=item.tags or [],
            categories=item.categories or [],
            target_locale=metadata.get("target_locale") or "zh-TW",
        )

    def _apply_proofreading_result(
        self,
        article: Article,
        result: ProofreadingResult,
    ) -> None:
        """Persist proofreading output on the article record."""
        article.proofreading_issues = [
            issue.model_dump(mode="json") for issue in result.issues
        ]
        article.critical_issues_count = result.statistics.blocking_issue_count

        metadata = dict(article.article_metadata or {})
        metadata["proofreading"] = result.model_dump(mode="json")
        article.article_metadata = metadata

    async def _record_status_history(
        self,
        *,
        article: Article,
        old_status: ArticleStatus | str | None,
        new_status: ArticleStatus,
        reason: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Append a row to article_status_history."""
        history = ArticleStatusHistory(
            article_id=article.id,
            old_status=self._status_to_str(old_status),
            new_status=self._status_to_str(new_status),
            changed_by="system",
            change_reason=reason,
            metadata=metadata or {},
            created_at=datetime.utcnow(),
        )
        self.session.add(history)

    @staticmethod
    def _status_to_str(status: ArticleStatus | str | None) -> str | None:
        if status is None:
            return None
        if isinstance(status, ArticleStatus):
            return status.value
        return status
