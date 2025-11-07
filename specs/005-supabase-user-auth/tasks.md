# Tasks – Supabase Authentication & User Management

> 建議依序執行，任務 ID 可在 Git 分支或 PR 標題中引用（例如 `feat/auth-005-t03`）。

| ID | 類別 | 描述 | 交付物 / 驗收標準 |
|----|------|------|--------------------|
| T01 | 準備 | 更新 `.env.example`, `.env.supabase`, `docs/CONFIGURATION_STATUS_REPORT.md`，加入 Supabase 相關變數與說明。 | 檔案更新；本地能透過 `pnpm run dev` 與 `poetry run uvicorn` 讀取新變數。 |
| T02 | DB/RLS | 在 Supabase 建立 `profiles` 表（`id uuid pk references auth.users`, `role text default 'editor'`, `display_name text`）。撰寫 RLS：`auth.uid() = id` 可 `select`；`role='admin'` 可 `insert/update/delete`。 | Supabase migration SQL + 測試截圖或 `supabase db diff` 結果。 |
| T03 | FE 客戶端 | 新增 `src/lib/supabase.ts`（singleton client）；建立 `AuthProvider` + `useAuth` hook 管理 session、signIn、signOut、sendMagicLink。 | Vitest 單元測試覆蓋 state 轉換；Storybook/文檔更新（如有）。 |
| T04 | Login UI | 建立 `/login` route + `LoginPage`：Email/Password、Magic Link、error 提示、loading。 | UI 截圖；Vitest 測試模擬成功/失敗流程。 |
| T05 | Route Guard | 建立 `ProtectedLayout` 或 `RequireAuth` HOC，包裹現有頁面。未登入 → redirect `/login?redirect=...`；登入後跳回原頁。 | Playwright case：未登入訪問 `/worklist` 時被重導。 |
| T06 | FE API 整合 | 更新 API client 或 `fetcher`，在每次請求自動附上 `Authorization` header；處理 401 → signOut。Viewer 角色在 UI 層禁用破壞性操作。 | API 層單元測試；viewer 帳號 Playwright 截圖顯示 CTA disabled。 |
| T07 | BE JWT 驗證 | 新增 `services/auth/jwt.py`（JWKS 下載 + 驗證）；建立 FastAPI dependency `get_current_user`。 | pytest：有效 JWT 通過，無效/過期被拒；文檔記錄配置。 |
| T08 | BE 授權整合 | 所有 router 套用 `Depends(get_current_user)`；敏感路由加 `require_role(['admin'])`。 | `pytest --maxfail=1` 全過；API Doc 更新說明授權。 |
| T09 | 測試矩陣 | 撰寫 Vitest、pytest、Playwright 測試（對應 tests.md）；在 CI 中啟用或標記。 | 測試報告或 CI 截圖、coverage ≥ 70%。 |
| T10 | Runbook & 手動驗收 | 更新 Runbook：「新增/停用帳號」、「常見錯誤」；按照 tests.md 驗收清單完成並附證據。 | README / Runbook 變更；驗收清單打勾。 |

## 依賴關係

- T02 需在 T03-T08 前完成，以便前後端可讀取角色。
- T04 依賴 T03（Auth Context）才能提交登入請求。
- T08 需在 T07 JWT 驗證完成後才能佈署。
- T09 覆蓋前後端所有變動，建議與 T07/T08 平行推進。

## 進度追蹤建議

- 在 Project Board 建立「005 Supabase Auth」泳道，欄位：Backlog / In Progress / Review / Done。
- 任務完成時同步更新此 tasks.md 或 README，確保 Stakeholder 知道現況。
