"""Prompt builder for single-call multi-output proofreading analysis.

Enhanced version based on《AI 校對規則生成與應用.docx》Chapter 7 design.
Supports the complete 405-rule catalog with DJY-specific "mixed characteristics":
- Traditional Chinese characters (正體字)
- Mainland translation standards for international names
- Party culture vocabulary filtering
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from src.services.proofreading.models import ArticlePayload

PACKAGE_ROOT = Path(__file__).resolve().parent
RULES_DIR = PACKAGE_ROOT / "rules"
# Use the full catalog with 405 rules instead of sample catalog
FULL_RULE_FILE = RULES_DIR / "catalog_full.json"
LEGACY_RULE_FILE = RULES_DIR / "catalog.json"


class RuleManifest:
    """Utility wrapper around machine-readable rule metadata."""

    def __init__(self, data: dict[str, Any], version: str) -> None:
        self.data = data
        self.version = version
        self._rule_count = data.get("total_rule_count", 0)

    @classmethod
    def from_json(cls, payload: dict[str, Any]) -> RuleManifest:
        """Construct from JSON payload ensuring version is present."""
        version = payload.get("version")
        if not version:
            raise ValueError("Rule manifest must include a 'version' field")
        return cls(data=payload, version=str(version))

    @property
    def total_rules(self) -> int:
        """Return total number of rules in manifest."""
        return self._rule_count

    @property
    def special_notes(self) -> dict[str, str]:
        """Return DJY-specific special handling notes."""
        return self.data.get("special_notes", {})

    def iter_rules(self) -> Iterable[dict[str, Any]]:
        """Iterate over flattened rule definitions."""
        for category in self.data.get("categories", []):
            for rule in category.get("rules", []):
                yield {
                    "category": category["category"],
                    "category_desc": category.get("description", ""),
                    "subcategory": rule.get("subcategory"),
                    "rule_id": rule["rule_id"],
                    "severity": rule.get("severity", "warning"),
                    "blocks_publish": rule.get("blocks_publish", False),
                    "can_auto_fix": rule.get("can_auto_fix", False),
                    "summary": rule.get("summary"),
                    "example_wrong": rule.get("example_wrong"),
                    "example_correct": rule.get("example_correct"),
                }

    def iter_categories(self) -> Iterable[dict[str, Any]]:
        """Iterate over category summaries."""
        for category in self.data.get("categories", []):
            yield {
                "category": category["category"],
                "description": category.get("description", ""),
                "rule_count": category.get("rule_count", len(category.get("rules", []))),
                "subcategories": category.get("subcategories", []),
            }

    def get_rules_by_category(self, category: str) -> list[dict[str, Any]]:
        """Get all rules for a specific category."""
        return [r for r in self.iter_rules() if r["category"] == category]

    def get_high_priority_rules(self) -> list[dict[str, Any]]:
        """Get rules that block publish or have error/critical severity."""
        return [
            r for r in self.iter_rules()
            if r["blocks_publish"] or r["severity"] in ("error", "critical")
        ]

    def to_prompt_table(self, max_rules: int | None = None) -> str:
        """Render a condensed markdown table for the prompt.

        Args:
            max_rules: If set, limit to first N rules (for token optimization)
        """
        rows: list[str] = [
            "| 规则ID | 类别 | 级别 | 阻断发布 | 自动修正 | 简述 |",
            "|--------|------|------|----------|----------|------|",
        ]
        count = 0
        for entry in self.iter_rules():
            if max_rules and count >= max_rules:
                rows.append(f"| ... | ... | ... | ... | ... | (共{self.total_rules}条规则，已截断) |")
                break
            rows.append(
                "| {rule_id} | {category} | {severity} | {blocks} | {auto_fix} | {summary} |".format(
                    rule_id=entry["rule_id"],
                    category=f"{entry['category']}/{entry.get('subcategory') or '-'}",
                    severity=entry["severity"],
                    blocks="✅" if entry["blocks_publish"] else "—",
                    auto_fix="✅" if entry["can_auto_fix"] else "—",
                    summary=(entry.get("summary") or "").replace("\n", " ")[:50],
                )
            )
            count += 1
        return "\n".join(rows)

    def to_category_summary(self) -> str:
        """Render category summary for system prompt."""
        lines = ["## 规则类别概览\n"]
        for cat in self.iter_categories():
            lines.append(f"**{cat['category']}类 - {cat['description']}** ({cat['rule_count']}条)")
            if cat.get("subcategories"):
                for subcat in cat["subcategories"]:
                    # Support both 'id'/'subcategory' key names
                    subcat_id = subcat.get("id") or subcat.get("subcategory", "")
                    subcat_name = subcat.get("name", "")
                    lines.append(f"  - {subcat_id}: {subcat_name}")
            lines.append("")
        return "\n".join(lines)

    def to_critical_rules_section(self) -> str:
        """Render high-priority rules that block publication."""
        high_priority = self.get_high_priority_rules()
        if not high_priority:
            return ""

        lines = ["## 关键阻断规则（必须检查）\n"]
        for rule in high_priority[:30]:  # Limit to top 30 critical rules
            lines.append(
                f"- **{rule['rule_id']}** [{rule['severity']}]: {rule.get('summary', 'N/A')}"
            )
        if len(high_priority) > 30:
            lines.append(f"  _(共{len(high_priority)}条阻断规则)_")
        return "\n".join(lines)

    @property
    def fingerprint(self) -> str:
        """Return deterministic hash for regression tracking."""
        normalized = json.dumps(self.data, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def load_default_manifest() -> RuleManifest:
    """Load the bundled rule manifest, preferring full catalog."""
    # Prefer full catalog if available
    if FULL_RULE_FILE.exists():
        rule_file = FULL_RULE_FILE
    elif LEGACY_RULE_FILE.exists():
        rule_file = LEGACY_RULE_FILE
    else:
        raise FileNotFoundError(
            f"Rule manifest missing. Expected at {FULL_RULE_FILE} or {LEGACY_RULE_FILE}"
        )

    with rule_file.open("r", encoding="utf-8") as fh:
        raw = json.load(fh)
    return RuleManifest.from_json(raw)


def load_full_manifest() -> RuleManifest:
    """Load the full 405-rule catalog explicitly."""
    if not FULL_RULE_FILE.exists():
        raise FileNotFoundError(f"Full rule catalog missing at {FULL_RULE_FILE}")
    with FULL_RULE_FILE.open("r", encoding="utf-8") as fh:
        raw = json.load(fh)
    return RuleManifest.from_json(raw)


# DJY-specific guidelines based on document Chapter 7
DJY_MIXED_CHARACTERISTICS = """
## 大纪元校对「混合特征」指引

本系统针对大纪元媒体的特殊定位，采用「混合特征」校对标准：

### 1. 字形标准：正体中文
- 使用正体字（繁体字），非简体字
- 但不强制对原稿进行繁简转换，除非规则明确要求特定字形
- 例：「煉功」必须用「煉」，「練習」用「練」——这是用字错误，需要修正

### 2. 译名标准：大陆译名 + 正体字形
- 国际人名、地名采用大陆译名标准
- 但输出时保持正体中文字形
- 例：「奥巴马」→「歐巴馬」（❌）应为「奧巴馬」（✅ 大陆译名+正体字）

### 3. 政治立场：去党文化
- 执行严格的「去党文化」词汇过滤
- 「建国」→「中共建政」
- 「解放」→「中共窃政」或具体年份
- 「新中国」→「中共统治下的中国」
- 中共官方宣传用语需要标注或改写

### 4. 法轮功相关术语
- 「法轮功」「法轮大法」不可简称为「法轮」
- 代词使用「他」而非「它」
- 「炼功」必须用「煉」字
- 「真、善、忍」需保持完整，不可拆分引用

### 5. 历史事件名称
- 使用全称：「六四事件」→「六四天安門事件」
- 「反右」→「反右運動」
- 「文革」→「文化大革命」
"""

# E-class special rules detail for AI reference
E_CLASS_SPECIAL_RULES = """
## E类特殊规范详细指引

### E1 宗教与信仰术语
- 各大正统宗教术语需准确使用
- 避免对信仰的不尊重表述

### E2 法轮功相关 (重点检查)
| 规则 | 错误示例 | 正确示例 |
|------|----------|----------|
| E2-001 | 法轮 | 法轮功/法轮大法 |
| E2-002 | 法轮功是它... | 法轮功是他... |
| E2-003 | 练功 | 煉功 |
| E2-201 | 学习法轮功 | 修炼法轮功 |
| E2-202 | 法轮功弟子们 | 法轮功学员 |

### E3 历史事件名称 (重点检查)
| 规则 | 错误示例 | 正确示例 |
|------|----------|----------|
| E3-001 | 六四 | 六四天安門事件 |
| E3-002 | 文革 | 文化大革命 |
| E3-303 | 反右 | 反右運動 |
| E3-305 | 大跃进 | 大躍進運動 |

### E4 敏感政治术语
- 中共相关：需明确是「中共」而非「中国」
- 台湾相关：尊重台湾主权表述
- 香港相关：注意一国两制相关敏感词
"""

# F-class compliance rules detail
F_CLASS_COMPLIANCE_RULES = """
## F类发布合规详细指引

### F1 版权合规
- 图片来源必须标注
- 引用内容需注明出处
- 避免大段引用受版权保护内容

### F2 信息准确性
- 数据来源需可查证
- 避免未经证实的消息
- 人物身份需准确

### F3 法律风险
- 避免诽谤性言论
- 敏感人物描述需谨慎
- 涉及诉讼内容需法律审核

### F4 党文化词汇过滤 (重点检查)
| 规则 | 党文化词汇 | 应改为 |
|------|------------|--------|
| F4-001 | 建国 | 中共建政 |
| F4-002 | 解放(指1949) | 中共窃政/1949年 |
| F4-003 | 新中国 | 中共统治下的中国 |
| F4-004 | 解放军 | 中共军队/共军 |
| F4-005 | 伟大领袖 | [删除或改写] |
| F4-006 | 党和国家 | 中共政权 |
"""


class ProofreadingPromptBuilder:
    """Builds the unified prompt used for AI proofreading & SEO analysis.

    Enhanced version supporting:
    - Full 405-rule catalog (catalog_full.json)
    - DJY-specific "mixed characteristics" guidelines
    - Detailed E-class and F-class rule references
    - Token-optimized prompt generation
    """

    def __init__(
        self,
        manifest: RuleManifest | None = None,
        include_full_rules: bool = True,
        max_rules_in_prompt: int | None = None,
    ) -> None:
        """Initialize prompt builder.

        Args:
            manifest: Rule manifest to use. Defaults to full catalog.
            include_full_rules: Whether to include detailed rule tables.
            max_rules_in_prompt: Limit rules in prompt for token optimization.
        """
        self.manifest = manifest or load_default_manifest()
        self.include_full_rules = include_full_rules
        self.max_rules_in_prompt = max_rules_in_prompt

    def build_prompt(self, payload: ArticlePayload) -> dict[str, str]:
        """Construct user + system prompts.

        Returns a dict with `system` and `user` keys so the caller can compose
        Anthropic messages easily.
        """
        # Build comprehensive system prompt
        system_prompt = self._build_system_prompt()

        # Build user prompt with article content
        user_prompt = self._build_user_prompt(payload)

        return {"system": system_prompt, "user": user_prompt}

    def _build_system_prompt(self) -> str:
        """Build the comprehensive system prompt with DJY guidelines."""

        # Category summary
        category_summary = self.manifest.to_category_summary()

        # Critical rules section
        critical_rules = self.manifest.to_critical_rules_section()

        # Rule table (potentially truncated for token optimization)
        if self.include_full_rules:
            rule_table = self.manifest.to_prompt_table(self.max_rules_in_prompt)
        else:
            rule_table = "_（规则表已省略，请参考规则ID进行校对）_"

        # Get special notes from manifest
        special_notes = self.manifest.special_notes
        notes_section = ""
        if special_notes:
            notes_section = "\n## 特殊处理说明\n"
            for key, value in special_notes.items():
                notes_section += f"- **{key}**: {value}\n"

        system_prompt = f"""你是大纪元媒体的资深新闻校对与发布合规专家，需要一次性完成以下任务：

# 角色定位
你负责对待发布的新闻稿件进行全面校对，确保符合大纪元的编辑规范和发布标准。

# 核心任务
1. 按照 A-F 类共 {self.manifest.total_rules} 条规则进行逐条校对
2. 针对无法程序化验证的语境类规则，给出高置信度结论并说明依据
3. 输出结构化 JSON，使系统可以将你的结果与确定性规则引擎结果合并
4. 所有 error/critical 级别或 blocks_publish=true 的问题必须给出阻断发布理由

{DJY_MIXED_CHARACTERISTICS}

{category_summary}

{critical_rules}

{E_CLASS_SPECIAL_RULES}

{F_CLASS_COMPLIANCE_RULES}

{notes_section}

# 规则清单快照
版本: {self.manifest.version}
哈希: {self.manifest.fingerprint[:12]}
总规则数: {self.manifest.total_rules}

{rule_table}

# 输出要求

**重要：只返回纯 JSON 对象，不要任何额外文字、解释或 markdown 代码块。**

JSON 必须严格符合以下 schema：

```json
{{
  "issues": [
    {{
      "rule_id": "A1-001",
      "category": "A",
      "subcategory": "A1",
      "message": "描述问题",
      "original_text": "原文中的问题文本",
      "suggestion": "修正建议",
      "severity": "info|warning|error|critical",
      "confidence": 0.0-1.0,
      "can_auto_fix": true|false,
      "blocks_publish": true|false,
      "location": {{"section": "body|title|meta", "paragraph": 1, "offset": 123}},
      "evidence": "引用原文片段或规则依据说明"
    }}
  ],
  "suggested_content": "若适用，返回整体建议后的正文（保持原文繁简体）",
  "seo_metadata": {{
    "meta_title": "建议的SEO标题（50-60字符）",
    "meta_description": "建议的meta描述（120-160字符）",
    "keywords": ["关键词1", "关键词2", "..."],
    "slug_suggestion": "url-friendly-slug"
  }},
  "processing_notes": {{
    "ai_rationale": "本次分析重点或困难点简述",
    "rule_coverage": ["A1-001", "B2-003", "..."],
    "high_confidence_count": 0,
    "low_confidence_count": 0,
    "skipped_rules": ["规则ID及原因"],
    "locale_detected": "zh-TW|zh-CN|mixed"
  }},
  "summary": {{
    "total_issues": 0,
    "by_severity": {{"critical": 0, "error": 0, "warning": 0, "info": 0}},
    "blocks_publish": true|false,
    "publish_recommendation": "approve|review|reject",
    "main_concerns": ["主要问题1", "主要问题2"]
  }}
}}
```

# 校对原则

1. **保持原文风格**：不要强制繁简转换，除非是明确的用字错误
2. **高置信度要求**：对于语境相关的判断，confidence < 0.7 需标注人工复核
3. **避免幻觉**：不确定时宁可标低 confidence，不要臆断
4. **完整覆盖**：在 rule_coverage 中列明检查过的规则，便于与确定性引擎对比
5. **阻断理由**：blocks_publish=true 的问题必须提供充分的 evidence

开始校对。"""

        return system_prompt

    def _build_user_prompt(self, payload: ArticlePayload) -> str:
        """Build the user prompt containing the article to proofread."""
        sections_md = self._render_sections(payload)
        metadata_md = self._render_metadata(payload)

        # Detect locale hint
        locale_hint = payload.target_locale or "auto-detect"

        user_prompt = f"""待校对的文章：

## 基本信息
- 文章ID: {payload.article_id or 'N/A'}
- 目标语系: {locale_hint}
- 标题: {payload.title}

## 正文内容
```
{payload.original_content}
```

## 结构化分段
{sections_md}

## 元数据信息
{metadata_md}

请严格遵循系统提示中的输出要求，返回唯一 JSON 对象。"""

        return user_prompt

    @staticmethod
    def _render_sections(payload: ArticlePayload) -> str:
        """Render article sections for the prompt."""
        if not payload.sections:
            return "_（无结构化分段）_"
        lines = []
        for index, section in enumerate(payload.sections, start=1):
            snippet = section.content.strip()
            if len(snippet) > 300:
                snippet = snippet[:300] + "..."
            lines.append(f"### Section {index} ({section.kind})\n```\n{snippet}\n```")
        return "\n\n".join(lines)

    @staticmethod
    def _render_metadata(payload: ArticlePayload) -> str:
        """Render metadata section for the prompt."""
        metadata_preview = json.dumps(
            payload.metadata, ensure_ascii=False, indent=2
        )

        # Image information
        image_lines: list[str] = []
        if payload.featured_image:
            img = payload.featured_image
            image_lines.append(
                f"- **Featured Image**: {img.width}x{img.height} ({img.file_format})"
            )
        for idx, img in enumerate(payload.images, start=1):
            image_lines.append(
                f"- Image {idx}: {img.width}x{img.height} ({img.file_format}) source={img.source}"
            )
        image_block = "\n".join(image_lines) or "_（无图片）_"

        # Keywords
        keywords = ", ".join(payload.keywords) if payload.keywords else "（无）"

        return f"""### 关键词
{keywords}

### 图片信息
{image_block}

### 自定义元数据
```json
{metadata_preview}
```"""

    def build_seo_only_prompt(self, payload: ArticlePayload) -> dict[str, str]:
        """Build a lighter prompt for SEO-only analysis.

        Use this when you only need SEO metadata suggestions without
        full proofreading.
        """
        system_prompt = f"""你是一名SEO专家，需要为新闻文章生成优化的元数据。

## 任务
分析文章内容，生成：
1. SEO优化的标题（meta_title, 50-60字符）
2. 元描述（meta_description, 120-160字符）
3. 关键词列表（5-10个相关关键词）
4. URL友好的slug建议

## 输出格式
只返回纯 JSON：
```json
{{
  "meta_title": "...",
  "meta_description": "...",
  "keywords": ["...", "..."],
  "slug_suggestion": "...",
  "reasoning": "简述SEO策略"
}}
```"""

        user_prompt = f"""文章标题: {payload.title}

文章内容:
```
{payload.original_content[:2000]}...
```

请生成SEO优化的元数据。"""

        return {"system": system_prompt, "user": user_prompt}

    def build_quick_check_prompt(
        self,
        payload: ArticlePayload,
        focus_categories: list[str] | None = None
    ) -> dict[str, str]:
        """Build a focused prompt for quick checks on specific categories.

        Args:
            payload: Article to check
            focus_categories: List of category letters to focus on (e.g., ["E", "F"])
        """
        focus = focus_categories or ["E", "F"]  # Default to special/compliance rules

        # Get rules for focused categories only
        focused_rules = []
        for cat in focus:
            focused_rules.extend(self.manifest.get_rules_by_category(cat))

        rules_table = "| 规则ID | 级别 | 简述 |\n|--------|------|------|\n"
        for rule in focused_rules[:50]:
            rules_table += f"| {rule['rule_id']} | {rule['severity']} | {rule.get('summary', '')[:40]} |\n"

        system_prompt = f"""你是大纪元的校对专家，进行快速重点检查。

## 检查范围
仅检查 {', '.join(focus)} 类规则（共{len(focused_rules)}条）

{E_CLASS_SPECIAL_RULES if 'E' in focus else ''}
{F_CLASS_COMPLIANCE_RULES if 'F' in focus else ''}

## 规则列表
{rules_table}

## 输出格式
只返回纯 JSON：
```json
{{
  "issues": [
    {{"rule_id": "...", "message": "...", "suggestion": "...", "severity": "...", "confidence": 0.0-1.0}}
  ],
  "quick_summary": "快速检查结论"
}}
```"""

        user_prompt = f"""快速检查以下文章的 {', '.join(focus)} 类问题：

标题: {payload.title}

内容:
```
{payload.original_content}
```"""

        return {"system": system_prompt, "user": user_prompt}


# Convenience function for backward compatibility
def build_proofreading_prompt(payload: ArticlePayload) -> dict[str, str]:
    """Build a standard proofreading prompt.

    This is a convenience function that creates a ProofreadingPromptBuilder
    with default settings and builds the prompt.
    """
    builder = ProofreadingPromptBuilder()
    return builder.build_prompt(payload)
