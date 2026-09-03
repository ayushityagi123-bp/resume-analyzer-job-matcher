import streamlit as st

st.set_page_config(
    page_title="Resume Analyzer & Job Matcher",
    page_icon="📄",
    layout="wide"
)

if "slide" not in st.session_state:
    st.session_state.slide = 1

if "resume_file" not in st.session_state:
    st.session_state.resume_file = None

st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #f8f7ff, #eef5ff);
}

.block-container {
    max-width: 1100px;
    padding-top: 25px;
}

#MainMenu, footer, header {
    visibility: hidden;
}

.top-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 30px;
}

.logo {
    font-size: 27px;
    font-weight: 800;
    color: #292641;
}

.logo span {
    color: #6c63ff;
}

.step {
    background: white;
    padding: 9px 18px;
    border-radius: 25px;
    color: #77758a;
    font-weight: 600;
    box-shadow: 0 5px 20px rgba(80,70,150,.08);
}

.card {
    background: white;
    border-radius: 28px;
    padding: 55px;
    text-align: center;
    box-shadow: 0 18px 50px rgba(65,54,120,.12);
}

.title {
    font-size: 42px;
    font-weight: 800;
    color: #292641;
    margin-bottom: 10px;
}

.title span {
    color: #6c63ff;
}

.subtitle {
    font-size: 17px;
    color: #77758a;
    margin-bottom: 40px;
}

.heading {
    font-size: 23px;
    font-weight: 750;
    color: #292641;
    margin-bottom: 20px;
}

.upload-box {
    max-width: 760px;
    margin: auto;
    padding: 45px 25px;
    border: 2px dashed #b8b1f7;
    border-radius: 22px;
    background: #faf9ff;
}

.upload-icon {
    font-size: 48px;
    margin-bottom: 12px;
}

.upload-text {
    font-size: 18px;
    font-weight: 700;
    color: #39345e;
}

.upload-or {
    margin: 10px 0;
    color: #9996a8;
}

[data-testid="stFileUploader"] {
    max-width: 760px;
    margin: 15px auto;
}

[data-testid="stFileUploaderDropzone"] {
    background: transparent !important;
    border: none !important;
}

[data-testid="stFileUploaderDropzoneInstructions"] {
    display: none !important;
}

[data-testid="stFileUploaderDropzone"] button {
    background: #6c63ff !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: 700 !important;
}

.file-box {
    max-width: 760px;
    margin: 20px auto;
    padding: 18px 22px;
    background: #f1f0ff;
    border: 1px solid #d8d4ff;
    border-radius: 15px;
    text-align: left;
}

.file-name {
    font-weight: 750;
    color: #39345e;
}

.file-size {
    margin-top: 5px;
    font-size: 13px;
    color: #77758a;
}

.privacy {
    margin: 25px 0;
    color: #77758a;
    font-size: 13px;
}

.slide-count {
    color: #77758a;
    font-weight: 600;
    padding-top: 10px;
}

div.stButton > button {
    border-radius: 12px;
    font-weight: 700;
    padding: 10px 22px;
}

.slide2 {
    background: white;
    padding: 100px;
    border-radius: 28px;
    text-align: center;
    box-shadow: 0 18px 50px rgba(65,54,120,.12);
}

.slide2 h1 {
    color: #292641;
}

.slide2 p {
    color: #77758a;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="top-header">
    <div class="logo">Resume<span>AI</span></div>
    <div class="step">Step 1 of 6</div>
</div>
""", unsafe_allow_html=True)

if st.session_state.slide == 1:

    st.markdown("""
    <div class="card">

        <div class="title">
            Resume Analyzer <span>&</span> Job Matcher
        </div>

        <div class="subtitle">
            Analyze your resume, match jobs and grow your career!
        </div>

        <div class="heading">
            Upload Your Resume (PDF)
        </div>

        <div class="upload-box">
            <div class="upload-icon">☁️</div>
            <div class="upload-text">
                Drag & Drop your PDF here
            </div>
            <div class="upload-or">or</div>
        </div>
    """, unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "Browse Files",
        type=["pdf"],
        label_visibility="collapsed"
    )

    if uploaded_file:

        st.session_state.resume_file = uploaded_file

        size = uploaded_file.size

        if size < 1024:
            size_text = f"{size} B"
        elif size < 1024 * 1024:
            size_text = f"{size / 1024:.1f} KB"
        else:
            size_text = f"{size / (1024 * 1024):.2f} MB"

        st.markdown(
            f"""
            <div class="file-box">
                <div class="file-name">
                    ✅ {uploaded_file.name}
                </div>
                <div class="file-size">
                    PDF Resume • {size_text}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("""
        <div class="privacy">
            🔒 We respect your privacy. Your data is secure with us.
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([2, 6, 2])

    with col1:
        st.markdown(
            '<div class="slide-count">Slide 1 of 6</div>',
            unsafe_allow_html=True
        )

    with col3:

        if st.session_state.resume_file:
            if st.button("Next →", use_container_width=True):
                st.session_state.slide = 2
                st.rerun()
        else:
            st.button(
                "Next →",
                disabled=True,
                use_container_width=True
            )

elif st.session_state.slide == 2:

    st.markdown("""
    <div class="slide2">
        <h1>Slide 2</h1>
        <p>Resume Text Extraction will be added here.</p>
    </div>
    """, unsafe_allow_html=True)

    st.write("")

    if st.button("← Back"):
        st.session_state.slide = 1
        st.rerun()