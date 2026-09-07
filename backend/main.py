from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pdfplumber
import io
import re
import requests

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

MAX_FILE_SIZE_MB = 10

# ---------------------------------------------------------------------
# Adzuna API credentials (free tier). Get your own at:
# https://developer.adzuna.com/
# ---------------------------------------------------------------------
ADZUNA_APP_ID = "dbca915e"
ADZUNA_APP_KEY = "ce2d3986f6b4415f468328de2704a9b1"

# ---------------------------------------------------------------------
# A reasonably wide skills dictionary. This is a rule-based approach —
# we search the resume text for any of these known skill names.
# You can keep adding to this list as you test with more resumes.
# ---------------------------------------------------------------------
SKILLS_DB = [
    "Python", "Java", "C++", "C", "JavaScript", "TypeScript", "SQL", "R",
    "HTML", "CSS", "React", "Node.js", "Angular", "Vue", "Django", "Flask",
    "FastAPI", "Streamlit", "Pandas", "NumPy", "Matplotlib", "Seaborn",
    "Scikit-learn", "TensorFlow", "PyTorch", "Keras", "Machine Learning",
    "Deep Learning", "Data Science", "Data Analysis", "Data Visualization",
    "Power BI", "Tableau", "Excel", "MySQL", "PostgreSQL", "MongoDB",
    "Git", "GitHub", "Docker", "Kubernetes", "AWS", "Azure", "GCP",
    "Linux", "REST API", "NLP", "Computer Vision", "OpenCV", "Statistics",
    "Probability", "ETL", "Spark", "Hadoop", "Firebase", "Figma",
    "Java Script", "Bootstrap", "Tailwind", "PHP", "C#", ".NET",
]

EDUCATION_KEYWORDS = [
    "B.Tech", "B Tech", "BTech", "Bachelor", "B.E", "BE ", "M.Tech", "MTech",
    "Master", "M.E", "MBA", "BCA", "MCA", "BSc", "MSc", "B.Sc", "M.Sc",
    "Diploma", "Ph.D", "PhD", "Intermediate", "High School", "12th", "10th"
]

SECTION_HEADERS = {
    "EDUCATION": ["EDUCATION", "ACADEMIC BACKGROUND", "QUALIFICATION"],
    "SKILLS": ["SKILLS", "TECHNICAL SKILLS", "KEY SKILLS", "CORE SKILLS"],
    "EXPERIENCE": ["EXPERIENCE", "WORK EXPERIENCE", "INTERNSHIP", "INTERNSHIPS", "PROFESSIONAL EXPERIENCE"],
    "PROJECTS": ["PROJECTS", "ACADEMIC PROJECTS", "PERSONAL PROJECTS"],
}


def split_into_sections(text: str) -> dict:
    """Splits resume text into sections based on common header keywords."""
    lines = text.split("\n")
    sections = {key: [] for key in SECTION_HEADERS}
    sections["OTHER"] = []
    current = "OTHER"

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue

        upper = line.upper()
        matched = None
        for section_name, keywords in SECTION_HEADERS.items():
            for kw in keywords:
                # A line counts as a header if it's short and mostly just the keyword
                if upper.startswith(kw) and len(line) <= len(kw) + 15:
                    matched = section_name
                    break
            if matched:
                break

        if matched:
            current = matched
        else:
            sections[current].append(line)

    return sections


def extract_skills(text: str) -> list:
    text_lower = text.lower()
    found = []
    for skill in SKILLS_DB:
        pattern = r'\b' + re.escape(skill.lower()) + r'\b'
        if re.search(pattern, text_lower):
            found.append(skill)
    return sorted(set(found))


def extract_education(section_lines: list) -> list:
    results = []
    joined = " ".join(section_lines)

    # Find degree mentions
    degree_pattern = r'(' + '|'.join(re.escape(k) for k in EDUCATION_KEYWORDS) + r')[^,.\n]*'
    matches = re.findall(degree_pattern, joined, flags=re.IGNORECASE)

    for line in section_lines:
        has_degree = any(k.lower() in line.lower() for k in EDUCATION_KEYWORDS)
        has_institute = any(w in line for w in ["University", "College", "Institute", "School"])
        if has_degree or has_institute:
            results.append(line)

    # De-duplicate while preserving order
    seen = set()
    unique = []
    for r in results:
        if r not in seen:
            seen.add(r)
            unique.append(r)

    return unique[:4]  # cap at 4 entries to avoid noise


def extract_experience(section_lines: list) -> list:
    results = []
    date_pattern = r'(\d{4}|\bJan\b|\bFeb\b|\bMar\b|\bApr\b|\bMay\b|\bJun\b|\bJul\b|\bAug\b|\bSep\b|\bOct\b|\bNov\b|\bDec\b|\d+\s*(month|months|year|years))'

    for line in section_lines:
        if any(w.lower() in line.lower() for w in ["intern", "engineer", "developer", "analyst", "trainee", "assistant"]):
            duration_match = re.search(date_pattern, line, flags=re.IGNORECASE)
            results.append({
                "role": line,
                "meta": duration_match.group(0) if duration_match else ""
            })

    return results[:5]


def extract_projects(section_lines: list) -> list:
    results = []
    current_title = None
    current_desc = []

    for line in section_lines:
        # Heuristic: short lines without periods are likely titles,
        # longer lines are likely descriptions
        if len(line) < 70 and not line.endswith("."):
            if current_title:
                results.append({
                    "name": current_title,
                    "desc": " ".join(current_desc)[:150]
                })
            current_title = line
            current_desc = []
        else:
            current_desc.append(line)

    if current_title:
        results.append({
            "name": current_title,
            "desc": " ".join(current_desc)[:150]
        })

    return results[:5]


@app.post("/upload-resume")
async def upload_resume(file: UploadFile = File(...)):

    filename = file.filename or ""
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed. Please upload your resume in .pdf format."
        )

    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="Invalid file type detected. Please upload a genuine PDF file."
        )

    contents = await file.read()

    size_mb = len(contents) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=400,
            detail=f"File too large ({size_mb:.1f}MB). Max allowed is {MAX_FILE_SIZE_MB}MB."
        )

    try:
        with pdfplumber.open(io.BytesIO(contents)) as pdf:
            if len(pdf.pages) == 0:
                raise HTTPException(status_code=400, detail="PDF has no pages.")

            full_text = ""
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    full_text += text + "\n"
            page_count = len(pdf.pages)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="This file could not be read as a valid PDF. It may be corrupted or renamed from another format."
        )

    if not full_text.strip():
        raise HTTPException(
            status_code=400,
            detail="No readable text found in this PDF. It may be a scanned image — please upload a text-based PDF."
        )

    # ---- Parse structured data from the extracted text ----
    sections = split_into_sections(full_text)

    skills = extract_skills(full_text)
    education = extract_education(sections["EDUCATION"] or sections["OTHER"])
    experience = extract_experience(sections["EXPERIENCE"])
    projects = extract_projects(sections["PROJECTS"])

    ats_result = calculate_ats_score(full_text, skills, education, experience, projects)

    return {
        "filename": filename,
        "pages": page_count,
        "extracted_text": full_text.strip(),
        "skills": skills,
        "education": education,
        "experience": experience,
        "projects": projects,
        "ats_score": ats_result["score"],
        "ats_verdict": ats_result["verdict"],
        "ats_verdict_desc": ats_result["verdict_desc"],
        "ats_breakdown": ats_result["breakdown"],
        "ats_passed_checks": ats_result["passed_checks"],
        "ats_needs_improvement": ats_result["needs_improvement"],
        "ats_tips": ats_result["tips"]
    }


def calculate_ats_score(text: str, skills: list, education: list, experience: list, projects: list) -> dict:
    """
    Rule-based ATS scoring — adapted from a standard 6-category weighted model
    (Keyword Strength, Skills Match, Experience Relevance, Education Match,
    ATS Formatting, Resume Completeness). No job description required —
    keyword scoring here measures general resume-language quality
    (action verbs + technical terms) instead of JD-specific keyword overlap.
    This is a heuristic estimate, not an official or universal ATS formula.
    """
    text_lower = text.lower()
    word_count = len(text.split())

    has_email = bool(re.search(r'[\w.+-]+@[\w-]+\.[\w.-]+', text))
    has_phone = bool(re.search(r'\+?\d[\d\s-]{8,}\d', text))
    has_numbers = bool(re.search(r'\d+%|\d+\s*(percent|users|projects|hours|days|months|years)', text_lower))

    action_verbs = ["developed", "built", "created", "designed", "managed", "led",
                     "implemented", "analyzed", "improved", "optimized", "achieved",
                     "collaborated", "automated", "increased", "reduced", "delivered",
                     "engineered", "researched", "presented", "trained"]
    verbs_found = sum(1 for v in action_verbs if v in text_lower)

    # ---- 1. Keyword Strength — out of 35 ----
    # (Without a JD, we measure how strong/technical the resume's own language is:
    # action verb usage + density of recognized technical/skill terms.)
    verb_score = min(verbs_found / 8, 1) * 20
    tech_density_score = min(len(skills) / 10, 1) * 15
    keyword_score = round(verb_score + tech_density_score)

    # ---- 2. Skills Match — out of 25 ----
    skills_score = round(min(len(skills) / 10, 1) * 25)

    # ---- 3. Experience Relevance — out of 15 ----
    exp_present = min(len(experience) / 2, 1) * 8
    quantified_score = 7 if has_numbers else 0
    experience_score = round(exp_present + quantified_score)

    # ---- 4. Education Match — out of 10 ----
    education_score = 10 if education else 0

    # ---- 5. ATS Formatting — out of 10 ----
    sections_present = sum([bool(education), bool(skills), bool(experience), bool(projects)])
    length_ok = 150 <= word_count <= 900
    formatting_score = round((sections_present / 4) * 7 + (3 if length_ok else 1))
    formatting_score = min(formatting_score, 10)

    # ---- 6. Resume Completeness — out of 5 ----
    completeness_items = [has_email, has_phone, bool(skills), bool(experience) or bool(projects), bool(education)]
    completeness_score = round((sum(completeness_items) / len(completeness_items)) * 5)

    overall = keyword_score + skills_score + experience_score + education_score + formatting_score + completeness_score
    overall = min(overall, 100)

    if overall >= 80:
        verdict = "Great job! 🎯"
        verdict_desc = "Your resume meets most of the important ATS criteria."
    elif overall >= 60:
        verdict = "Good Match 👍"
        verdict_desc = "Your resume covers the basics but has room to improve."
    else:
        verdict = "Needs Work"
        verdict_desc = "Several key ATS elements are missing from your resume."

    # ---- Passed / Needs Improvement checks ----
    passed = []
    needs_improvement = []

    if sections_present >= 3:
        passed.append("Standard section headings detected (Skills, Experience, Education, etc.)")
    else:
        needs_improvement.append("Use clear standard section headings (Education, Skills, Experience, Projects)")

    if has_email and has_phone:
        passed.append("Contact information detected (email, phone)")
    else:
        needs_improvement.append("Add clear contact details (email and phone number)")

    if skills:
        passed.append(f"{len(skills)} skill(s) detected")
    else:
        needs_improvement.append("No recognizable skills detected — add a dedicated Skills section")

    if education:
        passed.append("Education section detected")
    else:
        needs_improvement.append("Education details not clearly detected")

    if has_numbers:
        passed.append("Quantified achievements found (numbers/percentages)")
    else:
        needs_improvement.append("Add measurable achievements (e.g. 'improved X by 20%')")

    if verbs_found >= 4:
        passed.append("Strong action verbs used")
    else:
        needs_improvement.append("Use more action verbs (developed, led, built, improved...)")

    tips = [
        "Use conventional section headings",
        "Avoid tables, text boxes, images, and multi-column layouts",
        "Use standard fonts (Arial, Calibri, Times New Roman)",
        "Keep a single-column layout",
        "Add specific tools and technologies relevant to your target role"
    ]

    return {
        "score": overall,
        "verdict": verdict,
        "verdict_desc": verdict_desc,
        "breakdown": [
            {"label": "Keyword Strength", "value": keyword_score, "max": 35},
            {"label": "Skills Match", "value": skills_score, "max": 25},
            {"label": "Experience Relevance", "value": experience_score, "max": 15},
            {"label": "Education Match", "value": education_score, "max": 10},
            {"label": "ATS Formatting", "value": formatting_score, "max": 10},
            {"label": "Resume Completeness", "value": completeness_score, "max": 5},
        ],
        "passed_checks": passed,
        "needs_improvement": needs_improvement,
        "tips": tips
    }


@app.get("/job-matches")
def get_job_matches(skills: str):
    """
    Fetches real, live job listings from Adzuna based on the resume's skills.
    'skills' is a comma-separated string, e.g. "Python,SQL,Machine Learning".
    """
    skills_list = [s.strip() for s in skills.split(",") if s.strip()]
    if not skills_list:
        raise HTTPException(status_code=400, detail="No skills provided to search jobs for.")

    # Use OR-based matching (any of these skills can appear) instead of
    # requiring ALL of them together — that was too restrictive and
    # returned zero results for most skill combinations.
    top_skills = skills_list[:6]

    url = "https://api.adzuna.com/v1/api/jobs/in/search/1"
    params = {
        "app_id": ADZUNA_APP_ID,
        "app_key": ADZUNA_APP_KEY,
        "results_per_page": 20,
        "what_or": " ".join(top_skills),
        "where": "India",
        "content-type": "application/json"
    }

    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Could not fetch live job listings: {str(e)}")

    results = data.get("results", [])

    # Fallback: if very few results with location filter, broaden the search
    if len(results) < 5:
        broader_params = dict(params)
        broader_params.pop("where", None)
        try:
            r2 = requests.get(url, params=broader_params, timeout=10)
            r2.raise_for_status()
            data2 = r2.json()
            if len(data2.get("results", [])) > len(results):
                data = data2
                results = data.get("results", [])
        except requests.exceptions.RequestException:
            pass  # keep whatever we already have
    if not results:
        return {"jobs": [], "total_found": 0}

    skills_lower = [s.lower() for s in skills_list]
    jobs = []

    for job in results:
        title = job.get("title", "Untitled Role")
        company = (job.get("company") or {}).get("display_name", "Unknown Company")
        location = (job.get("location") or {}).get("display_name", "India")
        description = job.get("description", "")
        apply_link = job.get("redirect_url", "")

        if not apply_link:
            continue  # skip any listing without a real, working apply link

        combined_text = (title + " " + description).lower()
        matched_skills = sum(1 for s in skills_lower if s in combined_text)

        # Base score reflects that the search query itself already filtered
        # for relevance; extra matched skills push the score higher.
        match_pct = min(60 + (matched_skills * 8), 97)

        jobs.append({
            "title": title,
            "company": company,
            "location": location,
            "match": match_pct,
            "link": apply_link
        })

    jobs.sort(key=lambda j: j["match"], reverse=True)

    return {
        "jobs": jobs[:12],
        "total_found": data.get("count", len(jobs))
    }


@app.get("/")
def health_check():
    return {"status": "Backend is running"}