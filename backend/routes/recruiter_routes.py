# JobNex Product - Recruiter Module
from fastapi import APIRouter, HTTPException, Depends, Query, status
from typing import Optional, List
import json

from database import (
    get_job_postings, get_job_posting_by_id, get_all_resumes
)
from auth import require_recruiter
from analyzer import analyze_resume

router = APIRouter(prefix="/api/recruiter", tags=["Recruiter Portal"])


@router.get("/job-postings")
def recruiter_search_jobs(
    search: Optional[str] = Query(None, description="Search by title, required skills, company, or keywords"),
    status_filter: Optional[str] = Query("approved", alias="status", description="Filter by job status"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    recruiter: dict = Depends(require_recruiter)
):
    """
    Search and browse relevant job postings.
    Protected strictly for recruiters (and administrators).
    """
    return get_job_postings(
        status=status_filter,
        search=search,
        page=page,
        limit=limit
    )


@router.get("/candidates")
def list_candidates(
    limit: int = Query(50, ge=1, le=200),
    recruiter: dict = Depends(require_recruiter)
):
    """
    List all candidate resumes in the talent pool.
    """
    candidates = get_all_resumes(limit=limit)
    return {
        "total": len(candidates),
        "candidates": candidates
    }


@router.get("/candidates/match/{job_id}")
def match_candidates_for_job(
    job_id: int,
    min_score: float = Query(0.0, ge=0.0, le=100.0, description="Minimum match percentage"),
    limit: int = Query(20, ge=1, le=100),
    recruiter: dict = Depends(require_recruiter)
):
    """
    Match and rank candidates for a specific job posting.
    Uses the JobNex analysis algorithm to compare candidates' resumes
    against the target job description and required skills.
    """
    job = get_job_posting_by_id(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job posting with ID {job_id} not found."
        )

    # Job description and skills combined
    job_text = f"{job['title']}\n{job['company']}\n{job.get('required_skills', '')}\n{job['description']}"

    # Fetch candidates from the database
    candidates = get_all_resumes(limit=100)
    matched_results = []

    for candidate in candidates:
        resume_text = candidate.get("raw_text") or ""
        if not resume_text:
            # Construct from structured fields if raw_text is empty
            parts = [
                candidate.get("name", ""),
                candidate.get("skills", ""),
                candidate.get("experience", ""),
                candidate.get("education", ""),
                candidate.get("summary", "")
            ]
            resume_text = "\n".join([p for p in parts if p])

        if not resume_text.strip():
            continue

        # Run resume matching engine
        analysis = analyze_resume(resume_text, job_text)
        score = analysis.get("matched_score", 0.0)

        if score >= min_score:
            matched_results.append({
                "candidate_id": candidate["id"],
                "candidate_name": candidate.get("name") or "Unnamed Candidate",
                "candidate_email": candidate.get("email"),
                "candidate_phone": candidate.get("phone"),
                "matched_score": score,
                "matched_skills": analysis.get("matched_skills", []),
                "missing_skills": analysis.get("missing_skills", []),
                "suggestions": analysis.get("suggestions", []),
                "summary": candidate.get("summary") or f"Matched {score}% with role."
            })

    # Rank by matched score descending
    matched_results.sort(key=lambda c: c["matched_score"], reverse=True)
    paged_results = matched_results[:limit]

    return {
        "job_id": job["id"],
        "job_title": job["title"],
        "company": job["company"],
        "total_matched": len(matched_results),
        "candidates": paged_results
    }

