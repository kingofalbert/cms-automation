"""
AI 編譯器配置
"""

import os
from enum import Enum


class AIProvider(Enum):
    """支援的 AI 提供者"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE_OPENAI = "azure_openai"
    GOOGLE_PALM = "google_palm"
    HUGGINGFACE = "huggingface"
    LOCAL_LLM = "local_llm"


class AICompilerConfig:
    """AI 編譯器配置"""

    # 預設提供者
    DEFAULT_PROVIDER = AIProvider.OPENAI

    # 模型配置
    MODELS = {
        AIProvider.OPENAI: {
            "model_name": "gpt-4-turbo-preview",
            "temperature": 0.1,
            "max_tokens": 500,
            "api_key_env": "OPENAI_API_KEY"
        },
        AIProvider.ANTHROPIC: {
            "model_name": "claude-3-opus-20240229",
            "temperature": 0.1,
            "max_tokens": 500,
            "api_key_env": "ANTHROPIC_API_KEY"
        },
        AIProvider.AZURE_OPENAI: {
            "deployment_name": "gpt-4",
            "api_version": "2024-02-15-preview",
            "temperature": 0.1,
            "max_tokens": 500,
            "api_key_env": "AZURE_OPENAI_API_KEY",
            "endpoint_env": "AZURE_OPENAI_ENDPOINT"
        },
        AIProvider.LOCAL_LLM: {
            "model_name": "THUDM/chatglm3-6b",
            "device": "cuda:0",
            "temperature": 0.1,
            "max_length": 500
        }
    }

    # 提示詞模板
    SYSTEM_PROMPT = """你是一個專業的文本校對規則編譯器，專門處理中文文本。

你的任務是將自然語言描述準確轉換為可執行的規則代碼。

# 輸出格式
必須輸出有效的 JSON，包含以下欄位：
{
    "pattern": "正則表達式模式（Python re 語法）",
    "replacement": "替換文本（支援 \\1, \\2 等反向引用）",
    "rule_type": "規則類型",
    "conditions": {},
    "confidence": 0.0-1.0,
    "priority": 1-200,
    "explanation": "規則解釋"
}

# 規則類型
- typo_correction: 錯字修正（優先級最高）
- grammar: 語法錯誤
- punctuation: 標點符號
- style: 風格建議
- preference: 個人偏好

# 條件欄位
- document_type: 文檔類型（article/report/email等）
- only_informal: 僅非正式文檔（true/false）
- paragraph_start: 僅段落開頭（true/false）
- ignore_quotes: 忽略引號內容（true/false）
- case_sensitive: 區分大小寫（true/false）

# 正則表達式提示
- 中文字符範圍：[\\u4e00-\\u9fff]
- 使用括號 () 創建捕獲組
- 使用 \\1, \\2 在替換中引用捕獲組
- 特殊字符需轉義：\\.+*?[]{}()|^$

# 置信度指南
- 0.9-1.0: 非常確定的規則（如常見錯字）
- 0.7-0.9: 較確定的規則（如標點符號）
- 0.5-0.7: 建議性規則（如風格改進）
- 0.0-0.5: 偏好性規則（個人風格）

# 優先級計算
Priority = Confidence × 100 + TypeWeight
- typo_correction: +20
- grammar: +18
- punctuation: +15
- style: +10
- preference: +5
"""

    USER_PROMPT_TEMPLATE = """請將以下自然語言描述轉換為規則代碼：

描述：{description}

{examples}

{context}

請確保：
1. 正則表達式語法正確
2. 準確理解描述意圖
3. 設置合理的置信度
4. 選擇正確的規則類型
"""

    @classmethod
    def get_api_key(cls, provider: AIProvider) -> str | None:
        """獲取 API 密鑰"""
        config = cls.MODELS.get(provider, {})
        api_key_env = config.get("api_key_env")
        if api_key_env:
            return os.getenv(api_key_env)
        return None

    @classmethod
    def get_model_config(cls, provider: AIProvider) -> dict:
        """獲取模型配置"""
        return cls.MODELS.get(provider, {})

    @classmethod
    def format_user_prompt(
        cls,
        description: str,
        examples: list | None = None,
        context: dict | None = None
    ) -> str:
        """格式化用戶提示詞"""
        examples_text = ""
        if examples:
            examples_text = "示例：\n"
            for ex in examples:
                examples_text += f"  修改前：{ex.get('before', '')}\n"
                examples_text += f"  修改後：{ex.get('after', '')}\n"

        context_text = ""
        if context:
            context_text = f"上下文：{context}"

        return cls.USER_PROMPT_TEMPLATE.format(
            description=description,
            examples=examples_text,
            context=context_text
        )
