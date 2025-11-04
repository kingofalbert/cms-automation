"""
AI 驅動的規則編譯器
使用 LLM 將自然語言描述轉換為可執行的規則代碼
"""

import json
import re
from typing import Any

import openai
from anthropic import Anthropic

from ..schemas.proofreading_decision import DraftRule


class AIRuleCompiler:
    """使用 AI 進行規則編譯的智能編譯器"""

    def __init__(self, ai_provider: str = "openai", api_key: str | None = None):
        """
        初始化 AI 編譯器

        Args:
            ai_provider: AI 提供者 (openai, anthropic, local_llm)
            api_key: API 密鑰
        """
        self.ai_provider = ai_provider
        self.api_key = api_key

        if ai_provider == "openai":
            openai.api_key = api_key
        elif ai_provider == "anthropic":
            self.client = Anthropic(api_key=api_key)

    def compile_natural_language_to_rule(
        self,
        natural_language: str,
        examples: list[dict[str, str]] | None = None,
        context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        使用 AI 將自然語言描述轉換為規則代碼

        Args:
            natural_language: 自然語言描述
            examples: 示例列表
            context: 上下文信息

        Returns:
            編譯後的規則結構
        """
        if self.ai_provider == "openai":
            return self._compile_with_openai(natural_language, examples, context)
        elif self.ai_provider == "anthropic":
            return self._compile_with_anthropic(natural_language, examples, context)
        else:
            return self._compile_with_local_llm(natural_language, examples, context)

    def _compile_with_openai(
        self,
        natural_language: str,
        examples: list[dict[str, str]] | None = None,
        context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """使用 OpenAI GPT 進行編譯"""

        # 構建提示詞
        system_prompt = """你是一個專業的文本校對規則編譯器。
你的任務是將中文自然語言描述轉換為可執行的規則代碼。

輸出必須是有效的 JSON 格式，包含以下欄位：
{
    "pattern": "正則表達式模式（Python re 語法）",
    "replacement": "替換文本（支援反向引用 \\1, \\2）",
    "rule_type": "規則類型（typo_correction/punctuation/style/grammar/preference）",
    "conditions": {
        "document_type": "適用的文檔類型（可選）",
        "only_informal": true/false,
        "paragraph_start": true/false,
        "ignore_quotes": true/false
    },
    "confidence": 0.0-1.0,
    "explanation": "規則的詳細解釋"
}

重要注意事項：
1. pattern 必須是有效的 Python 正則表達式
2. 如果需要捕獲組，使用括號 ()
3. replacement 中使用 \\1, \\2 等引用捕獲組
4. 對於中文字符，可以使用 [\\u4e00-\\u9fff] 或直接使用中文
5. 根據描述的確定性設置 confidence 分數
"""

        user_prompt = f"""請將以下自然語言描述轉換為規則代碼：

描述：{natural_language}

"""
        if examples:
            user_prompt += "示例：\n"
            for ex in examples:
                user_prompt += f"  修改前：{ex.get('before', '')}\n"
                user_prompt += f"  修改後：{ex.get('after', '')}\n"

        if context:
            user_prompt += f"\n上下文：{json.dumps(context, ensure_ascii=False)}"

        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,  # 低溫度以獲得更確定的結果
                max_tokens=500
            )

            result_text = response.choices[0].message.content

            # 解析 JSON 結果
            result = json.loads(result_text)

            # 驗證正則表達式
            try:
                re.compile(result['pattern'])
            except re.error:
                result['pattern'] = self._fix_regex_pattern(result['pattern'])

            return result

        except Exception as e:
            print(f"OpenAI 編譯失敗: {e}")
            # 回退到基礎實現
            return self._fallback_compile(natural_language, examples)

    def _compile_with_anthropic(
        self,
        natural_language: str,
        examples: list[dict[str, str]] | None = None,
        context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """使用 Anthropic Claude 進行編譯"""

        prompt = f"""<task>
將中文自然語言描述轉換為可執行的文本校對規則代碼。
</task>

<input>
描述：{natural_language}
</input>

<examples>
"""
        if examples:
            for ex in examples:
                prompt += f"""
修改前：{ex.get('before', '')}
修改後：{ex.get('after', '')}
"""
        prompt += """
</examples>

<output_format>
請輸出 JSON 格式：
{{
    "pattern": "正則表達式模式",
    "replacement": "替換文本",
    "rule_type": "typo_correction|punctuation|style|grammar|preference",
    "conditions": {{...}},
    "confidence": 0.0-1.0,
    "explanation": "解釋"
}}
</output_format>

<requirements>
1. pattern 必須是有效的 Python 正則表達式
2. 使用捕獲組和反向引用處理複雜替換
3. 根據描述設置適當的 confidence 分數
4. 輸出必須是有效的 JSON
</requirements>
"""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-5-20250929",  # Upgraded to Sonnet 4.5
                max_tokens=500,
                temperature=0.1,
                messages=[{"role": "user", "content": prompt}]
            )

            # 提取 JSON 部分
            content = response.content[0].text
            json_match = re.search(r'\{[^}]+\}', content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                return result

        except Exception as e:
            print(f"Claude 編譯失敗: {e}")

        return self._fallback_compile(natural_language, examples)

    def _compile_with_local_llm(
        self,
        natural_language: str,
        examples: list[dict[str, str]] | None = None,
        context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """使用本地 LLM 進行編譯（如 Llama, ChatGLM 等）"""

        # 這裡可以接入本地部署的模型
        # 例如使用 Hugging Face Transformers

        try:
            from transformers import pipeline

            # 使用本地模型
            generator = pipeline(
                "text-generation",
                model="THUDM/chatglm-6b",  # 或其他本地模型
                device=0
            )

            prompt = f"""任務：將自然語言轉換為正則表達式規則
輸入：{natural_language}
輸出 JSON：
"""
            generator(prompt, max_length=200)
            # 解析響應...

        except Exception as e:
            print(f"本地 LLM 編譯失敗: {e}")

        return self._fallback_compile(natural_language, examples)

    def _fallback_compile(
        self,
        natural_language: str,
        examples: list[dict[str, str]] | None = None
    ) -> dict[str, Any]:
        """基礎的回退編譯方法"""

        # 使用規則分析自然語言
        patterns = {
            r'當看到「([^」]+)」.*?改為「([^」]+)」': ('simple_replace', 0.9),
            r'當遇到「([^」]+)」.*?替換為「([^」]+)」': ('simple_replace', 0.9),
            r'「([^」]+)」應該.*?「([^」]+)」': ('should_be', 0.8),
            r'在(.+?)的情況下.*?「([^」]+)」.*?「([^」]+)」': ('conditional', 0.7),
            r'(.+?)之間.*?加入(.+)': ('insert_between', 0.85),
        }

        for pattern_str, (rule_type, confidence) in patterns.items():
            match = re.search(pattern_str, natural_language)
            if match:
                if rule_type == 'simple_replace':
                    return {
                        "pattern": re.escape(match.group(1)),
                        "replacement": match.group(2),
                        "rule_type": "typo_correction",
                        "confidence": confidence,
                        "conditions": {}
                    }
                elif rule_type == 'insert_between':
                    # 處理「中英文之間加入空格」這類規則
                    if "中英文" in match.group(1) and "空格" in match.group(2):
                        return {
                            "pattern": r"([\\u4e00-\\u9fff])([a-zA-Z])",
                            "replacement": r"\\1 \\2",
                            "rule_type": "punctuation",
                            "confidence": 0.88,
                            "conditions": {}
                        }

        # 如果無法解析，返回基礎結構
        return {
            "pattern": "",
            "replacement": "",
            "rule_type": "unknown",
            "confidence": 0.5,
            "conditions": {},
            "error": "無法解析自然語言描述"
        }

    def _fix_regex_pattern(self, pattern: str) -> str:
        """修復常見的正則表達式錯誤"""
        # 處理未轉義的特殊字符
        special_chars = r'\.+*?[]{}()|^$'
        for char in special_chars:
            if char in pattern and f'\\{char}' not in pattern:
                pattern = pattern.replace(char, f'\\{char}')
        return pattern

    def batch_compile_rules(
        self,
        rules: list[DraftRule],
        use_parallel: bool = True
    ) -> list[dict[str, Any]]:
        """批量編譯規則

        Args:
            rules: 規則列表
            use_parallel: 是否並行處理

        Returns:
            編譯後的規則列表
        """
        compiled_rules = []

        if use_parallel:
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = []
                for rule in rules:
                    future = executor.submit(
                        self.compile_natural_language_to_rule,
                        rule.natural_language,
                        rule.examples,
                        rule.conditions
                    )
                    futures.append(future)

                for future in concurrent.futures.as_completed(futures):
                    try:
                        result = future.result()
                        compiled_rules.append(result)
                    except Exception as e:
                        print(f"規則編譯失敗: {e}")
        else:
            for rule in rules:
                try:
                    result = self.compile_natural_language_to_rule(
                        rule.natural_language,
                        rule.examples,
                        rule.conditions
                    )
                    compiled_rules.append(result)
                except Exception as e:
                    print(f"規則編譯失敗: {e}")

        return compiled_rules

    def validate_compiled_rule(self, rule: dict[str, Any]) -> tuple[bool, list[str]]:
        """驗證編譯後的規則

        Args:
            rule: 編譯後的規則

        Returns:
            (是否有效, 錯誤列表)
        """
        errors = []

        # 驗證正則表達式
        if 'pattern' in rule:
            try:
                re.compile(rule['pattern'])
            except re.error as e:
                errors.append(f"無效的正則表達式: {e}")

        # 驗證替換文本
        if 'replacement' in rule:
            # 檢查反向引用
            backrefs = re.findall(r'\\(\d+)', rule['replacement'])
            if backrefs and 'pattern' in rule:
                # 檢查捕獲組數量
                pattern = rule['pattern']
                num_groups = pattern.count('(') - pattern.count('\\(')
                for ref in backrefs:
                    if int(ref) > num_groups:
                        errors.append(f"反向引用 \\{ref} 超出捕獲組數量")

        # 驗證規則類型
        valid_types = ['typo_correction', 'punctuation', 'style', 'grammar', 'preference']
        if 'rule_type' in rule and rule['rule_type'] not in valid_types:
            errors.append(f"無效的規則類型: {rule['rule_type']}")

        # 驗證置信度
        if 'confidence' in rule:
            if not (0.0 <= rule['confidence'] <= 1.0):
                errors.append("置信度必須在 0.0 到 1.0 之間")

        return len(errors) == 0, errors


# 工廠函數
def create_ai_compiler(provider: str = "openai", api_key: str | None = None) -> AIRuleCompiler:
    """創建 AI 編譯器實例

    Args:
        provider: AI 提供者
        api_key: API 密鑰

    Returns:
        AI 編譯器實例
    """
    # 從環境變數獲取 API 密鑰
    import os
    if not api_key:
        if provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
        elif provider == "anthropic":
            api_key = os.getenv("ANTHROPIC_API_KEY")

    return AIRuleCompiler(ai_provider=provider, api_key=api_key)
