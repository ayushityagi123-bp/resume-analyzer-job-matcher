from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pdfplumber
import io
import re
import requests
import os
import difflib
from dotenv import load_dotenv

load_dotenv()  # reads variables from the .env file into the environment

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
ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID")
ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY")

if not ADZUNA_APP_ID or not ADZUNA_APP_KEY:
    print("WARNING: Adzuna API credentials not found. Make sure backend/.env "
          "contains ADZUNA_APP_ID and ADZUNA_APP_KEY.")

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
    "Bootstrap", "Tailwind", "PHP", "C#", ".NET",
    # CS fundamentals / commonly listed on student resumes
    "Data Structures", "Algorithms", "DSA", "OOP", "Object Oriented Programming",
    "DBMS", "Operating Systems", "Computer Networks", "System Design",
    "Kotlin", "Swift", "Go", "Rust", "Ruby", "Redux", "Next.js", "GraphQL",
    "Jira", "Postman", "VS Code", "Shell Scripting", "Bash", "Jupyter",
    "LangChain", "OpenAI API", "Hugging Face", "Selenium", "JUnit",
    "CI/CD", "Agile", "Scrum", "Web Scraping", "Data Cleaning", "A/B Testing",
]

EDUCATION_KEYWORDS = [
    "B.Tech", "B Tech", "BTech", "Bachelor", "B.E", "BE ", "M.Tech", "MTech",
    "Master", "M.E", "MBA", "BCA", "MCA", "BSc", "MSc", "B.Sc", "M.Sc",
    "Diploma", "Ph.D", "PhD", "Intermediate", "High School", "12th", "10th",
    # Broader schooling/qualification wording (many Indian resumes use these
    # instead of a degree name for 10th/12th entries)
    "Senior Secondary", "Secondary", "CBSE", "ICSE", "SSC", "HSC",
    "Matriculation", "State Board", "Class 10", "Class 12", "Class X", "Class XII",
]

# Institute-name signals — kept broad and regional (e.g. "Vidyalaya"/"Vidhyalaya"
# for schools) so 10th/12th school entries are recognized just as reliably as
# college/university entries, rather than relying only on a degree keyword.
EDUCATION_INSTITUTE_KEYWORDS = [
    "University", "College", "Institute", "School",
    "Vidyalaya", "Vidhyalaya", "Academy", "Polytechnic",
]

SECTION_HEADERS = {
    "EDUCATION": ["EDUCATION", "ACADEMIC BACKGROUND", "ACADEMIC QUALIFICATION", "QUALIFICATION"],
    "SKILLS": ["SKILLS", "TECHNICAL SKILLS", "KEY SKILLS", "CORE SKILLS", "SKILL SET",
               "TECHNOLOGIES", "TECHNOLOGY", "TECH STACK", "TOOLS AND TECHNOLOGIES",
               "TOOLS & TECHNOLOGIES", "LANGUAGES AND TOOLS", "LANGUAGES & TOOLS",
               "TECHNICAL PROFICIENCY", "AREAS OF EXPERTISE"],
    "EXPERIENCE": ["EXPERIENCE", "WORK EXPERIENCE", "INTERNSHIP", "INTERNSHIPS",
                   "PROFESSIONAL EXPERIENCE", "WORK HISTORY", "EMPLOYMENT HISTORY"],
    "PROJECTS": ["PROJECTS", "TECHNICAL PROJECTS", "ACADEMIC PROJECTS", "PERSONAL PROJECTS",
                 "KEY PROJECTS", "MAJOR PROJECTS", "PROJECT EXPERIENCE"],
    "SUMMARY": ["SUMMARY", "PROFESSIONAL SUMMARY", "CAREER OBJECTIVE", "OBJECTIVE", "PROFILE"],
}


def normalize_extracted_text(text: str) -> str:
    """
    Fixes common PDF-extraction artifacts where PDF font kerning causes
    words to split apart with an extra space (e.g. "Java Script" instead
    of "JavaScript"). Without this, skill detection can misfire — treating
    "Java" as a separate skill when the resume only ever said "JavaScript".
    """
    fixes = [
        (r'\bJava\s+Script\b', 'JavaScript'),
        (r'\bType\s+Script\b', 'TypeScript'),
        (r'\bNode\s*\.\s*js\b', 'Node.js'),
        (r'\bScikit\s*-?\s*learn\b', 'Scikit-learn'),
        (r'\bPower\s+BI\b', 'Power BI'),
        (r'\bC\s*\+\s*\+', 'C++'),
    ]
    for pattern, replacement in fixes:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return text


def _normalize_header_line(line: str) -> str:
    """
    Strips decorative characters that resumes commonly wrap headers in
    (e.g. "=== SKILLS ===", "** Projects **", "--- Education ---", ":"),
    so the underlying keyword can be compared cleanly. This makes header
    detection independent of *how* the heading is decorated/styled.
    """
    cleaned = re.sub(r'[=\-_*~#•·|>]+', ' ', line)
    cleaned = re.sub(r'\s+', ' ', cleaned)
    return cleaned.strip()


def _looks_like_header_shape(line: str) -> bool:
    """
    Structural check independent of any specific keyword or its length:
    a section heading is short (a handful of words), doesn't end with a
    sentence-ending period, and isn't a long descriptive sentence. This
    replaces the old "line length <= keyword length + 20" rule, which
    unfairly penalized short keywords like "SKILLS" while being lenient
    for long ones — the shape check now applies the same way regardless
    of which keyword eventually matches.
    """
    stripped = line.strip()
    if not stripped:
        return False
    word_count = len(stripped.split())
    if word_count == 0 or word_count > 6:
        return False
    if stripped.endswith("."):
        return False
    return True


def _best_section_match(line: str) -> str | None:
    """
    Matches a (already shape-checked) line against SECTION_HEADERS keywords
    using both containment and fuzzy similarity, so headers are detected
    regardless of exact wording, minor typos, or decorative formatting —
    not just the literal keyword list.

    A containment match ("PROJECTS" found inside the line) is only trusted
    when the keyword makes up MOST of the line — i.e. at most a couple of
    extra words remain after removing it (covers cases like "TECHNICAL
    PROJECTS" or "MY PROJECTS"). Without this guard, a keyword that happens
    to appear inside unrelated text gets misread as a header — e.g. the
    word "Technology" inside the institute name "XYZ Institute of
    Technology" would otherwise be misdetected as a "SKILLS" section header
    (since "TECHNOLOGY" is a Skills synonym), silently swallowing whatever
    section came after it.
    """
    normalized = _normalize_header_line(line)
    upper = normalized.upper()
    if not upper:
        return None

    best_section = None
    best_score = 0.0

    for section_name, keywords in SECTION_HEADERS.items():
        for kw in keywords:
            score = 0.0
            if kw in upper:
                remainder = upper.replace(kw, "", 1).split()
                if len(remainder) <= 2:
                    # Keyword makes up nearly the whole line — trustworthy header.
                    score = 1.0 + (len(kw) / 100.0)
                # else: keyword is just a fragment of a longer, unrelated
                # line (e.g. an institute/company name) — don't trust it as
                # containment; fall through to the fuzzy check below instead.
            if score == 0.0:
                score = difflib.SequenceMatcher(None, upper, kw).ratio()

            if score > best_score:
                best_score = score
                best_section = section_name

    # 1.0+ = trusted containment. Below that, require a close fuzzy match
    # (handles typos / near-variants) so we don't misfire on unrelated text.
    if best_score >= 0.78:
        return best_section
    return None


def split_into_sections(text: str) -> dict:
    """
    Splits resume text into sections based on header keywords, wherever
    in the document they appear and however they're worded or styled.
    Detection is a two-step process: (1) does this line have the *shape*
    of a heading (short, not a sentence)? (2) does it match — exactly,
    by containment, or fuzzily — one of the known section keywords?
    """
    lines = text.split("\n")
    sections = {key: [] for key in SECTION_HEADERS}
    sections["OTHER"] = []
    current = "OTHER"

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue

        matched = None
        if _looks_like_header_shape(line):
            matched = _best_section_match(line)

        if matched:
            current = matched
        else:
            sections[current].append(line)

    return sections


def extract_skills(full_text: str, skills_section_text: str = "") -> list:
    """
    Searches for known skills in the resume.
    Short, ambiguous names (like "R" or "C") are only matched inside the
    dedicated Skills section — searching the whole document for a single
    letter causes false positives (e.g. "R" matching inside "R&D").
    Longer, unambiguous skill names are searched across the full text.
    """
    full_lower = full_text.lower()
    skills_lower = skills_section_text.lower()

    found = []
    for skill in SKILLS_DB:
        pattern = r'\b' + re.escape(skill.lower()) + r'\b'
        search_space = skills_lower if len(skill) <= 2 else full_lower
        if re.search(pattern, search_space):
            found.append(skill)
    return sorted(set(found))


def extract_education(section_lines: list) -> list:
    """
    Groups education lines block-by-block, one block per institution —
    rather than filtering lines independently — so a 10th/12th school entry
    (which usually has no "degree" keyword, just "Senior Secondary"/CBSE
    wording) is captured just as reliably as a B.Tech/university entry.

    A new block starts whenever a line names an institute (broad keyword
    list covering schools, colleges, universities, regional naming like
    "Vidyalaya"). Every institute name is treated as a new entry even if
    the exact same school name repeats for both 10th and 12th, since it's
    a genuinely separate qualification each time.
    """
    if not section_lines:
        return []

    def is_institute_line(line: str) -> bool:
        return any(kw.lower() in line.lower() for kw in EDUCATION_INSTITUTE_KEYWORDS)

    def is_relevant_detail(line: str) -> bool:
        has_keyword = any(k.lower() in line.lower() for k in EDUCATION_KEYWORDS)
        has_year = bool(re.search(r'\b(19|20)\d{2}\b', line))
        has_score = bool(re.search(r'\bcgpa\b', line, re.IGNORECASE) or re.search(r'\d{1,3}(\.\d+)?\s*%', line))
        return has_keyword or has_year or has_score

    blocks = []
    current = []

    for line in section_lines:
        if is_institute_line(line):
            if current:
                blocks.append(current)
            current = [line]
        elif current:
            if is_relevant_detail(line):
                current.append(line)
            # non-relevant lines inside a block (rare filler text) are skipped
        elif is_relevant_detail(line):
            # A degree/score line appearing with no institute line before it
            blocks.append([line])

    if current:
        blocks.append(current)

    # Each block becomes its own set of result lines (institute + its details)
    results = []
    for block in blocks:
        results.extend(block)

    return results[:9]  # allow room for multiple qualifications (10th/12th/degree)


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


_PROJECT_DATE_PATTERN = re.compile(
    r'((?:Jan\.?|Feb\.?|Mar\.?|Apr\.?|May|Jun\.?|Jul\.?|Aug\.?|Sep\.?|Oct\.?|Nov\.?|Dec\.?)?\s*'
    r'(19|20)\d{2}\s*(–|-|to)?\s*(present|(19|20)\d{2})?)\s*$', re.IGNORECASE
)
_PROJECT_BULLET_PATTERN = re.compile(r'^\s*([•*\-–—▪●]|\d+[\.\)])\s+')


def _is_probable_project_title(line: str) -> bool:
    """
    A project title line is short and mostly Capitalized/Title Case.
    This is a *shape* signal, independent of whether a date is present —
    so projects without any date still get split correctly.
    """
    words = line.split()
    if not words or len(words) > 10:
        return False
    capitalized = sum(1 for w in words if w[:1].isupper())
    return (capitalized / len(words)) >= 0.6


def extract_projects(section_lines: list) -> list:
    """
    Groups project section lines into individual projects using multiple
    signals, not just a trailing year/date:
      1. A bullet or numbered prefix ("•", "-", "1.") starts a new project.
      2. A short, mostly Title-Case line starts a new project (works even
         when there's no date at all).
      3. A trailing year/date (e.g. "...Engine 2026", "Mar. 2026 – Present")
         is still treated as a strong signal when present, and is stripped
         from the stored title.
    Any one of these firing is enough — the date is now a bonus signal,
    not a requirement, so undated project titles are no longer merged
    into the previous project's description.
    """
    results = []
    current = None

    for raw_line in section_lines:
        line = raw_line.strip()
        if not line:
            continue

        has_date_signal = bool(_PROJECT_DATE_PATTERN.search(line)) and len(line) < 110
        has_bullet_signal = bool(_PROJECT_BULLET_PATTERN.match(line))
        has_title_shape = (not has_bullet_signal) and _is_probable_project_title(line) and len(line) < 110

        # A title-shaped line only counts as the start of a NEW project if
        # we're not still inside the "header block" (title + tech-stack
        # subtitle) of the current one. Real resumes often list a tech-stack
        # line right under the project title (e.g. "React, Node.js, Leaflet
        # API") which is ALSO short and Title-Case — without this check it
        # gets misread as its own project, leaving the real title with an
        # empty description. So: if current has no description yet, treat
        # this line as a continuation (subtitle/tech-stack), not a new item.
        # Bullets and explicit dates are unambiguous, so they always split.
        if has_date_signal or has_bullet_signal:
            starts_new_project = True
        elif has_title_shape:
            starts_new_project = (current is None) or (current["desc"].strip() != "")
        else:
            starts_new_project = False

        if starts_new_project:
            if current:
                current["desc"] = current["desc"][:150]
                results.append(current)

            name = _PROJECT_DATE_PATTERN.sub("", line).strip(" -–|:")
            name = _PROJECT_BULLET_PATTERN.sub("", name).strip(" -–|:")
            current = {"name": name or line, "desc": ""}
        elif current:
            current["desc"] += (" " if current["desc"] else "") + line
        # lines before the first detected title are ignored (usually noise)

    if current:
        current["desc"] = current["desc"][:150]
        results.append(current)

    return results[:6]


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

    full_text = normalize_extracted_text(full_text)

    # ---- Parse structured data from the extracted text ----
    sections = split_into_sections(full_text)

    skills_section_text = "\n".join(sections["SKILLS"])
    skills = extract_skills(full_text, skills_section_text)
    education = extract_education(sections["EDUCATION"] or sections["OTHER"])
    experience = extract_experience(sections["EXPERIENCE"])
    projects = extract_projects(sections["PROJECTS"])

    ats_result = calculate_ats_score(full_text, skills, education, experience, projects, sections)

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


def calculate_ats_score(text: str, skills: list, education: list, experience: list,
                         projects: list, sections: dict) -> dict:
    """
    Rule-based ATS scoring — adapted from a standard 6-category weighted model
    (Keyword Strength, Skills Match, Experience Relevance, Education Match,
    ATS Formatting, Resume Completeness). No job description required —
    keyword scoring here measures general resume-language quality
    (action verbs + technical terms) instead of JD-specific keyword overlap.

    This checks quantified-achievement DENSITY (what fraction of experience/
    project bullets actually contain a measurable number) rather than just
    "does a number appear anywhere" — real ATS/resume-checker tools
    (Enhancv, Zety, Jobscan) flag exactly this ("Quantifying Impact") as a
    common weak point, and a one-off number anywhere was scoring resumes
    too generously.

    This is a heuristic estimate, not an official or universal ATS formula.
    """
    text_lower = text.lower()
    word_count = len(text.split())

    has_email = bool(re.search(r'[\w.+-]+@[\w-]+\.[\w.-]+', text))
    has_phone = bool(re.search(r'\+?\d[\d\s-]{8,}\d', text))

    number_pattern = re.compile(r'\d+(\.\d+)?\s*%|\d+\s*(percent|users|projects|hours|days|months|years|x\b)', re.IGNORECASE)

    action_verbs = ["developed", "built", "created", "designed", "managed", "led",
                     "implemented", "analyzed", "improved", "optimized", "achieved",
                     "collaborated", "automated", "increased", "reduced", "delivered",
                     "engineered", "researched", "presented", "trained"]
    verbs_found = sum(1 for v in action_verbs if v in text_lower)

    # ---- Quantified achievement DENSITY across experience + project bullets ----
    bullet_lines = (sections.get("EXPERIENCE", []) or []) + (sections.get("PROJECTS", []) or [])
    # Only count lines that look like actual bullet content, not short titles/dates
    content_lines = [l for l in bullet_lines if len(l) > 25]
    quantified_lines = [l for l in content_lines if number_pattern.search(l)]
    quantified_ratio = (len(quantified_lines) / len(content_lines)) if content_lines else 0

    has_summary = bool(sections.get("SUMMARY"))

    # ---- 1. Keyword Strength — out of 35 ----
    verb_score = min(verbs_found / 8, 1) * 15
    tech_density_score = min(len(skills) / 10, 1) * 10
    quantified_language_score = quantified_ratio * 10
    keyword_score = round(verb_score + tech_density_score + quantified_language_score)

    # ---- 2. Skills Match — out of 25 ----
    skills_score = round(min(len(skills) / 10, 1) * 25)

    # ---- 3. Experience Relevance — out of 15 ----
    exp_present = 5 if (experience or projects) else 0
    quantified_score = round(quantified_ratio * 10)
    experience_score = exp_present + quantified_score

    # ---- 4. Education Match — out of 10 ----
    education_score = 10 if education else 0

    # ---- 5. ATS Formatting — out of 10 ----
    sections_present = sum([bool(education), bool(skills), bool(experience), bool(projects)])
    length_ok = 150 <= word_count <= 900
    formatting_score = round((sections_present / 4) * 5 + (2 if length_ok else 0) + (3 if has_summary else 0))
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

    if quantified_ratio >= 0.5:
        passed.append("Most bullet points include measurable outcomes")
    elif quantified_ratio > 0:
        needs_improvement.append(f"Only {round(quantified_ratio*100)}% of your bullet points have measurable numbers — add metrics to more of them")
    else:
        needs_improvement.append("Add measurable achievements to your bullets (e.g. 'improved accuracy by 20%')")

    if verbs_found >= 4:
        passed.append("Strong action verbs used")
    else:
        needs_improvement.append("Use more action verbs (developed, led, built, improved...)")

    if has_summary:
        passed.append("Professional summary/objective section found")
    else:
        needs_improvement.append("Add a short professional summary at the top framing your target role")

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


def _fetch_adzuna(what_or_terms: str, use_location: bool = True) -> dict:
    url = "https://api.adzuna.com/v1/api/jobs/in/search/1"
    params = {
        "app_id": ADZUNA_APP_ID,
        "app_key": ADZUNA_APP_KEY,
        "results_per_page": 10,
        "what_or": what_or_terms,
        "content-type": "application/json"
    }
    if use_location:
        params["where"] = "India"
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    return r.json()


@app.get("/job-matches")
def get_job_matches(skills: str, role: str = ""):
    """
    Fetches real, live job listings from Adzuna based on the resume's skills
    AND a guessed target role (from the most recent experience title).
    'skills' is comma-separated, e.g. "Python,SQL,Machine Learning".
    'role' is a free-text guess like "Data Analyst" — used to make sure the
    person's actual best-fit role shows up, not just any skill overlap.
    """
    skills_list = [s.strip() for s in skills.split(",") if s.strip()]
    if not skills_list:
        raise HTTPException(status_code=400, detail="No skills provided to search jobs for.")

    top_skills = skills_list[:8]
    skill_groups = [top_skills[i:i + 2] for i in range(0, len(top_skills), 2)] or [top_skills]

    all_results = []
    seen_job_keys = set()
    total_found_estimate = 0

    # ---- Search 1: the guessed target role itself (title-focused) ----
    # This is what guarantees a role like "Data Analyst" shows up when the
    # resume's own experience says "Data Analyst Intern", instead of only
    # surfacing jobs that happen to share a skill keyword.
    role_clean = re.sub(r'\b(intern|trainee|fresher|associate)\b', '', role, flags=re.IGNORECASE).strip()
    if role_clean:
        try:
            data = _fetch_adzuna(role_clean, use_location=True)
            role_results = data.get("results", [])
            if len(role_results) < 3:
                data = _fetch_adzuna(role_clean, use_location=False)
                role_results = data.get("results", [])
            total_found_estimate = max(total_found_estimate, data.get("count", 0))
            for job in role_results:
                key = job.get("id") or job.get("redirect_url")
                if key and key not in seen_job_keys:
                    seen_job_keys.add(key)
                    all_results.append(job)
        except requests.exceptions.RequestException:
            pass

    # ---- Search 2+: skill-pair groups (adds variety/breadth) ----
    for group in skill_groups:
        query = " ".join(group)
        try:
            data = _fetch_adzuna(query, use_location=True)
            group_results = data.get("results", [])
            if len(group_results) < 3:
                data = _fetch_adzuna(query, use_location=False)
                group_results = data.get("results", [])
            total_found_estimate = max(total_found_estimate, data.get("count", 0))
        except requests.exceptions.RequestException:
            continue

        for job in group_results:
            key = job.get("id") or job.get("redirect_url")
            if key and key not in seen_job_keys:
                seen_job_keys.add(key)
                all_results.append(job)

    if not all_results:
        return {"jobs": [], "total_found": 0, "missing_skills": []}

    skills_lower = [s.lower() for s in skills_list]
    role_words = [w for w in re.findall(r'\w+', role_clean.lower()) if len(w) > 2]
    jobs = []

    for job in all_results:
        title = job.get("title", "Untitled Role")
        company = (job.get("company") or {}).get("display_name", "Unknown Company")
        location = (job.get("location") or {}).get("display_name", "India")
        description = job.get("description", "")
        apply_link = job.get("redirect_url", "")

        if not apply_link:
            continue

        combined_text = (title + " " + description).lower()
        matched_skills = sum(1 for s in skills_lower if s in combined_text)

        # Cap the denominator so someone with many skills isn't unfairly
        # diluted — matching most of your CORE skills should still score high.
        effective_total = min(len(skills_lower), 8) if skills_lower else 1
        coverage_ratio = min(matched_skills / effective_total, 1)

        # Bonus if the job title itself reflects the person's actual target
        # role (e.g. resume says "Data Analyst" and title contains it too).
        title_lower = title.lower()
        role_hits = sum(1 for w in role_words if w in title_lower)
        title_bonus = min(role_hits * 10, 20)

        match_pct = round(55 + coverage_ratio * 25 + title_bonus)
        match_pct = min(match_pct, 97)

        jobs.append({
            "title": title,
            "company": company,
            "location": location,
            "match": match_pct,
            "link": apply_link,
            "_description": description
        })

    jobs.sort(key=lambda j: j["match"], reverse=True)

    # ---- Diversify: round-robin across distinct job titles instead of ----
    # ---- taking many of the same title back-to-back                  ----
    from collections import defaultdict
    grouped = defaultdict(list)
    title_order = []
    for job in jobs:
        norm_title = job["title"].strip().lower()
        if norm_title not in grouped:
            title_order.append(norm_title)
        grouped[norm_title].append(job)

    final_jobs = []
    round_index = 0
    while len(final_jobs) < 12 and any(round_index < len(grouped[t]) for t in title_order):
        for t in title_order:
            if round_index < len(grouped[t]):
                final_jobs.append(grouped[t][round_index])
                if len(final_jobs) >= 12:
                    break
        round_index += 1

    # ---- Missing Skills: scan descriptions for skills not already known ----
    all_job_text = " ".join(j["_description"] for j in final_jobs).lower()
    skill_frequency = {}
    for skill in SKILLS_DB:
        if skill.lower() in skills_lower:
            continue  # already have this skill — not "missing"
        pattern = r'\b' + re.escape(skill.lower()) + r'\b'
        count = len(re.findall(pattern, all_job_text))
        if count > 0:
            skill_frequency[skill] = count

    missing_skills = sorted(skill_frequency, key=skill_frequency.get, reverse=True)[:6]

    # Strip the internal description field before sending the response
    for j in final_jobs:
        j.pop("_description", None)

    return {
        "jobs": final_jobs,
        "total_found": total_found_estimate,
        "missing_skills": missing_skills
    }


@app.get("/")
def health_check():
    return {"status": "Backend is running"}