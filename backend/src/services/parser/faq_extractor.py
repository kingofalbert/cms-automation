"""FAQ Extractor for parsing existing FAQ sections from article HTML.

This module extracts FAQ sections that may already exist in the article content,
marked with various patterns like:
- HTML comments: <!--FAQ-START--> ... <!--FAQ-END-->
- HTML sections: <section class="faq">, <div class="faq-section">
- Markdown headers: ## FAQ, ## 常見問題, ### FAQ
- HTML headers: <h2>常見問題</h2>, <h2>FAQ</h2>

The extractor is flexible and supports multiple formats for Q&A pairs within
the FAQ block.
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Any

from bs4 import BeautifulSoup, Comment, Tag

logger = logging.getLogger(__name__)


@dataclass
class ExtractedFAQ:
    """A single FAQ item extracted from the article."""

    question: str
    answer: str
    position: int = 0  # Order in the FAQ list
    source_format: str = "unknown"  # How it was formatted in the source

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "question": self.question,
            "answer": self.answer,
            "position": self.position,
            "source_format": self.source_format,
        }


@dataclass
class FAQExtractionResult:
    """Result of FAQ extraction from an article."""

    found: bool = False
    faqs: list[ExtractedFAQ] = field(default_factory=list)
    detection_method: str = "none"  # How the FAQ section was detected
    raw_html: str | None = None  # Original HTML of FAQ section (for removal)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "found": self.found,
            "faqs": [faq.to_dict() for faq in self.faqs],
            "detection_method": self.detection_method,
            "faq_count": len(self.faqs),
            "warnings": self.warnings,
        }


class FAQExtractor:
    """Extracts existing FAQ sections from article HTML content.

    Supports multiple detection patterns:
    1. HTML comments: <!--FAQ-START--> ... <!--FAQ-END-->
    2. CSS class markers: <section class="faq">, <div class="faq-section">
    3. ID markers: <div id="faq">, <section id="faq-section">
    4. Header-based: <h2>常見問題</h2>, <h2>FAQ</h2>, ## FAQ

    Within FAQ sections, supports multiple Q&A formats:
    - <dt>/<dd> pairs (definition lists)
    - <div class="faq-item"> with <h3>question</h3> and <p>answer</p>
    - <details>/<summary> (expandable FAQ)
    - Q1: question / A1: answer format
    - Schema.org FAQ markup
    """

    # Patterns for detecting FAQ section headers
    FAQ_HEADER_PATTERNS = [
        r"^常見問題",
        r"^FAQ",
        r"^Frequently Asked Questions",
        r"^問答",
        r"^Q&A",
        r"^問與答",
    ]

    # CSS class patterns for FAQ containers
    FAQ_CLASS_PATTERNS = [
        r"\bfaq\b",
        r"\bfaq-section\b",
        r"\bfaq-list\b",
        r"\bfaqs\b",
        r"\bcommon-questions\b",
    ]

    def __init__(self):
        """Initialize the FAQ extractor."""
        self._header_pattern = re.compile(
            "|".join(self.FAQ_HEADER_PATTERNS),
            re.IGNORECASE
        )
        self._class_pattern = re.compile(
            "|".join(self.FAQ_CLASS_PATTERNS),
            re.IGNORECASE
        )

    def extract(self, html_content: str) -> FAQExtractionResult:
        """Extract FAQ section from HTML content.

        Args:
            html_content: Raw HTML content of the article

        Returns:
            FAQExtractionResult with extracted FAQs or empty result
        """
        if not html_content:
            return FAQExtractionResult()

        # Try different detection methods in order of specificity
        result = self._try_html_comment_markers(html_content)
        if result.found:
            return result

        # Try Google Doc friendly text markers (【FAQ開始】/【FAQ結束】)
        result = self._try_text_markers(html_content)
        if result.found:
            return result

        soup = BeautifulSoup(html_content, "html.parser")

        result = self._try_css_class_markers(soup)
        if result.found:
            return result

        result = self._try_id_markers(soup)
        if result.found:
            return result

        result = self._try_header_based_detection(soup)
        if result.found:
            return result

        result = self._try_schema_org_markup(soup)
        if result.found:
            return result

        # No FAQ section found
        return FAQExtractionResult()

    def _try_html_comment_markers(self, html_content: str) -> FAQExtractionResult:
        """Try to find FAQ section using HTML comment markers.

        Looks for patterns like:
        <!--FAQ-START--> or <!-- FAQ START --> or <!--FAQ-->
        """
        # Flexible pattern for FAQ comment markers
        start_patterns = [
            r"<!--\s*FAQ[-_]?START\s*-->",
            r"<!--\s*FAQ\s+START\s*-->",
            r"<!--\s*BEGIN[-_]?FAQ\s*-->",
            r"<!--\s*FAQ\s*-->",
        ]

        end_patterns = [
            r"<!--\s*FAQ[-_]?END\s*-->",
            r"<!--\s*FAQ\s+END\s*-->",
            r"<!--\s*END[-_]?FAQ\s*-->",
            r"<!--\s*/FAQ\s*-->",
        ]

        for start_pattern in start_patterns:
            start_match = re.search(start_pattern, html_content, re.IGNORECASE)
            if start_match:
                # Found start marker, look for end marker
                remaining = html_content[start_match.end():]

                for end_pattern in end_patterns:
                    end_match = re.search(end_pattern, remaining, re.IGNORECASE)
                    if end_match:
                        # Extract content between markers
                        faq_html = remaining[:end_match.start()]
                        full_match = html_content[start_match.start():start_match.end() + end_match.end()]

                        faqs = self._parse_faq_content(faq_html)

                        if faqs:
                            logger.info(f"Found {len(faqs)} FAQs using HTML comment markers")
                            return FAQExtractionResult(
                                found=True,
                                faqs=faqs,
                                detection_method="html_comment_markers",
                                raw_html=full_match,
                            )

        return FAQExtractionResult()

    def _try_text_markers(self, html_content: str) -> FAQExtractionResult:
        """Try to find FAQ section using Google Doc friendly text markers.

        Supports markers like:
        - 【FAQ開始】...【FAQ結束】
        - 【常見問題開始】...【常見問題結束】
        - [FAQ開始]...[FAQ結束]
        - ===FAQ===...===/FAQ===
        """
        # Get plain text for matching
        soup = BeautifulSoup(html_content, "html.parser")
        plain_text = soup.get_text()

        # Define start/end marker pairs (start_pattern, end_pattern)
        marker_pairs = [
            # 【】brackets - Traditional Chinese style
            (r"【FAQ[開开]始】", r"【FAQ[結结]束】"),
            (r"【常見問題[開开]始】", r"【常見問題[結结]束】"),
            (r"【問答[開开]始】", r"【問答[結结]束】"),
            # [] brackets
            (r"\[FAQ[開开]始\]", r"\[FAQ[結结]束\]"),
            (r"\[常見問題[開开]始\]", r"\[常見問題[結结]束\]"),
            # === style
            (r"={3,}\s*FAQ\s*={3,}", r"={3,}\s*/FAQ\s*={3,}"),
            # --- style
            (r"-{3,}\s*FAQ[開开]始\s*-{3,}", r"-{3,}\s*FAQ[結结]束\s*-{3,}"),
            # Simple markers
            (r"FAQ[開开]始[：:\s]*", r"FAQ[結结]束"),
            (r"常見問題[開开]始[：:\s]*", r"常見問題[結结]束"),
        ]

        for start_pattern, end_pattern in marker_pairs:
            start_match = re.search(start_pattern, plain_text, re.IGNORECASE)
            if start_match:
                remaining_text = plain_text[start_match.end():]
                end_match = re.search(end_pattern, remaining_text, re.IGNORECASE)

                if end_match:
                    # Extract FAQ content between markers
                    faq_text = remaining_text[:end_match.start()].strip()

                    if faq_text:
                        # Parse the FAQ content
                        faqs = self._parse_text_patterns(f"<p>{faq_text}</p>")

                        if faqs:
                            # Calculate the raw text to remove (for body cleanup)
                            full_match_text = plain_text[start_match.start():start_match.end() + end_match.end()]

                            logger.info(f"Found {len(faqs)} FAQs using text markers")
                            return FAQExtractionResult(
                                found=True,
                                faqs=faqs,
                                detection_method="text_markers",
                                raw_html=full_match_text,
                            )

        return FAQExtractionResult()

    def _try_css_class_markers(self, soup: BeautifulSoup) -> FAQExtractionResult:
        """Try to find FAQ section using CSS class markers."""
        # Look for elements with FAQ-related classes
        for element in soup.find_all(["section", "div", "article"]):
            classes = element.get("class", [])
            if isinstance(classes, str):
                classes = [classes]

            class_str = " ".join(classes)
            if self._class_pattern.search(class_str):
                faqs = self._parse_faq_content(str(element))

                if faqs:
                    logger.info(f"Found {len(faqs)} FAQs using CSS class markers")
                    return FAQExtractionResult(
                        found=True,
                        faqs=faqs,
                        detection_method="css_class_markers",
                        raw_html=str(element),
                    )

        return FAQExtractionResult()

    def _try_id_markers(self, soup: BeautifulSoup) -> FAQExtractionResult:
        """Try to find FAQ section using ID markers."""
        id_patterns = ["faq", "faqs", "faq-section", "common-questions", "qa"]

        for id_pattern in id_patterns:
            element = soup.find(id=re.compile(f"^{id_pattern}$", re.IGNORECASE))
            if element:
                faqs = self._parse_faq_content(str(element))

                if faqs:
                    logger.info(f"Found {len(faqs)} FAQs using ID markers")
                    return FAQExtractionResult(
                        found=True,
                        faqs=faqs,
                        detection_method="id_markers",
                        raw_html=str(element),
                    )

        return FAQExtractionResult()

    def _try_header_based_detection(self, soup: BeautifulSoup) -> FAQExtractionResult:
        """Try to find FAQ section based on header text."""
        # Look for h2, h3 headers with FAQ-related text
        for header in soup.find_all(["h2", "h3"]):
            header_text = header.get_text(strip=True)

            if self._header_pattern.search(header_text):
                # Found FAQ header, extract content until next same-level header
                faq_content = []
                current = header.find_next_sibling()

                while current:
                    # Stop at next header of same or higher level
                    if current.name in ["h1", "h2"] or (current.name == "h3" and header.name == "h3"):
                        break
                    faq_content.append(str(current))
                    current = current.find_next_sibling()

                if faq_content:
                    faq_html = "\n".join(faq_content)
                    faqs = self._parse_faq_content(faq_html)

                    if faqs:
                        # Include header in raw_html for removal
                        full_html = str(header) + "\n" + faq_html
                        logger.info(f"Found {len(faqs)} FAQs using header-based detection")
                        return FAQExtractionResult(
                            found=True,
                            faqs=faqs,
                            detection_method="header_based",
                            raw_html=full_html,
                        )

        return FAQExtractionResult()

    def _try_schema_org_markup(self, soup: BeautifulSoup) -> FAQExtractionResult:
        """Try to find FAQ using Schema.org FAQPage markup."""
        # Look for itemtype="https://schema.org/FAQPage"
        faq_page = soup.find(itemtype=re.compile(r"schema\.org/FAQPage", re.IGNORECASE))

        if faq_page:
            faqs = []
            position = 0

            # Find all Question items
            questions = faq_page.find_all(itemtype=re.compile(r"schema\.org/Question", re.IGNORECASE))

            for q_element in questions:
                # Get question text
                q_prop = q_element.find(itemprop="name")
                question_text = q_prop.get_text(strip=True) if q_prop else None

                # Get answer text
                answer_elem = q_element.find(itemtype=re.compile(r"schema\.org/Answer", re.IGNORECASE))
                if answer_elem:
                    a_prop = answer_elem.find(itemprop="text")
                    answer_text = a_prop.get_text(strip=True) if a_prop else None
                else:
                    answer_text = None

                if question_text and answer_text:
                    faqs.append(ExtractedFAQ(
                        question=question_text,
                        answer=answer_text,
                        position=position,
                        source_format="schema_org",
                    ))
                    position += 1

            if faqs:
                logger.info(f"Found {len(faqs)} FAQs using Schema.org markup")
                return FAQExtractionResult(
                    found=True,
                    faqs=faqs,
                    detection_method="schema_org",
                    raw_html=str(faq_page),
                )

        return FAQExtractionResult()

    def _parse_faq_content(self, faq_html: str) -> list[ExtractedFAQ]:
        """Parse FAQ Q&A pairs from HTML content.

        Supports multiple formats:
        1. Definition lists (<dl>/<dt>/<dd>)
        2. Structured divs with classes
        3. Details/summary elements
        4. Q/A text patterns
        5. Numbered Q1/A1 format
        """
        soup = BeautifulSoup(faq_html, "html.parser")
        faqs: list[ExtractedFAQ] = []

        # Try definition list format
        dl_faqs = self._parse_definition_list(soup)
        if dl_faqs:
            return dl_faqs

        # Try structured div format
        div_faqs = self._parse_structured_divs(soup)
        if div_faqs:
            return div_faqs

        # Try details/summary format
        details_faqs = self._parse_details_format(soup)
        if details_faqs:
            return details_faqs

        # Try text-based Q/A patterns
        text_faqs = self._parse_text_patterns(faq_html)
        if text_faqs:
            return text_faqs

        return faqs

    def _parse_definition_list(self, soup: BeautifulSoup) -> list[ExtractedFAQ]:
        """Parse FAQ from <dl>/<dt>/<dd> format."""
        faqs = []

        for dl in soup.find_all("dl"):
            dt_elements = dl.find_all("dt")
            dd_elements = dl.find_all("dd")

            for i, (dt, dd) in enumerate(zip(dt_elements, dd_elements)):
                question = dt.get_text(strip=True)
                answer = dd.get_text(strip=True)

                if question and answer:
                    faqs.append(ExtractedFAQ(
                        question=self._clean_question(question),
                        answer=answer,
                        position=i,
                        source_format="definition_list",
                    ))

        return faqs

    def _parse_structured_divs(self, soup: BeautifulSoup) -> list[ExtractedFAQ]:
        """Parse FAQ from structured div format."""
        faqs = []
        position = 0

        # Look for FAQ item containers
        item_patterns = [
            {"class_": re.compile(r"faq[-_]?item", re.IGNORECASE)},
            {"class_": re.compile(r"qa[-_]?item", re.IGNORECASE)},
            {"class_": re.compile(r"question[-_]?item", re.IGNORECASE)},
        ]

        for pattern in item_patterns:
            items = soup.find_all(["div", "article"], **pattern)

            for item in items:
                # Look for question in h3, h4, or .question class
                question_elem = (
                    item.find(["h3", "h4"]) or
                    item.find(class_=re.compile(r"question", re.IGNORECASE))
                )

                # Look for answer in p or .answer class
                answer_elem = (
                    item.find(class_=re.compile(r"answer", re.IGNORECASE)) or
                    item.find("p")
                )

                if question_elem and answer_elem:
                    question = question_elem.get_text(strip=True)
                    answer = answer_elem.get_text(strip=True)

                    if question and answer:
                        faqs.append(ExtractedFAQ(
                            question=self._clean_question(question),
                            answer=answer,
                            position=position,
                            source_format="structured_div",
                        ))
                        position += 1

            if faqs:
                return faqs

        return faqs

    def _parse_details_format(self, soup: BeautifulSoup) -> list[ExtractedFAQ]:
        """Parse FAQ from <details>/<summary> format."""
        faqs = []

        for i, details in enumerate(soup.find_all("details")):
            summary = details.find("summary")
            if summary:
                question = summary.get_text(strip=True)

                # Answer is the content after summary
                summary.extract()
                answer = details.get_text(strip=True)

                if question and answer:
                    faqs.append(ExtractedFAQ(
                        question=self._clean_question(question),
                        answer=answer,
                        position=i,
                        source_format="details_summary",
                    ))

        return faqs

    def _parse_text_patterns(self, html_content: str) -> list[ExtractedFAQ]:
        """Parse FAQ from text-based Q/A patterns."""
        faqs = []

        # Get plain text
        soup = BeautifulSoup(html_content, "html.parser")
        text = soup.get_text()

        # Pattern 1: Q1: ... A1: ... format
        qa_pattern = re.compile(
            r"Q\s*(\d+)\s*[：:．.]\s*(.+?)\s*A\s*\1\s*[：:．.]\s*(.+?)(?=Q\s*\d+|$)",
            re.DOTALL | re.IGNORECASE
        )

        for match in qa_pattern.finditer(text):
            question = match.group(2).strip()
            answer = match.group(3).strip()

            if question and answer:
                faqs.append(ExtractedFAQ(
                    question=self._clean_question(question),
                    answer=self._clean_answer(answer),
                    position=int(match.group(1)) - 1,
                    source_format="numbered_qa",
                ))

        if faqs:
            return faqs

        # Pattern 2: Q: ... A: ... format (without numbers)
        qa_simple_pattern = re.compile(
            r"[問Q]\s*[：:．.]\s*(.+?)\s*[答A]\s*[：:．.]\s*(.+?)(?=[問Q]\s*[：:．.]|$)",
            re.DOTALL
        )

        position = 0
        for match in qa_simple_pattern.finditer(text):
            question = match.group(1).strip()
            answer = match.group(2).strip()

            if question and answer:
                faqs.append(ExtractedFAQ(
                    question=self._clean_question(question),
                    answer=self._clean_answer(answer),
                    position=position,
                    source_format="simple_qa",
                ))
                position += 1

        return faqs

    def _clean_question(self, question: str) -> str:
        """Clean up question text."""
        # Remove common prefixes
        question = re.sub(r"^(Q\s*\d*\s*[：:．.]\s*|問\s*[：:．.]\s*)", "", question)
        # Ensure ends with question mark
        question = question.strip()
        if question and not question.endswith(("?", "？")):
            question += "？"
        return question

    def _clean_answer(self, answer: str) -> str:
        """Clean up answer text."""
        # Remove common prefixes
        answer = re.sub(r"^(A\s*\d*\s*[：:．.]\s*|答\s*[：:．.]\s*)", "", answer)
        return answer.strip()

    def remove_faq_section(self, html_content: str, raw_faq_html: str) -> str:
        """Remove the extracted FAQ section from the original HTML.

        Args:
            html_content: Original HTML content
            raw_faq_html: The raw HTML/text of the FAQ section to remove

        Returns:
            HTML content with FAQ section removed
        """
        if not raw_faq_html:
            return html_content

        # Try direct replacement first
        if raw_faq_html in html_content:
            return html_content.replace(raw_faq_html, "")

        soup = BeautifulSoup(html_content, "html.parser")

        # For text markers, we need to find and remove paragraphs containing the FAQ content
        # Extract key phrases from the raw_faq_html to identify which paragraphs to remove
        faq_text_clean = raw_faq_html.strip()

        # Find all paragraphs and check if they're part of the FAQ section
        paragraphs_to_remove = []
        faq_started = False

        # Markers that indicate FAQ section boundaries
        start_markers = ["【FAQ開始】", "【FAQ开始】", "[FAQ開始]", "[FAQ开始]",
                        "【常見問題開始】", "FAQ開始", "FAQ开始", "===FAQ==="]
        end_markers = ["【FAQ結束】", "【FAQ结束】", "[FAQ結束]", "[FAQ结束]",
                      "【常見問題結束】", "FAQ結束", "FAQ结束", "===/FAQ==="]

        for element in soup.find_all(["p", "div", "span"]):
            text = element.get_text(strip=True)

            # Check for start marker
            if any(marker in text for marker in start_markers):
                faq_started = True
                paragraphs_to_remove.append(element)
                continue

            # Check for end marker
            if any(marker in text for marker in end_markers):
                paragraphs_to_remove.append(element)
                faq_started = False
                continue

            # If we're inside FAQ section, mark for removal
            if faq_started:
                paragraphs_to_remove.append(element)

        # Remove marked paragraphs
        if paragraphs_to_remove:
            for elem in paragraphs_to_remove:
                elem.decompose()
            logger.info(f"Removed {len(paragraphs_to_remove)} FAQ elements from body content")
            return str(soup)

        # Fallback: Try fuzzy matching for HTML elements
        faq_soup = BeautifulSoup(raw_faq_html, "html.parser")
        faq_element = faq_soup.find()
        if faq_element and faq_element.name:
            for element in soup.find_all(faq_element.name):
                if element.get_text(strip=True) == faq_element.get_text(strip=True):
                    element.decompose()
                    logger.info("Removed FAQ section from body content")
                    return str(soup)

        return html_content

    def format_faqs_as_schema_html(
        self,
        faqs: list[dict[str, Any]],
        section_title: str = "常見問題",
        include_section_wrapper: bool = True,
    ) -> str:
        """Format FAQs as Schema.org Microdata HTML for insertion into article body.

        This creates a visible FAQ section with embedded Schema.org markup,
        which satisfies Google's requirement that structured data must match
        visible content on the page.

        Args:
            faqs: List of FAQ dicts with 'question' and 'answer' keys
            section_title: Title for the FAQ section (default: 常見問題)
            include_section_wrapper: Whether to wrap in <section> tag

        Returns:
            HTML string with Schema.org FAQPage Microdata
        """
        if not faqs:
            return ""

        html_parts = []

        if include_section_wrapper:
            html_parts.append(
                f'<section class="faq-section" itemscope itemtype="https://schema.org/FAQPage">'
            )
            html_parts.append(f'<h2 class="faq-title">{section_title}</h2>')

        for faq in faqs:
            question = faq.get("question", "").strip()
            answer = faq.get("answer", "").strip()

            if not question or not answer:
                continue

            # Each Q&A pair with Schema.org Question/Answer markup
            html_parts.append(
                f'<div class="faq-item" itemscope itemprop="mainEntity" itemtype="https://schema.org/Question">'
            )
            html_parts.append(
                f'<h3 class="faq-question" itemprop="name">{self._escape_html(question)}</h3>'
            )
            html_parts.append(
                f'<div class="faq-answer" itemscope itemprop="acceptedAnswer" itemtype="https://schema.org/Answer">'
            )
            html_parts.append(
                f'<p itemprop="text">{self._escape_html(answer)}</p>'
            )
            html_parts.append('</div>')  # Close answer div
            html_parts.append('</div>')  # Close question div

        if include_section_wrapper:
            html_parts.append('</section>')

        return "\n".join(html_parts)

    def insert_faq_section_into_body(
        self,
        body_html: str,
        faqs: list[dict[str, Any]],
        position: str = "end",
        section_title: str = "常見問題",
    ) -> str:
        """Insert formatted FAQ section into article body HTML.

        Args:
            body_html: Original article body HTML
            faqs: List of FAQ dicts with 'question' and 'answer' keys
            position: Where to insert - "end" (default) or "start"
            section_title: Title for the FAQ section

        Returns:
            Updated body HTML with FAQ section inserted
        """
        if not faqs:
            return body_html

        faq_html = self.format_faqs_as_schema_html(faqs, section_title)

        if not faq_html:
            return body_html

        if position == "start":
            return faq_html + "\n" + body_html
        else:
            return body_html + "\n" + faq_html

    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters."""
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#x27;")
        )


# Singleton instance
_faq_extractor: FAQExtractor | None = None


def get_faq_extractor() -> FAQExtractor:
    """Get the singleton FAQ extractor instance."""
    global _faq_extractor
    if _faq_extractor is None:
        _faq_extractor = FAQExtractor()
    return _faq_extractor
