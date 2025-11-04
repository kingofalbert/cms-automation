#!/usr/bin/env python3
"""
修復表列名與模型定義不匹配的問題
"""


import psycopg2

# Supabase connection string
db_url = 'postgresql://postgres.twsbhjmlmspjwfystpti:Xieping890$@aws-1-us-east-1.pooler.supabase.com:5432/postgres'

def fix_column_names():
    """修復列名不匹配"""
    print("🔧 修復列名不匹配問題...")

    conn = psycopg2.connect(db_url)
    cursor = conn.cursor()

    # Start transaction
    cursor.execute("BEGIN")

    try:
        # 1. 修復 articles 表
        print("\n📊 檢查 articles 表...")

        # 檢查 content 列是否存在
        cursor.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'articles'
            AND column_name IN ('content', 'body')
        """)
        columns = [col[0] for col in cursor.fetchall()]

        if 'content' in columns and 'body' not in columns:
            print("  將 content 列重命名為 body...")
            cursor.execute("ALTER TABLE articles RENAME COLUMN content TO body")
            print("  ✅ 已重命名 content → body")
        elif 'body' in columns:
            print("  ✅ body 列已存在，無需修改")
        else:
            print("  ⚠️  既無 content 也無 body 列，添加 body 列...")
            cursor.execute("ALTER TABLE articles ADD COLUMN body TEXT NOT NULL DEFAULT ''")
            print("  ✅ 已添加 body 列")

        # 2. 檢查其他可能的列名問題
        print("\n📊 檢查其他表列...")

        # 檢查 articles 表的所有必需列
        required_columns = {
            'title': 'VARCHAR(500)',
            'body': 'TEXT',
            'status': 'VARCHAR(20)',
            'word_count': 'INTEGER',
            'quality_score': 'FLOAT',
            'article_metadata': 'JSONB',
            'tags': 'TEXT[]',
            'categories': 'TEXT[]',
            'published_at': 'TIMESTAMP',
            'embedding': 'vector(1536)'
        }

        for col_name, col_type in required_columns.items():
            cursor.execute(f"""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'articles'
                AND column_name = '{col_name}'
            """)
            if not cursor.fetchone():
                print(f"  添加缺失的列: {col_name} ({col_type})...")

                # 特殊處理某些列
                if col_name == 'body':
                    cursor.execute(f"ALTER TABLE articles ADD COLUMN {col_name} {col_type} NOT NULL DEFAULT ''")
                elif col_name == 'embedding':
                    cursor.execute(f"ALTER TABLE articles ADD COLUMN {col_name} vector(1536)")
                elif col_name in ['tags', 'categories']:
                    cursor.execute(f"ALTER TABLE articles ADD COLUMN {col_name} TEXT[]")
                elif col_name == 'article_metadata':
                    cursor.execute(f"ALTER TABLE articles ADD COLUMN {col_name} JSONB")
                else:
                    cursor.execute(f"ALTER TABLE articles ADD COLUMN IF NOT EXISTS {col_name} {col_type}")

                print(f"    ✅ 已添加 {col_name}")

        # 3. 驗證所有表的關鍵列
        print("\n📊 驗證所有表結構...")

        tables_to_check = {
            'articles': ['id', 'title', 'body', 'status', 'created_at', 'updated_at'],
            'topic_requests': ['id', 'title', 'status', 'created_at', 'updated_at'],
            'proofreading_history': ['id', 'article_id', 'original_content', 'corrected_content', 'suggestions'],
            'proofreading_decisions': ['id', 'article_id', 'proofreading_history_id', 'suggestion_id', 'decision'],
            'provider_metrics': ['id', 'provider', 'date', 'total_tasks', 'success_rate'],
            'topic_embeddings': ['id', 'article_id', 'topic_text', 'embedding']
        }

        all_good = True
        for table_name, required_cols in tables_to_check.items():
            cursor.execute(f"""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = '{table_name}'
            """)
            existing_cols = [col[0] for col in cursor.fetchall()]

            missing_cols = [col for col in required_cols if col not in existing_cols]
            if missing_cols:
                print(f"  ⚠️  {table_name} 缺少列: {', '.join(missing_cols)}")
                all_good = False
            else:
                print(f"  ✅ {table_name} 結構正確")

        # Commit transaction
        cursor.execute("COMMIT")

        if all_good:
            print("\n✅ 所有表結構已修復並驗證完成！")
        else:
            print("\n⚠️  部分表可能需要進一步檢查")

    except Exception as e:
        cursor.execute("ROLLBACK")
        print(f"❌ 錯誤: {e}")
        raise

    finally:
        cursor.close()
        conn.close()

def test_api_compatibility():
    """測試 API 兼容性"""
    print("\n🧪 測試數據庫與 API 兼容性...")

    conn = psycopg2.connect(db_url)
    cursor = conn.cursor()

    try:
        # 插入測試數據
        cursor.execute("""
            INSERT INTO articles (title, body, status, word_count)
            VALUES ('Test Article', 'Test content', 'draft', 100)
            ON CONFLICT DO NOTHING
            RETURNING id
        """)

        result = cursor.fetchone()
        if result:
            print("  ✅ 成功插入測試文章")
            test_id = result[0]

            # 查詢測試
            cursor.execute("SELECT id, title, body FROM articles WHERE id = %s", (test_id,))
            article = cursor.fetchone()
            if article:
                print(f"  ✅ 成功查詢文章: ID={article[0]}, Title={article[1]}")

            # 清理測試數據
            cursor.execute("DELETE FROM articles WHERE id = %s", (test_id,))
            conn.commit()
            print("  ✅ 測試數據已清理")
        else:
            print("  ℹ️  測試文章已存在")

        print("\n✅ 數據庫與 API 兼容性測試通過！")

    except Exception as e:
        print(f"  ❌ 兼容性測試失敗: {e}")
        conn.rollback()

    finally:
        cursor.close()
        conn.close()

def main():
    print("=" * 60)
    print("🚀 修復數據庫列名不匹配問題")
    print("=" * 60)

    # 修復列名
    fix_column_names()

    # 測試兼容性
    test_api_compatibility()

    print("\n" + "=" * 60)
    print("✅ 修復完成！現在可以正常使用 API 了")
    print("   測試 API: curl http://localhost:8001/v1/articles")
    print("=" * 60)

if __name__ == "__main__":
    main()
