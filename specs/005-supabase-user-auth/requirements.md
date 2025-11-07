# Requirements – Supabase Authentication & User Management

## 1. 背景與目標

- 目前 CMS Automation 前端預設匿名可訪問，缺乏統一的身份驗證層，導致敏感內容暴露風險。
- 團隊已擁有 `twsbhjmlmspjwfystpti.supabase.co` 專案與對應 API Key，希望利用 Supabase Auth 迅速導入登入體驗。
- 使用者量級小（< 30 人），偏向內部操作人員，因此方案需「簡單、易維護、安全」。

**目標**
1. 全站僅允許通過 Supabase Auth 驗證的使用者訪問。
2. 提供登入/登出頁面，支援 Email + 密碼及魔術連結（選配）。
3. 以 Supabase JWT 作為前後端之間的唯一信任，後端無自建 Session。
4. 允許 Admin 在 Supabase Dashboard 手動新增/停用帳號，應用自動同步角色。

## 2. 角色與使用者旅程

| 角色 | 主要需求 | 權限 |
|------|----------|------|
| Admin | 管理帳號、存取所有 CMS 功能 | 完整 CRUD、設定管理 |
| Editor | 存取工作清單、校對、發佈 | Worklist / Proofreading / Publishing |
| Viewer | 只讀監控 | Dashboard / Reports |

**User Journey**
1. 訪客進入 `/` 或任意深層路由 → 被重導至 `/login`。
2. 使用者輸入 Email/Password（或點擊魔術連結），Supabase 回傳 session。
3. 前端 `AuthProvider` 儲存 session，並在路由守衛中檢查 `user` 狀態。
4. 前端呼叫後端 API 時附帶 `Authorization: Bearer <access_token>`。
5. FastAPI 透過 Supabase JWKS 驗證 JWT，解析 `sub` (user id) 與 `role`。
6. 根據 `profiles.role` 控制細部權限；若無權限則回傳 403。
7. 使用者可在 UI 中檢視基本檔案與按 `Sign out` 清除 session。

## 3. 功能需求

1. **登入頁面**
   - Vite Route `/login`（公開），包含 Email/Password 表單與「Send Magic Link」按鈕（可選）。
   - 對錯誤訊息（信箱未驗證、密碼錯誤）提供明確提示。
   - 提供 `Remember me`（預設使用 Supabase refresh token）。

2. **路由守衛**
   - 未登入訪客自動跳轉 `/login`，保留原始目標路徑於 query 以便成功後導回。
   - 已登入使用者訪問 `/login` 會被導向 dashboard。
   - 採用 `AuthProvider` + `useAuth()` hook 暴露 `user`, `session`, `loading`, `signOut`.

3. **Supabase 集成**
   - 使用 `@supabase/supabase-js` 前端客戶端；後端透過 HTTP 驗證 JWT。
   - `.env` 新增 `VITE_SUPABASE_URL` / `VITE_SUPABASE_ANON_KEY`（前端）、`SUPABASE_SERVICE_KEY`（後端）。
   - 建立 `profiles` table（`id uuid PK references auth.users`, `role text`, `display_name`, `created_at`）。
   - 啟用 Row Level Security，規則：`auth.uid() = id` 允許讀自己的 profile；Admins 可以更新所有人。

4. **後端保護**
   - FastAPI 以中介層驗證 Authorization header，將使用者資訊附於 `request.state.user`。
   - 所有 router 依需求引用 `current_user` 依賴；若缺 token → 401，若角色不足 → 403。
   - 後端若需查詢詳細資料，可透過 Supabase Admin API（service key）或本地 `profiles`。

5. **操作與監控**
   - `AuthProvider` 監聽 `onAuthStateChange`，session 過期時自動刷新或登出。
   - 提供簡易「Profile」下拉顯示 `display_name / role`。
   - 記錄登入/登出事件於前端 `console.info` + 後端指標（可選 Slack 告警）。

## 4. 安全與合規

- 強制使用 HTTPS（Vercel / CloudFront 已配置），本地開發以 `.env.local` 連線 Supabase dev 專案。
- 禁止在前端使用 service key；僅後端讀取並保存在秘密管理器（GCP Secret Manager）。
- 依照 Supabase 建議啟用 Email Confirm；未確認帳號不得登入。
- 針對重複登入失敗使用 Supabase 的 `rate_limit_config` 或 Cloudflare WAF。
- JWT 驗證需檢查 `aud`、`iss`、`exp`，並在後端快取 JWKS（有效期 5 分鐘）。

## 5. 邊界與不在範圍

- 不實作自訂 OIDC Provider，也不整合企業 SSO（未來可擴充）。
- 不提供自動註冊流程；新帳號由 Admin 於 Supabase Dashboard 建立。
- 不實作複雜權限矩陣，僅使用 `role` 欄位（admin/editor/viewer）。
- 不改動既有 WordPress 或其他第三方登入流程。

## 6. 依賴

- Supabase Project `twsbhjmlmspjwfystpti`（已存在）。
- `@supabase/supabase-js`、`python-jose`、`Authlib`（視需求選用）。
- FastAPI、React Router 既有框架。

## 7. 成功標準

- 未授權使用者無法載入除 `/login` 以外的任何頁面。
- 所有 API 若缺少或無效 JWT，100% 回傳 401/403（以監控佐證）。
- Admin 可在 5 分鐘內新增/停用一位使用者且權限立即生效。
- 使用者可以在任何裝置於 5 秒內完成登入與重導回原路徑。
