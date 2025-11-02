# Feature Specification: SEO Optimization & Multi-Provider Computer Use Publishing

**Feature Branch**: `001-cms-automation`
**Created**: 2025-10-26
**Last Updated**: 2025-10-26
**Status**: In Development (Refactored Architecture)
**Input**: "Implement SEO optimization for existing articles and automated CMS publishing using flexible Computer Use providers (Anthropic/Gemini/Playwright) with browser automation."

## Overview

This feature provides an automated content management platform that optimizes existing articles for SEO and publishes them to WordPress CMS using flexible browser automation providers.

### Core Workflow

```
External Articles (Existing Content)
    ↓
[1] Article Import (CSV/JSON/Manual)
    ↓
[2] Proofreading & SEO Analysis
    ├─ Single Prompt (Claude Messages API)
    │   ├─ A–F 规则检查（返回 issue 列表 + rule_coverage）
    │   ├─ Suggested Content / Meta / Keywords / FAQ
    │   └─ Processing notes（ai_rationale, confidence）
    ├─ Deterministic Rule Engine (Python)
    │   ├─ F 类强制：图片宽度 / 标题层级 / 授权字段
    │   └─ 高置信度规则库（B2-002、A1-001 等，可扩展）
    └─ Result Merger
        ├─ 比对 AI vs Script，统一 schema（ProofreadingIssue）
        ├─ source_breakdown（ai/script/merged）
        └─ F 类阻断 → `critical_issues_count`
    ↓
[3] Human Review & Manual Adjustments (Optional)
    ↓
[4] CMS Publishing (Multi-Provider Computer Use)
    ├─ Provider Options:
    │   ├─ Anthropic Computer Use (AI-driven, adaptive)
    │   ├─ Gemini Computer Use (AI-driven, cost-effective)
    │   └─ Playwright (Traditional, reliable fallback)
    ├─ Browser Operations:
    │   ├─ WordPress Login
    │   ├─ Article Creation
    │   ├─ Content & Image Upload
    │   ├─ Yoast SEO / Rank Math Configuration
    │   └─ Publication & Verification
    └─ Screenshot Audit Trail (8+ steps)
    ↓
Published Article with SEO ✅
```

**Core Value Propositions**:
- **Batch SEO Optimization**: Process existing article libraries at scale
- **Multi-Provider Flexibility**: Switch between Anthropic/Gemini/Playwright providers
- **Cost-Effective**: Claude Messages API for SEO (~$0.02-0.05/article)
- **Reliable Publishing**: Computer Use automation with fallback options
- **Complete Audit Trail**: Screenshot verification at every step
- **Future-Proof Architecture**: Provider abstraction enables easy integration of new Computer Use APIs
- **Deterministic Guard Rails**: Scripted F 类校验防止 AI 幻觉遗漏关键合规项

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Article Import & Content Management (Priority: P0)

**As a** content manager
**I want to** batch import existing articles (from external writers, archives, or other sources)
**So that** I can feed them into the SEO optimization and publishing pipeline

**Why this priority**: This is the entry point for the entire system. Without article import, there is no content to optimize or publish. This is the foundational capability that enables all downstream features.

**Independent Test**: Upload a CSV file containing 100 articles with various formats (HTML, Markdown, plain text) and verify all are correctly imported, validated, and stored with proper data integrity.

**Acceptance Scenarios**:

1. **Given** a content manager has a CSV file with 100 existing articles
   **When** they upload the file through the import API/interface
   **Then** all 100 articles are imported within 5 minutes with:
   - Validation of required fields (title, content)
   - HTML sanitization (prevent XSS)
   - Image URL extraction and validation
   - Status set to `imported`
   - Source tracking metadata

2. **Given** an article contains 5 image URLs
   **When** the import process runs
   **Then** all image references are:
   - Validated for accessibility
   - Stored in `article_metadata.images` JSONB field
   - Downloaded to local storage (optional)
   - Ready for Computer Use upload

3. **Given** imported content contains malicious HTML (`<script>` tags, `onclick` attributes)
   **When** the sanitization process runs
   **Then** all dangerous HTML is stripped while preserving safe formatting (headings, paragraphs, lists, links, images)

4. **Given** a manually entered article (via UI form)
   **When** submitted
   **Then** the article is validated, saved to database, and status set to `imported`

5. **Given** duplicate detection is enabled
   **When** importing an article with 85%+ title similarity to an existing one
   **Then** the system displays a warning and requires user confirmation before proceeding

**Dependencies**: None (foundational feature)

---

### User Story 2 - Intelligent SEO Analysis & Metadata Generation (Priority: P0)

**As a** content manager
**I want to** automatically analyze articles and generate SEO-optimized metadata
**So that** my articles rank higher in search engines without manual SEO work

**Why this priority**: This is the core value proposition of the system. SEO optimization directly impacts search visibility, organic traffic, and business outcomes. This must work reliably before publishing.

**Independent Test**: Analyze 20 test articles and compare generated SEO metadata against expert-written benchmarks. Verify 85%+ keyword accuracy and proper character length constraints.

**Acceptance Scenarios**:

1. **Given** an imported article with 1500 words
   **When** SEO analysis is triggered (via API or UI)
   **Then** within 30 seconds the system generates:
   - SEO Title: 50-60 characters, includes focus keyword
   - Meta Description: 150-160 characters, compelling call-to-action
   - Focus Keyword: 1 primary keyword (highest relevance)
   - Primary Keywords: 3-5 semantically related keywords
   - Secondary Keywords: 5-10 long-tail variations
   - Keyword Density: JSONB map of {keyword: percentage}
   - Readability Score: Flesch-Kincaid grade level (target: 8-10)
   - Optimization Recommendations: Array of actionable suggestions

2. **Given** 20 test articles analyzed by the system
   **When** compared to SEO metadata written by qualified SEO experts
   **Then** the system achieves:
   - 85%+ accuracy on keyword extraction
   - 90%+ compliance with character length limits
   - 80%+ relevance score for generated meta descriptions

3. **Given** a generated SEO title is 70 characters (exceeds limit)
   **When** validation runs
   **Then** the system:
   - Automatically truncates to 60 characters at word boundary
   - Adds warning to `optimization_recommendations`
   - Logs the issue for review

4. **Given** SEO analysis completes successfully
   **When** results are saved
   **Then** all metadata is stored in `seo_metadata` table with:
   - Foreign key to `articles.id`
   - Generation timestamp
   - Claude API cost tracking
   - Token usage metrics

5. **Given** a content manager reviews auto-generated SEO metadata
   **When** they manually edit the SEO title or description
   **Then** changes are:
   - Saved to `seo_metadata` table
   - Tracked in `manual_overrides` JSONB field with timestamp
   - Used in final publishing (overrides AI-generated values)

**Dependencies**: User Story 1 (requires articles to analyze)

---

### User Story 3 - Multi-Provider Computer Use Publishing (Priority: P0)

**As a** content manager
**I want to** publish articles to WordPress using flexible automation providers (Anthropic/Gemini/Playwright)
**So that** I can choose the best balance of cost, reliability, and adaptability for my use case

**Why this priority**: This is the core technical innovation. Multi-provider architecture ensures we're not locked into a single vendor and can optimize for cost/performance based on testing results.

**Independent Test**: Execute full publishing workflow using each provider (Anthropic, Gemini, Playwright) on test WordPress instance. Verify all steps complete successfully with screenshot evidence.

**Acceptance Scenarios**:

1. **Given** an article with SEO metadata ready for publishing
   **And** the system is configured to use Anthropic Computer Use provider
   **When** a publish task is submitted
   **Then** within 5 minutes the system:
   - Opens Chrome browser (headless)
   - Navigates to WordPress admin panel
   - Logs in with provided credentials
   - Creates new post
   - Fills title and content
   - Uploads images (if any)
   - Configures Yoast SEO fields:
     - SEO Title (from `seo_metadata.meta_title`)
     - Meta Description (from `seo_metadata.meta_description`)
     - Focus Keyphrase (from `seo_metadata.focus_keyword`)
   - Sets categories and tags
   - Clicks "Publish" button
   - Verifies publication success
   - Extracts published article URL
   - Takes 8+ screenshots documenting each step

2. **Given** the system is configured to use Gemini Computer Use provider
   **When** the same publish task is executed
   **Then** the publishing workflow completes successfully using Gemini's Computer Use API with equivalent results

3. **Given** the system is configured to use Playwright provider (fallback)
   **When** the same publish task is executed
   **Then** the traditional browser automation completes successfully using pre-defined selectors

4. **Given** a Computer Use publish task fails (e.g., login error)
   **When** the failure is detected
   **Then** the system:
   - Marks task status as `failed`
   - Records error message in `publish_tasks.error_message`
   - Saves screenshot of failure state
   - Retries up to 3 times (configurable)
   - If still failing, notifies user via webhook/email

5. **Given** WordPress UI has changed (e.g., plugin update)
   **And** Playwright provider fails due to outdated selectors
   **When** automatic fallback is enabled
   **Then** the system:
   - Detects Playwright failure
   - Automatically retries with Anthropic provider (AI-adaptive)
   - Logs the fallback event for analysis

6. **Given** a publish task with 5 images
   **When** Computer Use executes image upload
   **Then** all 5 images are:
   - Uploaded to WordPress media library
   - Set as featured image (first image) or inserted inline (remaining)
   - Verified via screenshot

**Dependencies**: User Story 2 (requires SEO metadata)

---

### User Story 4 - Publishing Task Monitoring & Audit Trail (Priority: P1)

**As a** content manager
**I want to** monitor real-time publishing task status and review execution screenshots
**So that** I can verify quality, debug failures, and maintain compliance audit records

**Why this priority**: Observability is critical for production reliability. Screenshot audit trail provides accountability and debugging capability that's essential for Computer Use automation.

**Independent Test**: Submit 10 publishing tasks and verify task status API returns accurate real-time progress and all screenshots are accessible.

**Acceptance Scenarios**:

1. **Given** a Computer Use publish task is running
   **When** the user queries task status via API
   **Then** the response includes:
   - Current status: `pending`, `running`, `completed`, `failed`
   - Current step description (e.g., "Uploading images...")
   - Progress percentage (based on step count)
   - Elapsed time (seconds)
   - Estimated remaining time

2. **Given** a publish task completes successfully
   **When** the user views task details
   **Then** the system displays:
   - 8+ screenshots in chronological order:
     - `login_success.png`
     - `editor_loaded.png`
     - `content_filled.png`
     - `images_uploaded.png`
     - `seo_fields_filled.png`
     - `categories_set.png`
     - `publish_clicked.png`
     - `article_live.png`
   - Execution logs with timestamps
   - Final article URL
   - Total execution time

3. **Given** a publish task fails at step 5 (SEO fields)
   **When** the user reviews the task
   **Then** the system shows:
   - Screenshot of the failure state
   - Error message explaining the issue
   - Logs leading up to the failure
   - Retry history (if applicable)

4. **Given** compliance requirements mandate 90-day audit retention
   **When** screenshots and logs are stored
   **Then** all artifacts are:
   - Stored in S3 or local filesystem with 90-day retention policy
   - Accessible via API with task_id
   - Include metadata: timestamp, provider used, user who initiated

**Dependencies**: User Story 3 (requires publishing tasks)

---

### User Story 5 - Provider Performance Comparison & Cost Tracking (Priority: P2)

**As a** system administrator
**I want to** compare performance metrics and costs across different Computer Use providers
**So that** I can optimize for the best balance of reliability, speed, and cost

**Why this priority**: Important for long-term optimization but not blocking initial deployment. Enables data-driven provider selection.

**Independent Test**: Run 50 publish tasks with each provider and verify cost/performance metrics are accurately tracked and queryable.

**Acceptance Scenarios**:

1. **Given** 50 articles published using Anthropic provider
   **And** 50 articles published using Gemini provider
   **And** 50 articles published using Playwright provider
   **When** administrator queries performance metrics API
   **Then** the system returns comparison data:
   - Success rate (% of tasks completed)
   - Average execution time (seconds)
   - Average cost per article (USD)
   - Failure modes breakdown
   - Screenshots per task (quality metric)

2. **Given** cost tracking is enabled
   **When** a Computer Use task completes
   **Then** the estimated cost is calculated and stored:
   - Anthropic: Based on Computer Use API pricing
   - Gemini: Based on Gemini API pricing
   - Playwright: $0.00 (no API cost)
   - Stored in `publish_tasks.cost_usd` field

3. **Given** historical performance data
   **When** administrator views provider comparison dashboard
   **Then** the UI displays:
   - Side-by-side metrics table
   - Cost trend chart over time
   - Recommendations based on usage patterns

**Dependencies**: User Story 3 (requires multiple provider executions)

---

### User Story 6 - Proofreading Feedback & Training Loop (Priority: P0) ⭐新增

**As a** language quality lead  
**I want to** capture用户对校对/SEO/TAG 建议的接受或拒绝，并跟踪是否用于后续脚本/Prompt 调优  
**So that** 我们可以基于真实反馈迭代规则脚本和 AI Prompt，持续提高建议质量

**Why this priority**: Feedback 数据是闭环优化的核心，缺少真实决策和使用状态无法指导下一轮模型/脚本升级。上线即需可用。

**Independent Test**: 对 5 篇文章执行建议决策（接受/拒绝/部分采纳），生成反馈调优导出任务，验证 pending → completed 状态流转、反馈记录与仪表盘统计。

**Acceptance Scenarios**:

1. **Given** ProofreadingAnalysisService 已生成建议  
   **When** 用户在 UI 点击“接受”或“拒绝”或“部分采纳”  
   **Then** 系统记录 `proofreading_decisions` 条目，字段包含：suggestion_id、suggestion_type、rule_id、original_text、suggested_text、final_text、decision、feedback、feedback_status='pending'。

2. **Given** 用户拒绝或部分采纳建议  
   **When** UI 弹出反馈面板  
   **Then** 用户可以选择预设原因（多选）或填写自定义说明（可选），前端提交批量决策时一并保存。

3. **Given** 反馈调优导出 worker 每 10 分钟运行  
   **When** worker 获取 `feedback_status='pending'` 的决策  
   **Then** 它会标记记录为 `in_progress`，成功写入调优素材（供人工分析脚本/Prompt）后更新 `feedback_status='completed'`、记录 `tuning_batch_id`、`prompt_or_rule_version`、`feedback_processed_at`；失败时标记 `failed` 并写错误信息。

4. **Given** 运营需要查看反馈使用情况  
   **When** 访问反馈调优监控 API/仪表盘  
   **Then** 可看到 pending/in_progress/completed/failed 数量、Prompt/规则版本统计、支持按时间/类型过滤；`proofreading_history` 汇总字段同步更新。

5. **Given** 某条决策调优失败  
   **When** 运营通过 `PATCH /proofreading/decisions/{id}/feedback-status` 将其重置为 `pending`  
   **Then** 系统记录操作人与原因，并允许 worker 再次处理。

**Dependencies**: User Story 2 (需要校对/SEO 建议输出), User Story 4 (监控与审计基础)

---

## Requirements *(mandatory)*

### Functional Requirements

#### Article Management (FR-001 to FR-008)

- **FR-001**: System MUST support single article import via API (POST /v1/articles/import) with fields: title, content, excerpt, category, tags, images
- **FR-002**: System MUST support batch article import via CSV/JSON file upload (max 500 articles per batch)
- **FR-003**: System MUST validate article content for:
  - Required fields: title (min 10 chars), content (min 100 chars)
  - HTML sanitization (strip `<script>`, `onclick`, `onerror`, etc.)
  - Image URL validation (HTTP 200 status check)
- **FR-004**: System MUST support article image upload (featured + up to 10 additional images, max 5MB each, formats: JPG, PNG, GIF, WebP)
- **FR-005**: System MUST preserve article formatting (HTML or Markdown)
- **FR-006**: System MUST track article source (`imported`, `manual_entry`) in metadata
- **FR-007**: System MUST detect duplicate articles (85%+ title similarity) and alert user before import
- **FR-008**: System MUST store article metadata (author, source URL, import date, custom fields) in JSONB field

#### SEO Optimization (FR-009 to FR-019)

- **FR-009**: System MUST analyze article content and extract keywords using TF-IDF and semantic analysis
- **FR-010**: System MUST generate SEO-optimized title (50-60 characters, includes focus keyword)
- **FR-011**: System MUST generate Meta description (150-160 characters, compelling and actionable)
- **FR-012**: System MUST identify 1 focus keyword (highest relevance score)
- **FR-013**: System MUST identify 3-5 primary keywords (semantically related to focus)
- **FR-014**: System MUST identify 5-10 secondary keywords (long-tail variations)
- **FR-015**: System MUST calculate keyword density for all identified keywords (target: 0.5%-3%)
- **FR-016**: System MUST calculate readability score using Flesch-Kincaid formula (target: grade 8-10)
- **FR-017**: System MUST generate optimization recommendations (array of actionable suggestions)
- **FR-018**: System MUST allow manual editing of all SEO metadata fields
- **FR-019**: System MUST track manual overrides with timestamp and user ID

#### Multi-Provider Computer Use Publishing (FR-020 to FR-036)

- **FR-020**: System MUST support 3 Computer Use providers: Anthropic, Gemini, Playwright
- **FR-021**: System MUST allow provider selection via:
  - Environment variable (`COMPUTER_USE_PROVIDER=anthropic|gemini|playwright`)
  - API request parameter (`?provider=anthropic`)
  - Per-article configuration
- **FR-022**: System MUST implement abstract `ComputerUseProvider` base class with methods:
  - `execute(instructions, context) -> ExecutionResult`
  - `navigate(url) -> ExecutionStep`
  - `type_text(selector, text) -> ExecutionStep`
  - `click(selector) -> ExecutionStep`
  - `upload_file(selector, file_path) -> ExecutionStep`
  - `screenshot(name) -> str`
  - `cleanup() -> None`
- **FR-023**: System MUST implement `ProviderFactory` for dynamic provider instantiation
- **FR-024**: System MUST implement Anthropic Computer Use provider using `claude-3-5-sonnet-20241022` model with `computer_20241022` tool
- **FR-025**: System MUST implement Gemini Computer Use provider using `gemini-2.0-flash-exp` model (when available)
- **FR-026**: System MUST implement Playwright provider using CSS selectors for WordPress UI elements
- **FR-027**: System MUST perform the following operations via Computer Use:
  - Navigate to WordPress admin panel
  - Login with credentials (username + password or application password)
  - Create new post
  - Fill title and content (WYSIWYG editor)
  - Upload images to media library
  - Set featured image
  - Configure Yoast SEO OR Rank Math fields:
    - SEO Title
    - Meta Description
    - Focus Keyphrase
  - Set categories and tags
  - Click "Publish" button
  - Wait for publication confirmation
  - Extract published article URL
- **FR-028**: System MUST take screenshots at minimum 8 steps:
  - Login success
  - Editor loaded
  - Content filled
  - Images uploaded
  - SEO fields configured
  - Categories set
  - Publish button clicked
  - Article live verification
- **FR-029**: System MUST store screenshots in:
  - Local filesystem (`/app/screenshots/{task_id}/`) for development
  - S3 or object storage for production
- **FR-030**: System MUST save screenshot paths to `publish_tasks.screenshots` JSONB field
- **FR-031**: System MUST retry failed operations up to 3 times with exponential backoff (2s, 4s, 8s)
- **FR-032**: System MUST distinguish between recoverable errors (network timeout, UI loading delay) and fatal errors (invalid credentials, missing plugin)
- **FR-033**: System MUST record all Computer Use operations to `execution_logs` table with:
  - log_level, step_name, message, details (JSONB)
  - action_type, action_target, action_result
  - screenshot_path, timestamp
- **FR-034**: System MUST support automatic provider fallback: If Playwright fails → retry with Anthropic
- **FR-035**: System MUST extract and save published article URL to `articles.published_url`
- **FR-036**: System MUST extract and save CMS article ID to `articles.cms_article_id`

#### Error Handling & Monitoring (FR-037 to FR-045)

- **FR-037**: System MUST log all errors to `publish_tasks.error_message` with detailed context
- **FR-038**: System MUST capture screenshot on error for debugging
- **FR-039**: System MUST update task status in real-time: `pending` → `running` → `completed|failed`
- **FR-040**: System MUST calculate and store task execution duration in `publish_tasks.duration_seconds`
- **FR-041**: System MUST provide task status query API (GET /v1/publish/tasks/{task_id}/status)
- **FR-042**: System MUST provide screenshot retrieval API (GET /v1/publish/tasks/{task_id}/screenshots)
- **FR-043**: System MUST record all CMS login attempts to `audit_logs` table for security compliance
- **FR-044**: System MUST track API costs for Anthropic and Gemini providers in `publish_tasks.cost_usd`
- **FR-045**: System MUST send webhook notification on task completion (success or failure)

#### Frontend UI/UX Requirements (FR-046 to FR-070)

**Status**: 🔴 Critical Gap Identified (2025-10-27)
**Reference**: See [UI Gaps Analysis](../../docs/UI_GAPS_ANALYSIS.md) and [UI Implementation Tasks](./UI_IMPLEMENTATION_TASKS.md)

**Overview**: The following UI requirements are currently **not implemented** (0% complete). Implementation is required to enable end-to-end user workflows.

##### Article Import UI (FR-046 to FR-052)

- **FR-046**: System MUST provide a web UI for CSV file upload with drag-and-drop support (max 500 articles, 10MB)
- **FR-047**: System MUST provide a web UI for JSON file upload with schema validation
- **FR-048**: System MUST provide a manual article entry form with rich text editor (TipTap or Quill)
- **FR-049**: System MUST provide image upload widget supporting featured image (1 required) and additional images (max 10, 5MB each)
- **FR-050**: System MUST display real-time validation errors with row number, field name, and error message
- **FR-051**: System MUST show batch import progress indicator (X/Y articles processed)
- **FR-052**: System MUST provide downloadable CSV template with correct column headers

##### SEO Optimization UI (FR-053 to FR-060)

- **FR-053**: System MUST provide SEO optimizer panel displaying AI-generated metadata with edit capability
- **FR-054**: System MUST provide Meta Title editor with real-time character counter (50-60 chars, color-coded validation)
- **FR-055**: System MUST provide Meta Description editor with character counter (150-160 chars)
- **FR-056**: System MUST provide keyword editor supporting Focus (1), Primary (3-5), and Secondary (5-10) keywords with tag-based UI
- **FR-057**: System MUST visualize keyword density using bar chart (Recharts) with reference lines at 0.5% and 3%
- **FR-058**: System MUST display readability score using gauge chart (Flesch-Kincaid Grade Level, target 8-10)
- **FR-059**: System MUST display optimization recommendations as bulleted list with icons
- **FR-060**: System MUST provide "Re-analyze SEO" button to trigger new analysis and "Save" button to persist manual edits

##### Multi-Provider Publishing UI (FR-061 to FR-065)

- **FR-061**: System MUST provide publish button with dropdown to select provider (Anthropic/Gemini/Playwright) showing cost and duration estimates
- **FR-062**: System MUST show confirmation dialog before publishing, displaying article title, selected provider, estimated cost, and estimated time
- **FR-063**: System MUST display real-time publish progress modal polling task status every 2 seconds with progress bar, current step description, and elapsed/estimated time
- **FR-064**: System MUST display screenshot gallery in 3-column grid layout with lightbox viewer for full-size images
- **FR-065**: System MUST display publish success card with article URL, duration, and screenshot count OR error card with error message and failure screenshot

##### Task Monitoring UI (FR-066 to FR-068)

- **FR-066**: System MUST provide task list page with table showing article title, provider, status badge (color-coded), duration, cost, and "View Details" button
- **FR-067**: System MUST provide task detail drawer showing full execution logs, 8+ screenshots with timestamps, and final result (success URL or error)
- **FR-068**: System MUST provide task filters by status (pending/running/completed/failed) and provider with pagination (20 items per page)

##### Provider Comparison Dashboard (FR-069 to FR-070)

- **FR-069**: System MUST provide provider comparison page with metrics table (success rate, avg duration, avg cost, total tasks) highlighting best values in green
- **FR-070**: System MUST visualize provider performance using line chart (success rate over time), bar chart (cost comparison), and pie chart (task distribution)

**Implementation Priority**: P0 (Critical) - Blocks end-to-end user workflow
**Estimated Effort**: 312 hours (6 weeks with 2 frontend engineers + 1 backend engineer)
**Current Status**: 0% complete (analysis phase completed 2025-10-27)

---

#### Google Drive Automation & Worklist (FR-071 to FR-087) 🆕

**Status**: 🆕 New Requirements Added (2025-10-27)
**Reference**: See [Google Drive Automation Analysis](../../docs/GOOGLE_DRIVE_AUTOMATION_ANALYSIS.md)

**Overview**: The following requirements add automated document ingestion from Google Drive and a comprehensive worklist UI for tracking document processing status.

##### Google Drive Integration (FR-071 to FR-075)

- **FR-071**: System MUST integrate with Google Drive API using OAuth 2.0 or Service Account for authentication
- **FR-072**: System MUST periodically scan a configured Google Drive folder for new Google Docs (default: every 5 minutes, configurable 1-60 minutes)
- **FR-073**: System MUST automatically read Google Doc content including text formatting and image references
- **FR-074**: System MUST mark processed documents by moving to "Processed" subfolder OR adding metadata tag to prevent duplicate processing
- **FR-075**: System MUST handle Google Drive API errors with retry logic (exponential backoff) and credential refresh for expired tokens

##### Worklist UI (FR-076 to FR-083)

- **FR-076**: System MUST provide a Worklist page (`/worklist`) displaying all documents in the processing pipeline
- **FR-077**: Worklist MUST display document metadata: title, source (Google Drive filename), creation time, current status, assigned user
- **FR-078**: Worklist MUST support 7 document statuses with visual indicators:
  - **Pending** ⏳ (imported, awaiting proofreading)
  - **Proofreading** 🟡 (AI analysis in progress)
  - **Under Review** 🔵 (awaiting human review)
  - **Ready to Publish** 🟢 (confirmed, awaiting publication)
  - **Publishing** 🔄 (publishing to WordPress in progress)
  - **Published** ✅ (successfully published)
  - **Failed** ❌ (processing failed with error details)
- **FR-079**: Worklist MUST support filtering by status, date range, and keyword search (title/content)
- **FR-080**: Worklist MUST support sorting by creation time (default: newest first), update time, and status
- **FR-081**: Clicking a document in Worklist MUST open detail view showing: full content, status history, operation logs, and action buttons
- **FR-082**: Worklist MUST update in real-time using WebSocket OR polling (every 5 seconds) to reflect status changes and new documents
- **FR-083**: Worklist MUST support batch operations: delete multiple, retry failed, mark as pending

##### Status Tracking & History (FR-084 to FR-087)

- **FR-084**: System MUST record all document status transitions to `article_status_history` table with timestamp, old status, new status, and operator (user or system)
- **FR-085**: System MUST log all document operations (who did what, when, with what result) for audit trail
- **FR-086**: System MUST support status rollback: if publishing fails, automatically revert to "Ready to Publish" status with error context preserved
- **FR-087**: System MUST calculate and display processing duration metrics: per-stage duration, total duration (import to publish), and average duration statistics

**Implementation Priority**: P0 (Critical) - Core automation feature
**Estimated Effort**: 200 hours (5 weeks with 1 frontend engineer + 1 backend engineer)
**Dependencies**: Requires FR-046 to FR-070 (base UI) to be implemented first

---

### Non-Functional Requirements

#### Performance (NFR-001 to NFR-006)

- **NFR-001**: SEO analysis MUST complete within 30 seconds (95th percentile)
- **NFR-002**: Computer Use publish task MUST complete within 5 minutes (95th percentile)
- **NFR-003**: Article import (batch 100 articles) MUST complete within 5 minutes
- **NFR-004**: System MUST support 5 concurrent Computer Use publishing tasks without performance degradation
- **NFR-005**: Screenshot storage MUST NOT exceed 10MB per task
- **NFR-006**: Database queries MUST return within 500ms for article/SEO metadata retrieval

#### Reliability (NFR-007 to NFR-012)

- **NFR-007**: Computer Use publishing success rate MUST be ≥90% (target: 95%)
- **NFR-008**: SEO analysis accuracy (vs expert benchmark) MUST be ≥85%
- **NFR-009**: System MUST handle WordPress plugin updates gracefully (AI providers auto-adapt, Playwright requires selector updates)
- **NFR-010**: System MUST recover from network interruptions with retry logic
- **NFR-011**: Screenshot capture MUST succeed for 100% of publish tasks
- **NFR-012**: Celery workers MUST auto-restart on crash

#### Security (NFR-013 to NFR-020)

- **NFR-013**: CMS credentials MUST be stored in encrypted secrets manager (AWS Secrets Manager or HashiCorp Vault)
- **NFR-014**: CMS credentials MUST NOT appear in logs or screenshots
- **NFR-015**: API endpoints MUST require JWT authentication (15-min expiration, 7-day refresh)
- **NFR-016**: Rate limiting MUST be enforced: 100 requests/minute per API key
- **NFR-017**: All imported HTML MUST be sanitized to prevent XSS attacks
- **NFR-018**: All Computer Use operations MUST be logged to audit trail
- **NFR-019**: Screenshot storage MUST have 90-day retention policy with automatic deletion
- **NFR-020**: Database connections MUST use SSL/TLS encryption

#### Scalability (NFR-021 to NFR-024)

- **NFR-021**: System MUST support 1,000 articles in database without query performance degradation
- **NFR-022**: System MUST support 100 concurrent SEO analysis tasks (via Celery horizontal scaling)
- **NFR-023**: Screenshot storage MUST scale to support 10,000 tasks (S3 or equivalent)
- **NFR-024**: System MUST support multi-region deployment for global availability

#### Observability (NFR-025 to NFR-029)

- **NFR-025**: All API requests MUST be logged with request ID, duration, status code
- **NFR-026**: All Celery tasks MUST emit metrics: start time, end time, success/failure
- **NFR-027**: System MUST expose Prometheus metrics for monitoring
- **NFR-028**: System MUST integrate with Sentry or equivalent for error tracking
- **NFR-029**: Screenshots MUST be viewable via admin UI for debugging

#### Cost Efficiency (NFR-030 to NFR-032)

- **NFR-030**: SEO analysis cost MUST NOT exceed $0.10 per article
- **NFR-031**: Computer Use publishing cost MUST NOT exceed $1.50 per article (Anthropic), $1.00 (Gemini), $0.00 (Playwright)
- **NFR-032**: System MUST track and report monthly API costs by provider

---

## Key Entities

### Articles
- `id`: Primary key
- `title`: Article title (VARCHAR 500)
- `content`: Article body (TEXT)
- `excerpt`: Short summary (TEXT, optional)
- `category`: Article category (VARCHAR 100)
- `tags`: Article tags (TEXT[], array)
- `status`: Article status (`imported`, `seo_optimized`, `ready_to_publish`, `publishing`, `published`)
- `source`: Content source (`imported`, `manual_entry`)
- `featured_image_path`: Featured image path (VARCHAR 500)
- `additional_images`: Additional images (JSONB array)
- `published_url`: Published article URL (VARCHAR 500)
- `cms_article_id`: WordPress post ID (VARCHAR 100)
- `article_metadata`: Custom metadata (JSONB)
- `created_at`, `updated_at`, `published_at`: Timestamps

### SEO Metadata
- `id`: Primary key
- `article_id`: Foreign key to articles (UNIQUE)
- `meta_title`: SEO-optimized title (VARCHAR 60)
- `meta_description`: Meta description (VARCHAR 160)
- `focus_keyword`: Primary keyword (VARCHAR 100)
- `primary_keywords`: Primary keywords (TEXT[] array, 3-5 items)
- `secondary_keywords`: Secondary keywords (TEXT[] array, 5-10 items)
- `keyword_density`: Keyword density map (JSONB)
- `readability_score`: Flesch-Kincaid score (FLOAT)
- `optimization_recommendations`: Suggestions (JSONB array)
- `manual_overrides`: User edits (JSONB with timestamps)
- `generated_by`: AI model used (VARCHAR 50)
- `generation_cost`: API cost (DECIMAL)
- `generation_tokens`: Token usage (INTEGER)
- `created_at`, `updated_at`: Timestamps

### Publish Tasks
- `id`: Primary key
- `article_id`: Foreign key to articles
- `task_id`: Celery task ID (VARCHAR 100, UNIQUE)
- `provider`: Computer Use provider (`anthropic`, `gemini`, `playwright`)
- `cms_type`: CMS type (`wordpress`, future: `strapi`, `ghost`)
- `cms_url`: WordPress URL (VARCHAR 500)
- `status`: Task status (`pending`, `running`, `completed`, `failed`)
- `retry_count`: Number of retries (INTEGER, default 0)
- `max_retries`: Max retry attempts (INTEGER, default 3)
- `error_message`: Error details (TEXT)
- `session_id`: Computer Use session ID (VARCHAR 100)
- `screenshots`: Screenshot paths (JSONB array)
- `cost_usd`: Estimated API cost (DECIMAL)
- `started_at`, `completed_at`: Timestamps
- `duration_seconds`: Execution time (INTEGER)
- `created_at`, `updated_at`: Timestamps

### Execution Logs
- `id`: Primary key
- `task_id`: Foreign key to publish_tasks
- `log_level`: Log level (`DEBUG`, `INFO`, `WARNING`, `ERROR`)
- `step_name`: Step description (VARCHAR 100)
- `message`: Log message (TEXT)
- `details`: Additional details (JSONB)
- `action_type`: Computer Use action (`navigate`, `click`, `type`, `upload`, `screenshot`)
- `action_target`: Target element (VARCHAR 200)
- `action_result`: Result status (`success`, `failed`, `timeout`)
- `screenshot_path`: Screenshot path (VARCHAR 500)
- `created_at`: Timestamp

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: SEO analysis completes in ≤30 seconds for 95% of articles
- **SC-002**: SEO keyword accuracy ≥85% compared to expert benchmarks
- **SC-003**: Computer Use publishing completes in ≤5 minutes for 95% of tasks
- **SC-004**: Publishing success rate ≥90% (target: 95%)
- **SC-005**: All publish tasks generate ≥8 screenshots
- **SC-006**: 100% of Computer Use operations logged to execution_logs
- **SC-007**: Batch import of 100 articles completes in ≤5 minutes
- **SC-008**: Manual SEO edits reflected in published articles 100% of the time
- **SC-009**: System supports 5 concurrent publish tasks without performance degradation
- **SC-010**: Provider switching (via env var) takes effect within 1 service restart
- **SC-011**: Anthropic Computer Use cost ≤$1.50 per article
- **SC-012**: Gemini Computer Use cost ≤$1.00 per article (when available)
- **SC-013**: Playwright fallback success rate ≥80% when AI providers fail
- **SC-014**: Screenshot retention policy enforced (90 days, auto-deletion verified)
- **SC-015**: Zero security vulnerabilities (HIGH/CRITICAL) in dependency scans

---

## Out of Scope

The following features are explicitly excluded from this specification:

- **AI Article Generation**: New content creation from topics (not a core requirement; can be added later as optional feature)
- **Multi-language Support**: Translation or i18n (future enhancement)
- **Social Media Publishing**: Cross-posting to Twitter, Facebook, LinkedIn (separate feature)
- **Advanced Media Creation**: Video generation, infographics, AI image creation
- **CMS Platforms Beyond WordPress**: Support for Ghost, Strapi, Drupal (Phase 1 is WordPress-only)
- **Content Plagiarism Detection**: Requires third-party integration (Copyscape, etc.)
- **Advanced Workflow Approval**: Multi-stage review process (future enhancement)
- **Real-time Collaboration**: Concurrent editing by multiple users
- **A/B Testing**: SEO metadata A/B testing for optimization
- **Analytics Integration**: Google Analytics, Search Console integration
- **Email Notifications**: Custom email alerts (webhook notifications supported)

---

## Technical Constraints

### Provider-Specific Limitations

#### Anthropic Computer Use
- **Status**: Beta (requires API access approval)
- **Rate Limits**: Subject to Anthropic's beta rate limits
- **Cost**: $0.50-1.50 per article (higher than Messages API)
- **Speed**: ~2-5 minutes per publish task
- **Pros**: AI-adaptive to UI changes, natural language instructions
- **Cons**: Expensive, slower, beta stability

#### Gemini Computer Use
- **Status**: Recently announced (API details pending)
- **Availability**: Flash version may be free or low-cost
- **Implementation**: Placeholder provider structure until API is finalized
- **Pros**: Potentially lower cost than Anthropic
- **Cons**: Untested, API may change, documentation pending

#### Playwright
- **Status**: Stable, production-ready
- **Cost**: Free (no API fees)
- **Speed**: Fast (~1-2 minutes per publish)
- **Pros**: Reliable, fast, free, complete control
- **Cons**: Requires selector maintenance, brittle to UI changes

### Infrastructure Constraints
- **Browser Environment**: Requires Chromium/Chrome in Docker container
- **Display Server**: Requires Xvfb for headless browser rendering
- **Storage**: S3 or equivalent for production screenshot storage
- **Database**: PostgreSQL 15+ (JSONB support required)
- **Celery**: Redis required for task queue
- **Memory**: Minimum 4GB RAM per worker for browser automation

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Anthropic Computer Use API changes (beta) | Medium | High | Abstract provider interface allows easy adapter updates |
| Gemini API not ready at launch | Medium | Medium | Start with Anthropic + Playwright, add Gemini later |
| WordPress UI changes break automation | Medium | Medium | AI providers auto-adapt; Playwright requires selector updates |
| Computer Use costs exceed budget | Medium | High | Implement cost tracking, provider switching, Playwright fallback |
| Screenshot storage costs grow rapidly | Low | Medium | Implement 90-day retention policy, compress images |
| Provider performance varies significantly | High | Medium | Build comparison dashboard, enable easy switching |
| Security: Credentials leaked in screenshots | Low | Critical | Mask password fields, audit screenshot capture logic |
| Concurrent tasks overwhelm browser resources | Medium | Medium | Implement queue limits, horizontal worker scaling |

---

## Dependencies

### External APIs
- **Anthropic Claude API**: Messages API (SEO analysis) + Computer Use API (publishing)
- **Google Gemini API**: Computer Use API (when available)
- **WordPress REST API**: Read-only queries for validation (not primary publish method)

### Infrastructure
- **PostgreSQL 15+**: Database with JSONB support
- **Redis 7+**: Celery task queue
- **S3 or Object Storage**: Screenshot and image storage
- **Docker**: Containerization for browser environment
- **Chromium/Chrome**: Browser for Computer Use automation

### Third-Party Libraries
- **Anthropic Python SDK**: ≥0.71.0
- **Google Generative AI SDK**: ≥0.3.0 (for Gemini)
- **Playwright for Python**: ≥1.40.0
- **Celery**: ≥5.5.0
- **FastAPI**: ≥0.104.0
- **SQLAlchemy**: ≥2.0.0

---

## Compliance & Governance

This specification adheres to the project's Constitution (`.specify/memory/constitution.md`):

- **I. Modularity**: Provider abstraction enables independent development and testing of each Computer Use implementation
- **II. Observability**: Comprehensive logging, screenshots, and execution logs provide full audit trail
- **III. Security**: Encrypted credential storage, XSS prevention, authentication required
- **IV. Testability**: Each User Story has independent test scenarios, provider switching enables A/B testing
- **V. API-First Design**: All functionality exposed via REST API before UI implementation

### Additional Security Requirements (per Constitution III.5)
- CMS credentials stored in AWS Secrets Manager or HashiCorp Vault
- Credentials only in Computer Use session memory, never logged
- Minimum privilege WordPress user (Editor role, not Administrator)
- Credential rotation every 90 days
- All CMS login attempts logged to audit_logs table

### Computer Use Testing Strategy (per Constitution IV.5)
- Unit tests use mock Computer Use API
- Integration tests run on isolated test WordPress instances
- Screenshot validation ensures UI elements found
- Quarterly UI regression tests detect WordPress changes
- Fallback to manual publishing if all providers fail

---

## Appendix: Provider Selection Guide

### When to Use Anthropic Computer Use
- WordPress UI frequently changes
- SEO plugin configuration varies across sites
- Budget allows $1.00-1.50 per article
- Need AI to handle unexpected UI variations

### When to Use Gemini Computer Use
- Cost optimization is critical
- Google ecosystem integration preferred
- Willing to test new/beta API
- Need balance between adaptability and cost

### When to Use Playwright
- High-volume publishing (100+ articles/day)
- WordPress setup is standardized and stable
- Zero API cost requirement
- Development team can maintain selectors
- Speed is critical (need <2 min publish time)

### Hybrid Approach (Recommended)
1. **Default**: Playwright (fast, free, reliable)
2. **Fallback**: Anthropic Computer Use (when Playwright fails)
3. **Testing**: Gemini Computer Use (parallel testing for cost comparison)

---

**Document Owner**: Product & Engineering Team
**Reviewers**: CTO, Security Lead, DevOps Lead
**Next Review**: After Phase 1 implementation (before production deployment)
**Version**: 2.0.0 (Refactored for Multi-Provider Architecture)
