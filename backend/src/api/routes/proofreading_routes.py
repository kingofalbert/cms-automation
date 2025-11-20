"""
Proofreading API Routes

獨立的校對API端點，專門處理文章正文的錯字、語法檢查。
只處理解析後的正文，不包括標題、SEO等其他部分。
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.config.database import get_session as get_db
from src.services.proofreading_service import (
    ProofreadingService,
    ProofreadingResult,
    ProofreadingIssue,
    ProofreadingStats
)
from src.models.article import Article
from src.models.worklist import WorklistItem

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/v1",
    tags=["proofreading"],
)


class ProofreadRequest(BaseModel):
    """Request model for proofreading"""
    worklist_id: Optional[int] = Field(None, description="Worklist item ID to proofread")
    article_id: Optional[int] = Field(None, description="Article ID to proofread")
    body_text: Optional[str] = Field(None, description="Manual body text input (純正文)")
    max_issues: int = Field(20, description="Maximum number of issues to return")
    severity_filter: Optional[List[str]] = Field(
        None,
        description="Filter by severity levels: critical, high, medium, low"
    )


class ProofreadResponse(BaseModel):
    """Response model for proofreading"""
    success: bool
    proofreading_issues: List[ProofreadingIssue]
    proofreading_stats: ProofreadingStats
    processed_text_length: int
    error: Optional[str] = None
    source: str = Field(..., description="Source: worklist, article, or manual")


def extract_body_text(article: Article) -> str:
    """
    從文章中提取純正文內容

    優先級：
    1. body (已解析的純文本)
    2. body_html (去除HTML標籤)
    3. 空字符串

    注意：不包括標題、SEO字段等其他內容
    """
    if article.body:
        return article.body

    if article.body_html:
        # 簡單移除HTML標籤
        import re
        text = re.sub(r'<[^>]+>', '', article.body_html)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    return ""


@router.post("/proofread", response_model=ProofreadResponse)
async def proofread_content(
    request: ProofreadRequest,
    db: AsyncSession = Depends(get_db)
) -> ProofreadResponse:
    """
    對文章正文進行校對

    This is an independent API that:
    1. Only processes article body text (純正文)
    2. Does not process titles, SEO keywords, or metadata
    3. Uses focused prompt for better success rate
    4. Has fallback rule-based checking
    5. Updates database if worklist_id is provided

    Priority:
    1. worklist_id (fetches article body from database)
    2. article_id (fetches article body from database)
    3. manual body_text input
    """

    try:
        body_text = None
        source = "manual"
        article_id = None

        # Priority 1: Worklist ID
        if request.worklist_id:
            logger.info(f"Proofreading body text for worklist item {request.worklist_id}")

            worklist_item = await db.get(WorklistItem, request.worklist_id)
            if not worklist_item:
                raise HTTPException(status_code=404, detail=f"Worklist item {request.worklist_id} not found")

            # Get associated article
            if worklist_item.article_id:
                article = await db.get(Article, worklist_item.article_id)
                if article:
                    body_text = extract_body_text(article)
                    article_id = article.id
                    source = "worklist"
                    logger.info(f"Extracted {len(body_text)} chars of body text from article {article.id}")

            if not body_text:
                # Fallback: try to extract from worklist metadata
                if worklist_item.meta and "body" in worklist_item.meta:
                    body_text = worklist_item.meta["body"]
                else:
                    raise HTTPException(
                        status_code=400,
                        detail=f"No body text found for worklist item {request.worklist_id}"
                    )

        # Priority 2: Article ID
        elif request.article_id:
            logger.info(f"Proofreading body text for article {request.article_id}")

            article = await db.get(Article, request.article_id)
            if not article:
                raise HTTPException(status_code=404, detail=f"Article {request.article_id} not found")

            body_text = extract_body_text(article)
            article_id = article.id
            source = "article"
            logger.info(f"Extracted {len(body_text)} chars of body text")

        # Priority 3: Manual input
        elif request.body_text:
            logger.info(f"Proofreading manual body text input ({len(request.body_text)} chars)")
            body_text = request.body_text
            source = "manual"

        else:
            raise HTTPException(
                status_code=400,
                detail="Must provide either worklist_id, article_id, or body_text"
            )

        # Validate body text
        if not body_text or len(body_text.strip()) < 10:
            logger.warning(f"Body text too short: {len(body_text)} chars")
            return ProofreadResponse(
                success=True,
                proofreading_issues=[],
                proofreading_stats=ProofreadingStats(),
                processed_text_length=len(body_text),
                error="Text too short for proofreading",
                source=source
            )

        # Initialize service
        if not settings.ANTHROPIC_API_KEY:
            raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY not configured")

        service = ProofreadingService(api_key=settings.ANTHROPIC_API_KEY)

        # Perform proofreading
        logger.info(f"Starting proofreading for {len(body_text)} characters")
        result: ProofreadingResult = await service.proofread_content(
            body_text=body_text,
            max_issues=request.max_issues,
            severity_filter=request.severity_filter
        )

        # Update database if needed
        if article_id and result.success and result.proofreading_issues:
            logger.info(f"Updating article {article_id} with proofreading results")

            article = await db.get(Article, article_id)
            if article:
                # Store proofreading results in article
                article.proofreading_issues = [
                    issue.model_dump() for issue in result.proofreading_issues
                ]
                await db.commit()
                logger.info(f"Saved {len(result.proofreading_issues)} proofreading issues to article {article_id}")

        return ProofreadResponse(
            success=result.success,
            proofreading_issues=result.proofreading_issues,
            proofreading_stats=result.proofreading_stats,
            processed_text_length=result.processed_text_length,
            error=result.error,
            source=source
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Proofreading failed: {e}", exc_info=True)

        # Return fallback result
        return ProofreadResponse(
            success=False,
            proofreading_issues=[],
            proofreading_stats=ProofreadingStats(),
            processed_text_length=0,
            error=f"Proofreading failed: {str(e)}",
            source=source
        )


@router.post("/worklist/{worklist_id}/proofread", response_model=ProofreadResponse)
async def proofread_worklist_item(
    worklist_id: int,
    db: AsyncSession = Depends(get_db),
    max_issues: int = 20
) -> ProofreadResponse:
    """
    Convenience endpoint: Proofread body text for a specific worklist item

    This is a shortcut for the main proofread endpoint.
    只處理正文，不處理標題或SEO字段。
    """

    return await proofread_content(
        request=ProofreadRequest(
            worklist_id=worklist_id,
            max_issues=max_issues
        ),
        db=db
    )


@router.get("/proofreading/health")
async def health_check():
    """Health check for proofreading service"""

    return {
        "status": "healthy",
        "service": "proofreading",
        "version": "1.0.0",
        "features": [
            "body_text_only",  # 只處理正文
            "worklist_integration",
            "article_integration",
            "manual_input",
            "fallback_checking",
            "severity_filtering"
        ],
        "note": "只校對解析後的正文內容，不包括標題、SEO等其他字段"
    }