#!/usr/bin/env python3
"""
創建缺失的表並修正表名以完全滿足系統需求
"""

import psycopg2
from datetime import datetime

# Supabase connection string
db_url = 'postgresql://postgres.twsbhjmlmspjwfystpti:Xieping890$@aws-1-us-east-1.pooler.supabase.com:5432/postgres'

def create_missing_tables():
    """創建缺失的表"""
    print("📊 創建缺失的表以完善數據庫...")

    conn = psycopg2.connect(db_url)
    cursor = conn.cursor()

    # Start transaction
    cursor.execute("BEGIN")

    try:
        # 1. 創建 provider_metrics 表
        print("  創建 provider_metrics 表...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS provider_metrics (
                id SERIAL PRIMARY KEY,
                provider provider_enum NOT NULL,
                date DATE NOT NULL,
                total_tasks INTEGER DEFAULT 0 NOT NULL,
                successful_tasks INTEGER DEFAULT 0 NOT NULL,
                failed_tasks INTEGER DEFAULT 0 NOT NULL,
                success_rate FLOAT DEFAULT 0.0 NOT NULL,
                avg_duration_seconds FLOAT,
                avg_cost_usd FLOAT,
                total_cost_usd FLOAT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                UNIQUE(provider, date)
            )
        """)

        # 添加索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_provider_metrics_provider ON provider_metrics(provider)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_provider_metrics_date ON provider_metrics(date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_provider_metrics_provider_date ON provider_metrics(provider, date)")

        print("    ✅ provider_metrics 表創建成功")

        # 2. 創建 topic_embeddings 表
        print("  創建 topic_embeddings 表...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS topic_embeddings (
                id SERIAL PRIMARY KEY,
                article_id INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
                topic_text TEXT NOT NULL,
                embedding vector(1536),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(article_id)
            )
        """)

        # 添加索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_topic_embeddings_article ON topic_embeddings(article_id)")

        # 如果 pgvector 支持，創建向量索引
        cursor.execute("""
            DO $$
            BEGIN
                -- 嘗試創建 HNSW 索引（pgvector 0.5+）
                IF EXISTS (SELECT 1 FROM pg_proc WHERE proname = 'hnsw_build') THEN
                    CREATE INDEX IF NOT EXISTS idx_topic_embeddings_vector_hnsw
                    ON topic_embeddings USING hnsw (embedding vector_cosine_ops);
                -- 否則創建 IVFFlat 索引（pgvector 0.4+）
                ELSE
                    CREATE INDEX IF NOT EXISTS idx_topic_embeddings_vector_ivfflat
                    ON topic_embeddings USING ivfflat (embedding vector_cosine_ops)
                    WITH (lists = 100);
                END IF;
            EXCEPTION
                WHEN OTHERS THEN
                    -- 如果索引創建失敗，不影響表創建
                    NULL;
            END;
            $$ LANGUAGE plpgsql;
        """)

        print("    ✅ topic_embeddings 表創建成功")

        # 3. 重命名 settings 表為 app_settings
        print("  檢查並重命名 settings 表...")

        # 檢查 settings 表是否存在
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_name = 'settings'
            )
        """)
        settings_exists = cursor.fetchone()[0]

        # 檢查 app_settings 表是否已存在
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_name = 'app_settings'
            )
        """)
        app_settings_exists = cursor.fetchone()[0]

        if settings_exists and not app_settings_exists:
            cursor.execute("ALTER TABLE settings RENAME TO app_settings")
            print("    ✅ settings 表已重命名為 app_settings")
        elif not settings_exists and not app_settings_exists:
            # 如果兩個表都不存在，創建 app_settings
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS app_settings (
                    id SERIAL PRIMARY KEY,
                    key VARCHAR(100) NOT NULL UNIQUE,
                    value JSONB NOT NULL,
                    description TEXT,
                    category VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("    ✅ app_settings 表創建成功")
        else:
            print("    ℹ️  app_settings 表已存在，無需修改")

        # Commit transaction
        cursor.execute("COMMIT")
        print("\n✅ 所有缺失的表已成功創建！")

    except Exception as e:
        cursor.execute("ROLLBACK")
        print(f"❌ 錯誤: {e}")
        raise

    finally:
        cursor.close()
        conn.close()

def verify_all_tables():
    """驗證所有表是否存在"""
    print("\n📊 驗證數據庫完整性...")

    conn = psycopg2.connect(db_url)
    cursor = conn.cursor()

    # 所有需要的表
    required_tables = [
        'app_settings',
        'articles',
        'execution_logs',
        'feedback_tuning_jobs',
        'proofreading_decisions',
        'proofreading_history',
        'provider_metrics',
        'publish_tasks',
        'seo_metadata',
        'topic_embeddings',
        'topic_requests',
        'uploaded_files',
        'worklist_items'
    ]

    # 檢查每個表
    cursor.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_name NOT LIKE 'pg_%'
        AND table_name != 'alembic_version'
        ORDER BY table_name
    """)
    existing_tables = [t[0] for t in cursor.fetchall()]

    print("\n✅ 系統所需的所有表:")
    all_exist = True
    for table in required_tables:
        if table in existing_tables:
            # 獲取行數
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  ✓ {table} ({count} rows)")
        else:
            print(f"  ✗ {table} (缺失)")
            all_exist = False

    # 檢查額外的表
    extra_tables = [t for t in existing_tables if t not in required_tables]
    if extra_tables:
        print("\n📌 額外的表 (非必需):")
        for table in extra_tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  - {table} ({count} rows)")

    if all_exist:
        print("\n✅ 數據庫已完全滿足所有功能需求！")
        print("🚀 系統可以正常運行所有功能：")
        print("  - 文章生成與管理")
        print("  - SEO 優化")
        print("  - 多提供者發布")
        print("  - 校對與反饋學習")
        print("  - 語義相似度檢測")
        print("  - 性能指標追蹤")
        print("  - 工作流管理")
        print("  - 文件上傳追蹤")
    else:
        print("\n⚠️  仍有缺失的表，請檢查錯誤信息")

    cursor.close()
    conn.close()

    return all_exist

def main():
    print("=" * 60)
    print("🚀 完善 CMS 自動化數據庫")
    print("=" * 60)

    # 創建缺失的表
    create_missing_tables()

    # 驗證
    success = verify_all_tables()

    if success:
        print("\n" + "=" * 60)
        print("🎉 恭喜！Supabase 數據庫現在完全滿足所有功能需求！")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("⚠️  請檢查錯誤並重新運行腳本")
        print("=" * 60)

if __name__ == "__main__":
    main()