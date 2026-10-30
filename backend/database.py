# JobNex Product - Database Module
import os
import json
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# MySQL Database configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 3306))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "resume_analyzer")


def get_connection(use_database: bool = True):
    """
    Establish and return a connection to MySQL database.
    If use_database is False, connects without selecting a specific database.
    """
    config = {
        "host": DB_HOST,
        "port": DB_PORT,
        "user": DB_USER,
        "password": DB_PASSWORD,
    }
    if use_database:
        config["database"] = DB_NAME

    return mysql.connector.connect(**config)


def init_db():
    """
    Initializes the MySQL database and necessary tables if they don't already exist.
    """
    conn = None
    cursor = None
    try:
        # Step 1: Connect to MySQL server to create the database if not exists
        conn = get_connection(use_database=False)
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}`;")
        cursor.close()
        conn.close()

        # Step 2: Connect to the specific database to create tables
        conn = get_connection(use_database=True)
        cursor = conn.cursor()

        # Create 'resumes' table for storing structured resume details
        create_resumes_table = """
        CREATE TABLE IF NOT EXISTS resumes (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255),
            email VARCHAR(255),
            phone VARCHAR(50),
            skills TEXT,
            experience TEXT,
            education TEXT,
            summary TEXT,
            raw_text LONGTEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        cursor.execute(create_resumes_table)

        # Create 'resume_analyzer' table for storing resume vs JD analysis runs
        create_analyzer_table = """
        CREATE TABLE IF NOT EXISTS resume_analyzer (
            Analysis_Id INT PRIMARY KEY AUTO_INCREMENT,
            resume_text LONGTEXT NOT NULL,
            jd_text LONGTEXT NOT NULL,
            matched_score DECIMAL(5, 2),
            matched_skills TEXT,
            missing_skills TEXT,
            suggestions TEXT,
            created_At TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        cursor.execute(create_analyzer_table)

        # Create 'users' table
        create_users_table = """
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            email VARCHAR(255) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            role ENUM('admin', 'recruiter', 'user') NOT NULL DEFAULT 'user',
            can_post_jobs BOOLEAN NOT NULL DEFAULT FALSE,
            job_access_granted_by INT NULL,
            job_access_granted_at TIMESTAMP NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        cursor.execute(create_users_table)

        # Create 'job_postings' table
        create_job_postings_table = """
        CREATE TABLE IF NOT EXISTS job_postings (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            company VARCHAR(255) NOT NULL,
            description LONGTEXT NOT NULL,
            required_skills TEXT,
            location VARCHAR(255) DEFAULT 'Remote',
            status ENUM('pending', 'approved', 'rejected', 'disabled') NOT NULL DEFAULT 'approved',
            created_by INT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        );
        """
        cursor.execute(create_job_postings_table)

        # Create 'job_access_requests' table
        create_access_requests_table = """
        CREATE TABLE IF NOT EXISTS job_access_requests (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            reason TEXT,
            status ENUM('pending', 'approved', 'rejected') NOT NULL DEFAULT 'pending',
            reviewed_by INT NULL,
            reviewed_at TIMESTAMP NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        cursor.execute(create_access_requests_table)

        # Create 'audit_logs' table
        create_audit_logs_table = """
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            actor_id INT NOT NULL,
            action VARCHAR(100) NOT NULL,
            target_type VARCHAR(50) NOT NULL,
            target_id INT NOT NULL,
            details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        cursor.execute(create_audit_logs_table)

        conn.commit()
        print(f"[Database] Successfully initialized database '{DB_NAME}' and tables.")
        return True

    except Error as err:
        print(f"[Database] Error during database initialization: {err}")
        return False
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None and conn.is_connected():
            conn.close()


def check_db_connection():
    """
    Verifies the connection to MySQL Server and DB.
    Returns a tuple: (status: bool, message: str)
    """
    try:
        conn = get_connection(use_database=True)
        if conn.is_connected():
            db_info = conn.get_server_info()
            conn.close()
            return True, f"Connected to MySQL Server v{db_info}, Database: '{DB_NAME}'"
    except Error as err:
        return False, str(err)
    return False, "Unknown connection error"


def save_resume(name: str = "", email: str = "", phone: str = "", skills=None,
                experience: str = "", education: str = "", summary: str = "", raw_text: str = "") -> int:
    """
    Saves a new resume to the 'resumes' table and returns the generated resume ID.
    """
    conn = None
    cursor = None
    try:
        conn = get_connection(use_database=True)
        cursor = conn.cursor()

        if isinstance(skills, list):
            skills_str = ", ".join(skills)
        else:
            skills_str = str(skills) if skills else ""

        query = """
        INSERT INTO resumes (name, email, phone, skills, experience, education, summary, raw_text)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        values = (name, email, phone, skills_str, experience, education, summary, raw_text)
        cursor.execute(query, values)
        conn.commit()

        resume_id = cursor.lastrowid
        return resume_id
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None and conn.is_connected():
            conn.close()


def get_all_resumes(limit: int = 50):
    """
    Retrieves all resumes ordered by creation date descending.
    """
    conn = None
    cursor = None
    try:
        conn = get_connection(use_database=True)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM resumes ORDER BY created_at DESC LIMIT %s", (limit,))
        return cursor.fetchall()
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None and conn.is_connected():
            conn.close()


def get_resume_by_id(resume_id: int):
    """
    Retrieves a single resume by its ID.
    """
    conn = None
    cursor = None
    try:
        conn = get_connection(use_database=True)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM resumes WHERE id = %s", (resume_id,))
        return cursor.fetchone()
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None and conn.is_connected():
            conn.close()


def delete_resume(resume_id: int) -> bool:
    """
    Deletes a resume by its ID.
    """
    conn = None
    cursor = None
    try:
        conn = get_connection(use_database=True)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM resumes WHERE id = %s", (resume_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None and conn.is_connected():
            conn.close()


def save_analysis(resume_text: str, jd_text: str, matched_score: float,
                  matched_skills=None, missing_skills=None, suggestions=None) -> int:
    """
    Saves an analysis record into the 'resume_analyzer' table and returns the Analysis_Id.
    """
    conn = None
    cursor = None
    try:
        conn = get_connection(use_database=True)
        cursor = conn.cursor()

        matched_skills_str = ", ".join(matched_skills) if isinstance(matched_skills, list) else str(matched_skills or "")
        missing_skills_str = ", ".join(missing_skills) if isinstance(missing_skills, list) else str(missing_skills or "")
        suggestions_str = " | ".join(suggestions) if isinstance(suggestions, list) else str(suggestions or "")

        query = """
        INSERT INTO resume_analyzer 
        (resume_text, jd_text, matched_score, matched_skills, missing_skills, suggestions)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        values = (resume_text, jd_text, matched_score, matched_skills_str, missing_skills_str, suggestions_str)
        cursor.execute(query, values)
        conn.commit()

        analysis_id = cursor.lastrowid
        return analysis_id
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None and conn.is_connected():
            conn.close()


def get_all_analyses(limit: int = 50):
    """
    Retrieves all resume analyzer records ordered by created_At descending.
    """
    conn = None
    cursor = None
    try:
        conn = get_connection(use_database=True)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM resume_analyzer ORDER BY created_At DESC LIMIT %s", (limit,))
        return cursor.fetchall()
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None and conn.is_connected():
            conn.close()


def get_analysis_by_id(analysis_id: int):
    """
    Retrieves a single analysis by its Analysis_Id.
    """
    conn = None
    cursor = None
    try:
        conn = get_connection(use_database=True)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM resume_analyzer WHERE Analysis_Id = %s", (analysis_id,))
        return cursor.fetchone()
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None and conn.is_connected():
            conn.close()


# ---------------------------------------------------------------------------
# User Data Access
# ---------------------------------------------------------------------------

def create_user(name: str, email: str, password_hash: str, role: str = "user",
                can_post_jobs: bool = False, granted_by: int = None) -> int:
    conn = None
    cursor = None
    try:
        conn = get_connection(use_database=True)
        cursor = conn.cursor()
        query = """
        INSERT INTO users (name, email, password_hash, role, can_post_jobs, job_access_granted_by, job_access_granted_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        granted_at = None
        if can_post_jobs and granted_by:
            from datetime import datetime
            granted_at = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

        cursor.execute(query, (name, email.strip().lower(), password_hash, role, can_post_jobs, granted_by, granted_at))
        conn.commit()
        return cursor.lastrowid
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None and conn.is_connected():
            conn.close()


def get_user_by_email(email: str):
    conn = None
    cursor = None
    try:
        conn = get_connection(use_database=True)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE LOWER(email) = LOWER(%s)", (email.strip(),))
        user = cursor.fetchone()
        if user:
            user["canPostJobs"] = bool(user.get("can_post_jobs"))
            user["jobAccessGrantedBy"] = user.get("job_access_granted_by")
            user["jobAccessGrantedAt"] = str(user.get("job_access_granted_at")) if user.get("job_access_granted_at") else None
        return user
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None and conn.is_connected():
            conn.close()


def get_user_by_id(user_id: int):
    conn = None
    cursor = None
    try:
        conn = get_connection(use_database=True)
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT u.id, u.name, u.email, u.role, u.can_post_jobs, 
                   u.job_access_granted_by, u.job_access_granted_at, u.created_at,
                   grantor.name AS granted_by_name
            FROM users u
            LEFT JOIN users grantor ON u.job_access_granted_by = grantor.id
            WHERE u.id = %s
            """,
            (user_id,)
        )
        user = cursor.fetchone()
        if user:
            user["canPostJobs"] = bool(user.get("can_post_jobs"))
            user["jobAccessGrantedBy"] = user.get("job_access_granted_by")
            user["jobAccessGrantedAt"] = str(user.get("job_access_granted_at")) if user.get("job_access_granted_at") else None
        return user
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None and conn.is_connected():
            conn.close()


def get_users(role: str = None, can_post_jobs: bool = None, search: str = None, page: int = 1, limit: int = 20):
    conn = None
    cursor = None
    try:
        conn = get_connection(use_database=True)
        cursor = conn.cursor(dictionary=True)

        where_clauses = []
        params = []

        if role:
            where_clauses.append("u.role = %s")
            params.append(role)

        if can_post_jobs is not None:
            where_clauses.append("u.can_post_jobs = %s")
            params.append(1 if can_post_jobs else 0)

        if search:
            where_clauses.append("(u.name LIKE %s OR u.email LIKE %s)")
            params.extend([f"%{search}%", f"%{search}%"])

        where_str = (" WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

        # Count total
        count_query = f"SELECT COUNT(*) AS total FROM users u {where_str}"
        cursor.execute(count_query, params)
        total = cursor.fetchone()["total"]

        # Fetch records
        offset = max(0, (page - 1) * limit)
        data_query = f"""
            SELECT u.id, u.name, u.email, u.role, u.can_post_jobs, 
                   u.job_access_granted_by, u.job_access_granted_at, u.created_at,
                   grantor.name AS granted_by_name
            FROM users u
            LEFT JOIN users grantor ON u.job_access_granted_by = grantor.id
            {where_str}
            ORDER BY u.id DESC
            LIMIT %s OFFSET %s
        """
        data_params = params + [limit, offset]
        cursor.execute(data_query, data_params)
        users = cursor.fetchall()

        for user in users:
            user["canPostJobs"] = bool(user.get("can_post_jobs"))
            user["jobAccessGrantedBy"] = user.get("job_access_granted_by")
            user["jobAccessGrantedAt"] = str(user.get("job_access_granted_at")) if user.get("job_access_granted_at") else None

        return {
            "total": total,
            "page": page,
            "limit": limit,
            "users": users
        }
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None and conn.is_connected():
            conn.close()


def update_user_job_access(user_id: int, can_post_jobs: bool, admin_id: int) -> bool:
    conn = None
    cursor = None
    try:
        conn = get_connection(use_database=True)
        cursor = conn.cursor()
        if can_post_jobs:
            query = """
            UPDATE users 
            SET can_post_jobs = TRUE, job_access_granted_by = %s, job_access_granted_at = NOW()
            WHERE id = %s
            """
            cursor.execute(query, (admin_id, user_id))
        else:
            query = """
            UPDATE users 
            SET can_post_jobs = FALSE, job_access_granted_by = %s, job_access_granted_at = NOW()
            WHERE id = %s
            """
            cursor.execute(query, (admin_id, user_id))

        conn.commit()
        return cursor.rowcount > 0
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None and conn.is_connected():
            conn.close()


# ---------------------------------------------------------------------------
# Job Postings Data Access
# ---------------------------------------------------------------------------

def create_job_posting(title: str, company: str, description: str,
                       required_skills: str = "", location: str = "Remote",
                       created_by: int = 1, status: str = "approved") -> int:
    conn = None
    cursor = None
    try:
        conn = get_connection(use_database=True)
        cursor = conn.cursor()
        query = """
        INSERT INTO job_postings (title, company, description, required_skills, location, status, created_by)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (title, company, description, required_skills, location, status, created_by))
        conn.commit()
        return cursor.lastrowid
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None and conn.is_connected():
            conn.close()


def get_job_postings(status: str = None, created_by: int = None, search: str = None, page: int = 1, limit: int = 20):
    conn = None
    cursor = None
    try:
        conn = get_connection(use_database=True)
        cursor = conn.cursor(dictionary=True)

        where_clauses = []
        params = []

        if status:
            where_clauses.append("j.status = %s")
            params.append(status)

        if created_by:
            where_clauses.append("j.created_by = %s")
            params.append(created_by)

        if search:
            where_clauses.append("(j.title LIKE %s OR j.company LIKE %s OR j.required_skills LIKE %s OR j.description LIKE %s)")
            params.extend([f"%{search}%", f"%{search}%", f"%{search}%", f"%{search}%"])

        where_str = (" WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

        # Count total
        count_query = f"SELECT COUNT(*) AS total FROM job_postings j {where_str}"
        cursor.execute(count_query, params)
        total = cursor.fetchone()["total"]

        offset = max(0, (page - 1) * limit)
        data_query = f"""
            SELECT j.*, u.name AS creator_name, u.email AS creator_email
            FROM job_postings j
            LEFT JOIN users u ON j.created_by = u.id
            {where_str}
            ORDER BY j.created_at DESC
            LIMIT %s OFFSET %s
        """
        data_params = params + [limit, offset]
        cursor.execute(data_query, data_params)
        jobs = cursor.fetchall()

        return {
            "total": total,
            "page": page,
            "limit": limit,
            "jobs": jobs
        }
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None and conn.is_connected():
            conn.close()


def get_job_posting_by_id(job_id: int):
    conn = None
    cursor = None
    try:
        conn = get_connection(use_database=True)
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT j.*, u.name AS creator_name, u.email AS creator_email
            FROM job_postings j
            LEFT JOIN users u ON j.created_by = u.id
            WHERE j.id = %s
            """,
            (job_id,)
        )
        return cursor.fetchone()
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None and conn.is_connected():
            conn.close()


def update_job_posting_status(job_id: int, status: str) -> bool:
    conn = None
    cursor = None
    try:
        conn = get_connection(use_database=True)
        cursor = conn.cursor()
        cursor.execute("UPDATE job_postings SET status = %s WHERE id = %s", (status, job_id))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None and conn.is_connected():
            conn.close()


# ---------------------------------------------------------------------------
# Access Requests Data Access
# ---------------------------------------------------------------------------

def create_access_request(user_id: int, reason: str = "") -> int:
    conn = None
    cursor = None
    try:
        conn = get_connection(use_database=True)
        cursor = conn.cursor()
        query = """
        INSERT INTO job_access_requests (user_id, reason, status)
        VALUES (%s, %s, 'pending')
        """
        cursor.execute(query, (user_id, reason))
        conn.commit()
        return cursor.lastrowid
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None and conn.is_connected():
            conn.close()


def get_access_requests(status: str = None, page: int = 1, limit: int = 20):
    conn = None
    cursor = None
    try:
        conn = get_connection(use_database=True)
        cursor = conn.cursor(dictionary=True)

        where_clauses = []
        params = []
        if status:
            where_clauses.append("r.status = %s")
            params.append(status)

        where_str = (" WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

        count_query = f"SELECT COUNT(*) AS total FROM job_access_requests r {where_str}"
        cursor.execute(count_query, params)
        total = cursor.fetchone()["total"]

        offset = max(0, (page - 1) * limit)
        data_query = f"""
            SELECT r.*, u.name AS user_name, u.email AS user_email,
                   reviewer.name AS reviewer_name
            FROM job_access_requests r
            LEFT JOIN users u ON r.user_id = u.id
            LEFT JOIN users reviewer ON r.reviewed_by = reviewer.id
            {where_str}
            ORDER BY r.created_at DESC
            LIMIT %s OFFSET %s
        """
        cursor.execute(data_query, params + [limit, offset])
        requests = cursor.fetchall()

        return {
            "total": total,
            "page": page,
            "limit": limit,
            "requests": requests
        }
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None and conn.is_connected():
            conn.close()


def update_access_request_status(request_id: int, status: str, reviewed_by: int) -> bool:
    conn = None
    cursor = None
    try:
        conn = get_connection(use_database=True)
        cursor = conn.cursor()
        query = """
        UPDATE job_access_requests
        SET status = %s, reviewed_by = %s, reviewed_at = NOW()
        WHERE id = %s
        """
        cursor.execute(query, (status, reviewed_by, request_id))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None and conn.is_connected():
            conn.close()


def get_access_request_by_id(request_id: int):
    conn = None
    cursor = None
    try:
        conn = get_connection(use_database=True)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM job_access_requests WHERE id = %s", (request_id,))
        return cursor.fetchone()
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None and conn.is_connected():
            conn.close()


# ---------------------------------------------------------------------------
# Audit Logs Data Access
# ---------------------------------------------------------------------------

def create_audit_log(actor_id: int, action: str, target_type: str, target_id: int, details: str = None) -> int:
    conn = None
    cursor = None
    try:
        conn = get_connection(use_database=True)
        cursor = conn.cursor()
        query = """
        INSERT INTO audit_logs (actor_id, action, target_type, target_id, details)
        VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(query, (actor_id, action, target_type, target_id, details))
        conn.commit()
        return cursor.lastrowid
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None and conn.is_connected():
            conn.close()


def get_audit_logs(target_type: str = None, page: int = 1, limit: int = 50):
    conn = None
    cursor = None
    try:
        conn = get_connection(use_database=True)
        cursor = conn.cursor(dictionary=True)

        where_clauses = []
        params = []
        if target_type:
            where_clauses.append("a.target_type = %s")
            params.append(target_type)

        where_str = (" WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

        count_query = f"SELECT COUNT(*) AS total FROM audit_logs a {where_str}"
        cursor.execute(count_query, params)
        total = cursor.fetchone()["total"]

        offset = max(0, (page - 1) * limit)
        data_query = f"""
            SELECT a.*, u.name AS actor_name, u.email AS actor_email
            FROM audit_logs a
            LEFT JOIN users u ON a.actor_id = u.id
            {where_str}
            ORDER BY a.created_at DESC
            LIMIT %s OFFSET %s
        """
        cursor.execute(data_query, params + [limit, offset])
        logs = cursor.fetchall()

        return {
            "total": total,
            "page": page,
            "limit": limit,
            "logs": logs
        }
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None and conn.is_connected():
            conn.close()
