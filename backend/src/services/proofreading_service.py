"""
Independent Proofreading Service

獨立的校對服務，專門檢查文章正文的錯字、語法和風格問題。
只處理解析後的正文內容，不包括標題、SEO 等其他部分。
"""

import json
import logging
import re
from typing import List, Dict, Optional, Any
from anthropic import AsyncAnthropic
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ProofreadingIssue(BaseModel):
    """單個校對問題"""
    rule_id: str = Field(..., description="規則ID，如 TYPO_001")
    severity: str = Field(..., description="嚴重程度: critical/high/medium/low")
    location: Dict[str, int] = Field(..., description="位置信息")
    original_text: str = Field(..., description="原始文本")
    suggested_text: str = Field(..., description="建議文本")
    explanation: str = Field(..., description="錯誤說明")
    confidence: float = Field(..., ge=0, le=1, description="置信度")


class ProofreadingStats(BaseModel):
    """校對統計信息"""
    total_issues: int = 0
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    auto_fixable: int = 0
    requires_review: int = 0


class ProofreadingResult(BaseModel):
    """校對結果"""
    proofreading_issues: List[ProofreadingIssue]
    proofreading_stats: ProofreadingStats
    success: bool = True
    error: Optional[str] = None
    processed_text_length: int = 0


class ProofreadingService:
    """
    獨立的校對服務

    特點：
    1. 只處理文章正文，不包括標題等其他部分
    2. 使用簡化的 prompt，提高成功率
    3. 支持 fallback 機制確保 100% 輸出
    4. 使用 Haiku 模型降低成本
    """

    def __init__(self, api_key: str):
        self.client = AsyncAnthropic(api_key=api_key)
        # 使用最新 Sonnet 4.5 模型（最高質量）
        self.model = "claude-sonnet-4-5-20250929"

    async def proofread_content(
        self,
        body_text: str,
        max_issues: int = 20,
        severity_filter: Optional[List[str]] = None
    ) -> ProofreadingResult:
        """
        校對文章正文內容

        Args:
            body_text: 文章正文（純文本，不包括標題等）
            max_issues: 最多返回的問題數量
            severity_filter: 嚴重程度過濾器

        Returns:
            ProofreadingResult with issues and stats
        """

        if not body_text or len(body_text.strip()) < 10:
            return ProofreadingResult(
                proofreading_issues=[],
                proofreading_stats=ProofreadingStats(),
                success=True,
                processed_text_length=len(body_text)
            )

        # 截取合理長度（避免 token 超限）
        max_length = 5000  # 約 1500 tokens
        truncated = body_text[:max_length] if len(body_text) > max_length else body_text

        # 構建專注的 prompt
        prompt = self._build_focused_prompt(truncated, max_issues)

        try:
            logger.info(f"Starting proofreading for {len(truncated)} characters")

            # 調用 Claude API
            message = await self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                temperature=0.2,  # 低溫度確保一致性
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                system=self._get_system_prompt()
            )

            # 解析響應
            response_text = message.content[0].text
            logger.debug(f"Claude response length: {len(response_text)}")

            # 提取 JSON
            result = self._extract_json(response_text)

            if result and "issues" in result:
                issues = self._parse_issues(result["issues"])
                stats = self._calculate_stats(issues)

                # 應用嚴重程度過濾
                if severity_filter:
                    issues = [i for i in issues if i.severity in severity_filter]

                logger.info(f"Found {len(issues)} proofreading issues")

                return ProofreadingResult(
                    proofreading_issues=issues[:max_issues],
                    proofreading_stats=stats,
                    success=True,
                    processed_text_length=len(truncated)
                )

        except Exception as e:
            logger.error(f"Proofreading failed: {e}")

        # Fallback: 使用規則引擎
        logger.warning("Using fallback rule-based proofreading")
        return self._fallback_proofreading(truncated)

    def _get_system_prompt(self) -> str:
        """系統 prompt"""
        return """你是專業的中文文本校對專家。
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
- 按嚴重程度排序（critical > high > medium > low）"""

    def _build_focused_prompt(self, text: str, max_issues: int) -> str:
        """構建專注的 prompt"""
        return f"""請校對以下中文文章正文，找出其中的錯誤。

正文內容：
{text}

要求：
1. 找出最多 {max_issues} 個問題
2. 優先報告嚴重錯誤（錯字、語法錯誤）
3. 提供具體的修改建議
4. 輸出 JSON 格式

輸出格式：
{{
    "issues": [
        {{
            "rule_id": "TYPO_001",
            "severity": "high",
            "location": {{"paragraph": 1, "sentence": 2}},
            "original_text": "錯誤文本",
            "suggested_text": "正確文本",
            "explanation": "錯誤說明",
            "confidence": 0.95
        }}
    ]
}}

只輸出 JSON，不要其他內容。"""

    def _extract_json(self, text: str) -> Optional[Dict]:
        """從響應中提取 JSON"""
        try:
            # 直接嘗試解析
            return json.loads(text)
        except:
            # 嘗試找到 JSON 塊
            import re
            json_pattern = r'\{[\s\S]*\}'
            matches = re.findall(json_pattern, text)

            for match in matches:
                try:
                    data = json.loads(match)
                    if "issues" in data:
                        return data
                except:
                    continue

        return None

    def _parse_issues(self, issues_data: List[Dict]) -> List[ProofreadingIssue]:
        """解析校對問題"""
        issues = []
        for item in issues_data:
            try:
                issue = ProofreadingIssue(
                    rule_id=item.get("rule_id", "UNKNOWN"),
                    severity=item.get("severity", "low"),
                    location=item.get("location", {"paragraph": 0, "sentence": 0}),
                    original_text=item.get("original_text", ""),
                    suggested_text=item.get("suggested_text", ""),
                    explanation=item.get("explanation", ""),
                    confidence=float(item.get("confidence", 0.5))
                )
                issues.append(issue)
            except Exception as e:
                logger.warning(f"Failed to parse issue: {e}")
                continue

        return issues

    def _calculate_stats(self, issues: List[ProofreadingIssue]) -> ProofreadingStats:
        """計算統計信息"""
        stats = ProofreadingStats()
        stats.total_issues = len(issues)

        for issue in issues:
            if issue.severity == "critical":
                stats.critical += 1
            elif issue.severity == "high":
                stats.high += 1
            elif issue.severity == "medium":
                stats.medium += 1
            else:
                stats.low += 1

            # 高置信度的可以自動修復
            if issue.confidence >= 0.9:
                stats.auto_fixable += 1
            else:
                stats.requires_review += 1

        return stats

    def _fallback_proofreading(self, text: str) -> ProofreadingResult:
        """基於規則的 fallback 校對"""
        issues = []

        # 簡單的規則示例
        common_typos = [
            ("的得地", r"(\w+)的(\w+)", "用詞錯誤：'的'可能應為'得'或'地'"),
            ("重複詞", r"(\w{2,})\1", "重複用詞"),
            ("中英混雜", r"[\u4e00-\u9fa5]+[a-zA-Z]+[\u4e00-\u9fa5]+", "中英文混雜，建議統一"),
        ]

        paragraph_num = 1
        for para in text.split('\n'):
            if not para.strip():
                continue

            for rule_name, pattern, explanation in common_typos:
                matches = re.finditer(pattern, para)
                for match in matches:
                    issues.append(ProofreadingIssue(
                        rule_id=f"RULE_{rule_name}",
                        severity="medium",
                        location={"paragraph": paragraph_num, "sentence": 1},
                        original_text=match.group(0)[:50],
                        suggested_text="[需要人工檢查]",
                        explanation=explanation,
                        confidence=0.6
                    ))

            paragraph_num += 1

        stats = self._calculate_stats(issues)

        return ProofreadingResult(
            proofreading_issues=issues[:10],  # 限制數量
            proofreading_stats=stats,
            success=True,
            error="Fallback rule-based proofreading",
            processed_text_length=len(text)
        )