# cms_automation Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-10-25

## Active Technologies
- TypeScript 5.x + React 18 (002-ui-modernization)
- N/A (frontend-only, uses backend REST API) (002-ui-modernization)

- (001-cms-automation)

## Project Structure

```text
src/
tests/
```

## Commands

# Add commands for 

## Code Style

: Follow standard conventions

## Recent Changes
- 002-ui-modernization: Added TypeScript 5.x + React 18

- 001-cms-automation: Added

<!-- MANUAL ADDITIONS START -->

## Deployment Configuration

### Google Cloud Platform
| Resource | Value |
|----------|-------|
| **Project ID** | `cmsupload-476323` |
| **Project Number** | `297291472291` |
| **Region** | `us-east1` |

### Frontend (GCS Buckets)
| Environment | Bucket | URL |
|-------------|--------|-----|
| **Production** | `cms-automation-frontend-476323` | https://storage.googleapis.com/cms-automation-frontend-476323/index.html |
| **Alternative** | `cms-automation-frontend-cmsupload-476323` | https://storage.googleapis.com/cms-automation-frontend-cmsupload-476323/index.html |

**IMPORTANT**: Do NOT use `cms-automation-frontend-2025` - this bucket does not exist!

### Backend (Cloud Run)
| Service | URL |
|---------|-----|
| **cms-automation-backend** | https://cms-automation-backend-297291472291.us-east1.run.app |

### Supabase
| Resource | Value |
|----------|-------|
| **Project Ref** | `twsbhjmlmspjwfystpti` |
| **URL** | https://twsbhjmlmspjwfystpti.supabase.co |

### Deployment Commands

```bash
# Load deployment configuration
source scripts/deployment/config.sh

# Deploy frontend
cd frontend && npm run build
gsutil -m rsync -r -d dist gs://cms-automation-frontend-476323

# Deploy backend
gcloud run deploy cms-automation-backend --source . --region us-east1
```

### CORS Configuration
The backend must allow these origins:
- `http://localhost:3000`
- `http://localhost:8000`
- `https://storage.googleapis.com`
- `https://cms-automation-frontend-476323.storage.googleapis.com`
- `https://cms-automation-frontend-cmsupload-476323.storage.googleapis.com`

## WordPress Publishing Rules

**IMPORTANT**: This project uses **Playwright browser automation** to publish articles to WordPress, NOT the WordPress REST API.

### Why Browser Automation (Not REST API)?
1. WordPress REST API is disabled on admin.epochtimes.com
2. Browser automation can handle complex WordPress admin workflows
3. Supports media uploads, category selection, SEO plugin configuration
4. Works with any WordPress theme/plugin configuration

### Available Publishing Methods
1. **Playwright** (Default, Free) - `PlaywrightWordPressPublisher`
   - Fully automated browser-based publishing
   - Uses Chrome/Chromium in headless mode
   - Works in Cloud Run with Playwright installed

2. **Anthropic Computer Use** (Alternative, Paid API) - `ComputerUseCMSService`
   - Claude controls browser via screenshots
   - Requires desktop environment for full functionality
   - More intelligent error handling
   - Currently used for complex publishing scenarios via Celery workers

### Current Implementation
- Service: `src/services/providers/playwright_wordpress_publisher.py`
- Publishes articles as DRAFT (not live) for editor review
- Supports HTTP Basic Auth for site-level authentication

### Publishing Flow (Playwright)
1. Launch headless Chromium browser
2. Navigate to WordPress admin with HTTP auth (if configured)
3. Log in with WordPress credentials
4. Navigate to Posts → Add New
5. Fill in title and content
6. Save as Draft
7. Return the draft editor URL and post ID

### WordPress Credentials (from Cloud Run secrets)
- `CMS_BASE_URL`: WordPress site URL (e.g., https://admin.epochtimes.com)
- `CMS_USERNAME`: WordPress username
- `CMS_APPLICATION_PASSWORD`: WordPress password
- `CMS_HTTP_AUTH_USERNAME`: Site-level HTTP Basic Auth username (if needed)
- `CMS_HTTP_AUTH_PASSWORD`: Site-level HTTP Basic Auth password (if needed)

<!-- MANUAL ADDITIONS END -->
