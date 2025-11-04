#!/usr/bin/env python3
"""简化的配置检查脚本"""

import sys
import os
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "backend"))

def main():
    print("🔍 配置检查工具\n")
    print("=" * 70)

    issues = []
    warnings = []
    success_count = 0

    # 1. 检查 .env 文件
    print("\n1️⃣ 检查 .env 文件...")
    env_file = project_root / ".env"
    if env_file.exists():
        print("✅ .env 文件存在")
        success_count += 1
    else:
        print("❌ .env 文件不存在")
        issues.append(".env 文件缺失")

    # 2. 检查配置加载
    print("\n2️⃣ 检查配置加载...")
    try:
        from src.config import get_settings
        settings = get_settings()
        print("✅ 配置加载成功")
        success_count += 1
    except Exception as e:
        print(f"❌ 配置加载失败: {e}")
        issues.append(f"配置加载失败: {e}")
        return False

    # 3. 检查 SECRET_KEY
    print("\n3️⃣ 检查 SECRET_KEY...")
    if len(settings.SECRET_KEY) < 32:
        print(f"❌ SECRET_KEY 太短 ({len(settings.SECRET_KEY)} 字符)")
        issues.append("SECRET_KEY 太短")
    elif settings.SECRET_KEY == "dev-secret-key-please-change-in-production":
        print("⚠️  SECRET_KEY 使用示例值（开发环境可接受）")
        warnings.append("SECRET_KEY 使用示例值")
        success_count += 1
    else:
        print(f"✅ SECRET_KEY 长度正常 ({len(settings.SECRET_KEY)} 字符)")
        success_count += 1

    # 4. 检查数据库配置
    print("\n4️⃣ 检查数据库配置...")
    if settings.DATABASE_URL:
        db_url_str = str(settings.DATABASE_URL)
        if "supabase" in db_url_str:
            print("✅ 使用 Supabase 数据库")
        else:
            print(f"✅ DATABASE_URL 已配置")
        success_count += 1
    else:
        print("❌ DATABASE_URL 未配置")
        issues.append("DATABASE_URL 未配置")

    # 5. 检查 Redis
    print("\n5️⃣ 检查 Redis 配置...")
    if settings.REDIS_URL:
        print(f"✅ REDIS_URL: {settings.REDIS_URL}")
        success_count += 1
    else:
        print("❌ REDIS_URL 未配置")
        issues.append("REDIS_URL 未配置")

    # 6. 检查 Anthropic API
    print("\n6️⃣ 检查 Anthropic API...")
    if settings.ANTHROPIC_API_KEY and settings.ANTHROPIC_API_KEY != "your-anthropic-api-key-here":
        if settings.ANTHROPIC_API_KEY.startswith("sk-ant-api"):
            print("✅ ANTHROPIC_API_KEY 已配置")
            success_count += 1
        else:
            print("⚠️  ANTHROPIC_API_KEY 格式可能不正确")
            warnings.append("ANTHROPIC_API_KEY 格式异常")
    else:
        print("❌ ANTHROPIC_API_KEY 未配置")
        issues.append("ANTHROPIC_API_KEY 未配置")

    # 7. 检查 Google Drive
    print("\n7️⃣ 检查 Google Drive...")
    gd_creds = project_root / "backend" / "credentials" / "google-drive-credentials.json"
    if gd_creds.exists():
        print(f"✅ 凭证文件存在")
        success_count += 1

        # 检查权限
        import stat
        file_stat = gd_creds.stat()
        if file_stat.st_mode & 0o077:
            print("⚠️  文件权限过于宽松 (建议: chmod 600)")
            warnings.append("Google Drive 凭证文件权限不安全")
        else:
            print("✅ 文件权限安全")
            success_count += 1
    else:
        print(f"❌ 凭证文件不存在: {gd_creds}")
        issues.append("Google Drive 凭证文件缺失")

    if settings.GOOGLE_DRIVE_FOLDER_ID:
        print(f"✅ 文件夹 ID: {settings.GOOGLE_DRIVE_FOLDER_ID}")
        print(f"   URL: https://drive.google.com/drive/folders/{settings.GOOGLE_DRIVE_FOLDER_ID}")
        success_count += 1
    else:
        print("⚠️  GOOGLE_DRIVE_FOLDER_ID 未配置")
        warnings.append("GOOGLE_DRIVE_FOLDER_ID 未配置")

    # 8. 检查 WordPress
    print("\n8️⃣ 检查 WordPress 配置...")
    if settings.CMS_BASE_URL and settings.CMS_BASE_URL != "https://your-wordpress-site.com":
        print(f"✅ CMS_BASE_URL: {settings.CMS_BASE_URL}")
        success_count += 1
    else:
        print("⚠️  CMS_BASE_URL 使用示例值或未配置")
        warnings.append("CMS_BASE_URL 需要配置")

    if settings.CMS_USERNAME and settings.CMS_USERNAME != "your-wordpress-username":
        print(f"✅ CMS_USERNAME: {settings.CMS_USERNAME}")
        success_count += 1
    else:
        print("⚠️  CMS_USERNAME 未配置")
        warnings.append("CMS_USERNAME 需要配置")

    if settings.CMS_APPLICATION_PASSWORD and settings.CMS_APPLICATION_PASSWORD != "your-wordpress-app-password":
        print("✅ CMS_APPLICATION_PASSWORD 已配置")
        success_count += 1
    else:
        print("⚠️  CMS_APPLICATION_PASSWORD 未配置")
        warnings.append("CMS_APPLICATION_PASSWORD 需要配置")

    # 9. 检查环境
    print("\n9️⃣ 环境信息...")
    print(f"   环境: {settings.ENVIRONMENT}")
    print(f"   日志级别: {settings.LOG_LEVEL}")
    print(f"   API 端口: {settings.API_PORT}")

    # 总结
    print("\n" + "=" * 70)
    print("\n📊 检查总结:\n")
    print(f"✅ 成功: {success_count} 项")
    print(f"⚠️  警告: {len(warnings)} 项")
    print(f"❌ 错误: {len(issues)} 项")

    if issues:
        print("\n❌ 发现严重问题:")
        for i, issue in enumerate(issues, 1):
            print(f"   {i}. {issue}")

    if warnings:
        print("\n⚠️  发现警告:")
        for i, warning in enumerate(warnings, 1):
            print(f"   {i}. {warning}")

    # 修复建议
    if issues or warnings:
        print("\n💡 修复建议:\n")

        if any("SECRET_KEY" in item for item in issues + warnings):
            print("   🔐 生成强 SECRET_KEY:")
            print("      openssl rand -hex 32\n")

        if any("Google Drive" in item for item in issues):
            print("   📁 配置 Google Drive:")
            print("      参考: GOOGLE_DRIVE_CONFIG_SUMMARY.md")
            print("      或运行: python3 scripts/verify_google_drive.py\n")

        if any("WordPress" in item for item in warnings):
            print("   📝 配置 WordPress:")
            print("      在 WordPress 后台生成应用密码")
            print("      更新 .env 中的 CMS_* 配置\n")

    if not issues:
        print("\n✅ 配置检查通过！")
        return True
    else:
        print("\n⚠️  请先修复严重问题。")
        return False


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
