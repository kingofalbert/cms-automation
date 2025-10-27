# Computer Use Publishing Integration Guide

## Overview

The Computer Use Publishing Integration enables automated article publishing to WordPress CMS using Claude's Computer Use API. This system automatically navigates WordPress, uploads images from Google Drive, configures SEO settings, and publishes articles.

## Architecture

### Components

1. **DriveImageRetriever** (`src/services/drive_image_retriever.py`)
   - Downloads article images from Google Drive to local temp directory
   - Manages temp file cleanup
   - Provides image metadata for Computer Use

2. **ComputerUseCMSService** (`src/services/computer_use_cms.py`)
   - Main service orchestrating Computer Use API
   - Builds detailed instructions for Claude
   - Manages publishing workflow
   - Handles screenshots and session tracking

3. **Celery Tasks** (`src/workers/tasks/computer_use_tasks.py`)
   - Async task for publishing articles
   - Integrates image download from Google Drive
   - Updates article status in database

4. **API Routes** (`src/api/routes/computer_use.py`)
   - `/v1/computer-use/publish` - Trigger publishing task
   - `/v1/computer-use/task/{task_id}` - Check task status
   - `/v1/computer-use/test-environment` - Verify Computer Use environment

### Database Models

#### PublishTask
Tracks Computer Use publishing tasks with:
- Provider selection (Anthropic, Gemini, Playwright)
- Task status (pending, running, completed, failed)
- Screenshots captured during publishing
- Cost tracking
- Retry logic

#### ExecutionLog
Detailed execution logs for Computer Use operations:
- Step-by-step action tracking
- Screenshot URLs
- Error messages
- Performance metrics

## Workflow

### 1. Article Publishing Flow

```
User API Request
    ↓
Celery Task Created
    ↓
DriveImageRetriever Downloads Images from Google Drive
    ↓
ComputerUseCMSService Builds Instructions
    ↓
Claude Computer Use Executes:
    - Navigate to WordPress
    - Login
    - Create Post
    - Upload Images to WordPress Media Library
    - Set Title & Content
    - Configure SEO (Yoast/Rank Math)
    - Publish
    ↓
Article Status Updated
    ↓
Temp Files Cleaned Up
```

### 2. Image Handling

Images stored in Google Drive are:
1. Downloaded to temp directory (`/tmp/cms_images_*`)
2. Provided to Computer Use with local file paths
3. Uploaded to WordPress media library by Claude
4. Referenced in article content
5. Temp files cleaned up after publishing

### 3. SEO Configuration

Computer Use automatically configures:
- Meta title
- Meta description
- Focus keyword
- Open Graph tags
- Canonical URL
- Schema markup (via Yoast SEO or Rank Math)

## API Usage

### Trigger Article Publishing

```bash
POST /v1/computer-use/publish
Content-Type: application/json

{
  "article_id": 123,
  "cms_url": "https://example.com",  # Optional, defaults to env var
  "cms_username": "admin",           # Optional, defaults to env var
  "cms_password": "app_password",    # Optional, defaults to env var
  "cms_type": "wordpress"
}
```

Response:
```json
{
  "task_id": "celery-task-id-12345",
  "message": "Computer Use publishing task started",
  "article_id": 123
}
```

### Check Task Status

```bash
GET /v1/computer-use/task/{task_id}
```

Response:
```json
{
  "task_id": "celery-task-id-12345",
  "status": "SUCCESS",
  "result": {
    "success": true,
    "cms_article_id": "456",
    "url": "https://example.com/article-slug",
    "metadata": {
      "session_id": "cu_1234567890",
      "screenshots": ["/screenshots/..."],
      "execution_time_seconds": 45.2
    }
  }
}
```

### Test Environment

```bash
POST /v1/computer-use/test-environment
```

Response:
```json
{
  "status": "ok",
  "checks": {
    "display": ":1",
    "vnc_running": true,
    "browser_available": true,
    "anthropic_api_key_set": true
  },
  "message": "All checks passed"
}
```

## Environment Setup

### Required Environment Variables

```bash
# Anthropic API
ANTHROPIC_API_KEY=sk-ant-...

# WordPress CMS
CMS_TYPE=wordpress
CMS_BASE_URL=https://your-wordpress-site.com
CMS_USERNAME=admin
CMS_APPLICATION_PASSWORD=xxxx xxxx xxxx xxxx

# Google Drive Storage
GOOGLE_DRIVE_CREDENTIALS_PATH=/app/credentials/google-drive-credentials.json
GOOGLE_DRIVE_FOLDER_ID=your-folder-id

# Database & Redis
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
```

### Docker Computer Use Environment

The system requires a special Docker container with:
- X11 virtual display (Xvfb)
- VNC server for remote viewing
- Chromium browser
- Window manager (Fluxbox)

Build with:
```bash
docker build -f Dockerfile.computer-use -t cms-computer-use .
```

Or use in docker-compose.yml:
```yaml
computer_use:
  build:
    context: ./backend
    dockerfile: Dockerfile.computer-use
  environment:
    DISPLAY: ":1"
    VNC_PORT: "5901"
    NOVNC_PORT: "6080"
    ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
  ports:
    - "5901:5901"  # VNC
    - "6080:6080"  # noVNC web interface
```

## Google Drive Integration

### Image Download Process

1. Query `uploaded_files` table for article images:
```sql
SELECT * FROM uploaded_files
WHERE article_id = ? AND file_type = 'image';
```

2. Download each image from Google Drive using `drive_file_id`

3. Save to temp directory with original filename

4. Provide local paths to Computer Use

5. Clean up temp files after publishing completes

### Image URL Replacement

The system handles two scenarios:

1. **Direct Drive URLs in article body**:
   - Pattern: `https://drive.google.com/file/d/{file_id}/...`
   - Replaced with WordPress media library URL after upload

2. **Markdown image references**:
   - Pattern: `![alt text](drive_file_id)`
   - Computer Use inserts uploaded WordPress media

## Computer Use Instructions

The system generates detailed step-by-step instructions for Claude:

### With Images:
1. Navigate to WordPress admin
2. Login
3. Create new post
4. Set article title
5. **Upload images to WordPress media library**
6. Add article content (with uploaded images)
7. Configure SEO settings
8. Publish article
9. Capture article URL and ID
10. Return results

### Without Images:
Steps 5-6 are simplified to just adding content.

## Error Handling

### Retry Logic

- Max retries: 3 (configurable)
- Retry delay: 5 minutes (300 seconds)
- Failed tasks are marked with error messages
- Execution logs capture detailed failure information

### Common Issues

1. **Google Drive Access Denied (403)**
   - Cause: Service account not added to Shared Drive
   - Solution: Add service account to Shared Drive with "Content Manager" role

2. **WordPress Login Failed**
   - Cause: Invalid credentials or application password
   - Solution: Verify CMS_USERNAME and CMS_APPLICATION_PASSWORD

3. **Browser/Display Not Available**
   - Cause: Computer Use container not properly configured
   - Solution: Run `/v1/computer-use/test-environment` to diagnose

4. **Image Upload Failed**
   - Cause: Image file not found in temp directory
   - Solution: Check DriveImageRetriever logs for download errors

## Monitoring

### Task Status Tracking

Monitor publishing tasks via PublishTask model:

```python
from src.models.publish import PublishTask

# Get task status
task = session.query(PublishTask).filter_by(id=task_id).first()
print(f"Status: {task.status}")
print(f"Duration: {task.duration_seconds}s")
print(f"Screenshots: {task.screenshot_count}")
print(f"Cost: ${task.cost_usd}")
```

### Execution Logs

View detailed execution logs:

```python
from src.models.publish import ExecutionLog

# Get logs for a task
logs = session.query(ExecutionLog).filter_by(task_id=task_id).all()
for log in logs:
    print(f"[{log.log_level}] {log.step_name}: {log.message}")
```

### VNC Remote Viewing

Connect to VNC server to watch Computer Use in action:

- VNC Client: `localhost:5901` (password: `vnc_password`)
- Web Browser (noVNC): `http://localhost:6080`

## Cost Optimization

### Provider Selection

1. **Playwright** (Free)
   - Uses Playwright automation
   - No AI model costs
   - Recommended for production

2. **Anthropic Computer Use** (Paid)
   - Uses Claude's Computer Use API
   - More intelligent error handling
   - Higher cost per publish

3. **Gemini** (Paid)
   - Alternative AI provider
   - Similar to Anthropic

### Cost Tracking

Each PublishTask tracks cost in USD:
```python
task.cost_usd  # Total cost for this publishing attempt
```

## Testing

### Manual Testing

1. Create article with images:
```bash
POST /v1/articles
{
  "title": "Test Article",
  "body": "Article content with images",
  "topic_id": 1
}
```

2. Upload images and associate with article:
```bash
POST /v1/files/upload
Form Data:
  file: image.jpg
  article_id: 123
  file_type: image
```

3. Trigger publishing:
```bash
POST /v1/computer-use/publish
{
  "article_id": 123
}
```

4. Monitor task:
```bash
GET /v1/computer-use/task/{task_id}
```

### Environment Test

```bash
curl -X POST http://localhost:8000/v1/computer-use/test-environment
```

Expected output:
```json
{
  "status": "ok",
  "checks": {
    "display": ":1",
    "vnc_running": true,
    "browser_available": true,
    "anthropic_api_key_set": true
  }
}
```

## Limitations

### Current Limitations

1. **Google Drive Shared Drive Required**
   - Service accounts cannot access personal "My Drive" folders
   - Must use Google Workspace Shared Drives
   - Or configure domain-wide delegation

2. **WordPress Only**
   - Currently only supports WordPress CMS
   - Other CMS platforms (Drupal, Strapi) not yet implemented

3. **Image Format Support**
   - Supports standard web image formats (JPG, PNG, GIF, WebP)
   - Video and other media types not yet supported

4. **Synchronous Publishing**
   - Each article published sequentially
   - Parallel publishing not currently supported

### Known Issues

1. **Temp File Cleanup**
   - If task crashes, temp files may not be cleaned up
   - Consider adding periodic cleanup job

2. **Screenshot Storage**
   - Screenshots currently stored in memory
   - Should implement Google Drive upload for screenshots

3. **Computer Use Runtime**
   - The `_execute_tool` method is currently simulated
   - Real Computer Use runtime integration needed for production

## Roadmap

### Planned Features

- [ ] Support for other CMS platforms (Drupal, Strapi)
- [ ] Video upload support
- [ ] Parallel article publishing
- [ ] Screenshot upload to Google Drive
- [ ] Real-time progress streaming via WebSockets
- [ ] Scheduled publishing
- [ ] A/B testing support

### Improvements

- [ ] Better error recovery
- [ ] Image optimization before upload
- [ ] Featured image auto-selection
- [ ] Category and tag auto-mapping
- [ ] Custom field support
- [ ] Multi-language support

## Troubleshooting

### Debug Mode

Enable detailed logging:

```python
import logging
logging.getLogger("src.services.computer_use_cms").setLevel(logging.DEBUG)
logging.getLogger("src.services.drive_image_retriever").setLevel(logging.DEBUG)
```

### Common Solutions

**Problem**: Images not uploading to WordPress

**Solution**:
1. Check Google Drive download succeeded
2. Verify temp files exist in `/tmp/cms_images_*`
3. Check WordPress media upload permissions
4. Review Computer Use screenshots for errors

**Problem**: Task stuck in "running" status

**Solution**:
1. Check Celery worker logs
2. Verify VNC/display server running
3. Test browser availability
4. Check Anthropic API rate limits

**Problem**: SEO not configured

**Solution**:
1. Verify Yoast SEO or Rank Math plugin installed
2. Check plugin is activated
3. Review Computer Use screenshots to see if SEO fields were found

## Support

For issues or questions:
1. Check execution logs in database
2. Review screenshots via VNC
3. Test environment with `/v1/computer-use/test-environment`
4. Check Celery worker logs
5. Review this documentation

## References

- [Anthropic Computer Use API](https://docs.anthropic.com/claude/docs/computer-use)
- [Google Drive API](https://developers.google.com/drive/api/v3/about-sdk)
- [WordPress REST API](https://developer.wordpress.org/rest-api/)
- [Celery Documentation](https://docs.celeryproject.org/)
