# 校對服務架構指南

> **最後更新**: 2025-12-07
> **版本**: 1.0
> **維護者**: CMS Automation Team

本文檔說明系統中兩套校對服務的設計目的、使用場景和調用方式，避免混淆和誤用。

---

## 目錄

1. [概述](#概述)
2. [兩套服務對比](#兩套服務對比)
3. [簡化版服務](#簡化版服務-proofreadingservice)
4. [進階版服務](#進階版服務-proofreadinganalysisservice)
5. [使用場景決策表](#使用場景決策表)
6. [UI 觸發說明](#ui-觸發說明)
7. [Prompt 設計詳解](#prompt-設計詳解)
8. [API 參考](#api-參考)

---

## 概述

系統中存在 **兩套校對服務**，各有不同的設計目的：

| 服務 | 定位 | 當前狀態 |
|------|------|----------|
| **簡化版** `ProofreadingService` | 輕量級正文校對 | API 可用，UI 未整合 |
| **進階版** `ProofreadingAnalysisService` | 完整校對 + SEO + 發布合規 | 自動化流程使用中 |

**重要**: 目前系統採用全自動校對流程，用戶無需手動觸發校對。

---

## 兩套服務對比

### 總覽表

| 維度 | 簡化版 | 進階版 |
|------|--------|--------|
| **文件位置** | `proofreading_service.py` | `proofreading/service.py` |
| **API 端點** | `POST /v1/proofread` | `POST /articles/{id}/proofread` |
| **處理內容** | 只有正文 | 全文 + 標題 + 圖片 + 元數據 |
| **規則數量** | 通用規則（5 類） | 460+ 專業規則（A-F 六大類） |
| **輸入限制** | 5000 字符 | 無限制 |
| **Fallback** | ✅ 規則引擎備援 | ❌ 無 |
| **輸出** | `issues` | `issues` + `suggested_content` + `seo_metadata` |
| **成本** | 較低（2048 tokens） | 較高（8192 tokens） |
| **UI 觸發** | ❌ 無 | ❌ 無（自動流程） |

### 架構關係圖

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend UI                              │
│                   (只顯示結果，不觸發校對)                         │
└─────────────────────────────────────────────────────────────────┘
                    │                           │
                    ▼                           ▼
         ┌──────────────────┐       ┌──────────────────────┐
         │ /v1/proofread    │       │ /articles/{id}/      │
         │ (手動 API 調用)   │       │ review-data (讀取)   │
         └────────┬─────────┘       └──────────────────────┘
                  │
                  ▼
    ┌─────────────────────────┐    ┌────────────────────────────┐
    │   ProofreadingService   │    │ ProofreadingAnalysisService│
    │   (簡化版)               │    │ (進階版)                    │
    │   - 只校對正文           │    │ - 全文 + 圖片 + 元數據      │
    │   - 通用規則             │    │ - 460+ 專業規則            │
    │   - 有 fallback         │    │ - AI + 確定性引擎合併       │
    └─────────────────────────┘    └────────────────────────────┘
                                               ▲
                                               │ (自動觸發)
                              ┌────────────────┴────────────────┐
                              │   WorklistPipelineService       │
                              │   (Google Drive 同步後自動執行)  │
                              └─────────────────────────────────┘
```

---

## 簡化版服務 (ProofreadingService)

### 文件位置

```
backend/src/services/proofreading_service.py
```

### 設計目的

- 獨立的正文校對，不依賴文章上下文
- 輕量級、快速響應
- 支持手動輸入文本
- 有 fallback 機制確保 100% 輸出

### System Prompt

```
你是專業的中文文本校對專家。
你的任務是檢查文章正文中的錯誤，包括：
1. 錯字和拼寫錯誤
2. 語法錯誤
3. 標點符號錯誤
4. 冗餘表達
5. 不當用詞

重要：
- 只檢查正文內容，不需要處理標題或其他元數據
- 輸出必須是有效的 JSON 格式
- 每個問題都要提供具體的修改建議
- 按嚴重程度排序（critical > high > medium > low）
```

### User Prompt 模板

```
請校對以下中文文章正文，找出其中的錯誤。

正文內容：
{text}

要求：
1. 找出最多 {max_issues} 個問題
2. 優先報告嚴重錯誤（錯字、語法錯誤）
3. 提供具體的修改建議
4. 輸出 JSON 格式

輸出格式：
{
    "issues": [
        {
            "rule_id": "TYPO_001",
            "severity": "high",
            "location": {"paragraph": 1, "sentence": 2},
            "original_text": "錯誤文本",
            "suggested_text": "正確文本",
            "explanation": "錯誤說明",
            "confidence": 0.95
        }
    ]
}

只輸出 JSON，不要其他內容。
```

### 技術參數

| 參數 | 值 |
|------|-----|
| 模型 | `claude-opus-4-5-20251101` |
| max_tokens | 2048 |
| temperature | 0.2 |
| 最大輸入 | 5000 字符 |

### 當前使用情況

⚠️ **此服務目前在 UI 中沒有觸發元素**

只能通過以下方式調用：
- 直接 API 調用（curl、Postman）
- E2E 測試腳本
- 未來可能的 UI 功能

---

## 進階版服務 (ProofreadingAnalysisService)

### 文件位置

```
backend/src/services/proofreading/service.py
backend/src/services/proofreading/ai_prompt_builder.py
backend/src/services/proofreading/rules/catalog.json
```

### 設計目的

- 完整的發布前審核
- 支持 460+ 條專業規則
- AI 校對 + 確定性規則引擎合併
- 發布阻斷機制（`blocks_publish`）
- SEO 建議輸出

### System Prompt（核心部分）

```
你是一名资深的新闻校对与发布合规专家，需要一次性完成以下任务：

1. 按照 A-F 类共 ~460 条规则进行逐条校对，规则清单见下表。
2. 针对无法程序化验证的语境类规则，给出高置信度结论，并说明依据。
3. 输出结构化 JSON，使系统可以将你的结果与脚本校验结果合并。
4. 所有严重等级达到 error/critical 或 blocks_publish=true 的问题必须给出阻断发布理由。
5. **重要注意事项**：
   - 尊重文章的 target_locale（目标语系），仅修正明确的用字错误
   - **不要强制繁简体转换**，除非规则明确要求
   - 若不确定是否需要繁简转换，将 confidence 设置为 0.5 以下

规则清单快照（版本 {version}，哈希 {fingerprint}）：
{manifest_table}

输出要求：
- **只返回纯 JSON 对象，不要任何额外文字或 markdown 代码块**
```

### 規則分類 (catalog.json)

| 類別 | 說明 | 規則數 | 示例 |
|------|------|--------|------|
| **A** | 用字與用詞規範 | ~150 | 錯別字、統一用字、敏感語彙 |
| **B** | 標點符號與排版 | ~60 | 引號、書名號、全角半角 |
| **C** | 數字與計量單位 | ~24 | 阿拉伯數字、貨幣格式 |
| **D** | 人名地名譯名 | ~40 | 譯名標準、機構縮寫 |
| **E** | 特殊規範 | ~40 | 圖片來源、宗教術語、年代表示 |
| **F** | 發布合規 | ~40 | 圖片規格、標題層級、授權 |

### 技術參數

| 參數 | 值 |
|------|-----|
| 模型 | `settings.ANTHROPIC_MODEL` |
| max_tokens | 8192 |
| temperature | 0.2 |
| stop_sequences | `["```"]` |

### 當前使用情況

✅ **此服務由自動化流程調用**

調用路徑：
```
Google Drive 同步
  → WorklistPipelineService.process_new_item()
    → _run_proofreading()
      → ProofreadingAnalysisService.analyze_article()
```

---

## 使用場景決策表

| 你需要... | 用哪個？ | 原因 |
|-----------|----------|------|
| 快速檢查一段文字的錯字 | **簡化版** | 輕量、有 fallback |
| 手動輸入文本校對 | **簡化版** | 支持 `body_text` 參數 |
| 完整的發布前審核 | **進階版** | 460+ 規則、阻斷機制 |
| 自動化流水線處理 | **進階版** | Pipeline 自動觸發 |
| 檢查圖片規格/標題層級 | **進階版** | F 類規則處理發布合規 |
| 需要 SEO 建議 | **進階版** | 輸出 `seo_metadata` |
| 開發/測試用途 | **簡化版** | API 直接可用 |

---

## UI 觸發說明

### 當前狀態

| API 端點 | UI 觸發 | 說明 |
|----------|---------|------|
| `POST /v1/proofread` | ❌ 無 | 無 UI 元素調用 |
| `POST /articles/{id}/proofread` | ❌ 無 | 由 Pipeline 自動觸發 |
| `GET /articles/{id}/review-data` | ✅ 有 | 讀取已存儲的校對結果 |

### 自動化流程說明

```
┌─────────────────────────────────────────────────────────────┐
│                    自動化流程（無需手動觸發）                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Google Drive 文件同步到 Worklist                        │
│  2. WorklistPipelineService 自動處理新項目                  │
│  3. 執行解析 (_run_parsing)                                 │
│  4. 執行校對 (_run_proofreading) ← 進階版服務               │
│  5. 結果存入 Article.proofreading_issues                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    UI 顯示流程（只讀）                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. 用戶在 Worklist 頁面點擊項目                            │
│  2. 點擊 "Review Proofreading" 按鈕                         │
│  3. 導航到 /worklist/{id}/review                           │
│  4. 調用 articlesAPI.getReviewData() 獲取已存儲結果         │
│  5. 顯示校對問題列表（不重新執行校對）                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 如果需要添加手動觸發功能

建議位置：

| 位置 | 功能建議 |
|------|----------|
| WorklistDetailDrawer | 添加「重新校對」按鈕 |
| ArticleReviewModal | 添加「觸發校對」操作 |
| 新的獨立頁面 | 手動輸入文本進行校對測試 |

---

## Prompt 設計詳解

### 簡化版 vs 進階版 Prompt 複雜度

| 維度 | 簡化版 | 進階版 |
|------|--------|--------|
| System Prompt 長度 | ~200 字 | ~1500 字 + 規則表格 |
| User Prompt 長度 | ~150 字 | ~500 字 + 結構化分段 |
| JSON Schema 欄位數 | 7 個 | 12+ 個 |
| 輸出內容 | `issues` only | `issues` + `suggested_content` + `seo_metadata` + `processing_notes` |
| 規則追蹤 | 無 | `rule_coverage` 列出檢查過的規則 ID |

### 進階版 JSON 輸出 Schema

```json
{
  "issues": [
    {
      "rule_id": "A1-001",
      "category": "A",
      "subcategory": "A1",
      "message": "描述問題",
      "suggestion": "修正建議",
      "severity": "info|warning|error|critical",
      "confidence": 0.0-1.0,
      "can_auto_fix": true|false,
      "blocks_publish": true|false,
      "location": {"section": "body", "offset": 123},
      "evidence": "引用原文片段"
    }
  ],
  "suggested_content": "建議後的正文",
  "seo_metadata": {
    "meta_title": "...",
    "meta_description": "...",
    "keywords": ["..."]
  },
  "processing_notes": {
    "ai_rationale": "分析重點簡述",
    "rule_coverage": ["A1-001", "B2-002", "..."]
  }
}
```

---

## API 參考

### 簡化版 API

#### POST /v1/proofread

校對文章正文內容。

**Request Body:**
```json
{
  "worklist_id": 123,        // 可選：從 worklist 獲取正文
  "article_id": 456,         // 可選：從 article 獲取正文
  "body_text": "文本內容",    // 可選：直接提供正文
  "max_issues": 20,          // 最多返回問題數
  "severity_filter": ["critical", "high"]  // 嚴重程度過濾
}
```

**Response:**
```json
{
  "success": true,
  "proofreading_issues": [...],
  "proofreading_stats": {
    "total_issues": 5,
    "critical": 1,
    "high": 2,
    "medium": 1,
    "low": 1
  },
  "processed_text_length": 3500,
  "source": "worklist|article|manual"
}
```

#### POST /v1/worklist/{worklist_id}/proofread

快捷端點：校對特定 worklist 項目的正文。

### 進階版 API

#### POST /articles/{article_id}/proofread

執行完整校對分析。

**Response:**
```json
{
  "issues": [...],
  "blocking_issues": [...],
  "statistics": {
    "total_issue_count": 15,
    "blocking_issue_count": 2,
    "ai_issue_count": 10,
    "script_issue_count": 5
  },
  "suggested_content": "...",
  "seo_metadata": {...},
  "processing_metadata": {
    "ai_model": "claude-sonnet-4-20250514",
    "ai_latency_ms": 2500,
    "rule_manifest_version": "2025.02.05"
  }
}
```

---

## 常見問題

### Q: 為什麼有兩套服務？

A: 設計考量不同：
- 簡化版：輕量、快速、適合獨立校對需求
- 進階版：完整、嚴謹、適合發布前審核

### Q: UI 上點哪裡可以觸發校對？

A: 目前 UI 沒有手動觸發校對的按鈕。校對在文章導入時自動執行。

### Q: 如何手動測試校對功能？

A: 使用 curl 或 Postman 調用簡化版 API：
```bash
curl -X POST http://localhost:8000/v1/proofread \
  -H "Content-Type: application/json" \
  -d '{"body_text": "測試文本內容"}'
```

### Q: 校對結果存在哪裡？

A: 存在 `Article.proofreading_issues` 欄位（JSON 格式）。

---

## 相關文檔

- [T7.2 校對服務架構](./T7.2_PROOFREADING_SERVICE_ARCHITECTURE.md)
- [校對需求規格 v2](./proofreading_requirements.v2.md)
- [單一 Prompt 設計](./single_prompt_design.md)
- [文章校對 SEO 工作流](./article_proofreading_seo_workflow.md)
