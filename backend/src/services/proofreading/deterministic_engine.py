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


class B2_001_CommaSpacingRule(DeterministicRule):
    """Check comma spacing in mixed Chinese-English text (B2-001)."""

    # 中英文混排时，英文逗号后缺少空格
    COMMA_NO_SPACE = re.compile(r",(?=[a-zA-Z])")

    def __init__(self) -> None:
        super().__init__(
            rule_id="B2-001",
            category="B",
            subcategory="B2",
            severity="info",
            blocks_publish=False,
            can_auto_fix=True,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        for match in self.COMMA_NO_SPACE.finditer(content):
            snippet_start = max(0, match.start() - 10)
            snippet_end = min(len(content), match.end() + 10)
            snippet = content[snippet_start:snippet_end]

            issues.append(
                ProofreadingIssue(
                    rule_id=self.rule_id,
                    category=self.category,
                    subcategory=self.subcategory,
                    message="逗号格式：英文逗号后应有空格。",
                    suggestion="在逗号后添加空格。",
                    severity=self.severity,
                    confidence=0.9,
                    can_auto_fix=self.can_auto_fix,
                    blocks_publish=self.blocks_publish,
                    source=RuleSource.SCRIPT,
                    attributed_by="B2_001_CommaSpacingRule",
                    location={"offset": match.start()},
                    evidence=snippet,
                )
            )
        return issues


class B2_006_ConsecutiveCommasRule(DeterministicRule):
    """Check consecutive commas (B2-006)."""

    # 连续逗号检测
    CONSECUTIVE_COMMAS = re.compile(r"[,，]{2,}")

    def __init__(self) -> None:
        super().__init__(
            rule_id="B2-006",
            category="B",
            subcategory="B2",
            severity="warning",
            blocks_publish=False,
            can_auto_fix=True,
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
                    message=f"逗号使用：检测到连续逗号 '{match.group()}'。",
                    suggestion="删除多余的逗号，保留一个。",
                    severity=self.severity,
                    confidence=1.0,
                    can_auto_fix=self.can_auto_fix,
                    blocks_publish=self.blocks_publish,
                    source=RuleSource.SCRIPT,
                    attributed_by="B2_006_ConsecutiveCommasRule",
                    location={"offset": match.start()},
                    evidence=snippet,
                )
            )
        return issues


class B2_007_DunhaoCommaMixRule(DeterministicRule):
    """Check dunhao and comma mixing (B2-007)."""

    # 顿号和逗号在同一并列结构中混用
    DUNHAO_COMMA_MIX = re.compile(r"[\u4e00-\u9fff]+、[\u4e00-\u9fff]+，[\u4e00-\u9fff]+、")

    def __init__(self) -> None:
        super().__init__(
            rule_id="B2-007",
            category="B",
            subcategory="B2",
            severity="warning",
            blocks_publish=False,
            can_auto_fix=False,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        for match in self.DUNHAO_COMMA_MIX.finditer(content):
            snippet_start = max(0, match.start() - 10)
            snippet_end = min(len(content), match.end() + 10)
            snippet = content[snippet_start:snippet_end]

            issues.append(
                ProofreadingIssue(
                    rule_id=self.rule_id,
                    category=self.category,
                    subcategory=self.subcategory,
                    message="顿号与逗号混用：并列结构中应统一使用顿号或逗号。",
                    suggestion="统一使用顿号「、」或逗号「，」。",
                    severity=self.severity,
                    confidence=0.8,
                    can_auto_fix=self.can_auto_fix,
                    blocks_publish=self.blocks_publish,
                    source=RuleSource.SCRIPT,
                    attributed_by="B2_007_DunhaoCommaMixRule",
                    location={"offset": match.start()},
                    evidence=snippet,
                )
            )
        return issues


class B3_004_EmptyQuoteRule(DeterministicRule):
    """Check empty quotes (B3-004)."""

    # 空引号检测
    EMPTY_QUOTE = re.compile(r"[「『""''][\s]*[」』""'']")

    def __init__(self) -> None:
        super().__init__(
            rule_id="B3-004",
            category="B",
            subcategory="B3",
            severity="warning",
            blocks_publish=False,
            can_auto_fix=False,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        for match in self.EMPTY_QUOTE.finditer(content):
            snippet_start = max(0, match.start() - 10)
            snippet_end = min(len(content), match.end() + 10)
            snippet = content[snippet_start:snippet_end]

            issues.append(
                ProofreadingIssue(
                    rule_id=self.rule_id,
                    category=self.category,
                    subcategory=self.subcategory,
                    message=f"引号使用：检测到空引号 '{match.group()}'。",
                    suggestion="删除空引号或添加内容。",
                    severity=self.severity,
                    confidence=1.0,
                    can_auto_fix=self.can_auto_fix,
                    blocks_publish=self.blocks_publish,
                    source=RuleSource.SCRIPT,
                    attributed_by="B3_004_EmptyQuoteRule",
                    location={"offset": match.start()},
                    evidence=snippet,
                )
            )
        return issues


class B3_005_BookTitleQuoteMixRule(DeterministicRule):
    """Check book title and quote mixing (B3-005)."""

    # 书名号与引号混用（书籍、文章、电影等应用书名号）
    TITLE_IN_QUOTE = re.compile(r"[""''][\u4e00-\u9fff]{2,8}(?:篇|章|文|书|集|部)[""'']")

    def __init__(self) -> None:
        super().__init__(
            rule_id="B3-005",
            category="B",
            subcategory="B3",
            severity="info",
            blocks_publish=False,
            can_auto_fix=False,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        for match in self.TITLE_IN_QUOTE.finditer(content):
            snippet_start = max(0, match.start() - 10)
            snippet_end = min(len(content), match.end() + 10)
            snippet = content[snippet_start:snippet_end]

            issues.append(
                ProofreadingIssue(
                    rule_id=self.rule_id,
                    category=self.category,
                    subcategory=self.subcategory,
                    message=f"书名号使用：'{match.group()}' 可能应使用书名号。",
                    suggestion="书籍、文章、电影等标题应使用书名号《》，而非引号。",
                    severity=self.severity,
                    confidence=0.7,
                    can_auto_fix=self.can_auto_fix,
                    blocks_publish=self.blocks_publish,
                    source=RuleSource.SCRIPT,
                    attributed_by="B3_005_BookTitleQuoteMixRule",
                    location={"offset": match.start()},
                    evidence=snippet,
                )
            )
        return issues


class B4_003_ParenthesisSpacingRule(DeterministicRule):
    """Check parenthesis spacing (B4-003)."""

    # 括号前有空格
    SPACE_BEFORE_PAREN = re.compile(r"\s+[（(]")
    # 括号后有空格（中文环境）
    SPACE_AFTER_PAREN = re.compile(r"[）)]\s+(?=[\u4e00-\u9fff])")

    def __init__(self) -> None:
        super().__init__(
            rule_id="B4-003",
            category="B",
            subcategory="B4",
            severity="info",
            blocks_publish=False,
            can_auto_fix=True,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        # Check space before parenthesis
        for match in self.SPACE_BEFORE_PAREN.finditer(content):
            snippet_start = max(0, match.start() - 10)
            snippet_end = min(len(content), match.end() + 10)
            snippet = content[snippet_start:snippet_end]

            issues.append(
                ProofreadingIssue(
                    rule_id=self.rule_id,
                    category=self.category,
                    subcategory=self.subcategory,
                    message="括号格式：括号前不应有空格。",
                    suggestion="删除括号前的空格。",
                    severity=self.severity,
                    confidence=0.9,
                    can_auto_fix=self.can_auto_fix,
                    blocks_publish=self.blocks_publish,
                    source=RuleSource.SCRIPT,
                    attributed_by="B4_003_ParenthesisSpacingRule",
                    location={"offset": match.start()},
                    evidence=snippet,
                )
            )

        # Check space after parenthesis
        for match in self.SPACE_AFTER_PAREN.finditer(content):
            snippet_start = max(0, match.start() - 10)
            snippet_end = min(len(content), match.end() + 10)
            snippet = content[snippet_start:snippet_end]

            issues.append(
                ProofreadingIssue(
                    rule_id=self.rule_id,
                    category=self.category,
                    subcategory=self.subcategory,
                    message="括号格式：中文环境下括号后不应有空格。",
                    suggestion="删除括号后的空格。",
                    severity=self.severity,
                    confidence=0.9,
                    can_auto_fix=self.can_auto_fix,
                    blocks_publish=self.blocks_publish,
                    source=RuleSource.SCRIPT,
                    attributed_by="B4_003_ParenthesisSpacingRule",
                    location={"offset": match.start()},
                    evidence=snippet,
                )
            )
        return issues


class B4_004_ParenthesisInnerSpaceRule(DeterministicRule):
    """Check inner space in parenthesis (B4-004)."""

    # 括号内首尾有空格
    INNER_SPACE = re.compile(r"[（(]\s+|\s+[）)]")

    def __init__(self) -> None:
        super().__init__(
            rule_id="B4-004",
            category="B",
            subcategory="B4",
            severity="warning",
            blocks_publish=False,
            can_auto_fix=True,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        for match in self.INNER_SPACE.finditer(content):
            snippet_start = max(0, match.start() - 10)
            snippet_end = min(len(content), match.end() + 10)
            snippet = content[snippet_start:snippet_end]

            issues.append(
                ProofreadingIssue(
                    rule_id=self.rule_id,
                    category=self.category,
                    subcategory=self.subcategory,
                    message="括号格式：括号内首尾不应有空格。",
                    suggestion="删除括号内首尾的空格。",
                    severity=self.severity,
                    confidence=1.0,
                    can_auto_fix=self.can_auto_fix,
                    blocks_publish=self.blocks_publish,
                    source=RuleSource.SCRIPT,
                    attributed_by="B4_004_ParenthesisInnerSpaceRule",
                    location={"offset": match.start()},
                    evidence=snippet,
                )
            )
        return issues


class B5_003_QuoteMixRule(DeterministicRule):
    """Check single and double quote mixing (B5-003)."""

    # 在同一句子中混用单双引号
    QUOTE_MIX = re.compile(r'[""''][^""''。！？；]{1,30}[''"]')

    def __init__(self) -> None:
        super().__init__(
            rule_id="B5-003",
            category="B",
            subcategory="B5",
            severity="info",
            blocks_publish=False,
            can_auto_fix=False,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        for match in self.QUOTE_MIX.finditer(content):
            # Check if opening and closing quotes are different types
            opening = match.group()[0]
            closing = match.group()[-1]

            if (opening in '""' and closing in "''") or (opening in "''" and closing in '""'):
                snippet_start = max(0, match.start() - 10)
                snippet_end = min(len(content), match.end() + 10)
                snippet = content[snippet_start:snippet_end]

                issues.append(
                    ProofreadingIssue(
                        rule_id=self.rule_id,
                        category=self.category,
                        subcategory=self.subcategory,
                        message=f"引号使用：引号类型不匹配 '{opening}...{closing}'。",
                        suggestion="统一使用双引号或单引号。",
                        severity=self.severity,
                        confidence=0.9,
                        can_auto_fix=self.can_auto_fix,
                        blocks_publish=self.blocks_publish,
                        source=RuleSource.SCRIPT,
                        attributed_by="B5_003_QuoteMixRule",
                        location={"offset": match.start()},
                        evidence=snippet,
                    )
                )
        return issues


class B6_002_DunhaoMisuseRule(DeterministicRule):
    """Check dunhao misuse for non-parallel items (B6-002)."""

    # 顿号用于非并列成分（如动词短语间）
    DUNHAO_VERB = re.compile(r"[\u4e00-\u9fff]{2,4}、[\u4e00-\u9fff]{2,4}(?=[，。！？])")

    def __init__(self) -> None:
        super().__init__(
            rule_id="B6-002",
            category="B",
            subcategory="B6",
            severity="info",
            blocks_publish=False,
            can_auto_fix=False,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        for match in self.DUNHAO_VERB.finditer(content):
            snippet_start = max(0, match.start() - 15)
            snippet_end = min(len(content), match.end() + 15)
            snippet = content[snippet_start:snippet_end]

            issues.append(
                ProofreadingIssue(
                    rule_id=self.rule_id,
                    category=self.category,
                    subcategory=self.subcategory,
                    message="顿号使用：请确认是否为并列名词，动词短语间应使用逗号。",
                    suggestion="如果是动词短语或句子成分，应使用逗号「，」而非顿号「、」。",
                    severity=self.severity,
                    confidence=0.5,
                    can_auto_fix=self.can_auto_fix,
                    blocks_publish=self.blocks_publish,
                    source=RuleSource.SCRIPT,
                    attributed_by="B6_002_DunhaoMisuseRule",
                    location={"offset": match.start()},
                    evidence=snippet,
                )
            )
        return issues


class B6_003_IntervalMarkMisuseRule(DeterministicRule):
    """Check interval mark misuse (B6-003)."""

    # 间隔号误用检测（应用于姓名、日期等）
    INTERVAL_MISUSE = re.compile(r"[\u4e00-\u9fff]{1}·[\u4e00-\u9fff]{1}(?![\u4e00-\u9fff])")

    def __init__(self) -> None:
        super().__init__(
            rule_id="B6-003",
            category="B",
            subcategory="B6",
            severity="info",
            blocks_publish=False,
            can_auto_fix=False,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        for match in self.INTERVAL_MISUSE.finditer(content):
            snippet_start = max(0, match.start() - 10)
            snippet_end = min(len(content), match.end() + 10)
            snippet = content[snippet_start:snippet_end]

            issues.append(
                ProofreadingIssue(
                    rule_id=self.rule_id,
                    category=self.category,
                    subcategory=self.subcategory,
                    message=f"间隔号使用：'{match.group()}' 可能不需要间隔号。",
                    suggestion="间隔号主要用于外文名字、日期等，单字间通常不使用。",
                    severity=self.severity,
                    confidence=0.6,
                    can_auto_fix=self.can_auto_fix,
                    blocks_publish=self.blocks_publish,
                    source=RuleSource.SCRIPT,
                    attributed_by="B6_003_IntervalMarkMisuseRule",
                    location={"offset": match.start()},
                    evidence=snippet,
                )
            )
        return issues


class B7_003_HyphenFormatRule(DeterministicRule):
    """Check hyphen format in numbers (B7-003)."""

    # 数字范围应使用波浪号或连字符
    NUMBER_HYPHEN = re.compile(r"\d+-\d+")

    def __init__(self) -> None:
        super().__init__(
            rule_id="B7-003",
            category="B",
            subcategory="B7",
            severity="info",
            blocks_publish=False,
            can_auto_fix=False,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        for match in self.NUMBER_HYPHEN.finditer(content):
            snippet_start = max(0, match.start() - 10)
            snippet_end = min(len(content), match.end() + 10)
            snippet = content[snippet_start:snippet_end]

            issues.append(
                ProofreadingIssue(
                    rule_id=self.rule_id,
                    category=self.category,
                    subcategory=self.subcategory,
                    message=f"连字符使用：数字范围 '{match.group()}' 建议使用波浪号。",
                    suggestion="数字范围建议使用波浪号「～」，如「1～10」。",
                    severity=self.severity,
                    confidence=0.7,
                    can_auto_fix=self.can_auto_fix,
                    blocks_publish=self.blocks_publish,
                    source=RuleSource.SCRIPT,
                    attributed_by="B7_003_HyphenFormatRule",
                    location={"offset": match.start()},
                    evidence=snippet,
                )
            )
        return issues


class B7_005_EllipsisDengRule(DeterministicRule):
    """Check ellipsis and 'deng' duplication (B7-005)."""

    # 省略号与"等"重复
    ELLIPSIS_DENG = re.compile(r"[…\.]{2,}等|等[…\.]{2,}")

    def __init__(self) -> None:
        super().__init__(
            rule_id="B7-005",
            category="B",
            subcategory="B7",
            severity="warning",
            blocks_publish=False,
            can_auto_fix=False,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        for match in self.ELLIPSIS_DENG.finditer(content):
            snippet_start = max(0, match.start() - 10)
            snippet_end = min(len(content), match.end() + 10)
            snippet = content[snippet_start:snippet_end]

            issues.append(
                ProofreadingIssue(
                    rule_id=self.rule_id,
                    category=self.category,
                    subcategory=self.subcategory,
                    message=f"省略号使用：'{match.group()}' 省略号与「等」重复。",
                    suggestion="省略号与「等」语义重复，只使用其一即可。",
                    severity=self.severity,
                    confidence=1.0,
                    can_auto_fix=self.can_auto_fix,
                    blocks_publish=self.blocks_publish,
                    source=RuleSource.SCRIPT,
                    attributed_by="B7_005_EllipsisDengRule",
                    location={"offset": match.start()},
                    evidence=snippet,
                )
            )
        return issues


class B7_006_DashLengthRule(DeterministicRule):
    """Check dash length (B7-006)."""

    # 破折号长度检测（应为两个em dash）
    SHORT_DASH = re.compile(r"(?<![——])—(?![——])")

    def __init__(self) -> None:
        super().__init__(
            rule_id="B7-006",
            category="B",
            subcategory="B7",
            severity="info",
            blocks_publish=False,
            can_auto_fix=True,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        for match in self.SHORT_DASH.finditer(content):
            snippet_start = max(0, match.start() - 10)
            snippet_end = min(len(content), match.end() + 10)
            snippet = content[snippet_start:snippet_end]

            issues.append(
                ProofreadingIssue(
                    rule_id=self.rule_id,
                    category=self.category,
                    subcategory=self.subcategory,
                    message="破折号长度：破折号应为两个字符长度「——」。",
                    suggestion="将单个 '—' 改为 '——'。",
                    severity=self.severity,
                    confidence=0.9,
                    can_auto_fix=self.can_auto_fix,
                    blocks_publish=self.blocks_publish,
                    source=RuleSource.SCRIPT,
                    attributed_by="B7_006_DashLengthRule",
                    location={"offset": match.start()},
                    evidence=snippet,
                )
            )
        return issues


class B1_011_ParagraphEndPunctuationRule(DeterministicRule):
    """Check paragraph ending punctuation (B1-011)."""

    # 段落末尾缺少标点
    PARA_NO_PUNCT = re.compile(r"[\u4e00-\u9fff]\n")

    def __init__(self) -> None:
        super().__init__(
            rule_id="B1-011",
            category="B",
            subcategory="B1",
            severity="warning",
            blocks_publish=False,
            can_auto_fix=False,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        for match in self.PARA_NO_PUNCT.finditer(content):
            # Check if it's really a paragraph end (not a list item or header)
            snippet_start = max(0, match.start() - 20)
            snippet_end = min(len(content), match.end() + 5)
            snippet = content[snippet_start:snippet_end]

            issues.append(
                ProofreadingIssue(
                    rule_id=self.rule_id,
                    category=self.category,
                    subcategory=self.subcategory,
                    message="段落标点：段落结尾可能缺少标点符号。",
                    suggestion="段落结尾应添加句号、问号或感叹号。",
                    severity=self.severity,
                    confidence=0.6,
                    can_auto_fix=self.can_auto_fix,
                    blocks_publish=self.blocks_publish,
                    source=RuleSource.SCRIPT,
                    attributed_by="B1_011_ParagraphEndPunctuationRule",
                    location={"offset": match.start()},
                    evidence=snippet,
                )
            )
        return issues


class B1_012_PunctuationStackingRule(DeterministicRule):
    """Check punctuation stacking (B1-012)."""

    # 标点符号堆叠（除省略号、破折号外）
    PUNCT_STACK = re.compile(r"[，。！？；：、][\s]*[，。！？；：、]")

    def __init__(self) -> None:
        super().__init__(
            rule_id="B1-012",
            category="B",
            subcategory="B1",
            severity="warning",
            blocks_publish=False,
            can_auto_fix=False,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        for match in self.PUNCT_STACK.finditer(content):
            snippet_start = max(0, match.start() - 10)
            snippet_end = min(len(content), match.end() + 10)
            snippet = content[snippet_start:snippet_end]

            issues.append(
                ProofreadingIssue(
                    rule_id=self.rule_id,
                    category=self.category,
                    subcategory=self.subcategory,
                    message=f"标点堆叠：检测到标点符号堆叠 '{match.group()}'。",
                    suggestion="删除多余的标点符号。",
                    severity=self.severity,
                    confidence=0.9,
                    can_auto_fix=self.can_auto_fix,
                    blocks_publish=self.blocks_publish,
                    source=RuleSource.SCRIPT,
                    attributed_by="B1_012_PunctuationStackingRule",
                    location={"offset": match.start()},
                    evidence=snippet,
                )
            )
        return issues


# ============================================================================
# B1 Extended - Additional Basic Punctuation Rules
# ============================================================================


class B1_013_EnglishPunctuationInChineseRule(DeterministicRule):
    """Check for English punctuation misuse in Chinese text (B1-013)."""

    # 英文标点在中文段落中
    ENG_PUNCT_IN_CN = re.compile(r'[\u4e00-\u9fff][,;:!?][\u4e00-\u9fff]')

    def __init__(self) -> None:
        super().__init__(
            rule_id="B1-013",
            category="B",
            subcategory="B1",
            severity="warning",
            blocks_publish=False,
            can_auto_fix=True,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        for match in self.ENG_PUNCT_IN_CN.finditer(content):
            snippet = content[max(0, match.start() - 10) : match.end() + 10]
            punct = match.group()[1]
            chinese_punct = {',': '，', ';': '；', ':': '：', '!': '！', '?': '？'}

            issues.append(
                ProofreadingIssue(
                    rule_id=self.rule_id,
                    category=self.category,
                    subcategory=self.subcategory,
                    message=f"中文文本中使用了英文标点 '{punct}'。",
                    suggestion=f"改为中文标点 '{chinese_punct.get(punct, punct)}'。",
                    severity=self.severity,
                    confidence=0.9,
                    can_auto_fix=self.can_auto_fix,
                    blocks_publish=self.blocks_publish,
                    source=RuleSource.SCRIPT,
                    attributed_by="B1_013_EnglishPunctuationInChineseRule",
                    location={"offset": match.start()},
                    evidence=snippet,
                )
            )
        return issues


class B1_014_PunctuationLeadingSpaceRule(DeterministicRule):
    """Check for unnecessary space before punctuation (B1-014)."""

    PUNCT_LEADING_SPACE = re.compile(r'\s+[，。！？；：、]')

    def __init__(self) -> None:
        super().__init__(
            rule_id="B1-014",
            category="B",
            subcategory="B1",
            severity="warning",
            blocks_publish=False,
            can_auto_fix=True,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        for match in self.PUNCT_LEADING_SPACE.finditer(content):
            snippet = content[max(0, match.start() - 10) : match.end() + 10]

            issues.append(
                ProofreadingIssue(
                    rule_id=self.rule_id,
                    category=self.category,
                    subcategory=self.subcategory,
                    message=f"标点符号 '{match.group().strip()}' 前有多余空格。",
                    suggestion="删除标点符号前的空格。",
                    severity=self.severity,
                    confidence=1.0,
                    can_auto_fix=self.can_auto_fix,
                    blocks_publish=self.blocks_publish,
                    source=RuleSource.SCRIPT,
                    attributed_by="B1_014_PunctuationLeadingSpaceRule",
                    location={"offset": match.start()},
                    evidence=snippet,
                )
            )
        return issues


# ============================================================================
# B2 Extended - Additional Comma and Dunhao Rules
# ============================================================================


class B2_008_DunhaoInMixedTextRule(DeterministicRule):
    """Check dunhao usage in Chinese-English mixed text (B2-008)."""

    DUNHAO_WITH_ENG = re.compile(r'[a-zA-Z]+、[a-zA-Z]+')

    def __init__(self) -> None:
        super().__init__(
            rule_id="B2-008",
            category="B",
            subcategory="B2",
            severity="warning",
            blocks_publish=False,
            can_auto_fix=True,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        for match in self.DUNHAO_WITH_ENG.finditer(content):
            snippet = content[max(0, match.start() - 10) : match.end() + 10]

            issues.append(
                ProofreadingIssue(
                    rule_id=self.rule_id,
                    category=self.category,
                    subcategory=self.subcategory,
                    message=f"英文词汇间使用了顿号：'{match.group()}'。",
                    suggestion="英文词汇间应使用逗号（,）或顿号改为中文词。",
                    severity=self.severity,
                    confidence=0.85,
                    can_auto_fix=self.can_auto_fix,
                    blocks_publish=self.blocks_publish,
                    source=RuleSource.SCRIPT,
                    attributed_by="B2_008_DunhaoInMixedTextRule",
                    location={"offset": match.start()},
                    evidence=snippet,
                )
            )
        return issues


class B2_009_OxfordCommaRule(DeterministicRule):
    """Check for Oxford comma usage (B2-009)."""

    # 检测"A、B和C"模式中缺少逗号
    OXFORD_PATTERN = re.compile(r'[\u4e00-\u9fff]{1,5}、[\u4e00-\u9fff]{1,5}[和与及][\u4e00-\u9fff]{1,5}')

    def __init__(self) -> None:
        super().__init__(
            rule_id="B2-009",
            category="B",
            subcategory="B2",
            severity="info",
            blocks_publish=False,
            can_auto_fix=False,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        for match in self.OXFORD_PATTERN.finditer(content):
            snippet = content[max(0, match.start() - 10) : match.end() + 10]

            issues.append(
                ProofreadingIssue(
                    rule_id=self.rule_id,
                    category=self.category,
                    subcategory=self.subcategory,
                    message=f"并列列举最后一项前可考虑添加顿号：'{match.group()}'。",
                    suggestion="在'和/与/及'之前可添加顿号以保持一致性（可选）。",
                    severity=self.severity,
                    confidence=0.7,
                    can_auto_fix=self.can_auto_fix,
                    blocks_publish=self.blocks_publish,
                    source=RuleSource.SCRIPT,
                    attributed_by="B2_009_OxfordCommaRule",
                    location={"offset": match.start()},
                    evidence=snippet,
                )
            )
        return issues


class B2_010_MissingDunhaoRule(DeterministicRule):
    """Check for missing dunhao in short parallel phrases (B2-010)."""

    # 检测短并列词组间缺顿号
    PARALLEL_NO_DUNHAO = re.compile(r'[\u4e00-\u9fff]{2,3}\s[\u4e00-\u9fff]{2,3}(?:\s[\u4e00-\u9fff]{2,3})+')

    def __init__(self) -> None:
        super().__init__(
            rule_id="B2-010",
            category="B",
            subcategory="B2",
            severity="info",
            blocks_publish=False,
            can_auto_fix=False,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        for match in self.PARALLEL_NO_DUNHAO.finditer(content):
            snippet = content[max(0, match.start() - 10) : match.end() + 10]

            issues.append(
                ProofreadingIssue(
                    rule_id=self.rule_id,
                    category=self.category,
                    subcategory=self.subcategory,
                    message=f"短并列词组间可能缺少顿号：'{match.group()}'。",
                    suggestion="如果是并列关系，应使用顿号分隔。",
                    severity=self.severity,
                    confidence=0.6,
                    can_auto_fix=self.can_auto_fix,
                    blocks_publish=self.blocks_publish,
                    source=RuleSource.SCRIPT,
                    attributed_by="B2_010_MissingDunhaoRule",
                    location={"offset": match.start()},
                    evidence=snippet,
                )
            )
        return issues


class B2_011_DunhaoInLongClausesRule(DeterministicRule):
    """Check for dunhao misuse in long parallel clauses (B2-011)."""

    # 检测长句间使用顿号
    LONG_DUNHAO = re.compile(r'[\u4e00-\u9fff，]{10,}、[\u4e00-\u9fff，]{10,}')

    def __init__(self) -> None:
        super().__init__(
            rule_id="B2-011",
            category="B",
            subcategory="B2",
            severity="warning",
            blocks_publish=False,
            can_auto_fix=False,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        for match in self.LONG_DUNHAO.finditer(content):
            snippet = content[max(0, match.start() - 10) : match.end() + 10]

            issues.append(
                ProofreadingIssue(
                    rule_id=self.rule_id,
                    category=self.category,
                    subcategory=self.subcategory,
                    message="并列长句间不应使用顿号。",
                    suggestion="较长的并列成分应使用逗号或分号，而非顿号。",
                    severity=self.severity,
                    confidence=0.8,
                    can_auto_fix=self.can_auto_fix,
                    blocks_publish=self.blocks_publish,
                    source=RuleSource.SCRIPT,
                    attributed_by="B2_011_DunhaoInLongClausesRule",
                    location={"offset": match.start()},
                    evidence=snippet,
                )
            )
        return issues


class B2_012_CommaInShortPhrasesRule(DeterministicRule):
    """Check for comma misuse in short parallel words (B2-012)."""

    # 检测短词组间使用逗号
    SHORT_COMMA = re.compile(r'[\u4e00-\u9fff]{2,4}，[\u4e00-\u9fff]{2,4}(?:，[\u4e00-\u9fff]{2,4})+')

    def __init__(self) -> None:
        super().__init__(
            rule_id="B2-012",
            category="B",
            subcategory="B2",
            severity="info",
            blocks_publish=False,
            can_auto_fix=False,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        for match in self.SHORT_COMMA.finditer(content):
            # 排除包含动词的情况
            if any(verb in match.group() for verb in ['是', '为', '有', '在', '说', '做', '去', '来']):
                continue

            snippet = content[max(0, match.start() - 10) : match.end() + 10]

            issues.append(
                ProofreadingIssue(
                    rule_id=self.rule_id,
                    category=self.category,
                    subcategory=self.subcategory,
                    message=f"短并列词组间可考虑使用顿号：'{match.group()}'。",
                    suggestion="短并列词组（2-4字）通常使用顿号，而非逗号。",
                    severity=self.severity,
                    confidence=0.7,
                    can_auto_fix=self.can_auto_fix,
                    blocks_publish=self.blocks_publish,
                    source=RuleSource.SCRIPT,
                    attributed_by="B2_012_CommaInShortPhrasesRule",
                    location={"offset": match.start()},
                    evidence=snippet,
                )
            )
        return issues


class B2_013_CommaSpacingEnglishRule(DeterministicRule):
    """Check comma spacing in English text (B2-013)."""

    # 英文中逗号后缺空格
    ENG_COMMA_NO_SPACE = re.compile(r',[a-zA-Z]')

    def __init__(self) -> None:
        super().__init__(
            rule_id="B2-013",
            category="B",
            subcategory="B2",
            severity="warning",
            blocks_publish=False,
            can_auto_fix=True,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        for match in self.ENG_COMMA_NO_SPACE.finditer(content):
            snippet = content[max(0, match.start() - 10) : match.end() + 10]

            issues.append(
                ProofreadingIssue(
                    rule_id=self.rule_id,
                    category=self.category,
                    subcategory=self.subcategory,
                    message=f"英文逗号后缺少空格：'{match.group()}'。",
                    suggestion="英文逗号后应添加空格。",
                    severity=self.severity,
                    confidence=0.95,
                    can_auto_fix=self.can_auto_fix,
                    blocks_publish=self.blocks_publish,
                    source=RuleSource.SCRIPT,
                    attributed_by="B2_013_CommaSpacingEnglishRule",
                    location={"offset": match.start()},
                    evidence=snippet,
                )
            )
        return issues


class B2_014_DunhaoWithDengRule(DeterministicRule):
    """Check for dunhao enumeration ending with 等 (B2-014)."""

    DUNHAO_DENG = re.compile(r'[\u4e00-\u9fff]{2,5}、[\u4e00-\u9fff]{2,5}(?:、[\u4e00-\u9fff]{2,5})*等')

    def __init__(self) -> None:
        super().__init__(
            rule_id="B2-014",
            category="B",
            subcategory="B2",
            severity="info",
            blocks_publish=False,
            can_auto_fix=False,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        for match in self.DUNHAO_DENG.finditer(content):
            snippet = content[max(0, match.start() - 10) : match.end() + 10]

            issues.append(
                ProofreadingIssue(
                    rule_id=self.rule_id,
                    category=self.category,
                    subcategory=self.subcategory,
                    message=f"顿号列举后使用'等'：'{match.group()}'。",
                    suggestion="可在'等'字前加顿号以保持一致性，或根据风格指南决定。",
                    severity=self.severity,
                    confidence=0.8,
                    can_auto_fix=self.can_auto_fix,
                    blocks_publish=self.blocks_publish,
                    source=RuleSource.SCRIPT,
                    attributed_by="B2_014_DunhaoWithDengRule",
                    location={"offset": match.start()},
                    evidence=snippet,
                )
            )
        return issues


class B2_015_CommaSemicolonMixRule(DeterministicRule):
    """Check for inconsistent comma and semicolon usage (B2-015)."""

    # 检测同一句中逗号和分号混用的不一致性
    COMMA_SEMI_MIX = re.compile(r'[^。！？；]{20,}；[^。！？]{10,}，[^。！？]{10,}；')

    def __init__(self) -> None:
        super().__init__(
            rule_id="B2-015",
            category="B",
            subcategory="B2",
            severity="info",
            blocks_publish=False,
            can_auto_fix=False,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        for match in self.COMMA_SEMI_MIX.finditer(content):
            snippet = content[max(0, match.start() - 10) : match.end() + 10]

            issues.append(
                ProofreadingIssue(
                    rule_id=self.rule_id,
                    category=self.category,
                    subcategory=self.subcategory,
                    message="同一长句中逗号和分号混用可能不一致。",
                    suggestion="检查是否应统一使用分号，或调整句子结构。",
                    severity=self.severity,
                    confidence=0.6,
                    can_auto_fix=self.can_auto_fix,
                    blocks_publish=self.blocks_publish,
                    source=RuleSource.SCRIPT,
                    attributed_by="B2_015_CommaSemicolonMixRule",
                    location={"offset": match.start()},
                    evidence=snippet,
                )
            )
        return issues


# ============================================================================
# B3 Extended - Additional Quote and Book Title Rules
# ============================================================================


class B3_006_QuoteMisuseRule(DeterministicRule):
    """Check for quotation mark misuse in non-quotation contexts (B3-006)."""

    # 检测引号用于强调而非引用
    QUOTE_EMPHASIS = re.compile(r'[""][\u4e00-\u9fff]{1,3}[""](?![说道曰云])')

    def __init__(self) -> None:
        super().__init__(
            rule_id="B3-006",
            category="B",
            subcategory="B3",
            severity="info",
            blocks_publish=False,
            can_auto_fix=False,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        for match in self.QUOTE_EMPHASIS.finditer(content):
            snippet = content[max(0, match.start() - 10) : match.end() + 10]

            issues.append(
                ProofreadingIssue(
                    rule_id=self.rule_id,
                    category=self.category,
                    subcategory=self.subcategory,
                    message=f"引号可能用于强调而非引用：'{match.group()}'。",
                    suggestion="引号主要用于引用，强调可考虑使用着重号或其他方式。",
                    severity=self.severity,
                    confidence=0.6,
                    can_auto_fix=self.can_auto_fix,
                    blocks_publish=self.blocks_publish,
                    source=RuleSource.SCRIPT,
                    attributed_by="B3_006_QuoteMisuseRule",
                    location={"offset": match.start()},
                    evidence=snippet,
                )
            )
        return issues


class B3_007_BookTitleOveruseRule(DeterministicRule):
    """Check for book title mark overuse (B3-007)."""

    # 检测书名号用于非作品名
    BOOK_TITLE_PATTERN = re.compile(r'《[\u4e00-\u9fff]{1,4}》')

    def __init__(self) -> None:
        super().__init__(
            rule_id="B3-007",
            category="B",
            subcategory="B3",
            severity="info",
            blocks_publish=False,
            can_auto_fix=False,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        # 常见的非作品名词汇
        non_works = ['方法', '理论', '概念', '原则', '规则', '标准', '模式', '体系']

        for match in self.BOOK_TITLE_PATTERN.finditer(content):
            inner_text = match.group()[1:-1]  # 去掉书名号
            if inner_text in non_works:
                snippet = content[max(0, match.start() - 10) : match.end() + 10]

                issues.append(
                    ProofreadingIssue(
                        rule_id=self.rule_id,
                        category=self.category,
                        subcategory=self.subcategory,
                        message=f"书名号可能用于非作品名：'{match.group()}'。",
                        suggestion="书名号应仅用于书籍、文章、影视等作品名称。",
                        severity=self.severity,
                        confidence=0.7,
                        can_auto_fix=self.can_auto_fix,
                        blocks_publish=self.blocks_publish,
                        source=RuleSource.SCRIPT,
                        attributed_by="B3_007_BookTitleOveruseRule",
                        location={"offset": match.start()},
                        evidence=snippet,
                    )
                )
        return issues


# ============================================================================
# B4 Extended - Additional Parenthesis Rules
# ============================================================================


class B4_005_MixedParenthesesRule(DeterministicRule):
    """Check for mixed Chinese and English parentheses (B4-005)."""

    # 检测中英文括号混用
    CN_OPEN_ENG_CLOSE = re.compile(r'（[^）]{1,20}\)')
    ENG_OPEN_CN_CLOSE = re.compile(r'\([^)]{1,20}）')

    def __init__(self) -> None:
        super().__init__(
            rule_id="B4-005",
            category="B",
            subcategory="B4",
            severity="warning",
            blocks_publish=False,
            can_auto_fix=True,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        for match in self.CN_OPEN_ENG_CLOSE.finditer(content):
            snippet = content[max(0, match.start() - 10) : match.end() + 10]

            issues.append(
                ProofreadingIssue(
                    rule_id=self.rule_id,
                    category=self.category,
                    subcategory=self.subcategory,
                    message=f"中文左括号配英文右括号：'{match.group()}'。",
                    suggestion="括号应成对使用，统一为中文括号（）或英文括号()。",
                    severity=self.severity,
                    confidence=1.0,
                    can_auto_fix=self.can_auto_fix,
                    blocks_publish=self.blocks_publish,
                    source=RuleSource.SCRIPT,
                    attributed_by="B4_005_MixedParenthesesRule",
                    location={"offset": match.start()},
                    evidence=snippet,
                )
            )

        for match in self.ENG_OPEN_CN_CLOSE.finditer(content):
            snippet = content[max(0, match.start() - 10) : match.end() + 10]

            issues.append(
                ProofreadingIssue(
                    rule_id=self.rule_id,
                    category=self.category,
                    subcategory=self.subcategory,
                    message=f"英文左括号配中文右括号：'{match.group()}'。",
                    suggestion="括号应成对使用，统一为中文括号（）或英文括号()。",
                    severity=self.severity,
                    confidence=1.0,
                    can_auto_fix=self.can_auto_fix,
                    blocks_publish=self.blocks_publish,
                    source=RuleSource.SCRIPT,
                    attributed_by="B4_005_MixedParenthesesRule",
                    location={"offset": match.start()},
                    evidence=snippet,
                )
            )
        return issues


class B4_006_NestedParenthesesRule(DeterministicRule):
    """Check for deeply nested parentheses (B4-006)."""

    # 检测括号嵌套
    NESTED_PAREN = re.compile(r'[（(][^）)]{0,50}[（(][^）)]{0,50}[）)][^）)]{0,50}[）)]')

    def __init__(self) -> None:
        super().__init__(
            rule_id="B4-006",
            category="B",
            subcategory="B4",
            severity="info",
            blocks_publish=False,
            can_auto_fix=False,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        for match in self.NESTED_PAREN.finditer(content):
            snippet = content[max(0, match.start() - 10) : match.end() + 10]

            issues.append(
                ProofreadingIssue(
                    rule_id=self.rule_id,
                    category=self.category,
                    subcategory=self.subcategory,
                    message="检测到括号嵌套使用。",
                    suggestion="过度嵌套会影响可读性，考虑改写句子结构或使用不同层级的标点。",
                    severity=self.severity,
                    confidence=0.85,
                    can_auto_fix=self.can_auto_fix,
                    blocks_publish=self.blocks_publish,
                    source=RuleSource.SCRIPT,
                    attributed_by="B4_006_NestedParenthesesRule",
                    location={"offset": match.start()},
                    evidence=snippet,
                )
            )
        return issues


# ============================================================================
# B7 Extended - Additional Dash and Hyphen Rules
# ============================================================================


class B7_007_DashForParallelRule(DeterministicRule):
    """Check for dash misuse in parallel components (B7-007)."""

    # 检测破折号用于并列成分
    DASH_PARALLEL = re.compile(r'[\u4e00-\u9fff]{2,6}—[\u4e00-\u9fff]{2,6}—[\u4e00-\u9fff]{2,6}')

    def __init__(self) -> None:
        super().__init__(
            rule_id="B7-007",
            category="B",
            subcategory="B7",
            severity="info",
            blocks_publish=False,
            can_auto_fix=False,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        for match in self.DASH_PARALLEL.finditer(content):
            snippet = content[max(0, match.start() - 10) : match.end() + 10]

            issues.append(
                ProofreadingIssue(
                    rule_id=self.rule_id,
                    category=self.category,
                    subcategory=self.subcategory,
                    message=f"破折号可能用于并列成分：'{match.group()}'。",
                    suggestion="并列成分应使用顿号或逗号，破折号主要用于解释说明。",
                    severity=self.severity,
                    confidence=0.75,
                    can_auto_fix=self.can_auto_fix,
                    blocks_publish=self.blocks_publish,
                    source=RuleSource.SCRIPT,
                    attributed_by="B7_007_DashForParallelRule",
                    location={"offset": match.start()},
                    evidence=snippet,
                )
            )
        return issues


class B7_008_HyphenInconsistencyRule(DeterministicRule):
    """Check for inconsistent hyphen format (B7-008)."""

    # 检测短横线格式不统一
    MIXED_HYPHENS = re.compile(r'\d+[-–—]\d+')

    def __init__(self) -> None:
        super().__init__(
            rule_id="B7-008",
            category="B",
            subcategory="B7",
            severity="warning",
            blocks_publish=False,
            can_auto_fix=True,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        # 统计使用的连接符类型
        hyphens_used = set()
        for match in self.MIXED_HYPHENS.finditer(content):
            hyphen = match.group()[len(str(int(match.group().split('-')[0] if '-' in match.group() else
                                          match.group().split('–')[0] if '–' in match.group() else
                                          match.group().split('—')[0]))):-len(str(int(match.group().split('-')[-1] if '-' in match.group() else
                                          match.group().split('–')[-1] if '–' in match.group() else
                                          match.group().split('—')[-1])))]
            hyphens_used.add(hyphen)

        # 如果使用了多种连接符，报告不一致
        if len(hyphens_used) > 1:
            snippet = content[:100]

            issues.append(
                ProofreadingIssue(
                    rule_id=self.rule_id,
                    category=self.category,
                    subcategory=self.subcategory,
                    message=f"数字范围使用了多种连接符：{hyphens_used}。",
                    suggestion="建议统一使用半角连接号（-）表示数字范围。",
                    severity=self.severity,
                    confidence=0.9,
                    can_auto_fix=self.can_auto_fix,
                    blocks_publish=self.blocks_publish,
                    source=RuleSource.SCRIPT,
                    attributed_by="B7_008_HyphenInconsistencyRule",
                    location={"offset": 0},
                    evidence=snippet,
                )
            )
        return issues


class B7_009_EllipsisMisplacementRule(DeterministicRule):
    """Check for ellipsis placement errors (B7-009)."""

    # 检测省略号在句首
    ELLIPSIS_START = re.compile(r'^……|[。！？]\s*……')

    def __init__(self) -> None:
        super().__init__(
            rule_id="B7-009",
            category="B",
            subcategory="B7",
            severity="info",
            blocks_publish=False,
            can_auto_fix=False,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        for match in self.ELLIPSIS_START.finditer(content):
            snippet = content[max(0, match.start() - 5) : match.end() + 20]

            issues.append(
                ProofreadingIssue(
                    rule_id=self.rule_id,
                    category=self.category,
                    subcategory=self.subcategory,
                    message="省略号出现在句首或独立使用。",
                    suggestion="省略号通常用于句中或句末，表示省略或停顿，句首使用较少见。",
                    severity=self.severity,
                    confidence=0.7,
                    can_auto_fix=self.can_auto_fix,
                    blocks_publish=self.blocks_publish,
                    source=RuleSource.SCRIPT,
                    attributed_by="B7_009_EllipsisMisplacementRule",
                    location={"offset": match.start()},
                    evidence=snippet,
                )
            )
        return issues


# ============================================================================
# B8 New - Whitespace Usage Rules
# ============================================================================


class B8_001_ExcessiveChineseSpacingRule(DeterministicRule):
    """Check for excessive spacing between Chinese characters (B8-001)."""

    # 检测中文字符间多余空格
    CN_SPACING = re.compile(r'[\u4e00-\u9fff]\s{2,}[\u4e00-\u9fff]')

    def __init__(self) -> None:
        super().__init__(
            rule_id="B8-001",
            category="B",
            subcategory="B8",
            severity="warning",
            blocks_publish=False,
            can_auto_fix=True,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        for match in self.CN_SPACING.finditer(content):
            snippet = content[max(0, match.start() - 10) : match.end() + 10]

            issues.append(
                ProofreadingIssue(
                    rule_id=self.rule_id,
                    category=self.category,
                    subcategory=self.subcategory,
                    message=f"中文字符间有多余空格：'{match.group()}'。",
                    suggestion="删除中文字符间的多余空格。",
                    severity=self.severity,
                    confidence=0.95,
                    can_auto_fix=self.can_auto_fix,
                    blocks_publish=self.blocks_publish,
                    source=RuleSource.SCRIPT,
                    attributed_by="B8_001_ExcessiveChineseSpacingRule",
                    location={"offset": match.start()},
                    evidence=snippet,
                )
            )
        return issues


class B8_002_ChineseEnglishSpacingRule(DeterministicRule):
    """Check for missing space between Chinese and English (B8-002)."""

    # 检测中英文间缺空格（可选规则，根据风格指南决定）
    CN_ENG_NO_SPACE = re.compile(r'[\u4e00-\u9fff][a-zA-Z]|[a-zA-Z][\u4e00-\u9fff]')

    def __init__(self) -> None:
        super().__init__(
            rule_id="B8-002",
            category="B",
            subcategory="B8",
            severity="info",
            blocks_publish=False,
            can_auto_fix=True,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        for match in self.CN_ENG_NO_SPACE.finditer(content):
            # 排除特定场景：单位、代码、URL等
            if any(pattern in content[max(0, match.start()-5):match.end()+5]
                   for pattern in ['http', 'www', 'kg', 'km', 'cm', 'mm', 'ml', 'GB', 'MB', 'KB']):
                continue

            snippet = content[max(0, match.start() - 10) : match.end() + 10]

            issues.append(
                ProofreadingIssue(
                    rule_id=self.rule_id,
                    category=self.category,
                    subcategory=self.subcategory,
                    message=f"中英文之间可能缺少空格：'{match.group()}'。",
                    suggestion="根据排版风格，中英文之间可添加空格（可选）。",
                    severity=self.severity,
                    confidence=0.6,
                    can_auto_fix=self.can_auto_fix,
                    blocks_publish=self.blocks_publish,
                    source=RuleSource.SCRIPT,
                    attributed_by="B8_002_ChineseEnglishSpacingRule",
                    location={"offset": match.start()},
                    evidence=snippet,
                )
            )
        return issues


class B8_003_LineSpacingRule(DeterministicRule):
    """Check for whitespace at line start/end (B8-003)."""

    # 检测行首行末空格
    LINE_SPACING = re.compile(r'^\s+|\s+$', re.MULTILINE)

    def __init__(self) -> None:
        super().__init__(
            rule_id="B8-003",
            category="B",
            subcategory="B8",
            severity="info",
            blocks_publish=False,
            can_auto_fix=True,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line != line.strip() and line.strip():  # 有内容但有空格
                snippet = line[:50]

                issues.append(
                    ProofreadingIssue(
                        rule_id=self.rule_id,
                        category=self.category,
                        subcategory=self.subcategory,
                        message=f"第 {i+1} 行存在行首或行末空格。",
                        suggestion="删除行首和行末的空格。",
                        severity=self.severity,
                        confidence=1.0,
                        can_auto_fix=self.can_auto_fix,
                        blocks_publish=self.blocks_publish,
                        source=RuleSource.SCRIPT,
                        attributed_by="B8_003_LineSpacingRule",
                        location={"line": i + 1},
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


class A1_024_QuanRule(UnifiedTermRule):
    """勸 统一写法."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A1-024",
            wrong_pattern=r"勸",
            correct_form="劝",
            description="'勸' 应统一为 '劝'（劝说、劝告等）。",
        )


class A1_025_RangRule(UnifiedTermRule):
    """讓 统一写法."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A1-025",
            wrong_pattern=r"讓",
            correct_form="让",
            description="'讓' 应统一为 '让'（让步、让位等）。",
        )


class A1_026_ReRule(UnifiedTermRule):
    """熱 统一写法."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A1-026",
            wrong_pattern=r"熱",
            correct_form="热",
            description="'熱' 应统一为 '热'（热情、热爱等）。",
        )


class A1_027_RenRule(UnifiedTermRule):
    """認 统一写法."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A1-027",
            wrong_pattern=r"認",
            correct_form="认",
            description="'認' 应统一为 '认'（认识、认可等）。",
        )


class A1_028_RongRule(UnifiedTermRule):
    """榮 统一写法."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A1-028",
            wrong_pattern=r"榮",
            correct_form="荣",
            description="'榮' 应统一为 '荣'（光荣、荣誉等）。",
        )


class A1_029_SaiRule(UnifiedTermRule):
    """賽 统一写法."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A1-029",
            wrong_pattern=r"賽",
            correct_form="赛",
            description="'賽' 应统一为 '赛'（比赛、赛跑等）。",
        )


class A1_030_ShanRule(UnifiedTermRule):
    """閃 统一写法."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A1-030",
            wrong_pattern=r"閃",
            correct_form="闪",
            description="'閃' 应统一为 '闪'（闪光、闪电等）。",
        )


class A1_031_ShengRule(UnifiedTermRule):
    """聲 统一写法."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A1-031",
            wrong_pattern=r"聲",
            correct_form="声",
            description="'聲' 应统一为 '声'（声音、声明等）。",
        )


class A1_032_ShiRule(UnifiedTermRule):
    """適 统一写法."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A1-032",
            wrong_pattern=r"適",
            correct_form="适",
            description="'適' 应统一为 '适'（适合、适应等）。",
        )


class A1_033_ShouRule(UnifiedTermRule):
    """壽 统一写法."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A1-033",
            wrong_pattern=r"壽",
            correct_form="寿",
            description="'壽' 应统一为 '寿'（长寿、寿命等）。",
        )


class A1_034_ShuRule(UnifiedTermRule):
    """術 统一写法."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A1-034",
            wrong_pattern=r"術",
            correct_form="术",
            description="'術' 应统一为 '术'（技术、艺术等）。",
        )


class A1_035_ShuaiRule(UnifiedTermRule):
    """帥 统一写法."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A1-035",
            wrong_pattern=r"帥",
            correct_form="帅",
            description="'帥' 应统一为 '帅'（帅气、元帅等）。",
        )


class A1_036_ShunRule(UnifiedTermRule):
    """順 统一写法."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A1-036",
            wrong_pattern=r"順",
            correct_form="顺",
            description="'順' 应统一为 '顺'（顺利、顺序等）。",
        )


class A1_037_ShuoRule(UnifiedTermRule):
    """説/說 统一写法."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A1-037",
            wrong_pattern=r"[説說]",
            correct_form="说",
            description="'説' 或 '說' 应统一为 '说'（说话、说明等）。",
        )


class A1_038_SiRule(UnifiedTermRule):
    """絲 统一写法."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A1-038",
            wrong_pattern=r"絲",
            correct_form="丝",
            description="'絲' 应统一为 '丝'（丝绸、丝毫等）。",
        )


class A1_039_SongRule(UnifiedTermRule):
    """鬆 统一写法."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A1-039",
            wrong_pattern=r"鬆",
            correct_form="松",
            description="'鬆' 应统一为 '松'（轻松、松弛等，表示「不紧」时）。",
        )


class A1_040_TaiRule(UnifiedTermRule):
    """臺/檯/枱 统一写法."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A1-040",
            wrong_pattern=r"[臺檯枱]",
            correct_form="台",
            description="'臺'、'檯' 或 '枱' 应统一为 '台'（台湾、舞台、台面等）。",
        )


class A1_041_TanRule(UnifiedTermRule):
    """談 统一写法."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A1-041",
            wrong_pattern=r"談",
            correct_form="谈",
            description="'談' 应统一为 '谈'（谈话、谈论等）。",
        )


class A1_042_TaoRule(UnifiedTermRule):
    """討 统一写法."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A1-042",
            wrong_pattern=r"討",
            correct_form="讨",
            description="'討' 应统一为 '讨'（讨论、讨厌等）。",
        )


class A1_043_TiRule(UnifiedTermRule):
    """題 统一写法."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A1-043",
            wrong_pattern=r"題",
            correct_form="题",
            description="'題' 应统一为 '题'（问题、题目等）。",
        )


class A1_044_TingRule(UnifiedTermRule):
    """聽 统一写法."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A1-044",
            wrong_pattern=r"聽",
            correct_form="听",
            description="'聽' 应统一为 '听'（听说、听见等）。",
        )


class A1_045_TongRule(UnifiedTermRule):
    """衕 统一写法."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A1-045",
            wrong_pattern=r"衕",
            correct_form="同",
            description="'衕' 应统一为 '同'（胡同等，表示「一起」或「相同」时）。",
        )


class A1_046_TuanRule(UnifiedTermRule):
    """團 统一写法."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A1-046",
            wrong_pattern=r"團",
            correct_form="团",
            description="'團' 应统一为 '团'（团队、团结等）。",
        )


class A1_047_WanRule(UnifiedTermRule):
    """萬 统一写法."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A1-047",
            wrong_pattern=r"萬",
            correct_form="万",
            description="'萬' 应统一为 '万'（万一、万分等）。",
        )


class A1_048_WeiRule(UnifiedTermRule):
    """衛 统一写法."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A1-048",
            wrong_pattern=r"衛",
            correct_form="卫",
            description="'衛' 应统一为 '卫'（卫生、保卫等）。",
        )


class A1_049_XianRule(UnifiedTermRule):
    """綫/線 统一写法."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A1-049",
            wrong_pattern=r"[綫線]",
            correct_form="线",
            description="'綫' 或 '線' 应统一为 '线'（线条、路线等）。",
        )


class A1_050_XiangRule(UnifiedTermRule):
    """響 统一写法."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A1-050",
            wrong_pattern=r"響",
            correct_form="响",
            description="'響' 应统一为 '响'（响应、影响等）。",
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


class A2_011_ZuoBiaoRule(VariantWordRule):
    """座标 → 坐标 (A2-011)."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A2-011",
            wrong_form="座标",
            correct_form="坐标",
            description="数学或地理术语应使用「坐标」，而非「座标」。",
        )


class A2_012_FuGaiRule(VariantWordRule):
    """复盖 → 覆盖 (A2-012)."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A2-012",
            wrong_form="复盖",
            correct_form="覆盖",
            description="表示「遮盖、覆盖面」时应使用「覆盖」，而非「复盖」。",
        )


class A2_013_FanFuRule(VariantWordRule):
    """反覆 → 反复 (A2-013)."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A2-013",
            wrong_form="反覆",
            correct_form="反复",
            description="现代标准用法应使用「反复」，而非「反覆」。",
        )


class A2_014_JueZeRule(VariantWordRule):
    """决择 → 抉择 (A2-014)."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A2-014",
            wrong_form="决择",
            correct_form="抉择",
            description="表示「选择、挑选」时应使用「抉择」，而非「决择」。",
        )


class A2_015_CangSangRule(VariantWordRule):
    """苍桑 → 沧桑 (A2-015)."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A2-015",
            wrong_form="苍桑",
            correct_form="沧桑",
            description="成语「沧海桑田」，应使用「沧桑」，而非「苍桑」。",
        )


class A2_016_BanJiaoShiRule(VariantWordRule):
    """拌脚石 → 绊脚石 (A2-016)."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A2-016",
            wrong_form="拌脚石",
            correct_form="绊脚石",
            description="表示「障碍物」时应使用「绊脚石」，而非「拌脚石」。",
        )


class A2_017_BaoGuangRule(VariantWordRule):
    """暴光 → 曝光 (A2-017)."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A2-017",
            wrong_form="暴光",
            correct_form="曝光",
            description="表示「揭露、公开」或「摄影曝光」时应使用「曝光」，而非「暴光」。",
        )


class A2_018_MengBiRule(VariantWordRule):
    """蒙敝 → 蒙蔽 (A2-018)."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A2-018",
            wrong_form="蒙敝",
            correct_form="蒙蔽",
            description="表示「欺骗、隐瞒」时应使用「蒙蔽」，而非「蒙敝」。",
        )


class A2_019_JiShenRule(VariantWordRule):
    """挤身 → 跻身 (A2-019)."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A2-019",
            wrong_form="挤身",
            correct_form="跻身",
            description="表示「进入某一行列」时应使用「跻身」，而非「挤身」。",
        )


class A2_020_TaoYuanRule(VariantWordRule):
    """世外桃园 → 世外桃源 (A2-020)."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A2-020",
            wrong_form="世外桃园",
            correct_form="世外桃源",
            description="成语应为「世外桃源」，而非「世外桃园」。",
        )


class A2_021_YiShenZuoZeRule(VariantWordRule):
    """以身作责 → 以身作则 (A2-021)."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A2-021",
            wrong_form="以身作责",
            correct_form="以身作则",
            description="成语应为「以身作则」，而非「以身作责」。",
        )


class A2_022_AnZhuangRule(VariantWordRule):
    """按装 → 安装 (A2-022)."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A2-022",
            wrong_form="按装",
            correct_form="安装",
            description="表示「安装设备、软件」时应使用「安装」，而非「按装」。",
        )


class A2_023_BanPeiRule(VariantWordRule):
    """班配 → 般配 (A2-023)."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A2-023",
            wrong_form="班配",
            correct_form="般配",
            description="表示「相称、匹配」时应使用「般配」，而非「班配」。",
        )


class A2_024_SuXingRule(VariantWordRule):
    """甦醒 → 苏醒 (A2-024)."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A2-024",
            wrong_form="甦醒",
            correct_form="苏醒",
            description="现代标准用法应使用「苏醒」，而非「甦醒」。",
        )


class A2_025_MoFangRule(VariantWordRule):
    """摹仿 → 模仿 (A2-025)."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A2-025",
            wrong_form="摹仿",
            correct_form="模仿",
            description="现代标准用法应使用「模仿」，而非「摹仿」。",
        )


class A2_026_TiXingRule(VariantWordRule):
    """体形 → 体型 (A2-026)."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A2-026",
            wrong_form="体形",
            correct_form="体型",
            description="表示「身体形态」时应使用「体型」，而非「体形」。",
        )


class A2_027_QiGaiRule(VariantWordRule):
    """气慨 → 气概 (A2-027)."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A2-027",
            wrong_form="气慨",
            correct_form="气概",
            description="表示「气魄、风度」时应使用「气概」，而非「气慨」。",
        )


class A2_028_LiaoWangRule(VariantWordRule):
    """了望 → 瞭望 (A2-028)."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A2-028",
            wrong_form="了望",
            correct_form="瞭望",
            description="表示「从高处远看」时应使用「瞭望」，而非「了望」。",
        )


class A2_029_TiGangRule(VariantWordRule):
    """题纲 → 提纲 (A2-029)."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A2-029",
            wrong_form="题纲",
            correct_form="提纲",
            description="表示「大纲、要点」时应使用「提纲」，而非「题纲」。",
        )


class A2_030_SongChiRule(VariantWordRule):
    """松驰 → 松弛 (A2-030)."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A2-030",
            wrong_form="松驰",
            correct_form="松弛",
            description="表示「不紧张、放松」时应使用「松弛」，而非「松驰」。",
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


class A3_045_WeiMiaoWeiXiaoRule(TypoReplacementRule):
    """A3-045: 维妙维肖 → 惟妙惟肖."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A3-045",
            wrong_pattern="维妙维肖",
            correct_form="惟妙惟肖",
            description="成语应为 '惟妙惟肖'，不写 '维妙维肖'。",
        )


class A3_046_CuZhiLanZaoRule(TypoReplacementRule):
    """A3-046: 粗制烂造 → 粗制滥造."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A3-046",
            wrong_pattern="粗制烂造",
            correct_form="粗制滥造",
            description="成语应为 '粗制滥造'，不写 '粗制烂造'。",
        )


class A3_047_SongChiRule(TypoReplacementRule):
    """A3-047: 松驰 → 松弛."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A3-047",
            wrong_pattern="松驰",
            correct_form="松弛",
            description="应为 '松弛'（弓字旁），不写 '松驰'（马字旁）。",
        )


class A3_048_QiKaiRule(TypoReplacementRule):
    """A3-048: 气慨 → 气概."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A3-048",
            wrong_pattern="气慨",
            correct_form="气概",
            description="应为 '气概'，不写 '气慨'。",
        )


class A3_049_TiGangRule(TypoReplacementRule):
    """A3-049: 题纲 → 提纲."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A3-049",
            wrong_pattern="题纲",
            correct_form="提纲",
            description="应为 '提纲'（提手旁），不写 '题纲'（页字旁）。",
        )


class A3_050_BiJingRule(TypoReplacementRule):
    """A3-050: 必竟 → 毕竟."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A3-050",
            wrong_pattern="必竟",
            correct_form="毕竟",
            description="应为 '毕竟'，不写 '必竟'。",
        )


class A3_051_JiBianRule(TypoReplacementRule):
    """A3-051: 既便 → 即便."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A3-051",
            wrong_pattern="既便",
            correct_form="即便",
            description="表示「假设、就算」时应为 '即便'，不写 '既便'。",
        )


class A3_052_ZuoLuoRule(TypoReplacementRule):
    """A3-052: 座落 → 坐落."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A3-052",
            wrong_pattern="座落",
            correct_form="坐落",
            description="表示「位于」时应为 '坐落'，不写 '座落'。",
        )


class A3_053_RuBuFuChuRule(TypoReplacementRule):
    """A3-053: 入不付出 → 入不敷出."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A3-053",
            wrong_pattern="入不付出",
            correct_form="入不敷出",
            description="成语应为 '入不敷出'，不写 '入不付出'。",
        )


class A3_054_BuJiQiShuRule(TypoReplacementRule):
    """A3-054: 不记其数 → 不计其数."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A3-054",
            wrong_pattern="不记其数",
            correct_form="不计其数",
            description="成语应为 '不计其数'，不写 '不记其数'。",
        )


class A3_055_QingZhuNanShuRule(TypoReplacementRule):
    """A3-055: 磬竹难书 → 罄竹难书."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A3-055",
            wrong_pattern="磬竹难书",
            correct_form="罄竹难书",
            description="成语应为 '罄竹难书'，不写 '磬竹难书'。",
        )


class A3_056_ZhenBianRule(TypoReplacementRule):
    """A3-056: 针贬 → 针砭."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A3-056",
            wrong_pattern="针贬",
            correct_form="针砭",
            description="应为 '针砭'（石字旁），不写 '针贬'（贝字旁）。",
        )


class A3_057_ZhenHanRule(TypoReplacementRule):
    """A3-057: 震憾 → 震撼."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A3-057",
            wrong_pattern="震憾",
            correct_form="震撼",
            description="应为 '震撼'（提手旁），不写 '震憾'（心字旁）。",
        )


class A3_058_FanZaoRule(TypoReplacementRule):
    """A3-058: 烦燥 → 烦躁."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A3-058",
            wrong_pattern="烦燥",
            correct_form="烦躁",
            description="表示「烦闷不安」时应为 '烦躁'（足字旁），不写 '烦燥'（火字旁）。",
        )


class A3_059_FengMiRule(TypoReplacementRule):
    """A3-059: 风糜 → 风靡."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A3-059",
            wrong_pattern="风糜",
            correct_form="风靡",
            description="表示「广泛流行」时应为 '风靡'（非字旁），不写 '风糜'（米字旁）。",
        )


class A3_060_FengYongErZhiRule(TypoReplacementRule):
    """A3-060: 蜂涌而至 → 蜂拥而至."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A3-060",
            wrong_pattern="蜂涌而至",
            correct_form="蜂拥而至",
            description="成语应为 '蜂拥而至'，不写 '蜂涌而至'。",
        )


class A3_061_GanBaiXiaFengRule(TypoReplacementRule):
    """A3-061: 甘败下风 → 甘拜下风."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A3-061",
            wrong_pattern="甘败下风",
            correct_form="甘拜下风",
            description="成语应为 '甘拜下风'（拜服），不写 '甘败下风'。",
        )


class A3_062_YiGuZuoQiRule(TypoReplacementRule):
    """A3-062: 一股作气 → 一鼓作气."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A3-062",
            wrong_pattern="一股作气",
            correct_form="一鼓作气",
            description="成语应为 '一鼓作气'，不写 '一股作气'。",
        )


class A3_063_GuiJiDuoDuanRule(TypoReplacementRule):
    """A3-063: 鬼计多端 → 诡计多端."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A3-063",
            wrong_pattern="鬼计多端",
            correct_form="诡计多端",
            description="成语应为 '诡计多端'（言字旁），不写 '鬼计多端'。",
        )


class A3_064_HongTangDaXiaoRule(TypoReplacementRule):
    """A3-064: 轰堂大笑 → 哄堂大笑."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A3-064",
            wrong_pattern="轰堂大笑",
            correct_form="哄堂大笑",
            description="成语应为 '哄堂大笑'（口字旁），不写 '轰堂大笑'（车字旁）。",
        )


class A3_065_HouMenSiHaiRule(TypoReplacementRule):
    """A3-065: 候门似海 → 侯门似海."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A3-065",
            wrong_pattern="候门似海",
            correct_form="侯门似海",
            description="成语应为 '侯门似海'（单人旁），不写 '候门似海'（双人旁）。",
        )


class A3_066_JiWangBuJiuRule(TypoReplacementRule):
    """A3-066: 既往不究 → 既往不咎."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A3-066",
            wrong_pattern="既往不究",
            correct_form="既往不咎",
            description="成语应为 '既往不咎'，不写 '既往不究'。",
        )


class A3_067_JiaoRouZaoZuoRule(TypoReplacementRule):
    """A3-067: 娇揉造作 → 矫揉造作."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A3-067",
            wrong_pattern="娇揉造作",
            correct_form="矫揉造作",
            description="成语应为 '矫揉造作'（矢字旁），不写 '娇揉造作'（女字旁）。",
        )


class A3_068_TingErZouXianRule(TypoReplacementRule):
    """A3-068: 挺而走险 → 铤而走险."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A3-068",
            wrong_pattern="挺而走险",
            correct_form="铤而走险",
            description="成语应为 '铤而走险'（金字旁），不写 '挺而走险'（提手旁）。",
        )


class A3_069_MiLiRule(TypoReplacementRule):
    """A3-069: 糜烂 → 靡烂 (in context of 奢靡)."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A3-069",
            wrong_pattern="奢糜",
            correct_form="奢靡",
            description="应为 '奢靡'（非字旁），不写 '奢糜'（米字旁）。",
        )


class A3_070_YuanXingBiLuRule(TypoReplacementRule):
    """A3-070: 原型毕露 → 原形毕露."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A3-070",
            wrong_pattern="原型毕露",
            correct_form="原形毕露",
            description="成语应为 '原形毕露'，不写 '原型毕露'。",
        )


class A3_071_ZuoKeRule(TypoReplacementRule):
    """A3-071: 做客 → 作客."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A3-071",
            wrong_pattern="做客",
            correct_form="作客",
            description="表示「当客人」时应为 '作客'，不写 '做客'。",
        )


class A3_072_ChuanDaiRule(TypoReplacementRule):
    """A3-072: 穿带 → 穿戴."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A3-072",
            wrong_pattern="穿带",
            correct_form="穿戴",
            description="应为 '穿戴'，不写 '穿带'。",
        )


class A3_073_DanWuRule(TypoReplacementRule):
    """A3-073: 耽误 → 担误."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="A3-073",
            wrong_pattern="担误",
            correct_form="耽误",
            description="应为 '耽误'（耳字旁），不写 '担误'（提手旁）。",
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


class C1_010_NegativeNumberRule(DeterministicRule):
    """Check negative number format (C1-010)."""

    # 匹配使用连字符作为负号的数字
    NEGATIVE_PATTERN = re.compile(r"(?<!\d)-(\d+(?:\.\d+)?)")

    def __init__(self) -> None:
        super().__init__(
            rule_id="C1-010",
            category="C",
            subcategory="C1",
            severity="info",
            blocks_publish=False,
            can_auto_fix=True,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        for match in self.NEGATIVE_PATTERN.finditer(content):
            original = match.group()
            corrected = original.replace("-", "−")  # 使用减号（U+2212）

            snippet_start = max(0, match.start() - 10)
            snippet_end = min(len(content), match.end() + 10)
            snippet = content[snippet_start:snippet_end]

            issues.append(
                ProofreadingIssue(
                    rule_id=self.rule_id,
                    category=self.category,
                    subcategory=self.subcategory,
                    message="数字格式：负数应使用减号「−」（U+2212），而非连字符「-」。",
                    suggestion=f"将 '{original}' 改为 '{corrected}'。",
                    severity=self.severity,
                    confidence=0.7,
                    can_auto_fix=self.can_auto_fix,
                    blocks_publish=self.blocks_publish,
                    source=RuleSource.SCRIPT,
                    attributed_by="C1_010_NegativeNumberRule",
                    location={"offset": match.start()},
                    evidence=snippet,
                    auto_fix_value=corrected,
                )
            )
        return issues


class C1_011_NumberRangeRule(DeterministicRule):
    """Check number range format (C1-011)."""

    # 匹配数字范围表示
    RANGE_PATTERN = re.compile(r"(\d+)\s*[-~～]\s*(\d+)")

    def __init__(self) -> None:
        super().__init__(
            rule_id="C1-011",
            category="C",
            subcategory="C1",
            severity="info",
            blocks_publish=False,
            can_auto_fix=True,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        for match in self.RANGE_PATTERN.finditer(content):
            original = match.group()
            start_num = match.group(1)
            end_num = match.group(2)

            # 建议使用全角波浪号或en-dash
            if "-" in original or "~" in original:
                corrected = f"{start_num}～{end_num}"  # 使用全角波浪号

                snippet_start = max(0, match.start() - 10)
                snippet_end = min(len(content), match.end() + 10)
                snippet = content[snippet_start:snippet_end]

                issues.append(
                    ProofreadingIssue(
                        rule_id=self.rule_id,
                        category=self.category,
                        subcategory=self.subcategory,
                        message="数字范围：建议使用全角波浪号「～」表示范围。",
                        suggestion=f"将 '{original}' 改为 '{corrected}'。",
                        severity=self.severity,
                        confidence=0.6,
                        can_auto_fix=self.can_auto_fix,
                        blocks_publish=self.blocks_publish,
                        source=RuleSource.SCRIPT,
                        attributed_by="C1_011_NumberRangeRule",
                        location={"offset": match.start()},
                        evidence=snippet,
                        auto_fix_value=corrected,
                    )
                )
        return issues


class C1_012_PhoneNumberRule(DeterministicRule):
    """Check phone number format (C1-012)."""

    # 匹配电话号码格式（简单模式）
    PHONE_PATTERN = re.compile(r"(?:电话|手机|Tel|Mobile)[:：]\s*(\d{3,4})[-\s]?(\d{7,8})")

    def __init__(self) -> None:
        super().__init__(
            rule_id="C1-012",
            category="C",
            subcategory="C1",
            severity="info",
            blocks_publish=False,
            can_auto_fix=True,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        for match in self.PHONE_PATTERN.finditer(content):
            area_code = match.group(1)
            number = match.group(2)
            original = match.group()

            # 建议使用统一格式
            corrected = original.replace(f"{area_code}-{number}", f"{area_code}-{number}")
            corrected = corrected.replace(f"{area_code} {number}", f"{area_code}-{number}")

            if original != corrected:
                snippet_start = max(0, match.start() - 10)
                snippet_end = min(len(content), match.end() + 10)
                snippet = content[snippet_start:snippet_end]

                issues.append(
                    ProofreadingIssue(
                        rule_id=self.rule_id,
                        category=self.category,
                        subcategory=self.subcategory,
                        message="电话号码：建议使用连字符「-」分隔区号和号码。",
                        suggestion=f"统一格式为 '{corrected}'。",
                        severity=self.severity,
                        confidence=0.7,
                        can_auto_fix=self.can_auto_fix,
                        blocks_publish=self.blocks_publish,
                        source=RuleSource.SCRIPT,
                        attributed_by="C1_012_PhoneNumberRule",
                        location={"offset": match.start()},
                        evidence=snippet,
                        auto_fix_value=corrected,
                    )
                )
        return issues


class C1_013_OrdinalNumberRule(DeterministicRule):
    """Check ordinal number format (C1-013)."""

    # 匹配序数词格式（第 + 空格 + 数字）
    ORDINAL_PATTERN = re.compile(r"第\s+(\d+|[一二三四五六七八九十百千万]+)\s*[个条项款张次]")

    def __init__(self) -> None:
        super().__init__(
            rule_id="C1-013",
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
            original = match.group()
            number = match.group(1)
            unit = original[-1]  # 获取量词

            # 建议不使用空格
            corrected = f"第{number}{unit}"

            if original != corrected:
                snippet_start = max(0, match.start() - 10)
                snippet_end = min(len(content), match.end() + 10)
                snippet = content[snippet_start:snippet_end]

                issues.append(
                    ProofreadingIssue(
                        rule_id=self.rule_id,
                        category=self.category,
                        subcategory=self.subcategory,
                        message="序数格式：「第」和数字之间不应有空格。",
                        suggestion=f"将 '{original}' 改为 '{corrected}'。",
                        severity=self.severity,
                        confidence=0.9,
                        can_auto_fix=self.can_auto_fix,
                        blocks_publish=self.blocks_publish,
                        source=RuleSource.SCRIPT,
                        attributed_by="C1_013_OrdinalNumberRule",
                        location={"offset": match.start()},
                        evidence=snippet,
                        auto_fix_value=corrected,
                    )
                )
        return issues


class C1_014_LargeNumberRule(DeterministicRule):
    """Check large number representation (C1-014)."""

    # 匹配大数字（7位以上）
    LARGE_NUMBER_PATTERN = re.compile(r"\b(\d{7,})\b")

    def __init__(self) -> None:
        super().__init__(
            rule_id="C1-014",
            category="C",
            subcategory="C1",
            severity="info",
            blocks_publish=False,
            can_auto_fix=False,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        for match in self.LARGE_NUMBER_PATTERN.finditer(content):
            number = match.group(1)
            length = len(number)

            if length >= 9:  # 亿级别
                suggestion = f"建议使用「{int(number) // 100000000}亿」或科学计数法。"
            elif length >= 5:  # 万级别
                suggestion = f"建议使用「{int(number) // 10000}万」或千位分隔符。"
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
                    message=f"大数字：'{number}' 太长，建议使用中文单位或千位分隔符。",
                    suggestion=suggestion,
                    severity=self.severity,
                    confidence=0.6,
                    can_auto_fix=self.can_auto_fix,
                    blocks_publish=self.blocks_publish,
                    source=RuleSource.SCRIPT,
                    attributed_by="C1_014_LargeNumberRule",
                    location={"offset": match.start()},
                    evidence=snippet,
                )
            )
        return issues


class C1_015_MixedNumberFormatRule(DeterministicRule):
    """Check mixed number format (C1-015)."""

    # 匹配阿拉伯数字和中文数字混用
    MIXED_PATTERN = re.compile(r"([一二三四五六七八九十百千万亿]+)(\d+)|(\d+)([一二三四五六七八九十百千万亿]+)")

    def __init__(self) -> None:
        super().__init__(
            rule_id="C1-015",
            category="C",
            subcategory="C1",
            severity="warning",
            blocks_publish=False,
            can_auto_fix=False,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        for match in self.MIXED_PATTERN.finditer(content):
            original = match.group()

            snippet_start = max(0, match.start() - 10)
            snippet_end = min(len(content), match.end() + 10)
            snippet = content[snippet_start:snippet_end]

            issues.append(
                ProofreadingIssue(
                    rule_id=self.rule_id,
                    category=self.category,
                    subcategory=self.subcategory,
                    message="数字格式：阿拉伯数字和中文数字不应混用。",
                    suggestion="统一使用阿拉伯数字或中文数字。",
                    severity=self.severity,
                    confidence=0.8,
                    can_auto_fix=self.can_auto_fix,
                    blocks_publish=self.blocks_publish,
                    source=RuleSource.SCRIPT,
                    attributed_by="C1_015_MixedNumberFormatRule",
                    location={"offset": match.start()},
                    evidence=snippet,
                )
            )
        return issues


class C2_007_SpeedUnitRule(DeterministicRule):
    """Check speed unit format (C2-007)."""

    # 匹配速度单位
    SPEED_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s*(?:公里[/／每]小时|千米[/／每]小时|米[/／每]秒)")

    def __init__(self) -> None:
        super().__init__(
            rule_id="C2-007",
            category="C",
            subcategory="C2",
            severity="info",
            blocks_publish=False,
            can_auto_fix=True,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        for match in self.SPEED_PATTERN.finditer(content):
            original = match.group()
            number = match.group(1)

            # 建议使用标准单位符号
            if "公里" in original or "千米" in original:
                corrected = f"{number} km/h"
            elif "米" in original:
                corrected = f"{number} m/s"
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
                    message="计量单位：建议使用国际标准单位符号（km/h、m/s）。",
                    suggestion=f"将 '{original}' 改为 '{corrected}'。",
                    severity=self.severity,
                    confidence=0.7,
                    can_auto_fix=self.can_auto_fix,
                    blocks_publish=self.blocks_publish,
                    source=RuleSource.SCRIPT,
                    attributed_by="C2_007_SpeedUnitRule",
                    location={"offset": match.start()},
                    evidence=snippet,
                    auto_fix_value=corrected,
                )
            )
        return issues


class C2_008_PressureUnitRule(DeterministicRule):
    """Check pressure unit format (C2-008)."""

    # 匹配压力单位
    PRESSURE_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s*(?:帕斯卡|千帕|兆帕|大气压)")

    def __init__(self) -> None:
        super().__init__(
            rule_id="C2-008",
            category="C",
            subcategory="C2",
            severity="info",
            blocks_publish=False,
            can_auto_fix=True,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        for match in self.PRESSURE_PATTERN.finditer(content):
            original = match.group()
            number = match.group(1)

            # 建议使用标准单位符号
            if "帕斯卡" in original:
                corrected = f"{number} Pa"
            elif "千帕" in original:
                corrected = f"{number} kPa"
            elif "兆帕" in original:
                corrected = f"{number} MPa"
            elif "大气压" in original:
                corrected = f"{number} atm"
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
                    message="计量单位：建议使用国际标准单位符号（Pa、kPa、MPa、atm）。",
                    suggestion=f"将 '{original}' 改为 '{corrected}'。",
                    severity=self.severity,
                    confidence=0.7,
                    can_auto_fix=self.can_auto_fix,
                    blocks_publish=self.blocks_publish,
                    source=RuleSource.SCRIPT,
                    attributed_by="C2_008_PressureUnitRule",
                    location={"offset": match.start()},
                    evidence=snippet,
                    auto_fix_value=corrected,
                )
            )
        return issues


class C2_009_EnergyUnitRule(DeterministicRule):
    """Check energy unit format (C2-009)."""

    # 匹配能量单位
    ENERGY_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s*(?:焦耳|千焦|兆焦|千瓦时|度电)")

    def __init__(self) -> None:
        super().__init__(
            rule_id="C2-009",
            category="C",
            subcategory="C2",
            severity="info",
            blocks_publish=False,
            can_auto_fix=True,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        for match in self.ENERGY_PATTERN.finditer(content):
            original = match.group()
            number = match.group(1)

            # 建议使用标准单位符号
            if "焦耳" in original and "千" not in original and "兆" not in original:
                corrected = f"{number} J"
            elif "千焦" in original:
                corrected = f"{number} kJ"
            elif "兆焦" in original:
                corrected = f"{number} MJ"
            elif "千瓦时" in original or "度电" in original:
                corrected = f"{number} kWh"
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
                    message="计量单位：建议使用国际标准单位符号（J、kJ、MJ、kWh）。",
                    suggestion=f"将 '{original}' 改为 '{corrected}'。",
                    severity=self.severity,
                    confidence=0.7,
                    can_auto_fix=self.can_auto_fix,
                    blocks_publish=self.blocks_publish,
                    source=RuleSource.SCRIPT,
                    attributed_by="C2_009_EnergyUnitRule",
                    location={"offset": match.start()},
                    evidence=snippet,
                    auto_fix_value=corrected,
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


class F1_003_ImageAltTextRule(DeterministicRule):
    """Check for image alt text (F1-003)."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="F1-003",
            category="F",
            subcategory="F1",
            severity="warning",
            blocks_publish=False,
            can_auto_fix=False,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []

        if not payload.images:
            return []

        for img in payload.images:
            alt_text = getattr(img, "alt_text", None) or getattr(img, "alt", None)
            if not alt_text or len(alt_text.strip()) == 0:
                evidence = f"Image: {img.id or img.path}"
                issues.append(
                    ProofreadingIssue(
                        rule_id=self.rule_id,
                        category=self.category,
                        subcategory=self.subcategory,
                        message="图片缺少Alt文本：所有图片应提供描述性Alt文本以提升可访问性和SEO。",
                        suggestion="为图片添加描述性Alt文本。",
                        severity=self.severity,
                        confidence=1.0,
                        can_auto_fix=self.can_auto_fix,
                        blocks_publish=self.blocks_publish,
                        source=RuleSource.SCRIPT,
                        attributed_by="F1_003_ImageAltTextRule",
                        location={"resource": img.id or img.path},
                        evidence=evidence,
                    )
                )
        return issues


class F1_004_ImageFileSizeRule(DeterministicRule):
    """Check image file size (F1-004)."""

    MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB

    def __init__(self) -> None:
        super().__init__(
            rule_id="F1-004",
            category="F",
            subcategory="F1",
            severity="warning",
            blocks_publish=False,
            can_auto_fix=False,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []

        if not payload.images:
            return []

        for img in payload.images:
            file_size = getattr(img, "file_size", None) or getattr(img, "size", None)
            if file_size and file_size > self.MAX_FILE_SIZE:
                size_mb = file_size / (1024 * 1024)
                evidence = f"Image: {img.id or img.path}, Size: {size_mb:.2f}MB"
                issues.append(
                    ProofreadingIssue(
                        rule_id=self.rule_id,
                        category=self.category,
                        subcategory=self.subcategory,
                        message=f"图片文件过大：{size_mb:.2f}MB 超过建议大小（2MB）。",
                        suggestion="压缩图片或使用更高效的格式（如WebP）。",
                        severity=self.severity,
                        confidence=1.0,
                        can_auto_fix=self.can_auto_fix,
                        blocks_publish=self.blocks_publish,
                        source=RuleSource.SCRIPT,
                        attributed_by="F1_004_ImageFileSizeRule",
                        location={"resource": img.id or img.path},
                        evidence=evidence,
                    )
                )
        return issues


class F1_005_ImageCountRule(DeterministicRule):
    """Check image count (F1-005)."""

    MAX_IMAGES = 20

    def __init__(self) -> None:
        super().__init__(
            rule_id="F1-005",
            category="F",
            subcategory="F1",
            severity="info",
            blocks_publish=False,
            can_auto_fix=False,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []

        if payload.images and len(payload.images) > self.MAX_IMAGES:
            issues.append(
                ProofreadingIssue(
                    rule_id=self.rule_id,
                    category=self.category,
                    subcategory=self.subcategory,
                    message=f"图片数量过多：文章包含 {len(payload.images)} 张图片，超过建议数量（{self.MAX_IMAGES}张）。",
                    suggestion="考虑减少图片数量或使用图集。",
                    severity=self.severity,
                    confidence=1.0,
                    can_auto_fix=self.can_auto_fix,
                    blocks_publish=self.blocks_publish,
                    source=RuleSource.SCRIPT,
                    attributed_by="F1_005_ImageCountRule",
                    location={},
                    evidence=f"Total images: {len(payload.images)}",
                )
            )
        return issues


class F1_006_ImageFormatRule(DeterministicRule):
    """Check image format recommendations (F1-006)."""

    RECOMMENDED_FORMATS = {"jpg", "jpeg", "png", "webp", "svg"}
    OPTIMAL_FORMAT = "webp"

    def __init__(self) -> None:
        super().__init__(
            rule_id="F1-006",
            category="F",
            subcategory="F1",
            severity="info",
            blocks_publish=False,
            can_auto_fix=False,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []

        if not payload.images:
            return []

        for img in payload.images:
            path = getattr(img, "path", "") or getattr(img, "url", "")
            if path:
                ext = path.split(".")[-1].lower() if "." in path else ""
                if ext and ext not in self.RECOMMENDED_FORMATS:
                    evidence = f"Image: {path}, Format: {ext}"
                    issues.append(
                        ProofreadingIssue(
                            rule_id=self.rule_id,
                            category=self.category,
                            subcategory=self.subcategory,
                            message=f"图片格式建议：'{ext}' 不是推荐格式。",
                            suggestion=f"建议使用 {', '.join(self.RECOMMENDED_FORMATS)} 格式，优先使用 {self.OPTIMAL_FORMAT}。",
                            severity=self.severity,
                            confidence=0.8,
                            can_auto_fix=self.can_auto_fix,
                            blocks_publish=self.blocks_publish,
                            source=RuleSource.SCRIPT,
                            attributed_by="F1_006_ImageFormatRule",
                            location={"resource": path},
                            evidence=evidence,
                        )
                    )
        return issues


class F1_007_ImageDuplicationRule(DeterministicRule):
    """Check for duplicate images (F1-007)."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="F1-007",
            category="F",
            subcategory="F1",
            severity="info",
            blocks_publish=False,
            can_auto_fix=False,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []

        if not payload.images or len(payload.images) < 2:
            return []

        seen_paths = {}
        for img in payload.images:
            path = getattr(img, "path", "") or getattr(img, "url", "")
            if path:
                if path in seen_paths:
                    seen_paths[path] += 1
                else:
                    seen_paths[path] = 1

        for path, count in seen_paths.items():
            if count > 1:
                issues.append(
                    ProofreadingIssue(
                        rule_id=self.rule_id,
                        category=self.category,
                        subcategory=self.subcategory,
                        message=f"图片重复使用：'{path}' 在文章中出现 {count} 次。",
                        suggestion="检查是否为有意重复，考虑去重。",
                        severity=self.severity,
                        confidence=1.0,
                        can_auto_fix=self.can_auto_fix,
                        blocks_publish=self.blocks_publish,
                        source=RuleSource.SCRIPT,
                        attributed_by="F1_007_ImageDuplicationRule",
                        location={"resource": path},
                        evidence=f"Used {count} times",
                    )
                )
        return issues


class F2_002_ArticleLengthRule(DeterministicRule):
    """Check article length (F2-002)."""

    MIN_LENGTH = 300  # 最少字数
    MAX_LENGTH = 5000  # 最多字数
    OPTIMAL_MIN = 800  # 理想最少字数

    def __init__(self) -> None:
        super().__init__(
            rule_id="F2-002",
            category="F",
            subcategory="F2",
            severity="info",
            blocks_publish=False,
            can_auto_fix=False,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        # 计算中文字符数（去除空格、标点）
        chinese_chars = len([c for c in content if "\u4e00" <= c <= "\u9fff"])

        if chinese_chars < self.MIN_LENGTH:
            issues.append(
                ProofreadingIssue(
                    rule_id=self.rule_id,
                    category=self.category,
                    subcategory=self.subcategory,
                    message=f"文章过短：仅 {chinese_chars} 字，低于最低要求（{self.MIN_LENGTH}字）。",
                    suggestion="扩充文章内容以提供更多价值。",
                    severity=self.severity,
                    confidence=1.0,
                    can_auto_fix=self.can_auto_fix,
                    blocks_publish=self.blocks_publish,
                    source=RuleSource.SCRIPT,
                    attributed_by="F2_002_ArticleLengthRule",
                    location={},
                    evidence=f"Length: {chinese_chars} characters",
                )
            )
        elif chinese_chars > self.MAX_LENGTH:
            issues.append(
                ProofreadingIssue(
                    rule_id=self.rule_id,
                    category=self.category,
                    subcategory=self.subcategory,
                    message=f"文章过长：{chinese_chars} 字，超过建议长度（{self.MAX_LENGTH}字）。",
                    suggestion="考虑分为多篇文章或优化内容密度。",
                    severity=self.severity,
                    confidence=1.0,
                    can_auto_fix=self.can_auto_fix,
                    blocks_publish=self.blocks_publish,
                    source=RuleSource.SCRIPT,
                    attributed_by="F2_002_ArticleLengthRule",
                    location={},
                    evidence=f"Length: {chinese_chars} characters",
                )
            )
        elif chinese_chars < self.OPTIMAL_MIN:
            issues.append(
                ProofreadingIssue(
                    rule_id=self.rule_id,
                    category=self.category,
                    subcategory=self.subcategory,
                    message=f"文章长度建议：{chinese_chars} 字，建议至少 {self.OPTIMAL_MIN} 字以获得更好的SEO效果。",
                    suggestion="适当扩充内容。",
                    severity="info",
                    confidence=0.7,
                    can_auto_fix=self.can_auto_fix,
                    blocks_publish=self.blocks_publish,
                    source=RuleSource.SCRIPT,
                    attributed_by="F2_002_ArticleLengthRule",
                    location={},
                    evidence=f"Length: {chinese_chars} characters",
                )
            )
        return issues


class F2_003_ParagraphLengthRule(DeterministicRule):
    """Check paragraph length (F2-003)."""

    MAX_PARAGRAPH_LENGTH = 300  # 最大段落字数

    def __init__(self) -> None:
        super().__init__(
            rule_id="F2-003",
            category="F",
            subcategory="F2",
            severity="info",
            blocks_publish=False,
            can_auto_fix=False,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        # 按双换行符分段
        paragraphs = content.split("\n\n")

        for i, para in enumerate(paragraphs):
            # 计算段落中文字符数
            chinese_chars = len([c for c in para if "\u4e00" <= c <= "\u9fff"])
            if chinese_chars > self.MAX_PARAGRAPH_LENGTH:
                snippet = para[:50] + "..." if len(para) > 50 else para
                issues.append(
                    ProofreadingIssue(
                        rule_id=self.rule_id,
                        category=self.category,
                        subcategory=self.subcategory,
                        message=f"段落过长：第 {i+1} 段有 {chinese_chars} 字，超过建议长度（{self.MAX_PARAGRAPH_LENGTH}字）。",
                        suggestion="将长段落拆分为多个段落以提升可读性。",
                        severity=self.severity,
                        confidence=1.0,
                        can_auto_fix=self.can_auto_fix,
                        blocks_publish=self.blocks_publish,
                        source=RuleSource.SCRIPT,
                        attributed_by="F2_003_ParagraphLengthRule",
                        location={"paragraph": i + 1},
                        evidence=snippet,
                    )
                )
        return issues


class F2_004_HeadingHierarchyRule(DeterministicRule):
    """Check heading hierarchy continuity (F2-004)."""

    HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)

    def __init__(self) -> None:
        super().__init__(
            rule_id="F2-004",
            category="F",
            subcategory="F2",
            severity="warning",
            blocks_publish=False,
            can_auto_fix=False,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        headings = []
        for match in self.HEADING_PATTERN.finditer(content):
            level = len(match.group(1))
            text = match.group(2)
            headings.append((level, text, match.start()))

        # 检查层级跳跃
        for i in range(1, len(headings)):
            prev_level, _, _ = headings[i - 1]
            curr_level, curr_text, offset = headings[i]

            if curr_level > prev_level + 1:
                snippet_start = max(0, offset - 10)
                snippet_end = min(len(content), offset + len(curr_text) + 10)
                snippet = content[snippet_start:snippet_end]

                issues.append(
                    ProofreadingIssue(
                        rule_id=self.rule_id,
                        category=self.category,
                        subcategory=self.subcategory,
                        message=f"标题层级跳跃：从 H{prev_level} 跳到 H{curr_level}，跳过了 H{prev_level+1}。",
                        suggestion=f"遵循标题层级顺序，在 H{curr_level} 之前应有 H{prev_level+1}。",
                        severity=self.severity,
                        confidence=0.9,
                        can_auto_fix=self.can_auto_fix,
                        blocks_publish=self.blocks_publish,
                        source=RuleSource.SCRIPT,
                        attributed_by="F2_004_HeadingHierarchyRule",
                        location={"offset": offset},
                        evidence=snippet,
                    )
                )
        return issues


class F2_005_ListFormatRule(DeterministicRule):
    """Check list formatting (F2-005)."""

    # 检测未格式化的列表（如：1. 2. 3. 或 - - - ）
    UNFORMATTED_LIST = re.compile(r"(?:^|\n)[  ]*((?:\d+\.|[-*+])\s+.+(?:\n[  ]*(?:\d+\.|[-*+])\s+.+){2,})", re.MULTILINE)

    def __init__(self) -> None:
        super().__init__(
            rule_id="F2-005",
            category="F",
            subcategory="F2",
            severity="info",
            blocks_publish=False,
            can_auto_fix=False,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        # 这个规则主要是提示性的，检查是否有明显的列表模式
        # 实际实现可能需要更复杂的逻辑
        return issues


class F2_006_LinkValidityRule(DeterministicRule):
    """Check link presence and format (F2-006)."""

    LINK_PATTERN = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
    URL_PATTERN = re.compile(r"https?://\S+")

    def __init__(self) -> None:
        super().__init__(
            rule_id="F2-006",
            category="F",
            subcategory="F2",
            severity="info",
            blocks_publish=False,
            can_auto_fix=False,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        # 检查markdown链接
        for match in self.LINK_PATTERN.finditer(content):
            text = match.group(1)
            url = match.group(2)

            # 检查空链接
            if not url or url.strip() == "":
                snippet_start = max(0, match.start() - 10)
                snippet_end = min(len(content), match.end() + 10)
                snippet = content[snippet_start:snippet_end]

                issues.append(
                    ProofreadingIssue(
                        rule_id=self.rule_id,
                        category=self.category,
                        subcategory=self.subcategory,
                        message=f"空链接：链接文本 '{text}' 没有URL。",
                        suggestion="为链接添加有效的URL。",
                        severity="warning",
                        confidence=1.0,
                        can_auto_fix=self.can_auto_fix,
                        blocks_publish=self.blocks_publish,
                        source=RuleSource.SCRIPT,
                        attributed_by="F2_006_LinkValidityRule",
                        location={"offset": match.start()},
                        evidence=snippet,
                    )
                )
        return issues


class F3_002_CitationSourceRule(DeterministicRule):
    """Check for citation sources (F3-002)."""

    # 检测引用标记但缺少来源
    QUOTE_PATTERN = re.compile(r"[""'']([^""'']{20,})[""'']")

    def __init__(self) -> None:
        super().__init__(
            rule_id="F3-002",
            category="F",
            subcategory="F3",
            severity="info",
            blocks_publish=False,
            can_auto_fix=False,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        # 这个规则需要更复杂的逻辑来判断是否是引用
        # 暂时返回空列表
        return issues


class F3_003_OriginalContentRatioRule(DeterministicRule):
    """Check original content ratio (F3-003)."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="F3-003",
            category="F",
            subcategory="F3",
            severity="info",
            blocks_publish=False,
            can_auto_fix=False,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        # 这个规则需要AI或其他工具来检测原创性
        # 暂时返回空列表
        return issues


class F4_001_MetaDescriptionLengthRule(DeterministicRule):
    """Check meta description length (F4-001)."""

    MIN_LENGTH = 120
    MAX_LENGTH = 160

    def __init__(self) -> None:
        super().__init__(
            rule_id="F4-001",
            category="F",
            subcategory="F4",
            severity="warning",
            blocks_publish=False,
            can_auto_fix=False,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []

        if not payload.meta_description:
            issues.append(
                ProofreadingIssue(
                    rule_id=self.rule_id,
                    category=self.category,
                    subcategory=self.subcategory,
                    message="Meta描述缺失：文章没有Meta描述。",
                    suggestion="添加Meta描述以改善SEO效果。",
                    severity=self.severity,
                    confidence=1.0,
                    can_auto_fix=self.can_auto_fix,
                    blocks_publish=self.blocks_publish,
                    source=RuleSource.SCRIPT,
                    attributed_by="F4_001_MetaDescriptionLengthRule",
                    location={},
                    evidence="No meta_description",
                )
            )
        else:
            desc_length = len(payload.meta_description)
            if desc_length < self.MIN_LENGTH:
                issues.append(
                    ProofreadingIssue(
                        rule_id=self.rule_id,
                        category=self.category,
                        subcategory=self.subcategory,
                        message=f"Meta描述过短：{desc_length}字符，建议至少{self.MIN_LENGTH}字符。",
                        suggestion="扩充Meta描述以提供更完整的文章摘要。",
                        severity="info",
                        confidence=1.0,
                        can_auto_fix=self.can_auto_fix,
                        blocks_publish=self.blocks_publish,
                        source=RuleSource.SCRIPT,
                        attributed_by="F4_001_MetaDescriptionLengthRule",
                        location={},
                        evidence=f"Length: {desc_length}",
                    )
                )
            elif desc_length > self.MAX_LENGTH:
                issues.append(
                    ProofreadingIssue(
                        rule_id=self.rule_id,
                        category=self.category,
                        subcategory=self.subcategory,
                        message=f"Meta描述过长：{desc_length}字符，超过建议长度（{self.MAX_LENGTH}字符）。",
                        suggestion="缩短Meta描述，搜索引擎可能会截断过长的描述。",
                        severity="info",
                        confidence=1.0,
                        can_auto_fix=self.can_auto_fix,
                        blocks_publish=self.blocks_publish,
                        source=RuleSource.SCRIPT,
                        attributed_by="F4_001_MetaDescriptionLengthRule",
                        location={},
                        evidence=f"Length: {desc_length}",
                    )
                )
        return issues


class F4_002_KeywordUsageRule(DeterministicRule):
    """Check keyword usage (F4-002)."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="F4-002",
            category="F",
            subcategory="F4",
            severity="info",
            blocks_publish=False,
            can_auto_fix=False,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []

        if not payload.seo_keywords or len(payload.seo_keywords) == 0:
            issues.append(
                ProofreadingIssue(
                    rule_id=self.rule_id,
                    category=self.category,
                    subcategory=self.subcategory,
                    message="SEO关键词缺失：文章没有设置关键词。",
                    suggestion="添加3-5个相关关键词以提升SEO效果。",
                    severity=self.severity,
                    confidence=1.0,
                    can_auto_fix=self.can_auto_fix,
                    blocks_publish=self.blocks_publish,
                    source=RuleSource.SCRIPT,
                    attributed_by="F4_002_KeywordUsageRule",
                    location={},
                    evidence="No keywords",
                )
            )
        elif len(payload.seo_keywords) > 10:
            issues.append(
                ProofreadingIssue(
                    rule_id=self.rule_id,
                    category=self.category,
                    subcategory=self.subcategory,
                    message=f"SEO关键词过多：设置了{len(payload.seo_keywords)}个关键词，建议3-5个。",
                    suggestion="精简关键词数量，聚焦核心主题。",
                    severity=self.severity,
                    confidence=0.8,
                    can_auto_fix=self.can_auto_fix,
                    blocks_publish=self.blocks_publish,
                    source=RuleSource.SCRIPT,
                    attributed_by="F4_002_KeywordUsageRule",
                    location={},
                    evidence=f"Keywords: {len(payload.seo_keywords)}",
                )
            )
        return issues


class F4_003_InternalLinkRule(DeterministicRule):
    """Check for internal links (F4-003)."""

    LINK_PATTERN = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

    def __init__(self) -> None:
        super().__init__(
            rule_id="F4-003",
            category="F",
            subcategory="F4",
            severity="info",
            blocks_publish=False,
            can_auto_fix=False,
        )

    def evaluate(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        issues: List[ProofreadingIssue] = []
        content = payload.original_content

        # 检查是否有内部链接
        has_internal_link = False
        for match in self.LINK_PATTERN.finditer(content):
            url = match.group(2)
            # 简单判断：相对路径或同域名
            if url and (url.startswith("/") or not url.startswith("http")):
                has_internal_link = True
                break

        if not has_internal_link:
            issues.append(
                ProofreadingIssue(
                    rule_id=self.rule_id,
                    category=self.category,
                    subcategory=self.subcategory,
                    message="缺少内部链接：文章没有内部链接，建议添加相关文章链接。",
                    suggestion="添加2-3个指向相关文章的内部链接以改善SEO和用户体验。",
                    severity=self.severity,
                    confidence=0.7,
                    can_auto_fix=self.can_auto_fix,
                    blocks_publish=self.blocks_publish,
                    source=RuleSource.SCRIPT,
                    attributed_by="F4_003_InternalLinkRule",
                    location={},
                    evidence="No internal links found",
                )
            )
        return issues


# ============================================================================
# 规则引擎
# ============================================================================


class DeterministicRuleEngine:
    """Coordinator for all deterministic proofreading rules."""

    VERSION = "1.7.0"  # Batch 7: 254条规则 (A1:50, A2:30, A3:70, A4:1, B:60, C:24, F:19)

    def __init__(self) -> None:
        self.rules: List[DeterministicRule] = [
            # B类 - 标点符号与排版（60条）
            # B1 子类 - 基本标点（14条）
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
            B1_011_ParagraphEndPunctuationRule(),  # B1-011: 段落末标点
            B1_012_PunctuationStackingRule(),  # B1-012: 标点堆叠
            B1_013_EnglishPunctuationInChineseRule(),  # B1-013: 中文中英文标点
            B1_014_PunctuationLeadingSpaceRule(),  # B1-014: 标点前空格
            # B2 子类 - 逗号顿号（15条）
            B2_001_CommaSpacingRule(),  # B2-001: 逗号后空格
            HalfWidthCommaRule(),  # B2-002
            B2_003_DunhaoUsageRule(),  # B2-003: 顿号使用
            B2_004_CommaAbuseRule(),  # B2-004: 逗号滥用
            B2_005_SerialCommaRule(),  # B2-005: 序列逗号
            B2_006_ConsecutiveCommasRule(),  # B2-006: 连续逗号
            B2_007_DunhaoCommaMixRule(),  # B2-007: 顿号逗号混用
            B2_008_DunhaoInMixedTextRule(),  # B2-008: 中英文混排顿号
            B2_009_OxfordCommaRule(),  # B2-009: 牛津逗号
            B2_010_MissingDunhaoRule(),  # B2-010: 并列短语缺顿号
            B2_011_DunhaoInLongClausesRule(),  # B2-011: 长句用顿号
            B2_012_CommaInShortPhrasesRule(),  # B2-012: 短语用逗号
            B2_013_CommaSpacingEnglishRule(),  # B2-013: 英文逗号空格
            B2_014_DunhaoWithDengRule(),  # B2-014: 顿号与等
            B2_015_CommaSemicolonMixRule(),  # B2-015: 逗号分号混用
            # B3 子类 - 引号书名号（7条）
            QuotationMatchingRule(),  # B3-001: 引号配对
            QuotationNestingRule(),  # B3-002: 引号嵌套
            BookTitleMatchingRule(),  # B3-003: 书名号配对
            B3_004_EmptyQuoteRule(),  # B3-004: 空引号
            B3_005_BookTitleQuoteMixRule(),  # B3-005: 书名号引号混用
            B3_006_QuoteMisuseRule(),  # B3-006: 引号误用
            B3_007_BookTitleOveruseRule(),  # B3-007: 书名号滥用
            # B4 子类 - 括号（6条）
            B4_001_ParenthesesMatchingRule(),  # B4-001: 括号配对
            B4_002_ParenthesesFormatRule(),  # B4-002: 括号格式
            B4_003_ParenthesisSpacingRule(),  # B4-003: 括号空格
            B4_004_ParenthesisInnerSpaceRule(),  # B4-004: 括号内空格
            B4_005_MixedParenthesesRule(),  # B4-005: 中英文括号混用
            B4_006_NestedParenthesesRule(),  # B4-006: 括号嵌套
            # B5 子类 - 引号（3条）
            B5_001_DoubleQuoteMisuseRule(),  # B5-001: 双引号误用
            B5_002_SingleQuoteMisuseRule(),  # B5-002: 单引号误用
            B5_003_QuoteMixRule(),  # B5-003: 单双引号混用
            # B6 子类 - 间隔号顿号（3条）
            B6_001_EmphasisMarkRule(),  # B6-001: 间隔号
            B6_002_DunhaoMisuseRule(),  # B6-002: 顿号误用
            B6_003_IntervalMarkMisuseRule(),  # B6-003: 间隔号误用
            # B7 子类 - 连接号省略号（9条）
            B7_001_DashFormatRule(),  # B7-001: 破折号格式
            B7_002_HyphenFormatRule(),  # B7-002: 连接号格式
            B7_003_HyphenFormatRule(),  # B7-003: 连字符格式
            HalfWidthDashRule(),  # B7-004: 半角短横线
            B7_005_EllipsisDengRule(),  # B7-005: 省略号与等
            B7_006_DashLengthRule(),  # B7-006: 破折号长度
            B7_007_DashForParallelRule(),  # B7-007: 破折号并列误用
            B7_008_HyphenInconsistencyRule(),  # B7-008: 连接号不一致
            B7_009_EllipsisMisplacementRule(),  # B7-009: 省略号位置
            # B8 子类 - 空格使用（3条）
            B8_001_ExcessiveChineseSpacingRule(),  # B8-001: 中文多余空格
            B8_002_ChineseEnglishSpacingRule(),  # B8-002: 中英文间空格
            B8_003_LineSpacingRule(),  # B8-003: 行首行末空格
            # A类 - 用字规范（120条）
            # A1 子类 - 统一用字（50条）
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
            A1_024_QuanRule(),  # A1-024: 勸 → 劝
            A1_025_RangRule(),  # A1-025: 讓 → 让
            A1_026_ReRule(),  # A1-026: 熱 → 热
            A1_027_RenRule(),  # A1-027: 認 → 认
            A1_028_RongRule(),  # A1-028: 榮 → 荣
            A1_029_SaiRule(),  # A1-029: 賽 → 赛
            A1_030_ShanRule(),  # A1-030: 閃 → 闪
            A1_031_ShengRule(),  # A1-031: 聲 → 声
            A1_032_ShiRule(),  # A1-032: 適 → 适
            A1_033_ShouRule(),  # A1-033: 壽 → 寿
            A1_034_ShuRule(),  # A1-034: 術 → 术
            A1_035_ShuaiRule(),  # A1-035: 帥 → 帅
            A1_036_ShunRule(),  # A1-036: 順 → 顺
            A1_037_ShuoRule(),  # A1-037: 説/說 → 说
            A1_038_SiRule(),  # A1-038: 絲 → 丝
            A1_039_SongRule(),  # A1-039: 鬆 → 松
            A1_040_TaiRule(),  # A1-040: 臺/檯/枱 → 台
            A1_041_TanRule(),  # A1-041: 談 → 谈
            A1_042_TaoRule(),  # A1-042: 討 → 讨
            A1_043_TiRule(),  # A1-043: 題 → 题
            A1_044_TingRule(),  # A1-044: 聽 → 听
            A1_045_TongRule(),  # A1-045: 衕 → 同
            A1_046_TuanRule(),  # A1-046: 團 → 团
            A1_047_WanRule(),  # A1-047: 萬 → 万
            A1_048_WeiRule(),  # A1-048: 衛 → 卫
            A1_049_XianRule(),  # A1-049: 綫/線 → 线
            A1_050_XiangRule(),  # A1-050: 響 → 响
            # A2 子类 - 异形词规范（30条）
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
            A2_011_ZuoBiaoRule(),  # A2-011: 座标 → 坐标
            A2_012_FuGaiRule(),  # A2-012: 复盖 → 覆盖
            A2_013_FanFuRule(),  # A2-013: 反覆 → 反复
            A2_014_JueZeRule(),  # A2-014: 决择 → 抉择
            A2_015_CangSangRule(),  # A2-015: 苍桑 → 沧桑
            A2_016_BanJiaoShiRule(),  # A2-016: 拌脚石 → 绊脚石
            A2_017_BaoGuangRule(),  # A2-017: 暴光 → 曝光
            A2_018_MengBiRule(),  # A2-018: 蒙敝 → 蒙蔽
            A2_019_JiShenRule(),  # A2-019: 挤身 → 跻身
            A2_020_TaoYuanRule(),  # A2-020: 世外桃园 → 世外桃源
            A2_021_YiShenZuoZeRule(),  # A2-021: 以身作责 → 以身作则
            A2_022_AnZhuangRule(),  # A2-022: 按装 → 安装
            A2_023_BanPeiRule(),  # A2-023: 班配 → 般配
            A2_024_SuXingRule(),  # A2-024: 甦醒 → 苏醒
            A2_025_MoFangRule(),  # A2-025: 摹仿 → 模仿
            A2_026_TiXingRule(),  # A2-026: 体形 → 体型
            A2_027_QiGaiRule(),  # A2-027: 气慨 → 气概
            A2_028_LiaoWangRule(),  # A2-028: 了望 → 瞭望
            A2_029_TiGangRule(),  # A2-029: 题纲 → 提纲
            A2_030_SongChiRule(),  # A2-030: 松驰 → 松弛
            # A3 子类 - 常见错字（70条）
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
            A3_045_WeiMiaoWeiXiaoRule(),  # A3-045: 惟妙惟肖
            A3_046_CuZhiLanZaoRule(),  # A3-046: 粗制滥造
            A3_047_SongChiRule(),  # A3-047: 松弛
            A3_048_QiKaiRule(),  # A3-048: 气概
            A3_049_TiGangRule(),  # A3-049: 提纲
            A3_050_BiJingRule(),  # A3-050: 毕竟
            A3_051_JiBianRule(),  # A3-051: 即便
            A3_052_ZuoLuoRule(),  # A3-052: 坐落
            A3_053_RuBuFuChuRule(),  # A3-053: 入不敷出
            A3_054_BuJiQiShuRule(),  # A3-054: 不计其数
            A3_055_QingZhuNanShuRule(),  # A3-055: 罄竹难书
            A3_056_ZhenBianRule(),  # A3-056: 针砭
            A3_057_ZhenHanRule(),  # A3-057: 震撼
            A3_058_FanZaoRule(),  # A3-058: 烦躁
            A3_059_FengMiRule(),  # A3-059: 风靡
            A3_060_FengYongErZhiRule(),  # A3-060: 蜂拥而至
            A3_061_GanBaiXiaFengRule(),  # A3-061: 甘拜下风
            A3_062_YiGuZuoQiRule(),  # A3-062: 一鼓作气
            A3_063_GuiJiDuoDuanRule(),  # A3-063: 诡计多端
            A3_064_HongTangDaXiaoRule(),  # A3-064: 哄堂大笑
            A3_065_HouMenSiHaiRule(),  # A3-065: 侯门似海
            A3_066_JiWangBuJiuRule(),  # A3-066: 既往不咎
            A3_067_JiaoRouZaoZuoRule(),  # A3-067: 矫揉造作
            A3_068_TingErZouXianRule(),  # A3-068: 铤而走险
            A3_069_MiLiRule(),  # A3-069: 奢靡
            A3_070_YuanXingBiLuRule(),  # A3-070: 原形毕露
            A3_071_ZuoKeRule(),  # A3-071: 作客
            A3_072_ChuanDaiRule(),  # A3-072: 穿戴
            A3_073_DanWuRule(),  # A3-073: 耽误
            # A4 子类 - 非正式用语（1条）
            InformalLanguageRule(),  # A4-014
            # C类 - 数字与计量（24条）
            # C1 子类 - 数字格式（15条）
            FullWidthDigitRule(),  # C1-006
            NumberSeparatorRule(),  # C1-001
            PercentageFormatRule(),  # C1-002: 百分比格式
            DecimalPointRule(),  # C1-003: 小数点格式
            DateFormatRule(),  # C1-004: 日期格式
            CurrencyFormatRule(),  # C1-005: 货币格式
            C1_007_TimeFormatRule(),  # C1-007: 时间格式
            C1_008_ScientificNotationRule(),  # C1-008: 科学计数法
            C1_009_OrdinalNumberRule(),  # C1-009: 序数格式
            # C2 子类 - 单位格式（9条）
            KilometerUnificationRule(),  # C2-001: 公里/千米统一
            SquareMeterSymbolRule(),  # C2-002: 平方米符号
            C2_003_TemperatureUnitRule(),  # C2-003: 温度单位
            C2_004_WeightUnitRule(),  # C2-004: 重量单位
            C2_005_VolumeUnitRule(),  # C2-005: 体积单位
            C2_006_AreaUnitRule(),  # C2-006: 面积单位
            C1_010_NegativeNumberRule(),  # C1-010: 负数格式
            C1_011_NumberRangeRule(),  # C1-011: 数字范围
            C1_012_PhoneNumberRule(),  # C1-012: 电话号码
            C1_013_OrdinalNumberRule(),  # C1-013: 序数格式
            C1_014_LargeNumberRule(),  # C1-014: 大数字表示
            C1_015_MixedNumberFormatRule(),  # C1-015: 混用数字格式
            C2_007_SpeedUnitRule(),  # C2-007: 速度单位
            C2_008_PressureUnitRule(),  # C2-008: 压力单位
            C2_009_EnergyUnitRule(),  # C2-009: 能量单位
            # F类 - 发布合规（19条）
            # F1 子类 - 图片规范（7条）
            ImageWidthRule(),  # F1-001
            FeaturedImageLandscapeRule(),  # F1-002
            F1_003_ImageAltTextRule(),  # F1-003
            F1_004_ImageFileSizeRule(),  # F1-004
            F1_005_ImageCountRule(),  # F1-005
            F1_006_ImageFormatRule(),  # F1-006
            F1_007_ImageDuplicationRule(),  # F1-007
            # F2 子类 - 内容结构（6条）
            InvalidHeadingLevelRule(),  # F2-001
            F2_002_ArticleLengthRule(),  # F2-002
            F2_003_ParagraphLengthRule(),  # F2-003
            F2_004_HeadingHierarchyRule(),  # F2-004
            F2_005_ListFormatRule(),  # F2-005
            F2_006_LinkValidityRule(),  # F2-006
            # F3 子类 - 内容质量（3条）
            ImageLicenseRule(),  # F3-001
            F3_002_CitationSourceRule(),  # F3-002
            F3_003_OriginalContentRatioRule(),  # F3-003
            # F4 子类 - SEO 优化（3条）
            F4_001_MetaDescriptionLengthRule(),  # F4-001
            F4_002_KeywordUsageRule(),  # F4-002
            F4_003_InternalLinkRule(),  # F4-003
        ]

    def run(self, payload: ArticlePayload) -> List[ProofreadingIssue]:
        """Execute all deterministic rules."""
        issues: List[ProofreadingIssue] = []
        for rule in self.rules:
            issues.extend(rule.evaluate(payload))
        return issues

