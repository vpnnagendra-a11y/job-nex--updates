# JobNex Product - Admin & Role Seeding Script
import os
import sys
import argparse
from dotenv import load_dotenv

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

from database import init_db, get_user_by_email, create_user
from auth import hash_password


def seed_admin(name: str = None, email: str = None, password: str = None):
    print("=" * 60)
    print(" JobNex Admin Seeding Utility")
    print("=" * 60)

    # Initialize database tables if not existing
    init_db()

    admin_name = name or os.getenv("ADMIN_NAME", "System Administrator")
    admin_email = (email or os.getenv("ADMIN_EMAIL", "admin@jobnex.com")).lower().strip()
    admin_password = password or os.getenv("ADMIN_PASSWORD", "AdminPass123!")

    existing = get_user_by_email(admin_email)
    if existing:
        print(f"[Info] User with email '{admin_email}' already exists (Role: {existing.get('role')}).")
        return existing["id"]

    pwd_hash = hash_password(admin_password)
    user_id = create_user(
        name=admin_name,
        email=admin_email,
        password_hash=pwd_hash,
        role="admin",
        can_post_jobs=True,
        granted_by=None
    )

    print(f"[Success] Admin account created successfully!")
    print(f"  User ID:       {user_id}")
    print(f"  Name:          {admin_name}")
    print(f"  Email:         {admin_email}")
    print(f"  Role:          admin")
    print(f"  can_post_jobs: True")
    print("=" * 60)
    return user_id


def seed_recruiter(name: str = None, email: str = None, password: str = None):
    recruiter_name = name or os.getenv("RECRUITER_NAME", "Senior Recruiter")
    recruiter_email = (email or os.getenv("RECRUITER_EMAIL", "recruiter@jobnex.com")).lower().strip()
    recruiter_password = password or os.getenv("RECRUITER_PASSWORD", "RecruiterPass123!")

    existing = get_user_by_email(recruiter_email)
    if existing:
        print(f"[Info] User with email '{recruiter_email}' already exists (Role: {existing.get('role')}).")
        return existing["id"]

    pwd_hash = hash_password(recruiter_password)
    user_id = create_user(
        name=recruiter_name,
        email=recruiter_email,
        password_hash=pwd_hash,
        role="recruiter",
        can_post_jobs=True,
        granted_by=None
    )

    print(f"[Success] Recruiter account created successfully!")
    print(f"  User ID:       {user_id}")
    print(f"  Name:          {recruiter_name}")
    print(f"  Email:         {recruiter_email}")
    print(f"  Role:          recruiter")
    print(f"  can_post_jobs: True")
    print("=" * 60)
    return user_id


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed JobNex Admin & Recruiter accounts")
    parser.add_argument("--name", type=str, help="Admin display name")
    parser.add_argument("--email", type=str, help="Admin email address")
    parser.add_argument("--password", type=str, help="Admin password")
    parser.add_argument("--create-recruiter", action="store_true", help="Also create a sample recruiter account")

    args = parser.parse_args()
    seed_admin(name=args.name, email=args.email, password=args.password)

    if args.create_recruiter:
        seed_recruiter()

