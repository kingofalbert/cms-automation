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

from src.config.wordpress_taxonomy import (
    get_category_candidates,
    get_category_hint,
    get_primary_categories,
    get_category_hierarchy,
)
from src.services.parser.models import (
    ImageMetadata,
    ParsedArticle,
    ParsedImage,
    ParsingError,
    ParsingResult,
)

logger = logging.getLogger(__name__)


def _repair_json(text: str) -> str | None:
    """Attempt to repair truncated or malformed JSON.

    Common issues:
    1. Truncated JSON (missing closing braces/brackets)
    2. Unescaped quotes in HTML content
    3. Control characters in strings (newlines inside strings)

    Returns:
        Repaired JSON string or None if repair failed.
    """
    import re

    repaired = text

    # Step 0: Log info about problematic characters around error position
    # Try to parse and get error position
    try:
        import json
        json.loads(repaired)
        return repaired  # Already valid
    except json.JSONDecodeError as e:
        error_pos = e.pos
        context_start = max(0, error_pos - 50)
        context_end = min(len(repaired), error_pos + 50)
        logger.info(f"[JSON REPAIR] Error at position {error_pos}")
        logger.info(f"[JSON REPAIR] Context around error: {repr(repaired[context_start:context_end])}")
        # Show the exact character at error position
        if error_pos < len(repaired):
            logger.info(f"[JSON REPAIR] Char at error: {repr(repaired[error_pos])}, ord={ord(repaired[error_pos])}")

    # Step 1: Fix unescaped control characters inside JSON strings
    # This is the most common issue - Claude outputs literal newlines in body_html
    def escape_control_chars_in_strings(json_text: str) -> str:
        """Escape control characters that appear inside JSON string values."""
        result = []
        in_string = False
        i = 0
        while i < len(json_text):
            char = json_text[i]

            # Track string boundaries (unescaped quotes)
            if char == '"' and (i == 0 or json_text[i-1] != '\\'):
                in_string = not in_string
                result.append(char)
            elif in_string:
                # Inside a string - escape control characters
                if char == '\n':
                    result.append('\\n')
                elif char == '\r':
                    result.append('\\r')
                elif char == '\t':
                    result.append('\\t')
                elif char == '\b':
                    result.append('\\b')
                elif char == '\f':
                    result.append('\\f')
                else:
                    result.append(char)
            else:
                result.append(char)
            i += 1
        return ''.join(result)

    # Apply control character escaping
    repaired = escape_control_chars_in_strings(repaired)
    logger.info("[JSON REPAIR] Applied control character escaping")

    # Step 1.5: Fix unescaped quotes in HTML attributes within JSON strings
    # Claude sometimes outputs: "body_html": "...<ol start="3">..."
    # The quotes around "3" are not escaped and break JSON parsing
    # We need to escape quotes that appear to be HTML attribute values
    import re

    def fix_html_attribute_quotes(json_text: str) -> str:
        """Fix unescaped quotes in HTML attributes within JSON string values.

        Looks for patterns like: <tag attr="value"> and escapes the quotes
        """
        # Pattern to find HTML attributes with unescaped quotes inside JSON strings
        # This is tricky - we need to identify quotes that are part of HTML attributes

        # Simple approach: Find all <tag...> patterns and escape quotes within them
        result = []
        i = 0
        in_json_string = False
        in_html_tag = False

        while i < len(json_text):
            char = json_text[i]

            # Track JSON string boundaries
            if char == '"' and (i == 0 or json_text[i-1] != '\\'):
                if not in_html_tag:
                    in_json_string = not in_json_string
                else:
                    # Inside HTML tag - this quote is an attribute quote, escape it
                    result.append('\\"')
                    i += 1
                    continue

            # Track HTML tag boundaries (only when inside JSON string)
            if in_json_string and char == '<':
                # Check if this starts an HTML tag
                if i + 1 < len(json_text) and (json_text[i+1].isalpha() or json_text[i+1] == '/'):
                    in_html_tag = True
            elif in_html_tag and char == '>':
                in_html_tag = False

            result.append(char)
            i += 1

        return ''.join(result)

    repaired = fix_html_attribute_quotes(repaired)
    logger.info("[JSON REPAIR] Applied HTML attribute quote escaping")

    # Step 2: Handle truncated JSON (missing closing braces/brackets)
    open_braces = repaired.count('{')
    close_braces = repaired.count('}')
    open_brackets = repaired.count('[')
    close_brackets = repaired.count(']')

    if open_braces > close_braces or open_brackets > close_brackets:
        logger.info(f"[JSON REPAIR] Detected truncated JSON: braces {open_braces}/{close_braces}, brackets {open_brackets}/{close_brackets}")

        # Try to find where the truncation happened
        in_string = False
        last_valid_pos = 0
        i = 0
        while i < len(repaired):
            char = repaired[i]
            if char == '"' and (i == 0 or repaired[i-1] != '\\'):
                in_string = not in_string
                if not in_string:
                    j = i + 1
                    while j < len(repaired) and repaired[j] in ' \t\n\r':
                        j += 1
                    if j < len(repaired) and repaired[j] in ',}]':
                        last_valid_pos = j + 1
            i += 1

        if in_string and last_valid_pos > 0:
            logger.info(f"[JSON REPAIR] Truncating at position {last_valid_pos}")
            repaired = repaired[:last_valid_pos]

            open_braces = repaired.count('{')
            close_braces = repaired.count('}')
            open_brackets = repaired.count('[')
            close_brackets = repaired.count(']')

        # Add missing closing brackets and braces
        missing_brackets = ']' * (open_brackets - close_brackets)
        missing_braces = '}' * (open_braces - close_braces)

        repaired = repaired.rstrip()
        if repaired.endswith(','):
            repaired = repaired[:-1]

        repaired = repaired + missing_brackets + missing_braces
        logger.info(f"[JSON REPAIR] Added {len(missing_brackets)} brackets and {len(missing_braces)} braces")

    return repaired


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
        model: str = "claude-opus-4-5-20251101",
        use_unified_prompt: bool = False,
    ):
        """Initialize the article parser service.

        Args:
            use_ai: Whether to use AI-based parsing (default: True)
            anthropic_api_key: Anthropic API key for Claude (required if use_ai=True)
            model: Claude model to use for AI parsing
            use_unified_prompt: Whether to use unified prompt (parsing + SEO + proofreading + FAQ)
        """
        self.use_ai = use_ai
        self.anthropic_api_key = anthropic_api_key
        self.model = model
        self.use_unified_prompt = use_unified_prompt

        logger.info(
            f"ArticleParserService initialized (use_ai={use_ai}, model={model}, unified={use_unified_prompt})"
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

    def _preprocess_html_for_ai(self, raw_html: str, max_chars: int = 500000) -> str:
        """Preprocess HTML to reduce token count for AI parsing.

        This function:
        1. Removes inline styles (which Google Docs exports heavily)
        2. Replaces base64 images with placeholders
        3. Removes unnecessary whitespace
        4. Truncates if still too long

        Args:
            raw_html: Raw HTML from Google Docs
            max_chars: Maximum character count (default 500k ~= 125k tokens)

        Returns:
            Cleaned HTML string safe for AI parsing
        """
        import re

        original_len = len(raw_html)

        # 1. Remove inline styles (style="..." attributes)
        cleaned = re.sub(r'\s*style="[^"]*"', '', raw_html)

        # 2. Replace base64 images with placeholders (preserve src URL images)
        cleaned = re.sub(
            r'<img([^>]*?)src="data:image/[^;]+;base64,[^"]*"([^>]*)>',
            r'<img\1src="[BASE64_IMAGE_REMOVED]"\2>',
            cleaned
        )

        # 3. Remove excessive whitespace and newlines
        cleaned = re.sub(r'\s+', ' ', cleaned)
        cleaned = cleaned.strip()

        # 4. Truncate if still too long
        if len(cleaned) > max_chars:
            logger.warning(
                f"HTML still too long after preprocessing ({len(cleaned)} chars), "
                f"truncating to {max_chars} chars"
            )
            cleaned = cleaned[:max_chars] + "... [CONTENT TRUNCATED]"

        logger.info(
            f"HTML preprocessing: {original_len} -> {len(cleaned)} chars "
            f"({100 - len(cleaned) * 100 // original_len}% reduction)"
        )

        return cleaned

    def _parse_with_ai(self, raw_html: str) -> ParsingResult:
        """Parse document using AI (Claude).

        Args:
            raw_html: Raw HTML content

        Returns:
            ParsingResult with AI-parsed data
        """
        import json

        logger.info("Starting AI-based parsing with Claude")
        logger.info(f"[DEBUG] Parser config: use_ai={self.use_ai}, model={self.model}, api_key_present={bool(self.anthropic_api_key)}, api_key_length={len(self.anthropic_api_key) if self.anthropic_api_key else 0}")

        if not self.anthropic_api_key:
            logger.error("[DEBUG] API key is missing or empty!")
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

            # Preprocess HTML to reduce token count (remove styles, base64 images)
            cleaned_html = self._preprocess_html_for_ai(raw_html)

            # Construct the parsing prompt
            prompt = self._build_ai_parsing_prompt(cleaned_html)

            # Call Claude API
            logger.info(f"[DEBUG] Calling Claude API (model={self.model})")
            message = client.messages.create(
                model=self.model,
                max_tokens=16384,  # Increased for unified parsing with long articles
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
            logger.info(f"[DEBUG] Claude raw response length: {len(response_text)}, starts_with: {response_text[:50] if response_text else 'EMPTY'}")

            # Clean response text - remove markdown code blocks if present
            cleaned_response = response_text.strip()
            if cleaned_response.startswith("```json"):
                logger.info("[DEBUG] Detected ```json markdown wrapper, stripping...")
                # Remove ```json at start and ``` at end
                cleaned_response = cleaned_response[7:]  # Remove ```json
                if cleaned_response.endswith("```"):
                    cleaned_response = cleaned_response[:-3]  # Remove ```
                cleaned_response = cleaned_response.strip()
            elif cleaned_response.startswith("```"):
                logger.info("[DEBUG] Detected ``` markdown wrapper, stripping...")
                # Remove ``` at start and end
                cleaned_response = cleaned_response[3:]
                if cleaned_response.endswith("```"):
                    cleaned_response = cleaned_response[:-3]
                cleaned_response = cleaned_response.strip()

            logger.info(f"[DEBUG] Cleaned response length: {len(cleaned_response)}, starts_with: {cleaned_response[:50]}")

            # Parse Claude's JSON response with repair fallback
            parsed_data = None
            try:
                parsed_data = json.loads(cleaned_response)
            except json.JSONDecodeError as initial_error:
                logger.warning(f"[DEBUG] Initial JSON parse failed: {initial_error}, attempting repair...")
                # Try to repair the JSON
                repaired_json = _repair_json(cleaned_response)
                if repaired_json:
                    try:
                        parsed_data = json.loads(repaired_json)
                        logger.info("[DEBUG] JSON repair successful!")
                    except json.JSONDecodeError as repair_error:
                        logger.error(f"[DEBUG] JSON repair also failed: {repair_error}")
                        raise initial_error  # Re-raise the original error
                else:
                    raise initial_error

            if parsed_data is None:
                raise json.JSONDecodeError("Failed to parse JSON", cleaned_response, 0)
            logger.info(f"[DEBUG] JSON parse SUCCESS! Keys: {list(parsed_data.keys())}")
            logger.info(f"[DEBUG] suggested_titles from Claude: {parsed_data.get('suggested_titles')}")
            # Phase 10/11: Debug logging for category classification
            logger.info(f"[DEBUG] primary_category from Claude: {parsed_data.get('primary_category')}")
            logger.info(f"[DEBUG] secondary_categories from Claude: {parsed_data.get('secondary_categories')}")
            logger.info(f"[DEBUG] suggested_seo from Claude: {parsed_data.get('suggested_seo')}")

            # Extract focus_keyword from suggested_seo if available
            suggested_seo = parsed_data.get("suggested_seo", {})
            focus_keyword = (
                suggested_seo.get("focus_keyword")
                if suggested_seo
                else None
            )

            # Construct ParsedArticle from AI response
            parsed_article = ParsedArticle(
                title_prefix=parsed_data.get("title_prefix"),
                title_main=parsed_data["title_main"],
                title_suffix=parsed_data.get("title_suffix"),
                seo_title=parsed_data.get("seo_title"),
                seo_title_extracted=parsed_data.get("seo_title_extracted", False),
                seo_title_source="extracted" if parsed_data.get("seo_title_extracted") else None,
                author_line=parsed_data.get("author_line"),
                author_name=parsed_data.get("author_name"),
                body_html=parsed_data["body_html"],
                meta_description=parsed_data.get("meta_description"),
                seo_keywords=parsed_data.get("seo_keywords", []),
                tags=parsed_data.get("tags", []),
                # Phase 10: WordPress taxonomy fields
                primary_category=parsed_data.get("primary_category"),
                # Phase 11: Secondary categories for cross-listing
                secondary_categories=parsed_data.get("secondary_categories", []),
                focus_keyword=focus_keyword,
                images=self._parse_images_from_ai_response(parsed_data.get("images", [])),
                # Phase 7.5: Unified AI Parsing fields
                suggested_titles=parsed_data.get("suggested_titles"),
                suggested_meta_description=suggested_seo.get("meta_description") if suggested_seo else None,
                suggested_seo_keywords=suggested_seo.get("primary_keywords", []) if suggested_seo else None,
                proofreading_issues=parsed_data.get("proofreading_issues"),
                proofreading_stats=parsed_data.get("proofreading_stats"),
                faqs=parsed_data.get("faqs"),
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
            logger.error(f"[DEBUG] JSON parse FAILED: {e}")
            logger.error(f"[DEBUG] Failed response text (first 500 chars): {cleaned_response[:500] if 'cleaned_response' in locals() else 'NOT_AVAILABLE'}")
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
            logger.error(f"[DEBUG] Anthropic API error: {e}")
            logger.error(f"[DEBUG] API error type: {type(e).__name__}")
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

    def _format_category_hierarchy(self) -> str:
        """Format the category hierarchy for the AI prompt.

        Returns:
            Formatted string showing primary -> secondary category relationships
        """
        hierarchy = get_category_hierarchy()
        lines = []
        for primary, secondaries in hierarchy.items():
            if secondaries:
                lines.append(f"- {primary}: {', '.join(secondaries)}")
            else:
                lines.append(f"- {primary}: (no subcategories)")
        return "\n".join(lines)

    def _build_ai_parsing_prompt(self, raw_html: str) -> str:
        """Build the prompt for Claude to parse article HTML.

        Args:
            raw_html: Raw HTML content from Google Docs

        Returns:
            Formatted prompt string
        """
        if self.use_unified_prompt:
            return self._build_unified_parsing_prompt(raw_html)

        # Original parsing-only prompt
        return f"""You are an expert at parsing Chinese article HTML from Google Docs into structured data.

Parse the following Google Doc HTML and extract structured information.

**Instructions**:
1. **Title**: Split into prefix (optional, e.g., "【專題】"), main title (required), and suffix (optional subtitle)
2. **SEO Title**: Look for text marked with "這是 SEO title" or similar markers. If found, extract it as seo_title and set seo_title_extracted=true. If not found, leave seo_title=null and seo_title_extracted=false.
3. **Author**: Extract from author patterns like:
   - "文 / 作者名" or "文／作者名" (with or without spaces)
   - "作者：作者名" or "撰文：作者名"
   - "編譯 / 作者名" or "By: Author Name"
   - IMPORTANT: Clean up the name - remove "編譯", "撰文", "作者" suffixes
   - Example: "文 / Leo Babauta 編譯 / 黃襄" → extract "Leo Babauta"
4. **Body**: Remove header metadata, navigation elements, and images. Keep only article paragraphs.
5. **Meta Description**: Create a 150-160 character SEO description summarizing the article.
6. **SEO Keywords**: Extract 5-10 relevant keywords for SEO.
7. **Tags**: Extract 3-6 content tags/categories.
8. **Images**: Extract all images including:
   - <img> tags with src attribute
   - Plain text image URLs (e.g., https://example.com/image.jpg)
   - Google Docs redirect URLs (extract the actual image URL from the redirect)
   - Find nearby "圖說:" markers for captions

**Output Format** (JSON):
```json
{{
  "title_prefix": "【專題報導】",  // Optional
  "title_main": "2024年醫療保健創新趨勢",  // Required
  "title_suffix": "從AI診斷到遠距醫療",  // Optional
  "seo_title": "2024年AI醫療創新趨勢",  // Extracted SEO Title (if marked in doc), null otherwise
  "seo_title_extracted": true,  // true if SEO title was found in doc, false otherwise
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

    def _build_unified_parsing_prompt(self, raw_html: str) -> str:
        """Build unified prompt that combines parsing + SEO + proofreading + FAQ.

        This is the Phase 7.5 unified prompt that reduces costs by 60% and time by 50%.

        Args:
            raw_html: Raw HTML content from Google Docs, or plain text content

        Returns:
            Complete unified prompt string
        """
        # Detect if content is HTML or plain text
        is_html = bool(raw_html and ('<' in raw_html and '>' in raw_html))
        content_type = "HTML" if is_html else "plain text"
        content_label = "HTML Content" if is_html else "Text Content"

        # Adjust instructions for plain text vs HTML
        parsing_note = ""
        if not is_html:
            parsing_note = """
⚠️ Note: The content below is plain text (not HTML).
- Extract title and author from the beginning of the text
- Body content is the main text (no HTML tags to remove)
- Images cannot be extracted from plain text (return empty array)
- Focus on generating high-quality SEO suggestions based on the text content
"""

        return f"""You are an expert content processor for Traditional Chinese articles from Google Docs.
{parsing_note}

Perform ALL the following tasks in a SINGLE comprehensive response:

## Task 1: Parse Article Structure

Extract and structure the following elements from the HTML:

1. **Title Components**:
   - `title_prefix`: Optional prefix like "【專題報導】", "【深度解析】"
   - `title_main`: The main title (required, never empty)
   - `title_suffix`: Optional subtitle or additional context

2. **Author Information**:
   - `author_line`: The COMPLETE raw author text line as it appears (e.g., "文 / Mercura Wang　編譯 / 方海冬")
   - `author_name`: The FULL author attribution including all contributors (原作者 + 編譯者/譯者)
   - IMPORTANT: Keep the full author line intact, don't extract just the first name
   - Examples:
     * "文 / Mercura Wang　編譯 / 方海冬" → author_name: "Mercura Wang、方海冬" or "文 / Mercura Wang　編譯 / 方海冬"
     * "文 / 張三 編譯 / 李四" → author_name: "張三、李四"
     * "撰文：王五" → author_name: "王五"

3. **Body Content**:
   - `body_html`: Clean HTML with only article paragraphs
   - Remove headers, navigation, metadata
   - Preserve paragraph structure and formatting

4. **Images**:
   - Extract all <img> tags and plain URL images
   - Find captions marked with "圖說:" or similar
   - Include position (paragraph index)

5. **Existing SEO** (ONLY extract if explicitly marked in document):
   - **SEO Title**: Look for "這是 SEO title" markers. Extract if found, set seo_title_extracted=true.
   - **Meta Description**: Look for "【Meta摘要】" or "【Meta】" or "Meta摘要：" markers.
     * If found, extract the text IMMEDIATELY following the marker as meta_description
     * Example: "【Meta摘要】\n萊姆病每年影響約47.6萬名美國人..." → meta_description: "萊姆病每年影響約47.6萬名美國人..."
     * This is the author's intended meta description - use EXACTLY as written
     * **IMPORTANT**: If NO meta description marker is found, set meta_description = null (DO NOT generate one here)
   - AI-generated suggestions go in `suggested_seo.meta_description` (Task 2), NOT in `meta_description`

## Task 2: Generate SEO Optimizations

Based on the article content, create:

1. **Optimized Title Suggestions** (2-3 variations):
   - More engaging and clickable
   - Include key search terms
   - Follow 3-part structure (prefix + main + suffix)
   - Provide score (0-1) and reasoning

2. **SEO Metadata**:
   - `suggested_meta_title`: Optimized for search (30 chars)
   - `suggested_meta_description`: Compelling description (150-160 chars)
   - Focus on benefits and key information
   - Include call-to-action if appropriate

3. **Keywords Strategy**:
   - `focus_keyword`: Primary keyword (1)
   - `primary_keywords`: Main keywords (3-5)
   - `secondary_keywords`: Supporting keywords (5-8)
   - `tags`: Content categories (3-6)

## Task 2.5: Article Category Classification (Primary + Secondary)

Based on the article content, classify the article into categories using the **two-tier hierarchical system** used by WordPress with Yoast SEO.

**Primary Categories (主分類)** - Choose ONE from this list:
{', '.join(get_primary_categories())}

**Category Hierarchy (分類層級)** - Each primary category may have secondary categories:
{self._format_category_hierarchy()}

**Classification Rules**:

1. **Primary Category (主分類)** - REQUIRED, SINGLE SELECTION:
   - Select EXACTLY ONE from the Primary Categories list above
   - This determines the URL structure (e.g., example.com/食療養生/article-slug)
   - This determines the breadcrumb navigation
   - Consider the title, first paragraphs, and key entities
   - Return the category name exactly as it appears in the list

2. **Secondary Categories (副分類)** - OPTIONAL, MULTIPLE SELECTION:
   - Select 0-3 categories from EITHER:
     a) Other primary categories (for cross-listing across major sections)
     b) Subcategories under the chosen primary category (for more specific classification)
   - These allow the article to appear in multiple category archive pages
   - Do NOT include the primary_category in secondary_categories (no duplicates)
   - Only select if the article genuinely covers these topics

## Task 3: Comprehensive Proofreading

Identify and categorize all issues:

1. **Critical Issues** (must fix):
   - Factual errors (事實錯誤)
   - Severe grammar mistakes (嚴重語法錯誤)

2. **High Priority** (should fix):
   - Typos and wrong characters (錯別字)
   - Incorrect punctuation (標點符號錯誤)
   - Subject-verb disagreement (主謂不一致)

3. **Medium Priority** (recommended):
   - Redundant expressions (冗餘表達)
   - Inconsistent terminology (術語不一致)
   - Awkward phrasing (表達不順)

4. **Low Priority** (optional):
   - Style improvements (文體優化)
   - Alternative word choices (詞彙選擇)

For each issue provide:
- `rule_id`: Category code (e.g., TYPO_001)
- `severity`: critical/high/medium/low
- `location`: {{paragraph, sentence}}
- `original_text`: The problematic text
- `suggested_text`: Corrected version
- `explanation`: Why this is an issue
- `confidence`: 0.0-1.0 score

## Task 4: Generate FAQ Section

Create 6-8 frequently asked questions that:

1. **Cover Different Intents**:
   - What is...? (definition)
   - How does...? (process)
   - Why is...? (reasoning)
   - When should...? (timing)
   - Who can...? (audience)

2. **Provide Value**:
   - Answer common reader concerns
   - Clarify complex concepts
   - Add practical information
   - Include actionable insights

3. **Structure**:
   - Clear, concise questions
   - Comprehensive 2-3 sentence answers
   - Mark importance (high/medium/low)
   - Tag intent type

## Output Format

Return ONLY valid JSON with this exact structure:

```json
{{
  "title_prefix": "【深度報導】",
  "title_main": "2024年AI醫療革命",
  "title_suffix": "改變未來的十大技術",
  "author_line": "文 / Mercura Wang　編譯 / 方海冬",
  "author_name": "Mercura Wang、方海冬",
  "body_html": "<p>文章內容...</p>",
  "images": [
    {{
      "position": 0,
      "source_url": "https://...",
      "caption": "圖1：AI診斷系統"
    }}
  ],
  "seo_title": null,
  "seo_title_extracted": false,
  "meta_description": null,  // null if no【Meta摘要】marker found; extracted text if marker exists
  "seo_keywords": ["醫療", "AI", "科技"],
  "tags": ["醫療", "科技", "AI"],
  "primary_category": "健康",
  "secondary_categories": ["科技", "生活"],
  "suggested_titles": [
    {{
      "prefix": "【產業革命】",
      "main": "AI醫療2024：十大突破技術完整解析",
      "suffix": "智慧診斷到精準治療全面升級",
      "score": 0.95,
      "reason": "更具吸引力，包含年份和數字，突出完整性"
    }},
    {{
      "prefix": "【專家解讀】",
      "main": "醫療AI大爆發",
      "suffix": "2024年必知的創新應用",
      "score": 0.88,
      "reason": "簡潔有力，強調時效性和必要性"
    }},
    {{
      "prefix": null,
      "main": "從診斷到治療：AI如何改變2024醫療產業",
      "suffix": null,
      "score": 0.82,
      "reason": "直接點出核心價值，適合專業讀者"
    }}
  ],
  "suggested_seo": {{
    "meta_title": "2024 AI醫療｜10大突破技術解析",
    "meta_description": "深入探討2024年AI醫療革命性進展，從智慧診斷、精準醫療到遠距照護，了解如何改變未來醫療產業。",
    "focus_keyword": "AI醫療",
    "primary_keywords": ["人工智慧醫療", "智慧診斷", "精準醫療"],
    "secondary_keywords": ["遠距醫療", "醫療科技", "數位健康"],
    "tags": ["AI", "醫療科技", "健康產業"]
  }},
  "proofreading_issues": [
    {{
      "rule_id": "TYPO_001",
      "severity": "high",
      "location": {{"paragraph": 3, "sentence": 2}},
      "original_text": "醫療保建",
      "suggested_text": "醫療保健",
      "explanation": "錯字：'建'應改為'健'",
      "confidence": 0.98
    }}
  ],
  "proofreading_stats": {{
    "total_issues": 5,
    "critical": 0,
    "high": 2,
    "medium": 2,
    "low": 1,
    "auto_fixable": 4,
    "requires_review": 1
  }},
  "faqs": [
    {{
      "question": "什麼是AI醫療診斷技術？",
      "answer": "AI醫療診斷是運用機器學習和深度學習算法，分析醫療影像、病歷數據和生理信號，協助醫生進行更準確快速的疾病診斷。",
      "intent": "definition",
      "importance": "high"
    }}
  ]
}}
```

{content_label} to Process:
```{content_type.lower()}
{raw_html}
```

Important Instructions:
1. Response Format: Return ONLY the JSON object, no additional text or markdown
2. Completeness: Every field must be present, use null for missing optional fields
3. **REQUIRED: suggested_titles MUST contain 2-3 title variations, NEVER null or empty**
4. All Chinese content in Traditional Chinese (繁體中文)
5. SEO meta descriptions must be compelling and include keywords naturally
6. Proofreading must catch real errors, not style preferences
7. FAQs must add value, not repeat article content
8. **CRITICAL JSON FORMATTING**:
   - Properly escape all special characters in JSON strings
   - Use \\" for double quotes, \\\\ for backslashes
   - Ensure ALL strings are properly terminated with closing quotes
   - Never truncate strings - complete every field fully
   - If text contains line breaks, use \\n escape sequence

Process the above {content_type} and return the complete JSON response:"""

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
            seo_title_data = self._extract_seo_title(soup)
            author_data = self._extract_author(soup)
            body_html = self._extract_body(soup)
            seo_data = self._extract_seo_metadata(soup)
            images = self._extract_images(soup)

            # Construct parsed article
            parsed_article = ParsedArticle(
                title_prefix=title_data.get("prefix"),
                title_main=title_data.get("main") or "Untitled",
                title_suffix=title_data.get("suffix"),
                seo_title=seo_title_data.get("seo_title"),
                seo_title_extracted=seo_title_data.get("extracted", False),
                seo_title_source="extracted" if seo_title_data.get("extracted") else None,
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

    def _extract_seo_title(self, soup: BeautifulSoup) -> dict[str, str | bool | None]:
        """Extract SEO Title from HTML if marked.

        Args:
            soup: BeautifulSoup parsed HTML

        Returns:
            Dict with 'seo_title' and 'extracted' keys
        """
        logger.debug("Extracting SEO Title using heuristics")

        import re

        # Common SEO title markers in Chinese
        seo_title_markers = [
            r"這是\s*SEO\s*title[:：]?\s*(.+)",
            r"SEO\s*title[:：]?\s*(.+)",
            r"SEO\s*標題[:：]?\s*(.+)",
            r"\[SEO\s*title\][:：]?\s*(.+)",
            r"【SEO\s*title】[:：]?\s*(.+)",
        ]

        # Search first 20 paragraphs for SEO title marker
        for p in soup.find_all(["p", "div", "span"], limit=20):
            text = p.get_text(strip=True)

            # Try each pattern
            for pattern in seo_title_markers:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    seo_title = match.group(1).strip()
                    logger.debug(f"Found SEO Title: {seo_title}")
                    return {"seo_title": seo_title, "extracted": True}

        # No SEO title marker found
        logger.debug("No SEO Title marker found")
        return {"seo_title": None, "extracted": False}

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
            r"文[／/\s]+([^｜|\n]+)",  # 文／張三 or 文 / 張三 (with spaces)
            r"作者[：:\s]+([^｜|\n]+)",  # 作者：張三 or 作者: 張三
            r"撰文[：:\s]+([^｜|\n]+)",  # 撰文：張三
            r"By[：:\s]+([^｜|\n]+)",  # By: John Doe
            r"記者[：:\s]+([^｜|\n]+)",  # 記者：張三
            r"編譯[／/\s]+([^｜|\n]+)",  # 編譯／張三
        ]

        # Strategy 1: Search in <p> tags first (HTML structure)
        for p in soup.find_all("p", limit=10):
            text = p.get_text(strip=True)

            # Try each pattern
            for pattern in author_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    raw_line = text
                    author_name = match.group(1).strip()

                    # Clean up author name (remove trailing info after ｜ or | or 編譯)
                    # Split by ｜, |, or 編譯/撰文/作者 markers
                    author_name = re.split(r"[｜|]|編譯|撰文|作者", author_name)[0].strip()

                    logger.debug(f"Found author in <p> tag: {author_name}")
                    return {"raw_line": raw_line, "name": author_name}

        # Strategy 2: If no <p> tags, search in raw text (plain text content)
        full_text = soup.get_text()
        text_lines = full_text.split("\n")

        for line in text_lines[:20]:  # Check first 20 lines
            line = line.strip()
            if not line:
                continue

            # Try each pattern on raw text lines
            for pattern in author_patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    raw_line = line
                    author_name = match.group(1).strip()

                    # Clean up author name
                    author_name = re.split(r"[｜|]|編譯|撰文|作者", author_name)[0].strip()

                    logger.debug(f"Found author in raw text: {author_name}")
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

        # Strategy 1: Find all <img> tags and <figure> elements (HTML structure)
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
                    logger.debug(f"Found image in <figure> at position {paragraph_index}: {source_url}")

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
                    logger.debug(f"Found <img> tag at position {paragraph_index}: {source_url}")

        # Strategy 2: If no images found in HTML tags, search for image URLs in plain text
        if not images:
            import re

            full_text = soup.get_text()

            # Common image URL patterns
            image_url_pattern = r'https?://[^\s]+\.(?:jpg|jpeg|png|gif|webp|svg)(?:\?[^\s\)]*)?'

            # Also look for Google Docs image redirects
            google_docs_image_pattern = r'https://www\.google\.com/url\?q=(https?://[^&]+\.(?:jpg|jpeg|png|gif|webp|svg)[^&]*)'

            # Find all image URLs
            matches = list(re.finditer(image_url_pattern, full_text, re.IGNORECASE))
            google_matches = list(re.finditer(google_docs_image_pattern, full_text, re.IGNORECASE))

            # Process direct image URLs
            for match in matches:
                source_url = match.group(0)
                # Try to find caption nearby (text before "圖說" or similar markers)
                start_pos = max(0, match.start() - 200)
                context = full_text[start_pos:match.start()]

                caption = None
                caption_match = re.search(r'圖說[：:]\s*([^\n]+)', context)
                if caption_match:
                    caption = caption_match.group(1).strip()

                images.append(
                    ParsedImage(
                        position=0,  # Place at beginning since we don't have paragraph context
                        source_url=source_url,
                        caption=caption,
                    )
                )
                logger.debug(f"Found image URL in text: {source_url}")

            # Process Google Docs redirected image URLs
            for match in google_matches:
                import urllib.parse
                source_url = urllib.parse.unquote(match.group(1))

                # Try to find caption
                start_pos = max(0, match.start() - 200)
                context = full_text[start_pos:match.start()]

                caption = None
                caption_match = re.search(r'圖說[：:]\s*([^\n]+)', context)
                if caption_match:
                    caption = caption_match.group(1).strip()

                images.append(
                    ParsedImage(
                        position=0,
                        source_url=source_url,
                        caption=caption,
                    )
                )
                logger.debug(f"Found Google Docs image URL in text: {source_url}")

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
