"""Batch SEO analysis service for imported articles."""


from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_logger
from src.models import Article, ArticleStatus, SEOMetadata
from src.services.seo_analyzer import SEOAnalyzerService

logger = get_logger(__name__)


class SEOBatchAnalyzer:
    """Service for batch SEO analysis of imported articles."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize batch SEO analyzer.

        Args:
            session: Database session
        """
        self.session = session
        self.seo_analyzer = SEOAnalyzerService()

    async def analyze_article_by_id(self, article_id: int) -> SEOMetadata:
        """Analyze a single article and save SEO metadata.

        Args:
            article_id: Article ID to analyze

        Returns:
            SEOMetadata: Created SEO metadata

        Raises:
            ValueError: If article not found or already has SEO
            Exception: If SEO analysis fails
        """
        # Get article
        result = await self.session.execute(
            select(Article).where(Article.id == article_id)
        )
        article = result.scalar_one_or_none()

        if not article:
            raise ValueError(f"Article {article_id} not found")

        # Check if SEO already exists
        existing_seo = await self.session.execute(
            select(SEOMetadata).where(SEOMetadata.article_id == article_id)
        )
        if existing_seo.scalar_one_or_none():
            raise ValueError(f"Article {article_id} already has SEO metadata")

        logger.info(
            "seo_analysis_started",
            article_id=article_id,
            title=article.title[:100],
        )

        try:
            # Analyze article with Claude
            analysis = await self.seo_analyzer.analyze_article(
                title=article.title,
                body=article.body,
                target_keyword=None,  # Auto-detect focus keyword
            )

            # Extract SEO data
            seo_data = analysis.seo_data

            # Create SEO metadata record
            seo_metadata = SEOMetadata(
                article_id=article.id,
                meta_title=seo_data.meta_title,
                meta_description=seo_data.meta_description,
                focus_keyword=seo_data.focus_keyword,
                primary_keywords=seo_data.keywords[:5] if seo_data.keywords else None,
                secondary_keywords=seo_data.keywords[5:15] if len(seo_data.keywords) > 5 else None,
                readability_score=seo_data.readability_score,
                seo_score=seo_data.seo_score,
                # Store additional data in JSONB fields
                open_graph_data={
                    "og_title": seo_data.og_title,
                    "og_description": seo_data.og_description,
                    "og_image": seo_data.og_image,
                } if seo_data.og_title else None,
                schema_markup={
                    "type": seo_data.schema_type,
                } if seo_data.schema_type else None,
            )

            self.session.add(seo_metadata)

            # Update article status to SEO_OPTIMIZED
            article.status = ArticleStatus.SEO_OPTIMIZED

            await self.session.commit()
            await self.session.refresh(seo_metadata)

            logger.info(
                "seo_analysis_completed",
                article_id=article_id,
                seo_id=seo_metadata.id,
                focus_keyword=seo_metadata.focus_keyword,
                seo_score=seo_metadata.seo_score,
            )

            return seo_metadata

        except Exception as e:
            await self.session.rollback()
            logger.error(
                "seo_analysis_failed",
                article_id=article_id,
                error=str(e),
                exc_info=True,
            )
            raise

    async def analyze_imported_articles(
        self,
        limit: int | None = None,
    ) -> tuple[int, int, list[str]]:
        """Analyze all imported articles without SEO metadata.

        Args:
            limit: Optional limit on number of articles to process

        Returns:
            tuple: (successful_count, failed_count, error_messages)
        """
        # Find articles with status IMPORTED that don't have SEO metadata
        query = (
            select(Article)
            .outerjoin(SEOMetadata, Article.id == SEOMetadata.article_id)
            .where(
                Article.status == ArticleStatus.IMPORTED,
                SEOMetadata.id.is_(None),
            )
            .order_by(Article.created_at.desc())
        )

        if limit:
            query = query.limit(limit)

        result = await self.session.execute(query)
        articles = list(result.scalars().all())

        if not articles:
            logger.info("no_articles_for_seo_analysis")
            return 0, 0, []

        logger.info(
            "batch_seo_analysis_started",
            article_count=len(articles),
        )

        successful = 0
        failed = 0
        errors = []

        for article in articles:
            try:
                await self.analyze_article_by_id(article.id)
                successful += 1
            except Exception as e:
                failed += 1
                error_msg = f"Article {article.id} ({article.title[:50]}): {str(e)}"
                errors.append(error_msg)
                logger.warning(
                    "batch_seo_article_failed",
                    article_id=article.id,
                    error=str(e),
                )
                continue

        logger.info(
            "batch_seo_analysis_completed",
            total=len(articles),
            successful=successful,
            failed=failed,
        )

        return successful, failed, errors


async def create_seo_batch_analyzer(session: AsyncSession) -> SEOBatchAnalyzer:
    """Factory function for SEO batch analyzer.

    Args:
        session: Database session

    Returns:
        SEOBatchAnalyzer: Configured service instance
    """
    return SEOBatchAnalyzer(session)
