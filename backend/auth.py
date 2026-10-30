# JobNex Product - Authentication & RBAC Module
import os
import time
import json
import base64
import hmac
import hashlib
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import Depends, HTTPException, status, Header
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET", os.getenv("SECRET_KEY", "jobnex_production_super_secret_jwt_key_2026"))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60 * 24))  # 24 hours

# ---------------------------------------------------------------------------
# Password Hashing with multi-engine fallback
# ---------------------------------------------------------------------------

try:
    import bcrypt

    def hash_password(password: str) -> str:
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    def verify_password(plain_password: str, hashed_password: str) -> bool:
        try:
            return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
        except Exception:
            return False

except ImportError:
    try:
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

        def hash_password(password: str) -> str:
            return pwd_context.hash(password)

        def verify_password(plain_password: str, hashed_password: str) -> bool:
            return pwd_context.verify(plain_password, hashed_password)

    except ImportError:
        # Standard library PBKDF2-HMAC fallback
        def hash_password(password: str) -> str:
            salt = os.urandom(16)
            key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
            return f"pbkdf2${salt.hex()}${key.hex()}"

        def verify_password(plain_password: str, hashed_password: str) -> bool:
            try:
                parts = hashed_password.split("$")
                if len(parts) == 3 and parts[0] == "pbkdf2":
                    salt = bytes.fromhex(parts[1])
                    expected_key = parts[2]
                    key = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, 100000)
                    return hmac.compare_digest(key.hex(), expected_key)
            except Exception:
                return False
            return False


# ---------------------------------------------------------------------------
# JWT Encoding & Decoding
# ---------------------------------------------------------------------------

try:
    import jwt

    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    def decode_access_token(token: str) -> dict:
        try:
            return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired. Please log in again."
            )
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token."
            )

except ImportError:
    # Standard library JWT-like HMAC-SHA256 signature token fallback
    def _b64_encode(data: bytes) -> str:
        return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")

    def _b64_decode(data: str) -> bytes:
        padding = 4 - (len(data) % 4)
        if padding != 4:
            data += "=" * padding
        return base64.urlsafe_b64decode(data.encode("utf-8"))

    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        to_encode = data.copy()
        expire_ts = time.time() + (expires_delta.total_seconds() if expires_delta else ACCESS_TOKEN_EXPIRE_MINUTES * 60)
        to_encode["exp"] = int(expire_ts)
        header = {"alg": "HS256", "typ": "JWT"}
        h_str = _b64_encode(json.dumps(header).encode("utf-8"))
        p_str = _b64_encode(json.dumps(to_encode).encode("utf-8"))
        signing_input = f"{h_str}.{p_str}"
        sig = hmac.new(SECRET_KEY.encode("utf-8"), signing_input.encode("utf-8"), hashlib.sha256).digest()
        sig_str = _b64_encode(sig)
        return f"{signing_input}.{sig_str}"

    def decode_access_token(token: str) -> dict:
        try:
            parts = token.split(".")
            if len(parts) != 3:
                raise ValueError("Malformed token")
            signing_input = f"{parts[0]}.{parts[1]}"
            expected_sig = hmac.new(SECRET_KEY.encode("utf-8"), signing_input.encode("utf-8"), hashlib.sha256).digest()
            actual_sig = _b64_decode(parts[2])
            if not hmac.compare_digest(expected_sig, actual_sig):
                raise ValueError("Signature verification failed")
            payload = json.loads(_b64_decode(parts[1]).decode("utf-8"))
            if payload.get("exp") and payload["exp"] < time.time():
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has expired. Please log in again."
                )
            return payload
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token."
            )


# ---------------------------------------------------------------------------
# FastAPI Auth & RBAC Dependencies
# ---------------------------------------------------------------------------

from database import get_user_by_id, create_audit_log


def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header. Please log in.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization format. Must be 'Bearer <token>'.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    token = parts[1]
    payload = decode_access_token(token)
    user_id = payload.get("sub") or payload.get("user_id")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload."
        )

    try:
        user_id = int(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID in token."
        )

    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User associated with this token no longer exists."
        )

    return user


def require_role(*allowed_roles: str):
    def role_checker(current_user: dict = Depends(get_current_user)) -> dict:
        user_role = current_user.get("role", "user")
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: role '{user_role}' does not have required permissions ({', '.join(allowed_roles)})."
            )
        return current_user
    return role_checker


# Convenient role shortcuts
require_admin = require_role("admin")
require_recruiter = require_role("recruiter", "admin")


def require_job_posting_permission(current_user: dict = Depends(get_current_user)) -> dict:
    """
    Enforces that only users explicitly approved with can_post_jobs=True (or admins)
    can create job postings.
    """
    if current_user.get("role") == "admin":
        return current_user

    can_post = bool(current_user.get("can_post_jobs") or current_user.get("canPostJobs"))
    if not can_post:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Job posting access denied. Only users approved by an administrator can create job postings."
        )

    return current_user


def log_admin_audit(admin_id: int, action: str, target_type: str, target_id: int, details: Optional[str] = None):
    try:
        create_audit_log(
            actor_id=admin_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            details=details
        )
    except Exception as err:
        print(f"[Warning] Failed to write audit log: {err}")

