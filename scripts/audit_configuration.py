#!/usr/bin/env python3
"""
配置审计工具
检查所有必需的配置项是否已正确设置
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "backend"))

from src.config import get_settings
from pydantic import ValidationError
import os


def check_secret_key_strength(secret_key: str) -> tuple[bool, str]:
    """检查 SECRET_KEY 强度"""
    if len(secret_key) < 32:
        return False, f"❌ SECRET_KEY 太短 ({len(secret_key)} 字符，需要至少 32 字符)"

    if secret_key in ["dev-secret-key-please-change-in-production", "your-secret-key-here-minimum-32-characters-long"]:
        return False, "⚠️  SECRET_KEY 使用了示例值，应该生成随机密钥"

    # 检查熵
    unique_chars = len(set(secret_key))
    if unique_chars < 16:
        return False, f"⚠️  SECRET_KEY 字符多样性不足 (仅 {unique_chars} 种不同字符)"

    return True, "✅ SECRET_KEY 强度良好"


def check_google_drive_config() -> dict:
    """检查 Google Drive 配置"""
    results = {}

    # 检查凭证文件
    creds_path = project_root / "backend" / "credentials" / "google-drive-credentials.json"
    if creds_path.exists():
        results["credentials_file"] = ("✅", f"凭证文件存在: {creds_path}")

        # 检查文件权限
        import stat
        file_stat = creds_path.stat()
        if file_stat.st_mode & 0o077:
            results["credentials_permissions"] = ("⚠️", "文件权限过于宽松，建议运行: chmod 600 " + str(creds_path))
        else:
            results["credentials_permissions"] = ("✅", "文件权限安全 (600)")
    else:
        results["credentials_file"] = ("❌", f"凭证文件不存在: {creds_path}")

    return results


def check_database_connection() -> tuple[bool, str]:
    """检查数据库连接"""
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.pool import NullPool

        settings = get_settings()
        engine = create_engine(
            str(settings.DATABASE_URL),
            poolclass=NullPool,
            connect_args={"connect_timeout": 5}
        )

        with engine.connect() as conn:
            conn.execute("SELECT 1")

        return True, "✅ 数据库连接正常"
    except Exception as e:
        return False, f"❌ 数据库连接失败: {str(e)[:100]}"


def check_redis_connection() -> tuple[bool, str]:
    """检查 Redis 连接"""
    try:
        import redis
        settings = get_settings()

        # 从 URL 解析 Redis 配置
        r = redis.from_url(str(settings.REDIS_URL), socket_connect_timeout=5)
        r.ping()

        return True, "✅ Redis 连接正常"
    except Exception as e:
        return False, f"❌ Redis 连接失败: {str(e)[:100]}"


def check_anthropic_api() -> tuple[bool, str]:
    """检查 Anthropic API"""
    try:
        settings = get_settings()

        if not settings.ANTHROPIC_API_KEY:
            return False, "❌ ANTHROPIC_API_KEY 未设置"

        if settings.ANTHROPIC_API_KEY == "your-anthropic-api-key-here":
            return False, "⚠️  ANTHROPIC_API_KEY 使用了示例值"

        if not settings.ANTHROPIC_API_KEY.startswith("sk-ant-api"):
            return False, "⚠️  ANTHROPIC_API_KEY 格式可能不正确"

        return True, "✅ ANTHROPIC_API_KEY 已设置"
    except Exception as e:
        return False, f"❌ Anthropic 配置检查失败: {str(e)[:100]}"


def check_wordpress_config() -> dict:
    """检查 WordPress 配置"""
    results = {}
    settings = get_settings()

    if not settings.CMS_BASE_URL:
        results["base_url"] = ("❌", "CMS_BASE_URL 未设置")
    elif settings.CMS_BASE_URL == "https://your-wordpress-site.com":
        results["base_url"] = ("⚠️", "CMS_BASE_URL 使用了示例值")
    else:
        results["base_url"] = ("✅", f"CMS_BASE_URL: {settings.CMS_BASE_URL}")

    if not settings.CMS_USERNAME:
        results["username"] = ("❌", "CMS_USERNAME 未设置")
    elif settings.CMS_USERNAME == "your-wordpress-username":
        results["username"] = ("⚠️", "CMS_USERNAME 使用了示例值")
    else:
        results["username"] = ("✅", f"CMS_USERNAME: {settings.CMS_USERNAME}")

    if not settings.CMS_APPLICATION_PASSWORD:
        results["password"] = ("❌", "CMS_APPLICATION_PASSWORD 未设置")
    elif settings.CMS_APPLICATION_PASSWORD == "your-wordpress-app-password":
        results["password"] = ("⚠️", "CMS_APPLICATION_PASSWORD 使用了示例值")
    else:
        results["password"] = ("✅", "CMS_APPLICATION_PASSWORD 已设置")

    return results


def main():
    """主函数"""
    print("🔍 CMS Automation 配置审计工具\n")
    print("=" * 70)

    issues = []
    warnings = []
    success = []

    # 1. 加载配置
    print("\n📋 1. 加载配置文件...")
    try:
        settings = get_settings()
        success.append("配置文件加载成功")
        print("✅ 配置文件加载成功")
    except ValidationError as e:
        print(f"❌ 配置验证失败:")
        for error in e.errors():
            field = " -> ".join(str(x) for x in error["loc"])
            print(f"   • {field}: {error['msg']}")
        return False
    except Exception as e:
        print(f"❌ 加载配置失败: {e}")
        return False

    # 2. 检查 SECRET_KEY
    print("\n🔐 2. 检查 SECRET_KEY...")
    is_strong, message = check_secret_key_strength(settings.SECRET_KEY)
    print(f"   {message}")
    if not is_strong:
        if message.startswith("❌"):
            issues.append(message)
        else:
            warnings.append(message)
    else:
        success.append("SECRET_KEY 配置正确")

    # 3. 检查数据库
    print("\n💾 3. 检查数据库连接...")
    db_ok, db_message = check_database_connection()
    print(f"   {db_message}")
    if db_ok:
        success.append("数据库连接正常")
    else:
        issues.append(db_message)

    # 4. 检查 Redis
    print("\n🔴 4. 检查 Redis 连接...")
    redis_ok, redis_message = check_redis_connection()
    print(f"   {redis_message}")
    if redis_ok:
        success.append("Redis 连接正常")
    else:
        issues.append(redis_message)

    # 5. 检查 Anthropic API
    print("\n🤖 5. 检查 Anthropic API...")
    anthropic_ok, anthropic_message = check_anthropic_api()
    print(f"   {anthropic_message}")
    if anthropic_ok:
        success.append("Anthropic API 配置正确")
    else:
        if anthropic_message.startswith("❌"):
            issues.append(anthropic_message)
        else:
            warnings.append(anthropic_message)

    # 6. 检查 Google Drive
    print("\n📁 6. 检查 Google Drive 配置...")
    gd_results = check_google_drive_config()
    for key, (status, message) in gd_results.items():
        print(f"   {message}")
        if status == "❌":
            issues.append(message)
        elif status == "⚠️":
            warnings.append(message)
        else:
            success.append(message)

    # 7. 检查 WordPress
    print("\n📝 7. 检查 WordPress 配置...")
    wp_results = check_wordpress_config()
    for key, (status, message) in wp_results.items():
        print(f"   {message}")
        if status == "❌":
            issues.append(message)
        elif status == "⚠️":
            warnings.append(message)
        else:
            success.append(message)

    # 8. 检查环境变量
    print("\n🌍 8. 检查环境配置...")
    print(f"   环境: {settings.ENVIRONMENT}")
    print(f"   日志级别: {settings.LOG_LEVEL}")
    print(f"   API 端口: {settings.API_PORT}")

    # 总结
    print("\n" + "=" * 70)
    print("\n📊 审计总结:\n")

    print(f"✅ 成功项: {len(success)}")
    print(f"⚠️  警告项: {len(warnings)}")
    print(f"❌ 错误项: {len(issues)}")

    if issues:
        print("\n❌ 发现以下严重问题:")
        for i, issue in enumerate(issues, 1):
            print(f"   {i}. {issue}")

    if warnings:
        print("\n⚠️  发现以下警告:")
        for i, warning in enumerate(warnings, 1):
            print(f"   {i}. {warning}")

    # 提供修复建议
    if issues or warnings:
        print("\n💡 修复建议:\n")

        if any("SECRET_KEY" in item for item in issues + warnings):
            print("   • 生成新的 SECRET_KEY:")
            print("     openssl rand -hex 32")
            print("     然后更新 .env 文件中的 SECRET_KEY\n")

        if any("Redis" in item for item in issues):
            print("   • 启动 Redis 服务:")
            print("     brew services start redis")
            print("     或检查 REDIS_URL 配置\n")

        if any("数据库" in item for item in issues):
            print("   • 检查数据库连接:")
            print("     确认 DATABASE_URL 配置正确")
            print("     确认数据库服务正在运行\n")

        if any("Google Drive" in item for item in issues):
            print("   • 配置 Google Drive:")
            print("     参考: backend/GOOGLE_DRIVE_SETUP_QUICKSTART.md")
            print("     或运行: python scripts/verify_google_drive.py\n")

        if any("WordPress" in item for item in issues + warnings):
            print("   • 配置 WordPress 凭证:")
            print("     在 WordPress 后台生成应用密码")
            print("     更新 .env 文件中的 CMS_* 配置\n")

    if not issues and not warnings:
        print("\n🎉 所有配置检查通过！系统已准备就绪。")
        return True
    elif not issues:
        print("\n✅ 配置基本完成，但有一些警告需要注意。")
        return True
    else:
        print("\n⚠️  发现严重问题，请先修复后再继续。")
        return False


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  审计被中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 发生未预期的错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
