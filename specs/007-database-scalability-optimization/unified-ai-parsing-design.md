# Unified AI Parsing Solution Design
**Date**: 2025-11-18
**Version**: 1.0.0
**Status**: Design Phase
**Author**: System Architecture Team

---

## 1. Executive Summary

### Current State Analysis

The CMS currently uses a **three-phase, multi-service architecture** that causes significant issues:

#### Problems Identified:
1. **Disconnected Services**: Three separate AI calls (parsing, optimization, proofreading)
2. **Data Flow Issues**: SEO suggestions (`suggested_*` fields) are not automatically generated
3. **Cost Inefficiency**: Multiple API calls cost ~$0.20-0.30 per article
4. **Time Waste**: Total processing takes 60-90 seconds across phases
5. **User Experience**: Must manually trigger optimization endpoint `/v1/articles/{id}/generate-all-optimizations`

#### Current Architecture:
```
Phase 1: ArticleParserService (Claude AI)
  └─> Extracts: title, author, body, basic SEO

Phase 2: UnifiedOptimizationService (Separate Claude call)
  └─> Generates: suggested titles, suggested SEO, FAQ

Phase 3: Proofreading Service (Another Claude call)
  └─> Identifies: grammar errors, style issues
```

### Proposed Solution

**Single AI Call Architecture**: Consolidate all functionality into ONE Claude API call during parsing.

#### Benefits:
- **Cost Reduction**: 60-70% savings ($0.08-0.10 per article)
- **Speed Improvement**: 50% faster (30-40 seconds total)
- **Data Consistency**: All fields populated in one transaction
- **Simplified Workflow**: No manual optimization triggers needed

---

## 2. Detailed Design

### 2.1 Unified Prompt Architecture

The new `ArticleParserService` will use an enhanced prompt that combines:

```python
class UnifiedParsingPrompt:
    """
    单一提示词包含所有功能:
    1. 文章解析 (Parsing)
    2. SEO优化建议 (SEO Optimization)
    3. 校对检查 (Proofreading)
    4. FAQ生成 (FAQ Generation)
    """
```

### 2.2 Enhanced Response Structure

```json
{
  // === Phase 1: Basic Parsing ===
  "title_prefix": "【專題報導】",
  "title_main": "2024年醫療保健創新趨勢",
  "title_suffix": "從AI診斷到遠距醫療",
  "author_line": "文／張三｜編輯／李四",
  "author_name": "張三",
  "body_html": "<p>正文內容...</p>",
  "images": [...],

  // === Phase 2: SEO Optimization ===
  "seo_title": "2024年AI醫療創新趨勢",  // Extracted if marked
  "meta_description": "本文探討2024年醫療保健...", // Basic version

  // NEW: AI-Optimized Suggestions
  "suggested_titles": [
    {
      "prefix": "【深度解析】",
      "main": "AI醫療革命：2024年十大創新技術",
      "suffix": "改變未來的健康科技",
      "score": 0.92,
      "reason": "更吸引點擊，包含關鍵詞"
    },
    {
      "prefix": "【產業觀察】",
      "main": "2024醫療AI應用大爆發",
      "suffix": "遠距診療新時代來臨",
      "score": 0.88,
      "reason": "簡潔有力，突出時效性"
    }
  ],

  "suggested_seo": {
    "meta_title": "2024 AI醫療創新｜10大突破技術完整解析",
    "meta_description": "深入探討2024年AI在醫療領域的革命性應用，包括智能診斷、遠距醫療、精準醫學等十大創新技術，了解如何改變未來健康產業。",
    "focus_keyword": "AI醫療",
    "primary_keywords": ["人工智能醫療", "智能診斷", "遠距醫療"],
    "secondary_keywords": ["醫療科技", "數位健康", "精準醫學"],
    "tags": ["醫療", "AI", "科技創新", "健康產業"]
  },

  // === Phase 3: Proofreading Results ===
  "proofreading_issues": [
    {
      "rule_id": "TYPO_001",
      "severity": "medium",
      "location": {"paragraph": 3, "sentence": 2},
      "original_text": "醫療保建",
      "suggested_text": "醫療保健",
      "explanation": "錯字：'建'應為'健'",
      "confidence": 0.95
    },
    {
      "rule_id": "STYLE_003",
      "severity": "low",
      "location": {"paragraph": 5, "sentence": 1},
      "original_text": "然後，接著",
      "suggested_text": "接著",
      "explanation": "冗餘：'然後'和'接著'重複",
      "confidence": 0.88
    }
  ],

  "proofreading_stats": {
    "total_issues": 12,
    "critical": 0,
    "high": 2,
    "medium": 5,
    "low": 5,
    "auto_fixable": 8
  },

  // === Phase 4: FAQ Generation ===
  "faqs": [
    {
      "question": "什麼是AI醫療診斷技術？",
      "answer": "AI醫療診斷是利用機器學習和深度學習算法...",
      "intent": "definition",
      "importance": "high"
    },
    {
      "question": "遠距醫療如何改變就醫體驗？",
      "answer": "遠距醫療透過視訊通話和數位工具...",
      "intent": "how_to",
      "importance": "high"
    }
  ],

  // === Metadata ===
  "parsing_metadata": {
    "model": "claude-sonnet-4-5",
    "tokens_used": 8500,
    "cost_usd": 0.095,
    "duration_ms": 35000,
    "confidence_scores": {
      "parsing": 0.96,
      "seo": 0.91,
      "proofreading": 0.89,
      "faq": 0.87
    }
  }
}
```

### 2.3 Implementation Plan

#### Step 1: Create Enhanced Prompt Template

```python
def _build_unified_ai_prompt(self, raw_html: str) -> str:
    """Build comprehensive prompt for all operations."""
    return f"""You are an expert content processor for Chinese articles.

    Perform ALL the following tasks in a SINGLE response:

    ## Task 1: Parse Article Structure
    - Extract title parts (prefix, main, suffix)
    - Extract author information
    - Clean and structure body HTML
    - Extract images with captions

    ## Task 2: Generate SEO Optimizations
    - Create 2-3 optimized title variations
    - Generate SEO-optimized meta title (30 chars)
    - Write compelling meta description (150-160 chars)
    - Identify focus keyword and related keywords
    - Suggest 3-6 content tags

    ## Task 3: Proofread Content
    - Identify spelling errors (錯別字)
    - Check grammar issues (語法錯誤)
    - Find style problems (文體問題)
    - Detect redundancies (冗餘表達)
    - Mark factual concerns (事實疑慮)

    ## Task 4: Generate FAQ
    - Create 6-8 frequently asked questions
    - Cover different user intents (what, why, how)
    - Provide comprehensive answers

    [Detailed JSON structure specification...]

    HTML Content:
    {raw_html}
    """
```

#### Step 2: Update ArticleParserService

```python
class ArticleParserService:
    def parse_document(self, raw_html: str) -> UnifiedParsingResult:
        """Single method that returns ALL data."""

        # One AI call for everything
        prompt = self._build_unified_ai_prompt(raw_html)
        response = self._call_claude_api(prompt)

        # Parse and validate response
        result = self._parse_unified_response(response)

        # Save to database in one transaction
        await self._save_all_data(result)

        return result
```

#### Step 3: Database Schema Updates

```sql
-- Ensure all fields exist in articles table
ALTER TABLE articles ADD COLUMN IF NOT EXISTS
    suggested_titles JSONB,
    suggested_meta_description TEXT,
    suggested_seo_keywords JSONB,
    proofreading_issues JSONB,
    proofreading_stats JSONB,
    faqs JSONB,
    parsing_metadata JSONB;
```

---

## 3. Migration Strategy

### 3.1 Phased Rollout

| Phase | Duration | Tasks | Risk |
|-------|----------|-------|------|
| **Phase A** | 1 week | Update prompt, test locally | Low |
| **Phase B** | 1 week | Update parser service, add fields | Low |
| **Phase C** | 1 week | Migrate existing data | Medium |
| **Phase D** | 1 week | Deploy to production | Medium |

### 3.2 Backward Compatibility

- Keep old endpoints operational for 30 days
- Add feature flag: `USE_UNIFIED_PARSER`
- Gradual migration of existing articles

---

## 4. SpecKit Alignment

### 4.1 Conflicts with Current Plan

The current `plan.md` states **"Single-Prompt Proofreading & SEO"** in the Executive Summary, but implementation is split across phases:

| Document | Current State | Required Change |
|----------|--------------|-----------------|
| `plan.md` | Phase 7 (Parsing) + Phase 2 (SEO) separate | Merge into Phase 7.5 "Unified Parsing" |
| `tasks.md` | Separate task blocks | Consolidate parsing tasks |
| `spec.md` | Multi-service architecture | Update to single-service |

### 4.2 Required SpecKit Updates

#### Update plan.md Phase 7:
```markdown
## Phase 7 – Unified AI Parsing (Extended)
**Duration**: 8 weeks → 10 weeks
**New Scope**: Single AI call for parsing + SEO + proofreading + FAQ

### Architecture Change:
- OLD: ArticleParser → OptimizationService → ProofreadingService
- NEW: UnifiedArticleParser (all-in-one)
```

#### Create new task in tasks.md:
```markdown
### T-UNIFY-1: Implement Unified AI Parser
**Priority**: P0
**Duration**: 40 hours
**Dependencies**: Phase 7 completion

Consolidate all AI operations into single parser:
- [ ] Design comprehensive prompt template
- [ ] Update ArticleParserService class
- [ ] Add all suggested_* fields to response
- [ ] Include proofreading in parsing
- [ ] Generate FAQ during parsing
- [ ] Update database schema
- [ ] Migrate existing articles
```

---

## 5. Cost-Benefit Analysis

### 5.1 Cost Comparison

| Metric | Current (3 Calls) | Unified (1 Call) | Savings |
|--------|------------------|------------------|---------|
| **API Calls** | 3 | 1 | 67% |
| **Tokens Used** | ~15,000 | ~9,000 | 40% |
| **Cost per Article** | $0.25 | $0.10 | 60% |
| **Processing Time** | 75s | 35s | 53% |
| **Manual Steps** | 2 | 0 | 100% |

### 5.2 Monthly Projections

Assuming 1,000 articles/month:
- **Current Cost**: $250/month
- **Unified Cost**: $100/month
- **Annual Savings**: $1,800

---

## 6. Implementation Checklist

### Week 1: Design & Planning
- [ ] Finalize unified prompt template
- [ ] Review with stakeholders
- [ ] Update SpecKit documentation
- [ ] Create test dataset

### Week 2: Development
- [ ] Modify ArticleParserService
- [ ] Update response models
- [ ] Add database fields
- [ ] Write unit tests

### Week 3: Testing
- [ ] Test with 100 sample articles
- [ ] Compare results with current system
- [ ] Optimize prompt based on results
- [ ] Performance testing

### Week 4: Deployment
- [ ] Deploy to staging
- [ ] Run parallel comparison
- [ ] Monitor error rates
- [ ] Production rollout

---

## 7. Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Prompt Too Complex** | High | Iterative refinement, A/B testing |
| **Response Timeout** | Medium | Increase timeout, optimize prompt |
| **Quality Degradation** | High | Parallel run for validation |
| **Breaking Changes** | Medium | Feature flag, gradual rollout |

---

## 8. Success Metrics

### Primary KPIs:
- API cost reduction ≥ 50%
- Processing time < 40 seconds
- All fields populated in single call
- Zero manual optimization triggers

### Quality Metrics:
- SEO suggestion acceptance rate > 70%
- Proofreading accuracy > 85%
- FAQ relevance score > 0.8
- User satisfaction > 4.0/5.0

---

## 9. Next Steps

1. **Immediate**: Review and approve this design
2. **Week 1**: Start prompt engineering
3. **Week 2**: Begin implementation
4. **Week 3**: Testing phase
5. **Week 4**: Production deployment

---

## Appendix A: Unified Prompt Template

[Full 200-line prompt template with all instructions...]

## Appendix B: Response Validation Schema

[Pydantic model for complete response...]

## Appendix C: Migration Script

[Python script to migrate existing articles...]