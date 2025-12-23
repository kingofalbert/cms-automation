"""Unified AI optimization service for Phase 7.

This service generates all AI optimization suggestions (title + SEO + FAQ)
in a single API call to save 40-60% cost and 30-40% time.

Cost comparison:
- Original (2 calls): ~$0.10-0.13 per article, 30-40s
- Unified (1 call): ~$0.06-0.08 per article, 20-30s
- Savings: 40-60% cost, 30-40% time
"""

import json
import logging
import re
from datetime import datetime
from decimal import Decimal
from typing import Any

from anthropic import AsyncAnthropic
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.article import Article
from src.models.article_faq import ArticleFAQ
from src.models.seo_suggestions import SEOSuggestion
from src.models.title_suggestions import TitleSuggestion

logger = logging.getLogger(__name__)


class UnifiedOptimizationService:
    """统一AI优化服务.

    一次性生成：
    1. 标题优化建议（3段式，2-3个选项）
    2. SEO关键词（focus/primary/secondary）
    3. Meta Description优化
    4. Tags推荐
    5. FAQ生成（8-10个）

    优势：节省Token成本40-60%，减少API调用次数
    """

    def __init__(self, anthropic_client: AsyncAnthropic, db_session: AsyncSession):
        """Initialize service.

        Args:
            anthropic_client: Async Anthropic API client
            db_session: Async database session
        """
        self.client = anthropic_client
        self.db = db_session
        self.model = "claude-opus-4-5-20251101"
        self.max_tokens = 6000  # Increased for comprehensive response
        self.temperature = 0.35  # Balanced creativity

    async def generate_all_optimizations(
        self,
        article: Article,
        regenerate: bool = False,
    ) -> dict[str, Any]:
        """一次性生成所有优化建议.

        Args:
            article: Article object with parsed content
            regenerate: Force regeneration even if suggestions exist

        Returns:
            {
                "title_suggestions": {...},
                "seo_suggestions": {...},
                "faqs": [...],
                "generation_metadata": {
                    "total_cost_usd": 0.07,
                    "total_tokens": 6500,
                    "duration_ms": 25000,
                    "savings_vs_separate": {...}
                }
            }

        Raises:
            ValueError: If article not parsed or prompt building fails
            RuntimeError: If AI API call fails
        """
        logger.info(f"Generating unified optimizations for article {article.id}")

        # Validation
        if not article.body_html and not article.body:
            raise ValueError(f"Article {article.id} has no content to optimize")

        # Check if already generated (unless regenerate=True)
        if not regenerate and article.unified_optimization_generated:
            logger.info(f"Article {article.id} already has optimizations, loading from cache")
            return await self._load_existing_optimizations(article.id)

        # Build unified prompt
        start_time = datetime.now()
        prompt = self._build_unified_prompt(article)

        # Call Claude API
        try:
            logger.info(f"Calling Claude API for article {article.id}")
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[{"role": "user", "content": prompt}],
            )

            # Track usage
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            total_tokens = input_tokens + output_tokens

            # Calculate cost (Claude Sonnet 4.5 pricing: $3/M input, $15/M output)
            cost_usd = (input_tokens / 1_000_000 * 3.0) + (output_tokens / 1_000_000 * 15.0)

            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)

            logger.info(
                f"Article {article.id} - Claude response received: "
                f"{total_tokens} tokens, ${cost_usd:.4f}, {duration_ms}ms"
            )

        except Exception as e:
            logger.error(f"Claude API call failed for article {article.id}: {e}")
            raise RuntimeError(f"Failed to generate optimizations: {e}")

        # Parse response
        try:
            result = self._parse_unified_response(response.content[0].text)
        except Exception as e:
            logger.error(f"Failed to parse Claude response for article {article.id}: {e}")
            raise ValueError(f"AI response parsing failed: {e}")

        # Store to database
        try:
            await self._store_optimizations(article.id, result)
        except Exception as e:
            logger.error(f"Failed to store optimizations for article {article.id}: {e}")
            raise RuntimeError(f"Database storage failed: {e}")

        # Update article metadata
        article.unified_optimization_generated = True
        article.unified_optimization_generated_at = datetime.now()
        article.unified_optimization_cost = Decimal(str(cost_usd))
        await self.db.commit()

        # Build response with metadata
        faq_assessment = result.get("faq_assessment", {})
        faq_applicable = faq_assessment.get("is_applicable", True)

        return {
            "title_suggestions": result.get("title_suggestions", {}),
            "seo_suggestions": {
                "seo_keywords": result.get("seo_keywords", {}),
                "meta_description": result.get("meta_description", {}),
                "tags": result.get("tags", {}),
            },
            "faqs": result.get("faqs", []),
            # FAQ v2.2 assessment fields
            "faq_assessment": faq_assessment,
            "faq_applicable": faq_applicable,
            "faq_editorial_notes": result.get("faq_editorial_notes", {}),
            "faq_html": article.faq_html,
            "generation_metadata": {
                "total_cost_usd": round(cost_usd, 4),
                "total_tokens": total_tokens,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "duration_ms": duration_ms,
                "savings_vs_separate": self._calculate_savings(cost_usd, total_tokens, duration_ms),
            },
        }

    def _build_unified_prompt(self, article: Article) -> str:
        """构建统一优化Prompt.

        包含5个子任务：
        1. 标题优化
        2. SEO关键词
        3. Meta Description
        4. Tags推荐
        5. FAQ生成
        """
        # Build full title from components
        full_title = self._build_full_title(article)

        # Get content for analysis (prioritize body_html)
        content = article.body_html or article.body or ""
        content_preview = content[:800] if len(content) > 800 else content

        # Build comprehensive prompt
        prompt = f"""你是一位资深的SEO专家、内容营销顾问和文案优化师。请为以下文章提供**全面的优化建议**。

## 📋 文章信息

### 结构化数据（已解析）

**标题组件**:
- 前缀: {article.title_prefix or "（无）"}
- 主标题: {article.title_main or article.title}
- 副标题: {article.title_suffix or "（无）"}
- 完整标题: {full_title}

**作者**:
- 作者行: {article.author_line or "（无）"}
- 作者名: {article.author_name or "（无）"}

**初步SEO数据**（从文档提取）:
- Meta Description: {article.meta_description or "（无）"}
- 关键词: {", ".join(article.seo_keywords[:10]) if article.seo_keywords else "（无）"}
- 标签: {", ".join(article.tags[:5]) if article.tags else "（无）"}

**正文内容**（前800字符）:
{content_preview}...

---

## 🎯 优化任务

请一次性完成以下**5个优化任务**：

---

### 任务1: 标题优化（3段式）📝

为三段式标题结构生成**2-3个**优化建议：

```
完整标题 = [前缀] | 主标题 | [副标题]
```

**要求**:
1. 生成2-3个不同风格的标题方案
2. 必须包含至少1个**Data-Driven型**（包含具体数据、百分比）
3. 推荐包含1个**Authority-Backed型**（权威背书）或**How-To型**（操作指南）
4. 可选1个**Comprehensive Guide型**（全面指南）或**Question-Based型**（疑问引导）

**长度规范**:
- 前缀: 2-6字符（简短有力）
- 主标题: 15-30字符（核心内容）
- 副标题: 4-12字符（补充信息）
- 完整标题: 25-50字符（推荐），不超过70字符

**输出格式**:
```json
"title_suggestions": {{
  "suggested_title_sets": [
    {{
      "id": "option_1",
      "title_prefix": "深度解析",
      "title_main": "人工智能革新医疗诊断：准确率提升30%",
      "title_suffix": "权威指南",
      "full_title": "深度解析 | 人工智能革新医疗诊断：准确率提升30% | 权威指南",
      "score": 95,
      "strengths": ["包含具体数据（30%）增强可信度", "使用动作词"革新"增强吸引力"],
      "type": "data_driven",
      "recommendation": "最佳选项，平衡数据与吸引力",
      "character_count": {{"prefix": 4, "main": 22, "suffix": 4, "total": 34}}
    }},
    {{
      "id": "option_2",
      "title_prefix": "实用指南",
      "title_main": "如何运用AI技术提升医疗诊断效率",
      "title_suffix": "专家解读",
      "full_title": "实用指南 | 如何运用AI技术提升医疗诊断效率 | 专家解读",
      "score": 88,
      "strengths": ["操作性强，提供实用价值", "专家背书增强权威性"],
      "type": "how_to",
      "recommendation": "适合寻求实用建议的读者",
      "character_count": {{"prefix": 4, "main": 18, "suffix": 4, "total": 30}}
    }}
  ],
  "optimization_notes": ["建议在标题中突出具体数据以增强可信度", "保持标题简洁，避免超过50字符"],
  "seo_title_suggestions": {{
    "variants": [
      {{
        "id": "seo_variant_1",
        "seo_title": "2024年AI醫療創新趨勢",
        "reasoning": "聚焦核心關鍵字「AI醫療」和「創新」，30字內，包含時效性",
        "keywords_focus": ["AI醫療", "創新", "2024"],
        "character_count": 12
      }},
      {{
        "id": "seo_variant_2",
        "seo_title": "AI醫療診斷技術全面解析",
        "reasoning": "突出「診斷技術」和「全面解析」，吸引深度閱讀者",
        "keywords_focus": ["AI醫療", "診斷技術", "解析"],
        "character_count": 12
      }}
    ],
    "original_seo_title": null,
    "notes": [
      "SEO Title 建議保持在 30 字以內",
      "包含核心關鍵字以提升搜尋排名",
      "與 H1 標題主題一致但更精簡"
    ]
  }}
}}
```

**注意**: `seo_title_suggestions` 是新增欄位，用於生成 SEO Title（`<title>` 標籤）建議，與 H1 標題分開。

**SEO Title vs H1 的區別**:
- **H1 標題**: 頁面內容的主標題，較長（25-50字），給用戶閱讀
- **SEO Title**: 搜尋引擎結果顯示的標題，較短（30字左右），給搜尋引擎看

**SEO Title 要求**:
1. 生成 2-3 個精簡變體
2. 長度: **30字左右**（最多40字）
3. 必須包含主關鍵詞
4. 可加入年份、數據等提升點擊率
5. 與 H1 主題一致但更精簡

---

### 任务2: SEO关键词分析🔑

深度分析文章内容，生成三级关键词体系：

**要求**:
1. **Focus Keyword**（主关键词）: 1个，搜索量高、竞争适中、与内容高度相关
2. **Primary Keywords**（主要关键词）: 3-5个，语义相关
3. **Secondary Keywords**（次要关键词）: 5-10个，长尾词

**输出格式**:
```json
"seo_keywords": {{
  "focus_keyword": "人工智能医疗应用",
  "focus_keyword_rationale": "该词搜索量高、竞争中等，与文章核心内容匹配",
  "primary_keywords": ["AI诊断", "医疗影像分析", "智能辅助诊断", "深度学习医疗", "医疗AI技术"],
  "secondary_keywords": ["AI早期筛查", "医疗大数据分析", "智能病理诊断", "远程AI诊疗", "精准医疗AI", "医学影像AI识别", "临床决策支持系统", "AI辅助手术", "智能健康管理", "医疗机器学习"],
  "keyword_difficulty": {{"focus_keyword": 0.65, "average_difficulty": 0.52}},
  "search_volume_estimate": {{"focus_keyword": "5000-10000/月", "primary_keywords_total": "15000-25000/月"}}
}}
```

---

### 任务3: Meta Description优化📄

基于文章内容生成吸引点击的Meta Description：

**要求**:
1. 长度: 150-160字符
2. 包含Focus Keyword
3. 具有吸引点击的元素（数据、行动号召、独特价值）
4. 如果原文已有Meta Description，进行优化改进

**输出格式**:
```json
"meta_description": {{
  "original_meta_description": "本文介绍AI在医疗领域的应用。",
  "suggested_meta_description": "深入解析AI如何革新医疗诊断：从影像分析到早期筛查，了解人工智能如何提升诊断准确率30%以上，助力精准医疗发展。",
  "meta_description_improvements": [
    "添加具体数据（30%）增强可信度",
    "使用动作词"革新"、"提升"增强吸引力",
    "包含主关键词"AI医疗诊断"",
    "符合150-160字符最佳长度"
  ],
  "meta_description_score": 92
}}
```

---

### 任务4: Tags推荐🏷️

分析内容后推荐相关标签：

**要求**:
1. 推荐6-8个标签
2. 包含高频标签（流量入口）+ 中频标签（精准定位）+ 长尾标签（细分流量）
3. 标签与文章内容高度相关
4. 优先推荐可能已存在的常见标签

**输出格式**:
```json
"tags": {{
  "suggested_tags": [
    {{"tag": "人工智能", "relevance": 0.95, "type": "primary"}},
    {{"tag": "医疗AI", "relevance": 0.92, "type": "primary"}},
    {{"tag": "深度学习医疗应用", "relevance": 0.78, "type": "secondary"}},
    {{"tag": "AI诊断工具", "relevance": 0.85, "type": "trending"}},
    {{"tag": "医学影像分析", "relevance": 0.82, "type": "primary"}},
    {{"tag": "智能医疗", "relevance": 0.88, "type": "primary"}},
    {{"tag": "医疗创新技术", "relevance": 0.75, "type": "secondary"}},
    {{"tag": "精准医疗", "relevance": 0.80, "type": "secondary"}}
  ],
  "recommended_tag_count": "建议使用6-8个标签",
  "tag_strategy": "3个高频标签 + 3个中频标签 + 2个长尾标签"
}}
```

---

### 任務5: FAQ生成（健康文章專業版 v2.2）❓

你是一名深耕健康領域多年的專業編輯、SEO專家及資訊架構師，精通Google最新AI搜索（AI Overviews）的抓取邏輯與E-E-A-T評核標準。

#### 5.1 適配性評估（系統前置判斷）

首先分析文章內容，判斷是否適合增加FAQ區塊：

**適合增加FAQ的文章類型**:
- 健康養生、中醫保健、營養食療
- 疾病預防、症狀說明、治療方法
- 運動健身、穴位按摩、生活保健

**不適合增加FAQ的文章類型**:
- 突發新聞、時事報導
- 短篇快訊（<500字）
- 純圖片/影片內容
- 廣告推廣類文章

**輸出格式（適配性評估）**:
```json
"faq_assessment": {{
  "is_applicable": true,
  "reason": "本文為健康養生類深度內容，適合增加FAQ以解答讀者常見疑問",
  "target_pain_points": ["消除用藥恐懼", "明確適用人群", "了解注意事項"]
}}
```

若 `is_applicable` 為 `false`，則 `faqs` 陣列為空。

#### 5.2 FAQ深度撰寫（若適用）

設計**3-5個**問題，遵循以下要求：

**搜索意圖匹配**:
- 模擬讀者在搜尋框中會輸入的自然語言提問
- 例如：不是「禁忌症」，而是「哪些人不能吃？」
- 例如：不是「服用方法」，而是「什麼時候吃最有效？」

**答案自洽性（Self-contained）**:
- 每個答案必須獨立完整
- 嚴禁使用「如前所述」、「見上文」或「參考正文」等代詞
- 確保當該問答被AI搜尋單獨引用時，邏輯依然閉環

**結構化表述**:
1. **首句定論**: 第一句話必須直接回答核心問題
2. **補充細節**: 第二、三句話提供證據支持、適用範圍或操作建議
3. **字數黃金律**: 每個回答總字數控制在**40-60字**之間（最佳AI摘要抓取率）

**信任邊界與醫學安全（YMYL合規）**:
- 答案為資訊分享，不可替代專業醫療診斷
- 針對「孕婦、慢性病患者、正在服藥者」等特殊人群，必須給出明確安全警示
- 避免絕對化用語（「一定」、「100%」），多使用「有助於」、「建議諮詢」、「通常情況下」

**輸出格式**:
```json
"faqs": [
  {{
    "question": "哪些人不適合服用這類保健品？",
    "answer": "孕婦、哺乳期婦女及正在服用抗凝血藥物者不建議使用。慢性病患者如糖尿病、高血壓患者服用前應先諮詢醫師，確認是否與現有藥物產生交互作用。",
    "question_type": "factual",
    "search_intent": "informational",
    "keywords_covered": ["禁忌人群", "孕婦", "藥物交互"],
    "confidence": 0.92,
    "safety_warning": true
  }},
  {{
    "question": "什麼時候吃效果最好？",
    "answer": "一般建議飯後30分鐘服用，有助於吸收且減少腸胃不適。若為脂溶性成分，搭配含油脂的餐點效果更佳。具體用量請參照產品說明。",
    "question_type": "how_to",
    "search_intent": "informational",
    "keywords_covered": ["服用時間", "吸收", "飯後"],
    "confidence": 0.88,
    "safety_warning": false
  }},
  {{
    "question": "這個方法真的有效嗎？有科學依據嗎？",
    "answer": "多項研究顯示其活性成分具有抗氧化作用，但效果因人而異。建議持續使用2-4週觀察，如無改善應諮詢專業醫師評估其他方案。",
    "question_type": "factual",
    "search_intent": "informational",
    "keywords_covered": ["科學依據", "研究", "效果"],
    "confidence": 0.85,
    "safety_warning": false
  }}
],
"faq_editorial_notes": {{
  "longtail_keywords_covered": ["保健品禁忌", "服用時間", "效果多久"],
  "multimedia_suggestions": ["穴位圖示", "食譜成品照", "運動姿勢示範"],
  "tone_adjustment_needed": false,
  "disclaimer_required": true
}}
```

---

## 📤 最終輸出格式

請嚴格按照以下JSON Schema輸出所有5個任務的結果：

```json
{{
  "title_suggestions": {{
    "suggested_title_sets": [...],
    "optimization_notes": [...],
    "seo_title_suggestions": {{...}}
  }},
  "seo_keywords": {{
    "focus_keyword": "...",
    "primary_keywords": [...],
    "secondary_keywords": [...],
    ...
  }},
  "meta_description": {{
    "suggested_meta_description": "...",
    "meta_description_improvements": [...],
    ...
  }},
  "tags": {{
    "suggested_tags": [...],
    ...
  }},
  "faq_assessment": {{
    "is_applicable": true/false,
    "reason": "說明為何適合/不適合增加FAQ",
    "target_pain_points": ["痛點1", "痛點2"]
  }},
  "faqs": [
    {{"question": "...", "answer": "...", "safety_warning": true/false, ...}},
    // ... 3-5個FAQ（若適用）
  ],
  "faq_editorial_notes": {{
    "longtail_keywords_covered": [...],
    "multimedia_suggestions": [...],
    "tone_adjustment_needed": false,
    "disclaimer_required": true
  }}
}}
```

---

## ⚠️ 重要注意事項

1. **內容一致性**: 標題、關鍵詞、Meta、Tags、FAQ應相互協調，使用統一的核心概念
2. **關鍵詞覆蓋**: 確保Focus Keyword在標題、Meta Description、FAQ中都有出現
3. **數據準確**: FAQ答案必須基於文章內容，不得杜撰數據
4. **長度控制**: 嚴格遵守各項長度限制（FAQ答案40-60字）
5. **YMYL合規**: 健康類FAQ必須包含適當的安全警示和免責聲明
6. **適配性判斷**: 若文章不適合FAQ，設置 `faq_assessment.is_applicable = false`

---

現在請完成所有5個優化任務。"""

        return prompt

    def _build_full_title(self, article: Article) -> str:
        """构建完整标题."""
        parts = []
        if article.title_prefix:
            parts.append(article.title_prefix)

        # Use title_main if available, otherwise fall back to title
        main_title = article.title_main or article.title
        parts.append(main_title)

        if article.title_suffix:
            parts.append(article.title_suffix)

        return " | ".join(parts)

    def _parse_unified_response(self, response_text: str) -> dict[str, Any]:
        """解析AI响应.

        提取：
        - title_suggestions
        - seo_keywords
        - meta_description
        - tags
        - faqs
        """
        # Try to extract JSON from response
        # Pattern 1: Look for JSON code block
        json_match = re.search(r"```json\s*(\{.*?\})\s*```", response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Pattern 2: Try to find raw JSON object
            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                raise ValueError("No JSON found in AI response")

        try:
            data = json.loads(json_str)
            logger.info("Successfully parsed AI response JSON")
            return data
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response JSON: {e}")
            logger.debug(f"Response text (first 500 chars): {response_text[:500]}")
            raise ValueError(f"AI response JSON parsing failed: {e}")

    async def _store_optimizations(self, article_id: int, result: dict[str, Any]) -> None:
        """分別存儲優化結果到對應的表.

        Args:
            article_id: Article ID
            result: AI生成的完整結果
        """
        logger.info(f"Storing optimizations for article {article_id}")

        # Get article to access original title components
        from sqlalchemy import select

        stmt = select(Article).where(Article.id == article_id)
        db_result = await self.db.execute(stmt)
        article = db_result.scalar_one()

        # 1. 存儲標題建議到 title_suggestions 表
        title_data = result.get("title_suggestions", {})
        await self._save_title_suggestions(article_id, article, title_data)

        # 2. 存儲SEO建議到 seo_suggestions 表
        seo_keywords = result.get("seo_keywords", {})
        meta_desc = result.get("meta_description", {})
        tags_data = result.get("tags", {})

        await self._save_seo_suggestions(article_id, seo_keywords, meta_desc, tags_data)

        # 3. 處理FAQ適配性評估 (v2.2)
        faq_assessment = result.get("faq_assessment", {})
        faq_applicable = faq_assessment.get("is_applicable", True)
        faq_editorial_notes = result.get("faq_editorial_notes", {})

        # 存儲FAQ評估到 article
        article.faq_applicable = faq_applicable
        article.faq_assessment = faq_assessment
        article.faq_editorial_notes = faq_editorial_notes

        # 4. 存儲FAQ到 article_faqs 表 (僅當適用時)
        faqs = result.get("faqs", [])
        if faq_applicable and faqs:
            await self._save_faqs(article_id, faqs)
            # 生成FAQ HTML區塊
            faq_html = self._generate_faq_html(faqs, faq_editorial_notes)
            article.faq_html = faq_html
            logger.info(f"Generated FAQ HTML for article {article_id}")
        else:
            logger.info(f"FAQ not applicable for article {article_id}: {faq_assessment.get('reason', 'N/A')}")

        await self.db.commit()
        logger.info(f"Successfully stored all optimizations for article {article_id}")

    async def _save_title_suggestions(
        self, article_id: int, article: Article, data: dict
    ) -> None:
        """存储标题建议（包含 H1 和 SEO Title）."""
        # Check if already exists
        from sqlalchemy import select

        stmt = select(TitleSuggestion).where(TitleSuggestion.article_id == article_id)
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()

        # Prepare SEO title suggestions data
        seo_title_suggestions = data.get("seo_title_suggestions", {})

        # Update original_seo_title in suggestions if article has extracted seo_title
        if article.seo_title and article.seo_title_extracted:
            if "original_seo_title" not in seo_title_suggestions or not seo_title_suggestions["original_seo_title"]:
                seo_title_suggestions["original_seo_title"] = article.seo_title

        if existing:
            # Update existing
            existing.suggested_title_sets = data.get("suggested_title_sets", [])
            existing.optimization_notes = data.get("optimization_notes", [])
            existing.suggested_seo_titles = seo_title_suggestions if seo_title_suggestions else None
            existing.generated_at = datetime.now()
        else:
            # Create new
            title_suggestion = TitleSuggestion(
                article_id=article_id,
                original_title_prefix=article.title_prefix,
                original_title_main=article.title_main or article.title,
                original_title_suffix=article.title_suffix,
                suggested_title_sets=data.get("suggested_title_sets", []),
                optimization_notes=data.get("optimization_notes", []),
                suggested_seo_titles=seo_title_suggestions if seo_title_suggestions else None,
            )
            self.db.add(title_suggestion)

        logger.info(f"Saved title suggestions (H1 + SEO) for article {article_id}")

    async def _save_seo_suggestions(
        self,
        article_id: int,
        seo_keywords: dict,
        meta_desc: dict,
        tags_data: dict,
    ) -> None:
        """存储SEO建议."""
        from sqlalchemy import select

        stmt = select(SEOSuggestion).where(SEOSuggestion.article_id == article_id)
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            # Update existing
            existing.focus_keyword = seo_keywords.get("focus_keyword")
            existing.focus_keyword_rationale = seo_keywords.get("focus_keyword_rationale")
            existing.primary_keywords = seo_keywords.get("primary_keywords", [])
            existing.secondary_keywords = seo_keywords.get("secondary_keywords", [])
            existing.keyword_difficulty = seo_keywords.get("keyword_difficulty")
            existing.search_volume_estimate = seo_keywords.get("search_volume_estimate")
            existing.suggested_meta_description = meta_desc.get("suggested_meta_description")
            existing.meta_description_improvements = meta_desc.get(
                "meta_description_improvements", []
            )
            existing.meta_description_score = meta_desc.get("meta_description_score")
            existing.suggested_tags = tags_data.get("suggested_tags", [])
            existing.tag_strategy = tags_data.get("tag_strategy")
            existing.generated_at = datetime.now()
        else:
            # Create new
            seo_suggestion = SEOSuggestion(
                article_id=article_id,
                focus_keyword=seo_keywords.get("focus_keyword"),
                focus_keyword_rationale=seo_keywords.get("focus_keyword_rationale"),
                primary_keywords=seo_keywords.get("primary_keywords", []),
                secondary_keywords=seo_keywords.get("secondary_keywords", []),
                keyword_difficulty=seo_keywords.get("keyword_difficulty"),
                search_volume_estimate=seo_keywords.get("search_volume_estimate"),
                suggested_meta_description=meta_desc.get("suggested_meta_description"),
                meta_description_improvements=meta_desc.get("meta_description_improvements", []),
                meta_description_score=meta_desc.get("meta_description_score"),
                suggested_tags=tags_data.get("suggested_tags", []),
                tag_strategy=tags_data.get("tag_strategy"),
            )
            self.db.add(seo_suggestion)

        logger.info(f"Saved SEO suggestions for article {article_id}")

    async def _save_faqs(self, article_id: int, faqs: list[dict]) -> None:
        """存儲FAQ (v2.2)."""
        from sqlalchemy import delete

        # Delete existing FAQs for this article
        stmt = delete(ArticleFAQ).where(ArticleFAQ.article_id == article_id)
        await self.db.execute(stmt)

        # Create new FAQs
        for position, faq_data in enumerate(faqs):
            # Use string values directly (matching varchar columns in database)
            question_type = faq_data.get("question_type", "factual")
            if question_type not in ("factual", "how_to", "comparison", "definition"):
                question_type = "factual"

            search_intent = faq_data.get("search_intent", "informational")
            if search_intent not in ("informational", "navigational", "transactional"):
                search_intent = "informational"

            faq = ArticleFAQ(
                article_id=article_id,
                question=faq_data.get("question", ""),
                answer=faq_data.get("answer", ""),
                question_type=question_type,
                search_intent=search_intent,
                keywords_covered=faq_data.get("keywords_covered", []),
                confidence=faq_data.get("confidence"),
                safety_warning=faq_data.get("safety_warning", False),  # v2.2 YMYL
                position=position,
                status="draft",  # String value instead of enum
            )
            self.db.add(faq)

        logger.info(f"Saved {len(faqs)} FAQs for article {article_id}")

    def _generate_faq_html(self, faqs: list[dict], editorial_notes: dict) -> str:
        """生成FAQ HTML區塊 (常見問題).

        生成可見的FAQ區塊，放置在文章正文底部。
        包含：
        1. 標題「常見問題」
        2. 問答列表
        3. 免責聲明（如果需要）

        Args:
            faqs: FAQ數據列表
            editorial_notes: 編輯備註（包含disclaimer_required）

        Returns:
            HTML字符串
        """
        if not faqs:
            return ""

        # 開始構建HTML
        html_parts = [
            '<section class="faq-section" id="faq">',
            '  <h2>常見問題</h2>',
            '  <div class="faq-list">',
        ]

        for i, faq in enumerate(faqs, 1):
            question = faq.get("question", "")
            answer = faq.get("answer", "")
            has_warning = faq.get("safety_warning", False)

            html_parts.append(f'    <div class="faq-item" data-index="{i}">')
            html_parts.append(f'      <h3 class="faq-question">Q{i}: {question}</h3>')

            if has_warning:
                html_parts.append(f'      <div class="faq-answer faq-warning">')
                html_parts.append(f'        <span class="warning-icon">⚠️</span>')
                html_parts.append(f'        <p>{answer}</p>')
                html_parts.append(f'      </div>')
            else:
                html_parts.append(f'      <div class="faq-answer">')
                html_parts.append(f'        <p>{answer}</p>')
                html_parts.append(f'      </div>')

            html_parts.append('    </div>')

        html_parts.append('  </div>')

        # 添加免責聲明（健康類文章）
        if editorial_notes.get("disclaimer_required", False):
            html_parts.append('  <div class="faq-disclaimer">')
            html_parts.append('    <p><em>免責聲明：本文提供的健康資訊僅供參考，不能替代專業醫療診斷或建議。')
            html_parts.append('    如有任何健康問題，請諮詢合格的醫療專業人員。</em></p>')
            html_parts.append('  </div>')

        html_parts.append('</section>')

        return '\n'.join(html_parts)

    async def _load_existing_optimizations(self, article_id: int) -> dict[str, Any]:
        """Load existing optimizations from database."""
        from sqlalchemy import select

        # Load article for FAQ assessment fields
        stmt = select(Article).where(Article.id == article_id)
        result = await self.db.execute(stmt)
        article = result.scalar_one_or_none()

        # Load title suggestions
        stmt = select(TitleSuggestion).where(TitleSuggestion.article_id == article_id)
        result = await self.db.execute(stmt)
        title_suggestion = result.scalar_one_or_none()

        # Load SEO suggestions
        stmt = select(SEOSuggestion).where(SEOSuggestion.article_id == article_id)
        result = await self.db.execute(stmt)
        seo_suggestion = result.scalar_one_or_none()

        # Load FAQs
        stmt = select(ArticleFAQ).where(ArticleFAQ.article_id == article_id).order_by(ArticleFAQ.position)
        result = await self.db.execute(stmt)
        faqs = result.scalars().all()

        return {
            "title_suggestions": {
                "suggested_title_sets": title_suggestion.suggested_title_sets if title_suggestion else [],
                "optimization_notes": title_suggestion.optimization_notes if title_suggestion else [],
                "seo_title_suggestions": title_suggestion.suggested_seo_titles if title_suggestion else {},
            },
            "seo_suggestions": {
                "seo_keywords": {
                    "focus_keyword": seo_suggestion.focus_keyword if seo_suggestion else None,
                    "focus_keyword_rationale": seo_suggestion.focus_keyword_rationale if seo_suggestion else None,
                    "primary_keywords": seo_suggestion.primary_keywords if seo_suggestion else [],
                    "secondary_keywords": seo_suggestion.secondary_keywords if seo_suggestion else [],
                },
                "meta_description": {
                    "suggested_meta_description": seo_suggestion.suggested_meta_description if seo_suggestion else None,
                    "meta_description_improvements": seo_suggestion.meta_description_improvements if seo_suggestion else [],
                    "meta_description_score": seo_suggestion.meta_description_score if seo_suggestion else None,
                },
                "tags": {
                    "suggested_tags": seo_suggestion.suggested_tags if seo_suggestion else [],
                    "tag_strategy": seo_suggestion.tag_strategy if seo_suggestion else None,
                },
            },
            "faq_assessment": article.faq_assessment if article else {},
            "faq_applicable": article.faq_applicable if article else None,
            "faq_editorial_notes": article.faq_editorial_notes if article else {},
            "faq_html": article.faq_html if article else None,
            "faqs": [
                {
                    "question": faq.question,
                    "answer": faq.answer,
                    "question_type": faq.question_type,  # Already a string
                    "search_intent": faq.search_intent,  # Already a string
                    "keywords_covered": faq.keywords_covered or [],
                    "confidence": float(faq.confidence) if faq.confidence else None,
                    "safety_warning": faq.safety_warning,  # v2.2 YMYL
                }
                for faq in faqs
            ],
            "generation_metadata": {
                "cached": True,
                "message": "Loaded from cache (no AI call)",
            },
        }

    def _calculate_savings(self, cost_usd: float, total_tokens: int, duration_ms: int) -> dict:
        """Calculate savings vs separate API calls."""
        # Estimated cost/time for separate calls (original approach)
        # Step 1 Title: ~2,700 tokens, $0.02-0.03, 10-15s
        # Step 3 SEO+FAQ: ~5,500 tokens, $0.08-0.10, 20-25s
        original_tokens = 8200
        original_cost = 0.115  # Average of $0.10-0.13
        original_duration_ms = 35000  # Average of 30-40s

        saved_tokens = original_tokens - total_tokens
        saved_cost = original_cost - cost_usd
        saved_time_ms = original_duration_ms - duration_ms

        return {
            "original_tokens": original_tokens,
            "original_cost_usd": round(original_cost, 4),
            "original_duration_ms": original_duration_ms,
            "saved_tokens": saved_tokens,
            "saved_cost_usd": round(saved_cost, 4),
            "saved_duration_ms": saved_time_ms,
            "cost_savings_percentage": round((saved_cost / original_cost) * 100, 1),
            "time_savings_percentage": round((saved_time_ms / original_duration_ms) * 100, 1),
        }
