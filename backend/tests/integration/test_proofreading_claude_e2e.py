"""
校對規則系統的端到端集成測試
測試從規則創建、Claude 編譯、發布到下載和應用的完整流程
"""

import pytest
import json
import os
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi import FastAPI
from httpx import AsyncClient

from src.api.routes import register_routes
from src.schemas.proofreading_decision import ReviewStatus


# Mock Claude 編譯器以避免實際 API 調用
class MockClaudeCompiler:
    """Mock Claude 編譯器用於測試"""

    def __init__(self):
        self.compile_count = 0

    def compile_natural_language_to_rule(
        self,
        natural_language: str,
        examples=None,
        context=None
    ):
        """模擬編譯規則"""
        self.compile_count += 1

        # 根據輸入生成模擬的編譯結果
        if "錯別字" in natural_language or "錯誤字" in natural_language:
            return {
                "pattern": r"錯別字",
                "replacement": "錯誤字",
                "rule_type": "style",
                "confidence": 0.95,
                "priority": 105,
                "conditions": {},
                "explanation": "將「錯別字」改為「錯誤字」"
            }
        elif "空格" in natural_language or "英文" in natural_language:
            return {
                "pattern": r"([\u4e00-\u9fff])([a-zA-Z]+)",
                "replacement": r"\1 \2",
                "rule_type": "punctuation",
                "confidence": 0.88,
                "priority": 103,
                "conditions": {"ignore_urls": True},
                "explanation": "中英文之間加入空格"
            }
        elif "重複" in natural_language or "標點" in natural_language:
            return {
                "pattern": r"([。！？])\\1+",
                "replacement": r"\1",
                "rule_type": "punctuation",
                "confidence": 0.92,
                "priority": 107,
                "conditions": {},
                "explanation": "簡化重複標點"
            }
        else:
            # 默認返回
            return {
                "pattern": r"test",
                "replacement": "TEST",
                "rule_type": "unknown",
                "confidence": 0.7,
                "priority": 100,
                "conditions": {},
                "explanation": "測試規則"
            }

    async def batch_compile_rules_async(
        self,
        rules,
        max_concurrent=3
    ):
        """模擬批量編譯"""
        results = []
        for rule in rules:
            result = self.compile_natural_language_to_rule(
                rule.natural_language,
                rule.examples if hasattr(rule, 'examples') else None,
                None
            )
            results.append(result)
        return results


@pytest.fixture
def mock_claude_compiler():
    """提供 Mock Claude 編譯器"""
    return MockClaudeCompiler()


@pytest.fixture
async def app_client(monkeypatch, mock_claude_compiler):
    """提供測試 FastAPI 客戶端"""
    app = FastAPI()
    register_routes(app)

    # Mock Claude 編譯器創建函數
    def create_mock_compiler():
        return mock_claude_compiler

    monkeypatch.setattr(
        "src.services.claude_rule_compiler.create_claude_compiler",
        create_mock_compiler
    )
    monkeypatch.setattr(
        "src.api.routes.proofreading_decisions_claude.create_claude_compiler",
        create_mock_compiler
    )

    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client, mock_claude_compiler


@pytest.mark.asyncio
async def test_proofreading_complete_workflow(app_client):
    """測試完整的校對規則工作流程"""
    client, mock_compiler = app_client

    print("\n" + "="*80)
    print("🧪 開始端到端集成測試")
    print("="*80)

    # ========== 步驟 1: 創建草稿 ==========
    print("\n📝 步驟 1: 創建規則草稿...")

    draft_rules = [
        {
            "natural_language": "當看到「錯別字」時，建議改為「錯誤字」",
            "examples": [
                {"before": "文章中有錯別字", "after": "文章中有錯誤字"}
            ],
            "rule_type": "style"
        },
        {
            "natural_language": "中英文之間應該加入一個空格",
            "examples": [
                {"before": "使用API介面", "after": "使用 API 介面"}
            ],
            "rule_type": "punctuation"
        },
        {
            "natural_language": "將重複的標點符號簡化為單個",
            "examples": [
                {"before": "真的嗎。。。", "after": "真的嗎。"}
            ],
            "rule_type": "punctuation"
        }
    ]

    draft_response = await client.post(
        "/api/v1/proofreading/decisions/rules/draft",
        json={
            "rules": draft_rules,
            "description": "測試規則集",
            "metadata": {"source": "integration_test"}
        }
    )

    assert draft_response.status_code == 200, f"創建草稿失敗: {draft_response.text}"
    draft_data = draft_response.json()
    assert draft_data["success"] is True
    draft_id = draft_data["data"]["draft_id"]
    print(f"✅ 草稿創建成功，ID: {draft_id}")
    print(f"   規則數量: {len(draft_data['data']['rules'])}")

    # ========== 步驟 2: 獲取草稿詳情 ==========
    print("\n📋 步驟 2: 獲取草稿詳情...")

    detail_response = await client.get(
        f"/api/v1/proofreading/decisions/rules/drafts/{draft_id}"
    )

    assert detail_response.status_code == 200
    detail_data = detail_response.json()
    assert detail_data["success"] is True
    assert len(detail_data["data"]["rules"]) == 3
    print(f"✅ 草稿詳情獲取成功")
    print(f"   狀態: {detail_data['data']['status']}")

    # ========== 步驟 3: 批量審查規則 ==========
    print("\n✔️ 步驟 3: 批量審查規則...")

    reviews = []
    for rule in detail_data["data"]["rules"]:
        reviews.append({
            "rule_id": rule["rule_id"],
            "status": "approved",
            "comment": "測試通過"
        })

    review_response = await client.post(
        f"/api/v1/proofreading/decisions/rules/drafts/{draft_id}/review",
        json={"reviews": reviews}
    )

    assert review_response.status_code == 200
    review_data = review_response.json()
    assert review_data["success"] is True
    print(f"✅ 規則審查完成")
    print(f"   已批准: {review_data['data']['approved_count']}")

    # ========== 步驟 4: 使用 Claude 編譯單個規則 ==========
    print("\n🤖 步驟 4: 測試 Claude 單規則編譯...")

    compile_response = await client.post(
        "/api/v1/proofreading/claude/compile-rule",
        json={
            "natural_language": "當看到「錯別字」時，建議改為「錯誤字」",
            "examples": [{"before": "錯別字", "after": "錯誤字"}]
        }
    )

    assert compile_response.status_code == 200
    compile_data = compile_response.json()
    assert compile_data["success"] is True
    assert compile_data["compiler"] == "claude-3.5-sonnet"
    assert "pattern" in compile_data["data"]
    print(f"✅ 單規則編譯成功")
    print(f"   編譯器: {compile_data['compiler']}")
    print(f"   置信度: {compile_data['data']['confidence']}")

    # ========== 步驟 5: 批量編譯規則 ==========
    print("\n🔄 步驟 5: 測試批量編譯...")

    batch_compile_response = await client.post(
        "/api/v1/proofreading/claude/compile-batch",
        json={"rules": draft_rules}
    )

    assert batch_compile_response.status_code == 200
    batch_data = batch_compile_response.json()
    assert batch_data["success"] is True
    assert batch_data["data"]["total"] == 3
    assert len(batch_data["data"]["compiled_rules"]) == 3
    print(f"✅ 批量編譯成功")
    print(f"   編譯數量: {batch_data['data']['total']}")

    # ========== 步驟 6: 發布規則集（使用 Claude 編譯） ==========
    print("\n🚀 步驟 6: 發布規則集...")

    publish_response = await client.post(
        f"/api/v1/proofreading/claude/publish-with-claude/{draft_id}",
        json={
            "name": "測試規則集",
            "description": "集成測試發布的規則集",
            "version": "1.0.0"
        }
    )

    assert publish_response.status_code == 200
    publish_data = publish_response.json()
    assert publish_data["success"] is True
    ruleset_id = publish_data["data"]["ruleset_id"]
    print(f"✅ 規則集發布成功")
    print(f"   規則集 ID: {ruleset_id}")
    print(f"   規則數量: {publish_data['data']['total_rules']}")
    print(f"   編譯統計: {json.dumps(publish_data['data']['compilation_stats'], ensure_ascii=False)}")

    # ========== 步驟 7: 獲取已發布規則集列表 ==========
    print("\n📚 步驟 7: 獲取已發布規則集列表...")

    published_response = await client.get(
        "/api/v1/proofreading/decisions/rules/published"
    )

    assert published_response.status_code == 200
    published_data = published_response.json()
    assert published_data["success"] is True
    print(f"✅ 規則集列表獲取成功")
    print(f"   規則集數量: {len(published_data['data']['rulesets'])}")

    # ========== 步驟 8: 測試規則 ==========
    print("\n🧪 步驟 8: 測試規則應用...")

    test_content = "文章中有錯別字，使用API介面真的很方便。。。"

    test_response = await client.post(
        "/api/v1/proofreading/decisions/rules/test",
        json={
            "rules": [
                {
                    "rule_id": "R001",
                    "natural_language": "錯別字改為錯誤字",
                    "pattern": "錯別字",
                    "replacement": "錯誤字",
                    "rule_type": "style",
                    "confidence": 0.95,
                    "examples": []
                }
            ],
            "test_content": test_content,
            "options": {
                "show_step_by_step": True,
                "apply_conditions": True
            }
        }
    )

    assert test_response.status_code == 200
    test_data = test_response.json()
    assert test_data["success"] is True
    print(f"✅ 規則測試完成")
    print(f"   原始文本: {test_content}")
    print(f"   修改建議數: {test_data['data']['total_suggestions']}")

    # ========== 步驟 9: 比較編譯方法 ==========
    print("\n📊 步驟 9: 比較不同編譯方法...")

    compare_response = await client.get(
        "/api/v1/proofreading/claude/compare-compilers"
    )

    assert compare_response.status_code == 200
    compare_data = compare_response.json()
    assert compare_data["success"] is True
    print(f"✅ 編譯方法比較完成")
    print(f"   比較方法數: {len(compare_data['comparison'])}")

    # ========== 測試完成統計 ==========
    print("\n" + "="*80)
    print("📈 測試完成統計")
    print("="*80)
    print(f"✅ 草稿創建: 成功")
    print(f"✅ 草稿獲取: 成功")
    print(f"✅ 規則審查: 成功")
    print(f"✅ Claude 單規則編譯: 成功 (調用 {mock_compiler.compile_count} 次)")
    print(f"✅ Claude 批量編譯: 成功")
    print(f"✅ 規則集發布: 成功")
    print(f"✅ 規則集列表: 成功")
    print(f"✅ 規則測試: 成功")
    print(f"✅ 編譯方法比較: 成功")
    print("\n🎉 所有測試通過！")


@pytest.mark.asyncio
async def test_claude_compilation_error_handling(app_client):
    """測試 Claude 編譯錯誤處理"""
    client, mock_compiler = app_client

    print("\n" + "="*80)
    print("🧪 測試錯誤處理")
    print("="*80)

    # 測試空輸入
    response = await client.post(
        "/api/v1/proofreading/claude/compile-rule",
        json={
            "natural_language": "",
            "examples": []
        }
    )

    # 應該返回錯誤或使用回退方法
    print(f"空輸入響應狀態碼: {response.status_code}")
    print(f"響應: {response.json()}")


@pytest.mark.asyncio
async def test_rule_modification(app_client):
    """測試規則修改功能"""
    client, _ = app_client

    print("\n" + "="*80)
    print("🧪 測試規則修改")
    print("="*80)

    # 1. 創建草稿
    draft_response = await client.post(
        "/api/v1/proofreading/decisions/rules/draft",
        json={
            "rules": [{
                "natural_language": "測試規則",
                "examples": [],
                "rule_type": "style"
            }],
            "description": "測試修改"
        }
    )

    draft_id = draft_response.json()["data"]["draft_id"]
    rules = draft_response.json()["data"]["rules"]
    rule_id = rules[0]["rule_id"]

    # 2. 修改規則
    modify_response = await client.put(
        f"/api/v1/proofreading/decisions/rules/drafts/{draft_id}/rules/{rule_id}",
        json={
            "natural_language": "修改後的規則",
            "pattern": "new_pattern",
            "replacement": "new_replacement"
        }
    )

    assert modify_response.status_code == 200
    modify_data = modify_response.json()
    assert modify_data["success"] is True
    print(f"✅ 規則修改成功")


@pytest.mark.asyncio
async def test_draft_lifecycle(app_client):
    """測試草稿的完整生命週期"""
    client, _ = app_client

    print("\n" + "="*80)
    print("🧪 測試草稿生命週期")
    print("="*80)

    # 1. 創建草稿
    create_response = await client.post(
        "/api/v1/proofreading/decisions/rules/draft",
        json={
            "rules": [{
                "natural_language": "生命週期測試",
                "examples": [],
                "rule_type": "grammar"
            }],
            "description": "生命週期測試"
        }
    )
    assert create_response.status_code == 200
    draft_id = create_response.json()["data"]["draft_id"]
    print(f"✅ 草稿創建: {draft_id}")

    # 2. 獲取草稿列表
    list_response = await client.get(
        "/api/v1/proofreading/decisions/rules/drafts"
    )
    assert list_response.status_code == 200
    drafts = list_response.json()["data"]["drafts"]
    assert len(drafts) > 0
    print(f"✅ 草稿列表獲取: {len(drafts)} 個草稿")

    # 3. 獲取特定草稿
    detail_response = await client.get(
        f"/api/v1/proofreading/decisions/rules/drafts/{draft_id}"
    )
    assert detail_response.status_code == 200
    print(f"✅ 草稿詳情獲取成功")

    # 4. 審查規則
    rules = detail_response.json()["data"]["rules"]
    review_response = await client.post(
        f"/api/v1/proofreading/decisions/rules/drafts/{draft_id}/review",
        json={
            "reviews": [{
                "rule_id": rules[0]["rule_id"],
                "status": "approved",
                "comment": "通過"
            }]
        }
    )
    assert review_response.status_code == 200
    print(f"✅ 規則審查完成")

    print("\n🎉 草稿生命週期測試完成！")


if __name__ == "__main__":
    # 可以直接運行此文件進行測試
    pytest.main([__file__, "-v", "-s"])
