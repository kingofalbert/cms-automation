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

<!-- MANUAL ADDITIONS END -->
