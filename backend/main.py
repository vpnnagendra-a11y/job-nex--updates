# JobNex Product - FastAPI Backend
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from database import get_connection
from analyzer import analyze_resume
import json

app = FastAPI(
    title="JobNex Product API",
    description="Backend API for JobNex - Intelligent Resume & Job Description Analyzer Product",
    version="1.0.0"
)

# Enable CORS for frontend clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    resume_text: str = ""
    jd_text: str = ""
    resume: str = ""
    job_description: str = ""

    def get_resume(self) -> str:
        return self.resume_text or self.resume

    def get_jd(self) -> str:
        return self.jd_text or self.job_description


@app.get("/")
def home():
    return {
        "product": "JobNex",
        "version": "1.0.0",
        "message": "JobNex Backend API is running successfully."
    }


@app.post("/api/analyze")
def analyze(request: AnalyzeRequest):
    resume_text = request.get_resume()
    jd_text = request.get_jd()

    if not resume_text.strip() or not jd_text.strip():
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