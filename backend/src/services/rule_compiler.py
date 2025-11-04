"""
規則編譯器服務
將審查通過的規則轉換為可執行的Python代碼
"""

import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from ..schemas.proofreading_decision import DraftRule, ReviewStatus


@dataclass
class CompiledRule:
    """編譯後的規則"""
    rule_id: str
    rule_type: str
    pattern: re.Pattern | None = None
    replacement: str | None = None
    conditions: dict[str, Any] = None
    confidence: float = 0.0
    priority: int = 0

    def apply(self, text: str, context: dict[str, Any] | None = None) -> tuple[str, list[dict]]:
        """應用規則到文本

        Args:
            text: 要處理的文本
            context: 上下文信息（如文檔類型等）

        Returns:
            處理後的文本和變更記錄
        """
        if not self.pattern:
            return text, []

        # 檢查條件
        if self.conditions and context:
            if not self._check_conditions(context):
                return text, []

        changes = []
        result_text = text

        # 查找所有匹配
        matches = list(self.pattern.finditer(text))

        # 從後往前替換，避免位置偏移
        for match in reversed(matches):
            start, end = match.span()
            original = match.group()

            # 處理替換文本（支持捕獲組引用）
            if self.replacement:
                replacement = self.replacement
                # 處理反向引用 \1, \2 等
                for i, group in enumerate(match.groups(), 1):
                    if group:
                        replacement = replacement.replace(f"\\{i}", group)
            else:
                replacement = original

            changes.append({
                "rule_id": self.rule_id,
                "position": [start, end],
                "original": original,
                "replacement": replacement,
                "confidence": self.confidence
            })

            result_text = result_text[:start] + replacement + result_text[end:]

        return result_text, changes

    def _check_conditions(self, context: dict[str, Any]) -> bool:
        """檢查條件是否滿足"""
        if not self.conditions:
            return True

        for key, value in self.conditions.items():
            if key == "document_type":
                if context.get("document_type") != value:
                    return False
            elif key == "only_informal":
                if value and context.get("is_formal", False):
                    return False
            elif key == "paragraph_start":
                # 這需要在應用時特別處理
                pass
            elif key == "ignore_quotes":
                # 這需要在模式中處理
                pass

        return True


class RuleCompiler:
    """規則編譯器"""

    def __init__(self):
        self.compiled_rules_cache = {}

    def compile_rules(self, rules: list[DraftRule]) -> list[CompiledRule]:
        """編譯規則列表

        Args:
            rules: 要編譯的規則列表

        Returns:
            編譯後的規則列表
        """
        compiled_rules = []

        for rule in rules:
            # 只編譯已批准或已修改的規則
            if rule.review_status not in [ReviewStatus.APPROVED, ReviewStatus.MODIFIED]:
                continue

            compiled_rule = self._compile_single_rule(rule)
            if compiled_rule:
                compiled_rules.append(compiled_rule)

        # 按優先級排序
        compiled_rules.sort(key=lambda x: x.priority, reverse=True)

        return compiled_rules

    def _compile_single_rule(self, rule: DraftRule) -> CompiledRule | None:
        """編譯單個規則

        Args:
            rule: 要編譯的規則

        Returns:
            編譯後的規則，失敗則返回None
        """
        try:
            # 編譯正則表達式
            pattern = None
            if rule.pattern:
                # 處理特殊條件
                pattern_str = rule.pattern
                if rule.conditions and rule.conditions.get("paragraph_start"):
                    pattern_str = f"^{pattern_str}"
                if rule.conditions and rule.conditions.get("case_sensitive"):
                    pattern = re.compile(pattern_str)
                else:
                    pattern = re.compile(pattern_str, re.IGNORECASE)

            # 計算優先級（基於置信度和規則類型）
            priority = self._calculate_priority(rule)

            return CompiledRule(
                rule_id=rule.rule_id,
                rule_type=rule.rule_type,
                pattern=pattern,
                replacement=rule.replacement,
                conditions=rule.conditions,
                confidence=rule.confidence,
                priority=priority
            )

        except Exception as e:
            print(f"編譯規則 {rule.rule_id} 失敗: {e}")
            return None

    def _calculate_priority(self, rule: DraftRule) -> int:
        """計算規則優先級

        優先級計算考慮：
        1. 置信度（0-100）
        2. 規則類型權重
        3. 是否有條件限制
        """
        priority = int(rule.confidence * 100)

        # 規則類型權重
        type_weights = {
            "typo_correction": 20,  # 錯字修正優先級高
            "punctuation": 15,      # 標點符號次之
            "style": 10,            # 風格建議較低
            "grammar": 18,          # 語法錯誤較高
            "preference": 5         # 個人偏好最低
        }
        priority += type_weights.get(rule.rule_type, 10)

        # 有條件限制的規則優先級稍低
        if rule.conditions:
            priority -= 5

        return max(0, min(200, priority))  # 限制在0-200範圍

    def generate_python_module(
        self,
        rules: list[DraftRule],
        module_name: str,
        output_dir: Path,
        metadata: dict[str, Any] | None = None
    ) -> Path:
        """生成可執行的Python模組

        Args:
            rules: 規則列表
            module_name: 模組名稱
            output_dir: 輸出目錄
            metadata: 元數據

        Returns:
            生成的模組檔案路徑
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # 編譯規則
        compiled_rules = self.compile_rules(rules)

        # 生成模組代碼
        module_code = self._generate_module_code(
            compiled_rules,
            module_name,
            metadata
        )

        # 寫入檔案
        module_path = output_dir / f"{module_name}.py"
        with open(module_path, "w", encoding="utf-8") as f:
            f.write(module_code)

        # 生成配置檔案
        config_path = output_dir / f"{module_name}_config.json"
        config_data = {
            "module_name": module_name,
            "version": "1.0.0",
            "created_at": datetime.utcnow().isoformat(),
            "total_rules": len(compiled_rules),
            "metadata": metadata or {},
            "rules": [
                {
                    "rule_id": r.rule_id,
                    "rule_type": r.rule_type,
                    "confidence": r.confidence,
                    "priority": r.priority
                }
                for r in compiled_rules
            ]
        }

        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, ensure_ascii=False, indent=2)

        return module_path

    def _generate_module_code(
        self,
        compiled_rules: list[CompiledRule],
        module_name: str,
        metadata: dict[str, Any] | None = None
    ) -> str:
        """生成Python模組代碼

        Returns:
            完整的Python模組代碼
        """
        # 規則數據序列化
        rules_data = []
        for rule in compiled_rules:
            rule_dict = {
                "rule_id": rule.rule_id,
                "rule_type": rule.rule_type,
                "pattern": rule.pattern.pattern if rule.pattern else None,
                "pattern_flags": rule.pattern.flags if rule.pattern else 0,
                "replacement": rule.replacement,
                "conditions": rule.conditions or {},
                "confidence": rule.confidence,
                "priority": rule.priority
            }
            rules_data.append(rule_dict)

        # 生成模組代碼
        code = f'''"""
{module_name} - 自動生成的校對規則模組
Generated at: {datetime.utcnow().isoformat()}
Total rules: {len(compiled_rules)}
"""

import re
from typing import List, Dict, Any, Tuple, Optional


# 規則定義
RULES_DATA = {json.dumps(rules_data, ensure_ascii=False, indent=2)}


class ProofreadingEngine:
    """校對引擎"""

    def __init__(self):
        self.rules = self._load_rules()

    def _load_rules(self) -> List[Dict[str, Any]]:
        """載入規則"""
        rules = []
        for rule_data in RULES_DATA:
            if rule_data["pattern"]:
                # 重新編譯正則表達式
                pattern = re.compile(
                    rule_data["pattern"],
                    rule_data["pattern_flags"]
                )
                rule_data["compiled_pattern"] = pattern
            rules.append(rule_data)
        return rules

    def process_text(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """處理文本

        Args:
            text: 要處理的文本
            context: 上下文信息

        Returns:
            處理後的文本和變更記錄
        """
        result_text = text
        all_changes = []

        # 按優先級順序應用規則
        for rule in self.rules:
            if "compiled_pattern" not in rule:
                continue

            # 檢查條件
            if not self._check_conditions(rule["conditions"], context):
                continue

            # 應用規則
            pattern = rule["compiled_pattern"]
            matches = list(pattern.finditer(result_text))

            # 從後往前替換
            for match in reversed(matches):
                start, end = match.span()
                original = match.group()

                # 處理替換
                replacement = rule["replacement"] or original
                if rule["replacement"]:
                    # 處理捕獲組引用
                    for i, group in enumerate(match.groups(), 1):
                        if group:
                            replacement = replacement.replace(f"\\\\{{i}}", group)

                all_changes.append({{
                    "rule_id": rule["rule_id"],
                    "rule_type": rule["rule_type"],
                    "position": [start, end],
                    "original": original,
                    "replacement": replacement,
                    "confidence": rule["confidence"]
                }})

                result_text = result_text[:start] + replacement + result_text[end:]

        return result_text, all_changes

    def _check_conditions(
        self,
        conditions: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> bool:
        """檢查條件"""
        if not conditions or not context:
            return True

        for key, value in conditions.items():
            if key == "document_type":
                if context.get("document_type") != value:
                    return False
            elif key == "only_informal":
                if value and context.get("is_formal", False):
                    return False

        return True

    def get_rules_info(self) -> List[Dict[str, Any]]:
        """獲取規則信息"""
        return [
            {{
                "rule_id": r["rule_id"],
                "rule_type": r["rule_type"],
                "confidence": r["confidence"],
                "priority": r["priority"]
            }}
            for r in self.rules
        ]


# 便捷函數
def proofread(text: str, **kwargs) -> Tuple[str, List[Dict]]:
    """校對文本

    Args:
        text: 要校對的文本
        **kwargs: 上下文參數

    Returns:
        校對後的文本和變更列表
    """
    engine = ProofreadingEngine()
    return engine.process_text(text, kwargs)


# 元數據
__version__ = "1.0.0"
__module_name__ = "{module_name}"
__created_at__ = "{datetime.utcnow().isoformat()}"
__total_rules__ = {len(compiled_rules)}
'''

        return code

    def generate_javascript_module(
        self,
        rules: list[DraftRule],
        module_name: str,
        output_dir: Path
    ) -> Path:
        """生成JavaScript/TypeScript模組（用於前端）

        Args:
            rules: 規則列表
            module_name: 模組名稱
            output_dir: 輸出目錄

        Returns:
            生成的模組檔案路徑
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # 編譯規則
        compiled_rules = self.compile_rules(rules)

        # 生成TypeScript代碼
        ts_code = self._generate_typescript_code(compiled_rules, module_name)

        # 寫入檔案
        module_path = output_dir / f"{module_name}.ts"
        with open(module_path, "w", encoding="utf-8") as f:
            f.write(ts_code)

        return module_path

    def _generate_typescript_code(
        self,
        compiled_rules: list[CompiledRule],
        module_name: str
    ) -> str:
        """生成TypeScript模組代碼"""

        rules_data = []
        for rule in compiled_rules:
            rule_dict = {
                "ruleId": rule.rule_id,
                "ruleType": rule.rule_type,
                "pattern": rule.pattern.pattern if rule.pattern else None,
                "replacement": rule.replacement,
                "conditions": rule.conditions or {},
                "confidence": rule.confidence,
                "priority": rule.priority
            }
            rules_data.append(rule_dict)

        code = f'''/**
 * {module_name} - 自動生成的校對規則模組
 * Generated at: {datetime.utcnow().isoformat()}
 * Total rules: {len(compiled_rules)}
 */

export interface Rule {{
  ruleId: string;
  ruleType: string;
  pattern: string | null;
  replacement: string | null;
  conditions: Record<string, any>;
  confidence: number;
  priority: number;
}}

export interface Change {{
  ruleId: string;
  ruleType: string;
  position: [number, number];
  original: string;
  replacement: string;
  confidence: number;
}}

export interface ProofreadingContext {{
  documentType?: string;
  isFormal?: boolean;
  [key: string]: any;
}}

// 規則數據
export const RULES: Rule[] = {json.dumps(rules_data, ensure_ascii=False, indent=2)};

export class ProofreadingEngine {{
  private rules: Rule[];

  constructor() {{
    this.rules = RULES;
  }}

  processText(text: string, context?: ProofreadingContext): {{ text: string; changes: Change[] }} {{
    let resultText = text;
    const changes: Change[] = [];

    // 按優先級應用規則
    for (const rule of this.rules) {{
      if (!rule.pattern) continue;

      // 檢查條件
      if (!this.checkConditions(rule.conditions, context)) continue;

      // 創建正則表達式
      const regex = new RegExp(rule.pattern, 'g');
      const matches = Array.from(text.matchAll(regex));

      // 從後往前替換
      for (let i = matches.length - 1; i >= 0; i--) {{
        const match = matches[i];
        const start = match.index!;
        const end = start + match[0].length;
        const original = match[0];
        const replacement = rule.replacement || original;

        changes.push({{
          ruleId: rule.ruleId,
          ruleType: rule.ruleType,
          position: [start, end],
          original,
          replacement,
          confidence: rule.confidence
        }});

        resultText = resultText.slice(0, start) + replacement + resultText.slice(end);
      }}
    }}

    return {{ text: resultText, changes }};
  }}

  private checkConditions(conditions: Record<string, any>, context?: ProofreadingContext): boolean {{
    if (!conditions || !context) return true;

    for (const [key, value] of Object.entries(conditions)) {{
      if (key === 'documentType' && context.documentType !== value) {{
        return false;
      }}
      if (key === 'onlyInformal' && value && context.isFormal) {{
        return false;
      }}
    }}

    return true;
  }}

  getRulesInfo(): Array<{{ ruleId: string; ruleType: string; confidence: number; priority: number }}> {{
    return this.rules.map(r => ({{
      ruleId: r.ruleId,
      ruleType: r.ruleType,
      confidence: r.confidence,
      priority: r.priority
    }}));
  }}
}}

// 便捷函數
export function proofread(text: string, context?: ProofreadingContext) {{
  const engine = new ProofreadingEngine();
  return engine.processText(text, context);
}}

// 元數據
export const metadata = {{
  version: "1.0.0",
  moduleName: "{module_name}",
  createdAt: "{datetime.utcnow().isoformat()}",
  totalRules: {len(compiled_rules)}
}};
'''

        return code


# 單例實例
rule_compiler = RuleCompiler()
