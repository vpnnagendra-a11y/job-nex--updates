# JobNex - Feature Verification Test Suite
import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from auth import (
    hash_password, verify_password,
    create_access_token, decode_access_token,
    require_job_posting_permission
)
from analyzer import analyze_resume
from fastapi import HTTPException


def test_password_hashing():
    print("[Test 1] Testing password hashing & verification...")
    password = "SuperSecretPassword123!"
    hashed = hash_password(password)
    assert hashed != password, "Hashed password must not equal plain password"
    assert verify_password(password, hashed), "Password verification failed for correct password"
    assert not verify_password("WrongPassword!", hashed), "Password verification succeeded for wrong password"
    print(" -> PASS: Password hashing & verification working properly.")


def test_token_lifecycle():
    print("[Test 2] Testing JWT token generation and decoding...")
    payload = {"sub": 42, "email": "test@jobnex.com", "role": "admin"}
    token = create_access_token(payload)
    assert isinstance(token, str) and len(token) > 20, "Invalid token format"

    decoded = decode_access_token(token)
    assert decoded.get("sub") == 42 or decoded.get("user_id") == 42
    assert decoded.get("email") == "test@jobnex.com"
    assert decoded.get("role") == "admin"
    print(" -> PASS: Token encoding and decoding working properly.")


def test_job_posting_access_control():
    print("[Test 3] Testing job posting permission enforcement...")
    # 1. Unapproved user -> must raise HTTPException with 403
    unapproved_user = {
        "id": 1,
        "name": "Jane User",
        "email": "jane@example.com",
        "role": "user",
        "can_post_jobs": False
    }

    denied = False
    try:
        require_job_posting_permission(unapproved_user)
    except HTTPException as e:
        if e.status_code == 403:
            denied = True
    assert denied, "Unapproved user was not denied with 403 status code"

    # 2. Approved user -> must succeed
    approved_user = {
        "id": 2,
        "name": "John Recruiter",
        "email": "john@example.com",
        "role": "user",
        "can_post_jobs": True
    }
    user_passed = require_job_posting_permission(approved_user)
    assert user_passed["id"] == 2, "Approved user failed permission check"

    # 3. Admin user -> must always succeed
    admin_user = {
        "id": 3,
        "name": "Admin",
        "email": "admin@jobnex.com",
        "role": "admin",
        "can_post_jobs": False
    }
    admin_passed = require_job_posting_permission(admin_user)
    assert admin_passed["id"] == 3, "Admin failed permission check"

    print(" -> PASS: 403 Forbidden properly enforced for unapproved users.")


def test_candidate_matching_engine():
    print("[Test 4] Testing candidate matching engine for recruiter...")
    sample_resume = "Experienced software engineer with deep Python, FastAPI, Docker, and SQL experience."
    sample_job = "Looking for a Python Developer proficient in Python, Docker, FastAPI, and React."

    result = analyze_resume(sample_resume, sample_job)
    assert "matched_score" in result
    assert "matched_skills" in result
    assert "missing_skills" in result
    assert "python" in result["matched_skills"]
    assert "docker" in result["matched_skills"]
    assert "fastapi" in result["matched_skills"]
    assert "react" in result["missing_skills"]
    print(f" -> PASS: Candidate matched with score: {result['matched_score']}%. Skills matched: {result['matched_skills']}.")


if __name__ == "__main__":
    print("=" * 60)
    print("Running JobNex Admin & Recruiter Feature Tests")
    print("=" * 60)
    test_password_hashing()
    test_token_lifecycle()
    test_job_posting_access_control()
    test_candidate_matching_engine()
    print("=" * 60)
    print("ALL TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)

