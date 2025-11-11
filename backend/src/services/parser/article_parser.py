"""Article parser service for Phase 7 structured parsing.

This service extracts structured data from raw Google Doc HTML, including:
- Title decomposition (prefix, main, suffix)
- Author extraction
- Body content sanitization
- SEO metadata extraction
- Image extraction with positions
"""

import logging
from datetime import datetime
from typing import Any

from bs4 import BeautifulSoup, Tag

from src.services.parser.models import (
    ImageMetadata,
    ParsedArticle,
    ParsedImage,
    ParsingError,
    ParsingResult,
)

logger = logging.getLogger(__name__)


class ArticleParserService:
    """Service for parsing Google Doc HTML into structured article data.

    Supports two parsing strategies:
    1. AI-based parsing using Claude (primary, high accuracy)
    2. Heuristic-based parsing using BeautifulSoup (fallback, deterministic)
    """

    def __init__(
        self,
        use_ai: bool = True,
        anthropic_api_key: str | None = None,
        model: str = "claude-3-5-sonnet-20241022",
    ):
        """Initialize the article parser service.

        Args:
            use_ai: Whether to use AI-based parsing (default: True)
            anthropic_api_key: Anthropic API key for Claude (required if use_ai=True)
            model: Claude model to use for AI parsing
        """
        self.use_ai = use_ai
        self.anthropic_api_key = anthropic_api_key
        self.model = model

        logger.info(
            f"ArticleParserService initialized (use_ai={use_ai}, model={model})"
        )

    def parse_document(
        self,
        raw_html: str,
        fallback_to_heuristic: bool = True,
    ) -> ParsingResult:
        """Parse a Google Doc HTML document into structured article data.

        Args:
            raw_html: Raw HTML content from Google Docs
            fallback_to_heuristic: Whether to fall back to heuristic parsing if AI fails

        Returns:
            ParsingResult with parsed article data or errors
        """
        logger.info("Starting article parsing")
        start_time = datetime.utcnow()

        try:
            # Primary: AI-based parsing
            if self.use_ai:
                logger.info("Attempting AI-based parsing")
                result = self._parse_with_ai(raw_html)

                if result.success:
                    logger.info("AI parsing succeeded")
                    result.metadata["parsing_duration_ms"] = (
                        datetime.utcnow() - start_time
                    ).total_seconds() * 1000
                    return result

                logger.warning(
                    f"AI parsing failed: {', '.join([e.error_message for e in result.errors])}"
                )

                if not fallback_to_heuristic:
                    return result

            # Fallback: Heuristic-based parsing
            logger.info("Using heuristic-based parsing")
            result = self._parse_with_heuristics(raw_html)

            result.metadata["parsing_duration_ms"] = (
                datetime.utcnow() - start_time
            ).total_seconds() * 1000

            if result.success:
                logger.info("Heuristic parsing succeeded")
            else:
                logger.error("Heuristic parsing failed")

            return result

        except Exception as e:
            logger.exception(f"Unexpected error during parsing: {e}")
            return ParsingResult(
                success=False,
                errors=[
                    ParsingError(
                        error_type="unexpected_error",
                        error_message=str(e),
                        suggestion="Check input HTML format and parser configuration",
                    )
                ],
                metadata={
                    "parsing_duration_ms": (datetime.utcnow() - start_time).total_seconds()
                    * 1000
                },
            )

    def _parse_with_ai(self, raw_html: str) -> ParsingResult:
        """Parse document using AI (Claude).

        Args:
            raw_html: Raw HTML content

        Returns:
            ParsingResult with AI-parsed data
        """
        import json

        logger.info("Starting AI-based parsing with Claude")

        if not self.anthropic_api_key:
            return ParsingResult(
                success=False,
                errors=[
                    ParsingError(
                        error_type="configuration_error",
                        error_message="Anthropic API key not configured",
                        suggestion="Set anthropic_api_key when creating ArticleParserService",
                    )
                ],
            )

        try:
            import anthropic

            client = anthropic.Anthropic(api_key=self.anthropic_api_key)

            # Construct the parsing prompt
            prompt = self._build_ai_parsing_prompt(raw_html)

            # Call Claude API
            logger.debug(f"Calling Claude API (model={self.model})")
            message = client.messages.create(
                model=self.model,
                max_tokens=4096,
                temperature=0.0,  # Deterministic for parsing
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
            )

            # Extract response text
            response_text = message.content[0].text

            # Parse Claude's JSON response
            parsed_data = json.loads(response_text)

            # Construct ParsedArticle from AI response
            parsed_article = ParsedArticle(
                title_prefix=parsed_data.get("title_prefix"),
                title_main=parsed_data["title_main"],
                title_suffix=parsed_data.get("title_suffix"),
                author_line=parsed_data.get("author_line"),
                author_name=parsed_data.get("author_name"),
                body_html=parsed_data["body_html"],
                meta_description=parsed_data.get("meta_description"),
                seo_keywords=parsed_data.get("seo_keywords", []),
                tags=parsed_data.get("tags", []),
                images=self._parse_images_from_ai_response(parsed_data.get("images", [])),
                parsing_method="ai",
                parsing_confidence=0.95,  # AI has high confidence
            )

            logger.info(
                f"AI parsing succeeded: {parsed_article.title_main}, "
                f"{len(parsed_article.images)} images"
            )

            return ParsingResult(
                success=True,
                parsed_article=parsed_article,
                metadata={
                    "model": self.model,
                    "usage": {
                        "input_tokens": message.usage.input_tokens,
                        "output_tokens": message.usage.output_tokens,
                    },
                },
            )

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            return ParsingResult(
                success=False,
                errors=[
                    ParsingError(
                        error_type="ai_response_parse_error",
                        error_message=f"Claude response was not valid JSON: {str(e)}",
                        suggestion="Check prompt format or retry with different model",
                    )
                ],
            )

        except anthropic.APIError as e:
            logger.error(f"Anthropic API error: {e}")
            return ParsingResult(
                success=False,
                errors=[
                    ParsingError(
                        error_type="api_error",
                        error_message=f"Anthropic API error: {str(e)}",
                        suggestion="Check API key and rate limits",
                    )
                ],
            )

        except Exception as e:
            logger.exception(f"Unexpected error in AI parsing: {e}")
            return ParsingResult(
                success=False,
                errors=[
                    ParsingError(
                        error_type="unexpected_ai_error",
                        error_message=str(e),
                        suggestion="Check logs and retry",
                    )
                ],
            )

    def _build_ai_parsing_prompt(self, raw_html: str) -> str:
        """Build the prompt for Claude to parse article HTML.

        Args:
            raw_html: Raw HTML content from Google Docs

        Returns:
            Formatted prompt string
        """
        return f"""You are an expert at parsing Chinese article HTML from Google Docs into structured data.

Parse the following Google Doc HTML and extract structured information.

**Instructions**:
1. **Title**: Split into prefix (optional, e.g., "【專題】"), main title (required), and suffix (optional subtitle)
2. **Author**: Extract from "文／" or "作者：" patterns. Provide both raw line and cleaned name.
3. **Body**: Remove header metadata, navigation elements, and images. Keep only article paragraphs.
4. **Meta Description**: Create a 150-160 character SEO description summarizing the article.
5. **SEO Keywords**: Extract 5-10 relevant keywords for SEO.
6. **Tags**: Extract 3-6 content tags/categories.
7. **Images**: Extract all images with their position (paragraph index), URL, and caption.

**Output Format** (JSON):
```json
{{
  "title_prefix": "【專題報導】",  // Optional
  "title_main": "2024年醫療保健創新趨勢",  // Required
  "title_suffix": "從AI診斷到遠距醫療",  // Optional
  "author_line": "文／張三｜編輯／李四",  // Raw author line
  "author_name": "張三",  // Cleaned author name
  "body_html": "<p>正文內容...</p>",  // Sanitized HTML
  "meta_description": "本文探討2024年醫療保健領域的創新趨勢...",  // 150-160 chars
  "seo_keywords": ["醫療保健", "AI診斷", "遠距醫療", "創新技術"],
  "tags": ["醫療", "科技", "AI"],
  "images": [
    {{
      "position": 0,  // Paragraph index (0-based)
      "source_url": "https://...",  // 原圖 URL
      "caption": "圖1：AI診斷示意圖"
    }}
  ]
}}
```

**HTML Content**:
```html
{raw_html}
```

**Important**:
- Respond ONLY with valid JSON, no additional text.
- Ensure title_main is never empty.
- body_html should not contain images or header metadata.
- position in images is the paragraph index where the image should appear (0-based).

Parse and respond with JSON:"""

    def _parse_images_from_ai_response(self, images_data: list[dict]) -> list[ParsedImage]:
        """Convert AI response images data to ParsedImage objects.

        Args:
            images_data: List of image dicts from AI response

        Returns:
            List of ParsedImage objects
        """
        parsed_images = []
        for img_data in images_data:
            try:
                parsed_image = ParsedImage(
                    position=img_data.get("position", 0),
                    source_url=img_data.get("source_url"),
                    caption=img_data.get("caption"),
                )
                parsed_images.append(parsed_image)
            except Exception as e:
                logger.warning(f"Failed to parse image from AI response: {e}, data: {img_data}")
                continue

        return parsed_images

    def _parse_with_heuristics(self, raw_html: str) -> ParsingResult:
        """Parse document using heuristic rules (BeautifulSoup).

        Args:
            raw_html: Raw HTML content

        Returns:
            ParsingResult with heuristic-parsed data
        """
        logger.debug("Starting heuristic parsing")

        try:
            soup = BeautifulSoup(raw_html, "html.parser")

            # Extract components
            title_data = self._extract_title(soup)
            author_data = self._extract_author(soup)
            body_html = self._extract_body(soup)
            seo_data = self._extract_seo_metadata(soup)
            images = self._extract_images(soup)

            # Construct parsed article
            parsed_article = ParsedArticle(
                title_prefix=title_data.get("prefix"),
                title_main=title_data.get("main") or "Untitled",
                title_suffix=title_data.get("suffix"),
                author_line=author_data.get("raw_line"),
                author_name=author_data.get("name"),
                body_html=body_html,
                meta_description=seo_data.get("description"),
                seo_keywords=seo_data.get("keywords", []),
                tags=seo_data.get("tags", []),
                images=images,
                parsing_method="heuristic",
                parsing_confidence=0.7,  # Heuristic has lower confidence than AI
            )

            warnings = []
            if not title_data.get("main"):
                warnings.append("Could not extract main title, using 'Untitled'")
            if not author_data.get("name"):
                warnings.append("Could not extract author name")

            return ParsingResult(
                success=True,
                parsed_article=parsed_article,
                warnings=warnings,
            )

        except Exception as e:
            logger.exception(f"Heuristic parsing error: {e}")
            return ParsingResult(
                success=False,
                errors=[
                    ParsingError(
                        error_type="heuristic_parsing_error",
                        error_message=str(e),
                        suggestion="Check HTML structure and parser implementation",
                    )
                ],
            )

    def _extract_title(self, soup: BeautifulSoup) -> dict[str, str | None]:
        """Extract title components from HTML.

        Args:
            soup: BeautifulSoup parsed HTML

        Returns:
            Dict with 'prefix', 'main', 'suffix' keys
        """
        logger.debug("Extracting title using heuristics")

        # Strategy 1: Look for <h1> tags
        h1_tag = soup.find("h1")
        if h1_tag:
            title_text = h1_tag.get_text(strip=True)
        else:
            # Strategy 2: Look for first paragraph with large font or bold
            for p in soup.find_all("p", limit=5):
                text = p.get_text(strip=True)
                if len(text) > 10 and len(text) < 200:
                    title_text = text
                    break
            else:
                return {"prefix": None, "main": None, "suffix": None}

        # Parse title components using patterns
        import re

        # Extract prefix (e.g., "【專題報導】", "《頭條》")
        prefix_match = re.match(r"^([【《\[][\u4e00-\u9fa5]+[】》\]])\s*(.*)", title_text)
        if prefix_match:
            prefix = prefix_match.group(1)
            remaining = prefix_match.group(2)
        else:
            prefix = None
            remaining = title_text

        # Extract suffix (separated by colon, dash, or em dash)
        suffix_match = re.match(r"^(.*?)\s*[：:\-—─]\s*(.+)$", remaining)
        if suffix_match:
            main = suffix_match.group(1).strip()
            suffix = suffix_match.group(2).strip()
        else:
            main = remaining.strip()
            suffix = None

        return {"prefix": prefix, "main": main or title_text, "suffix": suffix}

    def _extract_author(self, soup: BeautifulSoup) -> dict[str, str | None]:
        """Extract author information from HTML.

        Args:
            soup: BeautifulSoup parsed HTML

        Returns:
            Dict with 'raw_line' and 'name' keys
        """
        logger.debug("Extracting author using heuristics")

        import re

        # Common Chinese author patterns
        author_patterns = [
            r"文[／/]([^｜|\n]+)",  # 文／張三
            r"作者[：:]([^｜|\n]+)",  # 作者：張三
            r"撰文[：:]([^｜|\n]+)",  # 撰文：張三
            r"By[：:\s]+([^｜|\n]+)",  # By: John Doe
            r"記者[：:]([^｜|\n]+)",  # 記者：張三
        ]

        # Search first 10 paragraphs for author info
        for p in soup.find_all("p", limit=10):
            text = p.get_text(strip=True)

            # Try each pattern
            for pattern in author_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    raw_line = text
                    author_name = match.group(1).strip()

                    # Clean up author name (remove trailing info after ｜ or |)
                    author_name = re.split(r"[｜|]", author_name)[0].strip()

                    logger.debug(f"Found author: {author_name}")
                    return {"raw_line": raw_line, "name": author_name}

        # No author found
        logger.debug("No author pattern matched")
        return {"raw_line": None, "name": None}

    def _extract_body(self, soup: BeautifulSoup) -> str:
        """Extract and sanitize body content.

        Args:
            soup: BeautifulSoup parsed HTML

        Returns:
            Cleaned body HTML
        """
        logger.debug("Extracting body content using heuristics")

        # Strategy:
        # 1. Remove script, style, nav, header, footer elements
        # 2. Skip metadata paragraphs (author, date, etc.) at the beginning
        # 3. Remove image tags and figure elements
        # 4. Keep only substantial paragraph content

        # Remove unwanted elements
        for tag in soup.find_all(["script", "style", "nav", "header", "footer", "iframe"]):
            tag.decompose()

        # Get all paragraphs
        paragraphs = soup.find_all("p")

        body_paragraphs = []
        metadata_section_ended = False

        for p in paragraphs:
            text = p.get_text(strip=True)

            # Skip empty paragraphs
            if not text or len(text) < 10:
                continue

            # Skip metadata lines at the beginning
            if not metadata_section_ended:
                # Check if this looks like metadata (author, date, etc.)
                if any(
                    pattern in text
                    for pattern in [
                        "文／",
                        "作者：",
                        "撰文：",
                        "記者：",
                        "編輯：",
                        "攝影：",
                        "By:",
                        "Published:",
                        "發布時間",
                    ]
                ):
                    continue

                # Check if this looks like navigation or category
                if len(text) < 50 and ("›" in text or ">" in text or "|" in text):
                    continue

                # If we've found substantial content, metadata section has ended
                if len(text) > 50:
                    metadata_section_ended = True

            # Remove images from this paragraph
            for img in p.find_all("img"):
                img.decompose()

            # Remove figure elements
            for fig in p.find_all("figure"):
                fig.decompose()

            # Get cleaned HTML content
            cleaned_html = p.decode_contents().strip()

            if cleaned_html:
                body_paragraphs.append(f"<p>{cleaned_html}</p>")

        result = "\n".join(body_paragraphs)
        logger.debug(f"Extracted {len(body_paragraphs)} paragraphs, {len(result)} chars")

        return result

    def _extract_seo_metadata(self, soup: BeautifulSoup) -> dict[str, Any]:
        """Extract SEO metadata from HTML.

        Args:
            soup: BeautifulSoup parsed HTML

        Returns:
            Dict with 'description', 'keywords', 'tags' keys
        """
        logger.debug("Extracting SEO metadata using heuristics")

        # Strategy 1: Check for existing meta tags
        description = None
        keywords = []

        # Look for meta description tag
        meta_desc = soup.find("meta", attrs={"name": "description"}) or soup.find(
            "meta", property="og:description"
        )
        if meta_desc and meta_desc.get("content"):
            description = meta_desc["content"]

        # Look for meta keywords tag
        meta_keywords = soup.find("meta", attrs={"name": "keywords"})
        if meta_keywords and meta_keywords.get("content"):
            keywords = [k.strip() for k in meta_keywords["content"].split(",")]

        # Strategy 2: Generate description from content if not found
        if not description:
            # Get first substantial paragraph as description
            for p in soup.find_all("p", limit=20):
                text = p.get_text(strip=True)
                # Skip metadata and short paragraphs
                if len(text) > 100 and not any(
                    pattern in text for pattern in ["文／", "作者：", "By:", "Published:"]
                ):
                    # Truncate to ~150-160 chars for SEO
                    if len(text) > 160:
                        description = text[:157] + "..."
                    else:
                        description = text
                    break

        # Strategy 3: Extract keywords from content if not found
        if not keywords:
            # Simple frequency-based keyword extraction
            all_text = soup.get_text()

            # Common Chinese stopwords to exclude
            stopwords = {
                "的",
                "了",
                "在",
                "是",
                "我",
                "有",
                "和",
                "就",
                "不",
                "人",
                "都",
                "一",
                "個",
                "上",
                "也",
                "很",
                "到",
                "說",
                "要",
                "去",
                "你",
                "會",
                "著",
                "沒有",
                "看",
                "好",
                "自己",
                "這",
            }

            # Extract Chinese words (2+ characters)
            import re

            chinese_words = re.findall(r"[\u4e00-\u9fa5]{2,}", all_text)

            # Count frequency
            from collections import Counter

            word_freq = Counter(chinese_words)

            # Filter out stopwords and get top keywords
            keywords = [
                word
                for word, _ in word_freq.most_common(20)
                if word not in stopwords and len(word) >= 2
            ][:10]  # Top 10 keywords

        # Strategy 4: Extract tags (simplified - use top keywords as tags)
        tags = keywords[:6] if keywords else []

        logger.debug(
            f"Extracted SEO metadata: description={bool(description)}, "
            f"{len(keywords)} keywords, {len(tags)} tags"
        )

        return {"description": description, "keywords": keywords, "tags": tags}

    def _extract_images(self, soup: BeautifulSoup) -> list[ParsedImage]:
        """Extract images with positions.

        Args:
            soup: BeautifulSoup parsed HTML

        Returns:
            List of ParsedImage objects
        """
        logger.debug("Extracting images using heuristics")

        images = []
        paragraph_index = 0

        # Strategy:
        # 1. Find all <img> tags and <figure> elements
        # 2. Calculate position based on paragraph index
        # 3. Extract src URL and caption (from alt, title, or figcaption)

        # Process all top-level elements to track paragraph positions
        for element in soup.find_all(["p", "figure", "img"]):
            if element.name == "p":
                # Track paragraph index for positioning
                text = element.get_text(strip=True)
                if text and len(text) > 10:  # Only count substantial paragraphs
                    paragraph_index += 1

            elif element.name == "figure":
                # Extract image from figure element
                img_tag = element.find("img")
                if img_tag and img_tag.get("src"):
                    source_url = img_tag.get("src")

                    # Try to get caption from figcaption
                    figcaption = element.find("figcaption")
                    caption = (
                        figcaption.get_text(strip=True)
                        if figcaption
                        else img_tag.get("alt") or img_tag.get("title")
                    )

                    images.append(
                        ParsedImage(
                            position=paragraph_index,
                            source_url=source_url,
                            caption=caption,
                        )
                    )
                    logger.debug(f"Found image at position {paragraph_index}: {source_url}")

            elif element.name == "img":
                # Standalone image tag (not in a figure)
                source_url = element.get("src")
                if source_url:
                    caption = element.get("alt") or element.get("title")

                    images.append(
                        ParsedImage(
                            position=paragraph_index,
                            source_url=source_url,
                            caption=caption,
                        )
                    )
                    logger.debug(f"Found image at position {paragraph_index}: {source_url}")

        logger.debug(f"Extracted {len(images)} images total")
        return images

    def validate_parsed_article(self, article: ParsedArticle) -> list[str]:
        """Validate a parsed article for quality issues.

        Args:
            article: Parsed article to validate

        Returns:
            List of validation warning messages
        """
        warnings = []

        # Title validation
        if len(article.title_main) < 10:
            warnings.append("Title is very short (< 10 chars)")
        if len(article.title_main) > 200:
            warnings.append("Title is very long (> 200 chars)")

        # Body validation
        if len(article.body_html) < 100:
            warnings.append("Body content is very short (< 100 chars)")

        # SEO validation
        if article.meta_description and len(article.meta_description) > 160:
            warnings.append("Meta description exceeds recommended 160 chars")

        # Image validation
        if article.image_count > 20:
            warnings.append(f"High number of images ({article.image_count})")

        return warnings
