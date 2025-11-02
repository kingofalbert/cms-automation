#!/usr/bin/env python3
"""测试 Pydantic 安装和基本功能"""

from pydantic import BaseModel, Field, ValidationError
from typing import List, Optional


class TestArticle(BaseModel):
    """测试文章模型"""
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    author: Optional[str] = None
    tags: List[str] = []


def main():
    print("=" * 70)
    print("Pydantic 功能验证")
    print("=" * 70)

    # 测试 1: 正常创建
    print("\n测试 1: 创建有效的模型实例")
    try:
        article = TestArticle(
            title="测试文章",
            content="这是一篇用于测试 Pydantic 的文章。",
            author="Claude",
            tags=["测试", "pydantic"]
        )
        print(f"✅ 成功创建: {article.title}")
        print(f"   作者: {article.author}")
        print(f"   标签: {', '.join(article.tags)}")
    except Exception as e:
        print(f"❌ 失败: {e}")
        return 1

    # 测试 2: 验证错误
    print("\n测试 2: 测试数据验证")
    try:
        invalid = TestArticle(
            title="",  # 空标题应该失败
            content="内容"
        )
        print(f"❌ 应该失败但成功了: {invalid}")
        return 1
    except ValidationError as e:
        print(f"✅ 正确捕获验证错误:")
        print(f"   {e.error_count()} 个错误")

    # 测试 3: JSON 序列化
    print("\n测试 3: JSON 序列化和反序列化")
    try:
        article = TestArticle(
            title="JSON 测试",
            content="测试 JSON 序列化功能"
        )
        json_str = article.model_dump_json(indent=2)
        print(f"✅ JSON 序列化成功:")
        print(f"   {json_str[:100]}...")

        # 反序列化
        restored = TestArticle.model_validate_json(json_str)
        print(f"✅ JSON 反序列化成功: {restored.title}")
    except Exception as e:
        print(f"❌ 失败: {e}")
        return 1

    # 测试 4: 字段默认值
    print("\n测试 4: 测试默认值")
    try:
        minimal = TestArticle(
            title="最小文章",
            content="只有必填字段"
        )
        print(f"✅ 默认值工作正常:")
        print(f"   author: {minimal.author} (None)")
        print(f"   tags: {minimal.tags} ([])")
    except Exception as e:
        print(f"❌ 失败: {e}")
        return 1

    print("\n" + "=" * 70)
    print("🎉 所有 Pydantic 测试通过！")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    import sys
    try:
        import pydantic
        print(f"\n📦 Pydantic 版本: {pydantic.__version__}")
        sys.exit(main())
    except ImportError as e:
        print(f"❌ 无法导入 Pydantic: {e}")
        sys.exit(1)
