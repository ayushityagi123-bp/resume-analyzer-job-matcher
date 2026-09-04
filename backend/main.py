from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pdfplumber
import io

app = FastAPI()

# Allow the frontend (index.html running on Live Server) to call this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # for development only
    allow_methods=["*"],
    allow_headers=["*"],
)

MAX_FILE_SIZE_MB = 10


@app.post("/upload-resume")
async def upload_resume(file: UploadFile = File(...)):

    # ---- 1. STRICT FILE TYPE CHECK ----
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

    # ---- 2. READ FILE INTO MEMORY ----
    contents = await file.read()

    # ---- 3. SIZE CHECK ----
    size_mb = len(contents) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=400,
            detail=f"File too large ({size_mb:.1f}MB). Max allowed is {MAX_FILE_SIZE_MB}MB."
        )

    # ---- 4. VERIFY IT'S ACTUALLY A READABLE PDF ----
    try:
        with pdfplumber.open(io.BytesIO(contents)) as pdf:
            if len(pdf.pages) == 0:
                raise HTTPException(status_code=400, detail="PDF has no pages.")

            full_text = ""
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    full_text += text + "\n"
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

    return {
        "filename": filename,
        "pages": len(pdf.pages) if 'pdf' in locals() else 0,
        "extracted_text": full_text.strip()
    }


@app.get("/")
def health_check():
    return {"status": "Backend is running"}