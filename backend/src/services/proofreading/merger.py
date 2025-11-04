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
        ai_result.issues = unified_issues
        ai_result.statistics = self._recalculate_statistics(
            unified_issues,
            ai_only_count=len([key for key in ai_keys if key not in script_keys]),
            script_only_count=len([key for key in script_keys if key not in ai_keys]),
        )
        return ai_result

    @staticmethod
    def _issue_key(issue: ProofreadingIssue) -> tuple[str, str | None]:
        """Create a deterministic key for deduplication."""
        evidence_hash = (issue.evidence or "")[:64]
        return issue.rule_id, evidence_hash

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
