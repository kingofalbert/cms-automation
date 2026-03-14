# Known Issues Suppression List

Issues listed here are known and tracked. The log analysis pipeline will filter
these out to reduce noise and focus on new/unexpected problems.

## Format

Each entry has:
- **Pattern**: regex or substring to match in log event/error fields
- **Category**: error | warning | infra
- **Status**: accepted | mitigating | wontfix
- **Notes**: why this is suppressed

---

## Active Suppressions

### 1. Redis unreachable from Cloud Run

- **Pattern**: `Error -3 connecting to redis:6379`
- **Category**: infra
- **Status**: resolved
- **First seen**: 2026-03-01
- **Resolved**: 2026-03-10 (commit `9c7307e` — Celery/Redis removed from codebase)
- **Notes**: No longer applicable. Redis and Celery were fully removed.

### 2. Celery status check failures (consequence of #1)

- **Pattern**: `celery_status_check_failed`
- **Category**: warning
- **Status**: resolved
- **First seen**: 2026-03-01
- **Resolved**: 2026-03-10 (commit `9c7307e` — Celery/Redis removed from codebase)
- **Notes**: No longer applicable. Celery health check code was removed.

### 3. Worklist sync 504 timeout

- **Pattern**: `httpRequest.status=504 AND requestUrl=~/v1/worklist/sync`
- **Category**: error
- **Status**: mitigating
- **First seen**: 2026-03-05
- **Notes**: The `/v1/worklist/sync` endpoint (triggered by Cloud Scheduler)
  hits the 300-second Cloud Run timeout. The sync operation needs to be
  chunked or moved to a background task. Track as P2.

### 4. Google Drive sync item failures (exportSizeLimitExceeded)

- **Pattern**: `google_drive_sync_item_failed`, `exportSizeLimitExceeded`
- **Category**: warning
- **Status**: mitigating
- **First seen**: 2026-03-08
- **Updated**: 2026-03-14
- **Notes**: 4 specific Google Docs exceed the 10MB HTML export limit. Fix
  (commit `4911a90`) downgraded to WARNING and added early exit, but docs are
  still attempted each sync cycle (~2700 warnings/day estimated at current sync
  frequency). Fully resolving requires a persistent skip list for known oversized
  files.

### 5. Celery retry limit exhausted (CRITICAL)

- **Pattern**: `Retry limit exceeded while trying to reconnect`
- **Category**: infra
- **Status**: resolved
- **First seen**: 2026-03-10
- **Resolved**: 2026-03-10 (commit `9c7307e` — Celery/Redis removed from codebase)
- **Notes**: No longer applicable. Celery was fully removed.

### 6. QueuePool exhaustion during worklist sync (connection contention)

- **Pattern**: `QueuePool limit of size .* overflow .* reached`, `TimeoutError`
- **Category**: error
- **Status**: resolved
- **First seen**: 2026-03-13
- **Resolved**: 2026-03-14 (commit `6465c2f` deployed as revision `00082-zbp`)
- **Notes**: Fix deployed: sync-in-progress guard, pool timeout catch in status
  endpoint, TimeoutError retry, asyncio.create_task for sync, pool_size=3,
  max_overflow=2. Post-reinit at 15:10 UTC on 3/14: 1 error vs 35 pre-reinit.
  Pool settings only take effect after instance recycles (DatabaseConfig singleton).

### 7. Playwright publish failures (WordPress title selector timeout)

- **Pattern**: `playwright_publish_failed`, `wait_for_selector.*editor-post-title`
- **Category**: error
- **Status**: mitigating
- **First seen**: 2026-03-14
- **Notes**: 10/10 publish attempts failed with title field selector timeout
  (03:31-06:20 UTC). WordPress editor page not loading — likely `ping.xie`
  password incorrect or WordPress admin unreachable. Requires human intervention
  to reset WordPress credentials. 6 related SEO configuration failures
  (`seo_configuration_failed`) for Yoast metabox selector also observed.

### 8. Stuck pipeline tasks (no stale task reaper)

- **Pattern**: `status=processing` tasks polled indefinitely
- **Category**: error
- **Status**: mitigating
- **First seen**: 2026-03-13
- **Updated**: 2026-03-14
- **Notes**: 3 tasks stuck in "processing": `5f585d9d`, `36c52b48` (from 3/13,
  24+ hours), `1557fe38` (new 3/14). GAS polls every 5 min with no max retry,
  generating ~288 API calls/day per stuck task. Needs stale task reaper
  (architectural decision) to mark tasks older than 30 min as failed.

---

## How to Add New Entries

When the log analysis identifies a recurring issue that has been triaged and
accepted (or is being worked on), add it here with the fields above. This
prevents the same issue from appearing as "new" in every daily report.

## How to Remove Entries

When the root cause is fixed and the issue no longer appears in logs for 7
consecutive days, remove the entry from this file and note the resolution
date in a comment.
