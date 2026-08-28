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
# CUSTOM CSS
# =====================================================

st.markdown(
"""
<style>

.stApp {
    background:
        radial-gradient(
            circle at 85% 15%,
            rgba(110, 70, 255, 0.20),
            transparent 30%
        ),
        radial-gradient(
            circle at 10% 80%,
            rgba(0, 140, 255, 0.12),
            transparent 28%
        ),
        #070914;
}

.block-container {
    max-width: 1400px;
    padding-top: 45px;
    padding-bottom: 50px;
}

#MainMenu {
    visibility: hidden;
}

footer {
    visibility: hidden;
}


/* =====================================================
   HERO
   ===================================================== */

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
    max-width: 720px;
}


/* =====================================================
   TAGS
   ===================================================== */

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


/* =====================================================
   UPLOAD CARD
   ===================================================== */

.upload-card {
    margin-top: 40px;
    padding: 45px 35px 35px 35px;
    border-radius: 22px;
    background: rgba(20, 23, 39, 0.92);
    border: 1px solid rgba(139, 92, 246, 0.45);
    box-shadow:
        0 0 35px rgba(124, 58, 237, 0.12),
        inset 0 1px 0 rgba(255,255,255,0.04);
    text-align: center;
}

.upload-icon {
    width: 64px;
    height: 64px;
    margin: -78px auto 20px auto;
    border-radius: 17px;
    background: linear-gradient(
        135deg,
        #7c3aed,
        #2563eb
    );
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 30px;
    color: white;
    box-shadow:
        0 0 28px rgba(124, 58, 237, 0.55);
}

.upload-heading {
    color: #ffffff;
    font-size: 27px;
    font-weight: 700;
}

.upload-subheading {
    color: #9ca3af;
    margin-top: 8px;
    font-size: 15px;
}


/* =====================================================
   RIGHT VISUAL
   ===================================================== */

.visual-box {
    margin-top: 40px;
    min-height: 390px;
    border-radius: 35px;
    border: 1px solid rgba(139, 92, 246, 0.35);
    background:
        radial-gradient(
            circle at 50% 35%,
            rgba(168, 85, 247, 0.28),
            transparent 45%
        ),
        rgba(20, 23, 39, 0.75);
    box-shadow:
        0 0 60px rgba(124, 58, 237, 0.15);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
}

.visual-document {
    font-size: 90px;
    line-height: 1;
    margin-bottom: 22px;
    filter:
        drop-shadow(
            0 0 20px rgba(168, 85, 247, 0.35)
        );
}

.visual-heading {
    color: #ffffff;
    font-size: 24px;
    font-weight: 700;
}

.visual-subheading {
    color: #94a3b8;
    font-size: 14px;
    margin-top: 10px;
}

.visual-points {
    color: #c4b5fd;
    font-size: 14px;
    line-height: 2;
    margin-top: 18px;
}


/* =====================================================
   SECURITY
   ===================================================== */

.security {
    margin-top: 15px;
    color: #94a3b8;
    font-size: 13px;
}


/* =====================================================
   FEATURES
   ===================================================== */

.feature-box {
    margin-top: 35px;
    padding: 24px 26px;
    border-radius: 18px;
    background: rgba(15, 18, 34, 0.85);
    border: 1px solid rgba(148, 163, 184, 0.15);
}

.feature-title {
    color: #a78bfa;
    font-weight: 700;
    font-size: 14px;
    margin-bottom: 20px;
}

.feature-item {
    color: #d1d5db;
    font-size: 14px;
    line-height: 1.7;
}

.feature-icon {
    font-size: 25px;
}


/* =====================================================
   BUTTON
   ===================================================== */

.stButton > button {
    border-radius: 12px;
    border: 1px solid rgba(139, 92, 246, 0.55);
    background:
        linear-gradient(
            135deg,
            #7c3aed,
            #2563eb
        );
    color: white;
    font-weight: 700;
    min-height: 45px;
}

.stButton > button:hover {
    border-color: #c4b5fd;
    box-shadow:
        0 0 25px rgba(99, 102, 241, 0.45);
}


/* =====================================================
   FILE UPLOADER
   ===================================================== */

[data-testid="stFileUploader"] {
    margin-top: 18px;
}

[data-testid="stFileUploaderDropzone"] {
    border: 1px dashed rgba(139, 92, 246, 0.6);
    border-radius: 15px;
    background: rgba(12, 15, 28, 0.75);
}

</style>
""",
unsafe_allow_html=True
)


# =====================================================
# SLIDE 1
# =====================================================

if st.session_state.slide == 1:

    # -------------------------------------------------
    # TITLE
    # -------------------------------------------------

    st.markdown(
"""
<div class="hero-title">
<span class="white">Resume</span>
<span class="purple"> Analyzer</span>
<span class="white">&amp;</span>
<span class="blue"> Job Matcher</span>
🚀
</div>
""",
unsafe_allow_html=True
    )


    # -------------------------------------------------
    # DESCRIPTION
    # -------------------------------------------------

    st.markdown(
"""
<div class="hero-text">
Analyze your resume, check ATS score, discover matching
opportunities and improve your career profile.
</div>
""",
unsafe_allow_html=True
    )


    # -------------------------------------------------
    # TAGS
    # -------------------------------------------------

    st.markdown(
"""
<div>
<span class="tag">✦ Smart Analysis</span>
<span class="tag">⚡ ATS Score</span>
<span class="tag">⌕ Job Matching</span>
<span class="tag">✧ Skill Improvement</span>
</div>
""",
unsafe_allow_html=True
    )


    st.write("")


    # =================================================
    # MAIN COLUMNS
    # =================================================

    left, right = st.columns(
        [1, 1],
        gap="large"
    )


    # =================================================
    # LEFT — UPLOAD
    # =================================================

    with left:

        st.markdown(
"""
<div class="upload-card">

<div class="upload-icon">
↑
</div>

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
            type=["pdf"],
            key="resume_uploader"
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


    # =================================================
    # RIGHT — VISUAL
    # =================================================

    with right:

        st.markdown(
"""
<div class="visual-box">

<div class="visual-document">
📄
</div>

<div class="visual-heading">
Smart Resume Analysis
</div>

<div class="visual-subheading">
Analyze • Match • Improve
</div>

<div class="visual-points">
✓ Resume Content<br>
✓ Skills Detection<br>
✓ ATS Compatibility
</div>

</div>
""",
unsafe_allow_html=True
        )


    # =================================================
    # FEATURES
    # =================================================

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
<div class="feature-icon">🛡️</div>
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
<div class="feature-icon">📊</div>
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
<div class="feature-icon">🔎</div>
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
<div class="feature-icon">💡</div>
<b>Skill Improvement</b><br>
Get personalized suggestions
</div>
""",
unsafe_allow_html=True
        )


# =====================================================
# SLIDE 2
# =====================================================

elif st.session_state.slide == 2:

    st.markdown(
"""
<div class="hero-title">
<span class="white">Resume</span>
<span class="purple"> Analysis</span>
🔍
</div>
""",
unsafe_allow_html=True
    )


    st.markdown(
"""
<div class="hero-text">
Your resume is ready. Review your uploaded file
and start the analysis to discover your career insights.
</div>
""",
unsafe_allow_html=True
    )


    st.write("")


    if st.session_state.resume_file is not None:

        st.success(
            f"✓ {st.session_state.resume_file.name} is ready for analysis."
        )


        st.write("")


        col1, col2 = st.columns(
            [1, 1],
            gap="large"
        )


        with col1:

            st.markdown(
"""
<div class="upload-card">

<div class="upload-icon">
📄
</div>

<div class="upload-heading">
Resume Ready
</div>

<div class="upload-subheading">
Your resume has been uploaded successfully.
</div>

</div>
""",
unsafe_allow_html=True
            )


        with col2:

            st.markdown(
"""
<div class="upload-card">

<div class="upload-heading">
✨ What We'll Analyze
</div>

<br>

📄 <b>Resume Content</b><br>
Extract important information.<br><br>

🛠️ <b>Detected Skills</b><br>
Identify technical skills.<br><br>

📊 <b>ATS Compatibility</b><br>
Evaluate ATS readiness.<br><br>

💼 <b>Career Profile</b><br>
Understand your strengths.

</div>
""",
unsafe_allow_html=True
            )


        st.write("")


        if st.button(
            "🚀 Analyze Resume",
            use_container_width=True
        ):

            st.success(
                "Resume analysis will be connected next."
            )


        st.write("")


        if st.button("← Back to Upload"):

            st.session_state.slide = 1
            st.rerun()