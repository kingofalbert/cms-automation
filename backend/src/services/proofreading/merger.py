"""Merge AI and deterministic proofreading results."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable

from src.services.proofreading.models import (
    ProofreadingIssue,
    ProofreadingResult,
    ProofreadingStatistics,
    RuleSource,
)


class ProofreadingResultMerger:
    """Utility to merge AI & script issues with deterministic precedence."""

    def merge(
        self,
        ai_result: ProofreadingResult,
        script_issues: Iterable[ProofreadingIssue],
    ) -> ProofreadingResult:
        """Merge two sources of issues into a unified result."""
        if ai_result.statistics is None:
            ai_result.statistics = ProofreadingStatistics()

        merged: dict[str, ProofreadingIssue] = {}
        ai_keys: set[tuple[str, str | None]] = set()
        script_only: list[ProofreadingIssue] = []
        script_keys: set[tuple[str, str | None]] = set()

        # Index AI issues by rule id + evidence hash to avoid collisions
        for issue in ai_result.issues:
            key = self._issue_key(issue)
            merged[key] = issue
            ai_keys.add(key)

        # Merge deterministic issues with precedence
        for script_issue in script_issues:
            key = self._issue_key(script_issue)
            script_keys.add(key)
            if key in merged:
                merged_issue = self._merge_issue_pair(
                    merged[key], script_issue
                )
                merged[key] = merged_issue
            else:
                merged[key] = script_issue
                script_only.append(script_issue)

        unified_issues = list(merged.values())

        # Apply semantic deduplication to remove cross-rule duplicates
        # (same original_text + suggestion from different rules)
        deduplicated_issues = self._semantic_deduplicate(unified_issues)

        # Filter out noise issues (confirmations of correct usage)
        # These provide no value to users and only add clutter
        filtered_issues = self._filter_noise_issues(deduplicated_issues)

        ai_result.issues = filtered_issues
        ai_result.statistics = self._recalculate_statistics(
            filtered_issues,
            ai_only_count=len([key for key in ai_keys if key not in script_keys]),
            script_only_count=len([key for key in script_keys if key not in ai_keys]),
        )
        return ai_result

    @staticmethod
    def _issue_key(issue: ProofreadingIssue) -> tuple[str, str | None]:
        """Create a deterministic key for deduplication.

        Uses (rule_id, evidence_hash) for rule-level deduplication.
        """
        evidence_hash = (issue.evidence or "")[:64]
        return issue.rule_id, evidence_hash

    @staticmethod
    def _semantic_key(issue: ProofreadingIssue) -> tuple[str | None, str | None, int | None]:
        """Create a semantic key for cross-rule deduplication.

        Uses (original_text, suggestion, position_start) to identify
        issues that point to the same text with the same fix suggestion,
        even if they come from different rules.
        """
        position_start = None
        if issue.plain_text_position:
            position_start = issue.plain_text_position.start
        elif issue.location and isinstance(issue.location, dict):
            position_start = issue.location.get("start")

        # Normalize text for comparison (strip whitespace)
        original = (issue.original_text or "").strip() if issue.original_text else None
        suggestion = (issue.suggestion or "").strip() if issue.suggestion else None

        return original, suggestion, position_start

    def _semantic_deduplicate(
        self, issues: list[ProofreadingIssue]
    ) -> list[ProofreadingIssue]:
        """Remove duplicate issues that point to the same text with the same fix.

        When multiple rules flag the same (original_text, suggestion, position),
        keep only one issue, preferring higher severity.
        """
        # Severity ranking: higher value = keep this one
        severity_rank = {
            "critical": 4,
            "error": 3,
            "warning": 2,
            "info": 1,
        }

        seen: dict[tuple[str | None, str | None, int | None], ProofreadingIssue] = {}

        for issue in issues:
            semantic_key = self._semantic_key(issue)

            # Skip issues without original_text (can't dedupe meaningfully)
            if semantic_key[0] is None:
                # Keep all issues without original_text
                # Use a unique key to avoid collision
                unique_key = (issue.rule_id, issue.evidence, id(issue))
                seen[unique_key] = issue
                continue

            if semantic_key not in seen:
                seen[semantic_key] = issue
            else:
                # Compare severity and keep the higher one
                existing = seen[semantic_key]
                existing_rank = severity_rank.get(existing.severity, 0)
                new_rank = severity_rank.get(issue.severity, 0)

                if new_rank > existing_rank:
                    # New issue has higher severity, replace
                    seen[semantic_key] = issue
                elif new_rank == existing_rank:
                    # Same severity, prefer SCRIPT or MERGED source over AI
                    if issue.source in {RuleSource.SCRIPT, RuleSource.MERGED} and existing.source == RuleSource.AI:
                        seen[semantic_key] = issue

        return list(seen.values())

    @staticmethod
    def _filter_noise_issues(
        issues: list[ProofreadingIssue],
    ) -> list[ProofreadingIssue]:
        """Filter out confirmation/noise issues that provide no value.

        Removes issues that:
        1. Have "無需修改", "格式正確", "正確使用", "已正確", "保留" in suggestion
        2. Suggest no change (suggestion == original_text)
        3. Are purely confirmatory with no actionable suggestion

        These issues only clutter the UI and waste reviewer time.
        """
        # Phrases that indicate a confirmation rather than an actual issue
        confirmation_phrases = [
            "無需修改",
            "格式正確",
            "正確使用",
            "已正確",
            "使用正確",
            "符合規範",
            "無需調整",
            "可保留",
            "建議保留",
            "無問題",
        ]

        filtered = []
        for issue in issues:
            suggestion = (issue.suggestion or "").strip()
            original = (issue.original_text or "").strip()
            message = (issue.message or "").strip()

            # Skip if suggestion is empty
            if not suggestion:
                continue

            # Skip if suggestion equals original (no change)
            if suggestion == original:
                continue

            # Skip if suggestion contains confirmation phrases
            is_confirmation = any(
                phrase in suggestion for phrase in confirmation_phrases
            )
            if is_confirmation:
                continue

            # Skip if message indicates it's a confirmation
            is_message_confirmation = any(
                phrase in message for phrase in confirmation_phrases
            )
            if is_message_confirmation and not suggestion:
                continue

            # Keep this issue - it's actionable
            filtered.append(issue)

        return filtered

    @staticmethod
    def _merge_issue_pair(
        ai_issue: ProofreadingIssue,
        script_issue: ProofreadingIssue,
    ) -> ProofreadingIssue:
        """When both AI and script hit same rule, prefer script severity."""
        merged_issue = script_issue.copy()
        merged_issue.source = RuleSource.MERGED
        merged_issue.confidence = max(ai_issue.confidence, script_issue.confidence)
        merged_issue.suggestion = script_issue.suggestion or ai_issue.suggestion
        merged_issue.message = script_issue.message or ai_issue.message
        merged_issue.attributed_by = (
            f"{ai_issue.attributed_by or 'ai'},{script_issue.attributed_by or 'script'}"
        )
        return merged_issue

    @staticmethod
    def _recalculate_statistics(
        issues: list[ProofreadingIssue],
        ai_only_count: int,
        script_only_count: int,
    ) -> ProofreadingStatistics:
        stats = ProofreadingStatistics()
        stats.total_issues = len(issues)
        stats.script_issue_count = sum(
            1 for issue in issues if issue.source in {RuleSource.SCRIPT, RuleSource.MERGED}
        )
        stats.ai_issue_count = sum(
            1 for issue in issues if issue.source in {RuleSource.AI, RuleSource.MERGED}
        )
        stats.blocking_issue_count = sum(
            1 for issue in issues if issue.blocks_publish
        )

        category_counter: dict[str, int] = defaultdict(int)
        source_counter: dict[str, int] = defaultdict(int)
        for issue in issues:
            category_counter[issue.category] += 1
            source_counter[issue.source.value] += 1

        stats.categories = dict(category_counter)
        stats.source_breakdown = dict(source_counter)
        # Provide high-level counts for reporting
        stats.source_breakdown.setdefault("ai_only", ai_only_count)
        stats.source_breakdown.setdefault("script_only", script_only_count)
        return stats
