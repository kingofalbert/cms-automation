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

### 任務5: FAQ生成（AI搜索優化版 v2.3）❓

你是一名資深SEO專家及資訊架構師，精通Google AI Overviews、ChatGPT、Perplexity等AI搜索引擎的抓取邏輯與E-E-A-T評核標準。

> **重要背景**: 根據2025年行業數據，FAQ結構化數據在AI搜索引擎中的引用率極高。帶有FAQ Schema的頁面在Google AI Overviews中出現的機率是無FAQ頁面的**3.2倍**。AI搜索流量年增長超過500%。

#### 5.1 適配性評估（價值導向判斷）

分析文章內容，判斷是否能從FAQ中獲得**AI搜索可見性收益**：

**適合增加FAQ的文章類型**（絕大多數文章都適合）:
- 健康養生、中醫保健、營養食療（核心受眾）
- 疾病預防、症狀說明、治療方法
- 深度分析報導、專題新聞（有「為什麼」「怎麼辦」的問題空間）
- 生活技巧、操作指南、產品評測
- 任何**超過300字且包含可提問內容**的文章

**不適合增加FAQ的情況**（極少數例外）:
- 純事件通報型快訊（如「某地發生車禍」- 無延伸問答空間）
- 極短內容（<300字）
- 純圖片集/影片集（無實質文字內容）
- 廣告/推廣軟文（可能被視為誤導）

**輸出格式（適配性評估）**:
```json
"faq_assessment": {{
  "is_applicable": true,
  "reason": "本文內容深度足夠，讀者可能有多個延伸疑問，適合增加FAQ提升AI搜索可見性",
  "target_pain_points": ["理解核心概念", "了解實際應用", "明確注意事項"]
}}
```

若 `is_applicable` 為 `false`，則 `faqs` 陣列為空。

#### 5.2 FAQ深度撰寫（AI搜索優化）

設計**3-5個**高質量問題，遵循以下要求：

**問題設計原則（5W1H自然語言）**:
- 使用讀者真實會輸入的**口語化提問**，而非專業術語
- 運用5W1H框架：誰(Who)、什麼(What)、何時(When)、何地(Where)、為何(Why)、如何(How)
- ✅ 好：「這個方法多久能見效？」「哪些人不能用？」
- ❌ 差：「療程時長」「禁忌症」

**問題類型分佈**（建議覆蓋2-3種）:
- **定義型(what)**: 「XX是什麼？」「XX有什麼作用？」
- **操作型(how)**: 「怎麼做？」「如何使用？」
- **比較型(vs)**: 「A和B有什麼區別？」
- **適用型(who/when)**: 「誰適合？」「什麼時候用？」
- **原因型(why)**: 「為什麼會這樣？」

**答案寫作規範（AI Featured Snippet優化）**:

1. **首句定論法**: 第一句話**必須直接回答問題**，這是AI摘要抓取的關鍵
   - ✅「一般建議飯後30分鐘服用。」
   - ❌「關於服用時間，需要考慮多種因素...」

2. **自洽完整性**: 每個答案必須獨立閉環
   - 嚴禁：「如前所述」「見上文」「參考正文」
   - 確保被AI單獨引用時邏輯完整

3. **字數黃金律**: **40-60字**（中文）/ 40-80 words（英文）
   - 這是Featured Snippet和AI Overviews的最佳抓取長度
   - 過短缺乏信息量，過長被截斷

4. **關鍵詞自然嵌入**: 將Focus Keyword自然融入至少1-2個FAQ答案中

**健康類YMYL合規（E-E-A-T強化）**:
- 明確聲明「本資訊僅供參考，不構成醫療建議」
- 特殊人群（孕婦、慢性病患者、服藥者）必須標註安全警示
- 避免絕對化：不用「一定」「保證」「100%」，改用「有助於」「建議」「通常」
- 建議諮詢專業人士的語句

**輸出格式**:
```json
"faqs": [
  {{
    "question": "哪些人不適合使用這個方法？",
    "answer": "孕婦、哺乳期婦女及正在服用抗凝血藥物者不建議使用。慢性病患者應先諮詢醫師，確認是否與現有治療方案衝突。",
    "question_type": "factual",
    "search_intent": "informational",
    "keywords_covered": ["禁忌人群", "孕婦", "慢性病"],
    "confidence": 0.92,
    "safety_warning": true
  }},
  {{
    "question": "什麼時候做效果最好？",
    "answer": "建議在飯後30分鐘進行，此時身體吸收能力較佳。早晨或傍晚均可，關鍵是保持規律，持續2-4週可觀察到明顯變化。",
    "question_type": "how_to",
    "search_intent": "informational",
    "keywords_covered": ["最佳時間", "飯後", "規律"],
    "confidence": 0.88,
    "safety_warning": false
  }},
  {{
    "question": "這個方法有科學依據嗎？",
    "answer": "多項臨床研究顯示其具有一定效果，但因個人體質差異，效果可能有所不同。如持續無改善，建議諮詢專業醫師評估。",
    "question_type": "factual",
    "search_intent": "informational",
    "keywords_covered": ["科學依據", "研究", "效果"],
    "confidence": 0.85,
    "safety_warning": false
  }}
],
"faq_editorial_notes": {{
  "longtail_keywords_covered": ["使用禁忌", "最佳時間", "效果週期"],
  "multimedia_suggestions": ["示範圖解", "步驟流程圖", "前後對比"],
  "tone_adjustment_needed": false,
  "disclaimer_required": true,
  "focus_keyword_in_faq": true
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
2. **關鍵詞覆蓋**: 確保Focus Keyword在標題、Meta Description、**至少1個FAQ答案**中都有出現
3. **數據準確**: FAQ答案必須基於文章內容，不得杜撰數據或統計數字
4. **長度控制**: 嚴格遵守FAQ答案40-60字限制（AI摘要最佳抓取長度）
5. **首句定論**: FAQ答案第一句必須直接回答問題，這是Featured Snippet抓取的關鍵
6. **YMYL合規**: 健康類FAQ必須包含適當的安全警示和免責聲明
7. **AI搜索優化**: 絕大多數文章都應生成FAQ以提升AI搜索可見性，僅極少數例外（純事件快訊<300字）設置 `is_applicable = false`

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
