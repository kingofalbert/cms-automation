"""High-level service orchestrating AI + deterministic proofreading.

Enhanced version supporting:
- Full 405-rule catalog (catalog_full.json)
- Multiple analysis modes (full, quick, seo-only)
- DJY-specific "mixed characteristics" guidelines
"""

from __future__ import annotations

import json
import time
from enum import Enum
from hashlib import sha256
from typing import Any

from anthropic import AsyncAnthropic

from src.config import get_logger, get_settings
from src.services.proofreading.ai_prompt_builder import (
    ProofreadingPromptBuilder,
    RuleManifest,
    load_default_manifest,
    load_full_manifest,
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


class AnalysisMode(str, Enum):
    """Available analysis modes for proofreading."""

    FULL = "full"  # Complete 405-rule analysis
    QUICK = "quick"  # Focused E/F class rules only
    SEO_ONLY = "seo_only"  # SEO metadata generation only
    DETERMINISTIC_ONLY = "deterministic_only"  # Skip AI, run only rule engine


class ProofreadingAnalysisService:
    """Coordinates single-call AI analysis with deterministic rule checks.

    Enhanced version supporting:
    - Full 405-rule catalog with DJY-specific guidelines
    - Multiple analysis modes (full, quick, seo-only, deterministic-only)
    - Token-optimized prompt generation
    """

    # Service version for tracking
    VERSION = "2.0.0"

    def __init__(
        self,
        *,
        anthropic_client: AsyncAnthropic | None = None,
        manifest: RuleManifest | None = None,
        use_full_catalog: bool = True,
        max_rules_in_prompt: int | None = None,
    ) -> None:
        """Initialize the proofreading service.

        Args:
            anthropic_client: Custom Anthropic client (optional)
            manifest: Custom rule manifest (optional)
            use_full_catalog: Whether to use the full 405-rule catalog
            max_rules_in_prompt: Limit rules in prompt for token optimization
        """
        # Load manifest - prefer full catalog if requested
        if manifest:
            self.manifest = manifest
        elif use_full_catalog:
            try:
                self.manifest = load_full_manifest()
                logger.info(
                    "proofreading_full_catalog_loaded",
                    version=self.manifest.version,
                    total_rules=self.manifest.total_rules,
                )
            except FileNotFoundError:
                logger.warning(
                    "proofreading_full_catalog_not_found_falling_back",
                )
                self.manifest = load_default_manifest()
        else:
            self.manifest = load_default_manifest()

        self.prompt_builder = ProofreadingPromptBuilder(
            self.manifest,
            include_full_rules=True,
            max_rules_in_prompt=max_rules_in_prompt,
        )
        self.ai_client = anthropic_client or AsyncAnthropic(
            api_key=settings.ANTHROPIC_API_KEY
        )
        self.model = settings.ANTHROPIC_MODEL
        self.rule_engine = DeterministicRuleEngine()
        self.merger = ProofreadingResultMerger()

    async def analyze_article(
        self,
        payload: ArticlePayload,
        mode: AnalysisMode = AnalysisMode.FULL,
        focus_categories: list[str] | None = None,
    ) -> ProofreadingResult:
        """Run analysis pipeline returning merged result.

        Args:
            payload: Article data to analyze
            mode: Analysis mode (full, quick, seo_only, deterministic_only)
            focus_categories: Categories to focus on for quick mode (e.g., ["E", "F"])

        Returns:
            ProofreadingResult with issues, suggestions, and metadata
        """
        # Handle deterministic-only mode (no AI call)
        if mode == AnalysisMode.DETERMINISTIC_ONLY:
            return await self._run_deterministic_only(payload)

        # Build appropriate prompt based on mode
        if mode == AnalysisMode.SEO_ONLY:
            prompt = self.prompt_builder.build_seo_only_prompt(payload)
        elif mode == AnalysisMode.QUICK:
            prompt = self.prompt_builder.build_quick_check_prompt(
                payload, focus_categories or ["E", "F"]
            )
        else:
            prompt = self.prompt_builder.build_prompt(payload)
        prompt_hash = self._hash_prompt(prompt)

        logger.info(
            "proofreading_analysis_started",
            article_id=payload.article_id,
            model=self.model,
            mode=mode.value,
            manifest_version=self.manifest.version,
            total_rules=self.manifest.total_rules,
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

        # For SEO-only mode, skip deterministic checks
        if mode == AnalysisMode.SEO_ONLY:
            ai_result.processing_metadata.notes["analysis_mode"] = "seo_only"
            ai_result.processing_metadata.notes["service_version"] = self.VERSION
            return ai_result

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
        merged_result.processing_metadata.notes["analysis_mode"] = mode.value
        merged_result.processing_metadata.notes["service_version"] = self.VERSION
        merged_result.processing_metadata.notes["catalog_total_rules"] = self.manifest.total_rules

        logger.info(
            "proofreading_analysis_completed",
            article_id=payload.article_id,
            mode=mode.value,
            issues=len(merged_result.issues),
            blocking=len(merged_result.blocking_issues),
            ai_issues=len(ai_result.issues),
            script_issues=len(script_issues),
            latency_ms=latency_ms,
        )

        return merged_result

    async def _run_deterministic_only(
        self, payload: ArticlePayload
    ) -> ProofreadingResult:
        """Run only the deterministic rule engine without AI.

        Useful for quick validation or when AI quota is limited.
        """
        logger.info(
            "proofreading_deterministic_only_started",
            article_id=payload.article_id,
        )

        start_time = time.perf_counter()
        script_issues = self.rule_engine.run(payload)
        latency_ms = int((time.perf_counter() - start_time) * 1000)

        # Convert to ProofreadingResult
        result = ProofreadingResult(
            article_id=payload.article_id,
            issues=script_issues,
            suggested_content=None,
            seo_metadata=None,
        )
        result.processing_metadata = ProcessingMetadata(
            ai_model=None,
            ai_latency_ms=None,
            script_engine_version=self.rule_engine.VERSION,
            rule_manifest_version=self.manifest.version,
        )
        result.processing_metadata.notes = {
            "analysis_mode": "deterministic_only",
            "service_version": self.VERSION,
            "script_issue_count": len(script_issues),
            "total_latency_ms": latency_ms,
        }

        logger.info(
            "proofreading_deterministic_only_completed",
            article_id=payload.article_id,
            issues=len(script_issues),
            blocking=len(result.blocking_issues),
            latency_ms=latency_ms,
        )

        return result

    async def quick_check(
        self,
        payload: ArticlePayload,
        categories: list[str] | None = None,
    ) -> ProofreadingResult:
        """Convenience method for quick category-focused checks.

        Args:
            payload: Article to check
            categories: Categories to check (default: ["E", "F"] for special/compliance)

        Returns:
            ProofreadingResult with focused issues
        """
        return await self.analyze_article(
            payload,
            mode=AnalysisMode.QUICK,
            focus_categories=categories or ["E", "F"],
        )

    async def seo_analysis(self, payload: ArticlePayload) -> dict[str, Any]:
        """Generate SEO metadata suggestions only.

        Args:
            payload: Article to analyze

        Returns:
            Dict with meta_title, meta_description, keywords, slug_suggestion
        """
        result = await self.analyze_article(payload, mode=AnalysisMode.SEO_ONLY)
        return result.seo_metadata or {}

    async def _call_ai(self, prompt: dict[str, str]) -> dict[str, Any]:
        """Invoke Anthropic Messages API with the combined prompt."""
        response = await self.ai_client.messages.create(
            model=self.model,
            max_tokens=8192,  # Increased to ensure complete JSON responses
            temperature=0.2,
            system=prompt["system"],  # System prompt as top-level parameter
            messages=[
                {"role": "user", "content": prompt["user"]},
            ],
            stop_sequences=["```"],  # Prevent markdown code block wrappers
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

        # Log the raw AI response for debugging
        logger.info(
            "proofreading_ai_raw_response",
            text_length=len(text),
            text_preview=text[:2000] if len(text) > 2000 else text,
        )

        parsed = self._extract_json(text)

        issues_data = parsed.get("issues", [])
        issues: list[ProofreadingIssue] = []
        for raw_issue in issues_data:
            try:
                # Extract original_text from AI response
                # AI returns it as "original_text", fallback to "evidence" if not present
                original_text = raw_issue.get("original_text") or raw_issue.get("evidence")

                issue = ProofreadingIssue(
                    rule_id=raw_issue["rule_id"],
                    category=raw_issue.get("category", raw_issue["rule_id"][0]),
                    subcategory=raw_issue.get("subcategory"),
                    message=raw_issue["message"],
                    original_text=original_text,
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
        """Extract JSON object from Claude response with robust parsing."""
        # Strip markdown code fences if present
        import re
        text = re.sub(r'^```(?:json)?\s*\n?', '', text, flags=re.MULTILINE)
        text = re.sub(r'\n?```\s*$', '', text, flags=re.MULTILINE)
        text = text.strip()

        start = text.find("{")
        end = text.rfind("}") + 1
        if start == -1 or end == 0:
            logger.error(
                "proofreading_json_extraction_failed",
                reason="no_json_found",
                text_preview=text[:200] if len(text) > 200 else text,
            )
            raise ValueError("AI response does not contain a JSON object")
        json_blob = text[start:end]

        # Try standard JSON parsing first
        try:
            return json.loads(json_blob)
        except json.JSONDecodeError as exc:
            logger.warning(
                "proofreading_json_parse_failed_trying_repair",
                error=str(exc),
                json_blob_length=len(json_blob),
                json_blob_preview=json_blob[:1000] if len(json_blob) > 1000 else json_blob,
            )

            # Attempt aggressive JSON repair
            try:
                import re
                repaired = json_blob

                # Remove all types of comments
                repaired = re.sub(r"//.*?$", "", repaired, flags=re.MULTILINE)
                repaired = re.sub(r"/\*.*?\*/", "", repaired, flags=re.DOTALL)

                # Fix trailing commas before closing brackets/braces (multiple passes)
                for _ in range(3):  # Multiple passes to handle nested structures
                    repaired = re.sub(r",(\s*[}\]])", r"\1", repaired)

                # Remove trailing commas at end of lines
                repaired = re.sub(r",(\s*\n)", r"\1", repaired)

                # Fix multiple consecutive commas
                repaired = re.sub(r",\s*,+", ",", repaired)

                # Try parsing the repaired JSON
                return json.loads(repaired)
            except json.JSONDecodeError as repair_exc:
                # If still failing, try one more aggressive approach: truncate at the error position
                try:
                    error_msg = str(repair_exc)
                    if "char" in error_msg:
                        # Extract character position from error message
                        import re
                        match = re.search(r"char (\d+)", error_msg)
                        if match:
                            error_pos = int(match.group(1))
                            # Try to find the last valid closing brace before the error
                            truncated = repaired[:error_pos]
                            last_brace = truncated.rfind("}")
                            if last_brace > 0:
                                # Count opening and closing braces
                                opening = truncated[:last_brace].count("{")
                                closing = truncated[:last_brace].count("}")
                                # Add missing closing braces
                                truncated = truncated[:last_brace+1] + "}" * (opening - closing - 1)
                                logger.info(
                                    "proofreading_json_truncation_attempt",
                                    original_length=len(repaired),
                                    truncated_length=len(truncated),
                                )
                                return json.loads(truncated)
                except:
                    pass  # Fall through to error logging

                logger.error(
                    "proofreading_json_repair_failed",
                    original_error=str(exc),
                    repair_error=str(repair_exc),
                    json_blob_length=len(json_blob),
                    json_blob_preview=json_blob[:2000] if len(json_blob) > 2000 else json_blob,
                )
                raise exc  # Raise the original exception

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
