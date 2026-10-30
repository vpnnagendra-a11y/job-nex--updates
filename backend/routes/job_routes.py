# JobNex Product - Job Posting Routes
from fastapi import APIRouter, HTTPException, Depends, Query, status
from pydantic import BaseModel, Field
from typing import Optional, List, Union

from database import (
    create_job_posting, get_job_postings, get_job_posting_by_id
)
from auth import require_job_posting_permission

router = APIRouter(prefix="/api/jobs", tags=["Job Postings"])


class CreateJobRequest(BaseModel):
    title: str = Field(min_length=3, max_length=255)
    company: str = Field(min_length=2, max_length=255)
    description: str = Field(min_length=20)
    required_skills: Optional[Union[List[str], str]] = None
    location: Optional[str] = "Remote"


@router.post("", status_code=status.HTTP_201_CREATED)
def create_job(request: CreateJobRequest, current_user: dict = Depends(require_job_posting_permission)):
    """
    Create a new job posting.
    Protected by manual admin access control:
    Returns 403 Forbidden with a clear message if canPostJobs is false.
    """
    # Enforce permission check (also verified by require_job_posting_permission dependency)
    if not (current_user.get("can_post_jobs") or current_user.get("role") == "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Job posting access denied: You have not been granted permission by an administrator to post jobs."
        )

    skills_val = request.required_skills
    if isinstance(skills_val, list):
        skills_str = ", ".join(skills_val)
    else:
        skills_str = skills_val or ""

    job_id = create_job_posting(
        title=request.title.strip(),
        company=request.company.strip(),
        description=request.description.strip(),
        required_skills=skills_str,
        location=request.location or "Remote",
        created_by=current_user["id"],
        status="approved"  # Approved creators post directly
    )

    created_job = get_job_posting_by_id(job_id)
    return {
        "message": "Job posting created successfully.",
        "job": created_job
    }


@router.get("")
def list_jobs(
    search: Optional[str] = Query(None, description="Search by title, company, or skills"),
    q: Optional[str] = Query(None, description="Alias for search query"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    """
    Retrieve active approved job postings.
    Returns both 'jobs' and 'items' for client compatibility.
    """
    search_val = q or search
    result = get_job_postings(
        status="approved",
        search=search_val,
        page=page,
        limit=limit
    )
    result["items"] = result.get("jobs", [])
    return result


@router.get("/{job_id}")
def get_job(job_id: int):
    """
    Retrieve a single job posting by ID.
    """
    job = get_job_posting_by_id(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job posting with ID {job_id} not found."
        )
    return job

