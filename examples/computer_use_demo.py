#!/usr/bin/env python3
"""
Computer Use Provider 使用示例

演示如何使用 Computer Use Provider 进行 WordPress 自动化发布

注意：
- 此示例需要有效的 ANTHROPIC_API_KEY 环境变量
- 实际运行会调用 Anthropic Computer Use API（会产生费用）
- 建议先在测试环境中运行
"""

import asyncio
import os
from datetime import datetime
from pathlib import Path

# 将项目根目录添加到 Python 路径
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config.computer_use_loader import load_instruction_templates
from src.providers.computer_use_provider import ComputerUseProvider
from src.models import (
    Article,
    ImageAsset,
    ArticleMetadata,
    SEOData,
    WordPressCredentials,
    PublishingContext
)


async def demo_basic_usage():
    """演示基本使用流程"""
    print("=" * 60)
    print("Computer Use Provider 基础使用示例")
    print("=" * 60)
    print()

    # 检查 API Key
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("❌ 错误：未找到 ANTHROPIC_API_KEY 环境变量")
        print("请设置环境变量：export ANTHROPIC_API_KEY='your-key-here'")
        return

    # 步骤 1: 加载指令模板
    print("📋 步骤 1: 加载指令模板")
    try:
        instructions = load_instruction_templates()
        print(f"✅ 成功加载 {len(instructions.templates)} 个指令模板")
        print(f"   可用模板: {', '.join(instructions.list_templates()[:5])}...")
        print()
    except Exception as e:
        print(f"❌ 加载指令模板失败: {e}")
        return

    # 步骤 2: 创建 Provider 实例
    print("🤖 步骤 2: 创建 Computer Use Provider")
    try:
        provider = ComputerUseProvider(
            api_key=api_key,
            instructions=instructions,
            display_width=1920,
            display_height=1080
        )
        print("✅ Provider 创建成功")
        print()
    except Exception as e:
        print(f"❌ Provider 创建失败: {e}")
        return

    # 步骤 3: 准备测试数据
    print("📝 步骤 3: 准备测试文章数据")

    # 创建 SEO 数据
    seo_data = SEOData(
        focus_keyword="WordPress自动化",
        meta_title="使用 Computer Use 实现 WordPress 自动化发布 - 技术教程",
        meta_description="本文介绍如何使用 Anthropic Computer Use API 实现 WordPress 后台自动化发布，包括文章创建、图片上传、SEO配置等完整流程。适合需要批量发布内容的开发者和内容团队。",
        primary_keywords=["Computer Use", "WordPress", "自动化", "AI"],
        secondary_keywords=["Anthropic", "Claude", "发布系统"]
    )

    # 创建文章
    article = Article(
        id=1,
        title="使用 Computer Use 实现 WordPress 自动化发布",
        content_html="""
<h2>什么是 Computer Use？</h2>
<p>Computer Use 是 Anthropic 推出的新功能，允许 Claude 通过视觉识别和自然语言指令来操作计算机界面。</p>

<h2>核心优势</h2>
<ul>
    <li>自然语言控制：无需编写复杂的选择器</li>
    <li>视觉适应：自动应对页面布局变化</li>
    <li>智能降级：Playwright 失败时自动切换</li>
</ul>

<h2>应用场景</h2>
<p>特别适合需要处理动态UI、频繁更新的WordPress站点，以及需要快速部署的MVP项目。</p>
        """,
        excerpt="介绍如何使用 Computer Use API 实现 WordPress 自动化发布",
        seo=seo_data
    )

    # 创建文章元数据
    metadata = ArticleMetadata(
        tags=["Computer Use", "WordPress", "自动化", "AI"],
        categories=["技术", "教程"],
        publish_immediately=True,
        status="publish"
    )

    # 创建凭证
    credentials = WordPressCredentials(
        username=os.getenv('PROD_USERNAME', 'your_username'),
        password=os.getenv('PROD_PASSWORD', 'your_password')
    )

    # WordPress URL
    wordpress_url = os.getenv('PROD_WORDPRESS_URL', 'https://example.com')

    print(f"✅ 测试数据准备完成")
    print(f"   文章标题: {article.title}")
    print(f"   标签数量: {len(metadata.tags)}")
    print(f"   分类数量: {len(metadata.categories)}")
    print(f"   WordPress URL: {wordpress_url}")
    print()

    # 步骤 4: 创建发布上下文
    print("🎯 步骤 4: 创建发布上下文")
    context = PublishingContext(
        task_id=f"demo-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        article=article,
        images=[],  # 暂不包含图片
        metadata=metadata,
        wordpress_url=wordpress_url,
        credentials=credentials
    )
    print(f"✅ 发布上下文创建完成，任务 ID: {context.task_id}")
    print()

    # 步骤 5: 执行发布（实际调用 API）
    print("🚀 步骤 5: 开始发布流程")
    print("⚠️  警告：此操作将调用 Anthropic API，会产生费用")
    print()

    # 询问用户是否继续
    response = input("是否继续执行？(yes/no): ").strip().lower()
    if response not in ['yes', 'y']:
        print("❌ 用户取消操作")
        return

    try:
        print("\n开始执行发布...")
        print("-" * 60)

        # 执行发布
        result = await provider.publish_article(context)

        print("-" * 60)
        print("\n📊 发布结果:")
        print(f"   状态: {'✅ 成功' if result.success else '❌ 失败'}")
        print(f"   任务 ID: {result.task_id}")
        print(f"   耗时: {result.duration_seconds:.2f} 秒")
        print(f"   Provider: {result.provider_used}")
        print(f"   重试次数: {result.retry_count}")

        if result.success:
            print(f"   文章 URL: {result.url}")
        else:
            print(f"   错误信息: {result.error}")

        print()

    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断操作")
    except Exception as e:
        print(f"\n❌ 发布失败: {e}")
        import traceback
        print(traceback.format_exc())


async def demo_instruction_templates():
    """演示指令模板的使用"""
    print("=" * 60)
    print("指令模板使用示例")
    print("=" * 60)
    print()

    # 加载模板
    print("📋 加载指令模板...")
    instructions = load_instruction_templates()
    print(f"✅ 成功加载 {len(instructions.templates)} 个模板\n")

    # 示例 1: 登录指令
    print("1️⃣  登录指令示例:")
    login_instruction = instructions.get(
        'login_to_wordpress',
        username='admin',
        password='******'
    )
    print(f"   {login_instruction[:80]}...")
    print()

    # 示例 2: 填写标题
    print("2️⃣  填写标题指令示例:")
    title_instruction = instructions.get(
        'fill_title',
        value='测试文章标题'
    )
    print(f"   {title_instruction[:80]}...")
    print()

    # 示例 3: 上传文件
    print("3️⃣  上传文件指令示例:")
    upload_instruction = instructions.get(
        'upload_file',
        file_path='/path/to/image.jpg'
    )
    print(f"   {upload_instruction[:80]}...")
    print()

    # 示例 4: 配置 SEO
    print("4️⃣  配置 SEO 指令示例:")
    seo_instruction = instructions.get(
        'configure_seo_plugin',
        focus_keyword='WordPress',
        meta_title='测试 SEO 标题',
        meta_description='这是一个测试的 Meta 描述'
    )
    print(f"   {seo_instruction[:80]}...")
    print()

    # 列出所有模板
    print("📋 所有可用模板:")
    for i, template_name in enumerate(instructions.list_templates(), 1):
        info = instructions.get_template_info(template_name)
        vars_str = f"[{', '.join(info['variables'])}]" if info['variables'] else "[无变量]"
        print(f"   {i:2d}. {template_name:30s} {vars_str}")

    print()


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("Computer Use Provider 演示程序")
    print("=" * 60)
    print()
    print("请选择演示模式：")
    print("  1. 指令模板演示（安全，不调用 API）")
    print("  2. 完整发布流程演示（需要 API Key，会产生费用）")
    print("  3. 退出")
    print()

    choice = input("请输入选择 (1/2/3): ").strip()

    if choice == '1':
        asyncio.run(demo_instruction_templates())
    elif choice == '2':
        asyncio.run(demo_basic_usage())
    elif choice == '3':
        print("👋 再见！")
    else:
        print("❌ 无效选择")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  程序被用户中断")
    except Exception as e:
        print(f"\n❌ 程序错误: {e}")
        import traceback
        traceback.print_exc()
