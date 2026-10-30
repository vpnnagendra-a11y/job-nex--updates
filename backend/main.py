# JobNex Product - FastAPI Backend
import os
import sys
import json
import logging
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from database import get_connection, init_db
from analyzer import analyze_resume

# Import modular routers
from routes.auth_routes import router as auth_router
from routes.admin_routes import router as admin_router
from routes.job_routes import router as job_router
from routes.recruiter_routes import router as recruiter_router

app = FastAPI(
    title="JobNex Product API",
    description="Backend API for JobNex - Intelligent Resume & Job Description Analyzer with Admin & Recruiter Modules",
    version="1.1.0"
)

# Enable CORS for frontend clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(job_router)
app.include_router(recruiter_router)


@app.on_event("startup")
def startup_db_init():
    try:
        init_db()
    except Exception as e:
        logger.warning(f"Database initialization deferred or failed: {e}")


class AnalyzeRequest(BaseModel):
    resume_text: Optional[str] = None
    jd_text: Optional[str] = None
    resume: Optional[str] = None
    job_description: Optional[str] = None

    def get_resume(self) -> str:
        return (self.resume_text or self.resume or "").strip()

    def get_jd(self) -> str:
        return (self.jd_text or self.job_description or "").strip()


@app.get("/")
def home():
    return {
        "product": "JobNex",
        "version": "1.1.0",
        "message": "JobNex Backend API is running successfully.",
        "modules": {
            "analyzer": "/api/analyze",
            "auth": "/api/auth",
            "admin": "/api/admin",
            "jobs": "/api/jobs",
            "recruiter": "/api/recruiter"
        }
    }


@app.post("/api/analyze")
def analyze(request: AnalyzeRequest):
    resume_text = request.get_resume()
    jd_text = request.get_jd()

    if not resume_text or not jd_text:
        raise HTTPException(
            status_code=400,
            detail="Both resume and job description text are required."
        )

    result = analyze_resume(resume_text, jd_text)
    connection = None
    cursor = None
    analysis_id = None

    try:
        connection = get_connection()
        cursor = connection.cursor()
        query = """
            INSERT INTO resume_analyzer (resume_text, jd_text, matched_skills, missing_skills, matched_score, suggestions)
            VALUES (%s, %s, %s, %s, %s, %s)
        """

        cursor.execute(
            query, (
                resume_text,
                jd_text,
                json.dumps(result["matched_skills"]),
                json.dumps(result["missing_skills"]),
                result["matched_score"],
                json.dumps(result["suggestions"])
            )
        )

        connection.commit()
        analysis_id = cursor.lastrowid

    except Exception as error:
        if connection is not None and connection.is_connected():
            connection.rollback()
            logger.exception("Failed to save analysis")
        print(f"[Warning] Could not persist analysis to database: {error}")

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()

    return {
        "Analysis_Id": analysis_id,
        **result
    }


# Backend API: Retrieve analysis history
@app.get("/api/analyses")
def get_analyses():
    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        query = """SELECT
                Analysis_id,
                matched_score,
                matched_skills,
                missing_skills,
                created_At
            FROM resume_analyzer
            ORDER BY Analysis_id DESC
            LIMIT 20"""

        cursor.execute(query)
        analyses = cursor.fetchall()

        for analysis in analyses:
            for field in ("matched_skills", "missing_skills"):
                if field in analysis:
                    value = analysis[field]
                    if isinstance(value, str):
                        try:
                            analysis[field] = json.loads(value)
                        except Exception:
                            pass

        return {"analyses": analyses}

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve analyses: {str(error)}"
        ) from error

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()
