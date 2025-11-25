"""WordPress taxonomy configuration for category classification.

This module contains the candidate list of WordPress categories
that will be used by AI to classify articles into primary categories.

To update the category list:
1. Export categories from WordPress: GET /wp-json/wp/v2/categories
2. Update CATEGORY_CANDIDATES list below
"""

from typing import Final

# Mock category candidates list
# TODO: Replace with actual WordPress categories exported from production site
CATEGORY_CANDIDATES: Final[list[str]] = [
    # News - China
    "中國時局",
    "中國經濟",
    "中國社會",
    "中國人權",

    # News - International
    "國際新聞",
    "美國新聞",
    "歐洲新聞",
    "亞太新聞",

    # News - Regional
    "港台新聞",
    "香港",
    "台灣",

    # Finance & Business
    "財經",
    "股市",
    "房地產",
    "科技財經",

    # Lifestyle
    "生活",
    "健康",
    "美食",
    "旅遊",
    "時尚",

    # Culture
    "文化",
    "傳統文化",
    "藝術",
    "歷史",

    # Entertainment
    "娛樂",
    "影視",
    "音樂",

    # Sports
    "體育",

    # Science & Technology
    "科技",
    "科學",

    # Opinion & Commentary
    "評論",
    "社論",

    # Special Reports
    "專題",
    "深度報導",
]

# Keywords to category mapping for quick matching
# Used as hints before AI classification
KEYWORD_CATEGORY_HINTS: Final[dict[str, str]] = {
    # China politics
    "中共": "中國時局",
    "習近平": "中國時局",
    "共產黨": "中國時局",
    "北京": "中國時局",
    "政治": "中國時局",

    # US News
    "美國": "美國新聞",
    "川普": "美國新聞",
    "拜登": "美國新聞",
    "白宮": "美國新聞",
    "國會": "美國新聞",

    # Finance
    "股市": "股市",
    "股票": "股市",
    "投資": "財經",
    "經濟": "財經",
    "房價": "房地產",
    "房市": "房地產",

    # Health
    "健康": "健康",
    "醫療": "健康",
    "養生": "健康",
    "疾病": "健康",
    "病毒": "健康",
    "疫苗": "健康",

    # Technology
    "科技": "科技",
    "AI": "科技",
    "人工智能": "科技",
    "手機": "科技",

    # Hong Kong / Taiwan
    "香港": "香港",
    "台灣": "台灣",
    "蔡英文": "台灣",
    "賴清德": "台灣",
}


def get_category_candidates() -> list[str]:
    """Get the list of category candidates for AI classification."""
    return CATEGORY_CANDIDATES.copy()


def get_category_hint(title: str, body: str | None = None) -> str | None:
    """Get a category hint based on keyword matching.

    This is used to provide hints to the AI classifier, not as the final decision.

    Args:
        title: Article title
        body: Article body (optional, first 500 chars used)

    Returns:
        Category hint or None if no match found
    """
    text = title
    if body:
        text += " " + body[:500]

    for keyword, category in KEYWORD_CATEGORY_HINTS.items():
        if keyword in text:
            return category

    return None
