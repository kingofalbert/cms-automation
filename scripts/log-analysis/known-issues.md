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
- **Status**: accepted
- **First seen**: 2026-03-01
- **Notes**: Cloud Run cannot reach the Redis instance because there is no
  VPC connector configured. Celery status checks fail on every poll. This is
  expected until a Serverless VPC Access connector or Redis Memorystore with
  direct VPC is provisioned.

### 2. Celery status check failures (consequence of #1)

- **Pattern**: `celery_status_check_failed`
- **Category**: warning
- **Status**: accepted
- **First seen**: 2026-03-01
- **Notes**: Direct consequence of Redis being unreachable. Will resolve when
  Redis connectivity is fixed.

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
- **Category**: error
- **Status**: fixed (merged to main 2026-03-10, commit `4911a90`)
- **First seen**: 2026-03-08
- **Updated**: 2026-03-10
- **Notes**: 4 specific Google Docs exceed the 10MB HTML export limit. This is
  a PERMANENT condition (not transient). Each 5-minute sync cycle retries these
  docs, generating ~65 errors and ~73 warnings per day. Auto-fix adds early
  exit on exportSizeLimitExceeded to skip these documents immediately.

### 5. Celery retry limit exhausted (CRITICAL)

- **Pattern**: `Retry limit exceeded while trying to reconnect`
- **Category**: infra
- **Status**: accepted
- **First seen**: 2026-03-10
- **Notes**: Consequence of Redis being unreachable (#1). Celery backend
  permanently stops reconnection attempts after exhausting retries. Generates
  CRITICAL-level log entries. Will resolve when Redis connectivity is fixed.

---

## How to Add New Entries

When the log analysis identifies a recurring issue that has been triaged and
accepted (or is being worked on), add it here with the fields above. This
prevents the same issue from appearing as "new" in every daily report.

## How to Remove Entries

When the root cause is fixed and the issue no longer appears in logs for 7
consecutive days, remove the entry from this file and note the resolution
date in a comment.
