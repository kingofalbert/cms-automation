"""High-level service orchestrating AI + deterministic proofreading."""

from __future__ import annotations

import json
import time
from hashlib import sha256
from typing import Any

from anthropic import AsyncAnthropic

from src.config import get_logger, get_settings
from src.services.proofreading.ai_prompt_builder import (
    ProofreadingPromptBuilder,
    RuleManifest,
    load_default_manifest,
)
from src.services.proofreading.deterministic_engine import DeterministicRuleEngine
from src.services.proofreading.merger import ProofreadingResultMerger
from src.services.proofreading.models import (
    ArticlePayload,
    ProcessingMetadata,
    ProofreadingIssue,
    ProofreadingResult,
    RuleSource,
)

logger = get_logger(__name__)
settings = get_settings()


class ProofreadingAnalysisService:
    """Coordinates single-call AI analysis with deterministic rule checks."""

    def __init__(
        self,
        *,
        anthropic_client: AsyncAnthropic | None = None,
        manifest: RuleManifest | None = None,
    ) -> None:
        self.manifest = manifest or load_default_manifest()
        self.prompt_builder = ProofreadingPromptBuilder(self.manifest)
        self.ai_client = anthropic_client or AsyncAnthropic(
            api_key=settings.ANTHROPIC_API_KEY
        )
        self.model = settings.ANTHROPIC_MODEL
        self.rule_engine = DeterministicRuleEngine()
        self.merger = ProofreadingResultMerger()

    async def analyze_article(self, payload: ArticlePayload) -> ProofreadingResult:
        """Run full analysis pipeline returning merged result."""
        prompt = self.prompt_builder.build_prompt(payload)
        prompt_hash = self._hash_prompt(prompt)

        logger.info(
            "proofreading_analysis_started",
            article_id=payload.article_id,
            model=self.model,
            prompt_hash=prompt_hash,
        )

        start_time = time.perf_counter()
        ai_response = await self._call_ai(prompt)
        latency_ms = int((time.perf_counter() - start_time) * 1000)

        ai_result = self._parse_ai_result(ai_response)
        ai_result.article_id = payload.article_id
        ai_result.processing_metadata.prompt_hash = prompt_hash
        ai_result.processing_metadata.ai_model = self.model
        ai_result.processing_metadata.ai_latency_ms = latency_ms
        ai_result.processing_metadata.rule_manifest_version = self.manifest.version

        # Deterministic scripts
        script_issues = self.rule_engine.run(payload)

        # Merge results
        merged_result = self.merger.merge(ai_result, script_issues)
        merged_result.processing_metadata.script_engine_version = (
            self.rule_engine.VERSION
        )
        merged_result.processing_metadata.notes.setdefault(
            "script_issue_count", len(script_issues)
        )

        logger.info(
            "proofreading_analysis_completed",
            article_id=payload.article_id,
            issues=len(merged_result.issues),
            blocking=len(merged_result.blocking_issues),
            latency_ms=latency_ms,
        )

        return merged_result

    async def _call_ai(self, prompt: dict[str, str]) -> dict[str, Any]:
        """Invoke Anthropic Messages API with the combined prompt."""
        response = await self.ai_client.messages.create(
            model=self.model,
            max_tokens=4096,
            temperature=0.2,
            system=prompt["system"],  # System prompt as top-level parameter
            messages=[
                {"role": "user", "content": prompt["user"]},
            ],
        )

        # Anthropic returns content list; we take first text block
        text_content = response.content[0].text if response.content else "{}"

        usage = getattr(response, "usage", None)
        token_info = (
            {
                "input": getattr(usage, "input_tokens", None),
                "output": getattr(usage, "output_tokens", None),
            }
            if usage
            else {}
        )
        return {"text": text_content, "tokens": token_info}

    def _parse_ai_result(self, ai_payload: dict[str, Any]) -> ProofreadingResult:
        """Parse AI JSON payload into ProofreadingResult."""
        text = ai_payload["text"]
        parsed = self._extract_json(text)

        issues_data = parsed.get("issues", [])
        issues: list[ProofreadingIssue] = []
        for raw_issue in issues_data:
            try:
                issue = ProofreadingIssue(
                    rule_id=raw_issue["rule_id"],
                    category=raw_issue.get("category", raw_issue["rule_id"][0]),
                    subcategory=raw_issue.get("subcategory"),
                    message=raw_issue["message"],
                    suggestion=raw_issue.get("suggestion"),
                    severity=raw_issue.get("severity", "warning"),
                    confidence=float(raw_issue.get("confidence", 0.7)),
                    can_auto_fix=bool(raw_issue.get("can_auto_fix", False)),
                    blocks_publish=bool(raw_issue.get("blocks_publish", False)),
                    source=RuleSource.AI,
                    attributed_by="claude",
                    location=raw_issue.get("location"),
                    evidence=raw_issue.get("evidence"),
                )
            except KeyError as exc:
                logger.warning(
                    "proofreading_ai_issue_parse_failed",
                    missing_key=exc.args[0],
                    issue=raw_issue,
                )
                continue
            issues.append(issue)

        result = ProofreadingResult(
            issues=issues,
            suggested_content=parsed.get("suggested_content"),
            seo_metadata=parsed.get("seo_metadata"),
            ai_raw_response=parsed,
        )
        result.processing_metadata = ProcessingMetadata(
            prompt_tokens=ai_payload["tokens"].get("input"),
            completion_tokens=ai_payload["tokens"].get("output"),
            total_tokens=self._calc_total_tokens(ai_payload["tokens"]),
        )
        return result

    @staticmethod
    def _extract_json(text: str) -> dict[str, Any]:
        """Extract JSON object from Claude response."""
        start = text.find("{")
        end = text.rfind("}") + 1
        if start == -1 or end == 0:
            raise ValueError("AI response does not contain a JSON object")
        json_blob = text[start:end]
        return json.loads(json_blob)

    @staticmethod
    def _hash_prompt(prompt: dict[str, str]) -> str:
        """Return SHA256 hash covering system+user prompt."""
        payload = prompt["system"] + "\n" + prompt["user"]
        return sha256(payload.encode("utf-8")).hexdigest()

    @staticmethod
    def _calc_total_tokens(token_info: dict[str, Any]) -> int | None:
        try:
            return int(token_info.get("input") or 0) + int(
                token_info.get("output") or 0
            )
        except (TypeError, ValueError):
            return None
