import streamlit as st


# =====================================================
# PAGE SETTINGS
# =====================================================

st.set_page_config(
    page_title="Resume Analyzer & Job Matcher",
    page_icon="📄",
    layout="wide"
)


# =====================================================
# SESSION STATE
# =====================================================

if "slide" not in st.session_state:
    st.session_state.slide = 1

if "resume_file" not in st.session_state:
    st.session_state.resume_file = None


# =====================================================
# CUSTOM DESIGN
# =====================================================

st.markdown(
    """
<style>

.stApp {
    background:
        radial-gradient(circle at 85% 20%, rgba(110, 70, 255, 0.20), transparent 30%),
        radial-gradient(circle at 10% 80%, rgba(0, 140, 255, 0.12), transparent 28%),
        #070914;
}

/* Main width */
.block-container {
    max-width: 1400px;
    padding-top: 45px;
    padding-bottom: 40px;
}

/* Hide Streamlit branding */
#MainMenu {
    visibility: hidden;
}

footer {
    visibility: hidden;
}

/* ---------------- HERO ---------------- */

.hero-title {
    font-size: 54px;
    font-weight: 800;
    line-height: 1.1;
    letter-spacing: -2px;
    margin-bottom: 15px;
}

.white {
    color: #ffffff;
}

.purple {
    color: #a855f7;
}

.blue {
    color: #38bdf8;
}

.hero-text {
    color: #9ca3af;
    font-size: 19px;
    line-height: 1.6;
    max-width: 650px;
}

/* ---------------- TAGS ---------------- */

.tag {
    display: inline-block;
    padding: 7px 15px;
    margin: 18px 8px 0 0;
    border-radius: 25px;
    border: 1px solid rgba(168, 85, 247, 0.45);
    background: rgba(124, 58, 237, 0.10);
    color: #c4b5fd;
    font-size: 14px;
}

/* ---------------- UPLOAD CARD ---------------- */

.upload-card {
    margin-top: 35px;
    padding: 32px;
    border-radius: 22px;
    background: rgba(20, 23, 39, 0.90);
    border: 1px solid rgba(139, 92, 246, 0.45);
    box-shadow:
        0 0 35px rgba(124, 58, 237, 0.12),
        inset 0 1px 0 rgba(255,255,255,0.04);
}

.upload-icon {
    width: 65px;
    height: 65px;
    margin: -62px auto 20px auto;
    border-radius: 17px;
    background: linear-gradient(135deg, #7c3aed, #2563eb);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 31px;
    box-shadow: 0 0 28px rgba(124, 58, 237, 0.55);
}

.upload-heading {
    text-align: center;
    color: #ffffff;
    font-size: 27px;
    font-weight: 700;
}

.upload-subheading {
    text-align: center;
    color: #9ca3af;
    margin-top: 8px;
    margin-bottom: 20px;
}

/* ---------------- ILLUSTRATION ---------------- */

.visual-area {
    min-height: 480px;
    position: relative;
    display: flex;
    align-items: center;
    justify-content: center;
}

/* Hero image */
.hero-image {
    width: 100%;
    max-width: 560px;
    height: auto;
    object-fit: contain;
    position: relative;
    z-index: 2;
    filter: drop-shadow(0 0 35px rgba(124, 58, 237, 0.30));
}

/* ---------------- SECURITY ---------------- */

.security {
    margin-top: 15px;
    color: #94a3b8;
    font-size: 13px;
}

/* ---------------- FEATURES ---------------- */

.feature-box {
    margin-top: 35px;
    padding: 23px 25px;
    border-radius: 18px;
    background: rgba(15,18,34,0.85);
    border: 1px solid rgba(148,163,184,0.15);
}

.feature-title {
    color: #a78bfa;
    font-weight: 700;
    font-size: 14px;
    margin-bottom: 18px;
}

.feature-item {
    color: #d1d5db;
    font-size: 14px;
}

.feature-item span {
    font-size: 22px;
}

/* ---------------- BUTTON ---------------- */

.stButton > button {
    border-radius: 12px;
    border: 1px solid rgba(139,92,246,0.55);
    background: linear-gradient(135deg, #7c3aed, #2563eb);
    color: white;
    font-weight: 700;
    min-height: 45px;
}

.stButton > button:hover {
    border-color: #c4b5fd;
    box-shadow: 0 0 25px rgba(99,102,241,0.45);
}

/* ---------------- FILE UPLOADER ---------------- */

[data-testid="stFileUploader"] {
    margin-top: 18px;
}

[data-testid="stFileUploaderDropzone"] {
    border: 1px dashed rgba(139,92,246,0.6);
    border-radius: 15px;
    background: rgba(12,15,28,0.75);
}

</style>
""",
    unsafe_allow_html=True
)


# =====================================================
# HERO SECTION
# =====================================================

st.markdown(
    """
<div class="hero-title">
    <span class="white">Resume</span>
    <span class="purple"> Analyzer</span>
    <span class="white">&amp;</span>
    <span class="blue"> Job Matcher</span>
    🚀
</div>

<div class="hero-text">
    Analyze your resume, check ATS score, discover matching
    opportunities and improve your career profile.
</div>

<div>
    <span class="tag">✦ Smart Analysis</span>
    <span class="tag">⚡ ATS Score</span>
    <span class="tag">⌕ Job Matching</span>
    <span class="tag">✧ Skill Improvement</span>
</div>
""",
    unsafe_allow_html=True
)


# =====================================================
# MAIN SECTION
# =====================================================

left, right = st.columns([1, 1], gap="large")


# =====================================================
# LEFT — UPLOAD
# =====================================================

with left:

    st.markdown(
        """
<div class="upload-card">

<div class="upload-icon">↑</div>

<div class="upload-heading">
Upload Your Resume
</div>

<div class="upload-subheading">
Upload your resume in PDF format to start the analysis.
</div>

</div>
""",
        unsafe_allow_html=True
    )

    uploaded_file = st.file_uploader(
        "Choose your Resume PDF",
        type=["pdf"]
    )

    if uploaded_file is not None:

        st.session_state.resume_file = uploaded_file

        st.success(
            f"✅ {uploaded_file.name} uploaded successfully!"
        )

        st.markdown(
            """
<div class="security">
🔒 Your resume is securely processed for analysis.
</div>
""",
            unsafe_allow_html=True
        )

        st.write("")

        if st.button(
            "Continue to Resume Analysis →",
            use_container_width=True
        ):

            st.session_state.slide = 2
            st.rerun()


# =====================================================
# RIGHT — HERO IMAGE
# =====================================================

with right:

    st.markdown(
        '<div class="visual-area">',
        unsafe_allow_html=True
    )

    st.image(
        "assets/hero.png",
        use_container_width=True
    )

    st.markdown(
        '</div>',
        unsafe_allow_html=True
    )


# =====================================================
# FEATURES
# =====================================================

st.markdown(
    """
<div class="feature-box">

<div class="feature-title">
✨ KEY FEATURES
</div>

</div>
""",
    unsafe_allow_html=True
)

f1, f2, f3, f4 = st.columns(4)

with f1:
    st.markdown(
        """
<div class="feature-item">
<span>🛡️</span><br>
<b>Smart Analysis</b><br>
AI-powered resume insights
</div>
""",
        unsafe_allow_html=True
    )

with f2:
    st.markdown(
        """
<div class="feature-item">
<span>📊</span><br>
<b>ATS Score</b><br>
Check your resume strength
</div>
""",
        unsafe_allow_html=True
    )

with f3:
    st.markdown(
        """
<div class="feature-item">
<span>🔎</span><br>
<b>Job Matching</b><br>
Find suitable opportunities
</div>
""",
        unsafe_allow_html=True
    )

with f4:
    st.markdown(
        """
<div class="feature-item">
<span>💡</span><br>
<b>Skill Improvement</b><br>
Get personalized suggestions
</div>
""",
        unsafe_allow_html=True
    )