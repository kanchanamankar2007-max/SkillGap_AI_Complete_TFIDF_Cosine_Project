
from flask import Flask, render_template, request, redirect, url_for, make_response, session, flash
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
import os
from werkzeug.utils import secure_filename
from pypdf import PdfReader
from docx import Document
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from xml.sax.saxutils import escape
from database import get_connection
import io
import re
import database

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-change-this-secret-before-deployment")
database.create_table()
database.create_account_tables()
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = os.environ.get("FLASK_ENV") == "production"
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

ALLOWED_EXTENSIONS = {"pdf", "docx"}

# ==========================================
# 20 JOB ROLES AND REQUIRED SKILLS
# ==========================================

JOB_REQUIREMENTS = {
    "Python Developer": [
        "Python", "SQL", "Flask", "Django", "Git",
        "OOP", "REST API", "Data Structures", "Algorithms"
    ],

    "Java Developer": [
        "Java", "SQL", "OOP", "Spring Boot", "Git",
        "REST API", "Data Structures", "Algorithms",
        "Maven", "Hibernate"
    ],

    "Full Stack Developer": [
        "HTML", "CSS", "JavaScript", "React", "Node.js",
        "Python", "SQL", "Git", "REST API", "MongoDB"
    ],

    "Frontend Developer": [
        "HTML", "CSS", "JavaScript", "React", "TypeScript",
        "Bootstrap", "Git", "Responsive Design"
    ],

    "Backend Developer": [
        "Python", "Java", "SQL", "Node.js", "Flask",
        "Django", "REST API", "Git", "MongoDB",
        "Data Structures"
    ],

    "Web Developer": [
        "HTML", "CSS", "JavaScript", "React",
        "Node.js", "SQL", "Git", "REST API"
    ],

    "Software Engineer": [
        "Python", "Java", "C++", "SQL", "OOP",
        "Data Structures", "Algorithms", "Git",
        "Problem Solving"
    ],

    "Data Analyst": [
        "Python", "SQL", "Excel", "Data Analysis",
        "Pandas", "NumPy", "Statistics", "Power BI",
        "Tableau"
    ],

    "Data Scientist": [
        "Python", "SQL", "Machine Learning",
        "Statistics", "Pandas", "NumPy",
        "Data Analysis", "Data Visualization",
        "Deep Learning"
    ],

    "Machine Learning Engineer": [
        "Python", "Machine Learning", "Deep Learning",
        "TensorFlow", "PyTorch", "Scikit-learn",
        "NumPy", "Pandas", "Statistics", "Git"
    ],

    "AI Engineer": [
        "Python", "Machine Learning", "Deep Learning",
        "NLP", "TensorFlow", "PyTorch",
        "Generative AI", "LLM", "SQL"
    ],

    "Database Administrator": [
        "SQL", "MySQL", "PostgreSQL", "Oracle",
        "Database Management", "Database Design",
        "Linux", "Python", "Backup and Recovery"
    ],

    "Cloud Engineer": [
        "AWS", "Azure", "Google Cloud", "Linux",
        "Docker", "Kubernetes", "Networking",
        "Python", "Git", "DevOps"
    ],

    "Cybersecurity Analyst": [
        "Cybersecurity", "Networking", "Linux",
        "Python", "Ethical Hacking", "Penetration Testing",
        "Cryptography", "Firewalls", "SIEM"
    ],

    "UI/UX Designer": [
        "UI Design", "UX Design", "Figma",
        "Wireframing", "Prototyping",
        "User Research", "HTML", "CSS"
    ],

    "Business Analyst": [
        "Business Analysis", "SQL", "Excel",
        "Power BI", "Communication",
        "Problem Solving", "Data Analysis",
        "Requirements Gathering", "Documentation"
    ],

    "DevOps Engineer": [
        "Linux", "Python", "Docker", "Kubernetes",
        "AWS", "Git", "CI/CD", "Jenkins",
        "Networking", "DevOps"
    ],

    "Mobile App Developer": [
        "Java", "Kotlin", "Swift", "Flutter",
        "Dart", "React Native", "Firebase",
        "REST API", "Git"
    ],

    "QA / Software Tester": [
        "Software Testing", "Manual Testing",
        "Automation Testing", "Selenium",
        "Python", "Java", "SQL", "API Testing",
        "Jira", "Problem Solving"
    ],

    "NLP Engineer": [
        "Python", "NLP", "Machine Learning",
        "Deep Learning", "TensorFlow", "PyTorch",
        "LLM", "Generative AI", "Statistics"
    ]
}


# ==========================================
# SKILL ALIASES
# ==========================================

SKILL_ALIASES = {
    "Python": ["python", "python programming"],
    "Java": ["java"],
    "C++": ["c++", "cpp"],
    "SQL": ["sql", "mysql", "postgresql"],
    "HTML": ["html", "html5"],
    "CSS": ["css", "css3"],
    "JavaScript": ["javascript", "js"],
    "TypeScript": ["typescript", "ts"],
    "React": ["react", "reactjs"],
    "Node.js": ["node.js", "nodejs"],
    "Flask": ["flask"],
    "Django": ["django"],
    "Spring Boot": ["spring boot"],
    "Git": ["git", "github", "version control"],
    "OOP": ["oop", "object oriented programming"],
    "REST API": ["rest api", "restful api"],
    "Machine Learning": ["machine learning", "ml"],
    "Data Analysis": ["data analysis", "data analytics"],
    "Pandas": ["pandas"],
    "NumPy": ["numpy"],
    "Excel": ["excel", "ms excel", "microsoft excel"],
    "Power BI": ["power bi", "powerbi"],
    "Tableau": ["tableau"],
    "AWS": ["aws", "amazon web services"],
    "Azure": ["azure", "microsoft azure"],
    "Google Cloud": ["google cloud", "gcp"],
    "Statistics": ["statistics", "statistical analysis"],
    "Data Structures": ["data structures", "dsa"],
    "Algorithms": ["algorithms", "algorithm"],
    "Communication": ["communication", "communication skills"],
    "Problem Solving": ["problem solving", "problem-solving"],
    "MongoDB": ["mongodb", "mongo db"],
    "Maven": ["maven"],
    "Hibernate": ["hibernate"],
    "Bootstrap": ["bootstrap"],
    "Responsive Design": ["responsive design", "mobile responsive"],
    "Spring": ["spring framework"],
    "Scikit-learn": ["scikit-learn", "sklearn"],
    "TensorFlow": ["tensorflow"],
    "PyTorch": ["pytorch"],
    "Deep Learning": ["deep learning"],
    "Data Visualization": ["data visualization", "data visualisation"],
    "Generative AI": ["generative ai", "gen ai"],
    "LLM": ["llm", "large language model", "large language models"],
    "NLP": ["nlp", "natural language processing"],
    "Oracle": ["oracle database", "oracle sql"],
    "Database Management": ["database management", "dbms"],
    "Database Design": ["database design"],
    "Linux": ["linux"],
    "Backup and Recovery": ["backup and recovery", "database backup"],
    "Docker": ["docker"],
    "Kubernetes": ["kubernetes", "k8s"],
    "Networking": ["networking", "computer networks"],
    "Cybersecurity": ["cybersecurity", "cyber security"],
    "Ethical Hacking": ["ethical hacking"],
    "Penetration Testing": ["penetration testing", "pen testing"],
    "Cryptography": ["cryptography"],
    "Firewalls": ["firewall", "firewalls"],
    "SIEM": ["siem", "security information and event management"],
    "UI Design": ["ui design", "user interface design"],
    "UX Design": ["ux design", "user experience design"],
    "Figma": ["figma"],
    "Wireframing": ["wireframing", "wireframe"],
    "Prototyping": ["prototyping", "prototype"],
    "User Research": ["user research"],
    "Business Analysis": ["business analysis"],
    "Requirements Gathering": ["requirements gathering"],
    "Documentation": ["documentation", "technical documentation"],
    "DevOps": ["devops"],
    "CI/CD": ["ci/cd", "continuous integration", "continuous delivery"],
    "Jenkins": ["jenkins"],
    "JavaScript Testing": ["javascript testing"],
    "Java Testing": ["java testing"],
    "Kotlin": ["kotlin"],
    "Swift": ["swift"],
    "Flutter": ["flutter"],
    "Dart": ["dart"],
    "React Native": ["react native"],
    "Firebase": ["firebase"],
    "Software Testing": ["software testing", "software quality testing"],
    "Manual Testing": ["manual testing"],
    "Automation Testing": ["automation testing", "automated testing"],
    "Selenium": ["selenium"],
    "API Testing": ["api testing"],
    "Jira": ["jira"]
}


# ==========================================
# LEARNING RECOMMENDATIONS
# ==========================================

LEARNING_RECOMMENDATIONS = {
    "Python": "Learn Python basics, functions, loops and OOP.",
    "Java": "Study Java syntax, classes and inheritance.",
    "C++": "Practice C++ fundamentals and data structures.",
    "SQL": "Learn SQL queries, joins and database management.",
    "HTML": "Learn HTML tags, forms and webpage structure.",
    "CSS": "Practice Flexbox, Grid and responsive design.",
    "JavaScript": "Learn functions, DOM and event handling.",
    "TypeScript": "Study TypeScript types and interfaces.",
    "React": "Learn React components, props and hooks.",
    "Node.js": "Practice server-side JavaScript.",
    "Flask": "Build Python web applications using Flask.",
    "Django": "Learn Django models, views and database integration.",
    "Spring Boot": "Build Java backend applications.",
    "Git": "Practice commits, branches and version control.",
    "OOP": "Study classes, objects and polymorphism.",
    "REST API": "Learn HTTP methods, API requests and JSON.",
    "Machine Learning": "Study supervised learning and model evaluation.",
    "Data Analysis": "Practice data cleaning and visualization.",
    "Pandas": "Learn DataFrames, filtering and data cleaning.",
    "NumPy": "Practice arrays and numerical computing.",
    "Excel": "Learn formulas, pivot tables and charts.",
    "Power BI": "Build interactive dashboards.",
    "Tableau": "Learn charts and data storytelling.",
    "AWS": "Understand cloud computing and AWS services.",
    "Azure": "Explore Microsoft Azure cloud services.",
    "Google Cloud": "Learn Google Cloud fundamentals.",
    "Statistics": "Study probability and statistical distributions.",
    "Data Structures": "Practice arrays, stacks, queues and trees.",
    "Algorithms": "Learn searching, sorting and complexity.",
    "MongoDB": "Practice NoSQL databases and collections.",
    "Spring Boot": "Build REST applications using Spring Boot.",
    "Bootstrap": "Create responsive interfaces using Bootstrap.",
    "Scikit-learn": "Practice machine learning models.",
    "TensorFlow": "Build and train neural networks.",
    "PyTorch": "Learn deep learning model development.",
    "Deep Learning": "Study neural networks and deep learning.",
    "Data Visualization": "Create meaningful charts and dashboards.",
    "Generative AI": "Explore generative AI applications.",
    "LLM": "Learn large language models and their applications.",
    "NLP": "Study text processing and natural language models.",
    "Oracle": "Practice Oracle SQL and database operations.",
    "Database Management": "Study database administration and DBMS.",
    "Database Design": "Learn ER diagrams and normalization.",
    "Linux": "Practice Linux commands and shell basics.",
    "Docker": "Learn containerization using Docker.",
    "Kubernetes": "Study container orchestration.",
    "Networking": "Learn TCP/IP, DNS and network fundamentals.",
    "Cybersecurity": "Study security fundamentals and threat detection.",
    "Ethical Hacking": "Learn ethical hacking concepts in legal labs.",
    "Penetration Testing": "Practice authorized security testing.",
    "Cryptography": "Study encryption and hashing.",
    "Firewalls": "Learn firewall configuration and monitoring.",
    "SIEM": "Understand security event monitoring.",
    "UI Design": "Practice visual design and interface layouts.",
    "UX Design": "Study user experience and usability.",
    "Figma": "Create designs and prototypes in Figma.",
    "Wireframing": "Practice low-fidelity wireframes.",
    "Prototyping": "Create interactive application prototypes.",
    "User Research": "Learn user interviews and usability research.",
    "Business Analysis": "Study business processes and requirements.",
    "Requirements Gathering": "Practice collecting project requirements.",
    "Documentation": "Improve technical documentation skills.",
    "DevOps": "Learn development and operations workflows.",
    "CI/CD": "Understand automated build and deployment pipelines.",
    "Jenkins": "Practice Jenkins automation pipelines.",
    "Kotlin": "Learn Kotlin programming fundamentals.",
    "Swift": "Study Swift and iOS development.",
    "Flutter": "Build cross-platform applications.",
    "Dart": "Learn Dart programming fundamentals.",
    "React Native": "Develop mobile applications with React Native.",
    "Firebase": "Practice authentication and cloud databases.",
    "Software Testing": "Study software testing principles.",
    "Manual Testing": "Practice test cases and defect reporting.",
    "Automation Testing": "Learn test automation frameworks.",
    "Selenium": "Automate browser testing with Selenium.",
    "API Testing": "Test APIs using Postman or similar tools.",
    "Jira": "Learn issue tracking and project workflows."
}


# ==========================================
# HELPER FUNCTIONS
# ==========================================

def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


def extract_text(file):
    filename = secure_filename(file.filename)
    extension = filename.rsplit(".", 1)[1].lower()
    file_bytes = file.read()

    if extension == "pdf":
        reader = PdfReader(io.BytesIO(file_bytes))
        return "\n".join(
            page.extract_text() or ""
            for page in reader.pages
        )

    if extension == "docx":
        document = Document(io.BytesIO(file_bytes))
        return "\n".join(
            paragraph.text
            for paragraph in document.paragraphs
        )

    return ""


def identify_skills(text):
    detected = []
    text = text.lower()

    for skill, aliases in SKILL_ALIASES.items():
        for alias in aliases:
            pattern = (
                r"(?<![a-z0-9])"
                + re.escape(alias.lower())
                + r"(?![a-z0-9])"
            )

            if re.search(pattern, text):
                detected.append(skill)
                break

    return detected


def calculate_skill_gap(detected_skills, required_skills):
    detected_lower = {skill.lower() for skill in detected_skills}

    matched_skills = [
        skill for skill in required_skills
        if skill.lower() in detected_lower
    ]

    missing_skills = [
        skill for skill in required_skills
        if skill.lower() not in detected_lower
    ]

    percentage = round(
        len(matched_skills) / len(required_skills) * 100
    ) if required_skills else 0

    return matched_skills, missing_skills, percentage


def calculate_cosine_similarity(resume_text, job_text):
    """Return TF-IDF cosine similarity as a percentage (0-100)."""
    resume_text = (resume_text or "").strip()
    job_text = (job_text or "").strip()
    if not resume_text or not job_text:
        return 0.0

    try:
        vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
        vectors = vectorizer.fit_transform([resume_text, job_text])
        score = cosine_similarity(vectors[0:1], vectors[1:2])[0][0]
        return round(float(score) * 100, 2)
    except ValueError:
        # For example, both texts may contain only stop words or punctuation.
        return 0.0


# ==========================================
# HOME
# ==========================================



def admin_required(route_function):
    @wraps(route_function)
    def wrapper(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin_login"))
        return route_function(*args, **kwargs)
    return wrapper


@app.route("/")
def home():
    report = session.get("report") or {}
    return render_template(
        "index.html",
        job_roles=list(JOB_REQUIREMENTS.keys()),
        job_role=report.get("job_role"),
        detected_skills=report.get("detected_skills"),
        matched_skills=report.get("matched_skills"),
        missing_skills=report.get("missing_skills"),
        match_percentage=report.get("match_percentage"),
        cosine_similarity_percentage=report.get("cosine_similarity_percentage", 0),
        recommendations=report.get("recommendations"),
        required_skills=report.get("required_skills")
    )


# ==========================================
# RESUME ANALYSIS
# ==========================================

@app.route("/analyze", methods=["POST"])
def analyze():

    file = request.files.get("resume")
    job_role = request.form.get("job_role", "").strip()
    job_description = request.form.get("job_description", "").strip()

    if not file or file.filename == "":
        return render_template(
            "index.html",
            job_roles=list(JOB_REQUIREMENTS.keys()),
            error="Please upload your resume."
        )

    if not allowed_file(file.filename):
        return render_template(
            "index.html",
            job_roles=list(JOB_REQUIREMENTS.keys()),
            error="Please upload a PDF or DOCX file."
        )

    if job_description:
        required_skills = identify_skills(job_description)
        job_label = "Custom Job Description"

        if not required_skills:
            return render_template(
                "index.html",
                job_roles=list(JOB_REQUIREMENTS.keys()),
                error="No recognized skills found in the job description. Please include skills from the supported skill list."
            )

    elif job_role in JOB_REQUIREMENTS:
        required_skills = JOB_REQUIREMENTS[job_role]
        job_label = job_role

    else:
        return render_template(
            "index.html",
            job_roles=list(JOB_REQUIREMENTS.keys()),
            error="Please select a job role or paste a job description."
        )

    try:
        extracted_text = extract_text(file)

        if not extracted_text.strip():
            return render_template(
                "index.html",
                job_roles=list(JOB_REQUIREMENTS.keys()),
                error="No readable text found. Please upload a text-based PDF or DOCX resume."
            )

        detected_skills = identify_skills(extracted_text)

        matched_skills, missing_skills, match_percentage = (
            calculate_skill_gap(detected_skills, required_skills)
        )

        # Compare full resume text with the supplied job description. For a
        # predefined role, use its required-skill list as the comparison text.
        similarity_job_text = job_description if job_description else " ".join(required_skills)
        cosine_similarity_percentage = calculate_cosine_similarity(
            extracted_text, similarity_job_text
        )

        recommendations = {
            skill: LEARNING_RECOMMENDATIONS.get(
                skill,
                "Practice this skill through projects and exercises."
            )
            for skill in missing_skills
        }

        session["report"] = {
            "job_role": job_label,
            "detected_skills": detected_skills,
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "match_percentage": match_percentage,
            "cosine_similarity_percentage": cosine_similarity_percentage,
            "recommendations": recommendations,
            "required_skills": required_skills
        }
        session["report_saved_id"] = None
        if session.get("user_id"):
            session["report_saved_id"] = database.save_analysis(
                session["user_id"], session["report"]
            )

        return render_template(
            "index.html",
            job_roles=list(JOB_REQUIREMENTS.keys()),
            job_role=job_label,
            detected_skills=detected_skills,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            match_percentage=match_percentage,
            cosine_similarity_percentage=cosine_similarity_percentage,
            recommendations=recommendations,
            required_skills=required_skills,
            extracted_text=extracted_text
        )

    except Exception:
        app.logger.exception("Resume analysis failed")
        return render_template(
            "index.html",
            job_roles=list(JOB_REQUIREMENTS.keys()),
            error="Unable to analyse resume. Please check your file and try again."
        )


# ==========================================
# ==========================================
# LEARNER ACCOUNTS
# ==========================================

def learner_required(route_function):
    @wraps(route_function)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please log in to access your learner dashboard.", "info")
            return redirect(url_for("login", next=request.path))
        return route_function(*args, **kwargs)
    return wrapper


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        job_role = request.form.get("job_role", "").strip()
        if not name or not email or len(password) < 8 or job_role not in JOB_REQUIREMENTS:
            return render_template("register.html", job_roles=list(JOB_REQUIREMENTS), error="Enter all details, choose a valid job role and use a password with at least 8 characters.")
        if database.get_user_by_email(email):
            return render_template("register.html", job_roles=list(JOB_REQUIREMENTS), error="An account with this email already exists.")
        user_id = database.create_user(name, email, generate_password_hash(password), job_role)
        guest_report = session.get("report")
        session.clear()
        if guest_report:
            session["report"] = guest_report
        session["user_id"] = user_id
        session["user_name"] = name
        return redirect(url_for("learner_dashboard"))
    return render_template("register.html", job_roles=list(JOB_REQUIREMENTS))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = database.get_user_by_email(email)
        if user and check_password_hash(user["password_hash"], password):
            guest_report = session.get("report")
            session.clear()
            if guest_report:
                session["report"] = guest_report
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            return redirect(url_for("learner_dashboard"))
        return render_template("login.html", error="Invalid email or password.")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


@app.route("/my-dashboard")
@learner_required
def learner_dashboard():
    return render_template(
        "learner_dashboard.html",
        user_name=session.get("user_name", "Learner"),
        history=database.get_user_history(session["user_id"]),
        current_report=session.get("report"),
        saved_id=session.get("report_saved_id")
    )


@app.route("/save-report", methods=["POST"])
@learner_required
def save_report():
    report = session.get("report")
    if not report:
        flash("Analyze a resume before saving a report.", "warning")
    elif not session.get("report_saved_id"):
        session["report_saved_id"] = database.save_analysis(session["user_id"], report)
        flash("Your analysis has been saved to your account.", "success")
    else:
        flash("This analysis is already saved.", "info")
    return redirect(url_for("learner_dashboard"))


@app.route("/my-report/<int:history_id>")
@learner_required
def my_report(history_id):
    report = database.get_saved_analysis(history_id, session["user_id"])
    if not report:
        return "Report not found.", 404
    session["report"] = report
    session["report_saved_id"] = history_id
    return redirect(url_for("home") + "#report")


# PDF REPORT DOWNLOAD
# ==========================================

@app.route("/download_report")
def download_report():

    report = session.get("report")

    if not report:
        return "Please analyse a resume before downloading the report.", 400

    pdf_buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        pdf_buffer,
        pagesize=A4,
        rightMargin=45,
        leftMargin=45,
        topMargin=45,
        bottomMargin=45
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Title"],
        fontSize=21,
        textColor=colors.HexColor("#243B64"),
        alignment=TA_CENTER,
        spaceAfter=15
    )

    heading_style = ParagraphStyle(
        "CustomHeading",
        parent=styles["Heading2"],
        textColor=colors.HexColor("#243B64"),
        spaceBefore=14,
        spaceAfter=8
    )

    normal_style = styles["BodyText"]
    story = []

    story.append(Paragraph("SKILL GAP ANALYSIS REPORT", title_style))

    story.append(Paragraph(
        "AI-Driven Skill Gap Analysis and Employment Outcome Tracking System",
        ParagraphStyle(
            "Subtitle",
            parent=normal_style,
            alignment=TA_CENTER,
            fontSize=9,
            textColor=colors.grey
        )
    ))

    story.append(Spacer(1, 20))

    story.append(Paragraph("Target Job Role", heading_style))
    story.append(Paragraph(escape(report["job_role"]), normal_style))

    story.append(Paragraph("Overall Skill Match", heading_style))
    story.append(Paragraph(
        f"<b>{report['match_percentage']}%</b>",
        ParagraphStyle(
            "Percentage",
            parent=normal_style,
            fontSize=22,
            textColor=colors.HexColor("#16865A")
        )
    ))

    if report.get("cosine_similarity_percentage") is not None:
        story.append(Paragraph("TF-IDF Cosine Similarity", heading_style))
        story.append(Paragraph(
            f"<b>{report['cosine_similarity_percentage']}%</b> (text similarity; separate from the skill-match score)",
            normal_style
        ))

    story.append(HRFlowable(width="100%", color=colors.lightgrey))

    sections = [
        ("Detected Skills", report["detected_skills"]),
        ("Matched Skills", report["matched_skills"]),
        ("Missing Skills", report["missing_skills"]),
        ("Required Job Skills", report["required_skills"])
    ]

    for heading, skills in sections:
        story.append(Paragraph(heading, heading_style))
        story.append(Paragraph(
            escape(", ".join(skills)) if skills else "None",
            normal_style
        ))

    story.append(Paragraph("Learning Recommendations", heading_style))

    if report["recommendations"]:
        for skill, recommendation in report["recommendations"].items():
            story.append(Paragraph(
                f"<b>{escape(skill)}:</b> {escape(recommendation)}",
                normal_style
            ))
            story.append(Spacer(1, 7))
    else:
        story.append(Paragraph(
            "All required skills have been matched.",
            normal_style
        ))

    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", color=colors.lightgrey))
    story.append(Spacer(1, 10))

    story.append(Paragraph(
        "Generated by SkillGap AI",
        ParagraphStyle(
            "Footer",
            parent=normal_style,
            fontSize=9,
            textColor=colors.grey,
            alignment=TA_CENTER
        )
    ))

    doc.build(story)
    pdf_buffer.seek(0)

    response = make_response(pdf_buffer.getvalue())
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = (
        "attachment; filename=Skill_Gap_Report.pdf"
    )

    return response


# ==========================================
# FILE SIZE ERROR
# ==========================================

@app.errorhandler(413)
def file_too_large(error):
    return render_template(
        "index.html",
        job_roles=list(JOB_REQUIREMENTS.keys()),
        error="File is too large. Maximum allowed size is 5 MB."
    ), 413


# ==========================================
# RUN APPLICATION
# ==========================================
@app.route("/employment")
@admin_required
def employment():
    learners = database.get_all_learners()

    return render_template(
        "employment.html",
        job_roles=list(JOB_REQUIREMENTS.keys()),
        learners=learners
    )


@app.route("/add_learner", methods=["POST"])
@admin_required
def add_learner():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    job_role = request.form.get("job_role", "").strip()

    if not name or not email or not job_role:
        return redirect(url_for("employment"))

    database.add_learner(name, email, job_role)

    return redirect(url_for("employment"))
@app.route("/dashboard")
@admin_required
def dashboard():
    learners = database.get_all_learners()

    total = len(learners)
    employed = sum(
        1 for learner in learners
        if learner["employment_status"] == "Employed"
    )
    training = sum(
        1 for learner in learners
        if learner["employment_status"] == "Training"
    )
    seeking = sum(
        1 for learner in learners
        if learner["employment_status"] == "Job Seeking"
    )

    return render_template(
        "dashboard.html",
        learners=learners,
        total=total,
        employed=employed,
        training=training,
        seeking=seeking
    )
@app.route("/update_status/<int:learner_id>", methods=["POST"])
@admin_required
def update_status(learner_id):
    status = request.form.get("status", "")

    allowed_statuses = [
        "Employed",
        "Job Seeking",
        "Training"
    ]

    if status in allowed_statuses:
        database.update_learner_status(learner_id, status)

    return redirect(url_for("dashboard"))
@app.route("/update_progress/<int:learner_id>", methods=["POST"])
@admin_required
def update_progress(learner_id):
    skills = request.form.get("skills_learned", "").strip()

    try:
        progress = int(request.form.get("progress", 0))
    except (ValueError, TypeError):
        return redirect(url_for("dashboard"))

    if not 0 <= progress <= 100:
        return redirect(url_for("dashboard"))

    database.update_learner_progress(
        learner_id,
        skills,
        progress
    )

    return redirect(url_for("dashboard"))
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "")
ADMIN_PASSWORD_HASH = os.environ.get("ADMIN_PASSWORD_HASH", "")


def admin_required(route_function):
    @wraps(route_function)
    def wrapper(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin_login"))
        return route_function(*args, **kwargs)
    return wrapper


@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    error = None

    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        if (ADMIN_USERNAME and username == ADMIN_USERNAME and ADMIN_PASSWORD_HASH and check_password_hash(ADMIN_PASSWORD_HASH, password)):
            session.clear()
            session["admin_logged_in"] = True
            return redirect(url_for("admin_dashboard"))
        else:
            error = "Invalid username or password"

    return render_template("admin_login.html", error=error)

@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():

    conn = get_connection()

    total_learners = conn.execute(
        "SELECT COUNT(*) FROM learners"
    ).fetchone()[0]

    employed_learners = conn.execute(
        """SELECT COUNT(*) FROM learners
           WHERE LOWER(TRIM(employment_status)) = 'employed'"""
    ).fetchone()[0]

    job_seeking = conn.execute(
        """SELECT COUNT(*) FROM learners
           WHERE LOWER(TRIM(employment_status)) = 'job seeking'"""
    ).fetchone()[0]

    higher_studies = conn.execute(
        """SELECT COUNT(*) FROM learners
           WHERE LOWER(TRIM(employment_status)) = 'higher studies'"""
    ).fetchone()[0]

    learners = conn.execute(
        "SELECT * FROM learners ORDER BY id DESC LIMIT 10"
    ).fetchall()

    conn.close()

    return render_template(
        "admin_dashboard.html",
        total_learners=total_learners,
        employed_learners=employed_learners,
        job_seeking=job_seeking,
        higher_studies=higher_studies,
        learners=learners
    )
@app.route("/admin/logout")
@admin_required
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))
@app.route("/admin/update-status/<int:learner_id>", methods=["POST"])
@admin_required
def admin_update_status(learner_id):

    from database import update_learner_status

    status = request.form.get("employment_status", "")

    allowed_statuses = [
        "Job Seeking",
        "Employed",
        "Higher Studies"
    ]

    if status not in allowed_statuses:
        return "Invalid employment status", 400

    update_learner_status(learner_id, status)

    return redirect(url_for("admin_dashboard"))
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=os.environ.get("FLASK_DEBUG") == "1")
