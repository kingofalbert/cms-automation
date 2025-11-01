"""Deterministic rule engine implementing high-confidence checks."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List

from src.services.proofreading.models import (
    ArticlePayload,
    ProofreadingIssue,
    RuleSource,
)


@dataclass
class DeterministicRule:
    """Base interface for deterministic rules."""

    rule_id: str
    category: str
    subcategory: str
    severity: str
    blocks_publish: bool = False
    can_auto_fix: bool = False

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        """Run rule on payload returning 0..n issues."""
        raise NotImplementedError


class HalfWidthCommaRule(DeterministicRule):
    """Detect half-width comma misuse within Chinese sentences (B2-002)."""

    HALF_WIDTH_COMMA_PATTERN = re.compile(r"(?<!\d),(?!\d)")

    def __init__(self) -> None:
        super().__init__(
            rule_id="B2-002",
            category="B",
            subcategory="B2",
            severity="warning",
            blocks_publish=False,
            can_auto_fix=True,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        matches = list(self.HALF_WIDTH_COMMA_PATTERN.finditer(payload.original_content))
        for match in matches:
            snippet_start = max(0, match.start() - 12)
            snippet_end = min(len(payload.original_content), match.end() + 12)
            snippet = payload.original_content[snippet_start:snippet_end]
            issues.append(
                ProofreadingIssue(
                    rule_id=self.rule_id,
                    category=self.category,
                    subcategory=self.subcategory,
                    message="检测到中文段落使用半角逗号，请改为全角 '，'。",
                    suggestion="将半角 ',' 替换为全角 '，'。",
                    severity=self.severity,
                    confidence=1.0,
                    can_auto_fix=self.can_auto_fix,
                    blocks_publish=self.blocks_publish,
                    source=RuleSource.SCRIPT,
                    attributed_by="HalfWidthCommaRule",
                    location={"offset": match.start()},
                    evidence=snippet,
                )
            )
        return issues


class InvalidHeadingLevelRule(DeterministicRule):
    """Ensure only H2/H3 headings are used within article HTML (F2-001)."""

    INVALID_HEADING_PATTERN = re.compile(r"<h([1465])[^>]*>", re.IGNORECASE)

    def __init__(self) -> None:
        super().__init__(
            rule_id="F2-001",
            category="F",
            subcategory="F2",
            severity="error",
            blocks_publish=True,
            can_auto_fix=False,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        if not payload.html_content:
            return []
        issues: List[ProofreadingIssue] = []
        for match in self.INVALID_HEADING_PATTERN.finditer(payload.html_content):
            level = match.group(1)
            issues.append(
                ProofreadingIssue(
                    rule_id=self.rule_id,
                    category=self.category,
                    subcategory=self.subcategory,
                    message=f"发现不允许的标题层级 <h{level}>，文章小标仅允许 H2/H3。",
                    suggestion="请将该标题改为 <h2> 或 <h3>。",
                    severity=self.severity,
                    confidence=1.0,
                    can_auto_fix=self.can_auto_fix,
                    blocks_publish=self.blocks_publish,
                    source=RuleSource.SCRIPT,
                    attributed_by="InvalidHeadingLevelRule",
                    location={"tag": f"h{level}", "offset": match.start()},
                    evidence=payload.html_content[match.start() : match.end() + 40],
                )
            )
        return issues


class FeaturedImageLandscapeRule(DeterministicRule):
    """Validate featured image landscape ratio requirement (F1-002)."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="F1-002",
            category="F",
            subcategory="F1",
            severity="critical",
            blocks_publish=True,
            can_auto_fix=False,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        featured = payload.featured_image
        if not featured or not featured.width or not featured.height:
            return []
        aspect_ratio = featured.width / featured.height
        if aspect_ratio <= 1.2:
            evidence = f"{featured.width}x{featured.height} (ratio={aspect_ratio:.2f})"
            return [
                ProofreadingIssue(
                    rule_id=self.rule_id,
                    category=self.category,
                    subcategory=self.subcategory,
                    message="特色图片必须为横向（宽高比 > 1.2）。",
                    suggestion="请裁剪或更换为宽高比大于 1.2 的横向图片。",
                    severity=self.severity,
                    confidence=1.0,
                    can_auto_fix=self.can_auto_fix,
                    blocks_publish=self.blocks_publish,
                    source=RuleSource.SCRIPT,
                    attributed_by="FeaturedImageLandscapeRule",
                    location={"resource": featured.id or featured.path},
                    evidence=evidence,
                )
            ]
        return []


# ============================================================================
# B类规则 - 标点符号与排版
# ============================================================================


class MissingPunctuationRule(DeterministicRule):
    """Detect sentences missing ending punctuation (B1-001)."""

    # 匹配句子末尾（中文字符后没有标点）
    SENTENCE_END_PATTERN = re.compile(r"[\u4e00-\u9fff](?=\n|$)", re.MULTILINE)

    def __init__(self) -> None:
        super().__init__(
            rule_id="B1-001",
            category="B",
            subcategory="B1",
            severity="warning",
            blocks_publish=False,
            can_auto_fix=True,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        for match in self.SENTENCE_END_PATTERN.finditer(content):
            # 检查前面是否已经有标点
            if match.start() > 0:
                prev_char = content[match.start() - 1]
                # 如果前一个字符是标点，跳过
                if prev_char in "。！？，、；：""''）】》":
                    continue

            snippet_start = max(0, match.start() - 15)
            snippet_end = min(len(content), match.end() + 5)
            snippet = content[snippet_start:snippet_end]

            issues.append(
                ProofreadingIssue(
                    rule_id=self.rule_id,
                    category=self.category,
                    subcategory=self.subcategory,
                    message="句末标点缺失：陈述句需要句号。",
                    suggestion="在句尾添加句号 '。'。",
                    severity=self.severity,
                    confidence=0.7,
                    can_auto_fix=self.can_auto_fix,
                    blocks_publish=self.blocks_publish,
                    source=RuleSource.SCRIPT,
                    attributed_by="MissingPunctuationRule",
                    location={"offset": match.start()},
                    evidence=snippet,
                )
            )
        return issues


class QuotationNestingRule(DeterministicRule):
    """Check quotation mark nesting: 「」 > 『』 (B3-002)."""

    # 检测不正确的嵌套：『』在外，「」在内
    INCORRECT_NESTING = re.compile(r"『[^』]*「[^」]*」[^』]*』")

    def __init__(self) -> None:
        super().__init__(
            rule_id="B3-002",
            category="B",
            subcategory="B3",
            severity="warning",
            blocks_publish=False,
            can_auto_fix=True,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        for match in self.INCORRECT_NESTING.finditer(content):
            snippet = match.group()

            issues.append(
                ProofreadingIssue(
                    rule_id=self.rule_id,
                    category=self.category,
                    subcategory=self.subcategory,
                    message="引号嵌套结构错误：应遵循 「」>『』 结构。",
                    suggestion="外层使用 「」，内层使用 『』。",
                    severity=self.severity,
                    confidence=0.9,
                    can_auto_fix=self.can_auto_fix,
                    blocks_publish=self.blocks_publish,
                    source=RuleSource.SCRIPT,
                    attributed_by="QuotationNestingRule",
                    location={"offset": match.start()},
                    evidence=snippet,
                )
            )
        return issues


class HalfWidthDashRule(DeterministicRule):
    """Detect half-width dashes in Chinese text (B7-004)."""

    # 检测中文中的半角短横线（排除数字范围、日期、URL）
    HALF_WIDTH_DASH_PATTERN = re.compile(
        r"(?<![a-zA-Z0-9/:])-(?![a-zA-Z0-9/:])"
    )

    def __init__(self) -> None:
        super().__init__(
            rule_id="B7-004",
            category="B",
            subcategory="B7",
            severity="warning",
            blocks_publish=False,
            can_auto_fix=True,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        for match in self.HALF_WIDTH_DASH_PATTERN.finditer(content):
            # 检查上下文是否是中文
            snippet_start = max(0, match.start() - 5)
            snippet_end = min(len(content), match.end() + 5)
            context = content[snippet_start:snippet_end]

            # 如果周围有中文字符，才报告问题
            if re.search(r"[\u4e00-\u9fff]", context):
                issues.append(
                    ProofreadingIssue(
                        rule_id=self.rule_id,
                        category=self.category,
                        subcategory=self.subcategory,
                        message="中文语句禁止使用半角短横线 '-'。",
                        suggestion="将半角 '-' 替换为全角破折号 '—'。",
                        severity=self.severity,
                        confidence=0.8,
                        can_auto_fix=self.can_auto_fix,
                        blocks_publish=self.blocks_publish,
                        source=RuleSource.SCRIPT,
                        attributed_by="HalfWidthDashRule",
                        location={"offset": match.start()},
                        evidence=context,
                    )
                )
        return issues


class EllipsisFormatRule(DeterministicRule):
    """Check ellipsis format: should use six dots (B1-002)."""

    # 匹配单个点或不规范的省略号
    IRREGULAR_ELLIPSIS = re.compile(r"\.{2}(?!\.)|\.{4}(?!\.)|\.{5}(?!\.)|\.{7,}")

    def __init__(self) -> None:
        super().__init__(
            rule_id="B1-002",
            category="B",
            subcategory="B1",
            severity="info",
            blocks_publish=False,
            can_auto_fix=True,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        for match in self.IRREGULAR_ELLIPSIS.finditer(content):
            original = match.group()
            dot_count = len(original)
            # 建议使用六点省略号
            corrected = "……"

            snippet_start = max(0, match.start() - 10)
            snippet_end = min(len(content), match.end() + 10)
            snippet = content[snippet_start:snippet_end]

            issues.append(
                ProofreadingIssue(
                    rule_id=self.rule_id,
                    category=self.category,
                    subcategory=self.subcategory,
                    message=f"省略号格式不规范：应使用六点省略号 '……' 而非 {dot_count} 个点。",
                    suggestion=f"将 '{original}' 改为 '{corrected}'。",
                    severity=self.severity,
                    confidence=0.9,
                    can_auto_fix=self.can_auto_fix,
                    blocks_publish=self.blocks_publish,
                    source=RuleSource.SCRIPT,
                    attributed_by="EllipsisFormatRule",
                    location={"offset": match.start()},
                    evidence=snippet,
                )
            )
        return issues


class QuestionMarkAbuseRule(DeterministicRule):
    """Detect multiple consecutive question marks (B1-003)."""

    MULTIPLE_QUESTION_MARKS = re.compile(r"\?{2,}")

    def __init__(self) -> None:
        super().__init__(
            rule_id="B1-003",
            category="B",
            subcategory="B1",
            severity="warning",
            blocks_publish=False,
            can_auto_fix=True,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        for match in self.MULTIPLE_QUESTION_MARKS.finditer(content):
            original = match.group()
            count = len(original)

            snippet_start = max(0, match.start() - 10)
            snippet_end = min(len(content), match.end() + 10)
            snippet = content[snippet_start:snippet_end]

            issues.append(
                ProofreadingIssue(
                    rule_id=self.rule_id,
                    category=self.category,
                    subcategory=self.subcategory,
                    message=f"问号滥用：连续使用 {count} 个问号，建议仅使用一个。",
                    suggestion="删除多余的问号，仅保留一个 '？'。",
                    severity=self.severity,
                    confidence=1.0,
                    can_auto_fix=self.can_auto_fix,
                    blocks_publish=self.blocks_publish,
                    source=RuleSource.SCRIPT,
                    attributed_by="QuestionMarkAbuseRule",
                    location={"offset": match.start()},
                    evidence=snippet,
                )
            )
        return issues


class ExclamationMarkAbuseRule(DeterministicRule):
    """Detect multiple consecutive exclamation marks (B1-004)."""

    MULTIPLE_EXCLAMATION_MARKS = re.compile(r"[!！]{2,}")

    def __init__(self) -> None:
        super().__init__(
            rule_id="B1-004",
            category="B",
            subcategory="B1",
            severity="warning",
            blocks_publish=False,
            can_auto_fix=True,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        for match in self.MULTIPLE_EXCLAMATION_MARKS.finditer(content):
            original = match.group()
            count = len(original)

            snippet_start = max(0, match.start() - 10)
            snippet_end = min(len(content), match.end() + 10)
            snippet = content[snippet_start:snippet_end]

            issues.append(
                ProofreadingIssue(
                    rule_id=self.rule_id,
                    category=self.category,
                    subcategory=self.subcategory,
                    message=f"感叹号滥用：连续使用 {count} 个感叹号，建议仅使用一个。",
                    suggestion="删除多余的感叹号，仅保留一个 '！'。",
                    severity=self.severity,
                    confidence=1.0,
                    can_auto_fix=self.can_auto_fix,
                    blocks_publish=self.blocks_publish,
                    source=RuleSource.SCRIPT,
                    attributed_by="ExclamationMarkAbuseRule",
                    location={"offset": match.start()},
                    evidence=snippet,
                )
            )
        return issues


class MixedPunctuationRule(DeterministicRule):
    """Detect mixed Chinese and English punctuation (B1-005)."""

    # 检测中文段落中使用英文标点的情况
    ENGLISH_PUNCT_IN_CHINESE = re.compile(r"[\u4e00-\u9fff][.!;:][\u4e00-\u9fff]")

    def __init__(self) -> None:
        super().__init__(
            rule_id="B1-005",
            category="B",
            subcategory="B1",
            severity="warning",
            blocks_publish=False,
            can_auto_fix=True,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        for match in self.ENGLISH_PUNCT_IN_CHINESE.finditer(content):
            snippet_start = max(0, match.start() - 10)
            snippet_end = min(len(content), match.end() + 10)
            snippet = content[snippet_start:snippet_end]

            # 提取英文标点符号
            original_text = match.group()
            if '.' in original_text:
                suggestion = "使用中文句号 '。'"
            elif '!' in original_text:
                suggestion = "使用中文感叹号 '！'"
            elif ';' in original_text:
                suggestion = "使用中文分号 '；'"
            elif ':' in original_text:
                suggestion = "使用中文冒号 '：'"
            else:
                suggestion = "使用对应的中文标点符号"

            issues.append(
                ProofreadingIssue(
                    rule_id=self.rule_id,
                    category=self.category,
                    subcategory=self.subcategory,
                    message="中文段落混用英文标点符号。",
                    suggestion=suggestion,
                    severity=self.severity,
                    confidence=0.8,
                    can_auto_fix=self.can_auto_fix,
                    blocks_publish=self.blocks_publish,
                    source=RuleSource.SCRIPT,
                    attributed_by="MixedPunctuationRule",
                    location={"offset": match.start()},
                    evidence=snippet,
                )
            )
        return issues


class QuotationMatchingRule(DeterministicRule):
    """Check quotation marks are properly matched (B3-001)."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="B3-001",
            category="B",
            subcategory="B3",
            severity="error",
            blocks_publish=False,
            can_auto_fix=False,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        # 检查引号配对：「」和『』
        left_main = content.count("「")
        right_main = content.count("」")
        left_inner = content.count("『")
        right_inner = content.count("」")

        if left_main != right_main:
            issues.append(
                ProofreadingIssue(
                    rule_id=self.rule_id,
                    category=self.category,
                    subcategory=self.subcategory,
                    message=f"引号「」不配对：左引号 {left_main} 个，右引号 {right_main} 个。",
                    suggestion="检查并补全缺失的引号。",
                    severity=self.severity,
                    confidence=1.0,
                    can_auto_fix=self.can_auto_fix,
                    blocks_publish=self.blocks_publish,
                    source=RuleSource.SCRIPT,
                    attributed_by="QuotationMatchingRule",
                    location={"offset": 0},
                    evidence=f"「={left_main}, 」={right_main}",
                )
            )

        if left_inner != right_inner:
            issues.append(
                ProofreadingIssue(
                    rule_id=self.rule_id,
                    category=self.category,
                    subcategory=self.subcategory,
                    message=f"引号『』不配对：左引号 {left_inner} 个，右引号 {right_inner} 个。",
                    suggestion="检查并补全缺失的引号。",
                    severity=self.severity,
                    confidence=1.0,
                    can_auto_fix=self.can_auto_fix,
                    blocks_publish=self.blocks_publish,
                    source=RuleSource.SCRIPT,
                    attributed_by="QuotationMatchingRule",
                    location={"offset": 0},
                    evidence=f"『={left_inner}, 』={right_inner}",
                )
            )

        return issues


class BookTitleMatchingRule(DeterministicRule):
    """Check book title marks are properly matched (B3-003)."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="B3-003",
            category="B",
            subcategory="B3",
            severity="error",
            blocks_publish=False,
            can_auto_fix=False,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        # 检查书名号配对：《》
        left_count = content.count("《")
        right_count = content.count("》")

        if left_count != right_count:
            issues.append(
                ProofreadingIssue(
                    rule_id=self.rule_id,
                    category=self.category,
                    subcategory=self.subcategory,
                    message=f"书名号《》不配对：左书名号 {left_count} 个，右书名号 {right_count} 个。",
                    suggestion="检查并补全缺失的书名号。",
                    severity=self.severity,
                    confidence=1.0,
                    can_auto_fix=self.can_auto_fix,
                    blocks_publish=self.blocks_publish,
                    source=RuleSource.SCRIPT,
                    attributed_by="BookTitleMatchingRule",
                    location={"offset": 0},
                    evidence=f"《={left_count}, 》={right_count}",
                )
            )

        return issues


# ============================================================================
# A类规则 - 用字与用词规范
# ============================================================================


class UnifiedTermMeterRule(DeterministicRule):
    """Enforce '表' for meters, except watches (A1-001)."""

    METER_PATTERN = re.compile(r"[電电]錶|水錶")
    WATCH_EXCLUSION = re.compile(r"手錶")

    def __init__(self) -> None:
        super().__init__(
            rule_id="A1-001",
            category="A",
            subcategory="A1",
            severity="warning",
            blocks_publish=False,
            can_auto_fix=True,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        for match in self.METER_PATTERN.finditer(content):
            # 排除手錶
            start = max(0, match.start() - 1)
            if self.WATCH_EXCLUSION.search(content[start : match.end()]):
                continue

            snippet_start = max(0, match.start() - 10)
            snippet_end = min(len(content), match.end() + 10)
            snippet = content[snippet_start:snippet_end]

            issues.append(
                ProofreadingIssue(
                    rule_id=self.rule_id,
                    category=self.category,
                    subcategory=self.subcategory,
                    message=f"统一用字：'{match.group()}' 应写作 '表'（手錶除外）。",
                    suggestion="将 '電錶/水錶' 替换为 '表'。",
                    severity=self.severity,
                    confidence=1.0,
                    can_auto_fix=self.can_auto_fix,
                    blocks_publish=self.blocks_publish,
                    source=RuleSource.SCRIPT,
                    attributed_by="UnifiedTermMeterRule",
                    location={"offset": match.start()},
                    evidence=snippet,
                )
            )
        return issues


class UnifiedTermOccupyRule(DeterministicRule):
    """Unify 佔/占 to 占 (A1-010)."""

    OCCUPY_PATTERN = re.compile(r"佔")

    def __init__(self) -> None:
        super().__init__(
            rule_id="A1-010",
            category="A",
            subcategory="A1",
            severity="warning",
            blocks_publish=False,
            can_auto_fix=True,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        for match in self.OCCUPY_PATTERN.finditer(content):
            snippet_start = max(0, match.start() - 10)
            snippet_end = min(len(content), match.end() + 10)
            snippet = content[snippet_start:snippet_end]

            issues.append(
                ProofreadingIssue(
                    rule_id=self.rule_id,
                    category=self.category,
                    subcategory=self.subcategory,
                    message="统一用字：'佔' 应统一为 '占'。",
                    suggestion="将 '佔' 替换为 '占'。",
                    severity=self.severity,
                    confidence=1.0,
                    can_auto_fix=self.can_auto_fix,
                    blocks_publish=self.blocks_publish,
                    source=RuleSource.SCRIPT,
                    attributed_by="UnifiedTermOccupyRule",
                    location={"offset": match.start()},
                    evidence=snippet,
                )
            )
        return issues


class CommonTypoRule(DeterministicRule):
    """Detect common typos like 莫明其妙 (A3-004)."""

    TYPO_PATTERN = re.compile(r"莫明其妙")

    def __init__(self) -> None:
        super().__init__(
            rule_id="A3-004",
            category="A",
            subcategory="A3",
            severity="warning",
            blocks_publish=False,
            can_auto_fix=True,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        for match in self.TYPO_PATTERN.finditer(content):
            snippet_start = max(0, match.start() - 10)
            snippet_end = min(len(content), match.end() + 10)
            snippet = content[snippet_start:snippet_end]

            issues.append(
                ProofreadingIssue(
                    rule_id=self.rule_id,
                    category=self.category,
                    subcategory=self.subcategory,
                    message="常见错字：应为 '莫名其妙'，不写 '莫明其妙'。",
                    suggestion="将 '莫明其妙' 替换为 '莫名其妙'。",
                    severity=self.severity,
                    confidence=1.0,
                    can_auto_fix=self.can_auto_fix,
                    blocks_publish=self.blocks_publish,
                    source=RuleSource.SCRIPT,
                    attributed_by="CommonTypoRule",
                    location={"offset": match.start()},
                    evidence=snippet,
                )
            )
        return issues


# ============================================================================
# A3类 - 常见错字规则（通用基类）
# ============================================================================


class TypoReplacementRule(DeterministicRule):
    """Generic typo replacement rule for A3 category."""

    def __init__(
        self,
        rule_id: str,
        wrong_pattern: str,
        correct_form: str,
        description: str,
    ) -> None:
        super().__init__(
            rule_id=rule_id,
            category="A",
            subcategory="A3",
            severity="error",
            blocks_publish=False,
            can_auto_fix=True,
        )
        self.wrong_pattern = re.compile(wrong_pattern)
        self.correct_form = correct_form
        self.description = description

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        for match in self.wrong_pattern.finditer(content):
            snippet_start = max(0, match.start() - 10)
            snippet_end = min(len(content), match.end() + 10)
            snippet = content[snippet_start:snippet_end]

            issues.append(
                ProofreadingIssue(
                    rule_id=self.rule_id,
                    category=self.category,
                    subcategory=self.subcategory,
                    message=f"常见错字：{self.description}",
                    suggestion=f"将 '{match.group()}' 替换为 '{self.correct_form}'。",
                    severity=self.severity,
                    confidence=1.0,
                    can_auto_fix=self.can_auto_fix,
                    blocks_publish=self.blocks_publish,
                    source=RuleSource.SCRIPT,
                    attributed_by=self.__class__.__name__,
                    location={"offset": match.start()},
                    evidence=snippet,
                )
            )
        return issues


class ZaiJieZaiLiTypoRule(TypoReplacementRule):
    """A3-005: 再接再励 → 再接再厉."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A3-005",
            wrong_pattern=r"再接再[励勵]",
            correct_form="再接再厉",
            description="应为 '再接再厉'，不写 '再接再励'",
        )


class AnBuJiuBanTypoRule(TypoReplacementRule):
    """A3-006: 按步就班 → 按部就班."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A3-006",
            wrong_pattern=r"按步就班",
            correct_form="按部就班",
            description="应为 '按部就班'，不写 '按步就班'",
        )


class YiRuJiWangTypoRule(TypoReplacementRule):
    """A3-007: 一如即往 → 一如既往."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A3-007",
            wrong_pattern=r"一如即往",
            correct_form="一如既往",
            description="应为 '一如既往'，不写 '一如即往'",
        )


class ShiWaiTaoYuanTypoRule(TypoReplacementRule):
    """A3-008: 世外桃园 → 世外桃源."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A3-008",
            wrong_pattern=r"世外桃[园園]",
            correct_form="世外桃源",
            description="应为 '世外桃源'，不写 '世外桃园'",
        )


class PoBuJiDaiTypoRule(TypoReplacementRule):
    """A3-009: 迫不急待 → 迫不及待."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A3-009",
            wrong_pattern=r"迫不[急]待",
            correct_form="迫不及待",
            description="应为 '迫不及待'，不写 '迫不急待'",
        )


class YinYeFeiShiTypoRule(TypoReplacementRule):
    """A3-010: 因咽废食 → 因噎废食."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A3-010",
            wrong_pattern=r"因[咽]废[食]",
            correct_form="因噎废食",
            description="应为 '因噎废食'，不写 '因咽废食'",
        )


class ChuanLiuBuXiTypoRule(TypoReplacementRule):
    """A3-011: 穿流不息 → 川流不息."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A3-011",
            wrong_pattern=r"[穿]流不息",
            correct_form="川流不息",
            description="应为 '川流不息'，不写 '穿流不息'",
        )


class KuaiZhiRenKouTypoRule(TypoReplacementRule):
    """A3-012: 烩炙人口 → 脍炙人口."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A3-012",
            wrong_pattern=r"[烩燴][炙]人口",
            correct_form="脍炙人口",
            description="应为 '脍炙人口'，不写 '烩炙人口'",
        )


class AnRanShiSeTypoRule(TypoReplacementRule):
    """A3-013: 暗然失色 → 黯然失色."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A3-013",
            wrong_pattern=r"[暗]然失色",
            correct_form="黯然失色",
            description="应为 '黯然失色'，不写 '暗然失色'",
        )


class PoFuChenZhouTypoRule(TypoReplacementRule):
    """A3-014: 破斧沉舟 → 破釜沉舟."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A3-014",
            wrong_pattern=r"破[斧]沉舟",
            correct_form="破釜沉舟",
            description="应为 '破釜沉舟'，不写 '破斧沉舟'",
        )


class InformalLanguageRule(DeterministicRule):
    """Detect informal or internet slang (A4-014)."""

    INFORMAL_TERMS = [
        "老公",
        "土豪",
        "颜值",
        "网红",
        "吃瓜",
        "打卡",
        "种草",
        "拔草",
        "佛系",
        "躺平",
    ]

    def __init__(self) -> None:
        super().__init__(
            rule_id="A4-014",
            category="A",
            subcategory="A4",
            severity="warning",
            blocks_publish=False,
            can_auto_fix=False,
        )
        # 构建正则模式
        pattern_str = "|".join(re.escape(term) for term in self.INFORMAL_TERMS)
        self.pattern = re.compile(pattern_str)

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        for match in self.pattern.finditer(content):
            snippet_start = max(0, match.start() - 10)
            snippet_end = min(len(content), match.end() + 10)
            snippet = content[snippet_start:snippet_end]

            issues.append(
                ProofreadingIssue(
                    rule_id=self.rule_id,
                    category=self.category,
                    subcategory=self.subcategory,
                    message=f"检测到网络流行语或粗俗用语：'{match.group()}'，建议使用正式表达。",
                    suggestion="请考虑使用更正式的表达方式。",
                    severity=self.severity,
                    confidence=0.8,
                    can_auto_fix=self.can_auto_fix,
                    blocks_publish=self.blocks_publish,
                    source=RuleSource.SCRIPT,
                    attributed_by="InformalLanguageRule",
                    location={"offset": match.start()},
                    evidence=snippet,
                )
            )
        return issues


# ============================================================================
# C类规则 - 数字与计量单位
# ============================================================================


class FullWidthDigitRule(DeterministicRule):
    """Detect full-width digits and require half-width (C1-006)."""

    FULL_WIDTH_DIGIT_PATTERN = re.compile(r"[０-９]+")

    def __init__(self) -> None:
        super().__init__(
            rule_id="C1-006",
            category="C",
            subcategory="C1",
            severity="warning",
            blocks_publish=False,
            can_auto_fix=True,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        for match in self.FULL_WIDTH_DIGIT_PATTERN.finditer(content):
            snippet_start = max(0, match.start() - 10)
            snippet_end = min(len(content), match.end() + 10)
            snippet = content[snippet_start:snippet_end]

            # 转换建议（全角→半角）
            full_width = match.group()
            half_width = "".join(
                chr(ord(c) - 0xFEE0) for c in full_width
            )

            issues.append(
                ProofreadingIssue(
                    rule_id=self.rule_id,
                    category=self.category,
                    subcategory=self.subcategory,
                    message=f"阿拉伯数字必须使用半角字符：'{full_width}' 应为 '{half_width}'。",
                    suggestion=f"将全角数字 '{full_width}' 替换为半角 '{half_width}'。",
                    severity=self.severity,
                    confidence=1.0,
                    can_auto_fix=self.can_auto_fix,
                    blocks_publish=self.blocks_publish,
                    source=RuleSource.SCRIPT,
                    attributed_by="FullWidthDigitRule",
                    location={"offset": match.start()},
                    evidence=snippet,
                )
            )
        return issues


class NumberSeparatorRule(DeterministicRule):
    """Suggest thousand separators for large numbers (C1-001)."""

    # 匹配4位及以上的数字（没有逗号分隔）
    LARGE_NUMBER_PATTERN = re.compile(r"\b\d{4,}\b")

    def __init__(self) -> None:
        super().__init__(
            rule_id="C1-001",
            category="C",
            subcategory="C1",
            severity="info",
            blocks_publish=False,
            can_auto_fix=True,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        for match in self.LARGE_NUMBER_PATTERN.finditer(content):
            number_str = match.group()
            # 跳过年份（4位数）
            if len(number_str) == 4:
                # 检查是否是年份（1000-2999范围）
                try:
                    num = int(number_str)
                    if 1000 <= num <= 2999:
                        continue
                except ValueError:
                    pass

            # 添加千位分隔符
            formatted = "{:,}".format(int(number_str))

            snippet_start = max(0, match.start() - 10)
            snippet_end = min(len(content), match.end() + 10)
            snippet = content[snippet_start:snippet_end]

            issues.append(
                ProofreadingIssue(
                    rule_id=self.rule_id,
                    category=self.category,
                    subcategory=self.subcategory,
                    message=f"统计数据建议使用千位分隔号：'{number_str}' 建议写为 '{formatted}'。",
                    suggestion=f"将 '{number_str}' 替换为 '{formatted}'。",
                    severity=self.severity,
                    confidence=0.6,
                    can_auto_fix=self.can_auto_fix,
                    blocks_publish=self.blocks_publish,
                    source=RuleSource.SCRIPT,
                    attributed_by="NumberSeparatorRule",
                    location={"offset": match.start()},
                    evidence=snippet,
                )
            )
        return issues


class PercentageFormatRule(DeterministicRule):
    """Check percentage format: require space before % (C1-002)."""

    # 匹配数字和%之间没有空格的情况
    NO_SPACE_PERCENTAGE = re.compile(r"\d+%")

    def __init__(self) -> None:
        super().__init__(
            rule_id="C1-002",
            category="C",
            subcategory="C1",
            severity="info",
            blocks_publish=False,
            can_auto_fix=True,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        for match in self.NO_SPACE_PERCENTAGE.finditer(content):
            original = match.group()
            corrected = original.replace("%", " %")

            snippet_start = max(0, match.start() - 10)
            snippet_end = min(len(content), match.end() + 10)
            snippet = content[snippet_start:snippet_end]

            issues.append(
                ProofreadingIssue(
                    rule_id=self.rule_id,
                    category=self.category,
                    subcategory=self.subcategory,
                    message=f"百分比格式：数字与 '%' 之间建议保留空格。",
                    suggestion=f"将 '{original}' 改为 '{corrected}'。",
                    severity=self.severity,
                    confidence=0.7,
                    can_auto_fix=self.can_auto_fix,
                    blocks_publish=self.blocks_publish,
                    source=RuleSource.SCRIPT,
                    attributed_by="PercentageFormatRule",
                    location={"offset": match.start()},
                    evidence=snippet,
                )
            )
        return issues


class DecimalPointRule(DeterministicRule):
    """Check decimal point format (C1-003)."""

    # 匹配使用中文句号作为小数点的情况
    CHINESE_DECIMAL = re.compile(r"\d+。\d+")

    def __init__(self) -> None:
        super().__init__(
            rule_id="C1-003",
            category="C",
            subcategory="C1",
            severity="error",
            blocks_publish=False,
            can_auto_fix=True,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        for match in self.CHINESE_DECIMAL.finditer(content):
            original = match.group()
            corrected = original.replace("。", ".")

            snippet_start = max(0, match.start() - 10)
            snippet_end = min(len(content), match.end() + 10)
            snippet = content[snippet_start:snippet_end]

            issues.append(
                ProofreadingIssue(
                    rule_id=self.rule_id,
                    category=self.category,
                    subcategory=self.subcategory,
                    message="小数点格式错误：应使用半角句点 '.' 而非中文句号 '。'。",
                    suggestion=f"将 '{original}' 改为 '{corrected}'。",
                    severity=self.severity,
                    confidence=1.0,
                    can_auto_fix=self.can_auto_fix,
                    blocks_publish=self.blocks_publish,
                    source=RuleSource.SCRIPT,
                    attributed_by="DecimalPointRule",
                    location={"offset": match.start()},
                    evidence=snippet,
                )
            )
        return issues


class DateFormatRule(DeterministicRule):
    """Check date format standardization (C1-004)."""

    # 匹配使用中文年月日的日期格式
    CHINESE_DATE = re.compile(r"\d{4}年\d{1,2}月\d{1,2}日")

    def __init__(self) -> None:
        super().__init__(
            rule_id="C1-004",
            category="C",
            subcategory="C1",
            severity="info",
            blocks_publish=False,
            can_auto_fix=True,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        for match in self.CHINESE_DATE.finditer(content):
            original = match.group()
            # 提取年月日并转换为 YYYY-MM-DD 格式
            import re
            parts = re.findall(r"\d+", original)
            if len(parts) == 3:
                year, month, day = parts
                corrected = f"{year}-{month.zfill(2)}-{day.zfill(2)}"

                snippet_start = max(0, match.start() - 10)
                snippet_end = min(len(content), match.end() + 10)
                snippet = content[snippet_start:snippet_end]

                issues.append(
                    ProofreadingIssue(
                        rule_id=self.rule_id,
                        category=self.category,
                        subcategory=self.subcategory,
                        message="日期格式：建议统一使用 YYYY-MM-DD 格式。",
                        suggestion=f"将 '{original}' 改为 '{corrected}'。",
                        severity=self.severity,
                        confidence=0.6,
                        can_auto_fix=self.can_auto_fix,
                        blocks_publish=self.blocks_publish,
                        source=RuleSource.SCRIPT,
                        attributed_by="DateFormatRule",
                        location={"offset": match.start()},
                        evidence=snippet,
                    )
                )
        return issues


class CurrencyFormatRule(DeterministicRule):
    """Check currency format (C1-005)."""

    # 匹配货币符号和数字之间有空格的情况
    SPACE_IN_CURRENCY = re.compile(r"([¥$€£]) +(\d+)")

    def __init__(self) -> None:
        super().__init__(
            rule_id="C1-005",
            category="C",
            subcategory="C1",
            severity="info",
            blocks_publish=False,
            can_auto_fix=True,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        for match in self.SPACE_IN_CURRENCY.finditer(content):
            symbol, number = match.groups()
            original = match.group()
            corrected = f"{symbol}{number}"

            snippet_start = max(0, match.start() - 10)
            snippet_end = min(len(content), match.end() + 10)
            snippet = content[snippet_start:snippet_end]

            issues.append(
                ProofreadingIssue(
                    rule_id=self.rule_id,
                    category=self.category,
                    subcategory=self.subcategory,
                    message="货币格式：货币符号与数字之间不应有空格。",
                    suggestion=f"将 '{original}' 改为 '{corrected}'。",
                    severity=self.severity,
                    confidence=0.9,
                    can_auto_fix=self.can_auto_fix,
                    blocks_publish=self.blocks_publish,
                    source=RuleSource.SCRIPT,
                    attributed_by="CurrencyFormatRule",
                    location={"offset": match.start()},
                    evidence=snippet,
                )
            )
        return issues


# ============================================================================
# C2类 - 计量单位规范
# ============================================================================


class KilometerUnificationRule(DeterministicRule):
    """Unify kilometer terminology: prefer '公里' over '千米' (C2-001)."""

    QIAN_MI_PATTERN = re.compile(r"千米")

    def __init__(self) -> None:
        super().__init__(
            rule_id="C2-001",
            category="C",
            subcategory="C2",
            severity="info",
            blocks_publish=False,
            can_auto_fix=True,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        for match in self.QIAN_MI_PATTERN.finditer(content):
            snippet_start = max(0, match.start() - 10)
            snippet_end = min(len(content), match.end() + 10)
            snippet = content[snippet_start:snippet_end]

            issues.append(
                ProofreadingIssue(
                    rule_id=self.rule_id,
                    category=self.category,
                    subcategory=self.subcategory,
                    message="统一用词：建议使用 '公里' 而非 '千米'。",
                    suggestion="将 '千米' 改为 '公里'。",
                    severity=self.severity,
                    confidence=0.8,
                    can_auto_fix=self.can_auto_fix,
                    blocks_publish=self.blocks_publish,
                    source=RuleSource.SCRIPT,
                    attributed_by="KilometerUnificationRule",
                    location={"offset": match.start()},
                    evidence=snippet,
                )
            )
        return issues


class SquareMeterSymbolRule(DeterministicRule):
    """Check square meter symbol format (C2-002)."""

    # 匹配使用文字"平方米"的情况
    TEXT_SQUARE_METER = re.compile(r"\d+ *平方米")

    def __init__(self) -> None:
        super().__init__(
            rule_id="C2-002",
            category="C",
            subcategory="C2",
            severity="info",
            blocks_publish=False,
            can_auto_fix=True,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        for match in self.TEXT_SQUARE_METER.finditer(content):
            original = match.group()
            # 提取数字部分
            number = re.search(r"\d+", original).group()
            corrected = f"{number} m²"

            snippet_start = max(0, match.start() - 10)
            snippet_end = min(len(content), match.end() + 10)
            snippet = content[snippet_start:snippet_end]

            issues.append(
                ProofreadingIssue(
                    rule_id=self.rule_id,
                    category=self.category,
                    subcategory=self.subcategory,
                    message="计量单位：建议使用符号 'm²' 表示平方米。",
                    suggestion=f"将 '{original}' 改为 '{corrected}'。",
                    severity=self.severity,
                    confidence=0.7,
                    can_auto_fix=self.can_auto_fix,
                    blocks_publish=self.blocks_publish,
                    source=RuleSource.SCRIPT,
                    attributed_by="SquareMeterSymbolRule",
                    location={"offset": match.start()},
                    evidence=snippet,
                )
            )
        return issues


# ============================================================================
# F类规则 - 发布合规（补充规则）
# ============================================================================


class ImageWidthRule(DeterministicRule):
    """Validate image width standards (F1-001)."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="F1-001",
            category="F",
            subcategory="F1",
            severity="error",
            blocks_publish=True,
            can_auto_fix=False,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []

        # 检查文章中的图片
        if not payload.images:
            return []

        for img in payload.images:
            if not img.width or not img.height:
                continue

            aspect_ratio = img.width / img.height
            is_landscape = aspect_ratio > 1.0

            expected_width = 600 if is_landscape else 450

            if img.width != expected_width:
                evidence = f"{img.width}x{img.height} (预期: {expected_width}px)"
                issues.append(
                    ProofreadingIssue(
                        rule_id=self.rule_id,
                        category=self.category,
                        subcategory=self.subcategory,
                        message=f"插图宽度不符合规范：{'横图' if is_landscape else '方/竖图'}应为 {expected_width}px。",
                        suggestion=f"调整图片宽度为 {expected_width}px。",
                        severity=self.severity,
                        confidence=1.0,
                        can_auto_fix=self.can_auto_fix,
                        blocks_publish=self.blocks_publish,
                        source=RuleSource.SCRIPT,
                        attributed_by="ImageWidthRule",
                        location={"resource": img.id or img.path},
                        evidence=evidence,
                    )
                )
        return issues


class ImageLicenseRule(DeterministicRule):
    """Check for image license attribution (F3-001)."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="F3-001",
            category="F",
            subcategory="F3",
            severity="critical",
            blocks_publish=True,
            can_auto_fix=False,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []

        # 检查文章中的图片是否有授权信息
        if not payload.images:
            return []

        for img in payload.images:
            # 检查是否有license或attribution字段
            has_license = bool(
                getattr(img, "license", None) or getattr(img, "attribution", None)
            )

            if not has_license:
                evidence = f"Image: {img.id or img.path}"
                issues.append(
                    ProofreadingIssue(
                        rule_id=self.rule_id,
                        category=self.category,
                        subcategory=self.subcategory,
                        message="图片缺少授权信息：仅允许使用具备明确授权的媒体素材。",
                        suggestion="添加图片来源和授权信息。",
                        severity=self.severity,
                        confidence=0.9,
                        can_auto_fix=self.can_auto_fix,
                        blocks_publish=self.blocks_publish,
                        source=RuleSource.SCRIPT,
                        attributed_by="ImageLicenseRule",
                        location={"resource": img.id or img.path},
                        evidence=evidence,
                    )
                )
        return issues


# ============================================================================
# 规则引擎
# ============================================================================


class DeterministicRuleEngine:
    """Coordinator for all deterministic proofreading rules."""

    VERSION = "0.5.0"  # Phase 1 MVP+：35条规则 (新增21条规则)

    def __init__(self) -> None:
        self.rules: List[DeterministicRule] = [
            # B类 - 标点符号与排版（10条）
            HalfWidthCommaRule(),  # B2-002
            MissingPunctuationRule(),  # B1-001
            EllipsisFormatRule(),  # B1-002: 省略号格式
            QuestionMarkAbuseRule(),  # B1-003: 问号滥用
            ExclamationMarkAbuseRule(),  # B1-004: 感叹号滥用
            MixedPunctuationRule(),  # B1-005: 中英文标点混用
            QuotationMatchingRule(),  # B3-001: 引号配对
            QuotationNestingRule(),  # B3-002
            BookTitleMatchingRule(),  # B3-003: 书名号配对
            HalfWidthDashRule(),  # B7-004
            # A类 - 用字规范（13条）
            UnifiedTermMeterRule(),  # A1-001
            UnifiedTermOccupyRule(),  # A1-010
            CommonTypoRule(),  # A3-004
            ZaiJieZaiLiTypoRule(),  # A3-005: 再接再厉
            AnBuJiuBanTypoRule(),  # A3-006: 按部就班
            YiRuJiWangTypoRule(),  # A3-007: 一如既往
            ShiWaiTaoYuanTypoRule(),  # A3-008: 世外桃源
            PoBuJiDaiTypoRule(),  # A3-009: 迫不及待
            YinYeFeiShiTypoRule(),  # A3-010: 因噎废食
            ChuanLiuBuXiTypoRule(),  # A3-011: 川流不息
            KuaiZhiRenKouTypoRule(),  # A3-012: 脍炙人口
            AnRanShiSeTypoRule(),  # A3-013: 黯然失色
            PoFuChenZhouTypoRule(),  # A3-014: 破釜沉舟
            InformalLanguageRule(),  # A4-014
            # C类 - 数字与计量（8条）
            FullWidthDigitRule(),  # C1-006
            NumberSeparatorRule(),  # C1-001
            PercentageFormatRule(),  # C1-002: 百分比格式
            DecimalPointRule(),  # C1-003: 小数点格式
            DateFormatRule(),  # C1-004: 日期格式
            CurrencyFormatRule(),  # C1-005: 货币格式
            KilometerUnificationRule(),  # C2-001: 公里/千米统一
            SquareMeterSymbolRule(),  # C2-002: 平方米符号
            # F类 - 发布合规（4条）
            InvalidHeadingLevelRule(),  # F2-001
            FeaturedImageLandscapeRule(),  # F1-002
            ImageWidthRule(),  # F1-001
            ImageLicenseRule(),  # F3-001
        ]

    def run(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        """Execute all deterministic rules."""
        issues: List[ProofreadingIssue] = []
        for rule in self.rules:
            issues.extend(rule.evaluate(payload))
        return issues

