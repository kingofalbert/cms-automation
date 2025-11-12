# Pipeline Issues Analysis - Critical Bugs in Parsing Flow

## Date: 2025-11-12
## Report by: Codex CLI + Claude Analysis

---

## 🚨 Executive Summary

**Status**: ✅ **ISSUES CONFIRMED - Both P1 issues are VALID and require immediate fixes**

Codex CLI identified two critical bugs in the worklist pipeline that make the new parsing stage ineffective:

1. **[P1] Parsing failures don't stop proofreading** - Breaks the review gate
2. **[P1] Parser receives cleaned text instead of HTML** - Images and structure lost

Both issues are **confirmed** and **actively breaking** the parsing functionality.

---

## 🔍 Issue #1: Skip Proofreading When Parsing Fails

### Problem Statement

**Location**: `backend/src/services/worklist/pipeline.py:47-55, 94-210`

**Current Behavior**:
```python
async def process_new_item(self, item: WorklistItem) -> None:
    """Ensure article exists, run parsing, then proofreading."""
    article = await self._ensure_article(item)

    # Step 1: Parse document
    await self._run_parsing(item)  # ❌ NEVER signals failure

    # Step 2: Run proofreading - ALWAYS executes
    await self._run_proofreading(item, article)  # ❌ Runs even if parsing failed
```

**Root Cause Analysis**:

`_run_parsing()` has **three code paths** but **none propagate failure upward**:

#### Path 1: Parsing Fails (Lines 110-127)
```python
if not parsing_result.success:
    # Parsing failed
    logger.error("worklist_parsing_failed", ...)
    item.mark_status(WorklistStatus.PARSING)  # ✅ Correct status
    item.add_note({"message": "AI解析失败，需要手动审核", ...})
    self.session.add(item)
    return  # ❌ Returns but doesn't signal failure
```

**Analysis**:
- ✅ Sets status to `PARSING` (waiting for manual review)
- ❌ **Returns without raising** → `process_new_item` continues
- ❌ **No return value** → Caller can't detect failure

#### Path 2: Parsing Succeeds (Lines 129-192)
```python
# Parsing succeeded
parsed_article = parsing_result.parsed_article
# ... update worklist item with parsed data ...
item.mark_status(WorklistStatus.PARSING_REVIEW)  # ✅ Correct
item.add_note({"message": "AI解析完成，等待人工审核解析结果", ...})
self.session.add(item)
# ❌ No explicit return value (implicit None)
```

**Analysis**:
- ✅ Sets status to `PARSING_REVIEW` (waiting for human approval)
- ❌ **No return value** → Success not communicated

#### Path 3: Exception Thrown (Lines 194-209)
```python
except Exception as exc:
    logger.error("worklist_parsing_exception", ...)
    item.mark_status(WorklistStatus.PARSING)  # ✅ Correct status
    item.add_note({"message": "解析过程异常，需要重试", ...})
    self.session.add(item)
    # ❌ Swallows exception, doesn't re-raise
```

**Analysis**:
- ✅ Sets status to `PARSING` (needs retry)
- ❌ **Exception swallowed** → No failure signal
- ❌ **No return value**

### Impact

**Severity**: 🔴 **CRITICAL**

1. **Review Gate Broken**: Items that fail parsing still advance to `proofreading_review`
2. **Status Confusion**: `_run_proofreading` overwrites status from `PARSING` → `PROOFREADING_REVIEW`
3. **Operator Confusion**: Failed parsing items appear as "successfully proofread"
4. **Data Loss**: Parsing failures masked by proofreading execution
5. **Wasted API Costs**: Proofreading runs on unparsed content

**Example Flow (Current - BROKEN)**:
```
1. Parsing fails → status = PARSING
2. process_new_item continues (no failure signal)
3. _run_proofreading executes
4. Status overwritten → status = PROOFREADING_REVIEW
5. Article marked as IN_REVIEW
6. ❌ Parsing failure completely masked
```

### Verification

I reviewed the code at:
- `pipeline.py:47-55` - `process_new_item` unconditionally calls both functions
- `pipeline.py:94-210` - `_run_parsing` never returns success/failure boolean
- `pipeline.py:211+` - `_run_proofreading` always executes

**Confirmed**: ✅ **Issue exists exactly as described**

---

## 🔍 Issue #2: Parser Receives Cleaned Text, Not HTML

### Problem Statement

**Location**:
- `backend/src/services/worklist/pipeline.py:94-109`
- `backend/src/services/google_drive/sync_service.py:256-336`

**Current Flow**:

```
1. Google Drive Sync
   ├─ Download HTML: _export_google_doc(..., "text/html")  ✅ Has images
   ├─ Parse HTML: _parse_html_content(html_content)
   │  └─ GoogleDocsHTMLParser strips all <img> tags  ❌
   ├─ Result: cleaned_text (Markdown-like, no HTML)
   └─ Store: WorklistItem.content = cleaned_text  ❌

2. Pipeline Parsing
   ├─ Read: raw_html = item.content  ❌ Actually cleaned text
   └─ Parse: parser_service.parse_document(raw_html)  ❌ No images to find
```

### Root Cause Analysis

#### Step 1: HTML Export (sync_service.py:256)
```python
html_content = await self._export_google_doc(storage, file_id, "text/html")
```
✅ **Correct**: Downloads full HTML with `<img>` tags, styles, structure

#### Step 2: HTML Cleaning (sync_service.py:268)
```python
# Parse and clean the HTML
content, parsing_status = self._parse_html_content(html_content)
```

**Inside `_parse_html_content` (lines 353-379)**:
```python
def _parse_html_content(self, html_content: str) -> tuple[str, Any]:
    parser = GoogleDocsHTMLParser()  # ❌ Strips images
    parser.feed(html_content)
    cleaned_text = parser.get_clean_text()  # ❌ Returns plain text
    return cleaned_text, status
```

**What `GoogleDocsHTMLParser` does**:
- ✅ Removes Google Docs CSS/styles
- ✅ Extracts text content
- ❌ **Strips all `<img>` tags and src URLs**
- ❌ **Removes HTML structure** (headers, lists, etc.)
- ❌ **Loses formatting cues**

#### Step 3: Storage (sync_service.py:328)
```python
parsed = self._parse_document_content(content, file_name=file_name)
# content is already cleaned text (no HTML)
```

**Stored in database**:
```python
WorklistItem(
    content=content,  # ❌ Cleaned text, not HTML
    ...
)
```

#### Step 4: Pipeline Parsing (pipeline.py:98)
```python
async def _run_parsing(self, item: WorklistItem) -> None:
    raw_html = item.content  # ❌ Not HTML - it's cleaned text!

    parsing_result = self.parser_service.parse_document(raw_html)
    # ArticleParserService expects HTML with <img> tags
    # But receives plain text → no images found
```

### Impact

**Severity**: 🔴 **CRITICAL**

1. **Images Always Empty**: Parser can't find `<img>` tags in cleaned text
2. **Structure Lost**: No `<h1>`, `<h2>`, `<p>` tags for heuristic parsing
3. **AI Prompting Wrong**: AI receives sanitized text instead of rich HTML
4. **Metadata Extraction Fails**: Title/author/SEO extraction relies on HTML structure
5. **Parsing Requirements Unmet**: New parsing stage can't satisfy its design goals

**Example**:

**Original Google Docs HTML**:
```html
<h1>【健康】如何提升免疫力</h1>
<p>作者：張醫師</p>
<img src="https://lh3.googleusercontent.com/..." alt="免疫系統示意圖">
<p>文章內容...</p>
```

**Cleaned Text (Stored in `WorklistItem.content`)**:
```
【健康】如何提升免疫力
作者：張醫師
文章內容...
```
❌ **Image URL lost completely**

**Parser Receives**:
```python
# parse_document() gets:
raw_html = "【健康】如何提升免疫力\n作者：張醫師\n文章內容..."
# No <img>, no <h1>, no structure → Parsing fails
```

### Verification

I traced the complete data flow:

1. ✅ **Confirmed**: `sync_service.py:256` exports HTML with images
2. ✅ **Confirmed**: `sync_service.py:268` strips HTML to text
3. ✅ **Confirmed**: `pipeline.py:98` receives cleaned text, not HTML
4. ✅ **Confirmed**: ArticleParserService expects HTML structure

**Issue Confirmed**: ✅ **Exactly as described**

---

## 🛠️ Required Fixes

### Fix #1: Make `_run_parsing` Return Success/Failure

**Option A: Return Boolean (Recommended)**
```python
async def _run_parsing(self, item: WorklistItem) -> bool:
    """Parse document content.

    Returns:
        True if parsing succeeded and item is ready for proofreading
        False if parsing failed or needs manual review
    """
    try:
        raw_html = item.content
        parsing_result = self.parser_service.parse_document(raw_html)

        if not parsing_result.success:
            # Parsing failed
            logger.error("worklist_parsing_failed", ...)
            item.mark_status(WorklistStatus.PARSING)
            item.add_note({"message": "AI解析失败，需要手动审核", ...})
            self.session.add(item)
            return False  # ✅ Signal failure

        # Parsing succeeded
        parsed_article = parsing_result.parsed_article
        # ... update worklist item ...
        item.mark_status(WorklistStatus.PARSING_REVIEW)
        item.add_note({"message": "AI解析完成，等待人工审核", ...})
        self.session.add(item)
        return True  # ✅ Signal success (but needs review)

    except Exception as exc:
        logger.error("worklist_parsing_exception", ...)
        item.mark_status(WorklistStatus.PARSING)
        item.add_note({"message": "解析过程异常，需要重试", ...})
        self.session.add(item)
        return False  # ✅ Signal failure

async def process_new_item(self, item: WorklistItem) -> None:
    """Ensure article exists, run parsing, then proofreading."""
    article = await self._ensure_article(item)

    # Step 1: Parse document
    parsing_success = await self._run_parsing(item)

    # Step 2: Only run proofreading if parsing succeeded
    if parsing_success:
        await self._run_proofreading(item, article)
    else:
        logger.info(
            "worklist_skipped_proofreading",
            worklist_id=item.id,
            reason="parsing_failed_or_needs_review"
        )
```

**Option B: Raise Exception (Alternative)**
```python
async def _run_parsing(self, item: WorklistItem) -> None:
    """Parse document content. Raises ParsingFailedError on failure."""
    try:
        raw_html = item.content
        parsing_result = self.parser_service.parse_document(raw_html)

        if not parsing_result.success:
            item.mark_status(WorklistStatus.PARSING)
            item.add_note({"message": "AI解析失败，需要手动审核", ...})
            self.session.add(item)
            raise ParsingFailedError("Parsing failed, needs manual review")

        # ... rest of success path ...

    except ParsingFailedError:
        raise  # Re-raise to caller
    except Exception as exc:
        item.mark_status(WorklistStatus.PARSING)
        item.add_note({"message": "解析过程异常", ...})
        self.session.add(item)
        raise ParsingFailedError(f"Parsing exception: {exc}") from exc

async def process_new_item(self, item: WorklistItem) -> None:
    article = await self._ensure_article(item)

    try:
        await self._run_parsing(item)
        # Only reached if parsing succeeded
        await self._run_proofreading(item, article)
    except ParsingFailedError as e:
        logger.info("worklist_parsing_failed", worklist_id=item.id, reason=str(e))
        # Don't run proofreading
```

**Recommendation**: Use **Option A (boolean return)** - simpler, more explicit

---

### Fix #2: Store and Use Raw HTML

**Strategy**: Store both raw HTML and cleaned text

#### Part 1: Update `WorklistItem` Model

```python
# backend/src/models/worklist.py
class WorklistItem(Base):
    __tablename__ = "worklist_items"

    content = Column(Text)  # Keep for backward compatibility (cleaned text)
    raw_html = Column(Text, nullable=True)  # NEW: Store original HTML
```

**Migration Required**:
```python
# alembic/versions/xxx_add_raw_html_to_worklist.py
def upgrade():
    op.add_column('worklist_items', sa.Column('raw_html', sa.Text(), nullable=True))

def downgrade():
    op.drop_column('worklist_items', 'raw_html')
```

#### Part 2: Update Sync Service to Store HTML

```python
# backend/src/services/google_drive/sync_service.py
async def _fetch_document(self, storage, file_id: str, file_metadata: dict) -> dict[str, Any] | None:
    mime_type = file_metadata.get("mimeType")

    if mime_type == "application/vnd.google-apps.document":
        # Export HTML
        html_content = await self._export_google_doc(storage, file_id, "text/html")

        # Parse and clean for backward compatibility
        content, parsing_status = self._parse_html_content(html_content)

        # Parse content with YAML front matter support
        file_name = file_metadata.get("name")
        parsed = self._parse_document_content(content, file_name=file_name)

        # ✅ NEW: Store raw HTML for parser
        parsed["raw_html"] = html_content

        parsed["drive_metadata"] = {
            "id": file_metadata.get("id"),
            "name": file_metadata.get("name"),
            "mimeType": mime_type,
            "webViewLink": file_metadata.get("webViewLink"),
            "createdTime": file_metadata.get("createdTime"),
        }
        return parsed
```

#### Part 3: Update Pipeline to Use Raw HTML

```python
# backend/src/services/worklist/pipeline.py
async def _run_parsing(self, item: WorklistItem) -> bool:
    """Parse document content to extract structured data."""
    try:
        # ✅ Use raw HTML if available, fallback to cleaned content
        raw_html = item.raw_html or item.content

        if not item.raw_html:
            logger.warning(
                "worklist_parsing_no_html",
                worklist_id=item.id,
                message="Using cleaned text as fallback (raw HTML not available)"
            )

        logger.info(
            "worklist_parsing_started",
            worklist_id=item.id,
            content_length=len(raw_html),
            has_raw_html=bool(item.raw_html),
        )

        # Parse with AI (will have images and structure now)
        parsing_result = self.parser_service.parse_document(raw_html)

        # ... rest of implementation ...
```

---

## 📊 Testing Strategy

### Test Fix #1: Parsing Failure Handling

```python
# tests/services/worklist/test_pipeline_parsing_failure.py
async def test_parsing_failure_stops_proofreading():
    """Verify proofreading doesn't run when parsing fails."""
    # Setup
    pipeline = WorklistPipeline(session, settings)
    item = WorklistItem(id=1, content="test", status=WorklistStatus.PENDING)

    # Mock parser to fail
    mock_parser.parse_document.return_value = ParseResult(
        success=False,
        errors=[ParseError(error_message="AI parsing failed")]
    )

    # Execute
    await pipeline.process_new_item(item)

    # Verify
    assert item.status == WorklistStatus.PARSING  # ✅ Stopped at parsing
    assert item.article.status == ArticleStatus.IMPORTED  # ✅ Not changed
    assert not mock_proofreader.called  # ✅ Proofreading not called

async def test_parsing_exception_stops_proofreading():
    """Verify proofreading doesn't run when parsing throws."""
    # Setup
    pipeline = WorklistPipeline(session, settings)
    item = WorklistItem(id=1, content="test", status=WorklistStatus.PENDING)

    # Mock parser to throw
    mock_parser.parse_document.side_effect = ValueError("Parser crashed")

    # Execute
    await pipeline.process_new_item(item)

    # Verify
    assert item.status == WorklistStatus.PARSING
    assert not mock_proofreader.called

async def test_parsing_success_continues_to_proofreading():
    """Verify proofreading runs when parsing succeeds."""
    # Setup
    pipeline = WorklistPipeline(session, settings)
    item = WorklistItem(id=1, content="test", status=WorklistStatus.PENDING)

    # Mock parser to succeed
    mock_parser.parse_document.return_value = ParseResult(
        success=True,
        parsed_article=ParsedArticle(author_name="Test", images=[...])
    )

    # Execute
    await pipeline.process_new_item(item)

    # Verify
    assert item.status == WorklistStatus.PARSING_REVIEW  # ✅ Parsing done
    # Note: In real flow, human reviews parsing before proofreading
    # This test would need to be adjusted based on workflow decision
```

### Test Fix #2: HTML Storage and Usage

```python
# tests/services/google_drive/test_sync_raw_html.py
async def test_sync_stores_raw_html():
    """Verify raw HTML is stored during sync."""
    # Setup
    mock_html = """
    <html>
        <h1>Test Title</h1>
        <img src="https://example.com/image.jpg">
        <p>Content</p>
    </html>
    """
    mock_storage.export.return_value = mock_html

    # Execute
    result = await sync_service._fetch_document(mock_storage, "file123", metadata)

    # Verify
    assert result["raw_html"] == mock_html  # ✅ HTML preserved
    assert "<img" not in result["content"]  # ✅ Cleaned text also stored

# tests/services/worklist/test_pipeline_html_parsing.py
async def test_parser_receives_html_with_images():
    """Verify parser gets HTML with image tags."""
    # Setup
    html_with_images = '<h1>Title</h1><img src="test.jpg"><p>Content</p>'
    item = WorklistItem(
        id=1,
        content="Title\nContent",  # Cleaned
        raw_html=html_with_images  # Raw HTML
    )

    # Execute
    await pipeline._run_parsing(item)

    # Verify
    mock_parser.parse_document.assert_called_with(html_with_images)  # ✅ Got HTML
    # Verify images were extracted
    assert len(item.drive_metadata["images"]) > 0

async def test_parser_fallback_to_content():
    """Verify parser falls back to cleaned content if no HTML."""
    # Setup
    item = WorklistItem(
        id=1,
        content="Title\nContent",
        raw_html=None  # No HTML available
    )

    # Execute
    await pipeline._run_parsing(item)

    # Verify
    mock_parser.parse_document.assert_called_with("Title\nContent")  # ✅ Used content
```

---

## 📋 Implementation Checklist

### Phase 1: Fix Parsing Failure Handling (1-2 hours)
- [ ] Update `_run_parsing` to return `bool`
- [ ] Update `process_new_item` to check return value
- [ ] Add logging for skipped proofreading
- [ ] Write unit tests (3 scenarios)
- [ ] Run existing tests to ensure no regression
- [ ] Manual testing with failing parser

### Phase 2: Add Raw HTML Storage (3-4 hours)
- [ ] Create Alembic migration for `raw_html` column
- [ ] Run migration on dev database
- [ ] Update `WorklistItem` model
- [ ] Update `sync_service._fetch_document` to store HTML
- [ ] Update `pipeline._run_parsing` to use raw HTML
- [ ] Add fallback logic for items without HTML
- [ ] Write integration tests
- [ ] Test with real Google Docs export

### Phase 3: Backfill Existing Items (Optional, 1-2 hours)
- [ ] Create script to re-sync items without `raw_html`
- [ ] Dry-run to verify backfill logic
- [ ] Execute backfill on production
- [ ] Monitor for errors

### Phase 4: Validation & Monitoring (1 hour)
- [ ] End-to-end test with real document
- [ ] Verify images are extracted correctly
- [ ] Add metrics for parsing success/failure rates
- [ ] Add alert for high parsing failure rate
- [ ] Update documentation

---

## 🎯 Expected Outcomes

### After Fix #1
✅ Parsing failures properly stop the pipeline
✅ Items stuck at `PARSING` status until manual review
✅ Proofreading only runs on successfully parsed items
✅ Operators see clear parsing failure messages
✅ No more masked failures

### After Fix #2
✅ Parser receives original HTML with images
✅ Images successfully extracted from documents
✅ Structural cues available for heuristic parsing
✅ AI prompting uses rich HTML context
✅ Parsing stage meets design requirements

---

## 🚨 Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Migration fails on production | Low | High | Test on staging first, have rollback plan |
| Backfill consumes too many Drive API quotas | Medium | Medium | Rate limit backfill script, run during off-hours |
| Raw HTML column increases DB size significantly | High | Low | HTML is text (compressible), monitor growth |
| Existing items without raw_html fail parsing | High | Medium | Implement fallback to cleaned content |
| Boolean return breaks other callers | Low | High | Check all callers of `_run_parsing` (none found) |

---

## 📚 References

**Issue #1 Analysis**:
- Code: `backend/src/services/worklist/pipeline.py:47-55, 94-210`
- Related: `backend/src/models/worklist.py` (WorklistStatus enum)

**Issue #2 Analysis**:
- Code: `backend/src/services/worklist/pipeline.py:94-109`
- Code: `backend/src/services/google_drive/sync_service.py:256-336, 353-379`
- Related: `backend/src/services/article_parser/service.py` (expects HTML)

---

**Analysis Completed**: 2025-11-12
**Analyst**: Claude (Anthropic) + Codex CLI
**Status**: ✅ Both issues confirmed and reproduction paths validated
**Priority**: 🔴 P1 - Both issues block parsing functionality
**Recommended Action**: Implement fixes in order (Fix #1 first, then Fix #2)
