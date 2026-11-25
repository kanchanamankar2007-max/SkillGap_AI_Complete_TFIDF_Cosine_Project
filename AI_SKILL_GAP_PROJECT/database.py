import sqlite3
import os

DATABASE = os.environ.get("DATABASE_PATH", os.path.join(os.path.dirname(os.path.abspath(__file__)), "skillgap.db"))


def get_connection():
    conn = sqlite3.connect(DATABASE)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def create_table():
    conn = get_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS learners (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            job_role TEXT NOT NULL,
            employment_status TEXT DEFAULT 'Job Seeking',
            skills_learned TEXT DEFAULT '',
            progress INTEGER DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()


def add_learner(name, email, job_role):
    conn = get_connection()

    conn.execute("""
        INSERT INTO learners (name, email, job_role)
        VALUES (?, ?, ?)
    """, (name, email, job_role))

    conn.commit()
    conn.close()


def get_all_learners():
    conn = get_connection()

    learners = conn.execute(
        "SELECT * FROM learners ORDER BY id DESC"
    ).fetchall()

    conn.close()
    return learners


def update_learner_status(learner_id, status):
    conn = get_connection()

    conn.execute("""
        UPDATE learners
        SET employment_status = ?
        WHERE id = ?
    """, (status, learner_id))

    conn.commit()
    conn.close()


def update_learner_progress(learner_id, skills_learned, progress):
    conn = get_connection()

    conn.execute("""
        UPDATE learners
        SET skills_learned = ?, progress = ?
        WHERE id = ?
    """, (skills_learned, progress, learner_id))

    conn.commit()
    conn.close()

# --- Learner accounts and saved analysis history ---
def create_account_tables():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE COLLATE NOCASE,
            password_hash TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS analysis_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            job_role TEXT NOT NULL,
            detected_skills TEXT NOT NULL,
            matched_skills TEXT NOT NULL,
            missing_skills TEXT NOT NULL,
            required_skills TEXT NOT NULL,
            recommendations TEXT NOT NULL,
            match_percentage INTEGER NOT NULL,
            cosine_similarity_percentage REAL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)
    # Backward-compatible migration for databases created before TF-IDF support.
    columns = {row[1] for row in conn.execute("PRAGMA table_info(analysis_history)").fetchall()}
    if "cosine_similarity_percentage" not in columns:
        conn.execute("ALTER TABLE analysis_history ADD COLUMN cosine_similarity_percentage REAL")
    conn.commit()
    conn.close()


def create_user(name, email, password_hash, job_role):
    conn = get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, password_hash)
        )
        user_id = cur.lastrowid
        # Keep the existing employment tracking feature connected to registered learners.
        conn.execute(
            """INSERT INTO learners (name, email, job_role)
               VALUES (?, ?, ?)""",
            (name, email, job_role)
        )
        conn.commit()
        return user_id
    finally:
        conn.close()


def get_user_by_email(email):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM users WHERE email = ? COLLATE NOCASE", (email,)
    ).fetchone()
    conn.close()
    return row


def get_user_by_id(user_id):
    conn = get_connection()
    row = conn.execute("SELECT id, name, email FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return row


def save_analysis(user_id, report):
    import json
    conn = get_connection()
    cur = conn.execute("""
        INSERT INTO analysis_history
        (user_id, job_role, detected_skills, matched_skills, missing_skills,
         required_skills, recommendations, match_percentage, cosine_similarity_percentage)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id, report["job_role"],
        json.dumps(report["detected_skills"]),
        json.dumps(report["matched_skills"]),
        json.dumps(report["missing_skills"]),
        json.dumps(report["required_skills"]),
        json.dumps(report["recommendations"]),
        report["match_percentage"],
        report.get("cosine_similarity_percentage")
    ))
    conn.commit()
    history_id = cur.lastrowid
    conn.close()
    return history_id


def get_user_history(user_id):
    conn = get_connection()
    rows = conn.execute("""
        SELECT id, job_role, match_percentage, cosine_similarity_percentage, created_at
        FROM analysis_history WHERE user_id = ?
        ORDER BY id DESC
    """, (user_id,)).fetchall()
    conn.close()
    return rows


def get_saved_analysis(history_id, user_id):
    import json
    conn = get_connection()
    row = conn.execute("""
        SELECT * FROM analysis_history WHERE id = ? AND user_id = ?
    """, (history_id, user_id)).fetchone()
    conn.close()
    if not row:
        return None
    result = dict(row)
    for key in ("detected_skills", "matched_skills", "missing_skills",
                "required_skills", "recommendations"):
        result[key] = json.loads(result[key])
    return result
