# SpecKit Documentation Update Summary

**Date**: 2025-11-08
**Phase**: Phase 7 - Proofreading Integration with Parsed Content
**Status**: Documentation Complete ✅ | Implementation Pending 🔄

---

## Overview

Following the user's discovery that proofreading was using `article.body` instead of `article.body_html` after Phase 7 parsing, comprehensive documentation has been created to plan and track the integration work required to fix this issue.

---

## Problem Statement

**Original Issue**: After Phase 7 article parsing extracts structured data (title, author, SEO) into separate fields and creates clean `body_html`, the proofreading workflow was still using `article.body` which may contain:
- ❌ Title components (already reviewed in Step 1)
- ❌ Author information (already reviewed in Step 1)
- ❌ Meta/SEO blocks (already reviewed in Step 1)
- ❌ Unprocessed images (already managed in Step 1)

**Expected Behavior**: Proofreading should ONLY check `body_html` (cleaned content) for parsed articles.

---

## Documentation Created

### 1. Technical Analysis Document ✅

**File**: `backend/docs/phase7_proofreading_integration_analysis.md` (600+ lines)

**Contents**:
- Problem statement with code examples
- Requirements definition (FR-1 to FR-4, NFR-1 to NFR-3)
- Workflow design (ideal vs compatibility flows)
- Implementation plan with detailed code snippets
- Comprehensive test plan (unit, integration, regression, performance)
- Task breakdown (T7.30-T7.36, 11 hours total)
- Acceptance criteria
- Risk analysis and mitigation strategies

**Key Sections**:
- 🔄 Workflow Design: Parse → Proofread (body_html) vs Legacy (body)
- 🛠️ Implementation Plan: 3 code modification points
- ✅ Test Plan: Unit tests, integration tests, regression tests
- 📋 Task Breakdown: 7 tasks with hourly estimates

---

### 2. SpecKit Updates ✅

#### A. `specs/001-cms-automation/spec.md`

**Added Requirements**: FR-106 to FR-110 (Proofreading Integration with Parsed Content)

**New Sections**:

1. **FR-106**: Content Source Selection
   - Priority: `body_html` (parsed) > `body` (unparsed)
   - Warning emission for unparsed articles

2. **FR-107**: Field Exclusions
   - ❌ Do NOT proofread: `title_*`, `author_*`, `meta_description`, `seo_keywords`, `tags`
   - ✅ ONLY proofread: `body_html` content

3. **FR-108**: Parsing Metadata Inclusion
   - Include parsing status in proofreading payload
   - Provide title components and author info for context

4. **FR-109**: Result Application Logic
   - Parsed articles: update `body_html`
   - Unparsed articles: update `body` (backward compatibility)
   - Preserve all structured fields

5. **FR-110**: Workflow Prerequisites (Optional)
   - Warning if accessing proofreading before parsing
   - Configurable enforcement (warn/block)
   - User can proceed anyway

**Metadata**:
- Implementation Priority: P0 (Critical)
- Estimated Effort: 11 hours
- Dependencies: Phase 7 Article Parsing (FR-088 to FR-105)

---

#### B. `specs/001-cms-automation/tasks.md`

**Added Tasks**: T7.30 to T7.36 (Week 23: Proofreading Integration)

**Task Breakdown**:

| Task | Description | Hours | Dependencies |
|------|-------------|-------|--------------|
| **T7.30** | Update Proofreading Payload Construction | 2h | T7.3, T7.15 |
| **T7.31** | Add Parsing Prerequisite Check | 1h | T7.30 |
| **T7.32** | Update Result Application Logic | 1.5h | T7.30 |
| **T7.33** | Unit Tests for Payload Construction | 2h | T7.30-T7.32 |
| **T7.34** | Integration Tests for Workflow | 2h | T7.30-T7.33 |
| **T7.35** | Update API Documentation | 1h | T7.30-T7.32 |
| **T7.36** | Update SpecKit Documentation | 1.5h | T7.35 |
| **Total** | | **11h** | |

**Updated Phase 7 Summary**:
- Duration: 6 weeks → **7 weeks** (Week 16-23)
- Estimated Hours: 140h → **151h** (140 parsing + 11 integration)
- Key Deliverables: Added "Proofreading integration (body_html priority, backward compatibility)"

---

## Implementation Plan

### Code Modifications Required

#### 1. Backend: Payload Construction (T7.30)

**File**: `backend/src/api/routes/articles.py`

**Function**: `_build_article_payload(article: Article) -> ArticlePayload`

**Changes**:
```python
# Before (WRONG)
original_content = article.body or ""

# After (CORRECT)
has_been_parsed = bool(article.body_html)
content_to_proofread = article.body_html if has_been_parsed else article.body or ""

# Add parsing metadata
parsing_metadata = {
    "parsed": has_been_parsed,
    "parsing_confirmed": article.parsing_confirmed,
    "title_components": {...},
    "author": {...}
}
metadata["parsing"] = parsing_metadata
```

---

#### 2. Backend: Result Application (T7.32)

**File**: `backend/src/api/routes/articles.py`

**Changes**:
- For parsed articles: update `article.body_html` with corrected content
- For unparsed articles: update `article.body` (legacy)
- Never overwrite `title_*`, `author_*`, SEO fields

---

#### 3. Backend: Prerequisite Warning (T7.31)

**File**: `backend/src/api/routes/articles.py`

**Changes**:
- Check `article.parsing_confirmed` flag
- Emit warning if false: "建议先进行文章解析以获得更准确的校对结果"
- Add config option: `REQUIRE_PARSING_BEFORE_PROOFREADING`

---

### Test Coverage Required

#### Unit Tests (T7.33)
- Test payload construction with parsed article
- Test payload construction with unparsed article
- Test parsing metadata inclusion
- Test warning generation

**File**: `backend/tests/unit/test_proofreading_payload.py` (new)

---

#### Integration Tests (T7.34)
1. Full workflow: Import → Parse → Confirm → Proofread → Apply → Verify
2. Backward compatibility: Import → Proofread (unparsed) → Verify warning
3. Field preservation: Verify structured fields not overwritten

**File**: `backend/tests/integration/test_parsing_proofreading_integration.py` (new)

---

## Workflow Diagrams

### Ideal Workflow (New Articles)

```
┌─────────────┐
│   Import    │ ← Google Drive sync
│   Article   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│    Parse    │ ← ArticleParserService (AI)
│   Article   │   Extracts: title_*, author_*, images, SEO
└──────┬──────┘   Creates: body_html (clean)
       │
       ▼
┌─────────────┐
│   Review    │ ← Step 1 UI (解析確認)
│   Parsing   │   Confirm: titles, author, images, meta
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Proofread  │ ← Uses body_html ONLY ✅
│  (body_html)│   Checks: grammar, style, content
└──────┬──────┘
       │
       ▼
┌─────────────┐
│    Apply    │ ← Updates body_html
│   Changes   │   Preserves: title_*, author_*, SEO
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Publish   │
│to WordPress │
└─────────────┘
```

### Compatibility Workflow (Legacy Articles)

```
┌─────────────┐
│   Legacy    │ ← Old articles (no parsing)
│   Article   │   Only has: body, title (flat)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Proofread  │ ← Uses body ⚠️
│   (body)    │   Shows warning: "建议先解析"
└──────┬──────┘
       │
       ▼
┌─────────────┐
│    Apply    │ ← Updates body (legacy)
│   Changes   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Publish   │
│to WordPress │
└─────────────┘
```

---

## Acceptance Criteria

### Functional Requirements ✅

- [ ] **FR-1**: Parsed articles use `body_html` for proofreading
- [ ] **FR-2**: Unparsed articles use `body` (backward compatibility)
- [ ] **FR-3**: Structured fields never overwritten by proofreading
- [ ] **FR-4**: Warning shown for unparsed articles

### Non-Functional Requirements ✅

- [ ] **NFR-1**: Zero breaking changes to existing API
- [ ] **NFR-2**: Test coverage ≥85% for modified code
- [ ] **NFR-3**: Performance impact <10ms per proofreading request

### Testing Requirements ✅

- [ ] Unit tests pass (payload construction)
- [ ] Integration tests pass (full workflow)
- [ ] Regression tests pass (unparsed articles)
- [ ] Performance tests pass (<10ms overhead)

---

## Risk Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Breaking existing proofreading for unparsed articles | Medium | High | Backward compatibility mode using `body` |
| Users confused by parsing prerequisite | Medium | Medium | Optional warning (not blocking) |
| Performance degradation | Low | Medium | Minimal logic, cached parsing status |
| Test coverage gaps | Low | High | Comprehensive test plan (unit + integration) |

---

## Next Steps

### Immediate Actions (Pending User Approval)

1. **Review Documentation** ✅ DONE
   - `backend/docs/phase7_proofreading_integration_analysis.md`
   - `specs/001-cms-automation/spec.md` (FR-106 to FR-110)
   - `specs/001-cms-automation/tasks.md` (T7.30 to T7.36)

2. **Await User Approval** 🔄 CURRENT STEP
   - User reviews requirements and implementation plan
   - User confirms approach is correct
   - User approves moving to implementation phase

3. **Implementation Phase** ⏳ WAITING
   - Execute tasks T7.30-T7.36 in sequence
   - Follow TDD approach (tests first)
   - Submit for code review after each major task

---

## Files Modified/Created

### Documentation Files

- ✅ `backend/docs/phase7_proofreading_integration_analysis.md` (NEW)
- ✅ `specs/001-cms-automation/spec.md` (UPDATED - added FR-106 to FR-110)
- ✅ `specs/001-cms-automation/tasks.md` (UPDATED - added T7.30 to T7.36)
- ✅ `backend/docs/SPECKIT_UPDATE_SUMMARY.md` (NEW - this file)

### Implementation Files (Pending)

- ⏳ `backend/src/api/routes/articles.py` (Payload construction + result application)
- ⏳ `backend/src/config/settings.py` (Add REQUIRE_PARSING_BEFORE_PROOFREADING)
- ⏳ `backend/tests/unit/test_proofreading_payload.py` (NEW - unit tests)
- ⏳ `backend/tests/integration/test_parsing_proofreading_integration.py` (NEW - integration tests)
- ⏳ `specs/001-cms-automation/api-spec.yaml` (API documentation)
- ⏳ `backend/docs/api/proofreading.md` (Workflow documentation)

---

## Summary

**Documentation Status**: ✅ **COMPLETE**

All planning and analysis documents have been created per user's directive:
- ✅ Technical analysis completed (600+ lines)
- ✅ Requirements defined (FR-106 to FR-110)
- ✅ Tasks broken down (T7.30 to T7.36, 11 hours)
- ✅ Test plan documented (unit, integration, regression)
- ✅ SpecKit updated (spec.md, tasks.md)
- ✅ Workflow diagrams created
- ✅ Risk analysis completed

**Implementation Status**: ⏳ **PENDING USER APPROVAL**

No code changes have been made yet. Implementation will begin after:
1. User reviews all documentation
2. User confirms requirements are correct
3. User approves implementation approach
4. User gives explicit approval to proceed

**Estimated Implementation Time**: 11 hours across 7 tasks (T7.30-T7.36)

---

**Document Owner**: Engineering Team
**Reviewers**: Product Team, User (Content Quality Lead)
**Next Review**: After implementation completion
**Version**: 1.0.0
