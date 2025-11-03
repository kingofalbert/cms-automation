"""
範例：展示規則發布和使用的完整流程
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path

# 假設這些模組已經生成
# from published_rules.python.rules_20241103_120000 import ProofreadingEngine


def demonstrate_rule_publishing():
    """演示規則發布流程"""

    print("=" * 60)
    print("規則發布與代碼生成演示")
    print("=" * 60)

    # 1. 模擬已審查通過的規則
    approved_rules = [
        {
            "rule_id": "R001",
            "rule_type": "typo_correction",
            "natural_language": "當看到「錯別字」時，建議改為「錯誤字」",
            "pattern": r"錯別字",
            "replacement": "錯誤字",
            "confidence": 0.95,
            "examples": [
                {"before": "文章中有錯別字", "after": "文章中有錯誤字"}
            ]
        },
        {
            "rule_id": "R002",
            "rule_type": "punctuation",
            "natural_language": "中英文之間應該加入空格",
            "pattern": r"([中文])([a-zA-Z])",
            "replacement": r"\1 \2",
            "confidence": 0.88,
            "examples": [
                {"before": "使用API介面", "after": "使用 API 介面"}
            ]
        },
        {
            "rule_id": "R003",
            "rule_type": "style",
            "natural_language": "段落開頭的「因此」建議改為「所以」（非正式文檔）",
            "pattern": r"^因此",
            "replacement": "所以",
            "confidence": 0.75,
            "conditions": {"only_informal": True}
        }
    ]

    print("\n📋 待發布規則：")
    for rule in approved_rules:
        print(f"  - [{rule['rule_id']}] {rule['natural_language']}")
        print(f"    類型: {rule['rule_type']}, 置信度: {rule['confidence']}")

    # 2. 發布請求
    publish_request = {
        "name": "2024年11月校對規則集",
        "description": "包含錯字修正、標點符號和風格建議的規則集",
        "include_rejected": False,
        "test_mode": False,
        "activation_date": datetime.utcnow().isoformat()
    }

    print(f"\n📦 發布規則集: {publish_request['name']}")

    # 3. 模擬編譯過程
    print("\n🔧 編譯規則...")
    print("  ✓ 解析自然語言描述")
    print("  ✓ 編譯正則表達式模式")
    print("  ✓ 計算優先級（基於置信度和類型）")
    print("  ✓ 生成條件檢查邏輯")

    # 4. 生成可執行代碼
    print("\n💻 生成可執行代碼：")

    # Python 模組範例
    python_code = '''
# rules_20241103_120000.py
import re
from typing import List, Dict, Any, Tuple

class ProofreadingEngine:
    def __init__(self):
        self.rules = [
            {
                "rule_id": "R001",
                "pattern": re.compile(r"錯別字"),
                "replacement": "錯誤字",
                "confidence": 0.95,
                "priority": 115  # 95 + 20 (typo_correction)
            },
            {
                "rule_id": "R002",
                "pattern": re.compile(r"([\\u4e00-\\u9fff])([a-zA-Z])"),
                "replacement": r"\\1 \\2",
                "confidence": 0.88,
                "priority": 103  # 88 + 15 (punctuation)
            }
        ]

    def process_text(self, text: str, context: Dict = None) -> Tuple[str, List]:
        result = text
        changes = []

        for rule in self.rules:
            matches = list(rule["pattern"].finditer(result))
            for match in reversed(matches):
                start, end = match.span()
                changes.append({
                    "rule_id": rule["rule_id"],
                    "position": [start, end],
                    "original": match.group(),
                    "replacement": rule["replacement"]
                })
                result = result[:start] + rule["replacement"] + result[end:]

        return result, changes
'''

    print("  ✓ Python 模組: rules_20241103_120000.py")

    # TypeScript 模組範例
    typescript_code = '''
// rules_20241103_120000.ts
export interface Rule {
    ruleId: string;
    pattern: string;
    replacement: string;
    confidence: number;
    priority: number;
}

export class ProofreadingEngine {
    private rules: Rule[] = [
        {
            ruleId: "R001",
            pattern: "錯別字",
            replacement: "錯誤字",
            confidence: 0.95,
            priority: 115
        },
        {
            ruleId: "R002",
            pattern: "([\\u4e00-\\u9fff])([a-zA-Z])",
            replacement: "$1 $2",
            confidence: 0.88,
            priority: 103
        }
    ];

    processText(text: string): { text: string; changes: any[] } {
        let result = text;
        const changes = [];

        // 應用規則...

        return { text: result, changes };
    }
}
'''

    print("  ✓ TypeScript 模組: rules_20241103_120000.ts")
    print("  ✓ JSON 配置: rules_20241103_120000.json")

    # 5. 使用發布的規則
    print("\n🚀 使用發布的規則：")

    test_text = "這篇文章包含錯別字，使用API介面時要注意。因此需要仔細檢查。"
    print(f"\n原始文本：\n  {test_text}")

    # 模擬執行校對
    corrected_text = "這篇文章包含錯誤字，使用 API 介面時要注意。所以需要仔細檢查。"
    changes = [
        {"rule_id": "R001", "position": [7, 10], "original": "錯別字", "replacement": "錯誤字"},
        {"rule_id": "R002", "position": [13, 16], "original": "使用API", "replacement": "使用 API"},
        {"rule_id": "R003", "position": [24, 26], "original": "因此", "replacement": "所以"}
    ]

    print(f"\n校對後文本：\n  {corrected_text}")

    print("\n📊 變更詳情：")
    for change in changes:
        print(f"  - 規則 {change['rule_id']}: "{change['original']}" → "{change['replacement']}"")
        print(f"    位置: {change['position']}")

    # 6. 下載連結
    print("\n📥 下載編譯後的規則：")
    ruleset_id = "ruleset_20241103_120000"
    print(f"  Python:     /api/v1/proofreading/decisions/rules/download/{ruleset_id}/python")
    print(f"  TypeScript: /api/v1/proofreading/decisions/rules/download/{ruleset_id}/typescript")
    print(f"  JSON:       /api/v1/proofreading/decisions/rules/download/{ruleset_id}/json")

    # 7. 整合範例
    print("\n🔗 整合範例：")
    print("\n後端整合（Python）:")
    print("""
    from published_rules.python.rules_20241103_120000 import ProofreadingEngine

    engine = ProofreadingEngine()
    corrected, changes = engine.process_text(article_content)
    """)

    print("\n前端整合（React）:")
    print("""
    import { ProofreadingEngine } from '@/rules/rules_20241103_120000';

    const engine = new ProofreadingEngine();
    const { text, changes } = engine.processText(originalText);
    """)

    print("\nAPI 調用:")
    print("""
    POST /api/v1/proofreading/decisions/rules/apply/ruleset_20241103_120000
    {
        "content": "要校對的文本",
        "context": {"document_type": "article", "is_formal": false}
    }
    """)

    # 8. 版本管理
    print("\n📦 版本管理：")
    print("  當前版本: v1.0.0")
    print("  創建時間: 2024-11-03 12:00:00")
    print("  規則數量: 3")
    print("  狀態: active")

    print("\n✅ 規則發布完成！")
    print("=" * 60)


def demonstrate_usage_in_production():
    """演示在生產環境中的使用"""

    print("\n" + "=" * 60)
    print("生產環境使用範例")
    print("=" * 60)

    # 範例 1: 自動校對文章
    print("\n📝 範例 1: 自動校對文章")
    print("""
    async def auto_proofread_article(article_id: int):
        # 1. 獲取文章
        article = await get_article(article_id)

        # 2. 載入最新規則集
        from published_rules.python.latest_rules import ProofreadingEngine
        engine = ProofreadingEngine()

        # 3. 執行校對
        corrected_text, changes = engine.process_text(
            article.content,
            {"document_type": article.type}
        )

        # 4. 保存結果
        await save_proofreading_result(
            article_id=article_id,
            original=article.content,
            corrected=corrected_text,
            changes=changes
        )

        return {"success": True, "changes_applied": len(changes)}
    """)

    # 範例 2: 批量處理
    print("\n📚 範例 2: 批量處理文章")
    print("""
    async def batch_proofread(article_ids: List[int]):
        from published_rules.python.latest_rules import ProofreadingEngine
        engine = ProofreadingEngine()

        results = []
        for article_id in article_ids:
            article = await get_article(article_id)
            corrected, changes = engine.process_text(article.content)

            results.append({
                "article_id": article_id,
                "changes_count": len(changes),
                "corrected": corrected
            })

        return results
    """)

    # 範例 3: 實時校對 API
    print("\n⚡ 範例 3: 實時校對 API")
    print("""
    @router.post("/realtime-proofread")
    async def realtime_proofread(text: str, ruleset_id: Optional[str] = None):
        # 使用指定或最新的規則集
        if ruleset_id:
            response = await apply_published_rules(
                ruleset_id=ruleset_id,
                content=text,
                context={"realtime": True}
            )
        else:
            from published_rules.python.latest_rules import proofread
            corrected, changes = proofread(text)
            response = {
                "original": text,
                "corrected": corrected,
                "changes": changes
            }

        return response
    """)

    # 範例 4: 前端集成
    print("\n🎨 範例 4: React 組件集成")
    print("""
    // ProofreadingEditor.tsx
    import React, { useState } from 'react';
    import { ProofreadingEngine } from '@/rules/latest_rules';

    export const ProofreadingEditor: React.FC = () => {
        const [text, setText] = useState('');
        const [corrections, setCorrections] = useState([]);
        const engine = new ProofreadingEngine();

        const handleProofread = () => {
            const { text: corrected, changes } = engine.processText(text);
            setCorrections(changes);

            // 高亮顯示變更
            highlightChanges(changes);
        };

        return (
            <div>
                <textarea value={text} onChange={(e) => setText(e.target.value)} />
                <button onClick={handleProofread}>校對</button>
                <div className="corrections">
                    {corrections.map((c, i) => (
                        <div key={i}>
                            {c.original} → {c.replacement}
                        </div>
                    ))}
                </div>
            </div>
        );
    };
    """)

    print("\n✨ 生產環境部署完成！")
    print("=" * 60)


if __name__ == "__main__":
    # 執行演示
    demonstrate_rule_publishing()
    demonstrate_usage_in_production()