"""
AI 編譯器演示
展示如何使用 AI 將自然語言轉換為可執行的規則代碼
"""

import json
from typing import Any


def demonstrate_ai_compilation():
    """演示 AI 編譯過程"""

    print("=" * 80)
    print("🤖 AI 規則編譯器演示")
    print("=" * 80)

    # 測試案例
    test_cases = [
        {
            "description": "當看到「錯別字」時，建議改為「錯誤字」",
            "examples": [
                {"before": "文章中有錯別字需要修正", "after": "文章中有錯誤字需要修正"}
            ]
        },
        {
            "description": "中英文之間應該加入一個空格，例如「使用API」應該改為「使用 API」",
            "examples": [
                {"before": "使用API介面", "after": "使用 API 介面"},
                {"before": "Python語言", "after": "Python 語言"}
            ]
        },
        {
            "description": "段落開頭的「因此」在非正式文檔中建議改為「所以」",
            "context": {"document_context": "informal"},
            "examples": [
                {"before": "因此，我們決定採用新方案", "after": "所以，我們決定採用新方案"}
            ]
        },
        {
            "description": "將重複的標點符號簡化，如「。。。」改為「。」，「！！」改為「！」",
            "examples": [
                {"before": "真的嗎。。。", "after": "真的嗎。"},
                {"before": "太棒了！！", "after": "太棒了！"}
            ]
        },
        {
            "description": "英文單詞前後如果是中文，需要加空格，但是標點符號除外",
            "examples": [
                {"before": "這是iPhone手機", "after": "這是 iPhone 手機"},
                {"before": "使用GitHub。", "after": "使用 GitHub。"}  # 標點前不加空格
            ]
        }
    ]

    print("\n📝 測試自然語言描述轉換：\n")

    for i, test in enumerate(test_cases, 1):
        print(f"\n案例 {i}: {test['description']}")
        print("-" * 60)

        # 模擬 AI 編譯過程
        compiled_rule = simulate_ai_compilation(
            test['description'],
            test.get('examples'),
            test.get('context')
        )

        print("✅ AI 編譯結果：")
        print(json.dumps(compiled_rule, ensure_ascii=False, indent=2))

        # 驗證結果
        if test.get('examples'):
            print("\n🧪 驗證示例：")
            for ex in test['examples']:
                result = apply_rule(compiled_rule, ex['before'])
                status = "✓" if result == ex['after'] else "✗"
                print(f"  {status} '{ex['before']}' → '{result}'")


def simulate_ai_compilation(
    description: str,
    examples: list = None,
    context: dict = None
) -> dict[str, Any]:
    """
    模擬 AI 編譯過程
    實際使用時會調用 OpenAI/Claude API
    """

    # 這裡模擬 AI 的思考過程
    print("\n🤔 AI 分析中...")

    # 案例 1: 簡單替換
    if "錯別字" in description and "錯誤字" in description:
        print("  → 識別為：簡單文字替換規則")
        print("  → 規則類型：錯字修正 (typo_correction)")
        print("  → 置信度：0.95（明確的錯字修正）")
        return {
            "pattern": r"錯別字",
            "replacement": "錯誤字",
            "rule_type": "typo_correction",
            "conditions": {},
            "confidence": 0.95,
            "priority": 115,  # 95 + 20
            "explanation": "將常見錯字「錯別字」修正為「錯誤字」"
        }

    # 案例 2: 中英文空格
    elif "中英文" in description and "空格" in description:
        print("  → 識別為：中英文混排規則")
        print("  → 規則類型：標點符號 (punctuation)")
        print("  → 使用捕獲組處理複雜替換")
        print("  → 置信度：0.88（常見格式規範）")
        return {
            "pattern": r"([\\u4e00-\\u9fff])([a-zA-Z]+)",
            "replacement": r"\\1 \\2",
            "rule_type": "punctuation",
            "conditions": {},
            "confidence": 0.88,
            "priority": 103,  # 88 + 15
            "explanation": "在中文和英文之間自動加入空格"
        }

    # 案例 3: 條件性替換
    elif "段落開頭" in description and "因此" in description:
        print("  → 識別為：條件性風格規則")
        print("  → 規則類型：風格建議 (style)")
        print("  → 添加條件：僅非正式文檔")
        print("  → 使用 ^ 錨定段落開頭")
        print("  → 置信度：0.75（風格建議）")
        return {
            "pattern": r"^因此",
            "replacement": "所以",
            "rule_type": "style",
            "conditions": {
                "only_informal": True,
                "paragraph_start": True
            },
            "confidence": 0.75,
            "priority": 85,  # 75 + 10
            "explanation": "非正式文檔中，段落開頭的「因此」改為「所以」"
        }

    # 案例 4: 重複標點
    elif "重複" in description and "標點" in description:
        print("  → 識別為：標點符號清理規則")
        print("  → 規則類型：標點符號 (punctuation)")
        print("  → 使用量詞 + 匹配重複")
        print("  → 置信度：0.92（明確的格式錯誤）")
        return {
            "pattern": r"([。！？，、])+",
            "replacement": r"\\1",
            "rule_type": "punctuation",
            "conditions": {},
            "confidence": 0.92,
            "priority": 107,  # 92 + 15
            "explanation": "將重複的標點符號簡化為單個"
        }

    # 案例 5: 複雜的中英文規則
    elif "英文單詞" in description and "標點符號除外" in description:
        print("  → 識別為：複雜的混排規則")
        print("  → 需要考慮標點符號的特殊情況")
        print("  → 使用負向前瞻 (?![。，！？])")
        print("  → 置信度：0.85（有例外情況）")
        return {
            "pattern": r"([\\u4e00-\\u9fff])([a-zA-Z]+)(?![。，！？])",
            "replacement": r"\\1 \\2",
            "rule_type": "punctuation",
            "conditions": {
                "ignore_before_punctuation": True
            },
            "confidence": 0.85,
            "priority": 100,  # 85 + 15
            "explanation": "英文單詞前後加空格，但標點符號前除外"
        }

    # 預設情況
    return {
        "pattern": "",
        "replacement": "",
        "rule_type": "unknown",
        "conditions": {},
        "confidence": 0.5,
        "priority": 50,
        "explanation": "無法解析規則"
    }


def apply_rule(rule: dict[str, Any], text: str) -> str:
    """應用編譯後的規則到文本"""
    import re

    if not rule.get('pattern'):
        return text

    try:
        pattern = rule['pattern']
        replacement = rule.get('replacement', '')

        # 處理特殊的正則表達式語法
        # 將 \\u 轉換為實際的 Unicode 範圍
        pattern = pattern.replace('\\\\u', '\\u')

        result = re.sub(pattern, replacement, text)
        return result
    except Exception as e:
        print(f"    ⚠️ 規則應用失敗: {e}")
        return text


def show_ai_vs_basic_comparison():
    """展示 AI 編譯 vs 基礎規則匹配的對比"""

    print("\n\n" + "=" * 80)
    print("📊 AI 編譯 vs 基礎規則匹配 對比")
    print("=" * 80)

    test_case = "請將所有的「台灣」統一改為「臺灣」，這是正式文件的要求"

    print(f"\n測試案例：\n{test_case}\n")

    # 基礎規則匹配（目前的實現）
    print("🔧 基礎規則匹配結果：")
    print("  方法：簡單的正則表達式提取引號內容")
    print("  結果：")
    print("  {")
    print('    "pattern": "台灣",')
    print('    "replacement": "臺灣"')
    print("  }")
    print("  ❌ 缺失：無法理解「正式文件」的語境")
    print("  ❌ 缺失：無置信度評估")
    print("  ❌ 缺失：無規則類型判斷")

    # AI 編譯結果
    print("\n🤖 AI 編譯結果：")
    print("  方法：使用 LLM 理解完整語境")
    print("  結果：")
    print("  {")
    print('    "pattern": "台灣",')
    print('    "replacement": "臺灣",')
    print('    "rule_type": "style",')
    print('    "conditions": {')
    print('      "document_type": "formal",')
    print('      "description": "正式文件用字規範"')
    print("    },")
    print('    "confidence": 0.95,')
    print('    "priority": 105,')
    print('    "explanation": "根據正式文件規範，將「台灣」統一為「臺灣」"')
    print("  }")
    print("  ✅ 理解語境：識別為正式文件要求")
    print("  ✅ 智能分類：判斷為風格規則")
    print("  ✅ 條件設置：自動添加文檔類型條件")
    print("  ✅ 置信評估：高置信度（0.95）")


def demonstrate_complex_ai_compilation():
    """展示 AI 處理複雜規則的能力"""

    print("\n\n" + "=" * 80)
    print("🎯 AI 處理複雜規則演示")
    print("=" * 80)

    complex_rules = [
        {
            "description": """
            在技術文檔中，當提到版本號時（如 v1.2.3 或 version 2.0），
            如果版本號前沒有空格，需要加入空格。但如果是在括號內則不需要。
            例如：「系統v1.2.3」改為「系統 v1.2.3」，但「(v1.2.3)」保持不變。
            """,
            "ai_result": {
                "pattern": r"(?<![(\\s])(?:v|version)\\d+(?:\\.\\d+)*",
                "replacement": r" \\g<0>",
                "rule_type": "punctuation",
                "conditions": {
                    "document_type": "technical",
                    "context_aware": True
                },
                "confidence": 0.82,
                "priority": 97,
                "explanation": "技術文檔中版本號前加空格，括號內除外"
            }
        },
        {
            "description": """
            將口語化的時間表達改為正式表達：
            - 「昨天」改為具體日期
            - 「下個月」改為具體月份
            - 「今年」改為具體年份
            但在引用對話時保持原樣。
            """,
            "ai_result": {
                "pattern": "複雜的上下文相關模式",
                "rule_type": "style",
                "conditions": {
                    "requires_context": True,
                    "date_resolution": True,
                    "ignore_quotes": True
                },
                "confidence": 0.70,
                "priority": 80,
                "explanation": "需要動態日期解析和上下文判斷的複雜規則"
            }
        }
    ]

    for i, rule in enumerate(complex_rules, 1):
        print(f"\n複雜規則 {i}:")
        print("描述：", rule['description'].strip())
        print("\n🤖 AI 編譯結果：")
        print(json.dumps(rule['ai_result'], ensure_ascii=False, indent=2))
        print("\n💡 AI 的理解：")
        print("  - 識別了多個條件限制")
        print("  - 理解了例外情況")
        print("  - 生成了複雜的正則表達式")
        print("  - 設置了合適的置信度")


if __name__ == "__main__":
    # 執行所有演示
    demonstrate_ai_compilation()
    show_ai_vs_basic_comparison()
    demonstrate_complex_ai_compilation()

    print("\n\n" + "=" * 80)
    print("🎓 總結")
    print("=" * 80)
    print("""
AI 編譯器的優勢：

1. **語義理解**：理解自然語言的完整含義，不只是簡單的模式匹配
2. **智能分類**：自動判斷規則類型（錯字/語法/風格等）
3. **條件推斷**：從描述中推斷應用條件（文檔類型、位置等）
4. **置信評估**：基於規則的確定性給出置信度分數
5. **複雜模式**：生成複雜的正則表達式和處理邏輯
6. **上下文感知**：理解例外情況和特殊條件

實施建議：

1. 使用 GPT-4 或 Claude 3 進行高質量編譯
2. 提供充分的示例以提高準確性
3. 人工審查 AI 生成的規則
4. 建立規則測試套件驗證正確性
5. 持續優化提示詞以提高編譯質量
    """)

    print("=" * 80)
