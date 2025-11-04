"""
使用 Anthropic Claude Sonnet 4.5 的規則編譯器
專門針對中文校對規則的優化實現
最新版本支持更強大的編程和推理能力
"""

import asyncio
import json
import os
import re
from typing import Any

# Anthropic Python SDK
try:
    from anthropic import Anthropic, AsyncAnthropic
except ImportError:
    print("請安裝 anthropic: pip install anthropic")

from ..schemas.proofreading_decision import DraftRule


class ClaudeRuleCompiler:
    """使用 Claude Sonnet 4.5 進行規則編譯的智能編譯器 - 世界最強編程模型"""

    def __init__(self, api_key: str | None = None):
        """
        初始化 Claude 編譯器

        Args:
            api_key: Anthropic API 密鑰
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")

        if not self.api_key:
            raise ValueError("請設置 ANTHROPIC_API_KEY 環境變數或提供 api_key")

        # 初始化同步和異步客戶端
        self.client = Anthropic(api_key=self.api_key)
        self.async_client = AsyncAnthropic(api_key=self.api_key)

        # 使用 Claude Sonnet 4.5 (2025年9月29日發布的最新模型)
        self.model = "claude-sonnet-4-5-20250929"  # 最強的編程模型

        # 編譯緩存
        self.compilation_cache = {}

    def compile_natural_language_to_rule(
        self,
        natural_language: str,
        examples: list[dict[str, str]] | None = None,
        context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        使用 Claude Sonnet 4.5 將自然語言描述轉換為規則代碼

        Args:
            natural_language: 自然語言描述
            examples: 示例列表
            context: 上下文信息

        Returns:
            編譯後的規則結構
        """

        # 檢查緩存
        cache_key = f"{natural_language}_{str(examples)}_{str(context)}"
        if cache_key in self.compilation_cache:
            return self.compilation_cache[cache_key]

        # 構建優化的提示詞
        prompt = self._build_prompt(natural_language, examples, context)

        try:
            # 調用 Claude API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                temperature=0.1,  # 低溫度確保一致性
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                system=self._get_system_prompt()
            )

            # 提取並解析響應
            result = self._parse_claude_response(response.content[0].text)

            # 驗證並修復規則
            result = self._validate_and_fix_rule(result)

            # 緩存結果
            self.compilation_cache[cache_key] = result

            return result

        except Exception as e:
            print(f"Claude 編譯失敗: {e}")
            # 使用增強的回退方法
            return self._enhanced_fallback_compile(natural_language, examples)

    async def compile_natural_language_to_rule_async(
        self,
        natural_language: str,
        examples: list[dict[str, str]] | None = None,
        context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """異步版本的規則編譯"""

        prompt = self._build_prompt(natural_language, examples, context)

        try:
            response = await self.async_client.messages.create(
                model=self.model,
                max_tokens=1000,
                temperature=0.1,
                messages=[{"role": "user", "content": prompt}],
                system=self._get_system_prompt()
            )

            result = self._parse_claude_response(response.content[0].text)
            return self._validate_and_fix_rule(result)

        except Exception as e:
            print(f"異步 Claude 編譯失敗: {e}")
            return self._enhanced_fallback_compile(natural_language, examples)

    def _get_system_prompt(self) -> str:
        """獲取優化的系統提示詞"""
        return """你是一個專業的中文文本校對規則編譯器，專門將自然語言描述轉換為精確的規則代碼。

# 核心任務
將中文自然語言描述轉換為可執行的校對規則，輸出必須是有效的 JSON 格式。

# 輸出格式
```json
{
    "pattern": "Python 正則表達式模式",
    "replacement": "替換文本（支援 \\1, \\2 等反向引用）",
    "rule_type": "規則類型",
    "conditions": {
        "document_type": "文檔類型（可選）",
        "only_informal": true/false,
        "paragraph_start": true/false,
        "ignore_quotes": true/false,
        "case_sensitive": true/false
    },
    "confidence": 0.0-1.0,
    "priority": 1-200,
    "explanation": "規則的中文解釋",
    "test_cases": [
        {"input": "測試輸入", "expected": "預期輸出"}
    ]
}
```

# 規則類型
- typo_correction: 錯字修正（優先級 +20）
- grammar: 語法錯誤（優先級 +18）
- punctuation: 標點符號（優先級 +15）
- style: 風格建議（優先級 +10）
- preference: 個人偏好（優先級 +5）

# 正則表達式要點
1. 中文字符使用：[\\u4e00-\\u9fff]
2. 捕獲組使用括號：()
3. 反向引用：\\1, \\2 (在 replacement 中)
4. 特殊字符轉義：\\.+*?[]{}()|^$
5. 段落開頭：^
6. 詞邊界：\\b (英文), (?<![\\u4e00-\\u9fff]) (中文前)

# 置信度標準
- 0.95-1.00: 明確的錯誤（錯字、明顯語法錯誤）
- 0.85-0.95: 標準規範（標點符號、格式要求）
- 0.70-0.85: 強烈建議（常見風格問題）
- 0.50-0.70: 一般建議（風格偏好）
- 0.00-0.50: 可選建議（個人偏好）

# 重要原則
1. 準確理解中文語境
2. 考慮所有例外情況
3. 生成可測試的規則
4. 提供清晰的解釋
5. 確保 JSON 格式正確"""

    def _build_prompt(
        self,
        natural_language: str,
        examples: list[dict[str, str]] | None = None,
        context: dict[str, Any] | None = None
    ) -> str:
        """構建優化的提示詞"""

        prompt = f"""請將以下中文自然語言描述轉換為精確的校對規則：

## 規則描述
{natural_language}
"""

        if examples:
            prompt += "\n## 示例\n"
            for i, ex in enumerate(examples, 1):
                prompt += f"{i}. 修改前：「{ex.get('before', '')}」\n"
                prompt += f"   修改後：「{ex.get('after', '')}」\n"

        if context:
            prompt += "\n## 上下文信息\n"
            for key, value in context.items():
                prompt += f"- {key}: {value}\n"

        prompt += """
## 要求
1. 仔細分析描述中的關鍵詞（如「但是」、「除外」、「只有」等）
2. 根據示例推斷正確的模式
3. 設置合理的置信度分數
4. 提供至少2個測試用例
5. 輸出必須是有效的 JSON 格式

請直接輸出 JSON，不要包含其他解釋文字。"""

        return prompt

    def _parse_claude_response(self, response_text: str) -> dict[str, Any]:
        """解析 Claude 的響應"""

        # 嘗試提取 JSON
        json_patterns = [
            r'```json\n(.*?)\n```',  # Markdown code block
            r'```\n(.*?)\n```',       # Generic code block
            r'\{.*\}',                 # Raw JSON
        ]

        for pattern in json_patterns:
            match = re.search(pattern, response_text, re.DOTALL)
            if match:
                json_str = match.group(1) if '```' in pattern else match.group(0)
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    continue

        # 如果無法解析，返回錯誤結構
        return {
            "pattern": "",
            "replacement": "",
            "rule_type": "unknown",
            "confidence": 0.5,
            "error": "無法解析 Claude 響應"
        }

    def _validate_and_fix_rule(self, rule: dict[str, Any]) -> dict[str, Any]:
        """驗證並修復規則"""

        # 驗證正則表達式
        if 'pattern' in rule and rule['pattern']:
            try:
                re.compile(rule['pattern'])
            except re.error as e:
                print(f"正則表達式錯誤: {e}")
                # 嘗試修復常見錯誤
                rule['pattern'] = self._fix_regex_pattern(rule['pattern'])

        # 確保必要欄位存在
        rule.setdefault('rule_type', 'unknown')
        rule.setdefault('confidence', 0.5)
        rule.setdefault('priority', self._calculate_priority(rule))
        rule.setdefault('conditions', {})
        rule.setdefault('explanation', '自動生成的規則')

        # 驗證置信度範圍
        if not 0.0 <= rule['confidence'] <= 1.0:
            rule['confidence'] = max(0.0, min(1.0, rule['confidence']))

        # 驗證規則類型
        valid_types = ['typo_correction', 'grammar', 'punctuation', 'style', 'preference']
        if rule['rule_type'] not in valid_types:
            rule['rule_type'] = 'unknown'

        return rule

    def _calculate_priority(self, rule: dict[str, Any]) -> int:
        """計算規則優先級"""

        type_weights = {
            'typo_correction': 20,
            'grammar': 18,
            'punctuation': 15,
            'style': 10,
            'preference': 5,
            'unknown': 0
        }

        base_priority = int(rule.get('confidence', 0.5) * 100)
        type_weight = type_weights.get(rule.get('rule_type', 'unknown'), 0)

        # 有條件的規則優先級稍低
        condition_penalty = 5 if rule.get('conditions') else 0

        return max(0, min(200, base_priority + type_weight - condition_penalty))

    def _fix_regex_pattern(self, pattern: str) -> str:
        """修復常見的正則表達式錯誤"""

        # 修復未轉義的特殊字符
        fixes = {
            r'\.': r'\.',
            r'\+': r'+',
            r'\*': r'*',
            r'\?': r'?',
            r'\[': r'[',
            r'\]': r']',
        }

        for wrong, correct in fixes.items():
            pattern = pattern.replace(wrong, correct)

        # 確保 Unicode 範圍正確
        pattern = pattern.replace('\\\\u', '\\u')

        return pattern

    def _enhanced_fallback_compile(
        self,
        natural_language: str,
        examples: list[dict[str, str]] | None = None
    ) -> dict[str, Any]:
        """增強的回退編譯方法"""

        # 使用更智能的模式匹配
        patterns = [
            # 簡單替換
            (r'「([^」]+)」.*?「([^」]+)」', 'simple_replace', 0.9),
            # 條件替換
            (r'當(.+?)時.*?「([^」]+)」.*?「([^」]+)」', 'conditional', 0.8),
            # 插入規則
            (r'(.+?)之間.*?(加入|插入|添加)(.+)', 'insert', 0.85),
            # 刪除規則
            (r'(刪除|去掉|移除)(.+?)的?「([^」]+)」', 'delete', 0.9),
            # 格式規則
            (r'(統一|全部|所有).*?「([^」]+)」.*?「([^」]+)」', 'format', 0.85),
        ]

        for pattern_str, rule_type, confidence in patterns:
            match = re.search(pattern_str, natural_language)
            if match:
                return self._generate_rule_from_match(
                    match, rule_type, confidence, natural_language, examples
                )

        # 如果無法匹配，嘗試從示例學習
        if examples and len(examples) > 0:
            return self._learn_from_examples(examples)

        # 最終回退
        return {
            "pattern": "",
            "replacement": "",
            "rule_type": "unknown",
            "confidence": 0.0,
            "priority": 0,
            "explanation": "無法解析規則",
            "error": "無法從描述中提取規則模式"
        }

    def _generate_rule_from_match(
        self,
        match: re.Match,
        rule_type: str,
        confidence: float,
        natural_language: str,
        examples: list[dict[str, str]] | None = None
    ) -> dict[str, Any]:
        """根據匹配結果生成規則"""

        if rule_type == 'simple_replace':
            return {
                "pattern": re.escape(match.group(1)),
                "replacement": match.group(2),
                "rule_type": "typo_correction",
                "confidence": confidence,
                "priority": int(confidence * 100) + 20,
                "conditions": {},
                "explanation": f"將「{match.group(1)}」替換為「{match.group(2)}」"
            }

        elif rule_type == 'insert':
            # 特殊處理中英文空格規則
            if "中英文" in match.group(1) and "空格" in match.group(3):
                return {
                    "pattern": r"([\\u4e00-\\u9fff])([a-zA-Z0-9]+)",
                    "replacement": r"\\1 \\2",
                    "rule_type": "punctuation",
                    "confidence": 0.88,
                    "priority": 103,
                    "conditions": {},
                    "explanation": "在中文和英文之間插入空格"
                }

        # 其他情況的處理...
        return self._enhanced_fallback_compile(natural_language, examples)

    def _learn_from_examples(self, examples: list[dict[str, str]]) -> dict[str, Any]:
        """從示例中學習規則"""

        if not examples:
            return self._enhanced_fallback_compile("", None)

        # 分析示例的差異
        first_example = examples[0]
        before = first_example.get('before', '')
        after = first_example.get('after', '')

        # 簡單的差異分析
        if before and after:
            # 查找不同的部分
            for i, (b, a) in enumerate(zip(before, after, strict=False)):
                if b != a:
                    # 找到差異
                    pattern = before[max(0, i-2):min(len(before), i+3)]
                    replacement = after[max(0, i-2):min(len(after), i+3)]

                    return {
                        "pattern": re.escape(pattern),
                        "replacement": replacement,
                        "rule_type": "typo_correction",
                        "confidence": 0.7,
                        "priority": 90,
                        "conditions": {},
                        "explanation": "基於示例學習的規則"
                    }

        return self._enhanced_fallback_compile("", None)

    async def batch_compile_rules_async(
        self,
        rules: list[DraftRule],
        max_concurrent: int = 5
    ) -> list[dict[str, Any]]:
        """批量異步編譯規則"""

        semaphore = asyncio.Semaphore(max_concurrent)

        async def compile_with_limit(rule: DraftRule):
            async with semaphore:
                # 將 Example 對象轉換為字典
                examples_dict = []
                if rule.examples:
                    for ex in rule.examples:
                        if hasattr(ex, 'before') and hasattr(ex, 'after'):
                            examples_dict.append({"before": ex.before, "after": ex.after})
                        elif isinstance(ex, dict):
                            examples_dict.append(ex)

                return await self.compile_natural_language_to_rule_async(
                    rule.natural_language,
                    examples_dict if examples_dict else None,
                    rule.conditions
                )

        tasks = [compile_with_limit(rule) for rule in rules]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 處理異常
        compiled_rules = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"編譯失敗: {result}")
                # 使用原規則的信息作為回退
                rule = rules[i]
                examples_dict = []
                if rule.examples:
                    for ex in rule.examples:
                        if hasattr(ex, 'before') and hasattr(ex, 'after'):
                            examples_dict.append({"before": ex.before, "after": ex.after})
                        elif isinstance(ex, dict):
                            examples_dict.append(ex)
                compiled_rules.append(self._enhanced_fallback_compile(
                    rule.natural_language,
                    examples_dict if examples_dict else None
                ))
            else:
                compiled_rules.append(result)

        return compiled_rules


# 工廠函數
def create_claude_compiler(api_key: str | None = None) -> ClaudeRuleCompiler:
    """創建 Claude 編譯器實例

    Args:
        api_key: Anthropic API 密鑰，如果不提供則從環境變數讀取

    Returns:
        Claude 編譯器實例
    """
    return ClaudeRuleCompiler(api_key=api_key)


# 便捷的同步編譯函數
def compile_with_claude(
    natural_language: str,
    examples: list[dict[str, str]] | None = None,
    context: dict[str, Any] | None = None,
    api_key: str | None = None
) -> dict[str, Any]:
    """使用 Claude 編譯單個規則

    Args:
        natural_language: 自然語言描述
        examples: 示例列表
        context: 上下文信息
        api_key: API 密鑰

    Returns:
        編譯後的規則
    """
    compiler = create_claude_compiler(api_key)
    return compiler.compile_natural_language_to_rule(natural_language, examples, context)
