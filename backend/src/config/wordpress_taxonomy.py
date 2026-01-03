"""WordPress taxonomy configuration for category classification.

This module contains the hierarchical category structure for WordPress:
- PRIMARY_CATEGORIES: Main categories (主分類) that determine URL structure
- CATEGORY_HIERARCHY: Primary -> Secondary category mapping (父子分類結構)
- CATEGORY_CANDIDATES: Flat list of all categories for AI classification

To update the category list:
1. Export categories from WordPress: GET /wp-json/wp/v2/categories
2. Update CATEGORY_HIERARCHY below
"""

from typing import Final

# DJY Health website category hierarchy (繁體中文)
# Updated 2026-01-03: New category structure from DJY Health website menu
CATEGORY_HIERARCHY: Final[dict[str, list[str]]] = {
    # 食療養生 - Food Therapy & Health Preservation
    "食療養生": [
        "血糖調節",
        "安神助眠",
        "補氣補血",
        "美容美顏",
        "清肺潤喉",
        "祛濕排毒",
        "健腎健脾",
        "四季養生",
        "養肝養胃",
    ],

    # 中醫寶典 - Traditional Chinese Medicine
    "中醫寶典": [
        "中醫保健",
        "經絡調理",
        "整合醫學",
        "中醫減肥",
        "中草藥",
    ],

    # 心靈正念 - Mindfulness & Mental Health (no subcategories)
    "心靈正念": [],

    # 健康生活 - Healthy Living
    "健康生活": [
        "居家樂活",
        "運動養生",
        "抗老減重",
        "人生健康站",
        "改善記憶力",
    ],

    # 病症查詢 - Disease Lookup (no subcategories)
    "病症查詢": [],

    # 健康專題 - Health Topics
    "健康專題": [
        "糖尿病教育專區",
    ],

    # 醫師專欄 - Doctor's Column (no subcategories)
    "醫師專欄": [],

    # 更多 - More (contains various content types)
    "更多": [
        "健康新聞",
        "健康圖解",
        "醫療科技",
        "療癒故事",
        "直播",
        "精選內容",
    ],
}

# Primary categories (主分類) - these determine URL structure
PRIMARY_CATEGORIES: Final[list[str]] = list(CATEGORY_HIERARCHY.keys())

# Flat list of all categories (primary + secondary) for AI classification
CATEGORY_CANDIDATES: Final[list[str]] = []
for primary, secondaries in CATEGORY_HIERARCHY.items():
    CATEGORY_CANDIDATES.append(primary)
    CATEGORY_CANDIDATES.extend(secondaries)

# Keywords to category mapping for quick matching
# Used as hints before AI classification
# Updated 2026-01-03: Adjusted for new category structure
KEYWORD_CATEGORY_HINTS: Final[dict[str, str]] = {
    # 食療養生 keywords
    "血糖": "食療養生",
    "助眠": "食療養生",
    "失眠": "食療養生",
    "補血": "食療養生",
    "美容": "食療養生",
    "潤肺": "食療養生",
    "排毒": "食療養生",
    "養肝": "食療養生",
    "養胃": "食療養生",
    "茶": "食療養生",
    "湯": "食療養生",
    "四季養生": "食療養生",

    # 中醫寶典 keywords
    "中醫": "中醫寶典",
    "經絡": "中醫寶典",
    "穴位": "中醫寶典",
    "針灸": "中醫寶典",
    "中藥": "中醫寶典",
    "草藥": "中醫寶典",
    "艾灸": "中醫寶典",
    "推拿": "中醫寶典",
    "拔罐": "中醫寶典",

    # 心靈正念 keywords
    "正念": "心靈正念",
    "冥想": "心靈正念",
    "靜心": "心靈正念",
    "心靈": "心靈正念",
    "心理健康": "心靈正念",

    # 健康生活 keywords
    "運動": "健康生活",
    "減肥": "健康生活",
    "減重": "健康生活",
    "健身": "健康生活",
    "居家": "健康生活",
    "記憶力": "健康生活",

    # 病症查詢 keywords
    "症狀": "病症查詢",
    "病症": "病症查詢",
    "疾病": "病症查詢",

    # 健康專題 keywords
    "糖尿病": "健康專題",

    # 更多 keywords (健康新聞, 醫療科技 now under 更多)
    "疫情": "更多",
    "疫苗": "更多",
    "病毒": "更多",
    "研究": "更多",
    "AI醫療": "更多",
    "醫療科技": "更多",
    "基因": "更多",
    "新藥": "更多",
    "療癒故事": "更多",
}


def get_category_candidates() -> list[str]:
    """Get the flat list of all category candidates for AI classification."""
    return CATEGORY_CANDIDATES.copy()


def get_primary_categories() -> list[str]:
    """Get the list of primary categories (main categories that determine URL)."""
    return PRIMARY_CATEGORIES.copy()


def get_category_hierarchy() -> dict[str, list[str]]:
    """Get the full category hierarchy (primary -> secondary mapping)."""
    return {k: v.copy() for k, v in CATEGORY_HIERARCHY.items()}


def get_secondary_categories(primary: str) -> list[str]:
    """Get secondary categories for a given primary category.

    Args:
        primary: Primary category name

    Returns:
        List of secondary category names, empty list if not found
    """
    return CATEGORY_HIERARCHY.get(primary, []).copy()


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
