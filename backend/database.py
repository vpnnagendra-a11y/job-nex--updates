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