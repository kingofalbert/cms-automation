"""
增強版校對決策API - 包含完整的規則發布功能
"""

from pathlib import Path
from typing import Literal
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Body, Path as PathParam
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import get_session
from src.services.proofreading_decision import ProofreadingDecisionService
from src.services.rule_compiler import rule_compiler
from src.schemas.proofreading_decision import (
    PublishRulesRequest,
    PublishRulesResponse,
    DraftStatus,
    ReviewStatus
)

router = APIRouter(prefix="/api/v1/proofreading/decisions", tags=["proofreading"])

# 儲存已發布規則的目錄
PUBLISHED_RULES_DIR = Path("published_rules")
PUBLISHED_RULES_DIR.mkdir(exist_ok=True)
(PUBLISHED_RULES_DIR / "python").mkdir(exist_ok=True)
(PUBLISHED_RULES_DIR / "typescript").mkdir(exist_ok=True)
(PUBLISHED_RULES_DIR / "json").mkdir(exist_ok=True)

# 暫時儲存（實際應使用數據庫）
published_rulesets = {}


@router.post("/rules/drafts/{draft_id}/publish", response_model=PublishRulesResponse)
async def publish_rules_enhanced(
    draft_id: str = PathParam(...),
    request: PublishRulesRequest = Body(...),
    session: AsyncSession = Depends(get_session)
):
    """確認並發布規則集為可執行代碼

    完整實現規則發布流程：
    1. 篩選已批准的規則
    2. 編譯規則為可執行代碼
    3. 生成 Python 和 TypeScript 模組
    4. 儲存發布記錄
    """
    try:
        # 獲取草稿（實際應從數據庫獲取）
        from .proofreading_decisions import rule_drafts

        if draft_id not in rule_drafts:
            raise HTTPException(status_code=404, detail="草稿不存在")

        draft = rule_drafts[draft_id]

        # 篩選要發布的規則
        rules_to_publish = []
        for rule in draft.rules:
            if rule.review_status == ReviewStatus.APPROVED or \
               rule.review_status == ReviewStatus.MODIFIED or \
               (request.include_rejected and rule.review_status == ReviewStatus.REJECTED):
                rules_to_publish.append(rule)

        if not rules_to_publish:
            raise HTTPException(status_code=400, detail="沒有可發布的規則")

        # 生成規則集ID
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        ruleset_id = f"ruleset_{timestamp}"
        module_name = f"rules_{timestamp}"

        # 準備元數據
        metadata = {
            "name": request.name,
            "description": request.description,
            "draft_id": draft_id,
            "total_rules": len(rules_to_publish),
            "approved_rules": sum(1 for r in rules_to_publish if r.review_status == ReviewStatus.APPROVED),
            "modified_rules": sum(1 for r in rules_to_publish if r.review_status == ReviewStatus.MODIFIED),
            "activation_date": request.activation_date.isoformat() if request.activation_date else None,
            "test_mode": request.test_mode
        }

        # 使用規則編譯器生成可執行代碼
        # 1. 生成 Python 模組
        python_module_path = rule_compiler.generate_python_module(
            rules=rules_to_publish,
            module_name=module_name,
            output_dir=PUBLISHED_RULES_DIR / "python",
            metadata=metadata
        )

        # 2. 生成 TypeScript 模組
        ts_module_path = rule_compiler.generate_javascript_module(
            rules=rules_to_publish,
            module_name=module_name,
            output_dir=PUBLISHED_RULES_DIR / "typescript"
        )

        # 3. 生成 JSON 配置
        import json
        json_config = {
            "ruleset_id": ruleset_id,
            "module_name": module_name,
            "metadata": metadata,
            "rules": [
                {
                    "rule_id": rule.rule_id,
                    "rule_type": rule.rule_type,
                    "natural_language": rule.natural_language,
                    "pattern": rule.pattern,
                    "replacement": rule.replacement,
                    "conditions": rule.conditions,
                    "confidence": rule.confidence,
                    "examples": [{"before": e.before, "after": e.after} for e in (rule.examples or [])]
                }
                for rule in rules_to_publish
            ],
            "created_at": datetime.utcnow().isoformat(),
            "version": "1.0.0"
        }

        json_path = PUBLISHED_RULES_DIR / "json" / f"{module_name}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(json_config, f, ensure_ascii=False, indent=2)

        # 儲存發布記錄
        published_rulesets[ruleset_id] = {
            "ruleset_id": ruleset_id,
            "module_name": module_name,
            "draft_id": draft_id,
            "metadata": metadata,
            "python_module": str(python_module_path),
            "ts_module": str(ts_module_path),
            "json_config": str(json_path),
            "created_at": datetime.utcnow(),
            "status": "active" if not request.test_mode else "test"
        }

        # 更新草稿狀態
        draft.status = DraftStatus.APPROVED

        return PublishRulesResponse(
            success=True,
            data={
                "ruleset_id": ruleset_id,
                "name": request.name,
                "total_rules": len(rules_to_publish),
                "approved_rules": metadata["approved_rules"],
                "modified_rules": metadata["modified_rules"],
                "status": "published",
                "activation_date": metadata["activation_date"],
                "code_generation": {
                    "success": True,
                    "python_module": str(python_module_path.name),
                    "typescript_module": str(ts_module_path.name),
                    "json_config": str(json_path.name)
                },
                "download_urls": {
                    "python": f"/api/v1/proofreading/decisions/rules/download/{ruleset_id}/python",
                    "typescript": f"/api/v1/proofreading/decisions/rules/download/{ruleset_id}/typescript",
                    "json": f"/api/v1/proofreading/decisions/rules/download/{ruleset_id}/json"
                }
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"發布規則失敗: {str(e)}"
        )


@router.get("/rules/download/{ruleset_id}/{format}")
async def download_compiled_rules(
    ruleset_id: str = PathParam(...),
    format: Literal["python", "typescript", "json"] = PathParam(...)
):
    """下載編譯後的規則模組

    Args:
        ruleset_id: 規則集ID
        format: 下載格式 (python/typescript/json)

    Returns:
        檔案下載響應
    """
    try:
        # 檢查規則集是否存在
        if ruleset_id not in published_rulesets:
            raise HTTPException(status_code=404, detail="規則集不存在")

        ruleset = published_rulesets[ruleset_id]
        module_name = ruleset["module_name"]

        # 根據格式決定檔案路徑
        if format == "python":
            file_path = PUBLISHED_RULES_DIR / "python" / f"{module_name}.py"
            media_type = "text/x-python"
            filename = f"{module_name}.py"
        elif format == "typescript":
            file_path = PUBLISHED_RULES_DIR / "typescript" / f"{module_name}.ts"
            media_type = "text/typescript"
            filename = f"{module_name}.ts"
        else:  # json
            file_path = PUBLISHED_RULES_DIR / "json" / f"{module_name}.json"
            media_type = "application/json"
            filename = f"{module_name}.json"

        # 檢查檔案是否存在
        if not file_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"檔案不存在: {file_path}"
            )

        return FileResponse(
            path=file_path,
            media_type=media_type,
            filename=filename,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"下載失敗: {str(e)}"
        )


@router.get("/rules/published")
async def list_published_rulesets():
    """列出所有已發布的規則集

    Returns:
        已發布規則集列表
    """
    return {
        "success": True,
        "data": {
            "total": len(published_rulesets),
            "rulesets": [
                {
                    "ruleset_id": rs["ruleset_id"],
                    "name": rs["metadata"]["name"],
                    "total_rules": rs["metadata"]["total_rules"],
                    "created_at": rs["created_at"].isoformat(),
                    "status": rs["status"],
                    "download_urls": {
                        "python": f"/api/v1/proofreading/decisions/rules/download/{rs['ruleset_id']}/python",
                        "typescript": f"/api/v1/proofreading/decisions/rules/download/{rs['ruleset_id']}/typescript",
                        "json": f"/api/v1/proofreading/decisions/rules/download/{rs['ruleset_id']}/json"
                    }
                }
                for rs in published_rulesets.values()
            ]
        }
    }


@router.post("/rules/apply/{ruleset_id}")
async def apply_published_rules(
    ruleset_id: str = PathParam(...),
    content: str = Body(..., embed=True),
    context: dict = Body(default={})
):
    """使用已發布的規則處理文本

    Args:
        ruleset_id: 規則集ID
        content: 要處理的文本
        context: 上下文信息（如文檔類型）

    Returns:
        處理結果
    """
    try:
        # 檢查規則集是否存在
        if ruleset_id not in published_rulesets:
            raise HTTPException(status_code=404, detail="規則集不存在")

        ruleset = published_rulesets[ruleset_id]
        module_name = ruleset["module_name"]

        # 動態導入生成的模組
        import sys
        import importlib.util

        module_path = PUBLISHED_RULES_DIR / "python" / f"{module_name}.py"

        # 載入模組
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

        # 使用模組處理文本
        engine = module.ProofreadingEngine()
        result_text, changes = engine.process_text(content, context)

        return {
            "success": True,
            "data": {
                "original": content,
                "result": result_text,
                "changes": changes,
                "total_changes": len(changes),
                "ruleset_id": ruleset_id,
                "context": context
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"應用規則失敗: {str(e)}"
        )


@router.get("/rules/published/{ruleset_id}")
async def get_published_ruleset_detail(
    ruleset_id: str = PathParam(...)
):
    """獲取已發布規則集的詳細信息

    Args:
        ruleset_id: 規則集ID

    Returns:
        規則集詳細信息
    """
    try:
        # 檢查規則集是否存在
        if ruleset_id not in published_rulesets:
            raise HTTPException(status_code=404, detail="規則集不存在")

        ruleset = published_rulesets[ruleset_id]

        # 讀取 JSON 配置獲取詳細規則信息
        json_path = Path(ruleset["json_config"])
        if json_path.exists():
            import json
            with open(json_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        else:
            config = {}

        return {
            "success": True,
            "data": {
                "ruleset_id": ruleset_id,
                "module_name": ruleset["module_name"],
                "metadata": ruleset["metadata"],
                "status": ruleset["status"],
                "created_at": ruleset["created_at"].isoformat(),
                "rules": config.get("rules", []),
                "version": config.get("version", "1.0.0"),
                "files": {
                    "python": ruleset["python_module"],
                    "typescript": ruleset["ts_module"],
                    "json": ruleset["json_config"]
                }
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"獲取規則集詳情失敗: {str(e)}"
        )