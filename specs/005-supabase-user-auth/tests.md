# Test Plan – Supabase Authentication & User Management

## 1. 測試範圍

- 登入/登出流程
- 路由守衛與 session 恢復
- Backend JWT 驗證與角色授權
- 資料庫 RLS 與 `profiles` 同步

## 2. 測試矩陣

| 類型 | 負責人 | 工具 | 內容 |
|------|--------|------|------|
| 前端單元 | FE | Vitest + RTL | `AuthProvider`, `useAuth`, `ProtectedRoute`, `LoginPage` 表單驗證與錯誤提示 |
| 前端整合 | FE | Vitest (msw) | API fetcher 自動掛 token、401 觸發 signOut |
| 後端單元 | BE | pytest | `verify_supabase_jwt`, `get_current_user`, `require_role` |
| 後端整合 | BE | pytest + TestClient | 帶有效/無效 JWT 的 API 請求、角色不足時的 403 |
| 資料庫 | BE | Supabase SQL | RLS policies 生效、自身可讀寫 profile、非 Admin 無法改他人 |
| E2E | QA | Playwright | 1) 未登入訪問 `/worklist` → redirect `/login`<br>2) 登入成功 → 導回原頁<br>3) 角色為 viewer 時阻擋破壞性操作<br>4) token 過期後自動登出 |
| 安全/手動 | SecOps | 手動 | 嘗試刪除 `Authorization` header、偽造 JWT、抓舊 token 使用 |

## 3. 測試案例概述

### Frontend
1. `AuthProvider` 在 `supabase.auth.onAuthStateChange` 觸發 `SIGNED_IN/SIGNED_OUT` 時更新 context。
2. `ProtectedRoute` 於 `loading` 期間顯示 spinner，完成後根據 `user` 判斷是否 redirect。
3. `LoginPage`：
   - 表單為空顯示錯誤。
   - Supabase 回傳 `Email not confirmed` 時顯示提示。
   - Magic link 成功送出後顯示 toast。

### Backend
1. `verify_supabase_jwt`：
   - 有效 token → 回傳 payload。
   - `iss` 不匹配 → raise HTTPException(401)。
   - 過期 token → raise 401。
2. `require_role(["admin"])`：
   - admin token → 通過。
   - editor token → 403。

### Database / Policies
1. `select` 自己 profile 成功；查他人 profile 失敗。
2. 非 admin 嘗試 `update role` → policy 拒絕。
3. Admin 透過 SQL 或 Dashboard 更新 role 後，下一次登入 role 生效。

### E2E
1. `login.spec.ts`：輸入有效帳密 → 帶至 `/worklist`，localStorage/session 更新。
2. `access-control.spec.ts`：viewer 角色檢視 Worklist，嘗試點擊「Publish」→ 前端 disabled + 後端 403。
3. `session-expiry.spec.ts`：模擬 token 過期 → API 回 401 → 前端自動 signOut 並提示。

## 4. 驗收清單

- [ ] 未登入訪問任意受保護頁時一律 redirect `/login`。
- [ ] 後端所有受保護 API 層層驗證（抓 log sample 確認）。
- [ ] Admin 可透過 Supabase Dashboard 更新角色並立即生效。
- [ ] Playwright 流程全綠並附錄屏。
- [ ] 安全測試（偽造 JWT、重放 token）全數失敗。

## 5. 測試資料

- Supabase Dashboard 中預先建立 3 個帳號：`admin@example.com`, `editor@example.com`, `viewer@example.com`。
- 密碼透過 Supabase 控制台設定，測試環境 `.env.local` 提供。
- Profiles 表插入範例資料，並在測試後還原。

## 6. 退出標準

- 所有自動化測試（unit/integration/E2E）100% 通過。
- 驗收清單項目全部打勾並有證據鏈（log、截圖或錄屏）。
- 401/403 監控在負載測試下無異常尖峰。
