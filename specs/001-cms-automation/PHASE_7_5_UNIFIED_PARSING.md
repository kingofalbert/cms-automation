# Phase 7.5 – Unified AI Parsing (NEW)
**Date Added**: 2025-11-18
**Duration**: 4 weeks
**Priority**: P0 (Critical - Solves root cause issues)
**Dependencies**: Phase 7 completion

---

## Overview

This new phase **consolidates all AI operations** into a single Claude API call during article parsing, addressing the root cause of NULL SEO fields and disconnected services.

### Problems Being Solved

1. **Disconnected Services** → **Unified Service**
   - OLD: ArticleParser → OptimizationService → ProofreadingService (3 calls)
   - NEW: UnifiedArticleParser (1 call)

2. **Manual Triggers Required** → **Automatic Population**
   - OLD: Must call `/v1/articles/{id}/generate-all-optimizations` manually
   - NEW: All fields populated during initial parsing

3. **High Cost** → **60% Cost Reduction**
   - OLD: $0.25 per article (3 API calls)
   - NEW: $0.10 per article (1 API call)

---

## Architecture Changes

### Before (Current Phase 7):
```
parse_document() → Basic fields only
  ├─> title_main, author_name, body_html
  └─> NO suggested_* fields

generate_optimizations() → Separate call
  ├─> suggested_titles
  ├─> suggested_meta_description
  └─> suggested_seo_keywords

proofread() → Another separate call
  └─> proofreading_issues
```

### After (Phase 7.5):
```
parse_document_unified() → ALL fields in one call
  ├─> Basic parsing (title, author, body)
  ├─> SEO optimization suggestions
  ├─> Proofreading results
  └─> FAQ generation
```

---

## Implementation Tasks

### T-7.5-1: Enhanced Prompt Engineering (Week 1)
- Design comprehensive prompt template combining all operations
- Include parsing + SEO + proofreading + FAQ instructions
- Test with 50 sample articles
- **Deliverable**: `unified_parsing_prompt.py`

### T-7.5-2: Update ArticleParserService (Week 2)
- Modify `_build_ai_parsing_prompt()` to use unified template
- Extend response parsing to handle all new fields
- Add `suggested_*` fields to ParsedArticle model
- **Deliverable**: Updated `article_parser.py`

### T-7.5-3: Database Schema Updates (Week 2)
- Add missing columns to articles table:
  - `suggested_titles JSONB`
  - `proofreading_issues JSONB`
  - `proofreading_stats JSONB`
  - `faqs JSONB`
- **Deliverable**: Migration script `alembic/versions/xxx_add_unified_fields.py`

### T-7.5-4: API Response Updates (Week 3)
- Update `ArticleResponse` schema to include all new fields
- Update `WorklistItemDetailResponse` to populate from unified data
- Remove dependency on separate optimization endpoint
- **Deliverable**: Updated schemas in `api/schemas/`

### T-7.5-5: Testing & Validation (Week 3-4)
- Compare results with current multi-service approach
- Validate quality of suggestions
- Performance testing (target: <40 seconds)
- Cost analysis verification
- **Deliverable**: Test report and metrics

### T-7.5-6: Migration & Rollout (Week 4)
- Feature flag: `USE_UNIFIED_PARSER`
- Parallel run for validation
- Gradual rollout (10% → 50% → 100%)
- Monitor error rates and quality metrics
- **Deliverable**: Production deployment

---

## Success Metrics

| Metric | Current | Target | Measurement |
|--------|---------|--------|-------------|
| **API Calls per Article** | 3 | 1 | CloudWatch logs |
| **Cost per Article** | $0.25 | $0.10 | Claude API billing |
| **Processing Time** | 75s | 35s | Performance logs |
| **Field Population Rate** | 40% | 100% | Database queries |
| **Manual Optimization Calls** | Required | 0 | API metrics |

---

## Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Prompt too complex | High | Iterative refinement, A/B testing |
| Quality degradation | High | Parallel validation, quality thresholds |
| Timeout issues | Medium | Optimize prompt, increase timeout |
| Breaking changes | Medium | Feature flag, backward compatibility |

---

## Integration with Phase 8

Phase 7.5 **must complete before Phase 8** (Workflow Simplification) because:
1. Phase 8 UI depends on all fields being populated
2. Modal design assumes single-source data
3. User experience requires no manual triggers

---

## Cost-Benefit Analysis

### Monthly Impact (1000 articles):
- **Cost Savings**: $150/month ($1,800/year)
- **Time Savings**: 11 hours/month (40s × 1000)
- **Manual Work Eliminated**: 100%

### ROI:
- **Implementation Cost**: 160 hours (4 weeks × 40 hours)
- **Break-even**: 2 months
- **Annual ROI**: 450%

---

## Alignment with Original Vision

This phase finally implements what was promised in the Executive Summary:
> "Core Workflow: Article Import → **Single-Prompt Proofreading & SEO** → Deterministic Merge → Computer Use Publishing"

We're correcting the implementation to match the original architectural vision.