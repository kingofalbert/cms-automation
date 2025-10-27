# Google Drive Integration Guide

## Overview

The CMS Automation system uses Google Drive as the primary file storage backend for uploaded images and documents. This guide covers setup, configuration, and usage of the Google Drive integration.

## Features

- 🔐 **Service Account Authentication**: Server-to-server access without user interaction
- ☁️ **Cloud Storage**: All files stored in Google Drive with public access links
- 📊 **Database Tracking**: Complete file metadata tracked in PostgreSQL
- 🔄 **CRUD Operations**: Full upload, download, list, and delete functionality
- 🖼️ **Image Support**: Optimized for article images and media files
- 📁 **Folder Organization**: Configurable folder structure in Google Drive

## Architecture

```
┌─────────────┐      ┌──────────────┐      ┌──────────────┐
│   FastAPI   │─────▶│  PostgreSQL  │      │ Google Drive │
│   Backend   │      │  (metadata)  │      │   (files)    │
└─────────────┘      └──────────────┘      └──────────────┘
      │                      │                      │
      │              ┌───────▼──────────────────────▼───┐
      └─────────────▶│  GoogleDriveStorage Service    │
                     └────────────────────────────────┘
```

### Data Flow

1. **Upload**: File uploaded via API → Saved to Google Drive → Metadata saved to `uploaded_files` table
2. **Retrieve**: File metadata queried from DB → Public URL returned (or file downloaded from Drive)
3. **Delete**: Soft delete (mark as deleted) OR hard delete (remove from Drive + DB)

## Setup Guide

### 1. Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing project
3. Note your **Project ID**

### 2. Enable Google Drive API

```bash
# Navigate to APIs & Services > Library
# Search for "Google Drive API"
# Click "Enable"
```

Or use gcloud CLI:

```bash
gcloud services enable drive.googleapis.com --project=YOUR_PROJECT_ID
```

### 3. Create Service Account

1. Navigate to **IAM & Admin > Service Accounts**
2. Click **Create Service Account**
3. Fill in details:
   - **Name**: `cms-automation-drive-service`
   - **Description**: `Service account for CMS automation Google Drive access`
4. Click **Create and Continue**
5. Skip role assignment (we'll use folder-level permissions)
6. Click **Done**

### 4. Generate Service Account Key

1. Click on the created service account
2. Go to **Keys** tab
3. Click **Add Key > Create New Key**
4. Select **JSON** format
5. Click **Create**
6. Save the downloaded JSON file securely

**Important**: Store this key securely. It provides access to Google Drive.

Example key structure:
```json
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "...",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "cms-automation-drive-service@your-project-id.iam.gserviceaccount.com",
  "client_id": "...",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "..."
}
```

### 5. Create Google Drive Folder

1. Open [Google Drive](https://drive.google.com/)
2. Create a new folder (e.g., "CMS Automation Files")
3. Right-click the folder → **Share**
4. Add the service account email (from JSON key: `client_email`)
5. Give it **Editor** permission
6. Click **Share**

**Get Folder ID**:
- Open the folder in Google Drive
- Copy the folder ID from the URL:
  ```
  https://drive.google.com/drive/folders/1a2b3c4d5e6f7g8h9i0j
                                        └────────────────┘
                                           Folder ID
  ```

### 6. Configure Backend

Place the service account JSON key file in your project:

```bash
# Create credentials directory
mkdir -p /path/to/CMS/backend/credentials

# Copy the downloaded JSON file
cp ~/Downloads/your-service-account-key.json \
   /path/to/CMS/backend/credentials/google-drive-credentials.json

# Secure the file (important!)
chmod 600 /path/to/CMS/backend/credentials/google-drive-credentials.json
```

Update `.env` file:

```bash
# Google Drive Storage Configuration
GOOGLE_DRIVE_CREDENTIALS_PATH=/app/credentials/google-drive-credentials.json
GOOGLE_DRIVE_FOLDER_ID=1a2b3c4d5e6f7g8h9i0j
```

**Docker Volume Mount**:

Ensure your `docker-compose.yml` mounts the credentials:

```yaml
services:
  backend:
    volumes:
      - ./backend:/app
      - ./backend/credentials:/app/credentials  # Add this line
```

### 7. Verify Configuration

Test the Google Drive connection:

```bash
# Start the backend
docker compose up -d backend

# Check logs for Google Drive initialization
docker compose logs backend | grep google_drive

# Expected output:
# google_drive_service_initialized
```

## API Reference

### Upload Single File

**Endpoint**: `POST /v1/files/upload`

**Request** (multipart/form-data):
```bash
curl -X POST http://localhost:8000/v1/files/upload \
  -F "file=@/path/to/image.jpg" \
  -F "article_id=42" \
  -F "file_type=image"
```

**Parameters**:
- `file` (required): File to upload
- `article_id` (optional): Associated article ID
- `file_type` (optional): `image`, `document`, `video`, or `other` (auto-detected if not provided)
- `folder_id` (optional): Custom Google Drive folder ID (uses default if not provided)

**Response** (201 Created):
```json
{
  "file_id": 123,
  "drive_file_id": "1xyz...",
  "filename": "image.jpg",
  "file_type": "image",
  "mime_type": "image/jpeg",
  "file_size": 245678,
  "web_view_link": "https://drive.google.com/file/d/1xyz.../view",
  "web_content_link": "https://drive.google.com/uc?id=1xyz...&export=download",
  "public_url": "https://drive.google.com/uc?id=1xyz...&export=download",
  "article_id": 42,
  "created_at": "2025-10-26T21:30:00Z"
}
```

### Upload Multiple Files

**Endpoint**: `POST /v1/files/upload-bulk`

**Request**:
```bash
curl -X POST http://localhost:8000/v1/files/upload-bulk \
  -F "files=@image1.jpg" \
  -F "files=@image2.png" \
  -F "files=@document.pdf" \
  -F "article_id=42"
```

**Response** (201 Created):
```json
{
  "successful_uploads": [
    {
      "file_id": 124,
      "drive_file_id": "1abc...",
      "filename": "image1.jpg",
      "file_type": "image",
      ...
    },
    {
      "file_id": 125,
      "drive_file_id": "1def...",
      "filename": "image2.png",
      "file_type": "image",
      ...
    }
  ],
  "failed_uploads": [
    {
      "filename": "document.pdf",
      "error": "Invalid file format"
    }
  ],
  "total_uploaded": 2,
  "total_failed": 1
}
```

### Get File Metadata

**Endpoint**: `GET /v1/files/{file_id}`

**Request**:
```bash
curl http://localhost:8000/v1/files/123
```

**Response** (200 OK):
```json
{
  "file_id": 123,
  "filename": "image.jpg",
  "drive_file_id": "1xyz...",
  "drive_folder_id": "1folder...",
  "mime_type": "image/jpeg",
  "file_size": 245678,
  "file_type": "image",
  "web_view_link": "https://drive.google.com/file/d/1xyz.../view",
  "web_content_link": "https://drive.google.com/uc?id=1xyz...&export=download",
  "public_url": "https://drive.google.com/uc?id=1xyz...&export=download",
  "article_id": 42,
  "uploaded_by": null,
  "file_metadata": {
    "original_mime_type": "image/jpeg",
    "upload_size_bytes": 245678
  },
  "created_at": "2025-10-26T21:30:00Z",
  "updated_at": "2025-10-26T21:30:00Z"
}
```

### List Files

**Endpoint**: `GET /v1/files/`

**Query Parameters**:
- `page` (default: 1): Page number
- `page_size` (default: 50, max: 100): Files per page
- `article_id` (optional): Filter by article ID
- `file_type` (optional): Filter by type (`image`, `document`, `video`, `other`)

**Request**:
```bash
# List all files
curl http://localhost:8000/v1/files/

# Filter by article
curl http://localhost:8000/v1/files/?article_id=42

# Filter by type with pagination
curl "http://localhost:8000/v1/files/?file_type=image&page=1&page_size=20"
```

**Response** (200 OK):
```json
{
  "files": [
    {
      "file_id": 123,
      "filename": "image.jpg",
      ...
    }
  ],
  "total": 150,
  "page": 1,
  "page_size": 50
}
```

### Delete File

**Endpoint**: `DELETE /v1/files/{file_id}`

**Query Parameters**:
- `hard_delete` (default: false): If true, permanently delete from Google Drive; if false, soft delete

**Request**:
```bash
# Soft delete (mark as deleted in DB)
curl -X DELETE http://localhost:8000/v1/files/123

# Hard delete (remove from Google Drive + DB)
curl -X DELETE "http://localhost:8000/v1/files/123?hard_delete=true"
```

**Response** (200 OK):
```json
{
  "file_id": 123,
  "drive_file_id": "1xyz...",
  "deleted": true,
  "message": "File 123 soft deleted (marked as deleted)"
}
```

## Integration Examples

### Python Example

```python
import requests

BASE_URL = "http://localhost:8000"

# Upload an image
def upload_image(file_path: str, article_id: int = None):
    with open(file_path, "rb") as f:
        files = {"file": f}
        data = {}
        if article_id:
            data["article_id"] = article_id

        response = requests.post(
            f"{BASE_URL}/v1/files/upload",
            files=files,
            data=data
        )
        response.raise_for_status()
        return response.json()

# Upload image and get public URL
result = upload_image("featured-image.jpg", article_id=42)
print(f"Public URL: {result['public_url']}")
print(f"File ID: {result['file_id']}")
```

### JavaScript Example

```javascript
// Upload file from browser
async function uploadFile(file, articleId = null) {
  const formData = new FormData();
  formData.append('file', file);
  if (articleId) {
    formData.append('article_id', articleId);
  }

  const response = await fetch('http://localhost:8000/v1/files/upload', {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`Upload failed: ${response.statusText}`);
  }

  return await response.json();
}

// Usage
const fileInput = document.querySelector('input[type="file"]');
const file = fileInput.files[0];
const result = await uploadFile(file, 42);
console.log('Public URL:', result.public_url);
```

### Bash/cURL Example

```bash
#!/bin/bash

# Upload all images in a directory
for image in images/*.jpg; do
  echo "Uploading: $image"

  response=$(curl -s -X POST http://localhost:8000/v1/files/upload \
    -F "file=@$image" \
    -F "article_id=42")

  file_id=$(echo $response | jq -r '.file_id')
  public_url=$(echo $response | jq -r '.public_url')

  echo "  File ID: $file_id"
  echo "  URL: $public_url"
  echo ""
done
```

## Database Schema

### `uploaded_files` Table

```sql
CREATE TABLE uploaded_files (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    drive_file_id VARCHAR(255) NOT NULL UNIQUE,
    drive_folder_id VARCHAR(255),
    mime_type VARCHAR(100) NOT NULL,
    file_size BIGINT,
    web_view_link TEXT,
    web_content_link TEXT,
    article_id INTEGER REFERENCES articles(id) ON DELETE CASCADE,
    file_type VARCHAR(50) NOT NULL,  -- image, document, video, other
    uploaded_by INTEGER,
    file_metadata JSONB,
    deleted_at TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX ix_uploaded_files_article_id ON uploaded_files(article_id);
CREATE UNIQUE INDEX ix_uploaded_files_drive_file_id ON uploaded_files(drive_file_id);
CREATE INDEX ix_uploaded_files_file_type ON uploaded_files(file_type);
```

### Query Examples

```sql
-- Get all images for an article
SELECT * FROM uploaded_files
WHERE article_id = 42 AND file_type = 'image'
ORDER BY created_at DESC;

-- Count files by type
SELECT file_type, COUNT(*) as count
FROM uploaded_files
WHERE deleted_at IS NULL
GROUP BY file_type;

-- Find large files (> 10MB)
SELECT filename, file_size, file_size / 1024 / 1024 AS size_mb
FROM uploaded_files
WHERE file_size > 10485760
ORDER BY file_size DESC;

-- Get recently uploaded files
SELECT filename, file_type, created_at
FROM uploaded_files
WHERE deleted_at IS NULL
  AND created_at > NOW() - INTERVAL '7 days'
ORDER BY created_at DESC
LIMIT 20;
```

## Security Considerations

### 1. Service Account Key Protection

**DO**:
- Store key file outside web-accessible directories
- Set file permissions to `600` (read/write for owner only)
- Never commit key file to version control
- Add to `.gitignore`: `credentials/*.json`
- Use environment variables for paths
- Rotate keys periodically (every 90 days recommended)

**DON'T**:
- Hardcode keys in source code
- Share keys via email or chat
- Store keys in public repositories
- Use personal Google accounts for service accounts

### 2. Folder Permissions

- Use **Editor** permission for service account (not Owner)
- Create dedicated folder for CMS files only
- Don't share folder publicly
- Service account access should be folder-specific, not Drive-wide

### 3. File Access Control

- Files are made publicly accessible via `public_url`
- If sensitive data: disable public access in `GoogleDriveStorage._make_public()`
- Implement access control at application level
- Use soft deletes to maintain audit trail

### 4. API Security

- Implement authentication/authorization on file upload endpoints
- Validate file types and sizes
- Sanitize filenames
- Rate limit upload endpoints
- Monitor upload activity

## Performance Optimization

### Upload Performance

**Concurrent Uploads**:
```python
import asyncio

async def upload_multiple_files(files: list[str]):
    storage = await create_google_drive_storage()

    tasks = [
        storage.upload_file_from_path(file_path)
        for file_path in files
    ]

    return await asyncio.gather(*tasks)
```

**Recommended Limits**:
- Max file size: 100MB per file
- Max concurrent uploads: 10
- Bulk upload batch size: 50 files

### Storage Quotas

Google Drive quotas (with service account):
- **15 GB free** per Google Workspace account
- Shared across all files in Drive
- Monitor usage: [Google Drive Storage](https://drive.google.com/settings/storage)

**Monitor storage usage**:
```bash
# Count total files
docker compose exec postgres psql -U cms_user -d cms_automation \
  -c "SELECT COUNT(*) FROM uploaded_files WHERE deleted_at IS NULL;"

# Calculate total storage used
docker compose exec postgres psql -U cms_user -d cms_automation \
  -c "SELECT SUM(file_size) / 1024 / 1024 / 1024 AS total_gb FROM uploaded_files WHERE deleted_at IS NULL;"
```

## Troubleshooting

### Error: "Google Drive credentials not found"

**Problem**: Backend can't find service account key file

**Solution**:
1. Check `GOOGLE_DRIVE_CREDENTIALS_PATH` in `.env`
2. Verify file exists at specified path
3. Check Docker volume mount includes credentials directory
4. Verify file permissions

```bash
# Check if file exists in container
docker compose exec backend ls -la /app/credentials/

# Expected output:
# -rw------- 1 root root 2345 Oct 26 21:00 google-drive-credentials.json
```

### Error: "Permission denied" when uploading

**Problem**: Service account doesn't have access to folder

**Solution**:
1. Open Google Drive folder
2. Click **Share**
3. Add service account email (from JSON key: `client_email`)
4. Grant **Editor** permission
5. Click **Share**

### Error: "File upload failed: API rate limit exceeded"

**Problem**: Too many requests to Google Drive API

**Solution**:
- Reduce concurrent uploads
- Implement exponential backoff retry logic
- Use bulk upload for multiple files
- Request quota increase: [Google Cloud Console](https://console.cloud.google.com/apis/api/drive.googleapis.com/quotas)

### Error: "Invalid folder ID"

**Problem**: Wrong folder ID in configuration

**Solution**:
1. Open folder in Google Drive
2. Copy folder ID from URL: `https://drive.google.com/drive/folders/FOLDER_ID_HERE`
3. Update `GOOGLE_DRIVE_FOLDER_ID` in `.env`
4. Restart backend: `docker compose restart backend`

### Files not publicly accessible

**Problem**: Public URLs return "Access Denied"

**Solution**:
1. Check if `_make_public()` method is being called
2. Verify service account has permission to change file permissions
3. Manually make file public:
   - Right-click file in Drive
   - Click **Share**
   - Change to "Anyone with the link"
   - Set access to "Viewer"

## Best Practices

1. **Organize Files by Type**:
   ```python
   # Use different folders for different file types
   image_folder_id = "1abc..."
   document_folder_id = "1def..."

   storage.upload_file(
       file_content=image_data,
       filename="image.jpg",
       mime_type="image/jpeg",
       folder_id=image_folder_id  # Organized by type
   )
   ```

2. **Use Descriptive Filenames**:
   ```python
   # Good: descriptive, unique
   filename = f"article-{article_id}-featured-{timestamp}.jpg"

   # Bad: generic, collision-prone
   filename = "image.jpg"
   ```

3. **Track File Usage**:
   ```python
   # Associate files with articles
   uploaded_file.article_id = article_id

   # Track uploader
   uploaded_file.uploaded_by = user_id

   # Add context in metadata
   uploaded_file.file_metadata = {
       "purpose": "featured_image",
       "article_title": "How to Use Google Drive",
       "upload_source": "article_import"
   }
   ```

4. **Clean Up Unused Files**:
   ```sql
   -- Find orphaned files (no associated article)
   SELECT * FROM uploaded_files
   WHERE article_id IS NULL
     AND created_at < NOW() - INTERVAL '30 days';

   -- Soft delete old files
   UPDATE uploaded_files
   SET deleted_at = NOW()
   WHERE article_id IS NULL
     AND created_at < NOW() - INTERVAL '90 days';
   ```

5. **Monitor Storage Costs**:
   - Implement file retention policies
   - Compress images before upload
   - Use appropriate image formats (WebP > JPEG > PNG for photos)
   - Delete unused files regularly

## Migration from Local Storage

If you're migrating from local filesystem storage:

```python
import os
from pathlib import Path

async def migrate_local_to_drive():
    """Migrate local files to Google Drive."""
    storage = await create_google_drive_storage()
    local_files_dir = Path("/path/to/local/files")

    for file_path in local_files_dir.rglob("*"):
        if file_path.is_file():
            print(f"Uploading: {file_path}")

            # Upload to Drive
            result = await storage.upload_file_from_path(str(file_path))

            # Create database record
            uploaded_file = UploadedFile(
                filename=file_path.name,
                drive_file_id=result["id"],
                mime_type=result.get("mimeType"),
                file_size=file_path.stat().st_size,
                web_view_link=result.get("webViewLink"),
                web_content_link=result.get("webContentLink"),
                file_type=classify_file_type(result.get("mimeType")),
            )
            session.add(uploaded_file)

            # Optional: delete local file after successful upload
            # file_path.unlink()

    await session.commit()
    print("Migration complete!")
```

## See Also

- [Google Drive API Documentation](https://developers.google.com/drive/api/guides/about-sdk)
- [Service Account Authentication](https://developers.google.com/identity/protocols/oauth2/service-account)
- [Article Import Guide](article_import_guide.md)
- [SEO Analysis Integration Guide](seo_analysis_integration_guide.md)
- [API Documentation](http://localhost:8000/docs)
