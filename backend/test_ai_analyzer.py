#test_ai_analyzer.py
import json 
from ai_analyzer import analyze_resume_with_ai

resume_text=''' VAMSI PRIYA TAVVA
+91 9908366216 · vamsipriya725@gmail.com · linkedin.com/in/tavva-vamsipriya · github.com/vamsipriya725-arch · Bengaluru, India
P R O F E S S I O N A L S U M M A R Y
Python Developer with hands-on experience building FastAPI applications, REST APIs, and LLM-integrated systems, with a strong
academic foundation in Information Technology. Applies data analysis skills and current industry trends in AI and cloud to deliver tested,
deployment-ready solutions across full-stack and backend projects.
E X P E R I E N C E
Python Developer Intern | Algonex IT Solutions | Apr 2026 – Jun 2026
• Implemented features across 5+ application modules using Python, FastAPI, React, and SQL, delivering working software aligned
with project planning milestones each sprint.
• Built and tested REST APIs for authentication, data management, and CRUD workflows, resolving 20+ functional and edge-case
issues before deployment.
• Deployed applications on Vercel and Netlify, configured integrations, and verified application behavior post-deployment.
SQL AI Fellow | Algonex IT Solutions | Jan 2026 – Apr 2026
• Delivered 20+ Python scripts and MySQL database modules across a structured 4-month program, meeting 100% of sprint deadlines
through basic project management practices.
• Implemented 20+ optimized SQL queries for data extraction, transformation, and CRUD operations on relational databases supporting
live AI projects.
• Managed schema design and data operations in MySQL, supporting backend data workflows powering AI model inputs across 3+
cross-functional project modules.
P R O J E C T S
AI Resume Analyzer & Job Match Platform | Python, React, MySQL, LLM, REST API, Git
• Engineered an LLM-powered analysis module that evaluates resume-JD fit using data analysis techniques, generating match scores,
skill gap reports, and personalized learning paths.
• Developed Python REST APIs connecting a React frontend to a MySQL database storing users, resumes, and analysis results; managed
feature-based Git workflow across the team.
Event Management Platform | Python, FastAPI, Supabase, Vercel | AIDLC
• Built a Python/FastAPI platform spanning 5+ modules, integrating Supabase authentication, real-time data synchronization, and
schema design informed by 10+ user interviews.
• Validated workflows through 3 feedback iterations, resolving 20+ edge cases before release, demonstrating end-to-end project
execution from planning to deployment.
E D U C A T I O N
Bachelor of Technology in Information Technology | Lakireddy Bali Reddy College of Engineering | 2021
– May 2025 | CGPA: 8.59
S K I L L S
Technical: Python, SQL, JavaScript, FastAPI, REST APIs, React, MySQL, HTML, CSS, Django, Flask, data analysis, data extraction,
OOP, data structures and algorithms, AIDLC, Git, GitHub, Vercel, Netlify, Streamlit, Supabase
Tools: Git, GitHub, Vercel, Netlify, Streamlit Community Cloud, Supabase, Antigravity
C E R T I F I C A T I O N S
• Python Certification, HackerRank
• SQL (Basic) Certification, HackerRank
• Microsoft Certified: Fabric Data Engineer Associate, Microsoft
• Generative AI Skill Badge, Google Cloud'''

jd_text='''Skip to content
HomeIBM
IBM Careers
Login
< Back to search results
Intern / Associate Engineer
Bangalore, Karnataka, India
Entry Level
Email
X
LinkedIn
Apply now
Introduction
This is a pre-requisition to screen and assess applicants across roles of IBM for different line of business and can be but not limited to the below units

IT Services & Consulting: Delivers enterprise technology, hybrid cloud solutions, and consulting services. Infrastructure & AI: Focuses on enterprise AI agents, hybrid cloud architecture, and infrastructure innovation

Your role and responsibilities
Students completing Engineering Degree ( BE/B.Tech/ME/M.Tech) by May 2027 with Computer Science, Electrical and Electronics Specializations/Branch of Studies only can apply•Only Students with a current aggregate of 6/ 60% or above CGPA / Percentage in the highest degree pursuing can apply

Required education
Bachelor's Degree
Required technical and professional expertise
• Exposure to Academic Programs: Currently enrolled at a university or educational institution, or recently completed qualification.

• Understanding of Business Operations: Familiarity with basic business concepts and processes, gained through academic studies or previous internships.

• Basic Administrative Skills: Experience with administrative tasks, such as data entry, record-keeping, or document management.

• Foundational Communication Skills: Ability to effectively communicate ideas and collaborate with colleagues in a team environment.

• Application of Theoretical Knowledge: Exposure to applying theoretical concepts and skills learned in an academic setting to practical problems or projects.



These are basic call outs and actual required skills may differ

Preferred technical and professional experience
• Familiarity with Industry Trends: Exposure to current industry trends and developments in a specific field, gained through academic studies or personal projects, would be beneficial in this role.

• Basic Project Management: Experience working on small projects or contributing to group assignments, demonstrating an understanding of project planning and execution principles.

• Data Analysis Skills: Exposure to data analysis tools and techniques, such as data visualization or statistical analysis, would be advantageous in supporting business operations and projects.

These are high-level callouts, and the specific skills required may vary based on the role.

Years of Experience:0 - 0
ABOUT BUSINESS UNIT
IBM Corporate Headquarters (CHQ) team represents a variety of functions such as marketing, finance, legal, operations, HR, and more, all working together to solve some of the world's most complex problems, help our clients achieve success and build collaborative work environments for IBMers.
YOUR LIFE @ IBM
In a world where technology never stands still, we understand that, dedication to our clients success, innovation that matters, and trust and personal responsibility in all our relationships, lives in what we do as IBMers as we strive to be the catalyst that makes the world work better.

Being an IBMer means you’ll be able to learn and develop yourself and your career, you’ll be encouraged to be courageous and experiment everyday, all whilst having continuous trust and support in an environment where everyone can thrive whatever their personal or professional background.



Our IBMers are growth minded, always staying curious, open to feedback and learning new information and skills to constantly transform themselves and our company. They are trusted to provide on-going feedback to help other IBMers grow, as well as collaborate with colleagues keeping in mind a team focused approach to include different perspectives to drive exceptional outcomes for our customers. The courage our IBMers have to make critical decisions everyday is essential to IBM becoming the catalyst for progress, always embracing challenges with resources they have to hand, a can-do attitude and always striving for an outcome focused approach within everything that they do.

When applying to jobs of your interest, we recommend that you do so for those that match your experience and expertise. Our recruiters advise that you apply to not more than 3 roles in a year for the best candidate experience. For additional information about location requirements, please discuss with the recruiter following submission of your application.
Job Title
Intern / Associate Engineer
Job ID
137023
City / Township / Village
Bangalore
State / Province
Karnataka
Country
India
Work arrangement
Hybrid
Area of work
Cloud
Employment type
Regular
Position type
Entry Level
Travel required
No Travel
Company
(0063) IBM India Private Limited
Shift
General (daytime)
Is this role a commissionable/sales incentive based position?
No
Apply now

'''

result=analyze_resume_with_ai(resume_text,jd_text)
try:
    data=json.loads(result)
    print("Matchscore:",data["matched_score"])
    print("Matching skills:",data["matched_skills"])
    print("Missing skills:",data["missing_skills"])
    print("Suggestions:",data["suggestions"])
    print("Summary:",data["summary"])
except(json.JSONDecodeError,KeyError) as error:
    print("Hey! Fix the json or column names")
    print("Hey! Error is:",error)