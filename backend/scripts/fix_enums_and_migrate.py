#!/usr/bin/env python3
"""
Fix enum types and run migrations for Supabase
"""

import subprocess
import sys
from pathlib import Path

import psycopg2

# Supabase connection string
db_url = 'postgresql://postgres.twsbhjmlmspjwfystpti:Xieping890$@aws-1-us-east-1.pooler.supabase.com:5432/postgres'

def setup_enums():
    """Create all required enum types"""
    print("📦 Setting up enum types...")

    conn = psycopg2.connect(db_url)
    cursor = conn.cursor()

    # Create all enum types with proper values
    enums = [
        ("provider_enum", "('playwright', 'computer_use', 'hybrid')"),
        ("task_status_enum", "('pending', 'in_progress', 'completed', 'failed', 'cancelled')"),
        ("decision_type", "('accept', 'reject', 'modify')"),
        ("feedback_status", "('pending', 'processed', 'rejected', 'error')"),
        ("tuning_job_type", "('supervised', 'reinforcement', 'preference')"),
        ("tuning_job_status", "('pending', 'running', 'completed', 'failed', 'cancelled')"),
    ]

    for enum_name, values in enums:
        try:
            cursor.execute(f"DROP TYPE IF EXISTS {enum_name} CASCADE")
            cursor.execute(f"CREATE TYPE {enum_name} AS ENUM {values}")
            print(f"  ✅ Created {enum_name}")
        except Exception as e:
            print(f"  ⚠️  Warning for {enum_name}: {e}")

    conn.commit()
    cursor.close()
    conn.close()
    print("✅ Enum types setup complete\n")

def reset_alembic():
    """Reset alembic version table"""
    print("🔄 Resetting alembic version...")

    conn = psycopg2.connect(db_url)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM alembic_version")
    conn.commit()

    cursor.close()
    conn.close()
    print("✅ Alembic version reset\n")

def run_migrations():
    """Run alembic migrations"""
    print("🚀 Running migrations...")

    # Change to backend directory
    backend_dir = Path(__file__).parent.parent

    result = subprocess.run(
        ["poetry", "run", "alembic", "upgrade", "head"],
        cwd=backend_dir,
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        print("✅ Migrations completed successfully")
        print(result.stdout)
    else:
        print("❌ Migration failed")
        print(result.stderr)
        return False

    return True

def verify_tables():
    """Verify tables were created"""
    print("\n📊 Verifying tables...")

    conn = psycopg2.connect(db_url)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name
    """)
    tables = cursor.fetchall()

    print("Created tables:")
    for table in tables:
        print(f"  - {table[0]}")

    # Check for key tables
    expected_tables = ['articles', 'proofreading_history', 'proofreading_decisions', 'feedback_tuning_jobs']
    table_names = [t[0] for t in tables]

    print("\n✅ Key tables check:")
    for expected in expected_tables:
        if expected in table_names:
            print(f"  ✅ {expected}")
        else:
            print(f"  ❌ {expected} (missing)")

    cursor.close()
    conn.close()

def main():
    print("=" * 60)
    print("🔧 Fixing Supabase Database Setup")
    print("=" * 60)

    # 1. Setup enums
    setup_enums()

    # 2. Reset alembic
    reset_alembic()

    # 3. Run migrations
    if run_migrations():
        # 4. Verify
        verify_tables()
        print("\n✅ Database setup complete!")
    else:
        print("\n❌ Database setup failed. Check error messages above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
