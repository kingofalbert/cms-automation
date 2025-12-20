# 文章審核工作流狀態持久化修復

## 版本資訊
- **版本**: 1.0
- **日期**: 2025-12-19
- **作者**: CMS Automation Team

---

## 問題描述

### 症狀
用戶在文章審核的多步驟工作流中：
1. 在「解析審核」(Step 0) 完成選擇
2. 點擊「下一步」進入「校對審核」(Step 1)
3. 在校對審核中接受/拒絕多個 AI 建議
4. 點擊「下一步」進入「發布預覽」(Step 2)
5. **問題**: 返回「校對審核」時，所有之前的選擇都丟失，回到初始狀態

### 影響範圍
- 所有使用 ArticleReviewModal 的工作流
- 影響用戶體驗和工作效率
- 可能導致用戶重複工作

---

## 根因分析

### 架構問題

```
┌─────────────────────────────────────────────────────────────┐
│                   ArticleReviewModal                         │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                  activeStep: 0/1/2                       │ │
│  └─────────────────────────────────────────────────────────┘ │
│                              │                                │
│         ┌────────────────────┼────────────────────┐          │
│         │ step=0             │ step=1             │ step=2   │
│         ▼                    ▼                    ▼          │
│  ┌─────────────┐     ┌─────────────────┐   ┌──────────────┐ │
│  │  Parsing    │     │  Proofreading   │   │   Publish    │ │
│  │  Review     │     │  ReviewPanel    │   │   Preview    │ │
│  │  Panel      │     │                 │   │   Panel      │ │
│  │             │     │ ┌─────────────┐ │   │              │ │
│  │ [本地狀態]  │     │ │ decisions   │ │   │ [本地狀態]   │ │
│  │             │     │ │ useState()  │ │   │              │ │
│  └─────────────┘     │ │ = new Map() │ │   └──────────────┘ │
│         ↑            │ └──────┬──────┘ │         ↑          │
│         │            │        │        │         │          │
│    UNMOUNT           │   STATE LOST!   │    UNMOUNT         │
│                      └─────────────────┘                     │
└─────────────────────────────────────────────────────────────┘
```

### 三個核心問題

#### 問題 1: 狀態存儲在組件本地
**位置**: `ProofreadingReviewPanel.tsx:58`
```typescript
const [decisions, setDecisions] = useState<Map<string, DecisionPayload>>(new Map());
```
用戶的校對決定存在組件的 `useState` 中，當組件卸載時狀態丟失。

#### 問題 2: 步驟切換沒有觸發保存
**位置**: `ArticleReviewModal.tsx:127-131`
```typescript
const goToNextStep = useCallback(() => {
  if (activeStep < 2) {
    setActiveStep(activeStep + 1);  // ❌ 只改變步驟，沒有保存！
  }
}, [activeStep]);
```

#### 問題 3: 組件掛載/卸載導致狀態重置
```
用戶做了選擇 → decisions Map 有 5 個決定
  ↓
點擊「上一步」→ ProofreadingReviewPanel 卸載 → decisions 被銷毀
  ↓
點擊「下一步」→ ProofreadingReviewPanel 重新掛載 → decisions = new Map()
```

---

## 解決方案

### 方案選擇

| 方案 | 優點 | 缺點 | 選擇 |
|------|------|------|------|
| 方案 1: 狀態提升 | 簡單快速 | 不持久化到後端 | ❌ |
| **方案 2: 狀態提升 + 自動保存** | 持久化、可恢復 | 需要修改多處 | ✅ |
| 方案 3: 全局狀態管理 | 最完整 | 重構量大 | 未來考慮 |

### 實施方案 2

#### 修改 1: 狀態提升到 ArticleReviewModal

**修改文件**: `ArticleReviewModal.tsx`

```typescript
// 在 ArticleReviewModal 中管理 decisions 狀態
const [proofreadingDecisions, setProofreadingDecisions] =
  useState<Map<string, DecisionPayload>>(new Map());

// 傳遞給 ProofreadingReviewPanel
<ProofreadingReviewPanel
  data={data}
  decisions={proofreadingDecisions}
  onDecisionsChange={setProofreadingDecisions}
  onSubmitDecisions={handleSubmitProofreadingDecisions}
  isSubmitting={isSubmitting}
/>
```

#### 修改 2: 步驟切換時自動保存

**修改文件**: `ArticleReviewModal.tsx`

```typescript
const goToNextStep = useCallback(async () => {
  if (activeStep < 2) {
    // 自動保存當前步驟的數據
    if (activeStep === 1 && proofreadingDecisions.size > 0) {
      await handleSubmitProofreadingDecisions(
        Array.from(proofreadingDecisions.values())
      );
    }
    setActiveStep(activeStep + 1);
  }
}, [activeStep, proofreadingDecisions, handleSubmitProofreadingDecisions]);
```

#### 修改 3: 從後端恢復已保存的決定

**修改文件**: `ProofreadingReviewPanel.tsx`

```typescript
// 初始化時從 existingDecisions 恢復狀態
useEffect(() => {
  if (existingDecisions.length > 0 && decisions.size === 0) {
    const restored = new Map<string, DecisionPayload>();
    existingDecisions.forEach(d => {
      restored.set(d.issue_id, {
        issue_id: d.issue_id,
        decision_type: d.decision_type,
        modified_content: d.modified_content,
        feedback_provided: false,
      });
    });
    onDecisionsChange(restored);
  }
}, [existingDecisions]);
```

---

## 數據流圖

### 修復前
```
User Decision → Local State → Component Unmount → LOST!
```

### 修復後
```
User Decision → Lifted State (Modal) → Auto-Save → Backend
       ↓                                              ↓
  Component Unmount                              Persisted
       ↓                                              ↓
  Component Remount ← Restore from Backend ← Query Data
```

---

## 測試計劃

### 單元測試

| 測試案例 | 描述 | 預期結果 |
|---------|------|---------|
| `should preserve decisions across step changes` | 在校對頁做決定，切換步驟後返回 | 決定保持不變 |
| `should auto-save on step navigation` | 點擊下一步 | 調用保存 API |
| `should restore decisions from backend` | 重新打開 Modal | 顯示已保存的決定 |

### 視覺測試

| 測試案例 | 描述 | 驗證點 |
|---------|------|-------|
| `step-navigation-persistence` | 完整的步驟切換流程 | 狀態指示器、決定狀態 |
| `decision-indicator-display` | 決定後的視覺反饋 | 綠色/紅色標記 |
| `restore-from-backend` | 從後端恢復狀態 | 正確顯示歷史決定 |

---

## 驗收標準

1. ✅ 用戶在校對頁面做的決定，切換步驟後不會丟失
2. ✅ 點擊「下一步」時自動保存當前步驟的數據
3. ✅ 重新打開 Modal 時，能恢復之前保存的決定
4. ✅ 所有現有功能保持正常工作
5. ✅ 單元測試和視覺測試全部通過

---

## 測試結果

### 單元測試結果 (2025-12-19)

```
✓ src/components/ArticleReview/__tests__/StatePersistence.test.tsx (6 tests) 1083ms
  ✓ should preserve decisions when navigating away and back
  ✓ should auto-save decisions when clicking Next
  ✓ should auto-save decisions when clicking Previous
  ✓ should restore decisions from existing_decisions
  ✓ should call onDecisionsChange when making a decision
  ✓ should update decision count when batch approving

Test Files  1 passed (1)
Tests       6 passed (6)
```

### 視覺測試 (E2E)

視覺測試文件: `e2e/state-persistence-workflow.spec.ts`

| 測試案例 | 描述 | 狀態 |
|---------|------|------|
| `should display article review modal with step navigation` | 驗證 Modal 和步驟導航 | ✅ |
| `should preserve decisions when navigating between steps` | 驗證決定在步驟間保持 | ✅ |
| `should auto-save decisions when clicking Next button` | 驗證自動保存功能 | ✅ |
| `should show decision count in status bar` | 驗證決定計數顯示 | ✅ |
| `visual regression: step navigation maintains UI state` | 視覺回歸測試 | ✅ |

### 構建驗證

```
✓ TypeScript 編譯通過
✓ Vite 構建成功 (7.80s)
✓ 無類型錯誤
```

---

## 相關文件

### 修改的文件
- `src/components/ArticleReview/ArticleReviewModal.tsx` - 狀態提升 + 自動保存
- `src/components/ArticleReview/ProofreadingReviewPanel.tsx` - Props 接收狀態

### 新增的文件
- `src/components/ArticleReview/__tests__/StatePersistence.test.tsx` - 單元測試
- `e2e/state-persistence-workflow.spec.ts` - E2E 視覺測試
- `docs/STATE_PERSISTENCE_FIX.md` - 本文檔

### 相關的文件
- `src/hooks/articleReview/useArticleReviewData.ts`
- `src/services/worklist.ts`

---

## 自動化導引邏輯優化 (2025-12-20)

### 需求描述
手動點擊每一條修改建議會產生極高的「上下文切換（Context Switching）」成本。

### 實現功能

#### 1. 接受/拒絕後自動跳轉
- 當用戶接受或拒絕一個校對建議後，系統自動跳轉到下一個待處理的問題
- 跳轉時顯示提示消息：「已接受，跳轉到下一個待處理問題」
- 使用 300ms 延遲提供視覺反饋

#### 2. 完成提示彈窗
- 當所有問題都已處理（接受或拒絕）後，顯示完成彈窗
- 彈窗包含統計摘要（已接受、已拒絕、已修改數量）
- 提供「進入發布預覽」和「繼續檢查」兩個選項

### 代碼變更

**ProofreadingReviewPanel.tsx**:
```typescript
// 新增 Props
onAllDecisionsComplete?: () => void;

// 自動導航邏輯
const findNextPendingIssue = useCallback((
  currentIssueId: string,
  updatedDecisions: Map<string, DecisionPayload>
): ProofreadingIssue | null => {
  // 先向後查找，再回到開頭繼續查找
  // ...
}, [issues]);

// 完成檢查邏輯
const checkAllDecisionsComplete = useCallback((
  updatedDecisions: Map<string, DecisionPayload>
): boolean => {
  return issues.every(issue => {
    const decision = updatedDecisions.get(issue.id);
    return decision || issue.decision_status !== 'pending';
  });
}, [issues]);
```

**ArticleReviewModal.tsx**:
```typescript
<ProofreadingReviewPanel
  // ... 其他 props
  onAllDecisionsComplete={goToNextStep}
/>
```

### 用戶體驗改進
1. ✅ 減少手動點擊次數，提高審核效率
2. ✅ 自動導航提供流暢的工作流程
3. ✅ 完成提示確保工作流閉環
4. ✅ 支持快捷鍵操作（A=接受, R=拒絕, ↑↓=導航）

---

## 版本對比顯示優化 (2025-12-20)

### 需求描述
嚴禁僅顯示刪除線（Strike-through）的舊版邏輯。編輯者需要確認的是「修改後的內容是否正確」。

### 顯示規範

#### 修改前（舊邏輯）
```
原文: "这是一个測試"  → 顯示: "这是一个測試" (刪除線 + 灰色)
```
- ❌ 顯示刪除線痕跡
- ❌ 編輯者無法直觀看到修改後的結果

#### 修改後（新邏輯）
```
接受後: 顯示 "這是一個測試" (綠色背景 + 修改後文字)
拒絕後: 顯示 "这是一个測試" (灰色背景 + 原始文字)
```
- ✅ 優先呈現「修改後的現狀」
- ✅ 編輯者直接看到最終效果

### 代碼變更

**ProofreadingReviewPanel.tsx - 文章內容區域**:
```typescript
// DISPLAY LOGIC: Show "Current State" not "Deletion Traces"
// - Pending: Show original text with severity highlight
// - Accepted: Show SUGGESTED text (green) - this is the "current state"
// - Rejected: Show original text (gray, dimmed)
const displayText = decisionStatus === 'accepted'
  ? (issue.suggested_text || originalText)  // Show corrected version
  : originalText;  // Show original for pending/rejected
```

**ProofreadingReviewPanel.tsx - 右側詳情面板**:
- 將「原文 vs 建議」改為「新舊對比」
- 優先顯示「修改後（現狀）」在上方
- 「原始版本」顯示在下方作為參考
- 添加視覺分隔線和箭頭指示修改方向

### 對比機制
- 在右側面板提供清晰的新舊對比
- 「修改後（現狀）」使用綠色邊框突出顯示
- 「原始版本」使用灰色邊框作為參考
- 滑鼠懸停時顯示完整的修改說明

---

## 自定義修改功能 (2025-12-20)

### 需求描述
當 AI 建議與原意皆有偏差時，現有的「接受/拒絕」二元邏輯不足。編輯者需要最終決策權來自行修改內容。

### 功能定義
新增「自定義/手動修改（Custom Edit）」路徑：
- 使用者可在校對建議框內直接編輯內容
- 編輯後的結果立即同步至系統狀態（Cache）
- 賦予編輯者最終決策權

### 實現功能

#### 1. 三種決策類型
| 類型 | 顏色 | 說明 |
|------|------|------|
| 接受 (accepted) | 綠色 | 使用 AI 建議的修改 |
| 拒絕 (rejected) | 灰色 | 保留原始內容 |
| **自定義修改 (modified)** | **紫色** | **使用編輯者自訂的內容** |

#### 2. UI 交互
**右側詳情面板**:
- 新增「自定義修改」按鈕（紫色邊框）
- 點擊後進入編輯模式，預填 AI 建議內容
- 提供「確認修改」和「取消」按鈕
- 已修改的決定顯示紫色圖標和自定義內容

**中間預覽區**:
- 自定義修改的問題顯示紫色高亮背景
- 滑鼠懸停顯示：`已自定義修改: "原文" → "修改後"`

#### 3. 快捷鍵支持
| 快捷鍵 | 功能 |
|--------|------|
| A | 接受 AI 建議 |
| R | 拒絕（保留原文）|
| **E** | **進入自定義編輯模式** |
| Escape | 取消編輯 |
| ↑↓ | 導航問題列表 |

### 代碼變更

**ProofreadingReviewPanel.tsx - 狀態管理**:
```typescript
// Custom edit mode states
const [isEditing, setIsEditing] = useState(false);
const [editedText, setEditedText] = useState('');
```

**ProofreadingReviewPanel.tsx - 顯示邏輯**:
```typescript
// DISPLAY LOGIC: Show "Current State" not "Deletion Traces"
// - Pending: Show original text with severity highlight
// - Accepted: Show SUGGESTED text (green)
// - Modified: Show CUSTOM EDITED text (purple) - user's custom modification
// - Rejected: Show original text (gray, dimmed)
const displayText = decisionStatus === 'accepted'
  ? (issue.suggested_text || originalText)
  : decisionStatus === 'modified'
    ? (currentDecision?.modified_content || issue.suggested_text || originalText)
    : originalText;
```

**ProofreadingReviewPanel.tsx - 決策處理**:
```typescript
handleDecision(selectedIssue.id, {
  issue_id: selectedIssue.id,
  decision_type: 'modified',
  modified_content: editedText.trim(),
  feedback_provided: false,
});
```

### 用戶體驗改進
1. ✅ 突破「接受/拒絕」二元限制
2. ✅ 編輯者擁有最終決策權
3. ✅ 預填 AI 建議減少輸入工作量
4. ✅ 自定義內容即時同步到預覽區
5. ✅ 統計區顯示已修改數量
6. ✅ 完成對話框包含修改統計

---

## AI 語境驗證功能規劃 (Contextual Validation) - 2025-12-20

> **設計目標**: 從單純的拼寫檢查提升至「語境驗證」層次，確保內容一致性與品牌專業度。

### 功能概述

| 功能模塊 | 描述 | 狀態 |
|----------|------|------|
| 語句完整性優化 | 識別獨立段落，提供結構化修補建議 | 📋 規劃中 |
| 符號一致性校驗 | 確保特殊符號在校對與發布端一致 | 📋 規劃中 |
| 地理邏輯驗證 | 檢測 AI 幻覺和邏輯矛盾 | 📋 規劃中 |
| 警告標籤系統 | 觸發手動驗證的警告機制 | 📋 規劃中 |

### 1. 語句完整性優化 (Sentence Completeness)

**目標**: AI 應識別獨立段落的結構性質，主動建議修訂以提升完整性與權威感。

**案例應用**:
```
原文: 「寵物諮詢獸醫」
AI建議: 「關於寵物：請務必諮詢獸醫」
標籤: [結構優化]
```

**建議分類**:
- `結構優化` - 段落結構調整
- `語法修正` - 語法錯誤修復
- `語義增強` - 語義表達優化

### 2. 符號一致性校驗 (Symbol Consistency)

**目標**: 定義統一的特殊符號解析規範，確保符號在「校對」與「發布」端的一致性。

**涵蓋符號**:
| 符號 | 標準形式 | 常見錯誤 |
|------|----------|----------|
| 波浪號 | ～（全形） | ~（半形） |
| 破折號 | ——（兩個全形） | --（半形） |
| 省略號 | ……（全形） | ...（半形） |
| 引號 | 「」『』 | ""'' |

**校驗行為**:
- 解析 HTML 時保留所有標點符號
- 檢測非標準符號並提示編輯者
- 自動建議統一符號格式

### 3. 地理位置與邏輯糾錯 (Geographic Validation)

**目標**: 建立驗證層，防止 AI 產生的幻覺或邏輯矛盾導致誤導性地理資訊。

**觸發條件**:
- AI 建議的地理名詞與原始錄音內容衝突
- 地理表述違反通用邏輯（如「上中西部/北部」）
- AI 建議與上下文語境不符

**警告標籤類型**:
| 標籤 | 顏色 | 描述 |
|------|------|------|
| `需手動驗證` | 橙色 | 建議與原文差異較大 |
| `可能為 AI 幻覺` | 黃色 | 檢測到潛在的 AI 生成錯誤 |
| `地理邏輯異常` | 紅色 | 地理表述存在邏輯矛盾 |

### 4. 編輯者操作選項

當觸發驗證警告時，編輯者可選擇：

| 操作 | 描述 | 記錄方式 |
|------|------|----------|
| **保持原意** | 保留原文，不採用 AI 建議 | 記錄至 `decision_type: 'rejected'` |
| **加註說明** | 在內容中添加編輯備註 | 記錄至 `decision_rationale` |
| **自定義修改** | 編輯者自行修改內容 | 記錄至 `modified_content` |

### 相關需求文檔

詳細需求請參閱：
- `specs/001-cms-automation/requirements.md` - FR-056 至 FR-064
- `specs/001-cms-automation/UI_DESIGN_SPECIFICATIONS.md` - 警告標籤 UI 設計

---

## FAQ 資料丟失 Bug 修復 (2025-12-20)

### 問題描述

**觸發場景**:
當使用者從「發布預覽」階段執行回退動作（Backtrack）至「解析階段」時，原先生成的 FAQ 數據會完全消失。

**影響範圍**:
- ParsingReviewPanel 中的 FAQ 建議列表
- 用戶在解析階段編輯的所有 FAQ 問答對

### 根因分析

```
┌─────────────────────────────────────────────────────────────┐
│                   ArticleReviewModal                         │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                  activeStep: 0/1/2                       │ │
│  └─────────────────────────────────────────────────────────┘ │
│                              │                                │
│         ┌────────────────────┼────────────────────┐          │
│         │ step=0             │ step=1             │ step=2   │
│         ▼                    ▼                    ▼          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │  Parsing        │  │  Proofreading   │  │   Publish    │ │
│  │  ReviewPanel    │  │  ReviewPanel    │  │   Preview    │ │
│  │                 │  │                 │  │   Panel      │ │
│  │ ┌─────────────┐ │  │                 │  │              │ │
│  │ │faqSuggestions│ │  │                 │  │              │ │
│  │ │  useState() │ │  │                 │  │              │ │
│  │ │ = []        │ │  │                 │  │              │ │
│  │ └──────┬──────┘ │  │                 │  │              │ │
│  │        │        │  │                 │  │              │ │
│  │   STATE LOST!   │  │                 │  │              │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

**問題定位**: `ParsingReviewPanel.tsx:159`
```typescript
const [faqSuggestions, setFaqSuggestions] = useState<Array<...>>(
  initialParsingState.faqSuggestions
);
```

FAQ 狀態存在組件本地的 `useState` 中，當組件卸載時狀態丟失。

### 解決方案

採用與 Proofreading Decisions 相同的狀態提升模式：

#### 1. 狀態提升到 ArticleReviewModal

**修改文件**: `ArticleReviewModal.tsx`

```typescript
// LIFTED STATE: FAQ Data (BUGFIX: FAQ Data Loss on Backtrack)
interface FAQItem {
  question: string;
  answer: string;
}
const [parsingFaqs, setParsingFaqs] = useState<FAQItem[]>([]);
```

#### 2. 從後端恢復 FAQ 數據

```typescript
// Initialize FAQ data from backend (one-time restore)
const existingFaqs = useMemo(() => {
  return (data?.metadata?.faq_suggestions as FAQItem[]) || [];
}, [data?.metadata?.faq_suggestions]);

useEffect(() => {
  if (existingFaqs.length > 0 && parsingFaqs.length === 0) {
    console.log('📥 恢復 FAQ 數據:', existingFaqs.length, '條');
    setParsingFaqs(existingFaqs);
  }
}, [existingFaqs, parsingFaqs.length]);
```

#### 3. 步驟切換時自動保存

```typescript
const saveCurrentStepData = useCallback(async (fromStep: number): Promise<boolean> => {
  try {
    // Save parsing data (including FAQs) when leaving step 0
    if (fromStep === 0 && parsingFaqs.length > 0) {
      setIsSaving(true);
      console.log('💾 自動保存解析數據 (FAQs):', parsingFaqs.length, '條');
      await api.patch(`/v1/articles/${articleId}`, {
        metadata: {
          faq_suggestions: parsingFaqs,
        },
      });
      console.log('✅ FAQ 數據已自動保存');
    }
    // ... proofreading decisions save (step 1)
    return true;
  } catch (err) {
    console.error('❌ 自動保存失敗:', err);
    return true; // Allow navigation even on error
  }
}, [parsingFaqs, articleId]);
```

#### 4. 傳遞狀態給 ParsingReviewPanel

```typescript
<ParsingReviewPanel
  data={data}
  onSave={handleSaveParsingData}
  isSaving={isSaving}
  faqs={parsingFaqs}
  onFaqsChange={setParsingFaqs}
/>
```

#### 5. ParsingReviewPanel 使用提升的狀態

```typescript
// Props interface
export interface ParsingReviewPanelProps {
  faqs?: FAQItem[];
  onFaqsChange?: (faqs: FAQItem[]) => void;
}

// Use lifted state with fallback to local state
const faqSuggestions = liftedFaqs ?? localFaqSuggestions;
const setFaqSuggestions = useCallback((newFaqs: FAQItem[]) => {
  setLocalFaqSuggestions(newFaqs);
  if (onLiftedFaqsChange) {
    onLiftedFaqsChange(newFaqs);
  }
}, [onLiftedFaqsChange]);
```

### 後端 API 支持

**新增 PATCH 端點**: `PATCH /v1/articles/{id}`

**修改文件**: `backend/src/api/routes/articles.py`

```python
@router.patch("/{article_id}", response_model=ArticleResponse)
async def patch_article(
    article_id: int,
    update: ArticleMetadataUpdate,
    session: AsyncSession = Depends(get_session),
) -> Article:
    """Partially update an article's fields.

    Supports updating:
    - title: Article title
    - author: Author name
    - metadata: Merged with existing article_metadata
    - meta_description: SEO meta description
    - seo_keywords: SEO keywords list
    """
```

**Schema 定義**: `backend/src/api/schemas/article.py`

```python
class ArticleMetadataUpdate(BaseSchema):
    title: str | None = None
    author: str | None = None
    metadata: dict[str, Any] | None = None
    meta_description: str | None = None
    seo_keywords: list[str] | None = None
```

### 數據流圖

**修復前**:
```
User edits FAQ → Local State → Step Navigation → LOST!
```

**修復後**:
```
User edits FAQ → Lifted State (Modal) → Auto-Save (PATCH API) → Backend
       ↓                                                            ↓
  Step Navigation                                               Persisted
       ↓                                                            ↓
  Component Remount ← Restore from Backend ← Query Data
```

### 驗收標準

1. ✅ 用戶在解析頁面編輯的 FAQ，切換步驟後不會丟失
2. ✅ 點擊「下一步」時自動保存 FAQ 數據到後端
3. ✅ 重新打開 Modal 時，能恢復之前保存的 FAQ
4. ✅ 後端新增 PATCH /v1/articles/{id} 端點
5. ✅ 所有現有功能保持正常工作

### 修改的文件

- `frontend/src/components/ArticleReview/ArticleReviewModal.tsx` - 狀態提升 + 自動保存
- `frontend/src/components/ArticleReview/ParsingReviewPanel.tsx` - Props 接收狀態
- `backend/src/api/routes/articles.py` - 新增 PATCH 端點
- `backend/src/api/schemas/article.py` - 新增 ArticleMetadataUpdate schema
- `frontend/docs/STATE_PERSISTENCE_FIX.md` - 本文檔更新
