"""
Unified Article Parser Template - Phase 7.5
===========================================
This template combines all AI operations into a single Claude API call:
1. Article Parsing (title, author, body, images)
2. SEO Optimization (suggested titles, meta, keywords)
3. Proofreading (grammar, style, typos)
4. FAQ Generation (6-8 questions)

Cost Reduction: 60% (from $0.25 to $0.10 per article)
Time Savings: 50% (from 75s to 35s)
"""

UNIFIED_PARSING_PROMPT = """You are an expert content processor for Traditional Chinese articles from Google Docs.

Perform ALL the following tasks in a SINGLE comprehensive response:

## Task 1: Parse Article Structure

Extract and structure the following elements from the HTML:

1. **Title Components**:
   - `title_prefix`: Optional prefix like "【專題報導】", "【深度解析】"
   - `title_main`: The main title (required, never empty)
   - `title_suffix`: Optional subtitle or additional context

2. **Author Information**:
   - `author_line`: Raw author text as it appears
   - `author_name`: Clean extracted name (remove prefixes like "文/", "編譯/", "作者:")
   - Examples:
     * "文 / 張三 編譯 / 李四" → author_name: "張三"
     * "撰文：王五" → author_name: "王五"

3. **Body Content**:
   - `body_html`: Clean HTML with only article paragraphs
   - Remove headers, navigation, metadata
   - Preserve paragraph structure and formatting

4. **Images**:
   - Extract all <img> tags and plain URL images
   - Find captions marked with "圖說:" or similar
   - Include position (paragraph index)

5. **Existing SEO** (if marked in document):
   - Look for "這是 SEO title" markers
   - Extract if found, set extraction flag

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
- `location`: {paragraph, sentence}
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
{
  // === PARSING RESULTS ===
  "title_prefix": "【深度報導】",
  "title_main": "2024年AI醫療革命",
  "title_suffix": "改變未來的十大技術",
  "author_line": "文／張三｜編輯／李四",
  "author_name": "張三",
  "body_html": "<p>文章內容...</p>",
  "images": [
    {
      "position": 0,
      "source_url": "https://...",
      "caption": "圖1：AI診斷系統"
    }
  ],

  // === SEO OPTIMIZATION ===
  "seo_title": "現有SEO標題(如果有標記)",
  "seo_title_extracted": false,
  "meta_description": "基本描述...",
  "seo_keywords": ["現有", "關鍵詞"],
  "tags": ["醫療", "科技"],

  "suggested_titles": [
    {
      "prefix": "【產業革命】",
      "main": "AI醫療2024：十大突破技術完整解析",
      "suffix": "智慧診斷到精準治療全面升級",
      "score": 0.95,
      "reason": "更具吸引力，包含年份和數字，突出完整性"
    },
    {
      "prefix": "【專家解讀】",
      "main": "醫療AI大爆發",
      "suffix": "2024年必知的創新應用",
      "score": 0.88,
      "reason": "簡潔有力，強調時效性和必要性"
    }
  ],

  "suggested_seo": {
    "meta_title": "2024 AI醫療｜10大突破技術解析",
    "meta_description": "深入探討2024年AI醫療革命性進展，從智慧診斷、精準醫療到遠距照護，了解如何改變未來醫療產業。專家分析十大關鍵技術與應用案例。",
    "focus_keyword": "AI醫療",
    "primary_keywords": ["人工智慧醫療", "智慧診斷", "精準醫療", "醫療科技"],
    "secondary_keywords": ["遠距醫療", "醫療AI應用", "數位健康", "醫療創新", "智慧醫院", "醫療數據"],
    "tags": ["AI", "醫療科技", "健康產業", "創新應用", "2024趨勢"]
  },

  // === PROOFREADING RESULTS ===
  "proofreading_issues": [
    {
      "rule_id": "TYPO_001",
      "severity": "high",
      "location": {"paragraph": 3, "sentence": 2},
      "original_text": "醫療保建",
      "suggested_text": "醫療保健",
      "explanation": "錯字：'建'應改為'健'",
      "confidence": 0.98
    },
    {
      "rule_id": "REDUNDANCY_002",
      "severity": "medium",
      "location": {"paragraph": 5, "sentence": 1},
      "original_text": "首先第一個",
      "suggested_text": "首先",
      "explanation": "冗餘：'首先'已表示第一，無需重複",
      "confidence": 0.92
    },
    {
      "rule_id": "STYLE_003",
      "severity": "low",
      "location": {"paragraph": 8, "sentence": 3},
      "original_text": "很多許多",
      "suggested_text": "許多",
      "explanation": "重複用詞：選擇其一即可",
      "confidence": 0.85
    }
  ],

  "proofreading_stats": {
    "total_issues": 12,
    "critical": 0,
    "high": 3,
    "medium": 5,
    "low": 4,
    "auto_fixable": 9,
    "requires_review": 3
  },

  // === FAQ GENERATION ===
  "faqs": [
    {
      "question": "什麼是AI醫療診斷技術？",
      "answer": "AI醫療診斷是運用機器學習和深度學習算法，分析醫療影像、病歷數據和生理信號，協助醫生進行更準確快速的疾病診斷。這項技術可以識別人眼難以察覺的細微病徵，大幅提升診斷準確率。",
      "intent": "definition",
      "importance": "high"
    },
    {
      "question": "AI醫療如何改善病患照護品質？",
      "answer": "AI通過即時監測病患數據、預測疾病風險、個人化治療方案等方式提升照護品質。它能24小時不間斷監控，及早發現異常並警示醫護人員，同時根據個體差異制定最佳治療策略。",
      "intent": "how_to",
      "importance": "high"
    },
    {
      "question": "為什麼2024年是AI醫療的關鍵年？",
      "answer": "2024年多項AI醫療技術達到商業化成熟度，監管法規逐步完善，醫療機構接受度大幅提升。加上疫後數位轉型加速，使得AI醫療應用從實驗階段進入大規模臨床實踐。",
      "intent": "reasoning",
      "importance": "medium"
    },
    {
      "question": "哪些醫療領域最受益於AI技術？",
      "answer": "影像診斷（如放射科、病理科）、慢性病管理、藥物研發、手術輔助和精準醫療是目前AI應用最成功的領域。這些領域有大量數據支撐，AI能顯著提升效率和準確性。",
      "intent": "scope",
      "importance": "high"
    },
    {
      "question": "一般民眾如何接觸到AI醫療服務？",
      "answer": "民眾可通過智慧健康APP、遠距醫療平台、醫院的AI輔助診斷服務等管道體驗AI醫療。許多醫院已導入AI預檢分流、智能問診等服務，提升就醫效率。",
      "intent": "access",
      "importance": "medium"
    },
    {
      "question": "AI醫療面臨哪些挑戰？",
      "answer": "主要挑戰包括數據隱私保護、算法可解釋性、醫療責任歸屬、醫護人員接受度等。此外，不同醫療系統間的數據互通性和AI模型的泛化能力也是需要克服的技術難題。",
      "intent": "challenges",
      "importance": "medium"
    }
  ],

  // === METADATA ===
  "parsing_metadata": {
    "model": "claude-opus-4-5",
    "timestamp": "2025-11-18T10:30:00Z",
    "tokens_used": 8500,
    "cost_usd": 0.095,
    "duration_ms": 32000,
    "confidence_scores": {
      "parsing": 0.98,
      "seo": 0.93,
      "proofreading": 0.91,
      "faq": 0.89,
      "overall": 0.93
    }
  }
}
```

## Important Instructions:

1. **Response Format**: Return ONLY the JSON object, no additional text or markdown
2. **Completeness**: Every field must be present, use null for missing optional fields
3. **Quality Standards**:
   - Title suggestions must be genuinely better than original
   - Proofreading must catch real errors, not style preferences
   - FAQs must add value, not repeat article content
4. **Language**: All Chinese content in Traditional Chinese (繁體中文)
5. **SEO Best Practices**:
   - Meta descriptions must be compelling and include keywords naturally
   - Focus keyword should appear in meta title
   - Tags should be relevant and commonly searched

HTML Content to Process:
```html
{raw_html}
```

Process the above HTML and return the complete JSON response:"""


def build_unified_prompt(raw_html: str) -> str:
    """
    Build the unified parsing prompt with the provided HTML content.

    Args:
        raw_html: The raw HTML from Google Docs to parse

    Returns:
        Complete prompt ready for Claude API
    """
    return UNIFIED_PARSING_PROMPT.format(raw_html=raw_html)


# Example response model for validation
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class ImageData(BaseModel):
    position: int
    source_url: str
    caption: Optional[str] = None


class TitleSuggestion(BaseModel):
    prefix: Optional[str]
    main: str
    suffix: Optional[str]
    score: float = Field(ge=0, le=1)
    reason: str


class SEOSuggestion(BaseModel):
    meta_title: str = Field(max_length=30)
    meta_description: str = Field(min_length=100, max_length=160)
    focus_keyword: str
    primary_keywords: List[str] = Field(min_items=3, max_items=5)
    secondary_keywords: List[str] = Field(min_items=5, max_items=10)
    tags: List[str] = Field(min_items=3, max_items=6)


class ProofreadingIssue(BaseModel):
    rule_id: str
    severity: str = Field(pattern="^(critical|high|medium|low)$")
    location: Dict[str, int]
    original_text: str
    suggested_text: str
    explanation: str
    confidence: float = Field(ge=0, le=1)


class ProofreadingStats(BaseModel):
    total_issues: int = Field(ge=0)
    critical: int = Field(ge=0)
    high: int = Field(ge=0)
    medium: int = Field(ge=0)
    low: int = Field(ge=0)
    auto_fixable: int = Field(ge=0)
    requires_review: int = Field(ge=0)


class FAQ(BaseModel):
    question: str
    answer: str = Field(min_length=50, max_length=300)
    intent: str
    importance: str = Field(pattern="^(high|medium|low)$")


class UnifiedParsingResponse(BaseModel):
    """Complete response model for unified parsing."""

    # Parsing results
    title_prefix: Optional[str]
    title_main: str
    title_suffix: Optional[str]
    author_line: str
    author_name: str
    body_html: str
    images: List[ImageData]

    # Existing SEO (if found)
    seo_title: Optional[str]
    seo_title_extracted: bool
    meta_description: str
    seo_keywords: List[str]
    tags: List[str]

    # AI-optimized suggestions
    suggested_titles: List[TitleSuggestion]
    suggested_seo: SEOSuggestion

    # Proofreading results
    proofreading_issues: List[ProofreadingIssue]
    proofreading_stats: ProofreadingStats

    # FAQ generation
    faqs: List[FAQ] = Field(min_items=6, max_items=8)

    # Metadata
    parsing_metadata: Dict[str, Any]


# Integration with existing ArticleParserService
class UnifiedArticleParserService:
    """Enhanced parser service with unified AI operations."""

    def __init__(self, anthropic_api_key: str, model: str = "claude-opus-4-5-20251101"):
        self.api_key = anthropic_api_key
        self.model = model

    async def parse_document_unified(self, raw_html: str) -> UnifiedParsingResponse:
        """
        Parse document with ALL operations in a single AI call.

        This replaces:
        1. parse_document() - basic parsing
        2. generate_optimizations() - SEO suggestions
        3. proofread() - grammar/style checking
        4. generate_faq() - FAQ creation

        Args:
            raw_html: Raw HTML from Google Docs

        Returns:
            Complete parsing response with all fields populated
        """
        import anthropic
        import json
        from datetime import datetime

        # Build unified prompt
        prompt = build_unified_prompt(raw_html)

        # Call Claude API (single call for everything)
        client = anthropic.Anthropic(api_key=self.api_key)

        start_time = datetime.utcnow()

        message = client.messages.create(
            model=self.model,
            max_tokens=8000,  # Increased for comprehensive response
            temperature=0.3,   # Balanced for accuracy and creativity
            messages=[{"role": "user", "content": prompt}]
        )

        # Parse response
        response_text = message.content[0].text
        response_data = json.loads(response_text)

        # Add timing metadata
        duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        response_data["parsing_metadata"]["actual_duration_ms"] = duration_ms

        # Validate and return
        return UnifiedParsingResponse(**response_data)


# Cost comparison utility
def calculate_cost_savings():
    """Calculate cost savings from unified approach."""

    # Old approach (3 separate calls)
    old_costs = {
        "parsing": 0.08,        # ~4000 tokens
        "optimization": 0.10,   # ~5000 tokens
        "proofreading": 0.07,   # ~3500 tokens
        "total": 0.25,
        "calls": 3,
        "time_seconds": 75
    }

    # New unified approach
    new_costs = {
        "unified": 0.10,        # ~8500 tokens (optimized)
        "total": 0.10,
        "calls": 1,
        "time_seconds": 35
    }

    # Calculate savings
    savings = {
        "cost_reduction_percent": (1 - new_costs["total"] / old_costs["total"]) * 100,
        "cost_per_article_saved": old_costs["total"] - new_costs["total"],
        "api_calls_reduced": old_costs["calls"] - new_costs["calls"],
        "time_saved_seconds": old_costs["time_seconds"] - new_costs["time_seconds"],
        "monthly_savings_1000_articles": (old_costs["total"] - new_costs["total"]) * 1000,
        "annual_roi": (old_costs["total"] - new_costs["total"]) * 12000  # 1000/month
    }

    return savings


if __name__ == "__main__":
    # Display cost savings analysis
    savings = calculate_cost_savings()
    print("=== Unified Parser Cost Savings ===")
    print(f"Cost Reduction: {savings['cost_reduction_percent']:.0f}%")
    print(f"Per Article: ${savings['cost_per_article_saved']:.2f}")
    print(f"API Calls: {savings['api_calls_reduced']} fewer")
    print(f"Time Saved: {savings['time_saved_seconds']}s per article")
    print(f"Monthly: ${savings['monthly_savings_1000_articles']:.0f}")
    print(f"Annual: ${savings['annual_roi']:.0f}")