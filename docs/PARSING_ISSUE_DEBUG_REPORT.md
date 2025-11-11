# Article Parsing Issue - Complete Debug Report

**Date**: 2025-11-11
**Reporter**: Claude Code
**Status**: 🔴 Unresolved (After 3 deployment attempts)

---

## Executive Summary

### The Problem
The Article Review Modal in Phase 8 displays empty **Author** and **Images** fields when reviewing Google Drive documents. Investigation revealed the backend was never extracting these fields from the raw HTML content.

### Root Causes Identified and Fixed
1. ✅ **Missing AI Parsing Integration** - Backend pipeline never called ArticleParserService
2. ✅ **Pgbouncer Prepared Statements** - Database connection error with Supabase pooler
3. ✅ **JSON Import Scope Error** - Variable reference before assignment in exception handler

### Current Status
Despite fixing 3 critical bugs and deploying 3 times, the parsing endpoint still returns HTTP 500 "Internal Server Error" with no detailed error logs visible in Cloud Run.

---

## Timeline of Investigation

### Initial Discovery (Session Start)

**User Report**:
> "打开文章审核的界面，没有上下的scroll的功能"
> "现在的刚打开模态框时里面的内容经过解析的吗？"

**Screenshot Analysis**:
- Author field: Empty
- Images section: No images displayed
- Raw content had both author info and image URLs

**Initial Hypothesis**: Frontend display issue or prompt problem

---

## Issue #1: Missing AI Parsing Integration

### Discovery Process

1. **Checked API Response** for worklist item ID 2:
   ```json
   {
     "id": 2,
     "author": null,
     "metadata": {
       "id": "1Hs-pv8kyGGIjYz3fOQrsTlYX_AwiZAysh8ELeh8dgsk",
       "name": "被蜱蟲咬了怎麼辦？警惕萊姆病的致命偽裝"
       // No "images" array
     },
     "content": "...<HTML with author '文 / Mercura Wang' and image URLs>..."
   }
   ```

2. **Checked ArticleParserService** - Exists at `/backend/src/services/parser/article_parser.py` with complete implementation

3. **Checked WorklistPipelineService** - Found the smoking gun:

**File**: `/backend/src/services/worklist/pipeline.py`

```python
async def process_new_item(self, item: WorklistItem) -> None:
    """Ensure article exists for the worklist item, run parsing, then proofreading."""
    article = await self._ensure_article(item)

    # ❌ MISSING: No parsing step!
    # Should call: await self._run_parsing(item)

    await self._run_proofreading(item, article)  # Only proofreading runs
```

**Root Cause**: The pipeline only ran proofreading, never parsing. The ArticleParserService existed but was never integrated.

### Solution Implemented

**Commit**: `f59ba7c` - "fix(backend): Add AI parsing step to extract author and images in worklist pipeline"

**Changes**:
1. Added `ArticleParserService` import
2. Initialized parser service in `__init__` with Anthropic API key
3. Created comprehensive `_run_parsing()` method (129 lines):
   - Calls `parser_service.parse_document(raw_html)`
   - Extracts author, images, SEO metadata, title components
   - Stores in worklist item fields and `metadata` JSON
   - Updates status to `PARSING_REVIEW`
   - Handles errors gracefully
4. Modified `process_new_item()` to call `_run_parsing()` before `_run_proofreading()`

**Code Added**:
```python
# In __init__
self.parser_service = parser_service or ArticleParserService(
    use_ai=True,
    anthropic_api_key=self.settings.ANTHROPIC_API_KEY,
)

# In process_new_item
async def process_new_item(self, item: WorklistItem) -> None:
    article = await self._ensure_article(item)

    # Step 1: Parse document to extract author, images, SEO, etc.
    await self._run_parsing(item)  # ✅ NEW

    # Step 2: Run proofreading
    await self._run_proofreading(item, article)

# New method (129 lines)
async def _run_parsing(self, item: WorklistItem) -> None:
    """Parse document content to extract structured data."""
    try:
        raw_html = item.content
        logger.info("worklist_parsing_started", worklist_id=item.id)

        parsing_result = self.parser_service.parse_document(raw_html)

        if not parsing_result.success:
            item.mark_status(WorklistStatus.PARSING)
            item.add_note({"message": "AI解析失败，需要手动审核", "level": "error"})
            return

        # Extract and store parsed data
        parsed_article = parsing_result.parsed_article
        item.author = parsed_article.author_name
        item.meta_description = parsed_article.meta_description
        item.seo_keywords = parsed_article.seo_keywords or []

        # Store images in metadata
        metadata = dict(item.drive_metadata or {})
        if parsed_article.images:
            metadata["images"] = [...]

        item.mark_status(WorklistStatus.PARSING_REVIEW)
        self.session.add(item)
    except Exception as exc:
        logger.error("worklist_parsing_exception", worklist_id=item.id, error=str(exc))
```

**Deployment**: ✅ Successful (revision cms-automation-backend-00040-t8j)

### Test Result
**Status**: ❌ Failed

**API Call**:
```bash
curl -X POST "https://cms-automation-backend-baau2zqeqq-ue.a.run.app/v1/worklist/2/trigger-proofreading"
```

**Response**: HTTP 200 (success), but data still null

**Verification**:
```json
{
  "id": 2,
  "author": null,  // Still null!
  "metadata": {
    "images": []   // Still empty!
  }
}
```

**Analysis**: Deployment succeeded but parsing didn't run. No parsing note in worklist item notes.

---

## Issue #2: Pgbouncer Prepared Statements Error

### Discovery Process

Triggered parsing again to observe behavior:

```bash
$ curl -X POST ".../v1/worklist/2/trigger-proofreading"
{
  "detail": "Proofreading failed: (sqlalchemy.dialects.postgresql.asyncpg.Error)
   <class 'asyncpg.exceptions.InvalidSQLStatementNameError'>:
   prepared statement \"__asyncpg_stmt_892__\" does not exist
   HINT: pgbouncer with pool_mode set to \"transaction\" or \"statement\"
   does not support prepared statements properly."
}
```

**Root Cause**: Supabase connection pooler (pgbouncer) in transaction mode doesn't support asyncpg's prepared statements.

**Why This Matters**:
- Every database operation was failing
- Transactions were rolling back
- No data could be saved
- This explained why author/images stayed null despite code running

### Solution Implemented

**Commit**: `7afab28` - "fix(backend): Disable prepared statements for pgbouncer compatibility"

**File**: `/backend/src/config/database.py`

**Change**:
```python
# BEFORE
engine_kwargs = {
    "echo": self.settings.LOG_LEVEL == "DEBUG",
    "pool_size": self.settings.DATABASE_POOL_SIZE,
    "max_overflow": self.settings.DATABASE_MAX_OVERFLOW,
    "pool_timeout": self.settings.DATABASE_POOL_TIMEOUT,
    "pool_recycle": self.settings.DATABASE_POOL_RECYCLE,
    "pool_pre_ping": True,
}

# AFTER
engine_kwargs = {
    "echo": self.settings.LOG_LEVEL == "DEBUG",
    "pool_size": self.settings.DATABASE_POOL_SIZE,
    "max_overflow": self.settings.DATABASE_MAX_OVERFLOW,
    "pool_timeout": self.settings.DATABASE_POOL_TIMEOUT,
    "pool_recycle": self.settings.DATABASE_POOL_RECYCLE,
    "pool_pre_ping": True,
    # ✅ NEW: Disable prepared statements for pgbouncer
    "connect_args": {"statement_cache_size": 0},
}
```

**Deployment**: ✅ Successful

### Test Result
**Status**: ⚠️ Partially Fixed

**API Call**: Same trigger-proofreading endpoint

**Response**: HTTP 200 ✅ (No more database error!)

**But**:
```json
{
  "notes": [
    {
      "level": "error",
      "message": "AI解析失败，需要手动审核"  // Parsing failed!
    }
  ]
}
```

**Analysis**: Database now works, but AI parsing is failing. Progress!

**Cloud Run Logs**:
```
2025-11-11T20:36:32 [INFO] worklist_parsing_started (worklist_id: 2)
2025-11-11T20:36:32 [INFO] Starting article parsing
2025-11-11T20:36:32 [INFO] Attempting AI-based parsing
2025-11-11T20:36:32 [INFO] Starting AI-based parsing with Claude
2025-11-11T20:36:32 [INFO] Unexpected error during parsing:
  cannot access local variable 'json' where it is not associated with a value
2025-11-11T20:36:32 [INFO] worklist_parsing_failed (worklist_id: 2)
```

---

## Issue #3: JSON Import Scope Error

### Discovery Process

**Error Message**: "cannot access local variable 'json' where it is not associated with a value"

**Location**: `ArticleParserService._parse_with_ai()` method

**File**: `/backend/src/services/parser/article_parser.py:126-250`

**Bug Analysis**:
```python
def _parse_with_ai(self, raw_html: str) -> ParsingResult:
    logger.info("Starting AI-based parsing with Claude")

    try:
        import anthropic
        # ... API call code ...
        response_text = message.content[0].text

        # ❌ PROBLEM: json imported INSIDE try block
        import json  # Line 175
        parsed_data = json.loads(response_text)

        # ... rest of parsing ...

    except json.JSONDecodeError as e:  # Line 212
        # ❌ If exception happens BEFORE line 175, json is undefined!
        logger.error(f"Failed to parse AI response as JSON: {e}")
```

**Root Cause**: Python variable scoping issue
- `import json` was inside the try block
- Exception handler `except json.JSONDecodeError` needed `json` to be defined
- If an exception occurred before line 175, `json` would be undefined
- This causes "cannot access local variable 'json'" error

### Solution Implemented

**Commit**: `d08df2c` - "fix(parser): Move json import to top of _parse_with_ai method"

**Change**:
```python
def _parse_with_ai(self, raw_html: str) -> ParsingResult:
    # ✅ FIXED: Move import to top of method
    import json

    logger.info("Starting AI-based parsing with Claude")

    try:
        import anthropic
        # ... rest remains the same ...

    except json.JSONDecodeError as e:  # Now json is always defined
        logger.error(f"Failed to parse AI response as JSON: {e}")
```

**Deployment**: ✅ Successful

### Test Result
**Status**: ❌ Still Failing

**API Call**: Same trigger-proofreading endpoint

**Response**: HTTP 500 "Internal Server Error"

**Response Body**:
```json
{
  "error": "Internal Server Error",
  "message": "An unexpected error occurred",
  "request_id": "0ba3b675-9cc8-47ca-b45d-b488bda0a89c"
}
```

**Cloud Run Logs**:
```
2025-11-11T20:44:50 [INFO] request_started
2025-11-11T20:44:50 [INFO] database_engine_created
2025-11-11T20:44:50 [INFO] database_session_factory_created
(no further logs...)
```

**Analysis**: No parsing logs, no error details visible. The error is being caught somewhere but not logged to Cloud Run.

---

## Summary of Attempts

### Deployment History

| # | Commit | Issue Fixed | Result | Status Code | Notes |
|---|--------|-------------|--------|-------------|-------|
| 1 | f59ba7c | Added parsing integration | ❌ Data still null | 200 | DB error prevented save |
| 2 | 7afab28 | Fixed pgbouncer | ⚠️ Parsing failed | 200 | json import error |
| 3 | d08df2c | Fixed json import | ❌ Still failing | 500 | No error logs |

### Key Observations

1. **Deployment Success ≠ Code Working**: All 3 deployments succeeded but functionality didn't work
2. **Error Masking**: Each fix revealed a deeper issue
3. **Log Visibility**: Cloud Run structured logs not showing detailed error traces
4. **Database Connection**: Fixed in deployment #2, but parsing logic has issues
5. **Missing Error Details**: Current 500 error has no stack trace in logs

---

## Technical Details

### Environment
- **Platform**: Google Cloud Run (us-east1)
- **Database**: Supabase PostgreSQL with pgbouncer pooler
- **Framework**: FastAPI + SQLAlchemy + asyncpg
- **AI Service**: Anthropic Claude API
- **Current Revision**: `cms-automation-backend-00042-xxx` (after deployment #3)

### File Locations
- Pipeline: `/backend/src/services/worklist/pipeline.py`
- Parser: `/backend/src/services/parser/article_parser.py`
- DB Config: `/backend/src/config/database.py`
- API Routes: `/backend/src/api/routes/worklist_routes.py`

### API Endpoint Used for Testing
```
POST /v1/worklist/{item_id}/trigger-proofreading
```

This endpoint calls:
```python
WorklistService.trigger_proofreading(item_id)
  → WorklistPipelineService.process_new_item(item)
    → _ensure_article(item)
    → _run_parsing(item)  # Where failures occur
    → _run_proofreading(item, article)
```

---

## Hypotheses for Current Failure

### Hypothesis 1: ANTHROPIC_API_KEY Not Configured ⭐ MOST LIKELY

**Evidence**:
- No API call logs visible
- Parser constructor: `ArticleParserService(anthropic_api_key=self.settings.ANTHROPIC_API_KEY)`
- If key is None or invalid, Anthropic client initialization might fail

**Check**:
```bash
gcloud secrets describe ANTHROPIC_API_KEY --project=cmsupload-476323
```

**Expected Behavior if Missing**:
- Constructor should succeed (key is optional parameter)
- First API call should fail with authentication error
- But we're getting generic 500 error

### Hypothesis 2: Exception Not Being Logged

**Evidence**:
- Only "request_started" appears in logs
- No "worklist_parsing_started" log (should appear on line 103 of pipeline.py)
- Suggests exception occurs BEFORE parsing logic runs

**Possible Causes**:
- Exception in `WorklistService.trigger_proofreading()` before pipeline call
- Exception in `WorklistPipelineService.__init__()` during parser_service creation
- Exception in database session creation

### Hypothesis 3: Import Error at Runtime

**Evidence**:
- `import anthropic` happens inside `_parse_with_ai()` method
- If anthropic package not installed in Docker image, would cause ImportError
- But deployment succeeded, suggesting dependency is present

**Check Needed**:
```bash
# In Docker container
pip list | grep anthropic
```

### Hypothesis 4: Memory/Timeout Issue

**Evidence**:
- Large HTML content (item.content)
- AI API call can take several seconds
- Cloud Run might have timeout/memory limits

**Check Needed**:
- Cloud Run service configuration
- Request timeout settings
- Memory allocation

---

## Data Points

### Worklist Item #2 Details
```json
{
  "id": 2,
  "title": "被蜱蟲咬了怎麼辦？警惕萊姆病的致命偽裝",
  "status": "proofreading_review",
  "author": null,
  "content": "<HTML with 11,790 bytes>",
  "drive_file_id": "1Hs-pv8kyGGIjYz3fOQrsTlYX_AwiZAysh8ELeh8dgsk",
  "metadata": {
    "id": "1Hs-pv8kyGGIjYz3fOQrsTlYX_AwiZAysh8ELeh8dgsk",
    "name": "被蜱蟲咬了怎麼辦？警惕萊姆病的致命偽裝",
    "mimeType": "application/vnd.google-apps.document"
  }
}
```

### Content Sample (from raw HTML)
```html
<p>文 / Mercura Wang 編譯 / 方海冬</p>
<!-- Author clearly present in HTML -->

<img src="https://lh7-rt.googleusercontent.com/..." />
<!-- Multiple images present in HTML -->
```

---

## Recommended Next Steps

### Immediate Actions (Ordered by Priority)

1. **Verify ANTHROPIC_API_KEY Secret** ⭐
   ```bash
   gcloud secrets versions access latest --secret=ANTHROPIC_API_KEY
   ```
   - Check if secret exists
   - Check if it's accessible by Cloud Run service account
   - Verify key is valid (not expired, has correct format)

2. **Check Cloud Run Service Configuration**
   ```bash
   gcloud run services describe cms-automation-backend --region=us-east1 --format=json
   ```
   - Verify environment variables are set
   - Check memory/CPU allocation
   - Check timeout settings

3. **Add Verbose Error Logging**

   Modify `WorklistService.trigger_proofreading()` to catch and log ALL exceptions:
   ```python
   async def trigger_proofreading(self, item_id: int) -> dict[str, Any]:
       try:
           # ... existing code ...
       except Exception as exc:
           logger.error(
               "DETAILED_ERROR",
               item_id=item_id,
               error_type=type(exc).__name__,
               error_message=str(exc),
               error_traceback=traceback.format_exc(),  # Full stack trace
               exc_info=True,
           )
           raise  # Re-raise to see in API response
   ```

4. **Test Simpler Endpoint**

   Create a dedicated parsing test endpoint that doesn't involve database:
   ```python
   @router.post("/test-parser")
   async def test_parser():
       parser = ArticleParserService(
           use_ai=True,
           anthropic_api_key=settings.ANTHROPIC_API_KEY
       )
       result = parser.parse_document("<html>Test content</html>")
       return {"success": result.success, "errors": result.errors}
   ```

5. **Check Dependencies in Deployed Image**
   ```bash
   # Get a shell in the running container
   gcloud run services exec cms-automation-backend --region=us-east1

   # Inside container
   pip list | grep anthropic
   python -c "import anthropic; print(anthropic.__version__)"
   ```

### Medium-Term Actions

6. **Add Health Check Endpoint**
   ```python
   @router.get("/health/parser")
   async def check_parser_health():
       try:
           parser = ArticleParserService(
               use_ai=True,
               anthropic_api_key=settings.ANTHROPIC_API_KEY
           )
           return {"status": "ok", "has_api_key": bool(settings.ANTHROPIC_API_KEY)}
       except Exception as e:
           return {"status": "error", "error": str(e)}
   ```

7. **Enable Debug Logging**

   Set `LOG_LEVEL=DEBUG` in Cloud Run environment variables to see all debug logs

8. **Test Locally with Production Database**
   ```bash
   # Set up local environment with production DB
   export DATABASE_URL="postgresql+asyncpg://..."
   export ANTHROPIC_API_KEY="..."

   # Run backend locally
   uvicorn main:app --reload

   # Test endpoint directly
   curl -X POST http://localhost:8000/v1/worklist/2/trigger-proofreading
   ```

### Long-Term Actions

9. **Improve Error Handling Architecture**
   - Add custom exception classes
   - Implement centralized error logging middleware
   - Add request ID tracing through all layers
   - Set up Sentry or similar error tracking

10. **Add Integration Tests**
    - Test parsing with real Google Docs HTML samples
    - Test database operations with test fixtures
    - Test API endpoints with various scenarios
    - Add CI/CD pipeline with automated testing

11. **Monitoring and Alerting**
    - Set up Cloud Monitoring alerts for 5xx errors
    - Add custom metrics for parsing success/failure rates
    - Track API call latencies
    - Monitor Anthropic API usage and costs

---

## Code References

### Files Modified

1. **frontend/src/components/ArticleReview/ArticleReviewModal.tsx** (uncommitted)
   - Fixed: Scroll overflow issue
   - Lines changed: 294-341

2. **backend/src/services/worklist/pipeline.py** (commit f59ba7c)
   - Added: _run_parsing() method (lines 94-210)
   - Added: ArticleParserService integration
   - Modified: process_new_item() to call parsing

3. **backend/src/config/database.py** (commit 7afab28)
   - Added: statement_cache_size=0 in connect_args (line 52)

4. **backend/src/services/parser/article_parser.py** (commit d08df2c)
   - Moved: `import json` to line 135 (top of method)

### Key Methods

- `WorklistPipelineService.process_new_item()` - Main workflow orchestration
- `WorklistPipelineService._run_parsing()` - NEW: Parsing logic (129 lines)
- `ArticleParserService.parse_document()` - AI-powered parsing
- `ArticleParserService._parse_with_ai()` - Claude API integration

---

## Lessons Learned

1. **Cascade of Errors**: Fixing one issue revealed the next. Chain: Missing parsing → DB error → JSON scope → Unknown error

2. **Database Pooling**: Supabase's pgbouncer requires `statement_cache_size=0` for asyncpg compatibility

3. **Import Placement**: Python imports inside try blocks can cause scope issues in exception handlers

4. **Log Visibility**: Cloud Run structured logs may not show all error details, especially for caught exceptions

5. **Testing in Production**: Need better local testing setup to catch these issues before deployment

6. **Error Masking**: Generic "Internal Server Error" responses hide root causes from debugging

---

## Questions for Further Investigation

1. **Why are detailed error logs not appearing in Cloud Run?**
   - Is there a log level filter?
   - Is FastAPI exception handler catching too broadly?
   - Are logs being written to stderr instead of stdout?

2. **Is ANTHROPIC_API_KEY properly configured?**
   - Does the secret exist?
   - Is it accessible to the service account?
   - Is the key valid and active?

3. **Why did deployment #1 return HTTP 200 with no database error?**
   - Was pgbouncer working intermittently?
   - Did we hit a cached connection?
   - Or was there a different code path?

4. **Can we reproduce this locally?**
   - Local uvicorn + production database
   - Would reveal if issue is environment-specific

5. **Are there Cloud Run resource constraints?**
   - Memory limits causing OOM?
   - CPU limits causing timeouts?
   - Request timeout too short for AI API calls?

---

## Conclusion

After 3 deployments and fixing 3 distinct bugs, the article parsing functionality still fails with an HTTP 500 error that provides no diagnostic information. The most likely cause at this point is a missing or invalid ANTHROPIC_API_KEY configuration, though other infrastructure issues (logging, timeouts, dependencies) cannot be ruled out.

**Recommendation**: Verify the ANTHROPIC_API_KEY secret configuration before attempting another deployment. If the key is configured correctly, add verbose error logging and test with a simpler endpoint to isolate the failure point.

**Time Invested**: ~2 hours of debugging across multiple layers (frontend, backend, database, parsing)

**Progress**: 3/4 major issues fixed, but core functionality still not working

**Next Session**: Should focus on verification steps #1-3 in the Recommended Actions section.
