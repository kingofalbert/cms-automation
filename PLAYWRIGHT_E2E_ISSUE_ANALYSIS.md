# Playwright E2E Testing Issue Analysis

**Generated**: 2025-11-04
**Project**: CMS Automation Frontend
**Environment**: Production Deployment on Google Cloud Storage

---

## Executive Summary

Attempted to implement Playwright E2E testing for a React + TypeScript frontend deployed on Google Cloud Storage (GCS). After extensive debugging and fixing multiple issues (Vite configuration, CDN caching, path resolution), **4 out of 7 tests are still failing** despite all static assets being correctly deployed and accessible.

### Current Status
- ✅ **3 tests passing**: API configuration check, no console errors, responsive design
- ❌ **4 tests failing**: Homepage title, app header visibility, navigation menu, page links
- ✅ All static files deployed correctly (93 files, 11.2 MB)
- ✅ CDN cache cleared and serving updated files
- ❌ React application fails to initialize in browser during tests

---

## Project Context

### Technology Stack
- **Frontend Framework**: React 18.2.0 + TypeScript 5.3.3
- **Build Tool**: Vite 5.0.6
- **Routing**: React Router DOM 6.20.0
- **Testing**: Playwright 1.56.1
- **Deployment**: Google Cloud Storage (static hosting)
- **Backend API**: FastAPI on Cloud Run (`https://cms-automation-backend-ufk65ob4ea-uc.a.run.app`)

### Deployment Architecture
```
┌─────────────────────────────────────────┐
│  Frontend (React SPA)                   │
│  Deployed to: GCS Bucket                │
│  gs://cms-automation-frontend-2025      │
│  URL: storage.googleapis.com/...        │
└─────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│  Backend API (FastAPI)                  │
│  Deployed to: Cloud Run                 │
│  URL: cms-automation-backend-*.run.app  │
└─────────────────────────────────────────┘
```

### Project Structure
```
cms_automation/
├── frontend/
│   ├── src/
│   ├── dist/               # Build output
│   ├── e2e/                # Playwright tests
│   ├── playwright.config.ts
│   ├── vite.config.ts
│   └── package.json
└── backend/                # FastAPI backend
```

---

## Initial Problem

**User Request**: "使用 Playwright 測試前端功能，找到問題，找到根因，解決，再測試，直到通過。"

**Goal**: Implement comprehensive E2E testing with Playwright against the production deployment.

---

## Implementation Steps

### 1. Playwright Setup
```bash
npm install --save-dev @playwright/test@^1.56.1
npx playwright install chromium
```

**Configuration** (`playwright.config.ts`):
```typescript
export default defineConfig({
  testDir: './e2e',
  baseURL: 'https://storage.googleapis.com/cms-automation-frontend-2025',
  use: {
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
});
```

### 2. Test Suite Created
7 comprehensive tests in `e2e/basic-functionality.spec.ts`:
1. Homepage loads successfully (check page title)
2. App title visible in header
3. Navigation menu visible
4. Can navigate to different pages
5. API configuration check
6. No console errors on load
7. Page responds to viewport resize

---

## Issues Encountered & Fixes Applied

### Issue 1: Vite Base Path Configuration
**Problem**: Built assets used absolute paths (`/assets/js/...`) which don't work with GCS static hosting.

**Root Cause**: Vite's default `base: '/'` generates absolute paths.

**Fix Applied**:
```typescript
// vite.config.ts
export default defineConfig({
  base: './',  // Changed from default '/'
  plugins: [react()],
  // ...
});
```

**Result**: Assets now use relative paths (`./assets/js/...`)

---

### Issue 2: GCS Root Path Limitation
**Problem**: GCS `storage.googleapis.com` doesn't automatically serve `index.html` for root path `/`.

**Evidence**:
```bash
curl https://storage.googleapis.com/cms-automation-frontend-2025/
# Returns: XML bucket listing instead of index.html
```

**Root Cause**: Unlike Firebase Hosting or Cloud Load Balancer, raw GCS doesn't have SPA routing.

**Fix Applied**: Updated all Playwright tests to navigate to `/index.html` explicitly:
```typescript
// Before
await page.goto('/');

// After
await page.goto('/index.html');
```

---

### Issue 3: Icon Absolute Path
**Problem**: Favicon used absolute path `/vite.svg` in source HTML.

**Fix Applied**:
```html
<!-- Before -->
<link rel="icon" type="image/svg+xml" href="/vite.svg" />

<!-- After -->
<link rel="icon" type="image/svg+xml" href="./vite.svg" />
```

---

### Issue 4: CDN Edge Caching
**Problem**: After deployment, old version still served due to CDN caching.

**Evidence**:
```bash
# Direct GCS API call
gsutil cat gs://cms-automation-frontend-2025/index.html
# Showed NEW version with relative paths

# Public CDN URL
curl https://storage.googleapis.com/cms-automation-frontend-2025/index.html
# Showed OLD version with absolute paths
```

**Root Cause**: Google CDN edge cache with 1-hour TTL (`Cache-Control: max-age=3600`).

**Resolution**: Waited 1+ hour for cache expiration. Verified cache cleared:
```bash
curl -s "https://storage.googleapis.com/cms-automation-frontend-2025/index.html" | grep vite.svg
# Output: <link rel="icon" type="image/svg+xml" href="./vite.svg" />
```

---

## Current Problem: Tests Still Failing

### Test Results After All Fixes
```
Running 7 tests using 5 workers

✓ [chromium] › checks API configuration (PASS)
✓ [chromium] › no console errors on load (PASS)
✓ [chromium] › page responds to resize (PASS)

✗ [chromium] › homepage loads successfully (FAIL)
✗ [chromium] › has correct app title in header (FAIL)
✗ [chromium] › navigation menu is visible (FAIL)
✗ [chromium] › can navigate to different pages (FAIL)

4 failed, 3 passed (13.1s)
```

### Failure Details

#### Test 1: Homepage Loads Successfully
```javascript
Error: expect(page).toHaveTitle(expected) failed
Expected pattern: /CMS Automation/i
Received string:  ""
Timeout: 5000ms
```

**Screenshot Analysis**: Shows XML error page:
```xml
<Error>
  <Code>NoSuchBucket</Code>
  <Message>The specified bucket does not exist.</Message>
</Error>
```

#### Tests 2-4: DOM Elements Not Found
All three tests fail with same pattern:
```javascript
Error: expect(locator).toBeVisible() failed
Expected: visible
Timeout: 10000ms
Error: element(s) not found
```

**Implication**: React application never mounted, DOM never rendered.

---

## Verification Steps Performed

### 1. Bucket Existence
```bash
gsutil ls gs://cms-automation-frontend-2025/ | head -5
# Output:
# gs://cms-automation-frontend-2025/index.html
# gs://cms-automation-frontend-2025/assets/
```
✅ Bucket exists

### 2. File Accessibility
```bash
curl -I "https://storage.googleapis.com/cms-automation-frontend-2025/index.html"
# HTTP/2 200
# content-type: text/html

curl -I "https://storage.googleapis.com/cms-automation-frontend-2025/assets/js/index-kHjtRX8F.js"
# HTTP/2 200
# content-type: text/javascript
```
✅ Files publicly accessible

### 3. File Count Verification
```bash
# GCS
gsutil ls gs://cms-automation-frontend-2025/assets/css/ | wc -l  # 6
gsutil ls gs://cms-automation-frontend-2025/assets/js/ | wc -l   # 86

# Local build
ls dist/assets/css/ | wc -l  # 6
ls dist/assets/js/ | wc -l   # 86
```
✅ All files deployed (93 total files, 11.2 MB)

### 4. Content Verification
```bash
# Check deployed index.html
curl -s "https://storage.googleapis.com/cms-automation-frontend-2025/index.html"
```

**Result**: Correct content with relative paths:
```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="./vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>CMS Automation</title>
    <script type="module" crossorigin src="./assets/js/index-kHjtRX8F.js"></script>
    <link rel="modulepreload" crossorigin href="./assets/js/chunk-hGTiAIL8.js">
    <link rel="modulepreload" crossorigin href="./assets/js/chunk-nQFRkMuv.js">
    <link rel="modulepreload" crossorigin href="./assets/js/chunk-Bh5vFPi6.js">
    <link rel="stylesheet" crossorigin href="./assets/css/index-Bv6dUzsf.css">
  </head>
  <body>
    <div id="root"></div>
  </body>
</html>
```
✅ HTML correct

### 5. JavaScript Bundle Check
```bash
curl -s "https://storage.googleapis.com/cms-automation-frontend-2025/assets/js/index-kHjtRX8F.js" | head -20
```

**Result**: Valid React application code (362 KB minified). Sample:
```javascript
import{j as n,Q as r,a as o}from"./chunk-nQFRkMuv.js";
import{b as i,r as a,u as s,d as l,e as c,g as u,R as d,a as f,c as h,f as p,B as m}from"./chunk-hGTiAIL8.js";
// ... React Router configuration
const R=[
  {path:"/",component:a.lazy(()=>import("./HomePage.tsx-CV4cLiFj.js")),title:"CMS Automation - 首頁"},
  // ... more routes
];
```
✅ JavaScript valid

### 6. MD5 Hash Verification
```bash
# Local file
openssl md5 -binary dist/index.html | openssl base64
# GP1pRZmW2Q3jOcLGjwUG9Q==

# GCS file metadata
gsutil stat gs://cms-automation-frontend-2025/index.html
# md5Hash: 'GP1pRZmW2Q3jOcLGjwUG9Q=='
```
✅ Files match exactly

---

## Puzzling Observations

### 1. "NoSuchBucket" Error is Misleading
- Bucket definitely exists (`gsutil ls` works)
- Files are publicly accessible (`curl` returns 200 OK)
- Browser screenshot shows XML error **rendered by browser**, not network error

**Hypothesis**: Error may be generated by **JavaScript runtime** attempting to access GCS API, not initial page load.

### 2. Passing Tests Indicate Partial Success
- ✅ **"checks API configuration"** passes - JavaScript executes enough to evaluate `window` object
- ✅ **"no console errors on load"** passes - Page loads without console errors (after CDN fix)
- ✅ **"page responds to resize"** passes - DOM exists and is responsive

**Contradiction**: If page completely fails to load, why do some tests pass?

### 3. React App Never Mounts
Failing tests all expect DOM elements that should be rendered by React:
- Page `<title>` should be set by React
- Header with app title should be rendered
- Navigation menu should be rendered
- Links should be present

**Implication**: `ReactDOM.createRoot(document.getElementById('root')).render(...)` never executes successfully.

---

## Environment Configuration

### Frontend `.env.production`
```bash
VITE_API_URL=https://cms-automation-backend-ufk65ob4ea-uc.a.run.app
VITE_WS_URL=wss://cms-automation-backend-ufk65ob4ea-uc.a.run.app/ws

VITE_APP_TITLE=CMS Automation
VITE_APP_VERSION=1.0.0
VITE_APP_DESCRIPTION=AI-powered CMS automation system

VITE_ENABLE_DEVTOOLS=false
VITE_ENABLE_MOCK_DATA=false
VITE_ENABLE_EXPERIMENTAL_FEATURES=false

VITE_ENABLE_PERFORMANCE_MONITORING=true
VITE_ENABLE_ERROR_REPORTING=true

VITE_DEFAULT_POLLING_INTERVAL=10000
VITE_TASK_POLLING_INTERVAL=5000

VITE_ENV=production
```

### Vite Build Configuration
```typescript
// vite.config.ts
export default defineConfig({
  base: './',
  plugins: [react()],
  resolve: {
    alias: { '@': path.resolve(__dirname, './src') },
  },
  server: {
    port: 3000,
    proxy: { '/api': { target: 'http://localhost:8000', changeOrigin: true } },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
    minify: 'terser',
    terserOptions: {
      compress: { drop_console: true, drop_debugger: true },
    },
    rollupOptions: {
      output: {
        manualChunks: {
          'react-core': ['react', 'react-dom', 'react-router-dom'],
          'react-query': ['@tanstack/react-query'],
          // ... more chunks
        },
      },
    },
  },
});
```

---

## Playwright Test Configuration

### Full Configuration
```typescript
// playwright.config.ts
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',

  use: {
    baseURL: 'https://storage.googleapis.com/cms-automation-frontend-2025',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },

  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
});
```

### Sample Test
```typescript
// e2e/basic-functionality.spec.ts
test('homepage loads successfully', async ({ page }) => {
  await page.goto('/index.html');
  await page.waitForLoadState('networkidle');

  // FAILS HERE - page.title() returns empty string
  await expect(page).toHaveTitle(/CMS Automation/i);
});
```

---

## Browser Network Activity (from Playwright trace)

Based on test execution and error screenshots:

1. **Initial Request**: `GET /index.html` → ✅ 200 OK
2. **JavaScript Module**: `GET ./assets/js/index-kHjtRX8F.js` → ❓ Status unclear
3. **CSS Stylesheet**: `GET ./assets/css/index-Bv6dUzsf.css` → ❓ Status unclear
4. **Module Preloads**: Multiple `GET ./assets/js/chunk-*.js` → ❓ Status unclear
5. **Error Rendered**: XML error page with "NoSuchBucket" appears in browser

**Key Question**: At what point does the "NoSuchBucket" error occur?

---

## Hypotheses for Root Cause

### Hypothesis 1: CORS Policy Issue
**Theory**: Browser blocks JavaScript module imports due to CORS restrictions from GCS.

**Evidence**:
- GCS buckets don't automatically set CORS headers
- React app uses ES modules with `import` statements
- Browser may reject cross-origin module imports

**Test Needed**: Check response headers for CORS headers:
```bash
curl -I "https://storage.googleapis.com/cms-automation-frontend-2025/assets/js/index-kHjtRX8F.js" | grep -i "access-control"
```

### Hypothesis 2: Service Worker or Cache Issue
**Theory**: Browser has stale service worker or cache causing conflicts.

**Evidence**:
- Vite generates service worker for PWA features
- Cache could be serving old version with absolute paths

**Test Needed**: Check for service worker registration in main.tsx

### Hypothesis 3: API Endpoint Unreachable
**Theory**: React app startup attempts to connect to backend API and fails.

**Evidence**:
- Environment variable: `VITE_API_URL=https://cms-automation-backend-ufk65ob4ea-uc.a.run.app`
- App may have API initialization code that throws on failure
- "NoSuchBucket" error could be GCS-related API call within app code

**Test Needed**:
```bash
curl -I https://cms-automation-backend-ufk65ob4ea-uc.a.run.app/health
```

### Hypothesis 4: GCS Static Hosting Limitations
**Theory**: `storage.googleapis.com` URLs have inherent limitations for SPA hosting.

**Evidence**:
- GCS is designed for object storage API, not web hosting
- Recommended approach is using custom domain with Load Balancer or Firebase Hosting
- Some browser features may be restricted on `storage.googleapis.com` domain

**Known Limitations**:
- No automatic `index.html` routing
- Limited control over response headers
- May have Content-Security-Policy restrictions

### Hypothesis 5: Module Import Path Resolution
**Theory**: Relative imports fail when base URL includes path components.

**Evidence**:
- Base URL: `https://storage.googleapis.com/cms-automation-frontend-2025/index.html`
- Relative imports: `./assets/js/...`
- Browser may resolve to wrong path

**Current Resolution**:
```
Base: https://storage.googleapis.com/cms-automation-frontend-2025/index.html
Import: ./assets/js/chunk.js
Resolves to: https://storage.googleapis.com/cms-automation-frontend-2025/assets/js/chunk.js ✅
```

Should be correct, but verify actual network requests.

---

## Recommendations for Debugging

### Immediate Actions

1. **Capture Full Browser Console Output**
   ```javascript
   // In test
   page.on('console', msg => console.log('BROWSER LOG:', msg.text()));
   page.on('pageerror', err => console.log('BROWSER ERROR:', err));
   ```

2. **Check Network Tab**
   ```javascript
   page.on('request', req => console.log('REQUEST:', req.url()));
   page.on('response', res => console.log('RESPONSE:', res.url(), res.status()));
   page.on('requestfailed', req => console.log('FAILED:', req.url(), req.failure()));
   ```

3. **Verify CORS Headers**
   ```bash
   curl -H "Origin: https://example.com" -I \
     "https://storage.googleapis.com/cms-automation-frontend-2025/assets/js/index-kHjtRX8F.js"
   ```

4. **Test Backend Connectivity**
   ```bash
   curl -v https://cms-automation-backend-ufk65ob4ea-uc.a.run.app/
   ```

5. **Try Local HTTP Server**
   ```bash
   cd dist
   python3 -m http.server 8080
   # Update playwright.config.ts baseURL to http://localhost:8080
   npm run test:e2e
   ```

### Alternative Solutions

1. **Migrate to Firebase Hosting**
   - Better SPA support
   - Automatic index.html routing
   - Better caching control
   ```bash
   npm install -g firebase-tools
   firebase init hosting
   firebase deploy --only hosting
   ```

2. **Use Cloud Load Balancer + Cloud CDN**
   - Configure Cloud Storage backend with custom domain
   - Set proper CORS and caching policies
   - Enable HTTPS with managed certificate

3. **Deploy Frontend to Cloud Run**
   - Serve static files through HTTP server (nginx or Node.js)
   - Full control over response headers
   - Same infrastructure as backend

---

## Files for Further Analysis

### Key Files to Examine
```
frontend/
├── dist/index.html                          # Built HTML (verified correct)
├── dist/assets/js/index-kHjtRX8F.js         # Main bundle (362 KB)
├── src/main.tsx                             # React app entry point
├── src/App.tsx                              # Root component
├── vite.config.ts                           # Build configuration
├── playwright.config.ts                     # Test configuration
└── e2e/basic-functionality.spec.ts          # Test suite
```

### Log Files
```
test-results/
├── basic-functionality-CMS-Au-4fe39-homepage-loads-successfully-chromium/
│   ├── test-failed-1.png                    # Screenshot showing XML error
│   ├── video.webm                           # Test execution video
│   └── error-context.md                     # Error details
└── playwright-report/                       # Full HTML report
```

---

## Technical Constraints

### What We Cannot Change
- ✅ GCS bucket exists and is configured
- ✅ All files are deployed correctly
- ✅ Files are publicly accessible
- ✅ CDN cache has been cleared
- ✅ Build configuration produces correct output

### What We Can Change
- 🔄 Hosting platform (GCS → Firebase/Cloud Run)
- 🔄 CORS configuration
- 🔄 API endpoint configuration
- 🔄 React app initialization logic
- 🔄 Test configuration and approach

---

## Questions for Root Cause Analysis

1. **Why does the browser show "NoSuchBucket" error when the bucket clearly exists?**
   - Is this error generated by application code making GCS API calls?
   - Is this a browser-rendered error or server response?

2. **Why do 3 tests pass if the page completely fails to load?**
   - Does "checks API configuration" test prove JavaScript executes?
   - What does "no console errors" actually verify?

3. **Does React app initialization depend on API connectivity?**
   - Does app fail to mount if backend API unreachable?
   - Is there error handling that renders error page?

4. **Are there CORS restrictions preventing module loading?**
   - Do GCS responses include required CORS headers?
   - Are there Content-Security-Policy violations?

5. **Is `storage.googleapis.com` domain suitable for SPA hosting?**
   - Are there known browser limitations on this domain?
   - Should we migrate to Firebase Hosting or custom domain?

---

## Reproduction Steps

```bash
# 1. Navigate to project
cd /Users/albertking/ES/cms_automation/frontend

# 2. Run tests
npm run test:e2e

# 3. View results
# Tests will fail with same pattern
# Screenshots saved to test-results/
```

---

## Summary

Despite successfully fixing multiple deployment and configuration issues:
- ✅ Vite build configuration (relative paths)
- ✅ GCS bucket setup and permissions
- ✅ CDN cache invalidation
- ✅ Playwright test configuration

**The React application still fails to initialize during E2E tests**, resulting in:
- Empty page title
- No DOM elements rendered
- "NoSuchBucket" XML error visible in browser

**The root cause remains unclear**, with multiple hypotheses pointing to:
1. CORS policy issues
2. Backend API connectivity problems
3. GCS static hosting limitations
4. Module import resolution failures

**Next steps require deeper debugging** of browser network activity and React initialization flow to identify why the application fails to mount despite all static assets being correctly deployed and accessible.

---

## Appendix: Full Test Output

```
Running 7 tests using 5 workers

[1/7] [chromium] › e2e/basic-functionality.spec.ts:4:3 › homepage loads successfully
[2/7] [chromium] › e2e/basic-functionality.spec.ts:14:3 › has correct app title in header
[3/7] [chromium] › e2e/basic-functionality.spec.ts:25:3 › navigation menu is visible
[4/7] [chromium] › e2e/basic-functionality.spec.ts:35:3 › can navigate to different pages
[5/7] [chromium] › e2e/basic-functionality.spec.ts:56:3 › checks API configuration
API URL configured: not found

[6/7] [chromium] › e2e/basic-functionality.spec.ts:74:3 › no console errors on load
[7/7] [chromium] › e2e/basic-functionality.spec.ts:100:3 › page responds to resize

  1) [chromium] › homepage loads successfully
     Error: expect(page).toHaveTitle(expected) failed
     Expected pattern: /CMS Automation/i
     Received string:  ""

  2) [chromium] › has correct app title in header
     Error: expect(locator).toBeVisible() failed
     Locator: locator('h1, [class*="logo"], [class*="title"]').first()
     Expected: visible
     Error: element(s) not found

  3) [chromium] › navigation menu is visible
     Error: expect(locator).toBeVisible() failed
     Locator: locator('nav, [class*="navigation"], [class*="sidebar"], [class*="menu"]').first()
     Expected: visible
     Error: element(s) not found

  4) [chromium] › can navigate to different pages
     Error: expect(received).toBeGreaterThan(expected)
     Expected: > 0
     Received:   0

  4 failed, 3 passed (13.1s)
```

---

**Document End**
