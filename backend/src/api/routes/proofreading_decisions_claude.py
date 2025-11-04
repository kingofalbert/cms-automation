"""
使用 Claude 3.5 Sonnet 的校對決策 API
整合 AI 編譯功能的完整實現
"""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi import Path as PathParam
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import get_session
from src.schemas.proofreading_decision import DraftRule, Example, PublishRulesRequest, ReviewStatus
from src.services.claude_rule_compiler import create_claude_compiler

router = APIRouter(prefix="/api/v1/proofreading/claude", tags=["claude-proofreading"])


@router.post("/compile-rule")
async def compile_rule_with_claude(
    natural_language: str = Body(..., description="自然語言規則描述"),
    examples: list[dict[str, str]] | None = Body(default=None, description="示例列表"),
    context: dict[str, Any] | None = Body(default=None, description="上下文信息")
):
    """
    使用 Claude 3.5 Sonnet 編譯單個規則

    Args:
        natural_language: 規則的自然語言描述
        examples: 輸入輸出示例
        context: 額外的上下文信息

    Returns:
        編譯後的規則結構
    """
    try:
        # 創建 Claude 編譯器
        compiler = create_claude_compiler()

        # 編譯規則
        compiled_rule = compiler.compile_natural_language_to_rule(
            natural_language=natural_language,
            examples=examples,
            context=context
        )

        return {
            "success": True,
            "data": compiled_rule,
            "compiler": "claude-3.5-sonnet",
            "timestamp": datetime.utcnow().isoformat()
        }

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"配置錯誤: {str(e)}. 請確保已設置 ANTHROPIC_API_KEY"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"編譯失敗: {str(e)}"
        )


@router.post("/compile-batch")
async def compile_batch_rules_with_claude(
    rules: list[dict[str, Any]] = Body(..., description="規則列表")
):
    """
    批量使用 Claude 編譯多個規則

    Args:
        rules: 包含自然語言描述的規則列表

    Returns:
        編譯後的規則列表
    """
    try:
        compiler = create_claude_compiler()

        # 將字典轉換為 DraftRule 對象
        draft_rules = []
        for rule_dict in rules:
            # 轉換 examples 為 Example 對象
            examples = []
            for ex in rule_dict.get("examples", []):
                if isinstance(ex, dict):
                    examples.append(Example(before=ex["before"], after=ex["after"]))
                else:
                    examples.append(ex)

            draft_rule = DraftRule(
                rule_id=rule_dict.get("rule_id", f"R{len(draft_rules)+1:03d}"),
                rule_type=rule_dict.get("rule_type", "unknown"),
                natural_language=rule_dict["natural_language"],
                examples=examples,
                conditions=rule_dict.get("conditions", {}),
                confidence=rule_dict.get("confidence", 0.5),
                review_status=ReviewStatus.PENDING
            )
            draft_rules.append(draft_rule)

        # 異步批量編譯
        compiled_rules = await compiler.batch_compile_rules_async(
            draft_rules,
            max_concurrent=5  # 限制並發數
        )

        return {
            "success": True,
            "data": {
                "total": len(compiled_rules),
                "compiled_rules": compiled_rules,
                "compiler": "claude-3.5-sonnet",
                "timestamp": datetime.utcnow().isoformat()
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"批量編譯失敗: {str(e)}"
        )


@router.post("/test-compilation")
async def test_claude_compilation():
    """
    測試 Claude 編譯器的各種場景

    Returns:
        測試結果
    """
    test_cases = [
        {
            "description": "當看到「錯別字」時，建議改為「錯誤字」",
            "examples": [
                {"before": "文章中有錯別字", "after": "文章中有錯誤字"}
            ]
        },
        {
            "description": "中英文之間應該加入一個空格",
            "examples": [
                {"before": "使用API介面", "after": "使用 API 介面"},
                {"before": "Python語言", "after": "Python 語言"}
            ]
        },
        {
            "description": "將重複的標點符號簡化為單個，如「。。。」改為「。」",
            "examples": [
                {"before": "真的嗎。。。", "after": "真的嗎。"},
                {"before": "太棒了！！！", "after": "太棒了！"}
            ]
        },
        {
            "description": "段落開頭的「因此」在非正式文檔中建議改為「所以」",
            "context": {"document_type": "informal"},
            "examples": [
                {"before": "因此，我們決定", "after": "所以，我們決定"}
            ]
        }
    ]

    try:
        compiler = create_claude_compiler()
        results = []

        for test_case in test_cases:
            compiled = compiler.compile_natural_language_to_rule(
                natural_language=test_case["description"],
                examples=test_case.get("examples"),
                context=test_case.get("context")
            )

            # 測試編譯結果
            test_result = {
                "description": test_case["description"],
                "compiled_rule": compiled,
                "test_status": "success" if compiled.get("pattern") else "partial"
            }

            results.append(test_result)

        return {
            "success": True,
            "data": {
                "test_count": len(results),
                "results": results,
                "compiler": "claude-3.5-sonnet"
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"測試失敗: {str(e)}"
        )


@router.post("/publish-with-claude/{draft_id}")
async def publish_rules_with_claude_compilation(
    draft_id: str = PathParam(...),
    request: PublishRulesRequest = Body(...),
    session: AsyncSession = Depends(get_session)
):
    """
    使用 Claude 編譯並發布規則集

    完整流程：
    1. 獲取草稿規則
    2. 使用 Claude 編譯自然語言規則
    3. 生成可執行代碼
    4. 發布到生產環境
    """
    try:
        # 獲取草稿（實際應從數據庫）
        from .proofreading_decisions import rule_drafts
        if draft_id not in rule_drafts:
            raise HTTPException(status_code=404, detail="草稿不存在")

        draft = rule_drafts[draft_id]

        # 篩選要發布的規則
        rules_to_compile = []
        for rule in draft.rules:
            if rule.review_status in [ReviewStatus.APPROVED, ReviewStatus.MODIFIED]:
                rules_to_compile.append(rule)

        if not rules_to_compile:
            raise HTTPException(status_code=400, detail="沒有可發布的規則")

        # 使用 Claude 編譯規則
        compiler = create_claude_compiler()

        # 異步批量編譯
        compiled_rules = await compiler.batch_compile_rules_async(
            rules_to_compile,
            max_concurrent=3  # Claude API 並發限制
        )

        # 生成規則集 ID
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        ruleset_id = f"claude_ruleset_{timestamp}"

        # 使用編譯後的規則生成可執行代碼
        from ...services.rule_compiler import rule_compiler

        # 創建增強的規則對象
        enhanced_rules = []
        for original_rule, compiled_data in zip(rules_to_compile, compiled_rules, strict=False):
            # 更新原規則的模式和替換
            original_rule.pattern = compiled_data.get("pattern", "")
            original_rule.replacement = compiled_data.get("replacement", "")
            original_rule.confidence = compiled_data.get("confidence", 0.5)
            original_rule.conditions = compiled_data.get("conditions", {})
            enhanced_rules.append(original_rule)

        # 生成 Python 和 TypeScript 模組
        from pathlib import Path
        output_dir = Path("published_rules")
        output_dir.mkdir(exist_ok=True)

        python_module = rule_compiler.generate_python_module(
            rules=enhanced_rules,
            module_name=f"claude_{timestamp}",
            output_dir=output_dir / "python",
            metadata={
                "compiler": "claude-3.5-sonnet",
                "name": request.name,
                "description": request.description,
                "compilation_time": datetime.utcnow().isoformat()
            }
        )

        ts_module = rule_compiler.generate_javascript_module(
            rules=enhanced_rules,
            module_name=f"claude_{timestamp}",
            output_dir=output_dir / "typescript"
        )

        return {
            "success": True,
            "data": {
                "ruleset_id": ruleset_id,
                "name": request.name,
                "total_rules": len(enhanced_rules),
                "compiler": "claude-3.5-sonnet",
                "compilation_stats": {
                    "successful": len([r for r in compiled_rules if r.get("pattern")]),
                    "partial": len([r for r in compiled_rules if not r.get("pattern")]),
                    "average_confidence": sum(r.get("confidence", 0) for r in compiled_rules) / len(compiled_rules)
                },
                "files": {
                    "python": str(python_module.name),
                    "typescript": str(ts_module.name)
                },
                "download_urls": {
                    "python": f"/api/v1/proofreading/claude/download/{ruleset_id}/python",
                    "typescript": f"/api/v1/proofreading/claude/download/{ruleset_id}/typescript"
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        }

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"API 密鑰錯誤: {str(e)}"
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"發布失敗: {str(e)}"
        )


@router.get("/compare-compilers")
async def compare_compilation_methods():
    """
    比較不同編譯方法的效果

    Returns:
        各種編譯方法的比較結果
    """
    test_case = {
        "description": "中英文之間應該加入空格，但標點符號前不需要",
        "examples": [
            {"before": "使用Python編程", "after": "使用 Python 編程"},
            {"before": "學習AI技術。", "after": "學習 AI 技術。"}
        ]
    }

    results = {}

    # 1. 基礎方法（正則匹配）
    from .proofreading_decisions import natural_language_to_code
    basic_result = natural_language_to_code(
        test_case["description"],
        test_case.get("examples")
    )
    results["basic_regex"] = {
        "method": "簡單正則表達式匹配",
        "result": basic_result,
        "quality_score": 2  # 1-10 分
    }

    # 2. Claude 3.5 Sonnet
    try:
        compiler = create_claude_compiler()
        claude_result = compiler.compile_natural_language_to_rule(
            test_case["description"],
            test_case.get("examples")
        )
        results["claude_3_5_sonnet"] = {
            "method": "Claude 3.5 Sonnet AI 編譯",
            "result": claude_result,
            "quality_score": 9  # 1-10 分
        }
    except Exception as e:
        results["claude_3_5_sonnet"] = {
            "method": "Claude 3.5 Sonnet AI 編譯",
            "error": str(e),
            "quality_score": 0
        }

    # 3. 增強回退方法
    compiler = create_claude_compiler()
    fallback_result = compiler._enhanced_fallback_compile(
        test_case["description"],
        test_case.get("examples")
    )
    results["enhanced_fallback"] = {
        "method": "增強的模式匹配",
        "result": fallback_result,
        "quality_score": 5  # 1-10 分
    }

    return {
        "success": True,
        "test_case": test_case,
        "comparison": results,
        "recommendation": "建議使用 Claude 3.5 Sonnet 以獲得最佳效果"
    }
