#!/usr/bin/env python3
"""
Supabase 數據庫設置腳本
用於配置和初始化 Supabase PostgreSQL 數據庫
"""

import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv
import psycopg2
from psycopg2 import sql
import subprocess

# 添加項目根目錄到 Python 路徑
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_connection(connection_string: str) -> bool:
    """測試數據庫連接"""
    try:
        # 從 asyncpg 格式轉換為 psycopg2 格式
        if connection_string.startswith("postgresql+asyncpg://"):
            connection_string = connection_string.replace("postgresql+asyncpg://", "postgresql://")

        print(f"🔍 測試連接...")
        conn = psycopg2.connect(connection_string)
        cursor = conn.cursor()

        # 測試基本查詢
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"✅ 成功連接到 PostgreSQL")
        print(f"   版本: {version[0]}")

        # 檢查數據庫信息
        cursor.execute("SELECT current_database(), current_user;")
        db_info = cursor.fetchone()
        print(f"   數據庫: {db_info[0]}")
        print(f"   用戶: {db_info[1]}")

        cursor.close()
        conn.close()
        return True

    except Exception as e:
        print(f"❌ 連接失敗: {str(e)}")
        return False


def check_extensions(connection_string: str):
    """檢查並安裝必要的擴展"""
    try:
        if connection_string.startswith("postgresql+asyncpg://"):
            connection_string = connection_string.replace("postgresql+asyncpg://", "postgresql://")

        conn = psycopg2.connect(connection_string)
        cursor = conn.cursor()

        print("\n📦 檢查數據庫擴展...")

        # 檢查已安裝的擴展
        cursor.execute("""
            SELECT extname, extversion
            FROM pg_extension
            ORDER BY extname;
        """)
        extensions = cursor.fetchall()

        print("   已安裝的擴展:")
        for ext in extensions:
            print(f"   - {ext[0]} (v{ext[1]})")

        # 檢查 pgvector 是否可用
        cursor.execute("""
            SELECT * FROM pg_available_extensions
            WHERE name = 'vector';
        """)
        vector_available = cursor.fetchone()

        if vector_available:
            print("\n   ✅ pgvector 擴展可用")

            # 嘗試創建 vector 擴展
            try:
                cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                conn.commit()
                print("   ✅ pgvector 擴展已啟用")
            except psycopg2.errors.InsufficientPrivilege:
                print("   ⚠️  需要超級用戶權限來創建 pgvector 擴展")
                print("   請在 Supabase Dashboard 的 SQL Editor 中運行：")
                print("   CREATE EXTENSION IF NOT EXISTS vector;")
        else:
            print("\n   ⚠️  pgvector 擴展不可用")
            print("   Supabase 通常預裝了 pgvector，請檢查您的項目設置")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"❌ 檢查擴展失敗: {str(e)}")


def run_migrations(env_file: str):
    """運行 Alembic 遷移"""
    print("\n🔄 準備運行數據庫遷移...")

    # 設置環境變量
    load_dotenv(env_file, override=True)

    try:
        # 檢查當前遷移狀態
        print("   檢查當前遷移狀態...")
        result = subprocess.run(
            ["poetry", "run", "alembic", "current"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        print(f"   當前狀態: {result.stdout.strip()}")

        # 運行遷移
        print("\n   運行遷移到最新版本...")
        result = subprocess.run(
            ["poetry", "run", "alembic", "upgrade", "head"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )

        if result.returncode == 0:
            print("   ✅ 遷移成功完成")
            print(result.stdout)
        else:
            print("   ❌ 遷移失敗")
            print(result.stderr)
            return False

        return True

    except Exception as e:
        print(f"❌ 運行遷移失敗: {str(e)}")
        return False


def verify_tables(connection_string: str):
    """驗證表是否創建成功"""
    try:
        if connection_string.startswith("postgresql+asyncpg://"):
            connection_string = connection_string.replace("postgresql+asyncpg://", "postgresql://")

        conn = psycopg2.connect(connection_string)
        cursor = conn.cursor()

        print("\n📊 驗證數據庫表...")

        # 檢查所有表
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        tables = cursor.fetchall()

        print("   已創建的表:")
        for table in tables:
            print(f"   - {table[0]}")

        # 特別檢查校對相關的表
        proofreading_tables = ['proofreading_history', 'proofreading_decisions', 'feedback_tuning_jobs']
        found_tables = [t[0] for t in tables]

        print("\n   檢查 T7.1 校對表:")
        for table_name in proofreading_tables:
            if table_name in found_tables:
                # 獲取表的列數
                cursor.execute(f"""
                    SELECT COUNT(*)
                    FROM information_schema.columns
                    WHERE table_name = '{table_name}';
                """)
                col_count = cursor.fetchone()[0]
                print(f"   ✅ {table_name} ({col_count} 列)")
            else:
                print(f"   ❌ {table_name} (未找到)")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"❌ 驗證表失敗: {str(e)}")


def main():
    """主函數"""
    print("=" * 60)
    print("🚀 Supabase 數據庫設置工具")
    print("=" * 60)

    # 檢查環境文件
    env_files = [
        Path(__file__).parent.parent.parent / ".env",
        Path(__file__).parent.parent.parent / ".env.supabase.local",
        Path(__file__).parent.parent.parent / ".env.supabase"
    ]

    env_file = None
    for file in env_files:
        if file.exists():
            env_file = file
            print(f"\n📄 使用配置文件: {env_file}")
            break

    if not env_file:
        print("\n❌ 找不到配置文件")
        print("   請先配置 .env.supabase 文件")
        print("   參考 /Users/albertking/ES/cms_automation/.env.supabase")
        return

    # 加載環境變量
    load_dotenv(env_file, override=True)

    # 獲取數據庫連接字符串
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("\n❌ 找不到 DATABASE_URL 環境變量")
        print("   請在 .env.supabase 文件中配置")
        return

    # 檢查是否包含占位符
    if "[PROJECT-REF]" in db_url or "[YOUR-PASSWORD]" in db_url:
        print("\n❌ 請替換 DATABASE_URL 中的占位符:")
        print("   - [PROJECT-REF]: 您的 Supabase 項目 ID")
        print("   - [YOUR-PASSWORD]: 數據庫密碼")
        print("   - [REGION]: 項目區域")
        print("\n   在 Supabase Dashboard -> Settings -> Database 中找到這些信息")
        return

    # 1. 測試連接
    if not test_connection(db_url):
        return

    # 2. 檢查擴展
    check_extensions(db_url)

    # 3. 詢問是否運行遷移
    print("\n" + "=" * 60)
    response = input("是否運行數據庫遷移？(y/n): ")
    if response.lower() == 'y':
        if run_migrations(env_file):
            # 4. 驗證表
            verify_tables(db_url)
            print("\n✅ Supabase 數據庫設置完成！")
        else:
            print("\n⚠️  遷移過程中出現問題，請檢查錯誤信息")
    else:
        print("\n跳過遷移")

    print("\n" + "=" * 60)
    print("下一步:")
    print("1. 如果遷移成功，可以啟動後端服務器:")
    print("   cd backend && poetry run uvicorn src.main:app --reload")
    print("2. 如果需要手動創建 pgvector 擴展，請在 Supabase SQL Editor 中運行:")
    print("   CREATE EXTENSION IF NOT EXISTS vector;")
    print("=" * 60)


if __name__ == "__main__":
    main()