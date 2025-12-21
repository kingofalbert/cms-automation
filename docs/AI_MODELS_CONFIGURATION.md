# AI Models Configuration Guide

本文檔說明 CMS Automation 系統中使用的所有 AI 模型及其用途。

## 模型總覽

| 功能 | 默認模型 | 備用模型 | 配置項 |
|------|----------|----------|--------|
| 文章解析/校對/SEO | Claude Opus 4.5 | - | `ANTHROPIC_MODEL` |
| 圖片 OCR/Alt Text | Gemini 3.0 Flash | GPT-4o | `VERTEX_AI_MODEL` / `OPENAI_MODEL` |
| 圖片生成 | Imagen 3.0 | - | `VERTEX_AI_IMAGE_MODEL` |

---

## 1. 文章處理模型

### Claude Opus 4.5 (Anthropic)

**用途：**
- 文章內容解析 (Article Parsing)
- 中文校對 (Proofreading)
- SEO 標題/描述生成
- FAQ Schema 生成
- 內部連結建議

**配置：**
```bash
ANTHROPIC_API_KEY=sk-ant-xxx
ANTHROPIC_MODEL=claude-opus-4-5-20251101
ANTHROPIC_MAX_TOKENS=16384
```

**為什麼選擇 Claude Opus 4.5：**
- 繁體中文理解能力最強
- 長文本處理能力優秀（支持 200K context）
- 校對規則遵循準確度高
- 輸出格式穩定（JSON Schema 遵循好）

**成本估算：**
- Input: $15/1M tokens
- Output: $75/1M tokens
- 每篇文章約 $0.05-0.15

---

## 2. 圖片 OCR / Alt Text 生成模型

### 主要模型：Gemini 3.0 Flash (Google Vertex AI)

**用途：**
- 圖片類型檢測（信息圖 vs 照片）
- 圖片文字提取 (OCR)
- Alt Text 生成
- 圖片描述生成

**配置：**
```bash
VERTEX_AI_PROJECT=cmsupload-476323
VERTEX_AI_LOCATION=us-central1
VERTEX_AI_MODEL=gemini-3.0-flash
USE_VERTEX_AI_FOR_VISION=true
```

**為什麼選擇 Gemini 3.0 Flash：**
- OCR 準確率比 2.5 版本提升 15%
- 成本比 GPT-4o 便宜約 5 倍
- 速度快 3 倍
- 手寫識別能力突破性提升
- 支持繁體中文

**成本估算：**
- Input: $0.50/1M tokens
- Output: $3.00/1M tokens
- 每張圖片約 $0.001-0.005

### 備用模型：GPT-4o (OpenAI)

**用途：**
- 當 Gemini 不可用時自動切換
- 與 Gemini 功能相同

**配置：**
```bash
OPENAI_API_KEY=sk-xxx
OPENAI_MODEL=gpt-4o
USE_VERTEX_AI_FOR_VISION=false  # 設為 false 強制使用 OpenAI
```

**成本估算：**
- Input: $2.50/1M tokens
- Output: $10.00/1M tokens
- 每張圖片約 $0.01-0.03

---

## 3. 圖片生成模型

### Imagen 3.0 (Google Vertex AI)

**用途：**
- 文章配圖生成（未來功能）
- 縮略圖生成（未來功能）

**配置：**
```bash
VERTEX_AI_IMAGE_MODEL=imagen-3.0-generate-001
```

**狀態：** 預留配置，尚未實現

---

## 4. 模型選擇邏輯

### 圖片 Alt Text 生成流程

```
開始
  │
  ├─ 檢查 USE_VERTEX_AI_FOR_VISION
  │     │
  │     ├─ true + Vertex AI 可用
  │     │     └─ 使用 Gemini 3.0 Flash
  │     │
  │     └─ false 或 Vertex AI 不可用
  │           └─ 使用 GPT-4o
  │
  ├─ 圖片是否可訪問？
  │     │
  │     ├─ 是 → 執行視覺分析 + OCR
  │     │
  │     └─ 否 → 回退到文本上下文推斷
  │
  └─ 返回結果
```

### 圖片類型檢測

| 類型 | 英文標識 | 說明 | Alt Text 策略 |
|------|----------|------|--------------|
| 信息圖 | `infographic` | 圖片上有嵌入文字 | 必須包含 OCR 提取的文字 |
| 照片 | `photo` | 純圖片，無嵌入文字 | 描述視覺內容 |
| 未知 | `unknown` | 無法確定或圖片不可訪問 | 基於上下文推斷 |

---

## 5. 環境變量完整列表

```bash
# === Anthropic (Claude) ===
ANTHROPIC_API_KEY=sk-ant-xxx           # 必需
ANTHROPIC_MODEL=claude-opus-4-5-20251101
ANTHROPIC_MAX_TOKENS=16384

# === OpenAI (GPT-4o) ===
OPENAI_API_KEY=sk-xxx                  # 可選（作為 Gemini 備用）
OPENAI_MODEL=gpt-4o

# === Google Vertex AI (Gemini) ===
VERTEX_AI_PROJECT=cmsupload-476323     # GCP 項目 ID
VERTEX_AI_LOCATION=us-central1         # 區域
VERTEX_AI_MODEL=gemini-3.0-flash       # 視覺/OCR 模型
VERTEX_AI_IMAGE_MODEL=imagen-3.0-generate-001  # 圖片生成模型
USE_VERTEX_AI_FOR_VISION=true          # 是否使用 Gemini 做視覺任務
```

---

## 6. 成本對比

### 每月預估成本（假設 1000 篇文章，每篇 5 張圖片）

| 模型 | 用途 | 單價 | 月用量 | 月成本 |
|------|------|------|--------|--------|
| Claude Opus 4.5 | 文章解析 | ~$0.10/篇 | 1000 篇 | ~$100 |
| Gemini 3.0 Flash | 圖片 OCR | ~$0.003/張 | 5000 張 | ~$15 |
| **總計** | | | | **~$115/月** |

### 如果全部使用 OpenAI

| 模型 | 用途 | 單價 | 月用量 | 月成本 |
|------|------|------|--------|--------|
| GPT-4 | 文章解析 | ~$0.15/篇 | 1000 篇 | ~$150 |
| GPT-4o | 圖片 OCR | ~$0.02/張 | 5000 張 | ~$100 |
| **總計** | | | | **~$250/月** |

**使用 Gemini 節省約 54% 成本**

---

## 7. 切換模型

### 強制使用 GPT-4o 做圖片 OCR

```bash
# .env
USE_VERTEX_AI_FOR_VISION=false
```

### 強制使用 Gemini 做圖片 OCR（默認）

```bash
# .env
USE_VERTEX_AI_FOR_VISION=true
```

---

## 8. 故障排除

### Gemini 初始化失敗

**症狀：** 日誌顯示 `Failed to initialize Vertex AI`

**解決方案：**
1. 確認 GCP 項目已啟用 Vertex AI API
2. 確認服務帳號有 `Vertex AI User` 角色
3. 檢查 `VERTEX_AI_PROJECT` 是否正確

### OCR 結果不準確

**症狀：** 信息圖的文字提取不完整

**解決方案：**
1. 確認使用 Gemini 3.0 Flash（非 2.5 Thinking）
2. 檢查圖片解析度是否足夠
3. 考慮增加圖片預處理

---

## 更新記錄

| 日期 | 變更 |
|------|------|
| 2025-12-20 | 初始版本：添加 Gemini 3.0 Flash 支持，設為默認 OCR 模型 |
| 2025-12-20 | 更新圖片類型命名：tocard → infographic, illustration → photo |
