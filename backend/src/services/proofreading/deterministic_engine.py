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


# B Class - Additional Punctuation Rules (15 new rules)

# B1 Subclass - Basic Punctuation (5 rules: B1-006 to B1-010)
class B1_006_ColonFormatRule(DeterministicRule):
    """Check colon format (B1-006)."""

    # 冒号后缺少空格（在列表或说明时）
    COLON_NO_SPACE = re.compile(r"[:：](?=[^\s\n])")
    # 半角冒号在中文中
    HALFWIDTH_COLON = re.compile(r"[：]")

    def __init__(self) -> None:
        super().__init__(
            rule_id="B1-006",
            category="B",
            subcategory="B1",
            severity="info",
            blocks_publish=False,
            can_auto_fix=True,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        # Check for halfwidth colon in Chinese text
        for match in re.finditer(r":", content):
            # 检查前后是否有中文
            start = max(0, match.start() - 1)
            end = min(len(content), match.end() + 1)
            context = content[start:end]

            if re.search(r'[\u4e00-\u9fff]', context):
                snippet_start = max(0, match.start() - 10)
                snippet_end = min(len(content), match.end() + 10)
                snippet = content[snippet_start:snippet_end]

                issues.append(
                    ProofreadingIssue(
                        rule_id=self.rule_id,
                        category=self.category,
                        subcategory=self.subcategory,
                        message="冒号格式：中文语境应使用全角冒号「：」。",
                        suggestion="将 ':' 改为 '：'。",
                        severity=self.severity,
                        confidence=0.8,
                        can_auto_fix=self.can_auto_fix,
                        blocks_publish=self.blocks_publish,
                        source=RuleSource.SCRIPT,
                        attributed_by="B1_006_ColonFormatRule",
                        location={"offset": match.start()},
                        evidence=snippet,
                    )
                )
        return issues


class B1_007_SemicolonFormatRule(DeterministicRule):
    """Check semicolon format (B1-007)."""

    # 半角分号在中文中
    HALFWIDTH_SEMICOLON = re.compile(r";")

    def __init__(self) -> None:
        super().__init__(
            rule_id="B1-007",
            category="B",
            subcategory="B1",
            severity="info",
            blocks_publish=False,
            can_auto_fix=True,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        for match in self.HALFWIDTH_SEMICOLON.finditer(content):
            # 检查前后是否有中文
            start = max(0, match.start() - 1)
            end = min(len(content), match.end() + 1)
            context = content[start:end]

            if re.search(r'[\u4e00-\u9fff]', context):
                snippet_start = max(0, match.start() - 10)
                snippet_end = min(len(content), match.end() + 10)
                snippet = content[snippet_start:snippet_end]

                issues.append(
                    ProofreadingIssue(
                        rule_id=self.rule_id,
                        category=self.category,
                        subcategory=self.subcategory,
                        message="分号格式：中文语境应使用全角分号「；」。",
                        suggestion="将 ';' 改为 '；'。",
                        severity=self.severity,
                        confidence=0.8,
                        can_auto_fix=self.can_auto_fix,
                        blocks_publish=self.blocks_publish,
                        source=RuleSource.SCRIPT,
                        attributed_by="B1_007_SemicolonFormatRule",
                        location={"offset": match.start()},
                        evidence=snippet,
                    )
                )
        return issues


class B1_008_ConsecutivePunctuationRule(DeterministicRule):
    """Check consecutive punctuation (B1-008)."""

    # 连续标点符号（如：。。、！！等）
    CONSECUTIVE_PUNCT = re.compile(r"([。！？；：，、])\1+")

    def __init__(self) -> None:
        super().__init__(
            rule_id="B1-008",
            category="B",
            subcategory="B1",
            severity="warning",
            blocks_publish=False,
            can_auto_fix=True,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        for match in self.CONSECUTIVE_PUNCT.finditer(content):
            # 排除省略号……
            if match.group() == "……":
                continue

            snippet_start = max(0, match.start() - 10)
            snippet_end = min(len(content), match.end() + 10)
            snippet = content[snippet_start:snippet_end]

            issues.append(
                ProofreadingIssue(
                    rule_id=self.rule_id,
                    category=self.category,
                    subcategory=self.subcategory,
                    message=f"连续标点：不应连续使用相同标点符号 '{match.group()}'。",
                    suggestion=f"删除多余的 '{match.group(0)[0]}'。",
                    severity=self.severity,
                    confidence=0.9,
                    can_auto_fix=self.can_auto_fix,
                    blocks_publish=self.blocks_publish,
                    source=RuleSource.SCRIPT,
                    attributed_by="B1_008_ConsecutivePunctuationRule",
                    location={"offset": match.start()},
                    evidence=snippet,
                )
            )
        return issues


class B1_009_PunctuationSpacingRule(DeterministicRule):
    """Check punctuation spacing (B1-009)."""

    # 中文标点后有多余空格
    PUNCT_EXTRA_SPACE = re.compile(r"([。！？；：，、]) +")

    def __init__(self) -> None:
        super().__init__(
            rule_id="B1-009",
            category="B",
            subcategory="B1",
            severity="info",
            blocks_publish=False,
            can_auto_fix=True,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        for match in self.PUNCT_EXTRA_SPACE.finditer(content):
            snippet_start = max(0, match.start() - 10)
            snippet_end = min(len(content), match.end() + 10)
            snippet = content[snippet_start:snippet_end]

            issues.append(
                ProofreadingIssue(
                    rule_id=self.rule_id,
                    category=self.category,
                    subcategory=self.subcategory,
                    message="标点后空格：中文标点符号后不应有空格。",
                    suggestion=f"删除 '{match.group(1)}' 后的空格。",
                    severity=self.severity,
                    confidence=0.9,
                    can_auto_fix=self.can_auto_fix,
                    blocks_publish=self.blocks_publish,
                    source=RuleSource.SCRIPT,
                    attributed_by="B1_009_PunctuationSpacingRule",
                    location={"offset": match.start()},
                    evidence=snippet,
                )
            )
        return issues


class B1_010_ChinesePeriodRule(DeterministicRule):
    """Check Chinese period format (B1-010)."""

    # 英文句号在中文语境
    ENGLISH_PERIOD = re.compile(r"\.")

    def __init__(self) -> None:
        super().__init__(
            rule_id="B1-010",
            category="B",
            subcategory="B1",
            severity="info",
            blocks_publish=False,
            can_auto_fix=True,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        for match in self.ENGLISH_PERIOD.finditer(content):
            # 检查是否在句末，且前后是中文
            start = max(0, match.start() - 5)
            end = min(len(content), match.end() + 2)
            context = content[start:end]

            # 排除小数点、网址、文件名等
            if re.search(r'\d\.\d|www\.|\.com|\.png|\.jpg|\.pdf', context):
                continue

            # 检查前面是否有中文，后面是否是换行或空白
            before = content[max(0, match.start() - 1):match.start()]
            after = content[match.end():min(len(content), match.end() + 1)]

            if re.search(r'[\u4e00-\u9fff]', before) and (not after or after in '\n\r ' or re.search(r'[\u4e00-\u9fff]', after)):
                snippet_start = max(0, match.start() - 10)
                snippet_end = min(len(content), match.end() + 10)
                snippet = content[snippet_start:snippet_end]

                issues.append(
                    ProofreadingIssue(
                        rule_id=self.rule_id,
                        category=self.category,
                        subcategory=self.subcategory,
                        message="句号格式：中文句子应使用全角句号「。」。",
                        suggestion="将 '.' 改为 '。'。",
                        severity=self.severity,
                        confidence=0.7,
                        can_auto_fix=self.can_auto_fix,
                        blocks_publish=self.blocks_publish,
                        source=RuleSource.SCRIPT,
                        attributed_by="B1_010_ChinesePeriodRule",
                        location={"offset": match.start()},
                        evidence=snippet,
                    )
                )
        return issues


# B2 Subclass - Comma and Enumeration (3 rules: B2-003 to B2-005)
class B2_003_DunhaoUsageRule(DeterministicRule):
    """Check dunhao (、) usage (B2-003)."""

    # 检查在应该用顿号的地方用了逗号
    COMMA_FOR_DUNHAO = re.compile(r"[\u4e00-\u9fff]，[\u4e00-\u9fff]，[\u4e00-\u9fff]")

    def __init__(self) -> None:
        super().__init__(
            rule_id="B2-003",
            category="B",
            subcategory="B2",
            severity="info",
            blocks_publish=False,
            can_auto_fix=False,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        for match in self.COMMA_FOR_DUNHAO.finditer(content):
            # 检查是否是简单并列词汇
            text = match.group()
            # 如果每个分句都很短（<5字），可能应该用顿号
            parts = text.split('，')
            if all(len(p) <= 5 for p in parts):
                snippet_start = max(0, match.start() - 10)
                snippet_end = min(len(content), match.end() + 10)
                snippet = content[snippet_start:snippet_end]

                issues.append(
                    ProofreadingIssue(
                        rule_id=self.rule_id,
                        category=self.category,
                        subcategory=self.subcategory,
                        message="顿号使用：短词并列时建议使用顿号「、」而非逗号。",
                        suggestion="考虑将短词并列的逗号改为顿号。",
                        severity=self.severity,
                        confidence=0.6,
                        can_auto_fix=self.can_auto_fix,
                        blocks_publish=self.blocks_publish,
                        source=RuleSource.SCRIPT,
                        attributed_by="B2_003_DunhaoUsageRule",
                        location={"offset": match.start()},
                        evidence=snippet,
                    )
                )
        return issues


class B2_004_CommaAbuseRule(DeterministicRule):
    """Check comma abuse (B2-004)."""

    # 连续多个逗号
    CONSECUTIVE_COMMAS = re.compile(r"(，[\u4e00-\u9fff]{1,20}){4,}")

    def __init__(self) -> None:
        super().__init__(
            rule_id="B2-004",
            category="B",
            subcategory="B2",
            severity="info",
            blocks_publish=False,
            can_auto_fix=False,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        for match in self.CONSECUTIVE_COMMAS.finditer(content):
            snippet_start = max(0, match.start() - 10)
            snippet_end = min(len(content), match.end() + 10)
            snippet = content[snippet_start:snippet_end]

            issues.append(
                ProofreadingIssue(
                    rule_id=self.rule_id,
                    category=self.category,
                    subcategory=self.subcategory,
                    message="逗号滥用：连续多个短分句建议使用句号或分号。",
                    suggestion="考虑将部分逗号改为句号或分号，拆分长句。",
                    severity=self.severity,
                    confidence=0.7,
                    can_auto_fix=self.can_auto_fix,
                    blocks_publish=self.blocks_publish,
                    source=RuleSource.SCRIPT,
                    attributed_by="B2_004_CommaAbuseRule",
                    location={"offset": match.start()},
                    evidence=snippet,
                )
            )
        return issues


class B2_005_SerialCommaRule(DeterministicRule):
    """Check serial comma (Oxford comma) (B2-005)."""

    # 检查 A、B 和 C 的格式
    SERIAL_PATTERN = re.compile(r"、[^、]{1,10}和[^。！？，；]{1,10}[。！？，；]")

    def __init__(self) -> None:
        super().__init__(
            rule_id="B2-005",
            category="B",
            subcategory="B2",
            severity="info",
            blocks_publish=False,
            can_auto_fix=False,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        for match in self.SERIAL_PATTERN.finditer(content):
            # 检查"和"前是否缺少顿号
            text = match.group()
            if '、' not in text[text.index('和'):]:
                snippet_start = max(0, match.start() - 10)
                snippet_end = min(len(content), match.end() + 10)
                snippet = content[snippet_start:snippet_end]

                issues.append(
                    ProofreadingIssue(
                        rule_id=self.rule_id,
                        category=self.category,
                        subcategory=self.subcategory,
                        message="序列标点：「和」前的最后一项可考虑添加顿号以保持一致性。",
                        suggestion="在「和」前添加顿号，如：A、B、和C。",
                        severity=self.severity,
                        confidence=0.5,
                        can_auto_fix=self.can_auto_fix,
                        blocks_publish=self.blocks_publish,
                        source=RuleSource.SCRIPT,
                        attributed_by="B2_005_SerialCommaRule",
                        location={"offset": match.start()},
                        evidence=snippet,
                    )
                )
        return issues


# B4-B7 Subclass - Other Punctuation (7 rules)
class B4_001_ParenthesesMatchingRule(DeterministicRule):
    """Check parentheses matching (B4-001)."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="B4-001",
            category="B",
            subcategory="B4",
            severity="error",
            blocks_publish=False,
            can_auto_fix=False,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        # 检查各种括号配对
        brackets = [
            ('（', '）', '圆括号'),
            ('(', ')', '半角圆括号'),
            ('【', '】', '方括号'),
            ('[', ']', '半角方括号'),
            ('〔', '〕', '方头括号'),
        ]

        for left, right, name in brackets:
            left_count = content.count(left)
            right_count = content.count(right)

            if left_count != right_count:
                issues.append(
                    ProofreadingIssue(
                        rule_id=self.rule_id,
                        category=self.category,
                        subcategory=self.subcategory,
                        message=f"{name}不配对：左{name} {left_count} 个，右{name} {right_count} 个。",
                        suggestion=f"检查并补全缺失的{name}。",
                        severity=self.severity,
                        confidence=1.0,
                        can_auto_fix=self.can_auto_fix,
                        blocks_publish=self.blocks_publish,
                        source=RuleSource.SCRIPT,
                        attributed_by="B4_001_ParenthesesMatchingRule",
                        location={"offset": 0},
                        evidence=f"{left}={left_count}, {right}={right_count}",
                    )
                )
        return issues


class B4_002_ParenthesesFormatRule(DeterministicRule):
    """Check parentheses format (B4-002)."""

    # 半角括号在中文中
    HALFWIDTH_PAREN = re.compile(r"[(\)]")

    def __init__(self) -> None:
        super().__init__(
            rule_id="B4-002",
            category="B",
            subcategory="B4",
            severity="info",
            blocks_publish=False,
            can_auto_fix=True,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        for match in self.HALFWIDTH_PAREN.finditer(content):
            # 检查前后是否有中文
            start = max(0, match.start() - 1)
            end = min(len(content), match.end() + 1)
            context = content[start:end]

            if re.search(r'[\u4e00-\u9fff]', context):
                snippet_start = max(0, match.start() - 10)
                snippet_end = min(len(content), match.end() + 10)
                snippet = content[snippet_start:snippet_end]

                suggestion = "'(' → '（'" if match.group() == '(' else "')' → '）'"
                issues.append(
                    ProofreadingIssue(
                        rule_id=self.rule_id,
                        category=self.category,
                        subcategory=self.subcategory,
                        message="括号格式：中文语境应使用全角括号「（）」。",
                        suggestion=suggestion,
                        severity=self.severity,
                        confidence=0.8,
                        can_auto_fix=self.can_auto_fix,
                        blocks_publish=self.blocks_publish,
                        source=RuleSource.SCRIPT,
                        attributed_by="B4_002_ParenthesesFormatRule",
                        location={"offset": match.start()},
                        evidence=snippet,
                    )
                )
        return issues


class B5_001_DoubleQuoteMisuseRule(DeterministicRule):
    """Check double quote misuse (B5-001)."""

    # 英文双引号在中文中
    ENGLISH_DOUBLE_QUOTE = re.compile(r'"')

    def __init__(self) -> None:
        super().__init__(
            rule_id="B5-001",
            category="B",
            subcategory="B5",
            severity="info",
            blocks_publish=False,
            can_auto_fix=True,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        for match in self.ENGLISH_DOUBLE_QUOTE.finditer(content):
            # 检查前后是否有中文
            start = max(0, match.start() - 1)
            end = min(len(content), match.end() + 1)
            context = content[start:end]

            if re.search(r'[\u4e00-\u9fff]', context):
                snippet_start = max(0, match.start() - 10)
                snippet_end = min(len(content), match.end() + 10)
                snippet = content[snippet_start:snippet_end]

                issues.append(
                    ProofreadingIssue(
                        rule_id=self.rule_id,
                        category=self.category,
                        subcategory=self.subcategory,
                        message="引号格式：中文语境应使用中文引号「」或『』。",
                        suggestion='将 " 改为 「」 或 『』。',
                        severity=self.severity,
                        confidence=0.8,
                        can_auto_fix=self.can_auto_fix,
                        blocks_publish=self.blocks_publish,
                        source=RuleSource.SCRIPT,
                        attributed_by="B5_001_DoubleQuoteMisuseRule",
                        location={"offset": match.start()},
                        evidence=snippet,
                    )
                )
        return issues


class B5_002_SingleQuoteMisuseRule(DeterministicRule):
    """Check single quote misuse (B5-002)."""

    # 英文单引号在中文中
    ENGLISH_SINGLE_QUOTE = re.compile(r"'")

    def __init__(self) -> None:
        super().__init__(
            rule_id="B5-002",
            category="B",
            subcategory="B5",
            severity="info",
            blocks_publish=False,
            can_auto_fix=True,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        for match in self.ENGLISH_SINGLE_QUOTE.finditer(content):
            # 检查前后是否有中文
            start = max(0, match.start() - 1)
            end = min(len(content), match.end() + 1)
            context = content[start:end]

            if re.search(r'[\u4e00-\u9fff]', context):
                snippet_start = max(0, match.start() - 10)
                snippet_end = min(len(content), match.end() + 10)
                snippet = content[snippet_start:snippet_end]

                issues.append(
                    ProofreadingIssue(
                        rule_id=self.rule_id,
                        category=self.category,
                        subcategory=self.subcategory,
                        message="引号格式：中文语境应使用中文引号『』。",
                        suggestion="将 ' 改为 『』。",
                        severity=self.severity,
                        confidence=0.7,
                        can_auto_fix=self.can_auto_fix,
                        blocks_publish=self.blocks_publish,
                        source=RuleSource.SCRIPT,
                        attributed_by="B5_002_SingleQuoteMisuseRule",
                        location={"offset": match.start()},
                        evidence=snippet,
                    )
                )
        return issues


class B6_001_EmphasisMarkRule(DeterministicRule):
    """Check emphasis mark format (B6-001)."""

    # 检查着重号使用（通常用·表示）
    EMPHASIS_PATTERN = re.compile(r"[\u4e00-\u9fff]+·[\u4e00-\u9fff]+")

    def __init__(self) -> None:
        super().__init__(
            rule_id="B6-001",
            category="B",
            subcategory="B6",
            severity="info",
            blocks_publish=False,
            can_auto_fix=False,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        for match in self.EMPHASIS_PATTERN.finditer(content):
            # 这可能是间隔号，检查是否应该用其他方式表示
            snippet_start = max(0, match.start() - 10)
            snippet_end = min(len(content), match.end() + 10)
            snippet = content[snippet_start:snippet_end]

            issues.append(
                ProofreadingIssue(
                    rule_id=self.rule_id,
                    category=self.category,
                    subcategory=self.subcategory,
                    message="间隔号使用：请确认是否需要使用间隔号「·」。",
                    suggestion="如用于强调，建议使用引号或其他方式。",
                    severity=self.severity,
                    confidence=0.5,
                    can_auto_fix=self.can_auto_fix,
                    blocks_publish=self.blocks_publish,
                    source=RuleSource.SCRIPT,
                    attributed_by="B6_001_EmphasisMarkRule",
                    location={"offset": match.start()},
                    evidence=snippet,
                )
            )
        return issues


class B7_001_DashFormatRule(DeterministicRule):
    """Check dash format (B7-001)."""

    # 单个破折号（应该用双破折号）
    SINGLE_DASH = re.compile(r"(?<![—])—(?![—])")

    def __init__(self) -> None:
        super().__init__(
            rule_id="B7-001",
            category="B",
            subcategory="B7",
            severity="info",
            blocks_publish=False,
            can_auto_fix=True,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        for match in self.SINGLE_DASH.finditer(content):
            snippet_start = max(0, match.start() - 10)
            snippet_end = min(len(content), match.end() + 10)
            snippet = content[snippet_start:snippet_end]

            issues.append(
                ProofreadingIssue(
                    rule_id=self.rule_id,
                    category=self.category,
                    subcategory=self.subcategory,
                    message="破折号格式：破折号应成对使用「——」。",
                    suggestion="将单个 '—' 改为 '——'。",
                    severity=self.severity,
                    confidence=0.8,
                    can_auto_fix=self.can_auto_fix,
                    blocks_publish=self.blocks_publish,
                    source=RuleSource.SCRIPT,
                    attributed_by="B7_001_DashFormatRule",
                    location={"offset": match.start()},
                    evidence=snippet,
                )
            )
        return issues


class B7_002_HyphenFormatRule(DeterministicRule):
    """Check hyphen format (B7-002)."""

    # 连字符/连接号检查
    HYPHEN_PATTERN = re.compile(r"[\u4e00-\u9fff]-[\u4e00-\u9fff]")

    def __init__(self) -> None:
        super().__init__(
            rule_id="B7-002",
            category="B",
            subcategory="B7",
            severity="info",
            blocks_publish=False,
            can_auto_fix=False,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        for match in self.HYPHEN_PATTERN.finditer(content):
            snippet_start = max(0, match.start() - 10)
            snippet_end = min(len(content), match.end() + 10)
            snippet = content[snippet_start:snippet_end]

            issues.append(
                ProofreadingIssue(
                    rule_id=self.rule_id,
                    category=self.category,
                    subcategory=self.subcategory,
                    message="连接号使用：中文间的连接建议使用「～」或「-」。",
                    suggestion="确认是否应使用波浪号「～」或全角连字符「－」。",
                    severity=self.severity,
                    confidence=0.6,
                    can_auto_fix=self.can_auto_fix,
                    blocks_publish=self.blocks_publish,
                    source=RuleSource.SCRIPT,
                    attributed_by="B7_002_HyphenFormatRule",
                    location={"offset": match.start()},
                    evidence=snippet,
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


# ============================================================================
# A1类 - 统一用字规则（通用基类）
# ============================================================================


class UnifiedTermRule(DeterministicRule):
    """Generic unified term rule for A1 category."""

    def __init__(
        self,
        rule_id: str,
        wrong_pattern: str,
        correct_form: str,
        description: str,
        exclusion_pattern: str | None = None,
    ) -> None:
        super().__init__(
            rule_id=rule_id,
            category="A",
            subcategory="A1",
            severity="warning",
            blocks_publish=False,
            can_auto_fix=True,
        )
        self.wrong_pattern = re.compile(wrong_pattern)
        self.correct_form = correct_form
        self.description = description
        self.exclusion_pattern = (
            re.compile(exclusion_pattern) if exclusion_pattern else None
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        for match in self.wrong_pattern.finditer(content):
            # Check exclusion pattern if exists
            if self.exclusion_pattern:
                context_start = max(0, match.start() - 2)
                context_end = min(len(content), match.end() + 2)
                context = content[context_start:context_end]
                if self.exclusion_pattern.search(context):
                    continue

            snippet_start = max(0, match.start() - 10)
            snippet_end = min(len(content), match.end() + 10)
            snippet = content[snippet_start:snippet_end]

            issues.append(
                ProofreadingIssue(
                    rule_id=self.rule_id,
                    category=self.category,
                    subcategory=self.subcategory,
                    message=f"统一用字：{self.description}",
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


# A1 Class Rules (Unified Terms) - 20 new rules
class A1_002_LiInsideRule(UnifiedTermRule):
    """裡/裏 统一为 里（表示inside）."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A1-002",
            wrong_pattern=r"[裡裏]",
            correct_form="里",
            description="'裡/裏' 应统一为 '里'（表示「里面」时）。",
            exclusion_pattern=r"公[裡裏]|千[裡裏]|英[裡裏]",  # Exclude distance usage
        )


class A1_003_MeQuestionRule(UnifiedTermRule):
    """麽/么 统一为 么."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A1-003",
            wrong_pattern=r"麽",
            correct_form="么",
            description="'麽' 应统一为 '么'（什么、怎么等）。",
        )


class A1_004_EmployRule(UnifiedTermRule):
    """僱 统一为 雇."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A1-004",
            wrong_pattern=r"僱",
            correct_form="雇",
            description="'僱' 应统一为 '雇'（雇佣、雇员等）。",
        )


class A1_005_AndAlsoRule(UnifiedTermRule):
    """並 统一为 并."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A1-005",
            wrong_pattern=r"並",
            correct_form="并",
            description="'並' 应统一为 '并'（并且、并列等）。",
        )


class A1_006_ReturnRule(UnifiedTermRule):
    """迴 统一为 回."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A1-006",
            wrong_pattern=r"迴",
            correct_form="回",
            description="'迴' 应统一为 '回'（回转、回避等）。",
        )


class A1_007_SecretRule(UnifiedTermRule):
    """祕 统一为 秘."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A1-007",
            wrong_pattern=r"祕",
            correct_form="秘",
            description="'祕' 应统一为 '秘'（秘密、秘书等）。",
        )


class A1_008_LineRule(UnifiedTermRule):
    """綫 统一为 线."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A1-008",
            wrong_pattern=r"綫",
            correct_form="线",
            description="'綫' 应统一为 '线'（线路、电线等）。",
        )


class A1_009_OnlyRule(UnifiedTermRule):
    """衹 统一为 只."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A1-009",
            wrong_pattern=r"衹",
            correct_form="只",
            description="'衹' 应统一为 '只'（只是、只有等）。",
        )


class A1_011_ExhaustRule(UnifiedTermRule):
    """儘 统一为 尽."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A1-011",
            wrong_pattern=r"儘",
            correct_form="尽",
            description="'儘' 应统一为 '尽'（尽管、尽力等）。",
        )


class A1_012_PrepareRule(UnifiedTermRule):
    """準 统一为 准."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A1-012",
            wrong_pattern=r"準",
            correct_form="准",
            description="'準' 应统一为 '准'（准备、标准等）。",
        )


class A1_013_CrowdRule(UnifiedTermRule):
    """衆 统一为 众."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A1-013",
            wrong_pattern=r"衆",
            correct_form="众",
            description="'衆' 应统一为 '众'（众人、群众等）。",
        )


class A1_014_GroupRule(UnifiedTermRule):
    """羣 统一为 群."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A1-014",
            wrong_pattern=r"羣",
            correct_form="群",
            description="'羣' 应统一为 '群'（群体、群众等）。",
        )


class A1_015_ForAsRule(UnifiedTermRule):
    """爲 统一为 为."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A1-015",
            wrong_pattern=r"爲",
            correct_form="为",
            description="'爲' 应统一为 '为'（因为、作为等）。",
        )


class A1_016_AtInRule(UnifiedTermRule):
    """於 统一为 于."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A1-016",
            wrong_pattern=r"於",
            correct_form="于",
            description="'於' 应统一为 '于'（在于、对于等）。",
        )


class A1_017_CleanRule(UnifiedTermRule):
    """淨 统一为 净."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A1-017",
            wrong_pattern=r"淨",
            correct_form="净",
            description="'淨' 应统一为 '净'（干净、净化等）。",
        )


class A1_018_JustNowRule(UnifiedTermRule):
    """纔 统一为 才."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A1-018",
            wrong_pattern=r"纔",
            correct_form="才",
            description="'纔' 应统一为 '才'（刚才、才能等）。",
        )


class A1_019_ThroughRule(UnifiedTermRule):
    """籍 统一为 藉 (表示through)."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A1-019",
            wrong_pattern=r"籍(?=由|着|此|以)",  # Only when followed by 由/着/此/以
            correct_form="藉",
            description="'籍' 应统一为 '藉'（藉由、凭藉等，表示「通过」时）。",
        )


class A1_020_TwoRule(UnifiedTermRule):
    """兩 统一为 两."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A1-020",
            wrong_pattern=r"兩",
            correct_form="两",
            description="'兩' 应统一为 '两'（两个、两者等）。",
        )


class A1_021_CheckRule(UnifiedTermRule):
    """檢 统一为 检."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A1-021",
            wrong_pattern=r"檢",
            correct_form="检",
            description="'檢' 应统一为 '检'（检查、检验等）。",
        )


class A1_022_BodyRule(UnifiedTermRule):
    """體 统一为 体."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A1-022",
            wrong_pattern=r"體",
            correct_form="体",
            description="'體' 应统一为 '体'（身体、体验等）。",
        )


class A1_023_LikeRule(UnifiedTermRule):
    """彷 统一为 仿 (表示resemble)."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A1-023",
            wrong_pattern=r"彷(?=彿|佛|如|若)",  # Only when followed by 彿/佛/如/若
            correct_form="仿",
            description="'彷' 应统一为 '仿'（仿佛、仿如等，表示「像」时）。",
        )


# ============================================================================
# A2类 - 异形词规范（Variant Word Forms）
# ============================================================================


class VariantWordRule(DeterministicRule):
    """Base class for variant word form rules (A2 subcategory)."""

    def __init__(
        self,
        rule_id: str,
        wrong_form: str,
        correct_form: str,
        description: str,
        use_regex: bool = False,
        exclusion_pattern: str | None = None,
    ):
        """
        Initialize variant word rule.

        Args:
            rule_id: Rule identifier (e.g., "A2-001")
            wrong_form: Incorrect or non-standard form (regex pattern if use_regex=True)
            correct_form: Correct or preferred standard form
            description: Description of the rule
            use_regex: Whether wrong_form is a regex pattern
            exclusion_pattern: Optional regex pattern to exclude from detection
        """
        super().__init__(
            rule_id=rule_id,
            category="A",
            subcategory="A2",
            severity="warning",
            blocks_publish=False,
            can_auto_fix=True,
        )
        self.wrong_form = wrong_form
        self.correct_form = correct_form
        self.description = description
        self.use_regex = use_regex
        self.exclusion_pattern = exclusion_pattern

        # Compile patterns
        if use_regex:
            self.wrong_pattern = re.compile(wrong_form)
        else:
            self.wrong_pattern = re.compile(re.escape(wrong_form))

        if exclusion_pattern:
            self.exclusion = re.compile(exclusion_pattern)
        else:
            self.exclusion = None

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        for match in self.wrong_pattern.finditer(content):
            # Check exclusion pattern
            if self.exclusion:
                context_start = max(0, match.start() - 5)
                context_end = min(len(content), match.end() + 5)
                context = content[context_start:context_end]
                if self.exclusion.search(context):
                    continue

            snippet_start = max(0, match.start() - 10)
            snippet_end = min(len(content), match.end() + 10)
            snippet = content[snippet_start:snippet_end]

            issues.append(
                ProofreadingIssue(
                    rule_id=self.rule_id,
                    category=self.category,
                    subcategory=self.subcategory,
                    message=f"异形词规范：'{match.group()}' 应写作 '{self.correct_form}'。{self.description}",
                    suggestion=f"将 '{match.group()}' 替换为 '{self.correct_form}'。",
                    severity=self.severity,
                    confidence=0.95,
                    can_auto_fix=self.can_auto_fix,
                    blocks_publish=self.blocks_publish,
                    source=RuleSource.SCRIPT,
                    attributed_by=self.__class__.__name__,
                    location={"offset": match.start()},
                    snippet=snippet,
                    auto_fix_value=self.correct_form,
                )
            )
        return issues


class A2_001_GouTongRule(VariantWordRule):
    """勾通 → 沟通 (A2-001)."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A2-001",
            wrong_form="勾通",
            correct_form="沟通",
            description="表示「交流」时应使用「沟通」，而非「勾通」。",
        )


class A2_002_ZhangHuRule(VariantWordRule):
    """帐户 → 账户 (A2-002)."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A2-002",
            wrong_form="帐户",
            correct_form="账户",
            description="现代标准用法中「账户」是正确形式。",
        )


class A2_003_BuFenRule(VariantWordRule):
    """部份 → 部分 (A2-003)."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A2-003",
            wrong_form="部份",
            correct_form="部分",
            description="标准用法应使用「部分」，而非「部份」。",
        )


class A2_004_FenERule(VariantWordRule):
    """分额 → 份额 (A2-004)."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A2-004",
            wrong_form="分额",
            correct_form="份额",
            description="表示「配额、定额」时应使用「份额」。",
        )


class A2_005_DuJiaRule(VariantWordRule):
    """渡假 → 度假 (A2-005)."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A2-005",
            wrong_form="渡假",
            correct_form="度假",
            description="表示「休假旅游」时应使用「度假」，而非「渡假」。",
        )


class A2_006_BuShuRule(VariantWordRule):
    """布署 → 部署 (A2-006)."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A2-006",
            wrong_form="布署",
            correct_form="部署",
            description="表示「安排、配置」时应使用「部署」，而非「布署」。",
        )


class A2_007_JiHuiZhuYiRule(VariantWordRule):
    """机会主意 → 机会主义 (A2-007)."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A2-007",
            wrong_form="机会主意",
            correct_form="机会主义",
            description="「机会主义」是政治术语，不是「机会主意」。",
        )


class A2_008_XiuLianRule(VariantWordRule):
    """修练 → 修炼 (A2-008)."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A2-008",
            wrong_form="修练",
            correct_form="修炼",
            description="表示「修行、炼功」时应使用「修炼」，而非「修练」。",
        )


class A2_009_JiaoDaiRule(VariantWordRule):
    """交待 → 交代 (A2-009)."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A2-009",
            wrong_form="交待",
            correct_form="交代",
            description="现代标准用法推荐「交代」，而非「交待」。",
        )


class A2_010_FenLiangRule(VariantWordRule):
    """份量 → 分量 (A2-010)."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A2-010",
            wrong_form="份量",
            correct_form="分量",
            description="表示「重量、轻重」时应使用「分量」，而非「份量」。",
        )


# ============================================================================
# A3类 - 常见错字规则
# ============================================================================


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


# A3 Class - Additional Common Typos (30 new rules: A3-015 to A3-044)
class A3_015_XiaoShengNiJiRule(TypoReplacementRule):
    """A3-015: 消声匿迹 → 销声匿迹."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A3-015",
            wrong_pattern=r"消声匿迹",
            correct_form="销声匿迹",
            description="应为 '销声匿迹'，不写 '消声匿迹'",
        )


class A3_016_MoShouChengGuiRule(TypoReplacementRule):
    """A3-016: 默守成规 → 墨守成规."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A3-016",
            wrong_pattern=r"默守成规",
            correct_form="墨守成规",
            description="应为 '墨守成规'，不写 '默守成规'",
        )


class A3_017_SuiShengFuHeRule(TypoReplacementRule):
    """A3-017: 随声附合 → 随声附和."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A3-017",
            wrong_pattern=r"随声附合",
            correct_form="随声附和",
            description="应为 '随声附和'，不写 '随声附合'",
        )


class A3_018_MingFuQiShiRule(TypoReplacementRule):
    """A3-018: 名符其实 → 名副其实."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A3-018",
            wrong_pattern=r"名符其实",
            correct_form="名副其实",
            description="应为 '名副其实'，不写 '名符其实'",
        )


class A3_019_BianBenJiaLiRule(TypoReplacementRule):
    """A3-019: 变本加励 → 变本加厉."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A3-019",
            wrong_pattern=r"变本加励",
            correct_form="变本加厉",
            description="应为 '变本加厉'，不写 '变本加励'",
        )


class A3_020_YiChouMoZhanRule(TypoReplacementRule):
    """A3-020: 一愁莫展 → 一筹莫展."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A3-020",
            wrong_pattern=r"一愁莫展",
            correct_form="一筹莫展",
            description="应为 '一筹莫展'，不写 '一愁莫展'",
        )


class A3_021_XingLuoQiBuRule(TypoReplacementRule):
    """A3-021: 星罗棋部 → 星罗棋布."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A3-021",
            wrong_pattern=r"星罗棋部",
            correct_form="星罗棋布",
            description="应为 '星罗棋布'，不写 '星罗棋部'",
        )


class A3_022_JingBingJianZhengRule(TypoReplacementRule):
    """A3-022: 精兵简正 → 精兵简政."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A3-022",
            wrong_pattern=r"精兵简正",
            correct_form="精兵简政",
            description="应为 '精兵简政'，不写 '精兵简正'",
        )


class A3_023_ZouTouWuLuRule(TypoReplacementRule):
    """A3-023: 走头无路 → 走投无路."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A3-023",
            wrong_pattern=r"走头无路",
            correct_form="走投无路",
            description="应为 '走投无路'，不写 '走头无路'",
        )


class A3_024_GuiFuShenGongRule(TypoReplacementRule):
    """A3-024: 鬼符神工 → 鬼斧神工."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A3-024",
            wrong_pattern=r"鬼符神工",
            correct_form="鬼斧神工",
            description="应为 '鬼斧神工'，不写 '鬼符神工'",
        )


class A3_025_ZhongShengXiangRiRule(TypoReplacementRule):
    """A3-025: 重生向日 → 重升向日 (errors may vary, using common variant)."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A3-025",
            wrong_pattern=r"蒸蒸日尚",
            correct_form="蒸蒸日上",
            description="应为 '蒸蒸日上'，不写 '蒸蒸日尚'",
        )


class A3_026_HanNiuChongDongRule(TypoReplacementRule):
    """A3-026: 汗流夹背 → 汗流浃背."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A3-026",
            wrong_pattern=r"汗流夹背",
            correct_form="汗流浃背",
            description="应为 '汗流浃背'，不写 '汗流夹背'",
        )


class A3_027_XinXinXiangRongRule(TypoReplacementRule):
    """A3-027: 欣欣向荣 typo variants."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A3-027",
            wrong_pattern=r"欣欣相荣",
            correct_form="欣欣向荣",
            description="应为 '欣欣向荣'，不写 '欣欣相荣'",
        )


class A3_028_BuYiErTongRule(TypoReplacementRule):
    """A3-028: 不一而同 → 不一而足."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A3-028",
            wrong_pattern=r"不一而同",
            correct_form="不一而足",
            description="应为 '不一而足'，不写 '不一而同'",
        )


class A3_029_YuYueYuShiRule(TypoReplacementRule):
    """A3-029: 于事无补 vs 与事无补."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A3-029",
            wrong_pattern=r"与事无补",
            correct_form="于事无补",
            description="应为 '于事无补'，不写 '与事无补'",
        )


class A3_030_CangHaiYiSuRule(TypoReplacementRule):
    """A3-030: 沧海一粟 typo."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A3-030",
            wrong_pattern=r"沧海一栗",
            correct_form="沧海一粟",
            description="应为 '沧海一粟'，不写 '沧海一栗'",
        )


class A3_031_ManBuJingXinRule(TypoReplacementRule):
    """A3-031: 漫不经心 typo."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A3-031",
            wrong_pattern=r"慢不经心",
            correct_form="漫不经心",
            description="应为 '漫不经心'，不写 '慢不经心'",
        )


class A3_032_BuQiErYuRule(TypoReplacementRule):
    """A3-032: 不期而遇 typo."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A3-032",
            wrong_pattern=r"不其而遇",
            correct_form="不期而遇",
            description="应为 '不期而遇'，不写 '不其而遇'",
        )


class A3_033_DiaoChaPinZhongRule(TypoReplacementRule):
    """A3-033: 调查 typo."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A3-033",
            wrong_pattern=r"凋查",
            correct_form="调查",
            description="应为 '调查'，不写 '凋查'",
        )


class A3_034_JiaoTaShiDiRule(TypoReplacementRule):
    """A3-034: 脚踏实地 typo."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A3-034",
            wrong_pattern=r"脚踏实[低底]",
            correct_form="脚踏实地",
            description="应为 '脚踏实地'，不写 '脚踏实底/低'",
        )


class A3_035_QingErYiJuRule(TypoReplacementRule):
    """A3-035: 倾耳易举 → 轻而易举."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A3-035",
            wrong_pattern=r"[倾清]而易举",
            correct_form="轻而易举",
            description="应为 '轻而易举'，不写 '倾而易举/清而易举'",
        )


class A3_036_JiuJiuGuiZhengRule(TypoReplacementRule):
    """A3-036: 纠正 typo."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A3-036",
            wrong_pattern=r"究正",
            correct_form="纠正",
            description="应为 '纠正'，不写 '究正'",
        )


class A3_037_BiMianRule(TypoReplacementRule):
    """A3-037: 避免 typo."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A3-037",
            wrong_pattern=r"[壁避辟]免",
            correct_form="避免",
            description="应为 '避免'，不写 '壁免/辟免'",
        )


class A3_038_BaoZhaRule(TypoReplacementRule):
    """A3-038: 爆炸 typo."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A3-038",
            wrong_pattern=r"暴炸",
            correct_form="爆炸",
            description="应为 '爆炸'，不写 '暴炸'",
        )


class A3_039_ShiGanRule(TypoReplacementRule):
    """A3-039: 试管 typo."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A3-039",
            wrong_pattern=r"试管婴[孩儿]",
            correct_form="试管婴儿",
            description="应为 '试管婴儿'，不写 '试管婴孩'",
        )


class A3_040_FenQiRule(TypoReplacementRule):
    """A3-040: 愤起 → 奋起."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A3-040",
            wrong_pattern=r"愤起",
            correct_form="奋起",
            description="应为 '奋起'，不写 '愤起'（在「奋起反抗」等语境）",
        )


class A3_041_JianDingRule(TypoReplacementRule):
    """A3-041: 坚定 typo."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A3-041",
            wrong_pattern=r"艰定",
            correct_form="坚定",
            description="应为 '坚定'，不写 '艰定'",
        )


class A3_042_ChengFenRule(TypoReplacementRule):
    """A3-042: 成分 typo."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A3-042",
            wrong_pattern=r"成份(?!股|有限)",
            correct_form="成分",
            description="应为 '成分'，不写 '成份'（除「份」用于股份等）",
        )


class A3_043_JianChaRule(TypoReplacementRule):
    """A3-043: 检察 vs 检查."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A3-043",
            wrong_pattern=r"检察(?!院|官|署|机关|长|系统)",
            correct_form="检查",
            description="一般应为 '检查'，'检察' 仅用于法律机关（检察院等）",
        )


class A3_044_WanQuanRule(TypoReplacementRule):
    """A3-044: 完全 typo."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A3-044",
            wrong_pattern=r"完[圈全](?![部满整])(?=不|没)",
            correct_form="完全",
            description="应为 '完全'，不写 '完圈'（在「完全不/没」等语境）",
        )


# ============================================================================
# A4类 - 非正式用语规则
# ============================================================================


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


# C Class - Additional Number & Unit Rules (7 new rules: C1-007 to C2-006)
class C1_007_TimeFormatRule(DeterministicRule):
    """Check time format consistency (C1-007)."""

    # 匹配不规范的时间格式
    IMPROPER_TIME = re.compile(r"(\d{1,2})\s*[:：]\s*(\d{2})\s*分?钟?")

    def __init__(self) -> None:
        super().__init__(
            rule_id="C1-007",
            category="C",
            subcategory="C1",
            severity="info",
            blocks_publish=False,
            can_auto_fix=True,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        for match in self.IMPROPER_TIME.finditer(content):
            snippet_start = max(0, match.start() - 10)
            snippet_end = min(len(content), match.end() + 10)
            snippet = content[snippet_start:snippet_end]

            issues.append(
                ProofreadingIssue(
                    rule_id=self.rule_id,
                    category=self.category,
                    subcategory=self.subcategory,
                    message="时间格式：建议使用标准格式如 '14:30' 或 '下午2点30分'。",
                    suggestion=f"统一时间表示格式。",
                    severity=self.severity,
                    confidence=0.6,
                    can_auto_fix=self.can_auto_fix,
                    blocks_publish=self.blocks_publish,
                    source=RuleSource.SCRIPT,
                    attributed_by="C1_007_TimeFormatRule",
                    location={"offset": match.start()},
                    evidence=snippet,
                )
            )
        return issues


class C1_008_ScientificNotationRule(DeterministicRule):
    """Check scientific notation format (C1-008)."""

    # 匹配科学计数法相关
    LARGE_NUMBER = re.compile(r"(\d{1,3})(,?\d{3}){3,}")  # 大数字建议用科学计数法

    def __init__(self) -> None:
        super().__init__(
            rule_id="C1-008",
            category="C",
            subcategory="C1",
            severity="info",
            blocks_publish=False,
            can_auto_fix=False,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        for match in self.LARGE_NUMBER.finditer(content):
            # 只对非常大的数字（10位以上）提示
            num_str = match.group().replace(',', '')
            if len(num_str) >= 10:
                snippet_start = max(0, match.start() - 10)
                snippet_end = min(len(content), match.end() + 10)
                snippet = content[snippet_start:snippet_end]

                issues.append(
                    ProofreadingIssue(
                        rule_id=self.rule_id,
                        category=self.category,
                        subcategory=self.subcategory,
                        message="数字格式：超大数字建议使用科学计数法或「亿、万」等单位。",
                        suggestion=f"考虑将 '{match.group()}' 转换为科学计数法。",
                        severity=self.severity,
                        confidence=0.5,
                        can_auto_fix=self.can_auto_fix,
                        blocks_publish=self.blocks_publish,
                        source=RuleSource.SCRIPT,
                        attributed_by="C1_008_ScientificNotationRule",
                        location={"offset": match.start()},
                        evidence=snippet,
                    )
                )
        return issues


class C1_009_OrdinalNumberRule(DeterministicRule):
    """Check ordinal number format (C1-009)."""

    # 匹配序数格式
    ORDINAL_PATTERN = re.compile(r"第\s*[0-9]+\s*[个|位|名|次|届|期|章|条|项]")

    def __init__(self) -> None:
        super().__init__(
            rule_id="C1-009",
            category="C",
            subcategory="C1",
            severity="info",
            blocks_publish=False,
            can_auto_fix=True,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        for match in self.ORDINAL_PATTERN.finditer(content):
            if ' ' in match.group():  # 只对有空格的情况提示
                snippet_start = max(0, match.start() - 10)
                snippet_end = min(len(content), match.end() + 10)
                snippet = content[snippet_start:snippet_end]

                corrected = match.group().replace(' ', '')
                issues.append(
                    ProofreadingIssue(
                        rule_id=self.rule_id,
                        category=self.category,
                        subcategory=self.subcategory,
                        message="序数格式：「第」与数字、量词之间不应有空格。",
                        suggestion=f"将 '{match.group()}' 改为 '{corrected}'。",
                        severity=self.severity,
                        confidence=0.9,
                        can_auto_fix=self.can_auto_fix,
                        blocks_publish=self.blocks_publish,
                        source=RuleSource.SCRIPT,
                        attributed_by="C1_009_OrdinalNumberRule",
                        location={"offset": match.start()},
                        evidence=snippet,
                    )
                )
        return issues


class C2_003_TemperatureUnitRule(DeterministicRule):
    """Check temperature unit format (C2-003)."""

    # 匹配温度表示
    TEMP_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s*(?:度|摄氏度|华氏度)")

    def __init__(self) -> None:
        super().__init__(
            rule_id="C2-003",
            category="C",
            subcategory="C2",
            severity="info",
            blocks_publish=False,
            can_auto_fix=True,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        for match in self.TEMP_PATTERN.finditer(content):
            original = match.group()
            if "华氏度" in original:
                # 华氏度不建议修改
                continue
            if "摄氏度" in original:
                # 建议使用°C
                number = re.search(r"(\d+(?:\.\d+)?)", original).group()
                corrected = f"{number}°C"
                snippet_start = max(0, match.start() - 10)
                snippet_end = min(len(content), match.end() + 10)
                snippet = content[snippet_start:snippet_end]

                issues.append(
                    ProofreadingIssue(
                        rule_id=self.rule_id,
                        category=self.category,
                        subcategory=self.subcategory,
                        message="计量单位：建议使用符号 '°C' 表示摄氏度。",
                        suggestion=f"将 '{original}' 改为 '{corrected}'。",
                        severity=self.severity,
                        confidence=0.7,
                        can_auto_fix=self.can_auto_fix,
                        blocks_publish=self.blocks_publish,
                        source=RuleSource.SCRIPT,
                        attributed_by="C2_003_TemperatureUnitRule",
                        location={"offset": match.start()},
                        evidence=snippet,
                    )
                )
        return issues


class C2_004_WeightUnitRule(DeterministicRule):
    """Check weight unit format (C2-004)."""

    # 匹配重量单位
    WEIGHT_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s*(?:公斤|千克|克|毫克|吨)")

    def __init__(self) -> None:
        super().__init__(
            rule_id="C2-004",
            category="C",
            subcategory="C2",
            severity="info",
            blocks_publish=False,
            can_auto_fix=True,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        for match in self.WEIGHT_PATTERN.finditer(content):
            original = match.group()
            number = re.search(r"(\d+(?:\.\d+)?)", original).group()

            # 建议使用标准单位符号
            if "公斤" in original or "千克" in original:
                corrected = f"{number} kg"
            elif "吨" in original:
                corrected = f"{number} t"
            elif "毫克" in original:
                corrected = f"{number} mg"
            elif "克" in original:
                corrected = f"{number} g"
            else:
                continue

            snippet_start = max(0, match.start() - 10)
            snippet_end = min(len(content), match.end() + 10)
            snippet = content[snippet_start:snippet_end]

            issues.append(
                ProofreadingIssue(
                    rule_id=self.rule_id,
                    category=self.category,
                    subcategory=self.subcategory,
                    message="计量单位：建议使用国际标准单位符号（kg、g、mg、t）。",
                    suggestion=f"将 '{original}' 改为 '{corrected}'。",
                    severity=self.severity,
                    confidence=0.6,
                    can_auto_fix=self.can_auto_fix,
                    blocks_publish=self.blocks_publish,
                    source=RuleSource.SCRIPT,
                    attributed_by="C2_004_WeightUnitRule",
                    location={"offset": match.start()},
                    evidence=snippet,
                )
            )
        return issues


class C2_005_VolumeUnitRule(DeterministicRule):
    """Check volume unit format (C2-005)."""

    # 匹配体积单位
    VOLUME_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s*(?:立方米|立方厘米|升|毫升)")

    def __init__(self) -> None:
        super().__init__(
            rule_id="C2-005",
            category="C",
            subcategory="C2",
            severity="info",
            blocks_publish=False,
            can_auto_fix=True,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        for match in self.VOLUME_PATTERN.finditer(content):
            original = match.group()
            number = re.search(r"(\d+(?:\.\d+)?)", original).group()

            # 建议使用标准单位符号
            if "立方米" in original:
                corrected = f"{number} m³"
            elif "立方厘米" in original:
                corrected = f"{number} cm³"
            elif "毫升" in original:
                corrected = f"{number} ml"
            elif "升" in original:
                corrected = f"{number} L"
            else:
                continue

            snippet_start = max(0, match.start() - 10)
            snippet_end = min(len(content), match.end() + 10)
            snippet = content[snippet_start:snippet_end]

            issues.append(
                ProofreadingIssue(
                    rule_id=self.rule_id,
                    category=self.category,
                    subcategory=self.subcategory,
                    message="计量单位：建议使用国际标准单位符号（m³、cm³、L、ml）。",
                    suggestion=f"将 '{original}' 改为 '{corrected}'。",
                    severity=self.severity,
                    confidence=0.6,
                    can_auto_fix=self.can_auto_fix,
                    blocks_publish=self.blocks_publish,
                    source=RuleSource.SCRIPT,
                    attributed_by="C2_005_VolumeUnitRule",
                    location={"offset": match.start()},
                    evidence=snippet,
                )
            )
        return issues


class C2_006_AreaUnitRule(DeterministicRule):
    """Check area unit format (C2-006)."""

    # 匹配面积单位（除了已有的平方米）
    AREA_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s*(?:平方公里|平方厘米|公顷)")

    def __init__(self) -> None:
        super().__init__(
            rule_id="C2-006",
            category="C",
            subcategory="C2",
            severity="info",
            blocks_publish=False,
            can_auto_fix=True,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        for match in self.AREA_PATTERN.finditer(content):
            original = match.group()
            number = re.search(r"(\d+(?:\.\d+)?)", original).group()

            # 建议使用标准单位符号
            if "平方公里" in original:
                corrected = f"{number} km²"
            elif "平方厘米" in original:
                corrected = f"{number} cm²"
            elif "公顷" in original:
                corrected = f"{number} ha"
            else:
                continue

            snippet_start = max(0, match.start() - 10)
            snippet_end = min(len(content), match.end() + 10)
            snippet = content[snippet_start:snippet_end]

            issues.append(
                ProofreadingIssue(
                    rule_id=self.rule_id,
                    category=self.category,
                    subcategory=self.subcategory,
                    message="计量单位：建议使用国际标准单位符号（km²、cm²、ha）。",
                    suggestion=f"将 '{original}' 改为 '{corrected}'。",
                    severity=self.severity,
                    confidence=0.6,
                    can_auto_fix=self.can_auto_fix,
                    blocks_publish=self.blocks_publish,
                    source=RuleSource.SCRIPT,
                    attributed_by="C2_006_AreaUnitRule",
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

    VERSION = "1.0.0"  # Phase 2 Complete: 119条规则 (A1+20, A2+10, A3+30, B+15, C+7)

    def __init__(self) -> None:
        self.rules: List[DeterministicRule] = [
            # B类 - 标点符号与排版（25条）
            # B1 子类 - 基本标点（10条）
            MissingPunctuationRule(),  # B1-001
            EllipsisFormatRule(),  # B1-002: 省略号格式
            QuestionMarkAbuseRule(),  # B1-003: 问号滥用
            ExclamationMarkAbuseRule(),  # B1-004: 感叹号滥用
            MixedPunctuationRule(),  # B1-005: 中英文标点混用
            B1_006_ColonFormatRule(),  # B1-006: 冒号格式
            B1_007_SemicolonFormatRule(),  # B1-007: 分号格式
            B1_008_ConsecutivePunctuationRule(),  # B1-008: 连续标点
            B1_009_PunctuationSpacingRule(),  # B1-009: 标点后空格
            B1_010_ChinesePeriodRule(),  # B1-010: 中文句号
            # B2 子类 - 逗号顿号（5条）
            HalfWidthCommaRule(),  # B2-002
            B2_003_DunhaoUsageRule(),  # B2-003: 顿号使用
            B2_004_CommaAbuseRule(),  # B2-004: 逗号滥用
            B2_005_SerialCommaRule(),  # B2-005: 序列逗号
            # B3 子类 - 引号书名号（3条）
            QuotationMatchingRule(),  # B3-001: 引号配对
            QuotationNestingRule(),  # B3-002: 引号嵌套
            BookTitleMatchingRule(),  # B3-003: 书名号配对
            # B4-B7 子类 - 其他标点（7条）
            B4_001_ParenthesesMatchingRule(),  # B4-001: 括号配对
            B4_002_ParenthesesFormatRule(),  # B4-002: 括号格式
            B5_001_DoubleQuoteMisuseRule(),  # B5-001: 双引号误用
            B5_002_SingleQuoteMisuseRule(),  # B5-002: 单引号误用
            B6_001_EmphasisMarkRule(),  # B6-001: 间隔号
            B7_001_DashFormatRule(),  # B7-001: 破折号格式
            B7_002_HyphenFormatRule(),  # B7-002: 连接号格式
            HalfWidthDashRule(),  # B7-004: 半角短横线
            # A类 - 用字规范（73条）
            # A1 子类 - 统一用字（23条）
            UnifiedTermMeterRule(),  # A1-001
            A1_002_LiInsideRule(),  # A1-002: 裡/裏 → 里
            A1_003_MeQuestionRule(),  # A1-003: 麽 → 么
            A1_004_EmployRule(),  # A1-004: 僱 → 雇
            A1_005_AndAlsoRule(),  # A1-005: 並 → 并
            A1_006_ReturnRule(),  # A1-006: 迴 → 回
            A1_007_SecretRule(),  # A1-007: 祕 → 秘
            A1_008_LineRule(),  # A1-008: 綫 → 线
            A1_009_OnlyRule(),  # A1-009: 衹 → 只
            UnifiedTermOccupyRule(),  # A1-010: 佔 → 占
            A1_011_ExhaustRule(),  # A1-011: 儘 → 尽
            A1_012_PrepareRule(),  # A1-012: 準 → 准
            A1_013_CrowdRule(),  # A1-013: 衆 → 众
            A1_014_GroupRule(),  # A1-014: 羣 → 群
            A1_015_ForAsRule(),  # A1-015: 爲 → 为
            A1_016_AtInRule(),  # A1-016: 於 → 于
            A1_017_CleanRule(),  # A1-017: 淨 → 净
            A1_018_JustNowRule(),  # A1-018: 纔 → 才
            A1_019_ThroughRule(),  # A1-019: 籍 → 藉
            A1_020_TwoRule(),  # A1-020: 兩 → 两
            A1_021_CheckRule(),  # A1-021: 檢 → 检
            A1_022_BodyRule(),  # A1-022: 體 → 体
            A1_023_LikeRule(),  # A1-023: 彷 → 仿
            # A2 子类 - 异形词规范（10条）
            A2_001_GouTongRule(),  # A2-001: 勾通 → 沟通
            A2_002_ZhangHuRule(),  # A2-002: 帐户 → 账户
            A2_003_BuFenRule(),  # A2-003: 部份 → 部分
            A2_004_FenERule(),  # A2-004: 分额 → 份额
            A2_005_DuJiaRule(),  # A2-005: 渡假 → 度假
            A2_006_BuShuRule(),  # A2-006: 布署 → 部署
            A2_007_JiHuiZhuYiRule(),  # A2-007: 机会主意 → 机会主义
            A2_008_XiuLianRule(),  # A2-008: 修练 → 修炼
            A2_009_JiaoDaiRule(),  # A2-009: 交待 → 交代
            A2_010_FenLiangRule(),  # A2-010: 份量 → 分量
            # A3 子类 - 常见错字（40条）
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
            # A3-015 to A3-044 (30 additional typos)
            A3_015_XiaoShengNiJiRule(),  # A3-015: 销声匿迹
            A3_016_MoShouChengGuiRule(),  # A3-016: 墨守成规
            A3_017_SuiShengFuHeRule(),  # A3-017: 随声附和
            A3_018_MingFuQiShiRule(),  # A3-018: 名副其实
            A3_019_BianBenJiaLiRule(),  # A3-019: 变本加厉
            A3_020_YiChouMoZhanRule(),  # A3-020: 一筹莫展
            A3_021_XingLuoQiBuRule(),  # A3-021: 星罗棋布
            A3_022_JingBingJianZhengRule(),  # A3-022: 精兵简政
            A3_023_ZouTouWuLuRule(),  # A3-023: 走投无路
            A3_024_GuiFuShenGongRule(),  # A3-024: 鬼斧神工
            A3_025_ZhongShengXiangRiRule(),  # A3-025: 蒸蒸日上
            A3_026_HanNiuChongDongRule(),  # A3-026: 汗流浃背
            A3_027_XinXinXiangRongRule(),  # A3-027: 欣欣向荣
            A3_028_BuYiErTongRule(),  # A3-028: 不一而足
            A3_029_YuYueYuShiRule(),  # A3-029: 于事无补
            A3_030_CangHaiYiSuRule(),  # A3-030: 沧海一粟
            A3_031_ManBuJingXinRule(),  # A3-031: 漫不经心
            A3_032_BuQiErYuRule(),  # A3-032: 不期而遇
            A3_033_DiaoChaPinZhongRule(),  # A3-033: 调查
            A3_034_JiaoTaShiDiRule(),  # A3-034: 脚踏实地
            A3_035_QingErYiJuRule(),  # A3-035: 轻而易举
            A3_036_JiuJiuGuiZhengRule(),  # A3-036: 纠正
            A3_037_BiMianRule(),  # A3-037: 避免
            A3_038_BaoZhaRule(),  # A3-038: 爆炸
            A3_039_ShiGanRule(),  # A3-039: 试管婴儿
            A3_040_FenQiRule(),  # A3-040: 奋起
            A3_041_JianDingRule(),  # A3-041: 坚定
            A3_042_ChengFenRule(),  # A3-042: 成分
            A3_043_JianChaRule(),  # A3-043: 检查
            A3_044_WanQuanRule(),  # A3-044: 完全
            # A4 子类 - 非正式用语（1条）
            InformalLanguageRule(),  # A4-014
            # C类 - 数字与计量（15条）
            # C1 子类 - 数字格式（9条）
            FullWidthDigitRule(),  # C1-006
            NumberSeparatorRule(),  # C1-001
            PercentageFormatRule(),  # C1-002: 百分比格式
            DecimalPointRule(),  # C1-003: 小数点格式
            DateFormatRule(),  # C1-004: 日期格式
            CurrencyFormatRule(),  # C1-005: 货币格式
            C1_007_TimeFormatRule(),  # C1-007: 时间格式
            C1_008_ScientificNotationRule(),  # C1-008: 科学计数法
            C1_009_OrdinalNumberRule(),  # C1-009: 序数格式
            # C2 子类 - 单位格式（6条）
            KilometerUnificationRule(),  # C2-001: 公里/千米统一
            SquareMeterSymbolRule(),  # C2-002: 平方米符号
            C2_003_TemperatureUnitRule(),  # C2-003: 温度单位
            C2_004_WeightUnitRule(),  # C2-004: 重量单位
            C2_005_VolumeUnitRule(),  # C2-005: 体积单位
            C2_006_AreaUnitRule(),  # C2-006: 面积单位
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

