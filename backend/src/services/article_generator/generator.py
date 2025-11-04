"""Article generator service with retry logic."""


from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_logger
from src.models import Article, ArticleStatus, TopicRequest, TopicRequestStatus
from src.services.article_generator.claude_client import ClaudeClient

logger = get_logger(__name__)


class ArticleGeneratorService:
    """Service for generating articles using Claude AI."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize article generator service.

        Args:
            session: Database session
        """
        self.session = session
        self.claude_client = ClaudeClient()

    async def generate_article(self, topic_request_id: int) -> Article:
        """Generate article from topic request.

        Args:
            topic_request_id: TopicRequest ID

        Returns:
            Article: Generated article

        Raises:
            ValueError: If topic request not found or invalid
            Exception: If generation fails
        """
        # Get topic request
        result = await self.session.execute(
            select(TopicRequest).where(TopicRequest.id == topic_request_id)
        )
        topic_request = result.scalar_one_or_none()

        if not topic_request:
            raise ValueError(f"TopicRequest {topic_request_id} not found")

        if topic_request.status != TopicRequestStatus.PENDING:
            raise ValueError(
                f"TopicRequest {topic_request_id} is not pending (status: {topic_request.status})"
            )

        try:
            # Mark as processing
            topic_request.status = TopicRequestStatus.PROCESSING
            await self.session.commit()

            logger.info(
                "article_generation_started",
                topic_request_id=topic_request_id,
                topic=topic_request.title[:100],
            )

            # Generate article using Claude
            result = await self.claude_client.generate_article(
                topic=topic_request.title,
                style_tone=topic_request.style_tone,
                target_word_count=topic_request.target_word_count,
                outline=topic_request.outline,
            )

            # Check cost limit
            cost = result["metadata"]["cost_usd"]
            max_cost = 0.50  # From settings
            if cost > max_cost:
                logger.warning(
                    "article_generation_cost_exceeded",
                    cost=cost,
                    max_cost=max_cost,
                    topic_request_id=topic_request_id,
                )

            # Create article
            article = Article(
                title=result["title"],
                body=result["body"],
                status=ArticleStatus.DRAFT,
                author_id=topic_request.submitted_by,
                article_metadata=result["metadata"],
                formatting={},
            )

            self.session.add(article)
            await self.session.flush()

            # Update topic request
            topic_request.article_id = article.id
            topic_request.status = TopicRequestStatus.COMPLETED

            await self.session.commit()
            await self.session.refresh(article)

            logger.info(
                "article_generation_completed",
                topic_request_id=topic_request_id,
                article_id=article.id,
                word_count=article.word_count,
                cost=cost,
            )

            return article

        except Exception as e:
            # Mark as failed
            topic_request.status = TopicRequestStatus.FAILED
            topic_request.error_message = str(e)
            await self.session.commit()

            logger.error(
                "article_generation_failed",
                topic_request_id=topic_request_id,
                error=str(e),
                exc_info=True,
            )

            raise


async def create_article_generator(session: AsyncSession) -> ArticleGeneratorService:
    """Factory function for article generator service.

    Args:
        session: Database session

    Returns:
        ArticleGeneratorService: Configured service instance
    """
    return ArticleGeneratorService(session)
