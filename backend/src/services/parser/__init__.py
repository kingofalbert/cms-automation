"""Article parsing service for Phase 7 structured parsing."""

from src.services.parser.article_parser import ArticleParserService
from src.services.parser.article_processor import (
    ArticleProcessingService,
    create_article_processor,
)
from src.services.parser.image_processor import (
    ImageProcessorService,
    create_image_processor,
)
from src.services.parser.models import (
    ImageMetadata,
    ParsedArticle,
    ParsedImage,
    ParsingError,
    ParsingResult,
)
from src.services.parser.html_utils import (
    strip_html_tags,
    calculate_plain_text_position,
    find_text_position_in_plain,
    validate_position,
    process_issue_positions,
    Position,
)

__all__ = [
    # Services
    "ArticleParserService",
    "ImageProcessorService",
    "ArticleProcessingService",
    "create_image_processor",
    "create_article_processor",
    # Models
    "ParsedArticle",
    "ParsedImage",
    "ImageMetadata",
    "ParsingResult",
    "ParsingError",
    # HTML utilities (Spec 014)
    "strip_html_tags",
    "calculate_plain_text_position",
    "find_text_position_in_plain",
    "validate_position",
    "process_issue_positions",
    "Position",
]
