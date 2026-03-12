# Cloud Run Log Access Reference

## Project Details

| Field | Value |
|-------|-------|
| Project ID | `cmsupload-476323` |
| Service | `cms-automation-backend` |
| Region | `us-east1` |
| Latest Revision | `cms-automation-backend-00044-llr` |
| Service URL | `https://cms-automation-backend-297291472291.us-east1.run.app` |
| GCP Account | `albert.king@epochtimes.nyc` |

## Prerequisites

Before querying logs, ensure the correct account and project are active:

```bash
gcloud config set account albert.king@epochtimes.nyc
gcloud config set project cmsupload-476323
```

---

## Method 1: gcloud logging read (Primary CLI Method)

This is the most reliable and flexible method. It queries Cloud Logging directly.

### Basic query (most recent logs)

```bash
gcloud logging read \
  "resource.type=cloud_run_revision AND resource.labels.service_name=cms-automation-backend" \
  --project=cmsupload-476323 \
  --limit=20 \
  --format=json
```

### Filter by severity (HTTP-level errors: 5xx, timeouts)

```bash
gcloud logging read \
  "resource.type=cloud_run_revision AND resource.labels.service_name=cms-automation-backend AND severity>=ERROR" \
  --project=cmsupload-476323 \
  --limit=10 \
  --format=json
```

### Filter by application-level log level (jsonPayload)

The application emits structured JSON logs with a `level` field. This is different from the Cloud Logging `severity` field.

```bash
# Application errors (Python logger)
gcloud logging read \
  "resource.type=cloud_run_revision AND resource.labels.service_name=cms-automation-backend AND jsonPayload.level=error" \
  --project=cmsupload-476323 \
  --limit=10 \
  --format="table(timestamp,jsonPayload.event,jsonPayload.level,jsonPayload.logger)"

# Application warnings
gcloud logging read \
  "resource.type=cloud_run_revision AND resource.labels.service_name=cms-automation-backend AND jsonPayload.level=warning" \
  --project=cmsupload-476323 \
  --limit=10 \
  --format="table(timestamp,jsonPayload.event,jsonPayload.logger)"
```

### Filter by specific event name

```bash
gcloud logging read \
  "resource.type=cloud_run_revision AND resource.labels.service_name=cms-automation-backend AND jsonPayload.event=\"celery_status_check_failed\"" \
  --project=cmsupload-476323 \
  --limit=10 \
  --format=json
```

### Filter by time range

```bash
# Last 1 hour
gcloud logging read \
  "resource.type=cloud_run_revision AND resource.labels.service_name=cms-automation-backend AND timestamp>=\"$(date -u -v-1H '+%Y-%m-%dT%H:%M:%SZ')\"" \
  --project=cmsupload-476323 \
  --limit=50 \
  --format=json

# Specific time window
gcloud logging read \
  "resource.type=cloud_run_revision AND resource.labels.service_name=cms-automation-backend AND timestamp>=\"2026-03-10T07:00:00Z\" AND timestamp<=\"2026-03-10T08:00:00Z\"" \
  --project=cmsupload-476323 \
  --limit=100 \
  --format=json
```

### Filter by HTTP request path

```bash
gcloud logging read \
  "resource.type=cloud_run_revision AND resource.labels.service_name=cms-automation-backend AND jsonPayload.path=\"/v1/pipeline/auto-publish\"" \
  --project=cmsupload-476323 \
  --limit=10 \
  --format=json
```

### Filter by HTTP status code (from request logs)

```bash
gcloud logging read \
  "resource.type=cloud_run_revision AND resource.labels.service_name=cms-automation-backend AND httpRequest.status>=500" \
  --project=cmsupload-476323 \
  --limit=10 \
  --format=json
```

### Compact table output formats

```bash
# Application logs - compact view
gcloud logging read \
  "resource.type=cloud_run_revision AND resource.labels.service_name=cms-automation-backend AND jsonPayload.event!=\"\"" \
  --project=cmsupload-476323 \
  --limit=20 \
  --format="table(timestamp,jsonPayload.level,jsonPayload.event,jsonPayload.logger)"

# HTTP request logs - compact view
gcloud logging read \
  "resource.type=cloud_run_revision AND resource.labels.service_name=cms-automation-backend AND httpRequest.requestUrl!=\"\"" \
  --project=cmsupload-476323 \
  --limit=20 \
  --format="table(timestamp,httpRequest.status,httpRequest.requestMethod,httpRequest.requestUrl,httpRequest.latency)"
```

---

## Method 2: gcloud run services logs (NOT working)

The `gcloud run services logs read` command exists but is currently broken in gcloud CLI 543.0.0 (crashes with a TypeError). Avoid this method until a fix is released.

```bash
# DO NOT USE - crashes with TypeError
gcloud run services logs read cms-automation-backend --project=cmsupload-476323 --region=us-east1 --limit=5
```

---

## Method 3: Google Cloud Console (Web UI)

Navigate directly to the logs in browser:

- **Cloud Run logs**: https://console.cloud.google.com/run/detail/us-east1/cms-automation-backend/logs?project=cmsupload-476323
- **Cloud Logging (Logs Explorer)**: https://console.cloud.google.com/logs/query;query=resource.type%3D%22cloud_run_revision%22%0Aresource.labels.service_name%3D%22cms-automation-backend%22?project=cmsupload-476323

---

## Method 4: Programmatic Access (Python)

Use the `google-cloud-logging` Python library:

```python
from google.cloud import logging as cloud_logging

client = cloud_logging.Client(project="cmsupload-476323")

filter_str = (
    'resource.type="cloud_run_revision" '
    'AND resource.labels.service_name="cms-automation-backend" '
    'AND severity>=ERROR'
)

for entry in client.list_entries(filter_=filter_str, max_results=10):
    print(f"{entry.timestamp} | {entry.severity} | {entry.payload}")
```

---

## Log Format Documentation

The service emits two types of log entries:

### Type 1: Application Logs (jsonPayload)

These come from the Python application's structured logger (via structlog/uvicorn) and are written to stdout.

**Log name**: `projects/cmsupload-476323/logs/run.googleapis.com%2Fstdout`

**Fields available in jsonPayload**:

| Field | Description | Example |
|-------|-------------|---------|
| `event` | Event name or message | `request_completed`, `celery_status_check_failed` |
| `level` | Application log level | `info`, `warning`, `error` |
| `logger` | Python logger name | `src.api.middleware.logging`, `uvicorn.access` |
| `timestamp` | Application-side timestamp | `2026-03-10T18:31:52.542996Z` |
| `method` | HTTP method (middleware logs) | `GET`, `POST` |
| `path` | Request path (middleware logs) | `/v1/pipeline/auto-publish/...` |
| `status_code` | Response status (middleware logs) | `200` |
| `duration_ms` | Request duration (middleware logs) | `21.33` |
| `request_id` | Correlation ID | `unknown` or UUID |
| `error` | Error message (on failures) | `Error -3 connecting to redis:6379...` |
| `task_id` | Celery task ID (pipeline logs) | UUID string |

### Type 2: HTTP Request Logs (httpRequest)

These are automatically generated by Cloud Run for every incoming HTTP request.

**Log name**: `projects/cmsupload-476323/logs/run.googleapis.com%2Frequests`

**Fields available in httpRequest**:

| Field | Description | Example |
|-------|-------------|---------|
| `requestMethod` | HTTP method | `GET`, `POST` |
| `requestUrl` | Full URL | `https://cms-automation-backend-297291472291.us-east1.run.app/v1/...` |
| `status` | HTTP status code | `200`, `504` |
| `latency` | Total request latency | `0.024830998s`, `300.000100303s` |
| `remoteIp` | Client IP | `34.98.143.75` |
| `userAgent` | Client user agent | `Google-Apps-Script`, `Mozilla/5.0` |
| `requestSize` | Request size in bytes | `1350` |
| `responseSize` | Response size in bytes | `298` |

**Additional metadata on request logs**:
- `severity`: Cloud Logging severity (e.g., `INFO`, `ERROR` for 5xx)
- `trace`: Distributed trace ID for correlating logs within a single request
- `spanId`: Span within the trace

### Resource Labels (on all log types)

| Label | Value |
|-------|-------|
| `service_name` | `cms-automation-backend` |
| `revision_name` | `cms-automation-backend-00044-llr` |
| `configuration_name` | `cms-automation-backend` |
| `location` | `us-east1` |
| `project_id` | `cmsupload-476323` |

---

## Current Infrastructure State

### Log Export Sinks

Only the default GCP sinks exist (no custom exports to BigQuery, Pub/Sub, or external systems):

| Sink | Destination | Purpose |
|------|-------------|---------|
| `_Required` | `_Required` bucket | Audit logs (mandatory, cannot be deleted) |
| `_Default` | `_Default` bucket | All other logs (30-day retention by default) |

### Monitoring

- **Dashboards**: None configured
- **Alert Policies**: Not checked (requires `gcloud alpha` component)
- **Uptime Checks**: Not verified

---

## Notable Observations from Current Logs

1. **Redis connectivity issue**: The Celery status check is failing because Redis is unreachable from Cloud Run (`Error -3 connecting to redis:6379. Temporary failure in name resolution.`). This is a recurring warning on every status poll.

2. **Worklist sync timeouts**: The `/v1/worklist/sync` endpoint (triggered by Google Cloud Scheduler) is hitting the 300-second Cloud Run timeout limit, resulting in HTTP 504 errors.

3. **Google Drive sync failures**: Application-level errors with events `google_drive_sync_item_failed` and `google_drive_fetch_failed` from the `src.services.google_drive.sync_service` logger.

4. **Google Apps Script polling**: The status endpoint is being polled by a Google Apps Script client (user agent: `Google-Apps-Script`).

---

## Useful Compound Queries

### Debug a specific auto-publish task by ID

```bash
TASK_ID="898e0b95-bb07-40f2-984b-a0631bb76dea"
gcloud logging read \
  "resource.type=cloud_run_revision AND resource.labels.service_name=cms-automation-backend AND jsonPayload.task_id=\"$TASK_ID\"" \
  --project=cmsupload-476323 \
  --limit=50 \
  --format=json
```

### All errors in the last 24 hours

```bash
gcloud logging read \
  "resource.type=cloud_run_revision AND resource.labels.service_name=cms-automation-backend AND (severity>=ERROR OR jsonPayload.level=error) AND timestamp>=\"$(date -u -v-24H '+%Y-%m-%dT%H:%M:%SZ')\"" \
  --project=cmsupload-476323 \
  --limit=100 \
  --format="table(timestamp,severity,jsonPayload.level,jsonPayload.event,jsonPayload.error)"
```

### Trace a single request end-to-end

```bash
TRACE_ID="a6640531ff8d06e0969e2a6699ab6427"
gcloud logging read \
  "resource.type=cloud_run_revision AND trace=\"projects/cmsupload-476323/traces/$TRACE_ID\"" \
  --project=cmsupload-476323 \
  --format=json
```

### Slow requests (latency > 10 seconds)

```bash
gcloud logging read \
  "resource.type=cloud_run_revision AND resource.labels.service_name=cms-automation-backend AND httpRequest.latency>\"10s\"" \
  --project=cmsupload-476323 \
  --limit=20 \
  --format="table(timestamp,httpRequest.status,httpRequest.latency,httpRequest.requestUrl)"
```
