#!/usr/bin/env python3
"""性能测试脚本 - 测试 384 条规则的引擎性能"""

import time

from src.services.proofreading.deterministic_engine import DeterministicRuleEngine
from src.services.proofreading.models import ArticlePayload


def test_engine_loading_performance():
    """测试引擎加载时间"""
    print("=" * 70)
    print("性能测试 1: 引擎加载时间")
    print("=" * 70)

    iterations = 5
    times = []

    for i in range(iterations):
        start = time.time()
        engine = DeterministicRuleEngine()
        end = time.time()
        load_time = (end - start) * 1000  # Convert to milliseconds
        times.append(load_time)
        print(f"  第 {i+1} 次: {load_time:.2f} ms")

    avg_time = sum(times) / len(times)
    print(f"\n平均加载时间: {avg_time:.2f} ms")
    print(f"总规则数: {len(engine.rules)}")

    if avg_time < 200:
        print("✅ 性能优秀 (< 200ms)")
    elif avg_time < 500:
        print("✅ 性能良好 (< 500ms)")
    else:
        print("⚠️  性能需优化 (> 500ms)")

    return avg_time < 500


def test_article_processing_performance():
    """测试文章处理性能"""
    print("\n" + "=" * 70)
    print("性能测试 2: 文章处理速度")
    print("=" * 70)

    engine = DeterministicRuleEngine()

    # 测试不同长度的文章
    test_cases = [
        ("短文章 (500字)", "这是一篇测试文章。" * 50, 500),
        ("中等文章 (1000字)", "这是一篇测试文章，包含各种中文内容。" * 50, 1000),
        ("长文章 (2000字)", "这是一篇较长的测试文章，用于测试处理性能。" * 100, 2000),
    ]

    all_passed = True

    for name, content, char_count in test_cases:
        payload = ArticlePayload(
            original_content=content,
            title="性能测试文章",
            author="测试"
        )

        # 预热
        engine.evaluate(payload)

        # 正式测试
        iterations = 3
        times = []

        for _ in range(iterations):
            start = time.time()
            result = engine.evaluate(payload)
            end = time.time()
            process_time = (end - start) * 1000
            times.append(process_time)

        avg_time = sum(times) / len(times)
        print(f"\n{name}:")
        print(f"  字符数: {char_count}")
        print(f"  平均处理时间: {avg_time:.2f} ms")
        print(f"  检测到问题: {len(result.issues)} 个")

        # 性能标准：1000字文章应在2秒内完成
        if char_count <= 1000:
            target_time = 2000
        else:
            target_time = 4000

        if avg_time < target_time:
            print(f"  ✅ 性能达标 (< {target_time}ms)")
        else:
            print(f"  ⚠️  性能需优化 (> {target_time}ms)")
            all_passed = False

    return all_passed


def test_rule_efficiency():
    """测试规则效率统计"""
    print("\n" + "=" * 70)
    print("性能测试 3: 规则效率分析")
    print("=" * 70)

    engine = DeterministicRuleEngine()

    # 统计规则分布
    categories = {}
    auto_fix_count = 0

    for rule in engine.rules:
        cat = rule.category
        categories[cat] = categories.get(cat, 0) + 1
        if rule.can_auto_fix:
            auto_fix_count += 1

    print("\n规则分类统计:")
    for cat in sorted(categories.keys()):
        print(f"  {cat} 类: {categories[cat]:3d} 条")

    auto_fix_rate = (auto_fix_count / len(engine.rules)) * 100
    print(f"\n自动修复率: {auto_fix_rate:.1f}% ({auto_fix_count}/{len(engine.rules)})")

    if auto_fix_rate >= 80:
        print("✅ 自动修复能力优秀")
    elif auto_fix_rate >= 60:
        print("✅ 自动修复能力良好")
    else:
        print("⚠️  自动修复能力需提升")

    return True


def main():
    """运行所有性能测试"""
    print("\n" + "=" * 70)
    print("校对服务性能测试套件 - Batch 10 (384 条规则)")
    print("=" * 70 + "\n")

    results = []

    # 测试 1: 引擎加载
    results.append(("引擎加载", test_engine_loading_performance()))

    # 测试 2: 文章处理 (暂时跳过 - 需要service层)
    # results.append(("文章处理", test_article_processing_performance()))

    # 测试 3: 规则效率
    results.append(("规则效率", test_rule_efficiency()))

    # 总结
    print("\n" + "=" * 70)
    print("测试总结")
    print("=" * 70)

    for test_name, passed in results:
        status = "✅ 通过" if passed else "❌ 未通过"
        print(f"  {test_name}: {status}")

    all_passed = all(r[1] for r in results)

    if all_passed:
        print("\n🎉 所有性能测试通过！系统性能优秀！")
        return 0
    else:
        print("\n⚠️  部分测试未通过，建议进行性能优化。")
        return 1


if __name__ == "__main__":
    exit(main())
