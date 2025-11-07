# 005: Supabase Authentication & User Management

**狀態:** 📝 待實施 (Planned)  
**優先級:** High  
**預估工期:** ~4 個工作日  
**最後更新:** 2025-02-14

---

## 📋 快速概述

這份 Spec Kit 定義了在整個 CMS Automation 應用中導入 Supabase 驗證與使用者管理的方案。核心目標：

1. **統一入口**：在進入任意前端路由前顯示登入頁面，僅授權用戶可訪問應用。
2. **受信任後端**：所有 API 以 Supabase JWT 為唯一信任來源，後端無需維護自建 Session。
3. **簡化維運**：透過 Supabase Dashboard 管理少量使用者與角色，避免複雜 IAM。
4. **安全預設**：強制 HTTPS、最小權限 API Key、服務端驗證 + RLS，避免繞過。

---

## 📚 文檔導航

| 文檔 | 說明 |
|------|------|
| **[requirements.md](./requirements.md)** | 功能/安全需求、使用者旅程、成功指標。 |
| **[plan.md](./plan.md)** | 架構設計、資料流、分階段實施與風險。 |
| **[tests.md](./tests.md)** | 單元 / 整合 / E2E / 手動驗收的測試矩陣。 |
| **[tasks.md](./tasks.md)** | 可執行任務清單，含輸入/輸出與驗收條件。 |

---

## 🎯 成功指標

- 100% 未授權請求被攔截（前端路由守衛 + 後端 401）。
- Supabase Email 驗證或魔術連結流程全通過，平均登入耗時 < 5 秒。
- 7 天內無高危安全警示（Supabase Audit / FastAPI logs）。
- 新增/停用帳號全流程僅需 Supabase Dashboard + 1 次部署配置更新。

---

## 🧭 開始使用

1. 依序閱讀 requirements → plan → tests，確保對範圍與實施順序有共識。  
2. 使用 tasks.md 追蹤任務進度，並在 MR 中引用該任務 ID。  
3. 專案 `.env` 中補齊 `SUPABASE_URL / ANON_KEY / SERVICE_KEY` 後即可開始開發。  
4. 驗收時，依 tests.md 的清單逐條確認並附上截图/錄屏或日誌。

---

**審批:** 待審批  
**實施者:** 待指派  
**審閱者:** 待指派
