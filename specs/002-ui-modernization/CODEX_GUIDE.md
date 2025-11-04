# Codex CLI 執行指南 - UI現代化項目

> 本指南專為在Codex CLI中繼續執行UI現代化項目而設計
>
> **當前狀態**: Phase 1-3 已完成 ✅
> **下一步**: Phase 4 - Settings Page Enhancement

---

## 📊 項目概覽

### 已完成的工作 (Phase 1-3)

**Git分支**: `002-ui-modernization`

**完成的Commits**:
```
12ea028 - test(ui): Improve navigation E2E tests - 11/15 passing
ebf8412 - test(ui): Add comprehensive E2E tests for navigation
1b12646 - feat(ui): Add responsive mobile navigation menu
f955f21 - feat(ui): Add cn() utility for Tailwind class merging
ee662db - fix(ui): Prevent navigation menu text from wrapping
```

**已實現功能**:
- ✅ Sonner toast library 安裝
- ✅ 目錄結構設置 (`components/ui/`, `hooks/`, `lib/`)
- ✅ `cn()` 工具函數 (Tailwind class merging)
- ✅ 導航組件響應式設計 (桌面版 + 移動版)
- ✅ 11/15 E2E測試通過

### 待完成的工作 (Phase 4-8)

總共剩餘 **118個任務** 分布在5個階段：

| Phase | 名稱 | 任務數 | 優先級 |
|-------|------|--------|--------|
| Phase 4 | Settings Page Enhancement | 34 | P1 |
| Phase 5 | Design System Foundation | 25 | P1 |
| Phase 6 | Responsive Design | 15 | P2 |
| Phase 7 | Performance Optimization | 18 | P2 |
| Phase 8 | Polish & Deployment | 20 | P0 |

---

## 🔧 Codex CLI vs Claude Code 差異

### Codex CLI 沒有的功能

❌ **SpecKit Commands** - 無法使用以下命令：
```
/speckit.tasks
/speckit.plan
/speckit.specify
```

❌ **TodoWrite Tool** - 無內建任務追蹤系統

❌ **自動文檔生成** - 需要手動參考已生成的文檔

### Codex CLI 有的功能

✅ **所有基本工具**:
- Read, Write, Edit - 檔案操作
- Bash - 執行命令
- Grep, Glob - 搜索功能
- Git 操作

✅ **開發工具**:
- npm/yarn 包管理
- TypeScript 編譯
- Playwright 測試
- Vite 開發服務器

✅ **AI能力**:
- 理解複雜的Markdown文檔
- 生成React/TypeScript代碼
- 創建測試用例
- 調試和修復問題

---

## 📁 關鍵文檔路徑

**項目根目錄**:
```
/Users/albertking/ES/cms_automation/
```

**前端目錄**:
```
/Users/albertking/ES/cms_automation/frontend/
```

**規格文檔目錄**:
```
/Users/albertking/ES/cms_automation/specs/002-ui-modernization/
├── spec.md           # 功能規格 (5個User Stories, 50+需求)
├── plan.md           # 實施計劃 (8階段, 技術棧, 憲法合規)
├── tasks.md          # ⭐ 146個任務清單 (你的主要參考)
├── research.md       # 技術決策 (Sonner選擇, 性能優化策略)
├── contracts/
│   ├── components.md # TypeScript接口定義 (32KB)
│   └── ...
├── data-model.md     # 設計Token和狀態模型
└── quickstart.md     # 開發指南和範例代碼 (29KB)
```

---

## 🚀 快速開始

### 第一步：準備環境

在Codex CLI中執行以下對話：

```
請幫我準備繼續UI現代化項目：

1. 檢查當前Git狀態
   - 確認在 002-ui-modernization 分支
   - 列出最近5個commits

2. 檢查開發環境
   - Node.js版本
   - npm packages是否安裝完整
   - dev server是否正在運行

3. 讀取項目狀態
   - 查看 /Users/albertking/ES/cms_automation/specs/002-ui-modernization/tasks.md
   - 告訴我Phase 4有哪些任務
   - 確認Phase 1-3的所有commit都存在
```

### 第二步：開始Phase 4

```
我要開始Phase 4: Settings Page Enhancement。

Phase 1-3已完成：
- ✅ Project setup (Sonner, directories, cn() utility)
- ✅ Navigation responsive design (desktop + mobile)
- ✅ E2E tests (11/15 passing)

請閱讀 tasks.md 中的 Phase 4 部分，然後：

1. 列出Phase 4的所有34個任務
2. 識別第一個任務 (應該是T036 - Skeleton組件)
3. 檢查是否有依賴未完成
4. 開始執行第一個任務

參考文檔：
- 組件接口: specs/002-ui-modernization/contracts/components.md
- 實施指南: specs/002-ui-modernization/quickstart.md
```

---

## 📋 Phase 4 任務清單

### Phase 4: Settings Page Enhancement (US2, P1) - 34 tasks

**目標**: 增強Settings頁面的視覺設計和交互體驗

#### 4.1 基礎組件創建 (T036-T043)

- [ ] **T036** Create Skeleton loading component
  - 文件: `frontend/src/components/ui/Skeleton.tsx`
  - 參考: `contracts/components.md` - SkeletonProps

- [ ] **T037** Create Toast notification system using Sonner
  - 文件: `frontend/src/components/ui/Toast.tsx`
  - Hook: `frontend/src/hooks/useToast.ts`
  - 參考: `research.md` - Sonner decision

- [ ] **T038** Create Spinner loading component
  - 文件: `frontend/src/components/ui/Spinner.tsx`
  - 參考: `contracts/components.md` - SpinnerProps

- [ ] **T039** Create enhanced Input component
  - 文件: `frontend/src/components/ui/Input.tsx`
  - 參考: `contracts/components.md` - InputProps

- [ ] **T040** Create enhanced Textarea component
  - 文件: `frontend/src/components/ui/Textarea.tsx`
  - 參考: `contracts/components.md` - TextareaProps

- [ ] **T041** Create enhanced Toggle/Switch component
  - 文件: `frontend/src/components/ui/Toggle.tsx`
  - 參考: `contracts/components.md` - ToggleProps

- [ ] **T042** Create Select dropdown component
  - 文件: `frontend/src/components/ui/Select.tsx`
  - 參考: `contracts/components.md` - SelectProps

- [ ] **T043** Create Badge component
  - 文件: `frontend/src/components/ui/Badge.tsx`
  - 參考: `contracts/components.md` - BadgeProps

#### 4.2 Settings頁面增強 (T044-T060)

- [ ] **T044** Add loading states with Skeleton
- [ ] **T045** Implement Toast notifications for save operations
- [ ] **T046** Add Spinner for async operations
- [ ] **T047** Replace input fields with enhanced Input component
- [ ] **T048** Add form validation with error messages
- [ ] **T049** Implement unsaved changes detection
- [ ] **T050** Add confirmation dialog for unsaved changes
- [ ] **T051** Improve section dividers with visual hierarchy
- [ ] **T052** Add smooth animations for Accordion sections
- [ ] **T053** Implement focus management
- [ ] **T054** Add keyboard shortcuts hints
- [ ] **T055** Improve color contrast for accessibility
- [ ] **T056** Add aria-labels for screen readers
- [ ] **T057** Implement field descriptions/help text
- [ ] **T058** Add reset to defaults functionality
- [ ] **T059** Improve mobile responsive layout for Settings
- [ ] **T060** Add settings validation feedback

#### 4.3 測試和文檔 (T061-T069)

- [ ] **T061** Create E2E tests for Skeleton component
- [ ] **T062** Create E2E tests for Toast notifications
- [ ] **T063** Create E2E tests for enhanced Settings form
- [ ] **T064** Create E2E tests for form validation
- [ ] **T065** Create E2E tests for unsaved changes dialog
- [ ] **T066** Test accessibility with screen readers
- [ ] **T067** Test keyboard navigation in Settings
- [ ] **T068** Document Settings component usage
- [ ] **T069** Update Storybook stories for new components

---

## 💬 Codex對話模板

### 模板1: 執行單個任務

```
任務ID: T036
任務: Create Skeleton loading component
文件路徑: frontend/src/components/ui/Skeleton.tsx

請執行以下步驟：

1. 閱讀組件接口定義
   - 文件: specs/002-ui-modernization/contracts/components.md
   - 搜索: "SkeletonProps"

2. 創建組件
   - 實現所有必需的props
   - 使用Tailwind CSS
   - 支持不同variants (text, circular, rectangular)
   - 添加動畫效果

3. 創建範例用法
   - 在組件文件中添加JSDoc註釋
   - 包含使用範例

4. 驗證
   - 運行 TypeScript 編譯檢查
   - 確認沒有類型錯誤

5. 提交
   - Commit message: "feat(ui): T036 - Add Skeleton loading component"
```

### 模板2: 批量執行相關任務

```
我要執行Phase 4的組件創建任務 (T036-T043)。

這8個任務都是創建UI組件：
- T036: Skeleton
- T037: Toast (使用Sonner)
- T038: Spinner
- T039: Input
- T040: Textarea
- T041: Toggle
- T042: Select
- T043: Badge

請按順序執行，每個組件：
1. 參考 contracts/components.md 中的接口定義
2. 使用 cn() utility 處理className
3. 確保TypeScript類型正確
4. 添加詳細的JSDoc註釋
5. 每完成一個就提交一次

完成後告訴我總共創建了多少個組件文件。
```

### 模板3: 處理錯誤

```
我在執行任務時遇到錯誤：

[貼上錯誤訊息]

請幫我：
1. 分析錯誤原因
2. 檢查相關文件
3. 提供修復方案
4. 應用修復
5. 驗證修復成功
```

### 模板4: 運行測試

```
我想驗證剛完成的任務。

已完成任務: T036-T043 (8個UI組件)

請執行：
1. TypeScript編譯檢查
   npm run build

2. 運行dev server確認沒有runtime錯誤
   npm run dev

3. 如果有測試，運行測試套件
   npm run test

4. 檢查Git狀態
   git status
   git log --oneline -n 5

告訴我是否一切正常，或有什麼需要修復。
```

---

## 🎯 執行策略建議

### 策略A: 按任務順序執行（推薦新手）

**優點**: 清晰、按部就班、不易遺漏
**缺點**: 可能較慢

**執行方式**:
```
第1天: T036-T040 (5個基礎組件)
第2天: T041-T045 (3個組件 + 開始集成)
第3天: T046-T055 (Settings頁面增強)
第4天: T056-T060 (可訪問性和驗證)
第5天: T061-T069 (測試和文檔)
```

### 策略B: 按功能模塊執行（推薦有經驗者）

**優點**: 快速、高效、可並行
**缺點**: 需要對項目有全面理解

**執行方式**:
```
模塊1: UI組件庫 (T036-T043) - 一次性完成所有組件
模塊2: Settings集成 (T044-T053) - 整合到Settings頁面
模塊3: 可訪問性 (T054-T060) - ARIA和鍵盤支持
模塊4: 測試 (T061-T067) - E2E測試套件
模塊5: 文檔 (T068-T069) - 使用指南
```

### 策略C: 混合式執行（推薦）

**第一輪**: 創建所有基礎組件 (T036-T043)
```
"請一次性創建8個UI組件，參考contracts/components.md"
```

**第二輪**: 集成到Settings頁面 (T044-T053)
```
"現在將這些組件集成到SettingsPageModern.tsx"
```

**第三輪**: 增強功能 (T054-T060)
```
"添加可訪問性支持和高級功能"
```

**第四輪**: 測試和文檔 (T061-T069)
```
"創建測試並更新文檔"
```

---

## 📝 進度追蹤方式

### 方法1: Git Commit Messages（推薦）

每個任務完成後提交，使用標準化的commit message：

```bash
git commit -m "feat(ui): T036 - Add Skeleton loading component"
git commit -m "feat(ui): T037 - Add Toast notification system"
git commit -m "test(ui): T061 - Add E2E tests for Skeleton"
```

**查看進度**:
```bash
git log --oneline --grep="T0" | wc -l  # 統計完成的任務數
```

### 方法2: Progress Markdown文件

創建一個進度追蹤文件：

```markdown
# UI現代化項目進度

## Phase 4: Settings Page Enhancement

### 進度統計
- 總任務數: 34
- 已完成: 8
- 進行中: 1
- 待開始: 25
- 完成率: 24%

### 已完成任務
- [x] T036 - Skeleton component (2024-11-04)
- [x] T037 - Toast system (2024-11-04)
- [x] T038 - Spinner component (2024-11-04)
...

### 當前任務
- [ ] T039 - Enhanced Input component (進行中)

### 待完成任務
- [ ] T040 - Textarea component
- [ ] T041 - Toggle component
...
```

**Codex對話**:
```
請更新進度文件 specs/002-ui-modernization/progress.md
任務T036-T038已完成，T039進行中
```

### 方法3: tasks.md直接標記

**Codex對話**:
```
請在 specs/002-ui-modernization/tasks.md 中：
1. 將任務T036的 [ ] 改為 [x]
2. 添加完成日期註釋
3. 不要修改其他任務
```

---

## 🔍 常見問題和解決方案

### Q1: Codex找不到某個文件

**症狀**: "Error: File not found"

**解決方案**:
```
請先確認文件路徑：
1. 使用絕對路徑: /Users/albertking/ES/cms_automation/...
2. 檢查當前工作目錄: pwd
3. 列出目錄內容: ls -la /path/to/directory
```

### Q2: TypeScript類型錯誤

**症狀**: 編譯時出現類型錯誤

**解決方案**:
```
我遇到TypeScript錯誤：
[貼上錯誤訊息]

請：
1. 讀取 contracts/components.md 確認正確的接口定義
2. 檢查導入語句是否正確
3. 確認所有必需的props都已實現
4. 修復錯誤並重新編譯
```

### Q3: 不確定如何實現某個組件

**解決方案**:
```
我要實現T036 Skeleton組件，但不確定具體細節。

請：
1. 讀取 contracts/components.md 中的SkeletonProps
2. 讀取 quickstart.md 中的組件範例
3. 參考已完成的Navigation.tsx作為範本
4. 根據這些信息生成完整的組件代碼
```

### Q4: 測試失敗

**症狀**: E2E測試運行失敗

**解決方案**:
```
測試失敗：[test_name]
錯誤：[error_message]

請：
1. 檢查組件實現是否與測試預期一致
2. 查看測試截圖: test-results/[test-name]/
3. 確認選擇器是否正確
4. 修復問題並重新運行測試
```

### Q5: Git衝突

**症狀**: git pull時出現merge衝突

**解決方案**:
```
我遇到Git衝突，請幫我：
1. 查看衝突文件: git status
2. 讀取衝突內容
3. 決定保留哪個版本（通常保留本地更改）
4. 解決衝突並提交
```

---

## ✅ 檢查清單

### 開始新任務前
- [ ] 確認在正確的Git分支 (`002-ui-modernization`)
- [ ] 讀取任務描述 (tasks.md)
- [ ] 檢查依賴任務是否完成
- [ ] 準備參考文檔 (contracts/, quickstart.md)

### 完成任務後
- [ ] 代碼通過TypeScript編譯
- [ ] 沒有ESLint警告
- [ ] 組件可以正常導入和使用
- [ ] 添加了適當的註釋
- [ ] Git commit with proper message
- [ ] 更新進度追蹤

### 完成一個Phase後
- [ ] 所有任務都已完成並提交
- [ ] 運行完整的測試套件
- [ ] 本地dev server正常運行
- [ ] 更新CHANGELOG或progress.md
- [ ] 推送到遠端分支

---

## 🎓 最佳實踐

### 1. 代碼質量
- 使用 `cn()` utility 處理className
- 遵循已有代碼的風格
- 添加詳細的JSDoc註釋
- 實現完整的TypeScript類型

### 2. Git工作流
- 每完成1-3個相關任務提交一次
- 使用描述性的commit message
- 包含任務ID便於追蹤
- 定期推送避免丟失工作

### 3. 測試策略
- 先實現功能，再寫測試
- 每完成幾個組件運行一次測試
- 測試失敗時立即修復
- 保持至少70%的測試通過率

### 4. 與Codex溝通
- 提供清晰的上下文
- 引用具體的文件路徑
- 描述預期結果
- 要求確認關鍵決策

### 5. 遇到困難時
- 先參考已完成的代碼
- 查閱文檔 (quickstart.md, contracts/)
- 將大任務分解為小步驟
- 向Codex尋求具體的幫助

---

## 📞 需要幫助？

### Codex對話範例

**一般幫助**:
```
我在執行Phase 4任務時需要幫助。
當前任務: T[編號]
問題: [描述具體問題]
已嘗試: [你已經做過的事]

請提供建議或解決方案。
```

**代碼審查**:
```
我剛完成任務T036-T040，請幫我審查代碼：
1. 檢查TypeScript類型是否正確
2. 確認遵循項目規範
3. 建議改進空間
4. 運行編譯測試

涉及的文件：
- src/components/ui/Skeleton.tsx
- src/components/ui/Toast.tsx
...
```

**進度確認**:
```
請幫我確認Phase 4的進度：
1. 讀取 tasks.md Phase 4部分
2. 統計已完成的任務（通過git log）
3. 列出還未完成的任務
4. 估算剩餘工作量
```

---

## 🎯 成功完成Phase 4的標誌

1. **所有34個任務完成** ✅
2. **至少20個新的組件文件創建** ✅
3. **Settings頁面顯著改善** ✅
4. **測試覆蓋率提升** ✅
5. **無TypeScript編譯錯誤** ✅
6. **所有更改已提交並推送** ✅

---

## 📚 附錄

### A. 任務ID速查表

**Phase 4任務範圍**: T036 - T069 (34個任務)

**關鍵里程碑**:
- T043: 所有基礎組件完成
- T053: Settings集成完成
- T060: 可訪問性完成
- T069: Phase 4完成

### B. 檔案結構參考

```
frontend/
├── src/
│   ├── components/
│   │   ├── ui/              # 新組件目錄
│   │   │   ├── Skeleton.tsx (T036)
│   │   │   ├── Toast.tsx    (T037)
│   │   │   ├── Spinner.tsx  (T038)
│   │   │   ├── Input.tsx    (T039)
│   │   │   ├── Textarea.tsx (T040)
│   │   │   ├── Toggle.tsx   (T041)
│   │   │   ├── Select.tsx   (T042)
│   │   │   └── Badge.tsx    (T043)
│   │   └── layout/
│   │       ├── Navigation.tsx (已完成)
│   │       └── MobileMenu.tsx (已完成)
│   ├── hooks/
│   │   └── useToast.ts      (T037)
│   ├── lib/
│   │   └── cn.ts            (已完成)
│   └── pages/
│       └── SettingsPageModern.tsx (需更新)
└── e2e/
    ├── navigation.spec.ts   (已完成)
    └── settings.spec.ts     (T061-T067)
```

### C. 有用的命令

```bash
# 檢查TypeScript
npm run build

# 開發服務器
npm run dev

# 運行測試
npm run test:e2e

# 檢查Git狀態
git status
git log --oneline -n 10

# 查看任務進度
git log --oneline --grep="T0" --grep="T1"

# 推送更改
git push origin 002-ui-modernization
```

---

**版本**: 1.0.0
**最後更新**: 2024-11-04
**維護者**: AI Assistant (Claude Code)
**適用於**: Codex CLI, Claude Code, 其他AI編碼助手
