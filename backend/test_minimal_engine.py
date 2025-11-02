#!/usr/bin/env python3
"""最小化引擎测试 - 完全绕过包导入"""

import sys
import re

# 直接读取并执行 rule_specs.py
with open('src/services/proofreading/rule_specs.py', 'r', encoding='utf-8') as f:
    rule_specs_code = f.read()

# 创建一个命名空间来执行规则定义
rule_specs_namespace = {}
exec(rule_specs_code, rule_specs_namespace)

# 提取规则数据
A4_SPECS = rule_specs_namespace.get('A4_INFORMAL_SPECS', [])
D_SPECS = rule_specs_namespace.get('D_TRANSLATION_SPECS', [])
E_SPECS = rule_specs_namespace.get('E_SPECIAL_SPECS', [])

print("=" * 70)
print("本地环境 - 校对规则数据验证")
print("=" * 70)

print(f"\n✅ 规则数据加载成功")
print(f"\n📊 规则统计:")
print(f"   A4 类 (非正式用语): {len(A4_SPECS)} 条")
print(f"   D 类 (译名规范): {len(D_SPECS)} 条")
print(f"   E 类 (特殊规范): {len(E_SPECS)} 条")
print(f"   字典规则总计: {len(A4_SPECS) + len(D_SPECS) + len(E_SPECS)} 条")

# 验证 A4 规则
print(f"\n📝 A4 类规则示例（前3条）:")
for rule in A4_SPECS[:3]:
    print(f"   - {rule['rule_id']}: {rule['description']}")

# 计算预期规则数
# A4: 29 条字典规则 + 1 条特殊类规则 (InformalLanguageRule) = 30 条
# D: 40 条字典规则
# E: 40 条字典规则
# 总计: 109 条字典规则
expected_a4_dict = 29  # A4-014 作为特殊类实现
expected_d = 40
expected_e = 40
expected_dict_total = 109

print(f"\n🎯 规则验证:")
print(f"   A4 字典规则: {len(A4_SPECS)}/{expected_a4_dict} (A4-014 为特殊类)")
print(f"   D 字典规则:  {len(D_SPECS)}/{expected_d}")
print(f"   E 字典规则:  {len(E_SPECS)}/{expected_e}")
print(f"   字典规则总计: {len(A4_SPECS) + len(D_SPECS) + len(E_SPECS)}/{expected_dict_total}")

# 完整引擎应有 384 条规则
# A1:50, A2:30, A3:70, A4:30, B:60, C:24, D:40, E:40, F:40
expected_total_rules = 384
print(f"\n📊 完整引擎规则数: {expected_total_rules} 条")
print(f"   其中字典驱动: {expected_dict_total} 条 (28.4%)")

if len(A4_SPECS) == expected_a4_dict and len(D_SPECS) == expected_d and len(E_SPECS) == expected_e:
    print(f"\n🎊 验证成功！字典规则数据完整！")
    print(f"   ✅ A4 字典规则: 29 条")
    print(f"   ✅ D 字典规则: 40 条")
    print(f"   ✅ E 字典规则: 40 条")
    print("=" * 70)
    exit(0)
else:
    print(f"\n⚠️  规则数据不完整")
    print("=" * 70)
    exit(1)
