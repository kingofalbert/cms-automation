#!/usr/bin/env python3
"""修復缺失的 ENUM 類型"""

import os

import psycopg2
from dotenv import load_dotenv

# 加載環境變量
load_dotenv()

# 數據庫連接
db_url = os.getenv('DATABASE_URL', '').replace('postgresql+asyncpg://', 'postgresql://')

def fix_enums():
    """創建缺失的 ENUM 類型"""
    print("🔧 修復缺失的 ENUM 類型...")

    conn = psycopg2.connect(db_url)
    cursor = conn.cursor()

    try:
        # 創建 articlestatus 枚舉
        cursor.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'articlestatus') THEN
                    CREATE TYPE articlestatus AS ENUM (
                        'imported',
                        'draft',
                        'in-review',
                        'seo_optimized',
                        'ready_to_publish',
                        'publishing',
                        'scheduled',
                        'published',
                        'failed'
                    );
                    RAISE NOTICE 'Created articlestatus enum';
                END IF;
            END $$;
        """)

        # 如果 articles 表的 status 列還是 VARCHAR，轉換為 enum
        cursor.execute("""
            SELECT data_type
            FROM information_schema.columns
            WHERE table_name = 'articles' AND column_name = 'status'
        """)

        result = cursor.fetchone()
        if result and result[0] == 'character varying':
            print("  轉換 articles.status 為 enum 類型...")

            # 首先創建臨時列
            cursor.execute("""
                ALTER TABLE articles ADD COLUMN status_new articlestatus;
                UPDATE articles SET status_new = status::articlestatus;
                ALTER TABLE articles DROP COLUMN status;
                ALTER TABLE articles RENAME COLUMN status_new TO status;
            """)
            print("  ✅ 已轉換 status 列為 enum 類型")

        conn.commit()
        print("✅ ENUM 類型修復完成")

    except Exception as e:
        print(f"❌ 錯誤: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    fix_enums()
