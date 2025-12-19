#!/usr/bin/env python3
"""
Create Supabase users for CMS Automation

Usage:
    python scripts/create_users.py

This script creates operator users with different roles.
"""

import os
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Load environment variables
from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / "backend" / ".env")

from supabase import create_client, Client

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    print("Error: Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY")
    print("Please check backend/.env file")
    sys.exit(1)

# Create admin client with service role key
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# Users to create
USERS_TO_CREATE = [
    {
        "email": "editor1@epochtimes.nyc",
        "password": "Editor123$",
        "display_name": "Editor One",
        "role": "editor"
    },
    {
        "email": "editor2@epochtimes.nyc",
        "password": "Editor123$",
        "display_name": "Editor Two",
        "role": "editor"
    },
    {
        "email": "viewer@epochtimes.nyc",
        "password": "Viewer123$",
        "display_name": "Viewer User",
        "role": "viewer"
    },
]


def create_user(email: str, password: str, display_name: str, role: str):
    """Create a user with Supabase Admin API."""
    print(f"\nCreating user: {email} ({role})")

    try:
        # Create user with admin API
        result = supabase.auth.admin.create_user({
            "email": email,
            "password": password,
            "email_confirm": True,  # Auto-confirm email
            "user_metadata": {
                "display_name": display_name,
                "role": role
            }
        })

        if result.user:
            print(f"  ✅ User created: {result.user.id}")
            print(f"     Email: {result.user.email}")
            print(f"     Role: {role}")
            return result.user
        else:
            print(f"  ❌ Failed to create user")
            return None

    except Exception as e:
        error_msg = str(e)
        if "already been registered" in error_msg or "already exists" in error_msg:
            print(f"  ⚠️  User already exists: {email}")
            return "exists"
        else:
            print(f"  ❌ Error: {e}")
            return None


def list_existing_users():
    """List existing users."""
    print("\n" + "=" * 60)
    print("Existing Users")
    print("=" * 60)

    try:
        # Get users from auth
        result = supabase.auth.admin.list_users()

        if result:
            for user in result:
                metadata = user.user_metadata or {}
                role = metadata.get("role", "unknown")
                display_name = metadata.get("display_name", "N/A")
                print(f"  - {user.email}")
                print(f"    ID: {user.id}")
                print(f"    Display Name: {display_name}")
                print(f"    Role: {role}")
                print()
        else:
            print("  No users found")

    except Exception as e:
        print(f"  Error listing users: {e}")


def main():
    print("=" * 60)
    print("CMS Automation - User Creation Script")
    print("=" * 60)
    print(f"Supabase URL: {SUPABASE_URL}")

    # List existing users first
    list_existing_users()

    # Create new users
    print("\n" + "=" * 60)
    print("Creating New Users")
    print("=" * 60)

    created = 0
    existed = 0
    failed = 0

    for user_data in USERS_TO_CREATE:
        result = create_user(
            email=user_data["email"],
            password=user_data["password"],
            display_name=user_data["display_name"],
            role=user_data["role"]
        )

        if result == "exists":
            existed += 1
        elif result:
            created += 1
        else:
            failed += 1

    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"  Created: {created}")
    print(f"  Already existed: {existed}")
    print(f"  Failed: {failed}")

    # List all users again
    list_existing_users()

    # Print credentials for reference
    print("\n" + "=" * 60)
    print("User Credentials (for testing)")
    print("=" * 60)
    print("\nAdmin:")
    print("  Email: albert.king@epochtimes.nyc")
    print("  Password: Tongxin123$")
    print("\nEditors:")
    for user in USERS_TO_CREATE:
        if user["role"] == "editor":
            print(f"  Email: {user['email']}")
            print(f"  Password: {user['password']}")
            print()
    print("Viewer:")
    for user in USERS_TO_CREATE:
        if user["role"] == "viewer":
            print(f"  Email: {user['email']}")
            print(f"  Password: {user['password']}")


if __name__ == "__main__":
    main()
