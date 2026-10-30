# JobNex Product - Authentication & User Routes
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr, Field
from typing import Optional

from database import (
    create_user, get_user_by_email, get_user_by_id,
    create_access_request, get_access_requests
)
from auth import (
    hash_password, verify_password, create_access_token,
    get_current_user
)

router = APIRouter(prefix="/api", tags=["Authentication & User"])


class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=6, max_length=100)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AccessRequestBody(BaseModel):
    reason: Optional[str] = "Requesting permission to create job postings on JobNex."


@router.post("/auth/register", status_code=status.HTTP_201_CREATED)
def register(request: RegisterRequest):
    email = request.email.lower().strip()
    existing_user = get_user_by_email(email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists."
        )

    # Public registration is strictly restricted to the 'user' role with can_post_jobs=False
    pwd_hash = hash_password(request.password)
    user_id = create_user(
        name=request.name.strip(),
        email=email,
        password_hash=pwd_hash,
        role="user",
        can_post_jobs=False
    )

    token = create_access_token({"sub": user_id, "email": email, "role": "user"})
    return {
        "message": "User registered successfully.",
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user_id,
            "name": request.name.strip(),
            "email": email,
            "role": "user",
            "canPostJobs": False
        }
    }


@router.post("/auth/login")
def login(request: LoginRequest):
    email = request.email.lower().strip()
    user = get_user_by_email(email)
    if not user or not verify_password(request.password, user.get("password_hash", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    token = create_access_token({
        "sub": user["id"],
        "email": user["email"],
        "role": user["role"]
    })

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "role": user["role"],
            "canPostJobs": bool(user.get("can_post_jobs")),
            "jobAccessGrantedBy": user.get("job_access_granted_by"),
            "jobAccessGrantedAt": str(user.get("job_access_granted_at")) if user.get("job_access_granted_at") else None
        }
    }


@router.get("/auth/me")
def get_current_user_profile(current_user: dict = Depends(get_current_user)):
    return {
        "id": current_user["id"],
        "name": current_user["name"],
        "email": current_user["email"],
        "role": current_user["role"],
        "canPostJobs": bool(current_user.get("can_post_jobs")),
        "jobAccessGrantedBy": current_user.get("job_access_granted_by"),
        "jobAccessGrantedAt": str(current_user.get("job_access_granted_at")) if current_user.get("job_access_granted_at") else None,
        "grantedByName": current_user.get("granted_by_name"),
        "createdAt": str(current_user.get("created_at")) if current_user.get("created_at") else None
    }


@router.post("/job-access-requests", status_code=status.HTTP_201_CREATED)
def request_job_access(body: AccessRequestBody, current_user: dict = Depends(get_current_user)):
    if current_user.get("can_post_jobs") or current_user.get("role") == "admin":
        return {
            "message": "You already have permission to post jobs.",
            "status": "already_approved"
        }

    request_id = create_access_request(
        user_id=current_user["id"],
        reason=body.reason or ""
    )

    return {
        "message": "Job posting access request submitted successfully. Awaiting administrator review.",
        "request_id": request_id,
        "status": "pending"
    }

