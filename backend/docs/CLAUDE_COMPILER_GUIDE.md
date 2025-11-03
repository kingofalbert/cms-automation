# Claude Sonnet 4.5 規則編譯器使用指南

## 概述

使用 **Anthropic Claude Sonnet 4.5** 作為 AI 編譯器，將自然語言描述智能轉換為可執行的校對規則。這是目前世界上最強大的編程模型（2025年9月29日發布）。

## 快速開始

### 1. 設置 API 密鑰

```bash
# 設置環境變數
export ANTHROPIC_API_KEY="your-api-key-here"

# 或在 .env 檔案中
ANTHROPIC_API_KEY=your-api-key-here
```

### 2. 安裝依賴

```bash
pip install anthropic
```

## API 端點

### 編譯單個規則

```bash
POST /api/v1/proofreading/claude/compile-rule

# 請求範例
curl -X POST "http://localhost:8001/api/v1/proofreading/claude/compile-rule" \
  -H "Content-Type: application/json" \
  -d '{
    "natural_language": "當看到「錯別字」時，建議改為「錯誤字」",
    "examples": [
      {"before": "文章中有錯別字", "after": "文章中有錯誤字"}
    ]
  }'

# 響應範例
{
  "success": true,
  "data": {
    "pattern": "錯別字",
    "replacement": "錯誤字",
    "rule_type": "typo_correction",
    "conditions": {},
    "confidence": 0.95,
    "priority": 115,
    "explanation": "將常見錯字「錯別字」修正為「錯誤字」",
    "test_cases": [
      {"input": "發現錯別字", "expected": "發現錯誤字"}
    ]
  },
  "compiler": "claude-3.5-sonnet"
}
```

### 批量編譯規則

```bash
POST /api/v1/proofreading/claude/compile-batch

# 請求範例
curl -X POST "http://localhost:8001/api/v1/proofreading/claude/compile-batch" \
  -H "Content-Type: application/json" \
  -d '{
    "rules": [
      {
        "natural_language": "中英文之間應該加入空格",
        "examples": [
          {"before": "使用API", "after": "使用 API"}
        ]
      },
      {
        "natural_language": "重複的標點符號簡化為單個",
        "examples": [
          {"before": "真的嗎。。。", "after": "真的嗎。"}
        ]
      }
    ]
  }'
```

## Python 使用範例

### 基本使用

```python
from src.services.claude_rule_compiler import create_claude_compiler

# 創建編譯器
compiler = create_claude_compiler()

# 編譯單個規則
rule = compiler.compile_natural_language_to_rule(
    natural_language="當看到「台灣」時，在正式文件中應改為「臺灣」",
    examples=[
        {"before": "台灣是個美麗的地方", "after": "臺灣是個美麗的地方"}
    ],
    context={"document_type": "formal"}
)

print(f"生成的規則：{rule}")
```

### 異步批量編譯

```python
import asyncio
from src.services.claude_rule_compiler import create_claude_compiler

async def batch_compile_example():
    compiler = create_claude_compiler()

    rules = [
        DraftRule(
            rule_id="R001",
            natural_language="錯別字改正",
            examples=[{"before": "錯別字", "after": "錯誤字"}]
        ),
        DraftRule(
            rule_id="R002",
            natural_language="中英文空格",
            examples=[{"before": "使用Python", "after": "使用 Python"}]
        )
    ]

    # 異步批量編譯
    compiled_rules = await compiler.batch_compile_rules_async(
        rules,
        max_concurrent=5
    )

    for rule in compiled_rules:
        print(f"規則 {rule['rule_type']}: {rule['pattern']} → {rule['replacement']}")

# 執行
asyncio.run(batch_compile_example())
```

## 典型使用場景

### 場景 1: 錯字修正規則

```python
description = "將常見的錯字修正，如「的確」誤寫為「的卻」"
examples = [
    {"before": "這的卻是個問題", "after": "這的確是個問題"},
    {"before": "的卻如此", "after": "的確如此"}
]

result = compiler.compile_natural_language_to_rule(description, examples)

# 結果
{
    "pattern": "的卻",
    "replacement": "的確",
    "rule_type": "typo_correction",
    "confidence": 0.95,
    "priority": 115
}
```

### 場景 2: 標點符號規範

```python
description = "中文和英文之間需要加空格，但標點符號前不加"
examples = [
    {"before": "使用Python編程", "after": "使用 Python 編程"},
    {"before": "學習AI。", "after": "學習 AI。"}  # 句號前不加空格
]

result = compiler.compile_natural_language_to_rule(description, examples)

# 結果
{
    "pattern": "([\\u4e00-\\u9fff])([a-zA-Z0-9]+)(?![。，！？；：])",
    "replacement": "\\1 \\2",
    "rule_type": "punctuation",
    "confidence": 0.88,
    "conditions": {
        "ignore_before_punctuation": true
    }
}
```

### 場景 3: 條件性風格規則

```python
description = "在非正式文檔中，段落開頭的「因此」建議改為「所以」"
context = {"document_type": "informal"}
examples = [
    {"before": "因此，我們決定", "after": "所以，我們決定"}
]

result = compiler.compile_natural_language_to_rule(description, examples, context)

# 結果
{
    "pattern": "^因此",
    "replacement": "所以",
    "rule_type": "style",
    "conditions": {
        "only_informal": true,
        "paragraph_start": true
    },
    "confidence": 0.75
}
```

## Claude Sonnet 4.5 的優勢

### 1. **智能語義理解**
- 理解「但是」、「除外」、「只有」等條件詞
- 識別規則的意圖和適用範圍

### 2. **複雜模式生成**
- 自動生成複雜的正則表達式
- 正確處理捕獲組和反向引用
- 支援前瞻、後顧等高級模式

### 3. **上下文感知**
- 根據文檔類型調整規則
- 理解位置相關條件（段落開頭、句尾等）
- 識別需要忽略的特殊情況

### 4. **置信度評估**
- 基於規則的確定性給出合理的置信度
- 區分必須修正的錯誤和可選的風格建議

## 編譯質量對比

| 方法 | 質量分數 | 優點 | 缺點 |
|------|---------|------|------|
| **基礎正則** | 2/10 | 快速、無需 API | 只能處理簡單模式 |
| **增強回退** | 5/10 | 不依賴外部 API | 無法理解複雜語境 |
| **Claude 4.5** | 10/10 | 世界最強編程模型、極高準確率 | 需要 API 密鑰、有成本 |

## 最佳實踐

### 1. **提供充分的示例**
```python
# 好的做法 - 多個示例幫助 Claude 理解規則
examples = [
    {"before": "使用API", "after": "使用 API"},
    {"before": "Python語言", "after": "Python 語言"},
    {"before": "開發iOS應用", "after": "開發 iOS 應用"}
]

# 不好的做法 - 示例太少
examples = [{"before": "使用API", "after": "使用 API"}]
```

### 2. **明確描述條件和例外**
```python
# 好的描述
description = """
中英文之間應該加入空格，但是：
1. 標點符號前不需要空格
2. 括號內的不處理
3. URL 和 Email 不處理
"""

# 不清楚的描述
description = "中英文之間加空格"
```

### 3. **使用上下文信息**
```python
# 提供上下文幫助 Claude 做出更好的判斷
context = {
    "document_type": "technical",  # 技術文檔
    "target_audience": "developers",  # 目標讀者
    "formality": "formal"  # 正式程度
}
```

### 4. **驗證編譯結果**
```python
# 總是驗證生成的規則
compiled = compiler.compile_natural_language_to_rule(description, examples)

# 驗證正則表達式
import re
try:
    pattern = re.compile(compiled['pattern'])
    # 測試幾個案例
    for example in examples:
        result = pattern.sub(compiled['replacement'], example['before'])
        assert result == example['after'], f"測試失敗: {result} != {example['after']}"
except Exception as e:
    print(f"規則驗證失敗: {e}")
```

### 5. **處理編譯失敗**
```python
# 使用 try-except 處理可能的失敗
try:
    compiled = compiler.compile_natural_language_to_rule(description, examples)
except Exception as e:
    # 回退到備用方案
    print(f"Claude 編譯失敗: {e}")
    compiled = compiler._enhanced_fallback_compile(description, examples)
```

## 成本優化

### 1. **使用緩存**
編譯器內建緩存機制，相同的輸入不會重複調用 API

### 2. **批量處理**
盡量使用批量編譯而不是單個編譯
```python
# 批量編譯更高效
compiled_rules = await compiler.batch_compile_rules_async(rules)
```

### 3. **混合策略**
- 簡單規則使用基礎方法
- 複雜規則使用 Claude
```python
if is_simple_pattern(description):
    # 使用基礎方法
    result = basic_compile(description)
else:
    # 使用 Claude
    result = compiler.compile_natural_language_to_rule(description)
```

## 故障排除

### 問題 1: API 密鑰錯誤
```
錯誤: 請設置 ANTHROPIC_API_KEY 環境變數
解決: export ANTHROPIC_API_KEY="your-key"
```

### 問題 2: 超時錯誤
```python
# 增加超時時間
compiler.client.timeout = 30  # 30 秒
```

### 問題 3: JSON 解析失敗
Claude 偶爾可能返回格式不正確的 JSON，編譯器會自動處理並回退

### 問題 4: 速率限制
```python
# 降低並發數
compiled_rules = await compiler.batch_compile_rules_async(
    rules,
    max_concurrent=2  # 降低並發數
)
```

## 完整工作流程範例

```python
async def complete_workflow():
    """完整的規則編譯和發布流程"""

    # 1. 創建編譯器
    compiler = create_claude_compiler()

    # 2. 準備規則
    rules_descriptions = [
        {
            "description": "錯別字修正",
            "examples": [{"before": "錯別字", "after": "錯誤字"}]
        },
        {
            "description": "中英文空格",
            "examples": [{"before": "使用API", "after": "使用 API"}]
        }
    ]

    # 3. 編譯規則
    compiled_rules = []
    for rule_desc in rules_descriptions:
        compiled = compiler.compile_natural_language_to_rule(
            rule_desc["description"],
            rule_desc["examples"]
        )
        compiled_rules.append(compiled)

    # 4. 驗證規則
    valid_rules = []
    for rule in compiled_rules:
        is_valid, errors = compiler.validate_compiled_rule(rule)
        if is_valid:
            valid_rules.append(rule)
        else:
            print(f"規則驗證失敗: {errors}")

    # 5. 生成可執行代碼
    from src.services.rule_compiler import rule_compiler

    python_module = rule_compiler.generate_python_module(
        rules=valid_rules,
        module_name="claude_rules",
        output_dir=Path("published_rules/python")
    )

    print(f"✅ 成功編譯並發布 {len(valid_rules)} 個規則")
    print(f"📦 Python 模組: {python_module}")

# 執行
asyncio.run(complete_workflow())
```

## 總結

使用 Claude Sonnet 4.5 作為 AI 編譯器可以：

✅ **準確理解**複雜的自然語言描述
✅ **智能生成**正確的正則表達式模式
✅ **自動判斷**規則類型和優先級
✅ **考慮條件**和例外情況
✅ **提供解釋**和測試用例

這是目前最先進的規則編譯方案，特別適合處理複雜的中文校對規則。