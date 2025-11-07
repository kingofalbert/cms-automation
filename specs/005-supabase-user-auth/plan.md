# Implementation Plan – Supabase Authentication & User Management

## 1. 架構概覽

```
┌─────────────┐      JWT       ┌────────────┐      service key      ┌─────────────┐
│   Browser   │ ─────────────▶ │  FastAPI   │ ────────────────────▶ │  Supabase   │
│ React + Vite│                │  Backend   │                       │  Auth/DB    │
└─────────────┘ ◀─ session ────└────────────┘ ◀── profile/role ────└─────────────┘
        │                             ▲
        └── Supabase JS client ◀──────┘
```

- 前端以 `SupabaseClient` 取得 session，存入 context，所有 API 請求在 `fetcher` 層自動掛上 `Authorization`。
- 後端以 JWKS 驗證 JWT，並透過 Supabase `profiles` 表更新/查詢角色，RLS 確保資料隔離。

## 2. 分階段實施

### Phase 0 – 準備 (0.5 d)
1. 確認 Supabase 專案可用，開啟 Email Confirm、Password Reset、Magic Link。
2. 設定 `.env` 模板：`VITE_SUPABASE_URL/ANON_KEY`、`SUPABASE_URL/ANON_KEY/SERVICE_KEY`。
3. 寫入 `docs/CONFIGURATION_STATUS_REPORT` 變更，並更新 secret manager。

### Phase 1 – 資料層與安全策略 (0.5 d)
1. 透過 Supabase SQL Editor 建立 `profiles` 表與 `role` enum default `editor`。
2. 啟用 RLS，撰寫 policies：
   - `authenticated` 用戶可 `select` 自己的 profile。
   - `role = 'admin'` 可 `insert/update` 任意 profile。
3. 設定 `admin` 組用於 Dashboard（可透過 metadata 或 `app_metadata`）。

### Phase 2 – 前端客戶端與路由守衛 (1.5 d)
1. 新增 `src/lib/supabase.ts` 建立 singleton client。
2. 建立 `AuthProvider` / `useAuth()` 封裝 `session`, `user`, `status`, `signIn`, `signOut`, `sendMagicLink`。
3. 實作 `/login` 頁面（表單驗證 + 錯誤提示 + loading 狀態）。
4. 加入 `ProtectedRoute`（或 layout）於 Router，未登入時 redirect → `/login?redirect=/target`.
5. 將 nav/header 顯示使用者名稱/角色 + Sign out 操作。

### Phase 3 – 前端 API 整合 (0.5 d)
1. 更新 `apiClient`（或 fetch wrapper）在每次請求前從 `supabase.auth.getSession()` 取得 access token。
2. 處理 401/403 時自動登出或提示重新登入。
3. 若需要 `viewer` read-only 限制，在 UI 層禁用對應動作（例如隱藏「Publish」按鈕）。

### Phase 4 – 後端驗證中介層 (1 d)
1. 安裝 `python-jose[cryptography]` 或 `pyjwt`。
2. 新增 `backend/src/services/auth/jwt.py`：下載 Supabase JWKS、驗證 `issuer/audience/exp`。
3. 建立 FastAPI dependency `get_current_user()`，失敗則 raise HTTP 401。
4. 新增 `require_role(['admin'])` decorator/dep 用於敏感路由。
5. 將 API router（Worklist、Proofreading、Publishing 等）套用 `Depends(get_current_user)`.

### Phase 5 – 測試與驗收 (0.5 d)
1. 撰寫 Vitest 單元測試：`AuthProvider`, `LoginPage`, `ProtectedRoute`。
2. 撰寫 FastAPI pytest：`test_auth_middleware_allows_valid_jwt`, `test_reject_invalid_issuer`.
3. Playwright E2E：登入流程、未登入訪問 redirect、expired token 重新登入。
4. 更新 Runbook：新增「如何新增使用者 / 停用 / 重設密碼」。

## 3. 風險與緩解

| 風險 | 影響 | 緩解 |
|------|------|------|
| Supabase JWK 輪換導致驗證失敗 | 全站 API 401 | 實作快取 + fallback refresh、監控 401 激增。 |
| 使用者等待刷新時閃爍 | UX | 在 `AuthProvider` 設置 `loading` 狀態並顯示 Skeleton。 |
| Service key 泄漏 | 高 | 僅後端使用 + Secret Manager + rotate 指南。 |
| 角色不同步 | 誤授權 | 每次登入後拉取 `profiles.role`；Admin 更新後強制重新登入。 |

## 4. 發佈策略

- 先在 staging 啟用 Supabase auth，僅少數 QA 帳號可登入。
- 覆蓋主要使用流程後，切換 production，並公告所有使用者需要 Supabase 帳號。
- 觀察 24 小時內 401/403 log，若無異常再刪除舊有匿名入口。

## 5. 監控與維運

- **前端**：Sentry (或 Vite logger) 監控登入錯誤、token refresh 失敗。
- **後端**：導出 401/403、JWT 驗證錯誤計數到 Cloud Logging + Alert。
- **Supabase**：啟用 Auth audit log，設定登入失敗閾值告警。

## 6. 後續擴充（非本階段）

- 支援 Google / Microsoft SSO。
- 多因素驗證（Supabase Authenticator）。
- 細粒度權限（以 Postgres POLICY 或 FastAPI ACL 實現）。
