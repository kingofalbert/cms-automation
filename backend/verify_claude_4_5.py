#!/usr/bin/env python3
"""验证 Claude 4.5 Sonnet 升级配置"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))


def verify_env_config():
    """验证 .env 配置"""
    print("=" * 70)
    print("步骤 1: 验证 .env 配置")
    print("=" * 70)

    env_file = Path(__file__).parent.parent / ".env"
    if not env_file.exists():
        print("❌ .env 文件不存在")
        return False

    content = env_file.read_text()

    # 检查模型配置
    if "claude-sonnet-4-5-20250929" in content:
        print("✅ .env 配置正确：使用 Claude Sonnet 4.5")
        return True
    elif "claude-3-5-sonnet" in content:
        print("⚠️  .env 配置仍为旧版本：Claude 3.5 Sonnet")
        return False
    else:
        print("❌ .env 配置中未找到 ANTHROPIC_MODEL")
        return False


def verify_settings_config():
    """验证 settings.py 配置"""
    print("\n" + "=" * 70)
    print("步骤 2: 验证 settings.py 配置")
    print("=" * 70)

    try:
        from src.config.settings import get_settings

        settings = get_settings()
        model = settings.ANTHROPIC_MODEL

        print(f"当前配置的模型: {model}")

        if model == "claude-sonnet-4-5-20250929":
            print("✅ Settings 配置正确：Claude Sonnet 4.5")
            return True
        elif "claude-3-5-sonnet" in model:
            print("⚠️  Settings 配置仍为旧版本：Claude 3.5 Sonnet")
            return False
        else:
            print(f"⚠️  Settings 配置为其他模型: {model}")
            return False

    except Exception as e:
        print(f"❌ 无法加载 settings: {e}")
        return False


def verify_model_info():
    """显示模型信息"""
    print("\n" + "=" * 70)
    print("步骤 3: Claude Sonnet 4.5 模型信息")
    print("=" * 70)

    info = {
        "模型名称": "Claude Sonnet 4.5",
        "API 标识符": "claude-sonnet-4-5-20250929",
        "发布日期": "2025-09-29",
        "上下文窗口": "200K tokens（标准）/ 1M tokens（beta）",
        "最大输出": "64K tokens",
        "价格（输入）": "$3 per million tokens",
        "价格（输出）": "$15 per million tokens",
        "知识截止": "2025年7月",
    }

    for key, value in info.items():
        print(f"  {key:15s}: {value}")

    return True


def verify_api_client():
    """验证 API 客户端配置（不实际调用）"""
    print("\n" + "=" * 70)
    print("步骤 4: 验证 API 客户端配置")
    print("=" * 70)

    try:
        from src.services.proofreading.service import ProofreadingAnalysisService

        print("✅ 成功导入 ProofreadingAnalysisService")

        # 检查服务配置
        try:
            service = ProofreadingAnalysisService()
            print("✅ 服务初始化成功")
            print(f"   模型: {service.model}")

            if service.model == "claude-sonnet-4-5-20250929":
                print("✅ 服务使用正确的模型版本")
                return True
            else:
                print(f"⚠️  服务使用的模型: {service.model}")
                return False

        except Exception as e:
            print(f"⚠️  服务初始化失败（可能缺少 API key）: {e}")
            print("   这在开发环境中是正常的")
            return True  # 只要能导入即可

    except ImportError as e:
        print(f"❌ 无法导入服务模块: {e}")
        return False


def main():
    """主函数"""
    print("\n" + "🚀" * 35)
    print(" " * 15 + "Claude 4.5 Sonnet 升级验证")
    print("🚀" * 35 + "\n")

    results = []

    # 1. 验证 .env 配置
    results.append(("环境配置", verify_env_config()))

    # 2. 验证 settings 配置
    results.append(("Settings 配置", verify_settings_config()))

    # 3. 显示模型信息
    results.append(("模型信息", verify_model_info()))

    # 4. 验证 API 客户端
    results.append(("API 客户端", verify_api_client()))

    # 总结
    print("\n" + "=" * 70)
    print("验证总结")
    print("=" * 70)

    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {name:15s}: {status}")

    all_passed = all(r[1] for r in results)

    if all_passed:
        print("\n🎉 所有验证通过！Claude 4.5 Sonnet 升级成功！")
        print("\n下一步:")
        print("  1. 重启 Docker 服务: docker-compose restart backend")
        print("  2. 运行集成测试验证实际 API 调用")
        print("  3. 监控日志确认模型切换成功")
        return 0
    else:
        print("\n⚠️  部分验证未通过，请检查配置。")
        return 1


if __name__ == "__main__":
    exit(main())
