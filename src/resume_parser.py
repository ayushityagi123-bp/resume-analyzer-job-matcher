import fitz


def extract_text_from_pdf(pdf_file):
    pdf_document = fitz.open(
        stream=pdf_file.read(),
        filetype="pdf"
    )

    text = ""

    for page in pdf_document:
        text += page.get_text()

    pdf_document.close()

    return text


def extract_skills(text):
    skills_list = [
        "python",
        "java",
        "c++",
        "c",
        "sql",
        "mysql",
        "pandas",
        "numpy",
        "matplotlib",
        "machine learning",
        "deep learning",
        "react",
        "javascript",
        "html",
        "css",
        "git",
        "github",
        "power bi",
        "tableau",
        "excel"
    ]

    text = text.lower()

    detected_skills = []

    for skill in skills_list:
        if skill in text:
            detected_skills.append(skill)

    return detected_skills