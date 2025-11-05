# Feature Specification: E2E Test Coverage & Production Regression Testing

**Feature Branch**: `003-e2e-test-coverage`
**Created**: 2025-11-04
**Status**: Draft
**Priority**: P0 (Critical - Production Stability)
**Current Coverage**: 37.5% (6/16 modules)
**Target Coverage**: 85% (14/16 modules)
**Input**: "準備用 Playwright 做整體的迴歸測試 (regression test)，要測試所有可能的邊緣情況，而且要對生產環境做測試。"

## Overview

This feature establishes comprehensive end-to-end (E2E) test coverage for the CMS Automation platform to ensure production stability, catch regressions early, and validate all critical user workflows. Currently, only 37.5% of functionality is covered by E2E tests, leaving significant gaps in edge cases, error handling, and cross-browser compatibility.

### Current State Analysis

**Existing Test Coverage** (from `PLAYWRIGHT_TEST_COVERAGE_ANALYSIS.md`):
- ✅ **Covered Modules (6)**: API Integration (70%), Article Generator (75%), Navigation (90%), Settings (65%), Production Smoke Tests (80%), Basic Functionality (50%)
- ❌ **Uncovered Modules (10)**: Article Import, Article List, Article Review, Publish Tasks, Provider Comparison, Worklist, Schedule Manager, Tags, Proofreading Rules, Published Rules, Proofreading Stats
- ⚠️ **Edge Case Coverage**: Only 15% (network errors, file uploads, security, performance untested)

### Core Problems Identified

1. **62.5% Functionality Untested**: 10 out of 16 modules lack any E2E tests, creating blind spots for production bugs
2. **Missing Edge Cases**: Network failures, file upload errors, XSS/injection attacks, race conditions not covered
3. **Single Browser Testing**: Only Chromium tested, Firefox/Safari users at risk
4. **No Performance Validation**: No LCP/FID/CLS budgets, user experience degradation undetected
5. **Insufficient Production Tests**: Limited smoke tests, no continuous monitoring or alerting

### Core Value Propositions

- **Production Stability**: Catch critical bugs before users encounter them
- **Regression Prevention**: Automated tests prevent feature breakage during updates
- **Multi-Browser Confidence**: Validate experience across Chrome, Firefox, Safari
- **Security Assurance**: Verify protection against XSS, injection, and other attacks
- **Performance Guarantees**: Enforce Web Vitals budgets (LCP < 2.5s, FID < 100ms)
- **Developer Velocity**: Faster deployments with automated validation

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Article Import Edge Cases (Priority: P0)

**As a** content manager
**I want** reliable article import from CSV/JSON/Google Drive with comprehensive error handling
**So that** I can confidently migrate large content libraries without data loss

**Why this priority**: Article import is the entry point for the entire system. Current 0% test coverage means production failures are undetected until users report them. This creates data loss risk and erodes trust.

**Independent Test**: Upload a 100MB CSV with 10,000 articles containing malformed data, special characters, and edge cases. Verify graceful handling of all errors, progress tracking, and data integrity.

**Acceptance Scenarios**:

1. **Given** a content manager uploads a CSV file larger than 100MB
   **When** the upload starts
   **Then** the system:
   - Shows upload progress bar (0-100%)
   - Supports chunked upload for large files
   - Displays estimated time remaining
   - Allows cancellation with cleanup
   - Resumes from checkpoint on network failure

2. **Given** a CSV file contains 50 rows with XSS attack vectors (`<script>alert('xss')</script>`, `onclick="evil()"`)
   **When** import validation runs
   **Then** all malicious content is:
   - Detected by HTML sanitizer
   - Stripped while preserving safe content
   - Logged to security audit trail
   - Reported to admin in summary (50 sanitized rows)
   - Never executed in browser context

3. **Given** a JSON file contains invalid UTF-8 encoding
   **When** parsing fails
   **Then** the system:
   - Shows clear error message: "File encoding error on line 42"
   - Suggests fix: "Please ensure file is UTF-8 encoded"
   - Provides partial import option for valid rows
   - Exports error report for manual review

4. **Given** network connection drops during Google Drive sync
   **When** connection interruption detected
   **Then** the system:
   - Pauses sync and shows "Connection lost" toast
   - Auto-retries after 5s with exponential backoff
   - Resumes from last successful checkpoint
   - Logs retry attempts to monitoring system
   - Alerts admin after 3 failed retries

**Dependencies**: Backend file upload service, sanitization library, Google Drive API integration

---

### User Story 2 - Article List Performance & UX (Priority: P0)

**As a** content manager
**I want** fast, responsive article list with smooth scrolling and filtering
**So that** I can efficiently browse and manage thousands of articles

**Why this priority**: Currently 0% tested. Article list is the most frequently accessed page. Performance issues directly impact daily productivity for all users.

**Independent Test**: Load article list with 10,000 articles, apply complex filters, scroll to bottom, and verify performance meets Web Vitals budgets (LCP < 2.5s, FID < 100ms, CLS < 0.1).

**Acceptance Scenarios**:

1. **Given** database contains 10,000 articles
   **When** user navigates to /articles page
   **Then** performance metrics are:
   - LCP (Largest Contentful Paint) < 2.5 seconds
   - FID (First Input Delay) < 100 milliseconds
   - CLS (Cumulative Layout Shift) < 0.1
   - Initial render shows 50 articles (virtualized)
   - Remaining articles load on scroll

2. **Given** user scrolls rapidly through 1,000 articles
   **When** virtual scroll renders new items
   **Then** scrolling experience is:
   - Smooth 60fps with no jank
   - Images lazy-load 500px before viewport
   - Skeleton placeholders prevent layout shift
   - Scroll position maintained on back navigation

3. **Given** user applies filter: "Status=Draft AND Created>2024-01-01"
   **When** filter debounces after 300ms typing pause
   **Then** filtered results:
   - Return within 500ms
   - Show result count: "Showing 234 of 10,000"
   - Maintain URL state for sharing (?status=draft&created_after=2024-01-01)
   - Clear filter button appears

4. **Given** user enables real-time updates (WebSocket)
   **When** another user publishes an article
   **Then** the list:
   - Shows toast: "1 new article published"
   - Updates count without full reload
   - Maintains scroll position
   - Highlights new item for 3 seconds

**Dependencies**: Virtual scroll component, WebSocket service, pagination API

---

### User Story 3 - Publish Tasks Real-Time Monitoring (Priority: P0)

**As a** content manager
**I want** real-time monitoring of article publishing tasks with detailed progress
**So that** I can track batch operations and quickly respond to failures

**Why this priority**: Currently 0% tested. Publishing is a critical async operation. Users report confusion about task status and miss failure alerts.

**Independent Test**: Start batch publish of 100 articles, simulate 10 failures, verify real-time progress updates, retry mechanism, and error notifications.

**Acceptance Scenarios**:

1. **Given** user initiates batch publish of 100 articles
   **When** publish tasks queue up
   **Then** the UI displays:
   - Overall progress: "Publishing 23/100 articles (23%)"
   - Individual task cards with status badges
   - Real-time updates via WebSocket (1s poll fallback)
   - Estimated completion time
   - Cancel batch button

2. **Given** 10 articles fail to publish (WordPress timeout)
   **When** failures occur
   **Then** the system:
   - Shows error toast: "10 articles failed to publish"
   - Marks failed tasks with red badge
   - Displays error details in task card
   - Offers "Retry Failed" button
   - Logs errors to monitoring system

3. **Given** user clicks "Retry Failed" for 10 failed tasks
   **When** retry starts
   **Then** the system:
   - Resets task status to "queued"
   - Uses exponential backoff (5s, 10s, 20s)
   - Shows retry attempt count (1/3)
   - Stops after 3 failures with manual override option

4. **Given** network connection is unstable
   **When** WebSocket disconnects
   **Then** the system:
   - Automatically falls back to 1s polling
   - Shows "Real-time updates paused" toast
   - Reconnects WebSocket when network restores
   - Resumes live updates seamlessly

**Dependencies**: WebSocket service, Celery task queue, error handling middleware

---

### User Story 4 - Settings Page Security & Validation (Priority: P1)

**As a** system administrator
**I want** comprehensive validation and security for settings configuration
**So that** I can prevent misconfigurations and protect sensitive credentials

**Why this priority**: Currently 65% tested but missing critical security scenarios. Settings page handles sensitive data (WordPress credentials, API keys). Security gaps pose major risk.

**Independent Test**: Attempt to inject XSS payloads, SQL commands, and invalid URLs into all settings fields. Verify all are blocked with clear error messages.

**Acceptance Scenarios**:

1. **Given** admin enters malicious WordPress URL: `javascript:alert('xss')`
   **When** URL validation runs
   **Then** the system:
   - Rejects input with error: "Invalid URL format"
   - Only accepts http:// or https:// protocols
   - Never executes JavaScript in any context
   - Logs attempt to security audit trail

2. **Given** admin enters SQL injection in username: `admin' OR '1'='1`
   **When** form submission occurs
   **Then** the system:
   - Escapes special characters in all text inputs
   - Uses parameterized queries (prevents SQL injection)
   - Displays sanitized value in UI
   - Never executes as SQL command

3. **Given** admin enters 100,000 character string in text field
   **When** field validation runs
   **Then** the system:
   - Rejects input exceeding max length (1000 chars)
   - Shows error: "Maximum 1000 characters allowed"
   - Prevents form submission
   - Protects against buffer overflow attacks

4. **Given** admin saves WordPress credentials
   **When** data is transmitted to backend
   **Then** the system:
   - Encrypts password before transmission (HTTPS)
   - Stores password hashed in database (bcrypt)
   - Never logs password in plaintext
   - Masks password in UI (••••••••)

**Dependencies**: Input validation library, encryption service, security audit logger

---

### User Story 5 - Cross-Browser Compatibility (Priority: P1)

**As a** user on any major browser
**I want** consistent functionality and appearance
**So that** I can use the platform regardless of my browser choice

**Why this priority**: Currently only Chromium tested (0% Firefox/Safari coverage). 30% of users report issues on non-Chrome browsers, creating poor UX.

**Independent Test**: Run full test suite on Chrome, Firefox, and Safari. Verify 100% pass rate on all browsers with identical behavior.

**Acceptance Scenarios**:

1. **Given** user opens application on Firefox 120
   **When** all features are tested
   **Then** behavior matches Chrome exactly:
   - Navigation menu renders correctly
   - Forms submit successfully
   - Modals display without layout issues
   - Date pickers use native controls
   - All JavaScript executes without errors

2. **Given** user opens application on Safari 17 (macOS)
   **When** WebSocket connections establish
   **Then** real-time features work:
   - WebSocket connects successfully
   - Live updates appear in task list
   - Fallback to polling if unsupported
   - No console errors in Safari DevTools

3. **Given** user opens application on mobile Safari (iOS 17)
   **When** responsive design activates
   **Then** mobile experience is optimal:
   - Hamburger menu opens smoothly
   - Touch gestures work (swipe, tap, pinch)
   - Viewport meta tag prevents zoom issues
   - No horizontal scrolling

4. **Given** user with high-DPI display (Retina)
   **When** page renders
   **Then** visual quality is sharp:
   - Images use 2x resolution sources
   - SVG icons render crisply
   - Text is readable at all sizes
   - No pixelated graphics

**Dependencies**: Playwright browser fixtures, cross-browser testing CI pipeline

---

### User Story 6 - Performance Budgets Enforcement (Priority: P1)

**As a** product owner
**I want** automated performance budget enforcement in CI/CD
**So that** we prevent performance regressions before they reach production

**Why this priority**: Currently 0% performance testing. Multiple user complaints about slow page loads. No automated guardrails to prevent regressions.

**Independent Test**: Deploy code change that adds 1MB uncompressed image. Verify CI pipeline fails with performance budget violation before merge.

**Acceptance Scenarios**:

1. **Given** developer commits code that increases bundle size by 500KB
   **When** CI pipeline runs performance tests
   **Then** the build:
   - Fails with error: "Bundle size exceeded: 2.5MB (budget: 2MB)"
   - Shows breakdown by chunk
   - Blocks merge to main branch
   - Requires approval override from tech lead

2. **Given** homepage LCP increases from 2.0s to 3.5s
   **When** Lighthouse CI runs
   **Then** the build:
   - Fails performance budget check
   - Reports: "LCP 3.5s exceeds budget of 2.5s"
   - Generates trace for debugging
   - Posts comment on PR with recommendations

3. **Given** new feature adds 50 synchronous scripts
   **When** blocking time analysis runs
   **Then** the build:
   - Fails if Total Blocking Time > 300ms
   - Identifies long tasks > 50ms
   - Suggests code-splitting strategies
   - Links to performance optimization guide

4. **Given** all performance budgets pass
   **When** PR is merged to main
   **Then** the system:
   - Records baseline metrics
   - Updates performance dashboard
   - Sends Slack notification: "Performance: ✅ All budgets passed"
   - Allows production deployment

**Dependencies**: Lighthouse CI, bundle analyzer, performance monitoring dashboard

---

### User Story 7 - End-to-End Critical Workflows (Priority: P2)

**As a** QA engineer
**I want** automated E2E tests for complete user workflows
**So that** we validate entire feature chains work together

**Why this priority**: Currently no E2E workflow tests. Integration bugs between modules go undetected until production.

**Independent Test**: Execute complete workflow: Import article → SEO analysis → Proofreading → Publish to WordPress → Verify live URL. All steps automated, no manual intervention.

**Acceptance Scenarios**:

1. **Given** test suite starts with clean database
   **When** complete workflow executes:
   - Step 1: Import CSV with 1 article
   - Step 2: Trigger SEO analysis
   - Step 3: Run proofreading engine
   - Step 4: Approve all changes
   - Step 5: Publish to WordPress
   - Step 6: Verify article live on test.example.com
   **Then** all steps succeed within 5 minutes with:
   - Each step logged to trace
   - Screenshots saved for each transition
   - Article visible at final URL
   - SEO metadata correct in HTML source

2. **Given** workflow fails at step 3 (proofreading timeout)
   **When** error occurs
   **Then** the system:
   - Rolls back database transaction
   - Shows error context: "Proofreading failed after 60s"
   - Offers retry from failed step (not restart)
   - Logs error to monitoring with full trace

3. **Given** concurrent workflows for 10 articles
   **When** all execute in parallel
   **Then** the system:
   - Handles race conditions gracefully
   - Completes all within 10 minutes
   - No deadlocks or resource starvation
   - Each article published successfully

**Dependencies**: Test database seeding, WordPress test instance, mock data generators

---

## Non-Functional Requirements

### Performance
- **Test Execution Time**: Full suite completes in < 15 minutes
- **Parallelization**: Tests run in parallel (4 workers default)
- **Retries**: Flaky tests auto-retry (max 2 retries)
- **Screenshot Storage**: Compressed to < 500KB per image

### Reliability
- **Test Flakiness**: < 5% flake rate (auto-quarantine flaky tests)
- **CI Stability**: 95% green build rate
- **Cross-Browser**: 100% pass rate on Chrome, Firefox, Safari

### Security
- **Test Isolation**: Each test uses isolated database/browser context
- **Credential Management**: Secrets stored in environment variables
- **Production Safety**: Read-only tests on production (no mutations)

### Maintainability
- **Page Object Pattern**: All tests use POM for reusability
- **Test Data Factories**: Centralized test data generators
- **Documentation**: Every test has clear description and purpose

---

## Success Metrics

### Coverage Metrics
- **Functional Coverage**: 85% (14/16 modules tested)
- **Edge Case Coverage**: 70% (network errors, security, performance)
- **Critical Path Coverage**: 95% (all P0 workflows)

### Quality Metrics
- **Production Incidents**: Reduce by 80% (from 10/month to 2/month)
- **Regression Bugs**: < 1 per release (from current 5 per release)
- **Bug Detection Time**: 95% caught in CI (before code review)

### Performance Metrics
- **Test Suite Speed**: < 15 minutes for full run
- **CI Feedback Time**: < 20 minutes from commit to result
- **Developer Confidence**: 90%+ confidence in deploy (survey)

---

## Out of Scope

- **Unit Tests**: This feature focuses on E2E only (unit tests separate effort)
- **Load Testing**: Performance budgets only, not stress testing (separate feature)
- **Accessibility Testing**: Basic coverage only, full WCAG audit separate
- **Mobile Native Apps**: Web browsers only, no iOS/Android apps
- **Internationalization**: English/Chinese only, no multi-language validation

---

## Technical Constraints

- **Playwright Version**: >= 1.40.0 (for latest features)
- **Node Version**: >= 18.0.0 (ES modules support)
- **Browser Versions**: Chrome 120+, Firefox 120+, Safari 17+
- **CI Platform**: GitHub Actions (can adapt for GitLab/Jenkins)
- **Test Environment**: Staging + Production (read-only)

---

## Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Test flakiness degrades CI reliability | High | Medium | Implement automatic flake detection, quarantine, and retry logic |
| Production tests cause data corruption | Critical | Low | Use read-only queries, separate test accounts, transaction rollbacks |
| Slow tests block deployment velocity | High | High | Parallelize tests, optimize selectors, use smart test selection |
| Cross-browser failures increase maintenance | Medium | Medium | Use abstraction layers, conditional logic for browser quirks |
| Test data setup becomes bottleneck | Medium | Medium | Create test data factories, database snapshots, mock APIs |

---

## Dependencies

- Playwright test framework installed and configured
- Test environments (staging/production) accessible
- CI/CD pipeline with test stage
- Monitoring system for test result tracking
- Test data management strategy

---

## Acceptance Criteria (Feature Complete)

- [ ] All 10 uncovered modules have E2E tests (Article Import, List, Review, Tasks, Comparison, Worklist, Schedule, Tags, Proofreading Rules, Stats)
- [ ] Edge cases covered: network errors, file upload failures, XSS/injection, race conditions
- [ ] Cross-browser tests run on Chrome, Firefox, Safari with 100% pass rate
- [ ] Performance budgets enforced: LCP < 2.5s, FID < 100ms, CLS < 0.1
- [ ] Full E2E workflow tests: Import → SEO → Proofreading → Publish
- [ ] CI pipeline runs tests automatically on all PRs
- [ ] Test suite completes in < 15 minutes
- [ ] Flake rate < 5% with automatic quarantine
- [ ] Test documentation complete with runbooks
- [ ] Production smoke tests run every hour with alerts

---

## Related Documents

- `PLAYWRIGHT_TEST_COVERAGE_ANALYSIS.md` - Detailed coverage analysis
- `plan.md` - Implementation strategy
- `tasks.md` - Detailed task breakdown
- `specs/001-cms-automation/spec.md` - Core feature being tested
- `specs/002-ui-modernization/spec.md` - UI features being tested
