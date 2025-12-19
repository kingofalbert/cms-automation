# 變更記錄：FAQ Schema 支持與 WordPress 編輯器檢測

**日期**: 2024-12-17
**版本**: v1.x
**狀態**: 已完成

---

## 概述

本次更新添加了 FAQ Schema JSON-LD 支持，用於 AI 搜索引擎優化（Perplexity、ChatGPT、Google SGE）。同時發現生產環境 WordPress 使用 Classic Editor，因此實現了優雅跳過機制。

---

## 1. 核心功能變更

### 1.1 FAQ Schema JSON-LD 支持

**目的**: 在文章中嵌入 Schema.org FAQPage 結構化數據，提升 AI 搜索引擎可見性。

**實現方式**:
- FAQs 作為隱藏的 JSON-LD 元數據嵌入，不顯示為可見內容
- 使用 WordPress Gutenberg 的 Custom HTML 區塊插入

**修改的文件**:

| 文件 | 變更內容 |
|------|----------|
| `backend/src/workers/tasks/computer_use_tasks.py` | 從 ArticleFAQ 表獲取已批准的 FAQs |
| `backend/src/services/hybrid_publisher.py` | 添加 `faqs` 參數傳遞鏈 |
| `backend/src/services/computer_use_cms.py` | 生成 FAQ Schema JSON-LD 和插入指令 |
| `scripts/test_instructions_standalone.py` | 添加 FAQ Schema 測試和驗證 |

**生成的 JSON-LD 格式**:
```json
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "問題內容",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "答案內容"
      }
    }
  ]
}
```

### 1.2 優雅跳過機制 (Graceful Skip)

**背景**: 生產環境 WordPress (`admin.epochtimes.com`) 使用 **Classic Editor**，不支持 Gutenberg 的 Custom HTML 區塊。

**解決方案**: FAQ Schema 步驟標記為 OPTIONAL，如果找不到 Custom HTML 區塊則優雅跳過。

**Computer Use 指令更新**:
```
11. Insert FAQ Schema JSON-LD for AI search engines (3 FAQs) - skip if not supported

**IF Custom HTML block is NOT found (graceful skip):**
  - This is OK - the WordPress editor may not support Custom HTML blocks
  - Take a screenshot showing the block search results
  - Log this as a warning: 'FAQ Schema skipped: Custom HTML block not available'
  - Continue to the next step - do NOT stop the publishing process
  - The article will still be published successfully without FAQ Schema
```

---

## 2. 生產環境發現

### 2.1 WordPress 編輯器檢測結果

**✅ 已通過 Playwright 視覺測試驗證 (2024-12-17)**

| 項目 | 結果 | 驗證方式 |
|------|------|----------|
| **URL** | https://admin.epochtimes.com | - |
| **編輯器類型** | Classic Editor（傳統編輯器）| `#wp-content-editor-container` 選擇器檢測 |
| **Gutenberg** | ❌ 未啟用 | 無 Block Editor 元素 |
| **Custom HTML 區塊** | ❌ 不可用 | Classic Editor 不支持 |
| **SEO 外掛** | **Lite SEO** | `h2.hndle:has-text('Lite SEO')` 選擇器檢測 |

> 截圖證據: `editor_check.png`, `seo_check.png`

### 2.2 認證流程

生產環境使用雙層認證：

```
┌─────────────────────────────────────────────────────────┐
│  第一層: HTTP Basic Auth (nginx)                        │
│  用戶: djy / 密碼: djy2013                              │
├─────────────────────────────────────────────────────────┤
│  第二層: WordPress 登錄                                  │
│  用戶: ping.xie / 密碼: kfS*qxdQqm@zic6lXvnR(ih!       │
│  注意: 密碼不包含結尾的 )                                │
└─────────────────────────────────────────────────────────┘
```

---

## 3. 密碼問題修復

### 3.1 問題描述

`.env` 中的密碼有多餘的 `)` 字符：
```
# 錯誤
CMS_APPLICATION_PASSWORD="kfS*qxdQqm@zic6lXvnR(ih!)"

# 正確
CMS_APPLICATION_PASSWORD="kfS*qxdQqm@zic6lXvnR(ih!"
```

### 3.2 受影響的文件

需要更新以下文件中的密碼（移除結尾的 `)`）：
- `.env`
- `backend/.env`
- 相關文檔中的示例

---

## 4. 新增腳本

### 4.1 WordPress 編輯器檢測腳本

**文件**: `scripts/check_wordpress_editor.py`

**功能**:
- 自動登錄 WordPress（支持雙層認證）
- 檢測編輯器類型（Gutenberg vs Classic）
- 檢查 Custom HTML 區塊可用性
- 生成截圖報告

**使用方法**:
```bash
source backend/venv/bin/activate
python scripts/check_wordpress_editor.py
```

---

## 5. 圖片 Caption 設置修復

### 5.1 問題

上傳圖片時只設置了 Alt Text，沒有設置 Caption（圖說）。

### 5.2 修復

更新 Computer Use 指令，明確要求設置兩個字段：
```
**IMPORTANT: For EACH image in the Media Library, set these fields:**
  - Alt Text (替代文字): Use the provided alt_text or caption
  - Caption (圖說): Use the provided caption text - this will display below the image
```

---

## 6. 測試結果

### 6.1 指令生成測試

```
📊 Summary: 33/33 checks passed
✅ All checks PASSED!
```

測試涵蓋：
- 文章標題、SEO 元數據
- 分類、標籤
- 圖片位置和 Caption
- 作者信息
- FAQ Schema（包括優雅跳過）

---

## 7. Git 提交記錄

```
983d002 fix(seo): Add graceful skip for FAQ Schema when Custom HTML not supported
9b6433f feat(seo): Add FAQ Schema JSON-LD support for AI search engines
1fd2361 fix(computer-use): Add explicit caption (圖說) setting instructions for images
```

---

## 8. 後續建議

### 如果需要啟用 FAQ Schema：

1. **切換到 Gutenberg 編輯器**
   - 在 WordPress 後台禁用 Classic Editor 外掛
   - 或安裝 Gutenberg 外掛

2. **使用 Schema 外掛**
   - Rank Math（內建 FAQ Schema 支持）
   - Yoast SEO（需要 Premium 版本）
   - Schema Pro

3. **主題代碼注入**
   - 在 `wp_head` 或 `wp_footer` hook 中添加 JSON-LD

---

## 9. 文檔更新記錄

本次更新對以下文檔進行了掃描和修正，確保與生產環境配置一致：

### 9.1 已更新的文檔

| 文件 | 更新內容 |
|------|----------|
| `docs/PROD_ENV_SETUP.md` | 添加 Classic Editor 和 Lite SEO 說明 |
| `backend/docs/hybrid_publishing_implementation_guide.md` | 添加生產環境編輯器配置說明 |
| `backend/docs/playwright_vs_computer_use_guide.md` | 添加生產環境配置說明章節 |
| `backend/docs/computer_use_publishing_guide.md` | 添加 Lite SEO 支持說明 |
| `COMPUTER_USE_GUIDE.md` | 添加生產環境 SEO 插件說明 |

### 9.2 密碼修復的文件

以下文件中的密碼已修正（移除多餘的 `)`）：
- `.env`
- `backend/.env`
- `backend/CONFIGURATION_COMPLETE.md`
- `backend/CONFIGURATION_STATUS_SUMMARY.md`
- `QUICK_SETUP_GUIDE.md`

---

## 10. 相關文件列表

| 文件 | 類型 | 狀態 |
|------|------|------|
| `backend/src/services/computer_use_cms.py` | 核心服務 | ✅ 已更新 |
| `backend/src/services/hybrid_publisher.py` | 發布服務 | ✅ 已更新 |
| `backend/src/workers/tasks/computer_use_tasks.py` | Celery 任務 | ✅ 已更新 |
| `scripts/test_instructions_standalone.py` | 測試腳本 | ✅ 已更新 |
| `scripts/check_wordpress_editor.py` | 診斷腳本 | ✅ 新增 |
| `scripts/generated_instructions.txt` | 生成示例 | ✅ 已更新 |
| `docs/PROD_ENV_SETUP.md` | 生產環境文檔 | ✅ 已更新 |
| `backend/docs/playwright_vs_computer_use_guide.md` | 方案對比文檔 | ✅ 已更新 |
| `backend/docs/computer_use_publishing_guide.md` | 發布指南 | ✅ 已更新 |
| `COMPUTER_USE_GUIDE.md` | 主使用指南 | ✅ 已更新 |

---

## 11. SEO 插件自動適配功能

**新增功能 (2024-12-17)**：Computer Use 腳本現在可以自動檢測並適配不同的 SEO 插件。

### 支持的 SEO 插件

| 插件 | 檢測方式 | 配置步驟 |
|------|----------|----------|
| **Lite SEO** | 頁面底部 metabox | SEO/Keywords 標籤頁 |
| **Yoast SEO** | 側邊欄或 metabox | Focus keyphrase + SEO 標題 |
| **Rank Math** | 側邊欄面板 | Edit Snippet 按鈕 |
| **Slim SEO** | 無面板 | 自動生成，跳過配置 |
| **無插件** | - | 記錄警告，繼續發布 |

### 修改的代碼

**文件**: `backend/src/services/computer_use_cms.py`

```python
add_step(
    "Configure SEO Metadata (Auto-detect SEO Plugin)",
    [
        "**FIRST: Detect which SEO plugin is installed...**",
        "**Option A - Lite SEO** (look for 'Lite SEO' metabox)...",
        "**Option B - Yoast SEO** (look for 'Yoast SEO' metabox)...",
        "**Option C - Rank Math** (look for 'Rank Math' panel)...",
        "**Option D - Slim SEO / Other** (minimal or no SEO panel)...",
        "**Option E - No SEO Plugin Found** - continue anyway...",
    ],
)
```

### 優勢

1. **開發/生產環境一致性**: 無論使用哪種 SEO 插件，同一套指令都能工作
2. **降低配置成本**: 不需要為每個環境單獨配置
3. **優雅降級**: 找不到插件時仍能繼續發布

---

## 12. 結論

所有變更已完成並經過驗證：

1. ✅ **FAQ Schema JSON-LD 支持** - 已實現，帶優雅跳過機制
2. ✅ **生產環境檢測** - 確認使用 Classic Editor + Lite SEO（通過 Playwright 視覺測試驗證）
3. ✅ **密碼問題修復** - 所有文件已更新
4. ✅ **文檔同步** - 所有文檔已更新為正確的配置信息
5. ✅ **SEO 插件自動適配** - Computer Use 現支持多種 SEO 插件自動檢測

**生產環境影響**:
- FAQ Schema JSON-LD 將被自動跳過（因 Classic Editor 不支持 Custom HTML 區塊）
- SEO 配置會自動檢測 Lite SEO 並使用對應的字段
- 系統將正常運行，文章發布不受影響
