from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pdfplumber
import io
import re

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

MAX_FILE_SIZE_MB = 10

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
        "ats_breakdown": ats_result["breakdown"]
    }


def calculate_ats_score(text: str, skills: list, education: list, experience: list, projects: list) -> dict:
    """
    Rule-based ATS scoring — no external job description required.
    Scores four areas: Content Quality, Skills Match, Keyword Usage, Formatting.
    This is a heuristic estimate, not an official ATS algorithm.
    """
    word_count = len(text.split())

    # ---- 1. Content Quality (contact info + summary + ideal length) ----
    has_email = bool(re.search(r'[\w.+-]+@[\w-]+\.[\w.-]+', text))
    has_phone = bool(re.search(r'\+?\d[\d\s-]{8,}\d', text))
    length_score = 100 if 200 <= word_count <= 800 else (60 if word_count < 200 else 75)
    content_quality = round((
        (25 if has_email else 0) +
        (25 if has_phone else 0) +
        (length_score * 0.5)
    ))
    content_quality = min(content_quality, 100)

    # ---- 2. Skills Match (based on number of recognizable skills found) ----
    skills_match = min(round((len(skills) / 12) * 100), 100)

    # ---- 3. Keyword Usage (action verbs + quantifiable achievements) ----
    action_verbs = ["developed", "built", "created", "designed", "managed", "led",
                     "implemented", "analyzed", "improved", "optimized", "achieved",
                     "collaborated", "automated", "increased", "reduced", "delivered"]
    text_lower = text.lower()
    verbs_found = sum(1 for v in action_verbs if v in text_lower)
    has_numbers = bool(re.search(r'\d+%|\d+\s*(percent|users|projects|hours|days|months)', text_lower))
    keyword_usage = min(round((verbs_found / 6) * 80 + (20 if has_numbers else 0)), 100)

    # ---- 4. Formatting (structure completeness) ----
    sections_present = sum([
        bool(education), bool(skills), bool(experience), bool(projects)
    ])
    formatting = round((sections_present / 4) * 100)

    overall = round((content_quality + skills_match + keyword_usage + formatting) / 4)

    if overall >= 80:
        verdict = "Excellent Score! 🎯"
    elif overall >= 60:
        verdict = "Good Score! 👍"
    else:
        verdict = "Needs Improvement"

    return {
        "score": overall,
        "verdict": verdict,
        "breakdown": [
            {"label": "Content Quality", "value": content_quality},
            {"label": "Skills Match", "value": skills_match},
            {"label": "Keyword Usage", "value": keyword_usage},
            {"label": "Formatting", "value": formatting},
        ]
    }


@app.get("/")
def health_check():
    return {"status": "Backend is running"}