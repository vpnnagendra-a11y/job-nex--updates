# JobNex Product - Admin Management Routes
from fastapi import APIRouter, HTTPException, Depends, Query, status
from pydantic import BaseModel, Field
from typing import Optional, Literal

from database import (
    get_users, get_user_by_id, update_user_job_access,
    get_job_postings, get_job_posting_by_id, update_job_posting_status,
    get_access_requests, update_access_request_status, get_access_request_by_id,
    get_audit_logs
)
from auth import require_admin, log_admin_audit

router = APIRouter(prefix="/api/admin", tags=["Admin Control Panel"])


class JobStatusUpdate(BaseModel):
    status: Literal["approved", "rejected", "disabled", "pending"]


class AccessRequestReview(BaseModel):
    action: Literal["approve", "reject"]


@router.get("/users")
def list_users(
    role: Optional[str] = Query(None, description="Filter by role: admin, recruiter, user"),
    canPostJobs: Optional[bool] = Query(None, description="Filter by posting permission (true/false)"),
    search: Optional[str] = Query(None, description="Search by name or email"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    admin: dict = Depends(require_admin)
):
    """
    List all registered users with filtering, search, and pagination.
    Protected strictly for admin accounts.
    """
    return get_users(
        role=role,
        can_post_jobs=canPostJobs,
        search=search,
        page=page,
        limit=limit
    )


@router.patch("/users/{user_id}/grant-job-access")
def grant_job_access(user_id: int, admin: dict = Depends(require_admin)):
    """
    Explicitly grants job posting permissions to a target user.
    Records admin ID, timestamp, and creates an audit log entry.
    """
    target_user = get_user_by_id(user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found."
        )

    success = update_user_job_access(user_id=user_id, can_post_jobs=True, admin_id=admin["id"])
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user job posting access."
        )

    # Log audit event
    log_admin_audit(
        admin_id=admin["id"],
        action="GRANT_JOB_ACCESS",
        target_type="user",
        target_id=user_id,
        details=f"Admin '{admin['name']}' ({admin['email']}) granted job posting access to '{target_user['name']}' ({target_user['email']})"
    )

    updated = get_user_by_id(user_id)
    return {
        "message": f"Job posting access successfully granted to {target_user['name']}.",
        "user": updated
    }


@router.patch("/users/{user_id}/revoke-job-access")
def revoke_job_access(user_id: int, admin: dict = Depends(require_admin)):
    """
    Revokes job posting permissions from a target user.
    Records admin ID, timestamp, and creates an audit log entry.
    """
    target_user = get_user_by_id(user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found."
        )

    success = update_user_job_access(user_id=user_id, can_post_jobs=False, admin_id=admin["id"])
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke user job posting access."
        )

    # Log audit event
    log_admin_audit(
        admin_id=admin["id"],
        action="REVOKE_JOB_ACCESS",
        target_type="user",
        target_id=user_id,
        details=f"Admin '{admin['name']}' ({admin['email']}) revoked job posting access from '{target_user['name']}' ({target_user['email']})"
    )

    updated = get_user_by_id(user_id)
    return {
        "message": f"Job posting access successfully revoked from {target_user['name']}.",
        "user": updated
    }


@router.get("/job-postings")
def list_all_job_postings(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status: pending, approved, rejected, disabled"),
    owner_id: Optional[int] = Query(None, alias="owner", description="Filter by posting creator user ID"),
    search: Optional[str] = Query(None, description="Search by title, company, or skills"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    admin: dict = Depends(require_admin)
):
    """
    View all job postings across the entire platform with status and owner filters.
    """
    return get_job_postings(
        status=status_filter,
        created_by=owner_id,
        search=search,
        page=page,
        limit=limit
    )


@router.patch("/job-postings/{job_id}/status")
def change_job_posting_status(
    job_id: int,
    body: JobStatusUpdate,
    admin: dict = Depends(require_admin)
):
    """
    Allows admin to approve, reject, or disable any job posting.
    """
    job = get_job_posting_by_id(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job posting with ID {job_id} not found."
        )

    success = update_job_posting_status(job_id=job_id, status=body.status)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update job posting status."
        )

    log_admin_audit(
        admin_id=admin["id"],
        action="UPDATE_JOB_STATUS",
        target_type="job_posting",
        target_id=job_id,
        details=f"Admin '{admin['name']}' changed status of job #{job_id} ('{job['title']}') to '{body.status}'"
    )

    updated_job = get_job_posting_by_id(job_id)
    return {
        "message": f"Job posting status updated to '{body.status}'.",
        "job": updated_job
    }


@router.get("/access-requests")
def list_access_requests(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by pending, approved, rejected"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    admin: dict = Depends(require_admin)
):
    """
    View users who submitted requests for job posting permissions.
    """
    return get_access_requests(status=status_filter, page=page, limit=limit)


@router.patch("/access-requests/{request_id}/review")
def review_access_request(
    request_id: int,
    body: AccessRequestReview,
    admin: dict = Depends(require_admin)
):
    """
    Admin approves or rejects a job posting access request.
    If approved, target user's can_post_jobs permission is automatically set to True.
    """
    req = get_access_request_by_id(request_id)
    if not req:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Access request with ID {request_id} not found."
        )

    new_status = "approved" if body.action == "approve" else "rejected"
    update_access_request_status(request_id=request_id, status=new_status, reviewed_by=admin["id"])

    if new_status == "approved":
        update_user_job_access(user_id=req["user_id"], can_post_jobs=True, admin_id=admin["id"])
        log_admin_audit(
            admin_id=admin["id"],
            action="APPROVE_JOB_ACCESS_REQUEST",
            target_type="user",
            target_id=req["user_id"],
            details=f"Admin '{admin['name']}' approved access request #{request_id} for user #{req['user_id']}"
        )
    else:
        log_admin_audit(
            admin_id=admin["id"],
            action="REJECT_JOB_ACCESS_REQUEST",
            target_type="user",
            target_id=req["user_id"],
            details=f"Admin '{admin['name']}' rejected access request #{request_id} for user #{req['user_id']}"
        )

    return {
        "message": f"Access request #{request_id} has been {new_status}.",
        "request_id": request_id,
        "status": new_status
    }


@router.get("/audit-logs")
def list_audit_logs(
    target_type: Optional[str] = Query(None, description="Filter by user or job_posting"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    admin: dict = Depends(require_admin)
):
    """
    Retrieve admin action audit logs with timestamps and actor details.
    """
    return get_audit_logs(target_type=target_type, page=page, limit=limit)

