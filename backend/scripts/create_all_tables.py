#!/usr/bin/env python3
"""
Create all CMS Automation tables directly in Supabase
"""

import psycopg2
from datetime import datetime

# Supabase connection string
db_url = 'postgresql://postgres.twsbhjmlmspjwfystpti:Xieping890$@aws-1-us-east-1.pooler.supabase.com:5432/postgres'

def create_tables():
    """Create all required tables"""
    print("📊 Creating tables...")

    conn = psycopg2.connect(db_url)
    cursor = conn.cursor()

    # Start transaction
    cursor.execute("BEGIN")

    try:
        # 1. Create enum types if not exist
        print("  Creating enum types...")
        cursor.execute("""
            DO $$
            BEGIN
                -- provider_enum
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'provider_enum') THEN
                    CREATE TYPE provider_enum AS ENUM ('playwright', 'computer_use', 'hybrid');
                END IF;

                -- task_status_enum
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'task_status_enum') THEN
                    CREATE TYPE task_status_enum AS ENUM ('pending', 'in_progress', 'completed', 'failed', 'cancelled');
                END IF;

                -- decision_type
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'decision_type') THEN
                    CREATE TYPE decision_type AS ENUM ('accept', 'reject', 'modify');
                END IF;

                -- feedback_status
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'feedback_status') THEN
                    CREATE TYPE feedback_status AS ENUM ('pending', 'processed', 'rejected', 'error');
                END IF;

                -- tuning_job_type
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'tuning_job_type') THEN
                    CREATE TYPE tuning_job_type AS ENUM ('supervised', 'reinforcement', 'preference');
                END IF;

                -- tuning_job_status
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'tuning_job_status') THEN
                    CREATE TYPE tuning_job_status AS ENUM ('pending', 'running', 'completed', 'failed', 'cancelled');
                END IF;
            END
            $$;
        """)

        # 2. Create core tables
        print("  Creating core tables...")

        # topic_requests table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS topic_requests (
                id SERIAL PRIMARY KEY,
                title VARCHAR(500) NOT NULL,
                keywords TEXT,
                target_audience VARCHAR(200),
                content_type VARCHAR(50),
                tone VARCHAR(50),
                status VARCHAR(20) DEFAULT 'pending',
                request_metadata JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # articles table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS articles (
                id SERIAL PRIMARY KEY,
                topic_request_id INTEGER REFERENCES topic_requests(id) ON DELETE SET NULL,
                title VARCHAR(500) NOT NULL,
                content TEXT NOT NULL,
                word_count INTEGER,
                status VARCHAR(20) DEFAULT 'draft',
                quality_score FLOAT,
                article_metadata JSONB,
                tags TEXT[],
                categories TEXT[],
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                published_at TIMESTAMP,
                embedding vector(1536)
            )
        """)

        # 3. Create proofreading tables (T7.1)
        print("  Creating T7.1 proofreading tables...")

        # proofreading_history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS proofreading_history (
                id SERIAL PRIMARY KEY,
                article_id INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
                original_content TEXT NOT NULL,
                corrected_content TEXT NOT NULL,
                suggestions JSONB NOT NULL,
                total_changes INTEGER DEFAULT 0,
                categories JSONB,
                provider VARCHAR(50),
                model_version VARCHAR(50),
                proofreading_metadata JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # proofreading_decisions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS proofreading_decisions (
                id SERIAL PRIMARY KEY,
                article_id INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
                proofreading_history_id INTEGER NOT NULL REFERENCES proofreading_history(id) ON DELETE CASCADE,
                suggestion_id VARCHAR(100) NOT NULL,
                decision decision_type NOT NULL,
                original_text TEXT,
                suggested_text TEXT,
                modified_text TEXT,
                rationale TEXT,
                category VARCHAR(50),
                user_id VARCHAR(100),
                decision_metadata JSONB,
                feedback_status feedback_status DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(article_id, suggestion_id)
            )
        """)

        # feedback_tuning_jobs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feedback_tuning_jobs (
                id SERIAL PRIMARY KEY,
                dataset_size INTEGER DEFAULT 0,
                positive_samples INTEGER DEFAULT 0,
                negative_samples INTEGER DEFAULT 0,
                job_type tuning_job_type NOT NULL,
                status tuning_job_status DEFAULT 'pending',
                model_version VARCHAR(50),
                training_config JSONB,
                performance_metrics JSONB,
                error_message TEXT,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 4. Create indexes
        print("  Creating indexes...")

        # Articles indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_articles_topic_request ON articles(topic_request_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_articles_status ON articles(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_articles_created ON articles(created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_articles_tags ON articles USING gin(tags)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_articles_categories ON articles USING gin(categories)")

        # Proofreading indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_proofreading_history_article ON proofreading_history(article_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_proofreading_history_created ON proofreading_history(created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_proofreading_decisions_article ON proofreading_decisions(article_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_proofreading_decisions_history ON proofreading_decisions(proofreading_history_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_proofreading_decisions_status ON proofreading_decisions(feedback_status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_proofreading_decisions_decision ON proofreading_decisions(decision)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_feedback_tuning_jobs_status ON feedback_tuning_jobs(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_feedback_tuning_jobs_type ON feedback_tuning_jobs(job_type)")

        # 5. Create other necessary tables
        print("  Creating additional tables...")

        # seo_metadata table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS seo_metadata (
                id SERIAL PRIMARY KEY,
                article_id INTEGER REFERENCES articles(id) ON DELETE CASCADE,
                meta_title VARCHAR(100),
                meta_description VARCHAR(200),
                canonical_url VARCHAR(500),
                keywords TEXT[],
                og_title VARCHAR(100),
                og_description VARCHAR(200),
                og_image VARCHAR(500),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # publish_tasks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS publish_tasks (
                id SERIAL PRIMARY KEY,
                article_id INTEGER REFERENCES articles(id) ON DELETE SET NULL,
                provider provider_enum DEFAULT 'playwright',
                target_url VARCHAR(500),
                username VARCHAR(100),
                password VARCHAR(100),
                status task_status_enum DEFAULT 'pending',
                retry_count INTEGER DEFAULT 0,
                max_retries INTEGER DEFAULT 3,
                error_message TEXT,
                screenshot_url VARCHAR(500),
                scheduled_at TIMESTAMP,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                execution_time_seconds FLOAT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # execution_logs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS execution_logs (
                id SERIAL PRIMARY KEY,
                task_id INTEGER REFERENCES publish_tasks(id) ON DELETE CASCADE,
                action VARCHAR(100) NOT NULL,
                status VARCHAR(20) NOT NULL,
                details JSONB,
                screenshot_url VARCHAR(500),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # settings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                id SERIAL PRIMARY KEY,
                key VARCHAR(100) NOT NULL UNIQUE,
                value JSONB NOT NULL,
                description TEXT,
                category VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # worklist_items table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS worklist_items (
                id SERIAL PRIMARY KEY,
                title VARCHAR(500) NOT NULL,
                description TEXT,
                priority INTEGER DEFAULT 5,
                status VARCHAR(20) DEFAULT 'pending',
                tags TEXT[],
                categories TEXT[],
                meta_description VARCHAR(200),
                seo_keywords TEXT[],
                assigned_to VARCHAR(100),
                due_date DATE,
                metadata JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # uploaded_files table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS uploaded_files (
                id SERIAL PRIMARY KEY,
                drive_file_id VARCHAR(255) NOT NULL UNIQUE,
                name VARCHAR(500) NOT NULL,
                mime_type VARCHAR(100),
                size_bytes BIGINT,
                file_path TEXT,
                parent_folder_id VARCHAR(255),
                web_view_link TEXT,
                web_content_link TEXT,
                created_time TIMESTAMP,
                modified_time TIMESTAMP,
                processed BOOLEAN DEFAULT FALSE,
                processed_at TIMESTAMP,
                metadata JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 6. Update alembic version
        print("  Updating alembic version...")
        cursor.execute("DELETE FROM alembic_version")
        cursor.execute("INSERT INTO alembic_version (version_num) VALUES ('20251031_1830')")

        # Commit transaction
        cursor.execute("COMMIT")
        print("✅ All tables created successfully!")

    except Exception as e:
        cursor.execute("ROLLBACK")
        print(f"❌ Error creating tables: {e}")
        raise

    finally:
        cursor.close()
        conn.close()

def verify_setup():
    """Verify the database setup"""
    print("\n📊 Verifying database setup...")

    conn = psycopg2.connect(db_url)
    cursor = conn.cursor()

    # Check tables
    cursor.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_name NOT LIKE 'pg_%'
        ORDER BY table_name
    """)
    tables = cursor.fetchall()

    print("\n✅ Created tables:")
    for table in tables:
        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
        count = cursor.fetchone()[0]
        print(f"  - {table[0]} ({count} rows)")

    # Check enum types
    cursor.execute("""
        SELECT typname
        FROM pg_type
        WHERE typcategory = 'E'
        AND typnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
        ORDER BY typname
    """)
    enums = cursor.fetchall()

    print("\n✅ Created enum types:")
    for enum in enums:
        print(f"  - {enum[0]}")

    cursor.close()
    conn.close()

def main():
    print("=" * 60)
    print("🚀 Creating CMS Automation Tables in Supabase")
    print("=" * 60)

    # Create tables
    create_tables()

    # Verify
    verify_setup()

    print("\n" + "=" * 60)
    print("✅ Database setup complete!")
    print("You can now start the backend server:")
    print("  cd backend && poetry run uvicorn src.main:app --reload")
    print("=" * 60)

if __name__ == "__main__":
    main()