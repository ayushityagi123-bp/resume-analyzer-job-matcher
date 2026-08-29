import streamlit as st
import pymupdf


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Resume Analyzer & Job Matcher",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# =========================================================
# SESSION STATE
# =========================================================

if "slide" not in st.session_state:
    st.session_state.slide = 1

if "resume_file" not in st.session_state:
    st.session_state.resume_file = None

if "resume_text" not in st.session_state:
    st.session_state.resume_text = ""


# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown(
    """
    <style>

    /* ---------- MAIN BACKGROUND ---------- */

    .stApp {
        background:
            radial-gradient(
                circle at 85% 15%,
                rgba(91, 45, 180, 0.30),
                transparent 35%
            ),
            radial-gradient(
                circle at 10% 85%,
                rgba(0, 110, 255, 0.18),
                transparent 35%
            ),
            linear-gradient(
                135deg,
                #030617 0%,
                #080b20 45%,
                #170b3d 100%
            );
        color: white;
    }


    /* ---------- REMOVE DEFAULT PADDING ---------- */

    .block-container {
        max-width: 1050px;
        padding-top: 30px;
        padding-bottom: 30px;
    }


    /* ---------- TITLE ---------- */

    .main-title {
        font-size: 48px;
        font-weight: 800;
        line-height: 1.1;
        margin-bottom: 10px;
        color: white;
    }

    .gradient-title {
        background: linear-gradient(
            90deg,
            #a855f7,
            #38bdf8
        );
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }


    .subtitle {
        color: #aeb9d8;
        font-size: 17px;
        line-height: 1.7;
        margin-bottom: 22px;
        max-width: 760px;
    }


    /* ---------- BADGES ---------- */

    .badge-row {
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
        margin-bottom: 35px;
    }

    .badge {
        border: 1px solid rgba(139, 92, 246, 0.7);
        background: rgba(92, 48, 180, 0.12);
        border-radius: 25px;
        padding: 8px 14px;
        color: #e7ddff;
        font-size: 13px;
    }


    /* ---------- CARDS ---------- */

    .card {
        background: rgba(16, 19, 42, 0.82);
        border: 1px solid rgba(139, 92, 246, 0.55);
        border-radius: 20px;
        padding: 30px;
        min-height: 310px;
        box-shadow:
            0 15px 45px rgba(0, 0, 0, 0.25);
    }


    .upload-icon {
        width: 58px;
        height: 58px;
        border-radius: 16px;
        margin: 0 auto 20px auto;

        display: flex;
        align-items: center;
        justify-content: center;

        font-size: 30px;
        background: linear-gradient(
            135deg,
            #7c3aed,
            #2563eb
        );

        box-shadow:
            0 0 30px rgba(99, 102, 241, 0.45);
    }


    .card-title {
        text-align: center;
        font-size: 23px;
        font-weight: 750;
        color: white;
        margin-bottom: 12px;
    }


    .card-title span {
        background: linear-gradient(
            90deg,
            #a855f7,
            #38bdf8
        );
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }


    .card-text {
        text-align: center;
        color: #9ca9ca;
        line-height: 1.6;
        font-size: 14px;
        margin-bottom: 25px;
    }


    /* ---------- INFO PILLS ---------- */

    .info-row {
        display: flex;
        justify-content: center;
        gap: 8px;
        flex-wrap: wrap;
    }

    .info-pill {
        background: rgba(55, 61, 88, 0.65);
        border: 1px solid rgba(130, 140, 180, 0.2);
        border-radius: 20px;
        padding: 7px 12px;
        color: #d8def1;
        font-size: 12px;
    }


    /* ---------- ANALYSIS CARD ---------- */

    .analysis-icon {
        width: 58px;
        height: 58px;
        border-radius: 16px;

        margin: 0 auto 20px auto;

        display: flex;
        align-items: center;
        justify-content: center;

        background: #f4f1ff;
        color: #5531c7;
        font-size: 30px;

        box-shadow:
            0 0 30px rgba(168, 85, 247, 0.25);
    }


    .analysis-title {
        text-align: center;
        color: white;
        font-size: 23px;
        font-weight: 750;
        margin-bottom: 5px;
    }


    .analysis-subtitle {
        text-align: center;
        color: #929dc0;
        font-size: 13px;
        margin-bottom: 25px;
    }


    .check-item {
        padding: 12px 0;
        border-bottom: 1px solid rgba(120, 130, 170, 0.15);
        color: #d8def1;
        font-size: 14px;
    }

    .check {
        color: #b14cff;
        font-weight: bold;
        margin-right: 8px;
    }


    /* ---------- SECTION TITLE ---------- */

    .section-title {
        color: white;
        font-size: 14px;
        font-weight: 700;
        margin-top: 20px;
        margin-bottom: 10px;
    }


    /* ---------- FEATURES ---------- */

    .feature-card {
        background: rgba(18, 21, 43, 0.85);
        border: 1px solid rgba(115, 125, 170, 0.25);
        border-radius: 15px;
        padding: 20px;
        min-height: 145px;
    }

    .feature-icon {
        font-size: 24px;
        margin-bottom: 8px;
    }

    .feature-name {
        color: white;
        font-weight: 700;
        font-size: 14px;
        margin-bottom: 8px;
    }

    .feature-desc {
        color: #8e9abb;
        font-size: 12px;
        line-height: 1.5;
    }


    /* ---------- PROGRESS ---------- */

    .progress-label {
        text-align: center;
        color: #7884a8;
        font-size: 11px;
        margin-top: 12px;
    }


    /* ---------- FOOTER ---------- */

    .footer {
        text-align: center;
        color: #626d91;
        font-size: 11px;
        margin-top: 35px;
        padding-top: 20px;
        border-top: 1px solid rgba(120, 130, 170, 0.15);
    }


    /* ---------- BUTTONS ---------- */

    .stButton > button {
        width: 100%;
        border-radius: 9px;
        border: none;
        height: 42px;
        font-weight: 600;
        color: white;
        background: linear-gradient(
            90deg,
            #7c3aed,
            #2563eb
        );
    }

    .stButton > button:hover {
        border: none;
        color: white;
        box-shadow:
            0 0 20px rgba(99, 102, 241, 0.35);
    }


    /* ---------- FILE UPLOADER ---------- */

    [data-testid="stFileUploader"] {
        background: rgba(8, 11, 30, 0.65);
        border: 1px dashed rgba(139, 92, 246, 0.7);
        border-radius: 15px;
        padding: 10px;
    }


    /* ---------- TEXT AREA ---------- */

    [data-testid="stTextArea"] textarea {
        background: rgba(12, 15, 35, 0.9);
        color: #e7ebff;
        border: 1px solid rgba(139, 92, 246, 0.45);
        border-radius: 12px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# FUNCTION: EXTRACT PDF TEXT
# =========================================================

def extract_pdf_text(uploaded_file):

    try:
        pdf_bytes = uploaded_file.read()

        document = pymupdf.open(
            stream=pdf_bytes,
            filetype="pdf"
        )

        text = ""

        for page in document:
            text += page.get_text()

        document.close()

        return text.strip()

    except Exception as error:
        st.error(f"Could not extract PDF text: {error}")
        return ""


# =========================================================
# SLIDE 1
# =========================================================

def slide_one():

    # ---------- HEADER ----------

    st.markdown(
        """
        <div class="main-title">
            Resume <span class="gradient-title">Analyzer</span>
            & Job <span class="gradient-title">Matcher</span> 🚀
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="subtitle">
            Analyze your resume, check ATS score, discover matching
            opportunities and improve your career profile.
        </div>
        """,
        unsafe_allow_html=True
    )


    # ---------- BADGES ----------

    st.markdown(
        """
        <div class="badge-row">
            <div class="badge">✦ Smart Analysis</div>
            <div class="badge">⚡ ATS Score</div>
            <div class="badge">🔎 Job Matching</div>
            <div class="badge">✦ Skill Improvement</div>
        </div>
        """,
        unsafe_allow_html=True
    )


    # ---------- TWO MAIN CARDS ----------

    left, right = st.columns(2, gap="large")


    # =====================================================
    # LEFT CARD
    # =====================================================

    with left:

        st.markdown(
            """
            <div class="card">

                <div class="upload-icon">
                    ↑
                </div>

                <div class="card-title">
                    Upload Your <span>Resume</span>
                </div>

                <div class="card-text">
                    Upload your resume in PDF format and let our
                    analyzer extract the information that matters
                    for your career.
                </div>

                <div class="info-row">

                    <div class="info-pill">
                        📄 PDF Only
                    </div>

                    <div class="info-pill">
                        🔒 Secure Processing
                    </div>

                    <div class="info-pill">
                        ⚡ Fast Analysis
                    </div>

                </div>

            </div>
            """,
            unsafe_allow_html=True
        )


    # =====================================================
    # RIGHT CARD
    # =====================================================

    with right:

        st.markdown(
            """
            <div class="card">

                <div class="analysis-icon">
                    📄
                </div>

                <div class="analysis-title">
                    Smart Resume Analysis
                </div>

                <div class="analysis-subtitle">
                    Analyze • Match • Improve
                </div>

                <div class="check-item">
                    <span class="check">✓</span>
                    Resume Content Detection
                </div>

                <div class="check-item">
                    <span class="check">✓</span>
                    Technical Skills Extraction
                </div>

                <div class="check-item">
                    <span class="check">✓</span>
                    ATS Compatibility Check
                </div>

                <div class="check-item">
                    <span class="check">✓</span>
                    Career Profile Insights
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )


    # =====================================================
    # UPLOAD
    # =====================================================

    st.markdown(
        '<div class="section-title">Choose your Resume PDF</div>',
        unsafe_allow_html=True
    )

    uploaded_file = st.file_uploader(
        "Upload your resume",
        type=["pdf"],
        label_visibility="collapsed"
    )


    # =====================================================
    # AFTER UPLOAD
    # =====================================================

    if uploaded_file is not None:

        st.session_state.resume_file = uploaded_file

        st.success(
            f"✓ {uploaded_file.name} uploaded successfully."
        )


    # =====================================================
    # NEXT BUTTON
    # =====================================================

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:

        if st.button(
            "Next →",
            key="slide1_next"
        ):

            if st.session_state.resume_file is None:

                st.warning(
                    "Please upload your resume PDF first."
                )

            else:

                # Extract PDF text
                extracted = extract_pdf_text(
                    st.session_state.resume_file
                )

                st.session_state.resume_text = extracted

                # MOVE TO SLIDE 2
                st.session_state.slide = 2

                st.rerun()


    # =====================================================
    # PROGRESS
    # =====================================================

    st.markdown(
        """
        <div class="progress-label">
            Slide 1 of 6
        </div>
        """,
        unsafe_allow_html=True
    )

    st.progress(1 / 6)


    # =====================================================
    # KEY FEATURES
    # =====================================================

    st.markdown(
        '<div class="section-title">✨ KEY FEATURES</div>',
        unsafe_allow_html=True
    )

    f1, f2, f3, f4 = st.columns(4, gap="small")


    with f1:
        st.markdown(
            """
            <div class="feature-card">

                <div class="feature-icon">🧠</div>

                <div class="feature-name">
                    Smart Analysis
                </div>

                <div class="feature-desc">
                    AI-powered resume insights
                    and content analysis.
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )


    with f2:
        st.markdown(
            """
            <div class="feature-card">

                <div class="feature-icon">📊</div>

                <div class="feature-name">
                    ATS Score
                </div>

                <div class="feature-desc">
                    Check your resume strength
                    for ATS systems.
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )


    with f3:
        st.markdown(
            """
            <div class="feature-card">

                <div class="feature-icon">🔎</div>

                <div class="feature-name">
                    Job Matching
                </div>

                <div class="feature-desc">
                    Find suitable opportunities
                    based on your profile.
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )


    with f4:
        st.markdown(
            """
            <div class="feature-card">

                <div class="feature-icon">💡</div>

                <div class="feature-name">
                    Skill Improvement
                </div>

                <div class="feature-desc">
                    Get personalized suggestions
                    to improve your profile.
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )


    # =====================================================
    # FOOTER
    # =====================================================

    st.markdown(
        """
        <div class="footer">
            © 2026 Resume Analyzer & Job Matcher •
            Your Success, Our Mission 🚀
        </div>
        """,
        unsafe_allow_html=True
    )


# =========================================================
# SLIDE 2
# =========================================================

def slide_two():

    # ---------- HEADER ----------

    st.markdown(
        """
        <div class="main-title">
            <span class="gradient-title">
                Extracted Resume
            </span> Text
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="subtitle">
            Here is the text extracted from your uploaded resume.
            Review the extracted information before moving to
            resume analysis.
        </div>
        """,
        unsafe_allow_html=True
    )


    # ---------- RESUME NAME ----------

    if st.session_state.resume_file:

        st.markdown(
            f"""
            <div class="section-title">
                📄 {st.session_state.resume_file.name}
            </div>
            """,
            unsafe_allow_html=True
        )


    # ---------- EXTRACTED TEXT ----------

    if st.session_state.resume_text:

        st.text_area(
            "Extracted Resume Text",
            value=st.session_state.resume_text,
            height=500
        )

    else:

        st.warning(
            "No resume text was extracted."
        )


    # ---------- NAVIGATION ----------

    st.markdown("<br>", unsafe_allow_html=True)

    back, space, next_col = st.columns([1, 2, 1])


    with back:

        if st.button(
            "← Back",
            key="slide2_back"
        ):

            st.session_state.slide = 1
            st.rerun()


    with next_col:

        if st.button(
            "Next →",
            key="slide2_next"
        ):

            st.session_state.slide = 3
            st.rerun()


    # ---------- PROGRESS ----------

    st.markdown(
        """
        <div class="progress-label">
            Slide 2 of 6
        </div>
        """,
        unsafe_allow_html=True
    )

    st.progress(2 / 6)


    # ---------- FOOTER ----------

    st.markdown(
        """
        <div class="footer">
            © 2026 Resume Analyzer & Job Matcher •
            Your Success, Our Mission 🚀
        </div>
        """,
        unsafe_allow_html=True
    )


# =========================================================
# SLIDE 3
# =========================================================

def slide_three():

    st.markdown(
        """
        <div class="main-title">
            Resume <span class="gradient-title">Analysis</span>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="subtitle">
            Key information extracted from your resume.
        </div>
        """,
        unsafe_allow_html=True
    )

    st.info(
        "Slide 3 will contain Skills, Education, Experience and Keywords."
    )

    if st.button("← Back", key="slide3_back"):
        st.session_state.slide = 2
        st.rerun()

    if st.button("Next →", key="slide3_next"):
        st.session_state.slide = 4
        st.rerun()

    st.markdown(
        """
        <div class="progress-label">
            Slide 3 of 6
        </div>
        """,
        unsafe_allow_html=True
    )

    st.progress(3 / 6)


# =========================================================
# SLIDE 4
# =========================================================

def slide_four():

    st.markdown(
        """
        <div class="main-title">
            <span class="gradient-title">ATS Score</span>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="subtitle">
            Your resume performance and ATS compatibility.
        </div>
        """,
        unsafe_allow_html=True
    )

    st.info(
        "Slide 4 will contain ATS score and score breakdown."
    )

    if st.button("← Back", key="slide4_back"):
        st.session_state.slide = 3
        st.rerun()

    if st.button("Next →", key="slide4_next"):
        st.session_state.slide = 5
        st.rerun()

    st.progress(4 / 6)


# =========================================================
# SLIDE 5
# =========================================================

def slide_five():

    st.markdown(
        """
        <div class="main-title">
            Job <span class="gradient-title">Matches</span>
            For You
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="subtitle">
            Top job opportunities based on your profile.
        </div>
        """,
        unsafe_allow_html=True
    )

    st.info(
        "Slide 5 will contain job matches and direct application links."
    )

    if st.button("← Back", key="slide5_back"):
        st.session_state.slide = 4
        st.rerun()

    if st.button("Next →", key="slide5_next"):
        st.session_state.slide = 6
        st.rerun()

    st.progress(5 / 6)


# =========================================================
# SLIDE 6
# =========================================================

def slide_six():

    st.markdown(
        """
        <div class="main-title">
            Missing Skills &
            <span class="gradient-title">
                Recommendations
            </span>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="subtitle">
            Improve your skills to get better opportunities.
        </div>
        """,
        unsafe_allow_html=True
    )

    st.info(
        "Slide 6 will contain missing skills and personalized recommendations."
    )

    if st.button("← Back", key="slide6_back"):
        st.session_state.slide = 5
        st.rerun()

    if st.button("Start Over 🔄", key="start_over"):
        st.session_state.slide = 1
        st.session_state.resume_file = None
        st.session_state.resume_text = ""
        st.rerun()

    st.progress(6 / 6)


# =========================================================
# PAGE ROUTING
# =========================================================

if st.session_state.slide == 1:
    slide_one()

elif st.session_state.slide == 2:
    slide_two()

elif st.session_state.slide == 3:
    slide_three()

elif st.session_state.slide == 4:
    slide_four()

elif st.session_state.slide == 5:
    slide_five()

elif st.session_state.slide == 6:
    slide_six()