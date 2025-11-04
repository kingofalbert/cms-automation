#!/usr/bin/env python3
"""本地环境测试脚本 - 直接测试引擎加载"""

import importlib.util

# 直接加载模块文件，绕过 __init__.py
spec = importlib.util.spec_from_file_location(
    "deterministic_engine",
    "src/services/proofreading/deterministic_engine.py"
)
engine_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine_module)

# 也需要加载 models
spec_models = importlib.util.spec_from_file_location(
    "models",
    "src/services/proofreading/models.py"
)
models_module = importlib.util.module_from_spec(spec_models)

# 模拟 pydantic models
# 实际上我们只需要类定义，不需要完整的功能
try:
    spec_models.loader.exec_module(models_module)
except Exception as e:
    print(f"Note: Could not load models fully: {e}")
    print("Trying simplified approach...\n")

# 现在测试引擎
try:
    DeterministicRuleEngine = engine_module.DeterministicRuleEngine

    print("=" * 70)
    print("本地环境 - 校对引擎测试")
    print("=" * 70)

    engine = DeterministicRuleEngine()
    print("\n✅ 引擎加载成功")
    print(f"📊 总规则数: {len(engine.rules)}")

    # Count by category
    categories = {}
    for rule in engine.rules:
        cat = rule.category
        categories[cat] = categories.get(cat, 0) + 1

    print("\n📋 规则分类:")
    for cat in sorted(categories.keys()):
        emoji = '✅' if cat in ['A', 'B', 'C', 'D', 'E', 'F'] else ''
        print(f"  {emoji} {cat} 类: {categories[cat]:3d} 条")

    if len(engine.rules) == 384:
        print("\n🎊 成功！100% 覆盖率 (384/384 规则)")
        print("=" * 70)
        exit(0)
    else:
        print(f"\n⚠️  期望 384 条，实际 {len(engine.rules)} 条")
        print("=" * 70)
        exit(1)

except Exception as e:
    print(f"\n❌ 错误: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
