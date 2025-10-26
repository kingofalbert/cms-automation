# Feature Specification: AI-Powered CMS Automation with SEO Optimization

**Feature Branch**: `001-cms-automation`
**Created**: 2025-10-25
**Last Updated**: 2025-10-25
**Status**: In Development (Fusion Architecture)
**Input**: "Implement dual-source CMS automation: AI article generation + external import, unified SEO optimization, and Computer Use API automated publishing to WordPress."

## Overview

This feature provides a comprehensive content management automation platform with dual content sources:

1. **AI Generation Path** (Preserved): Users submit topics → Claude generates articles → Ready for SEO
2. **Import Path** (New): Users import existing articles → Stored in system → Ready for SEO
3. **Unified Processing** (New): All articles → SEO optimization → Computer Use publishing → WordPress

**Core Value Propositions**:
- Maximize existing AI generation investment while meeting new requirements
- Batch SEO optimization for existing article libraries
- Browser automation for reliable WordPress publishing
- Complete audit trail with screenshot verification
- Support for outsourced content with unified quality standards

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - AI Article Generation (Priority: P1) [PRESERVED]

Content managers can provide article topics or outlines and receive fully formatted, ready-to-publish articles without manual content creation.

**Why this priority**: This is an existing core value proposition that reduces content creation time by 70%. Preserving this functionality maximizes our investment in the current system.

**Independent Test**: Can be fully tested by submitting an article topic and verifying a complete article is generated with proper formatting (existing E2E tests cover this).

**Acceptance Scenarios**:

1. **Given** a content manager is logged into the CMS, **When** they submit an article topic through the automation interface, **Then** a complete article with title, body, and formatting is generated within 5 minutes for 95% of requests
2. **Given** an article outline is provided with specific sections, **When** the automation processes the request, **Then** the generated article follows the outlined structure exactly
3. **Given** multiple article topics are submitted simultaneously, **When** the automation processes the batch, **Then** all articles are generated without conflicts or data corruption
4. **Given** an AI-generated article is created, **When** stored in the database, **Then** the article.source field is set to 'ai_generated' for tracking

---

### User Story 2 - External Article Import (Priority: P1) [NEW]

Content managers can import existing articles from external sources (CSV, JSON, manual entry) to feed into the unified SEO and publishing pipeline.

**Why this priority**: Supports the primary requirement of SEO-optimizing existing article libraries. Without this, we cannot process outsourced content or migrate existing articles.

**Independent Test**: Upload CSV file with 50 articles and verify all are correctly imported with proper data mapping and validation.

**Acceptance Scenarios**:

1. **Given** a content manager has a CSV file with 100 existing articles, **When** they upload the file through the import interface, **Then** all 100 articles are imported within 5 minutes with validation of required fields (title, body) and optional fields (images, metadata)
2. **Given** an imported article contains 3 image URLs, **When** the import process runs, **Then** all image references are validated and stored in article.metadata.images field for later uploading
3. **Given** an article with HTML special characters, **When** imported, **Then** HTML is correctly sanitized to prevent XSS while preserving formatting
4. **Given** imported articles are stored, **When** queried, **Then** the article.source field is set to 'imported' to distinguish from AI-generated content
5. **Given** duplicate detection is enabled, **When** importing an article semantically similar (>0.85 similarity) to an existing one, **Then** the system alerts the user before proceeding

---

### User Story 3 - Unified SEO Optimization (Priority: P1) [NEW]

Articles from both sources (AI-generated and imported) are automatically analyzed to generate optimized SEO metadata including titles, descriptions, keywords, and density analysis.

**Why this priority**: This is the core new requirement. SEO optimization is the primary value driver for the enhanced system, directly impacting search rankings and traffic.

**Independent Test**: Provide test articles and verify SEO metadata quality against expert-written benchmarks (85%+ accuracy target).

**Acceptance Scenarios**:

1. **Given** an article (from either source) with 1500 words, **When** SEO analysis is triggered, **Then** within 30 seconds the system generates:
   - SEO title (50-60 characters)
   - Meta description (150-160 characters)
   - Focus keyword (1 primary keyword)
   - Primary keywords (3-5 keywords)
   - Secondary keywords (5-10 keywords)
   - Keyword density analysis (JSONB with percentages)
   - Optimization recommendations (array of actionable suggestions)
2. **Given** 20 test articles analyzed by the system, **When** compared to SEO metadata written by qualified experts, **Then** the automated keyword extraction achieves 85%+ accuracy
3. **Given** a generated SEO title exceeds 60 characters, **When** validation runs, **Then** the system automatically truncates to 60 chars and adds a warning to optimization_recommendations
4. **Given** SEO metadata is generated, **When** stored, **Then** all metadata is saved in the seo_metadata table with proper foreign key relationship to the article
5. **Given** a content manager wants to refine SEO, **When** they manually edit SEO fields, **Then** changes are tracked in seo_metadata.manual_overrides JSONB field with timestamps

---

### User Story 4 - Computer Use Automated Publishing (Priority: P1) [NEW]

The system uses Claude Computer Use API to automate browser-based WordPress publishing, including content entry, image upload, SEO field configuration, and publication verification.

**Why this priority**: This is the core technical innovation enabling true end-to-end automation. Computer Use provides reliability and flexibility beyond REST API integration.

**Independent Test**: Execute full publishing workflow on test WordPress instance and verify all steps complete successfully with screenshot evidence.

**Acceptance Scenarios**:

1. **Given** an article with SEO metadata ready for publishing, **When** a Computer Use publish task is submitted, **Then** within 5 minutes the system completes and screenshots:
   - Browser login to WordPress (login_success.png)
   - New post creation (editor_loaded.png)
   - Title and body content filled (content_filled.png)
   - Featured image upload if present (image_uploaded.png)
   - SEO plugin fields filled (Yoast/Rank Math) (seo_fields_filled.png)
   - Categories and tags assigned (taxonomy_set.png)
   - Publish button clicked (publish_clicked.png)
   - Article live verification (article_live.png)
2. **Given** WordPress login fails due to incorrect credentials, **When** Computer Use attempts login, **Then** after 3 retries the task is marked as 'failed', error details saved to publish_tasks.error_message, and user is notified
3. **Given** an article with 5 images, **When** Computer Use uploads images, **Then** all images are uploaded in sequence and inserted at correct positions in the article body, verified by screenshots
4. **Given** network timeout occurs during publishing, **When** Computer Use detects timeout, **Then** the system retries the current step up to 3 times with 10-second delays between retries
5. **Given** publishing completes successfully, **When** the task finishes, **Then** the article.cms_article_id is updated with the WordPress post ID and article.published_at is set to the current timestamp

---

### User Story 5 - Publishing Task Monitoring & Audit (Priority: P2) [NEW]

Content managers can view real-time status, execution logs, and screenshots for all Computer Use publishing tasks for transparency and debugging.

**Why this priority**: Observability is critical for quality assurance and troubleshooting, but doesn't block core publishing functionality (can be added after P1 features work).

**Independent Test**: Simulate publishing tasks and verify status updates, screenshot storage, and log completeness.

**Acceptance Scenarios**:

1. **Given** a Computer Use task is executing, **When** a user views the task detail page, **Then** real-time status shows current step (e.g., "Uploading images") and progress percentage
2. **Given** a completed publishing task, **When** reviewing task details, **Then** all 8 key screenshots are accessible and correctly labeled with timestamps
3. **Given** a system administrator needs audit history, **When** exporting execution logs, **Then** a JSON file is generated containing all operation records including: action type, target element, timestamp, result status, and error messages if applicable
4. **Given** 100 publishing tasks executed in the past month, **When** viewing the dashboard, **Then** success rate, average duration, and common failure reasons are displayed in aggregate metrics

---

### User Story 6 - Intelligent Tagging and Categorization (Priority: P3) [PRESERVED]

Articles from both sources are automatically tagged and categorized based on content analysis, ensuring consistent taxonomy and improving content discoverability.

**Why this priority**: Tagging enhances content organization and SEO, but is less critical than core SEO metadata. This is preserved from the original system as a P3 feature.

**Independent Test**: Provide pre-written articles to the tagging system and verify appropriate tags and categories are assigned based on content analysis.

**Acceptance Scenarios**:

1. **Given** an article (from either source) about a specific topic, **When** the tagging system analyzes the content, **Then** relevant tags are automatically assigned with at least 85% accuracy compared to manual tagging by qualified content editors
2. **Given** an article covering multiple topics, **When** categorization runs, **Then** the article is assigned to all relevant categories without duplicates
3. **Given** existing tags in the CMS taxonomy, **When** new articles are processed, **Then** the system uses existing tags when appropriate rather than creating synonyms

---

### User Story 7 - Scheduling and Publishing Workflow (Priority: P4) [PRESERVED]

Content managers can define publishing schedules and the system automatically publishes articles at specified times without manual intervention.

**Why this priority**: Scheduling automation ensures consistent publishing cadence, but articles must exist first and be optimized. Preserved from original system as P4.

**Independent Test**: Schedule pre-created articles for future publication and verify they publish at the correct time with proper status transitions.

**Acceptance Scenarios**:

1. **Given** a completed article ready for publication, **When** a content manager sets a future publication date and time, **Then** the article automatically publishes at the specified time within 1-minute accuracy
2. **Given** multiple articles scheduled for the same time slot, **When** the publication time arrives, **Then** all articles publish successfully without system overload
3. **Given** a scheduled article with dependencies (e.g., SEO metadata incomplete), **When** publication time arrives but dependencies are missing, **Then** the system notifies the content manager and holds the article in draft status

---

### Edge Cases

**MVP Scope (Covered by Tasks)**:
- What happens when the Claude API is temporarily unavailable during article generation? → Handled by retry logic with exponential backoff (existing)
- What happens when Computer Use encounters an unexpected WordPress UI change? → Screenshot comparison detects anomalies and alerts user for manual intervention (T037)
- How does the system handle articles imported without images? → Image fields are optional; Computer Use skips image upload step if article.metadata.images is empty (T029)

**Post-MVP / Phase 5+ Enhancements**:
- How does the system handle duplicate article topics submitted by different users? → Semantic similarity detection alerts users before generation (FR-018, existing)
- What occurs when scheduled publication conflicts with CMS maintenance windows? → Future: Add maintenance window awareness to scheduling service
- How does the system manage articles that exceed WordPress content length limits? → Future: Pre-validation against CMS-specific limits
- What happens when SEO metadata confidence is below threshold? → Future: Flag for manual review when confidence < 70%
- How does Computer Use handle multi-language WordPress installations? → Future: Language detection and locale-specific publishing
- What occurs when a WordPress plugin (Yoast/Rank Math) is updated and changes UI? → Future: Version-aware Computer Use prompts with fallback strategies

---

## Requirements *(mandatory)*

### Functional Requirements

#### Article Generation (Preserved)
- **FR-001**: System MUST accept article topics or outlines as input from authorized users
- **FR-002**: System MUST generate complete articles including title, body content, and basic formatting within 5 minutes for 95% of requests (using Claude Messages API)
- **FR-003**: System SHALL validate generated article quality against measurable criteria:
  - **Readability**: Flesch-Kincaid Grade 8-12
  - **Word count**: 500-2000 words
  - **Coherence**: semantic similarity to prompt ≥ 0.7
- **FR-004**: System MUST mark AI-generated articles with source='ai_generated' in the articles table

#### Article Import (New)
- **FR-005**: System MUST accept article imports via CSV, JSON, and manual form entry
- **FR-006**: System MUST validate imported articles for required fields (title, body) and sanitize HTML content
- **FR-007**: System MUST support batch import of up to 1000 articles per upload with progress tracking
- **FR-008**: System MUST mark imported articles with source='imported' in the articles table
- **FR-009**: System MUST store image URLs from imported articles in article.metadata.images JSONB field

#### SEO Optimization (New)
- **FR-010**: System MUST analyze article content and generate SEO metadata within 30 seconds:
  - SEO title (50-60 characters)
  - Meta description (150-160 characters)
  - Focus keyword (1 primary)
  - Primary keywords (3-5)
  - Secondary keywords (5-10)
  - Keyword density analysis (JSONB)
  - Optimization recommendations (array)
- **FR-011**: System MUST achieve 85%+ accuracy for automated keyword extraction compared to expert benchmarks
- **FR-012**: System MUST store SEO metadata in seo_metadata table with article_id foreign key
- **FR-013**: System MUST allow manual editing of SEO metadata with change tracking in manual_overrides JSONB field
- **FR-014**: System MUST automatically validate SEO field lengths and truncate with warnings if exceeded

#### Computer Use Publishing (New)
- **FR-015**: System MUST use Claude Computer Use API to publish articles to WordPress via browser automation
- **FR-016**: System MUST complete publishing workflow within 5 minutes for 95% of requests including:
  - WordPress login authentication
  - New post creation
  - Title and body content entry
  - Featured image upload (if present)
  - SEO plugin field configuration (Yoast SEO or Rank Math)
  - Category and tag assignment
  - Publish action and verification
- **FR-017**: System MUST capture screenshots at 8 key steps during publishing for audit trail
- **FR-018**: System MUST store screenshots in publish_tasks.screenshots JSONB field with timestamps and labels
- **FR-019**: System MUST retry failed Computer Use operations up to 3 times with exponential backoff (10s, 30s, 90s delays)
- **FR-020**: System MUST update article.cms_article_id with WordPress post ID upon successful publication
- **FR-021**: System MUST log all Computer Use actions to execution_logs table with action, element, timestamp, and result fields

#### Workflow & Monitoring (New/Updated)
- **FR-022**: System MUST maintain article status throughout workflow (draft, seo_optimizing, seo_complete, publishing, published, failed)
- **FR-023**: System MUST track publishing task status (pending, in_progress, completed, failed) in publish_tasks table
- **FR-024**: System MUST provide real-time status updates for publishing tasks via API polling
- **FR-025**: System MUST notify users of task failures via configured notification channels (email, webhook)
- **FR-026**: System MUST generate aggregate metrics for publishing tasks (success rate, avg duration, failure reasons)

#### Content Management (Preserved)
- **FR-027**: System MUST automatically analyze article content and assign relevant tags from existing taxonomy
- **FR-028**: System MUST create new tags when content topics are not covered by existing taxonomy
- **FR-029**: System MUST categorize articles into appropriate sections based on content analysis
- **FR-030**: System MUST allow content managers to schedule articles for future publication with date and time specification
- **FR-031**: System MUST publish scheduled articles automatically at the specified time with 1-minute accuracy
- **FR-032**: System MUST handle concurrent article processing requests (generation, import, SEO, publishing) without performance degradation

#### Security & Compliance (Updated)
- **FR-033**: System MUST store WordPress credentials in encrypted environment variables or secret vault
- **FR-034**: System MUST NOT log WordPress passwords in execution logs or screenshots
- **FR-035**: System MUST use dedicated CMS accounts with minimum required permissions (author or editor role)
- **FR-036**: System MUST maintain complete audit trails for all automation actions (FR-014)
- **FR-037**: System MUST integrate with existing CMS authentication and authorization systems

#### Data Management (Updated)
- **FR-038**: System SHOULD prevent duplicate article creation by using semantic similarity analysis (>0.85 cosine similarity) to detect substantially similar content (Post-MVP Phase 5)
- **FR-039**: System MUST preserve all article metadata (author, creation date, tags, categories, source) throughout the automation process
- **FR-040**: System MUST support rollback of published articles to draft status if issues are discovered

---

### Key Entities

- **Article**: Represents a content piece with attributes including:
  - Core: id, title, body, status
  - Source tracking: **source** (enum: 'ai_generated', 'imported')
  - SEO: **seo_optimized** (boolean)
  - CMS integration: cms_article_id, published_at
  - Metadata: author_id, created_at, metadata (JSONB for images, formatting)

- **TopicRequest** [Preserved]: Represents a user's submission for AI article creation:
  - topic_description, outline, style_tone, target_word_count
  - priority, submitted_by, submitted_at, status
  - article_id (foreign key to generated article)

- **SEOMetadata** [New]: Represents SEO analysis results:
  - article_id (foreign key), seo_title, meta_description
  - focus_keyword, primary_keywords (array), secondary_keywords (array)
  - keyword_density (JSONB), optimization_recommendations (array)
  - manual_overrides (JSONB with timestamps)
  - generated_at, updated_at

- **PublishTask** [New]: Represents a Computer Use publishing operation:
  - article_id (foreign key), cms_type (default: 'wordpress')
  - status (enum: pending, in_progress, completed, failed)
  - screenshots (JSONB array with {step, url, timestamp})
  - retry_count, max_retries, error_message
  - started_at, completed_at, duration_seconds

- **ExecutionLog** [New]: Represents detailed Computer Use action log:
  - publish_task_id (foreign key)
  - action (e.g., 'click', 'type', 'screenshot', 'verify')
  - target_element (CSS selector or description)
  - payload (JSONB with action-specific data)
  - result (enum: success, failure, retry)
  - timestamp

- **Tag** [Preserved]: Represents a content classification keyword:
  - name, slug, category, usage_count
  - source (automated or manual), cms_tag_id

- **Schedule** [Preserved]: Represents a publishing schedule:
  - article_id, scheduled_time, creator_id
  - status, retry_count, max_retries

- **WorkflowState** [Preserved]: Represents approval and review state:
  - article_id, current_status, assigned_reviewers
  - approval_history (JSONB), modification_requests (JSONB)

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

#### AI Generation (Preserved)
- **SC-001**: Content managers can generate publication-ready articles within 5 minutes for 95% of requests from topic submission to completed draft (95th percentile SLA)
- **SC-002**: AI-generated articles require minimal editing (fewer than 10% word changes or less than 2 minutes editing time) in 90% of cases

#### Article Import (New)
- **SC-003**: System successfully imports 100 articles from CSV within 5 minutes with 100% data integrity
- **SC-004**: HTML sanitization prevents 100% of XSS vulnerabilities in imported content

#### SEO Optimization (New)
- **SC-005**: Automated SEO keyword extraction achieves at least 85% accuracy compared to expert-written metadata (measured on 100-article test set)
- **SC-006**: SEO metadata generation completes within 30 seconds for 95% of articles
- **SC-007**: 90% of SEO-optimized articles meet Google Search Console recommendations (title length, description length, keyword placement)

#### Computer Use Publishing (New)
- **SC-008**: Computer Use publishing completes successfully for 95% of tasks within 5 minutes
- **SC-009**: Screenshot capture achieves 100% coverage of 8 mandatory steps per publishing task
- **SC-010**: Computer Use retry logic reduces transient failure rate by 80% compared to single-attempt execution
- **SC-011**: Zero WordPress credentials are exposed in logs or screenshots (100% security compliance)

#### System Performance (Updated)
- **SC-012**: System processes at least 50 concurrent requests (mix of generation, import, SEO, publishing) without performance degradation
- **SC-013**: Article processing workflow from import to published reduces average time from 4 hours (manual) to under 10 minutes (automated) - 95% time reduction
- **SC-014**: Zero data loss or corruption occurs during automated article processing across all workflows
- **SC-015**: System uptime for automation services maintains 99.5% availability during business hours

#### User Satisfaction (Updated)
- **SC-016**: Content managers report at least 80% satisfaction with dual-source workflow in feedback surveys
- **SC-017**: SEO metadata quality receives 4/5 or higher rating from content managers (80%+ approval)
- **SC-018**: Computer Use publishing accuracy achieves 4.5/5 rating for correct field population

---

## Assumptions *(mandatory)*

- Content managers have basic CMS access permissions and understand content approval workflows
- WordPress installation is accessible via web browser with stable network connectivity
- WordPress uses Gutenberg or Classic Editor (supported; custom editors may require additional Computer Use prompt engineering)
- SEO plugin (Yoast SEO or Rank Math) is installed and configured on target WordPress site
- Content quality standards and style guides are defined and can be provided as reference material for AI generation
- Network connectivity to Claude API is reliable during normal business operations
- Imported articles are primarily text-based; complex media embedding is handled separately
- Content managers will provide feedback on SEO quality to improve future analysis
- Publishing schedules follow standard timezone conventions defined in CMS settings
- Generated articles comply with copyright and plagiarism standards enforced by Claude API
- System will operate during defined business hours with maintenance windows communicated in advance
- WordPress sites are running version 5.0+ with modern PHP (7.4+) for compatibility

---

## Dependencies *(mandatory)*

- **Claude API**: Messages API for article generation, Computer Use API for browser automation
- **WordPress CMS**: Target publishing platform with admin access
- **SEO Plugin**: Yoast SEO or Rank Math installed on WordPress
- **Browser Environment**: Chrome or Chromium for Computer Use automation
- **Database**: PostgreSQL 15+ with pgvector extension for semantic similarity
- **Task Queue**: Celery + Redis for async processing (generation, SEO, publishing)
- **User Authentication**: Existing auth system for access control
- **Notification System**: Email or webhook service for task alerts
- **Storage**: File storage for screenshots (local filesystem or S3-compatible storage)

---

## Constraints *(mandatory)*

- Article generation time cannot exceed 5 minutes for 95% of requests to maintain user productivity
- SEO analysis must complete within 30 seconds to support batch processing workflows
- Computer Use publishing must complete within 5 minutes to prevent timeout and maintain throughput
- System must work within existing WordPress capabilities (no core CMS modifications)
- Claude API usage cost must not exceed:
  - $0.03 per article for AI generation (Messages API)
  - $0.50 per article for Computer Use publishing
  - $0.10 per article for SEO analysis
  - Total: $0.63 per article average cost target
- Automated actions must maintain complete audit trails with screenshots for compliance
- System must not bypass existing WordPress security or permission models
- WordPress credentials must be stored encrypted and never logged in plain text
- Performance must not degrade existing CMS functionality for non-automation users
- Computer Use sessions must be isolated in sandboxed environments to prevent security risks
- Screenshot storage must comply with data retention policies (default: 90 days)

---

## Out of Scope

- Training custom AI models or fine-tuning language models for SEO analysis
- Content translation or multi-language article generation in initial release
- Advanced media creation (images, videos, infographics) beyond text content
- Integration with external social media platforms for cross-posting
- Analytics and performance tracking for published articles (e.g., page views, engagement)
- Plagiarism detection beyond what Claude API provides
- Custom WordPress plugin development or core CMS functionality modifications
- Content monetization or paywall management
- User-generated content moderation or community features
- Support for CMS platforms other than WordPress (Drupal, Joomla, etc.) in initial release
- Advanced A/B testing for SEO variations
- Real-time collaboration features for multi-user article editing
