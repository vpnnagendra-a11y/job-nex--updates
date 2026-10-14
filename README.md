# JobNex - AlgoNex Product (v1.0)

[![Product Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/vpnnagendra-a11y/jobnex_analgonex_product)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Backend](https://img.shields.io/badge/FastAPI-0.100+-009688.svg)](https://fastapi.tiangolo.com/)
[![Database](https://img.shields.io/badge/MySQL-Connector-4479A1.svg)](https://www.mysql.com/)

> **JobNex** is an intelligent resume and job fit analyzer product designed for recruiters, job seekers, and hiring teams. It accurately matches candidate resumes against job descriptions, identifies skill gaps, calculates match scores, and provides actionable recommendations to optimize talent acquisition and job readiness.

---

## 🌟 Key Product Features

- **Automated Skill Extraction & Matching**: Analyzes technical proficiencies across both candidate resumes and target job descriptions.
- **Match Score Computation**: Generates real-time, percentage-based fit scores based on required proficiencies.
- **Skill Gap & Learning Recommendations**: Identifies missing competencies and delivers instant suggestions to bridge qualifications.
- **Audit & History Persistence**: Automatically stores every analysis in a relational MySQL database with timestamps for tracking and retrospective review.
- **High-Performance REST API**: Built on top of FastAPI with CORS support, Pydantic validation, and clean error handling.
- **Modern Responsive Frontend**: Streamlined UI for submitting resumes and inspecting matching breakdowns instantly.

---

## 🏗️ Architecture & Product Structure

```
jobnex/
├── backend/
│   ├── analyzer.py          # AlgoNex resume & JD analysis core logic
│   ├── database.py          # MySQL persistence layer, schema init & queries
│   ├── insert_db.py         # Test insertion script for DB records
│   ├── main.py              # FastAPI REST API endpoints & CORS middleware
│   ├── requirements.txt     # Backend Python dependencies
│   ├── test_analyzer.py     # Unit test runner for resume analyzer
│   └── test_db.py           # Database connectivity verification test
├── frontend/
│   ├── index.html           # JobNex responsive web interface
│   ├── scripts.js           # Client API handler & dynamic UI renderer
│   └── style.css            # Dark-mode product styling
├── .env.example             # Database configuration template
├── .gitignore               # Production Git ignore rules
└── README.md                # Product documentation
```

---

## 🚀 Getting Started

### 1. Prerequisites
- **Python 3.10+**
- **MySQL Server 8.0+**

---

### 2. Database Configuration

1. Make sure your MySQL service is running.
2. Copy the sample environment file and configure your credentials:
   ```bash
   cp .env.example .env
   ```
3. Update the `.env` file with your MySQL details:
   ```env
   DB_HOST=localhost
   DB_PORT=3306
   DB_USER=root
   DB_PASSWORD=your_password
   DB_NAME=resume_analyzer
   ```

---

### 3. Backend Setup

1. Create and activate a Python virtual environment:
   ```bash
   python -m venv .venv
   # Windows (PowerShell):
   .venv\Scripts\Activate.ps1
   # Linux/macOS:
   source .venv/bin/activate
   ```

2. Install backend dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```

3. (Optional) Run the database test to verify your connection:
   ```bash
   python backend/test_db.py
   ```

4. Start the JobNex API server:
   ```bash
   uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
   ```
   The interactive API docs will be available at:
   - **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
   - **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

### 4. Frontend Setup

Open `frontend/index.html` in your web browser, or serve it using any static HTTP server:

```bash
# Using Python built-in HTTP server:
python -m http.server 3000 --directory frontend
```
Navigate to `http://localhost:3000` to access the JobNex product interface.

---

## 📡 API Reference

### Health Check
- **Endpoint**: `GET /`
- **Description**: Returns service health and version metadata.

### Analyze Resume
- **Endpoint**: `POST /api/analyze`
- **Request Body**:
  ```json
  {
    "resume_text": "Python developer experienced in FastAPI, SQL, and Docker.",
    "jd_text": "Looking for a backend engineer proficient in Python, SQL, and Docker."
  }
  ```
- **Response**:
  ```json
  {
    "Analysis_Id": 1,
    "matched_skills": ["python", "sql", "docker"],
    "missing_skills": ["react", "fastapi"],
    "suggestions": [
      "Try learning react for this profile add react to your resume",
      "Try learning fastapi for this profile add fastapi to your resume"
    ],
    "matched_score": 60.0
  }
  ```

### Retrieve Analysis History
- **Endpoint**: `GET /api/analyses`
- **Description**: Returns the latest 20 stored analyses from MySQL.

---

## 📦 Version 1.0 Release Notes

- Initial product release of **JobNex (AlgoNex Product)**.
- Integrated FastAPI backend with MySQL storage.
- Implemented matching algorithm with matched/missing skill classification and score calculation.
- Connected responsive frontend with real-time feedback.
- Configurable environment management with `.env.example`.

---

## 👨‍💻 Author & Maintainer

- **Nagendra** ([@vpnnagendra-a11y](https://github.com/vpnnagendra-a11y))
- Product Repository: [jobnex_analgonex_product](https://github.com/vpnnagendra-a11y/jobnex_analgonex_product.git)
