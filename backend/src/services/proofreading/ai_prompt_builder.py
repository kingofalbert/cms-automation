"""Prompt builder for single-call multi-output proofreading analysis."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from src.services.proofreading.models import ArticlePayload

PACKAGE_ROOT = Path(__file__).resolve().parent
RULES_DIR = PACKAGE_ROOT / "rules"
DEFAULT_RULE_FILE = RULES_DIR / "catalog.json"


class RuleManifest:
    """Utility wrapper around machine-readable rule metadata."""

    def __init__(self, data: dict[str, Any], version: str) -> None:
        self.data = data
        self.version = version

    @classmethod
    def from_json(cls, payload: dict[str, Any]) -> RuleManifest:
        """Construct from JSON payload ensuring version is present."""
        version = payload.get("version")
        if not version:
            raise ValueError("Rule manifest must include a 'version' field")
        return cls(data=payload, version=str(version))

    def iter_rules(self) -> Iterable[dict[str, Any]]:
        """Iterate over flattened rule definitions."""
        for category in self.data.get("categories", []):
            for rule in category.get("rules", []):
                yield {
                    "category": category["category"],
                    "subcategory": rule.get("subcategory"),
                    "rule_id": rule["rule_id"],
                    "severity": rule.get("severity", "warning"),
                    "blocks_publish": rule.get("blocks_publish", False),
                    "can_auto_fix": rule.get("can_auto_fix", False),
                    "summary": rule.get("summary"),
                }

    def to_prompt_table(self) -> str:
        """Render a condensed markdown table for the prompt."""
        rows: list[str] = [
            "| 规则ID | 类别 | 级别 | 阻断发布 | 自动修正 | 简述 |",
            "|--------|------|------|----------|----------|------|",
        ]
        for entry in self.iter_rules():
            rows.append(
                "| {rule_id} | {category} | {severity} | {blocks} | {auto_fix} | {summary} |".format(
                    rule_id=entry["rule_id"],
                    category=f"{entry['category']}/{entry.get('subcategory') or '-'}",
                    severity=entry["severity"],
                    blocks="✅" if entry["blocks_publish"] else "—",
                    auto_fix="✅" if entry["can_auto_fix"] else "—",
                    summary=(entry.get("summary") or "").replace("\n", " "),
                )
            )
        return "\n".join(rows)

    @property
    def fingerprint(self) -> str:
        """Return deterministic hash for regression tracking."""
        normalized = json.dumps(self.data, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def load_default_manifest() -> RuleManifest:
    """Load the bundled rule manifest."""
    if not DEFAULT_RULE_FILE.exists():
        raise FileNotFoundError(f"Rule manifest missing at {DEFAULT_RULE_FILE}")
    with DEFAULT_RULE_FILE.open("r", encoding="utf-8") as fh:
        raw = json.load(fh)
    return RuleManifest.from_json(raw)


class ProofreadingPromptBuilder:
    """Builds the unified prompt used for AI proofreading & SEO analysis."""

    def __init__(
        self,
        manifest: RuleManifest | None = None,
    ) -> None:
        self.manifest = manifest or load_default_manifest()

    def build_prompt(self, payload: ArticlePayload) -> dict[str, str]:
        """Construct user + system prompts.

        Returns a dict with `system` and `user` keys so the caller can compose
        Anthropic messages easily.
        """
        manifest_table = self.manifest.to_prompt_table()
        sections_md = self._render_sections(payload)
        metadata_md = self._render_metadata(payload)

        system_prompt = f"""你是一名资深的新闻校对与发布合规专家，需要一次性完成以下任务：

1. 按照 A-F 类共 ~460 条规则进行逐条校对，规则清单见下表。
2. 针对无法程序化验证的语境类规则，给出高置信度结论，并说明依据。
3. 输出结构化 JSON，使系统可以将你的结果与脚本校验结果合并。
4. 所有严重等级达到 error/critical 或 blocks_publish=true 的问题必须给出阻断发布理由。
5. **重要注意事项**：
   - 尊重文章的 target_locale（目标语系），仅修正明确的用字错误（如「煉」vs「練」）
   - **不要强制繁简体转换**，除非规则明确要求特定术语使用特定字形
   - 历史事件名称等专有名词应使用全称，但保持原文的繁简体
   - 若不确定是否需要繁简转换，将 confidence 设置为 0.5 以下并标注需要人工复核

规则清单快照（版本 {self.manifest.version}，哈希 {self.manifest.fingerprint[:12]}）：

{manifest_table}

输出要求：
- 只返回 JSON，不要额外文字。
- JSON 必须符合下列 schema：
```
{{
  "issues": [
    {{
      "rule_id": "A1-001",
      "category": "A",
      "subcategory": "A1",
      "message": "描述问题",
      "suggestion": "可选的修正建议",
      "severity": "info|warning|error|critical",
      "confidence": 0.0-1.0,
      "can_auto_fix": true|false,
      "blocks_publish": true|false,
      "location": {{"section":"body","offset":123}},
      "evidence": "引用原文片段或依据说明"
    }}
  ],
  "suggested_content": "若适用，返回整体建议后的正文",
  "seo_metadata": {{"meta_title": "...", "meta_description": "...", "keywords": ["..."]}},
  "processing_notes": {{
      "ai_rationale": "本次分析重点或困难点简述",
      "rule_coverage": ["A1-001", "..."]  // 表示你实际检查过的规则 id 列表
  }}
}}
```
- 若某条规则不适用亦需在 `processing_notes.rule_coverage` 中列明，以便与脚本结果对比。
- 避免幻觉：当规则无法确认时，将 `confidence` 设置为 0.5 以下，并在 `message` 说明需要人工复核。
"""

        user_prompt = f"""待校对的文章（ID: {payload.article_id or 'N/A'}, 目标语系：{payload.target_locale}）：

# 标题
{payload.title}

# 原始内容
```
{payload.original_content}
```

# 结构化分段
{sections_md}

# 元数据
{metadata_md}

请严格遵循输出要求，返回唯一 JSON。"""

        return {"system": system_prompt, "user": user_prompt}

    @staticmethod
    def _render_sections(payload: ArticlePayload) -> str:
        if not payload.sections:
            return "_（无结构化分段）_"
        lines = []
        for index, section in enumerate(payload.sections, start=1):
            snippet = section.content.strip()
            if len(snippet) > 280:
                snippet = snippet[:280] + "..."
            lines.append(f"- Section {index} ({section.kind}): `{snippet}`")
        return "\n".join(lines)

    @staticmethod
    def _render_metadata(payload: ArticlePayload) -> str:
        metadata_preview = json.dumps(
            payload.metadata, ensure_ascii=False, indent=2
        )
        image_lines: list[str] = []
        if payload.featured_image:
            image_lines.append(
                f"- Featured: {payload.featured_image.width}x{payload.featured_image.height} ({payload.featured_image.file_format})"
            )
        for idx, img in enumerate(payload.images, start=1):
            image_lines.append(
                f"- Image {idx}: {img.width}x{img.height} ({img.file_format}) source={img.source}"
            )
        image_block = "\n".join(image_lines) or "_（无图片）_"
        keywords = ", ".join(payload.keywords) if payload.keywords else "（无）"

        return f"""## 关键元数据
- 关键词: {keywords}
- 图片信息:
{image_block}

## 自定义字段
```json
{metadata_preview}
```
"""

