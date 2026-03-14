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
- **Updated**: 2026-03-13
- **Notes**: 4 specific Google Docs exceed the 10MB HTML export limit. Fix
  (commit `4911a90`) downgraded to WARNING and added early exit, but docs are
  still attempted each sync cycle (~100 warnings/day). Fully resolving requires
  a persistent skip list for known oversized files.

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
- **Status**: mitigating
- **First seen**: 2026-03-13
- **Notes**: Long-lived DB sessions held during AI pipeline processing (2-5 min
  per document) starve short-lived queries (status polls, upserts). Fix applied
  in worktree branch `worktree-agent-a98b56c4`: sync-in-progress guard, pool
  timeout catch in status endpoint, TimeoutError retry, asyncio.create_task for
  sync. Needs deploy to take effect.

---

## How to Add New Entries

When the log analysis identifies a recurring issue that has been triaged and
accepted (or is being worked on), add it here with the fields above. This
prevents the same issue from appearing as "new" in every daily report.

## How to Remove Entries

When the root cause is fixed and the issue no longer appears in logs for 7
consecutive days, remove the entry from this file and note the resolution
date in a comment.
