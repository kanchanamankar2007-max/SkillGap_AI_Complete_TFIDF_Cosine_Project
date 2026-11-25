# SkillGap AI – Complete Project (with TF-IDF + Cosine Similarity)

This folder contains the complete Flask project, not only the changed files. It retains the existing learner accounts, admin dashboard, employment tracking, resume analysis, skill-gap calculation, recommendations, analysis history, and PDF report features.

## New feature
- TF-IDF converts resume and job-description text into weighted text vectors.
- Cosine similarity calculates a separate text-similarity percentage.
- For a custom job description, the resume is compared with that description. For a predefined job role, the resume is compared with that role's required-skill text.
- The original rule-based skill-match percentage, matched/missing skills, and recommendations are unchanged.
- Existing SQLite databases are migrated safely by adding a nullable `cosine_similarity_percentage` column only when it is missing. Existing learner accounts and history rows are retained.

## Replace your local project safely (Windows)
1. Make a backup of your current project folder first. Do not delete your existing `skillgap.db` or any `.env` file.
2. Extract this ZIP. Open the extracted `AI_SKILL_GAP_PROJECT` folder.
3. Copy the contents of that folder into your existing project/repository folder and allow the updated project files to replace files with the same names. Keep your existing database file, `.env` file, and any personal files that are not included in this ZIP.
4. Open a terminal in the project folder and activate your existing virtual environment, or create one:
   ```powershell
   py -m venv .venv
   .venv\Scripts\Activate.ps1
   ```
5. Install/update dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
6. Run locally:
   ```powershell
   python app.py
   ```
7. Open `http://127.0.0.1:5000` and test resume upload, skill matching, similarity score, recommendations, learner login/history, admin pages, and PDF reports before deploying.

## Environment variables
Keep the values already configured for your working deployment. The application supports:
- `SECRET_KEY`
- `ADMIN_USERNAME`
- `ADMIN_PASSWORD_HASH`
- `DATABASE_PATH`

For a local development environment, set your own secret key and admin credentials. Never commit real passwords, password hashes, or production secrets to a public repository.

## Deploying the update to your existing Render service
1. First confirm the local app works.
2. Commit and push the replacement project files to the same GitHub repository connected to your existing Render service.
3. Render should build using `pip install -r requirements.txt` and start using the existing `gunicorn app:app` command.
4. Do not create a new Render service or change your existing environment variables, database path, disk mount, or service settings just for this code update.
5. After deployment, test the live app. Keep a backup of your SQLite database before any production database maintenance.

## Main routes
- `/` – public homepage and resume analysis
- `/register` – learner registration
- `/login` – learner login
- `/my-dashboard` – learner analysis history
- `/admin` – admin login
- `/admin/dashboard` – admin dashboard

## Notes
- PDF and DOCX resume uploads are supported by the existing application.
- The text-similarity score is not the same as the skill-match percentage. A high cosine score does not prove that every required skill is present; use both measures together.
- `scikit-learn` is an added dependency and is included in `requirements.txt`.
