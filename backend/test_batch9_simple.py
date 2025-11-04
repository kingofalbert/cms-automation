#!/usr/bin/env python3
"""简化验证 Batch 9 (D/E 类) 规则加载。"""

from src.services.proofreading.deterministic_engine import DeterministicRuleEngine


def main():
    """验证规则加载。"""
    print("=" * 70)
    print(" Batch 9 规则加载验证")
    print("=" * 70)

    try:
        engine = DeterministicRuleEngine()
        print("\n✅ 引擎初始化成功")
        print("\n📊 规则统计:")
        print(f"   总规则数: {len(engine.rules)}")

        # 按类别统计
        categories = {}
        for rule in engine.rules:
            cat = rule.category
            categories[cat] = categories.get(cat, 0) + 1

        print("\n📋 分类详情:")
        for cat in sorted(categories.keys()):
            emoji = "⭐" if cat in ["D", "E"] else "  "
            print(f"   {emoji} {cat} 类: {categories[cat]:3d} 条")

        # 重点验证 D/E 类
        d_count = categories.get("D", 0)
        e_count = categories.get("E", 0)

        print("\n🎯 Batch 9 验证:")
        print(f"   D 类规则: {d_count} 条 {'✅' if d_count >= 40 else '❌'}")
        print(f"   E 类规则: {e_count} 条 {'✅' if e_count >= 40 else '❌'}")

        # 展示几个 D 类规则示例
        d_rules = [r for r in engine.rules if r.category == "D"][:5]
        if d_rules:
            print("\n📝 D 类规则示例（前5条）:")
            for rule in d_rules:
                print(f"   - {rule.rule_id}: {rule.category}/{rule.subcategory}")

        # 展示几个 E 类规则示例
        e_rules = [r for r in engine.rules if r.category == "E"][:5]
        if e_rules:
            print("\n📝 E 类规则示例（前5条）:")
            for rule in e_rules:
                print(f"   - {rule.rule_id}: {rule.category}/{rule.subcategory}")

        # 最终判断
        total_expected = 355
        d_expected = 40
        e_expected = 40

        success = (
            len(engine.rules) >= total_expected
            and d_count >= d_expected
            and e_count >= e_expected
        )

        print(f"\n{'=' * 70}")
        if success:
            print(" 🎉 验证成功！Batch 9 规则已正确加载！")
            print(f"    - 总规则数: {len(engine.rules)}/{total_expected} ✅")
            print(f"    - D 类规则: {d_count}/{d_expected} ✅")
            print(f"    - E 类规则: {e_count}/{e_expected} ✅")
        else:
            print(" ⚠️  验证未完全通过")
            print(f"    - 总规则数: {len(engine.rules)}/{total_expected}")
            print(f"    - D 类规则: {d_count}/{d_expected}")
            print(f"    - E 类规则: {e_count}/{e_expected}")
        print(f"{'=' * 70}\n")

        return 0 if success else 1

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
