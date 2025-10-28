"""
配置加载器验证测试

验证所有配置文件能否正常加载和使用
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config.loader import config, settings


def test_settings_loaded():
    """测试 Settings 是否正确加载"""
    print("=" * 60)
    print("测试 1: Settings 加载")
    print("=" * 60)

    assert settings is not None, "Settings 未加载"

    # 检查关键配置
    print(f"✓ WordPress URL: {settings.wordpress_url}")
    print(f"✓ Default Provider: {settings.default_provider}")
    print(f"✓ Browser Type: {settings.browser_type}")
    print(f"✓ Playwright Headless: {settings.playwright_headless}")
    print(f"✓ Enable Screenshots: {settings.enable_screenshots}")
    print(f"✓ Screenshot Path: {settings.screenshot_path}")

    print("\n✅ Settings 加载成功！\n")


def test_selectors_loaded():
    """测试 Selectors 配置是否正确加载"""
    print("=" * 60)
    print("测试 2: Selectors 配置加载")
    print("=" * 60)

    selectors = config.selectors
    assert selectors is not None, "Selectors 配置未加载"
    assert len(selectors) > 0, "Selectors 配置为空"

    # 检查关键选择器
    critical_selectors = [
        ('login', 'username_input'),
        ('login', 'password_input'),
        ('login', 'submit_button'),
        ('editor', 'classic', 'title_input'),
        ('editor', 'classic', 'text_editor'),
        ('yoast_seo', 'focus_keyword', 'input'),
        ('yoast_seo', 'meta_title', 'input'),
        ('yoast_seo', 'meta_description', 'textarea'),
        ('publish', 'publish_button'),
        ('media', 'modal', 'container'),
    ]

    print(f"总共 {len(selectors)} 个选择器类别")
    print("\n检查关键选择器:")

    for keys in critical_selectors:
        selector = config.get_selector(*keys)
        assert selector is not None, f"选择器 {'.'.join(keys)} 未找到"
        print(f"  ✓ {'.'.join(keys)}: {selector}")

    print("\n✅ Selectors 配置加载成功！\n")


def test_instructions_loaded():
    """测试 Instructions 配置是否正确加载"""
    print("=" * 60)
    print("测试 3: Instructions 配置加载")
    print("=" * 60)

    instructions = config.instructions
    assert instructions is not None, "Instructions 配置未加载"
    assert len(instructions) > 0, "Instructions 配置为空"

    # 检查关键指令
    critical_instructions = [
        ('login', 'enter_credentials'),
        ('navigation', 'go_to_new_post'),
        ('article', 'enter_title'),
        ('article', 'enter_content'),
        ('taxonomy', 'add_categories'),
        ('taxonomy', 'add_tags'),
        ('media', 'upload_image'),
        ('media', 'set_as_featured_image'),
        ('yoast_seo', 'set_focus_keyword'),
        ('yoast_seo', 'set_seo_title'),
        ('yoast_seo', 'set_meta_description'),
        ('publish', 'publish_immediately'),
    ]

    print(f"总共 {len(instructions)} 个指令类别")
    print("\n检查关键指令:")

    for keys in critical_instructions:
        instruction = config.get_instruction(*keys)
        assert instruction is not None, f"指令 {'.'.join(keys)} 未找到"
        # 只打印前 60 个字符
        preview = instruction[:60].replace('\n', ' ') + "..." if len(instruction) > 60 else instruction.replace('\n', ' ')
        print(f"  ✓ {'.'.join(keys)}: {preview}")

    print("\n✅ Instructions 配置加载成功！\n")


def test_selectors_validation():
    """测试选择器验证功能"""
    print("=" * 60)
    print("测试 4: Selectors 验证")
    print("=" * 60)

    validation_results = config.validate_selectors()

    print("验证结果:")
    print(f"  缺少的关键选择器: {len(validation_results['missing_critical'])}")
    print(f"  缺少的重要选择器: {len(validation_results['missing_important'])}")
    print(f"  缺少的可选选择器: {len(validation_results['missing_optional'])}")

    if validation_results['missing_critical']:
        print("\n⚠️  警告：缺少关键选择器:")
        for selector in validation_results['missing_critical']:
            print(f"    - {selector}")
        raise AssertionError("存在缺少的关键选择器")

    if validation_results['missing_important']:
        print("\n⚠️  提示：缺少重要选择器:")
        for selector in validation_results['missing_important']:
            print(f"    - {selector}")

    print("\n✅ 选择器验证通过！\n")


def test_instruction_formatting():
    """测试指令格式化功能"""
    print("=" * 60)
    print("测试 5: 指令格式化")
    print("=" * 60)

    # 测试带参数的指令
    test_cases = [
        {
            'keys': ('article', 'enter_title'),
            'params': {'title': '测试文章标题'},
            'expected_contains': '测试文章标题'
        },
        {
            'keys': ('media', 'upload_image'),
            'params': {'file_path': '/path/to/image.jpg'},
            'expected_contains': '/path/to/image.jpg'
        },
        {
            'keys': ('yoast_seo', 'set_focus_keyword'),
            'params': {'focus_keyword': 'WordPress'},
            'expected_contains': 'WordPress'
        },
    ]

    for i, test in enumerate(test_cases, 1):
        formatted = config.format_instruction(*test['keys'], **test['params'])
        assert formatted is not None, f"指令格式化失败: {'.'.join(test['keys'])}"
        assert test['expected_contains'] in formatted, f"格式化结果不包含预期内容: {test['expected_contains']}"
        preview = formatted[:80].replace('\n', ' ') + "..." if len(formatted) > 80 else formatted.replace('\n', ' ')
        print(f"  ✓ 测试 {i}: {preview}")

    print("\n✅ 指令格式化功能正常！\n")


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("配置加载器验证测试")
    print("=" * 60 + "\n")

    try:
        test_settings_loaded()
        test_selectors_loaded()
        test_instructions_loaded()
        test_selectors_validation()
        test_instruction_formatting()

        print("=" * 60)
        print("🎉 所有测试通过！")
        print("=" * 60)
        print("\n配置系统工作正常，可以继续开发。\n")

        return 0

    except Exception as e:
        print(f"\n❌ 测试失败: {e}\n")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit(main())
