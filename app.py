import streamlit as st
import fitz
import os
import json
import re
from dotenv import load_dotenv
from groq import Groq
from docx import Document

# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

load_dotenv()

API_KEY = os.getenv("GROQ_API_KEY")

if not API_KEY:
    st.error("GROQ_API_KEY is missing. Add it to your .env file.")
    st.stop()

client = Groq(api_key=API_KEY)

MODEL = "llama-3.3-70b-versatile"

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------

st.set_page_config(
    page_title="AI Resume Analyzer",
    page_icon="📄",
    layout="wide"
)

# --------------------------------------------------
# CUSTOM CSS
# --------------------------------------------------

st.markdown("""
<style>

.main-title {
    font-size: 42px;
    font-weight: bold;
    text-align: center;
    margin-bottom: 5px;
}

.subtitle {
    text-align: center;
    color: gray;
    font-size: 18px;
    margin-bottom: 30px;
}

.score-box {
    padding: 20px;
    border-radius: 15px;
    text-align: center;
    background-color: #f5f5f5;
    margin: 10px;
}

.score {
    font-size: 35px;
    font-weight: bold;
}

.section {
    font-size: 25px;
    font-weight: bold;
    margin-top: 25px;
}

</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# HEADER
# --------------------------------------------------

st.markdown(
    '<div class="main-title">🤖 AI Resume Analyzer</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'Analyze your resume using Llama 3.3 AI and improve your chances of getting shortlisted.'
    '</div>',
    unsafe_allow_html=True
)

# --------------------------------------------------
# FUNCTIONS
# --------------------------------------------------

def extract_pdf_text(file):
    """Extract text from PDF."""

    text = ""

    try:
        pdf = fitz.open(stream=file.read(), filetype="pdf")

        for page in pdf:
            text += page.get_text()

        pdf.close()

    except Exception as e:
        st.error(f"PDF extraction error: {e}")

    return text


def extract_docx_text(file):
    """Extract text from DOCX."""

    text = ""

    try:
        document = Document(file)

        for paragraph in document.paragraphs:
            text += paragraph.text + "\n"

    except Exception as e:
        st.error(f"DOCX extraction error: {e}")

    return text


def extract_resume_text(uploaded_file):

    file_type = uploaded_file.name.lower()

    if file_type.endswith(".pdf"):
        return extract_pdf_text(uploaded_file)

    elif file_type.endswith(".docx"):
        return extract_docx_text(uploaded_file)

    else:
        return ""


def analyze_resume(resume_text, job_description):

    prompt = f"""
You are an expert ATS Resume Analyzer and Career Coach.

Analyze the following resume.

RESUME:
{resume_text}

JOB DESCRIPTION:
{job_description}

Return ONLY valid JSON.

Use this exact structure:

{{
    "overall_score": 0,
    "ats_score": 0,
    "job_match_score": 0,

    "candidate_summary": "",

    "skills": [],

    "matching_skills": [],

    "missing_skills": [],

    "education_analysis": "",

    "experience_analysis": "",

    "projects_analysis": "",

    "strengths": [],

    "weaknesses": [],

    "ats_issues": [],

    "recommended_keywords": [],

    "skills_to_learn": [],

    "resume_improvements": [],

    "improved_summary": "",

    "improved_project_bullet_points": [],

    "interview_questions": []
}}

Scoring rules:

overall_score:
Overall quality of resume from 0-100.

ats_score:
ATS compatibility from 0-100.

job_match_score:
How closely the resume matches the job description from 0-100.

Be realistic.

Do not invent experience, education, skills or projects that are not present.

For missing skills, compare the resume against the job description.

For improved bullet points, improve the wording without inventing achievements.
"""

    try:

        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert resume analyzer."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.2,
            max_tokens=5000
        )

        result = response.choices[0].message.content

        # Remove markdown JSON fences if model adds them
        result = result.replace("```json", "")
        result = result.replace("```", "")
        result = result.strip()

        return json.loads(result)

    except json.JSONDecodeError:
        st.error("AI returned invalid JSON. Please try again.")
        st.code(result)
        return None

    except Exception as e:
        st.error(f"AI analysis failed: {e}")
        return None


# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

with st.sidebar:

    st.header("⚙️ Settings")

    st.write("### AI Model")

    st.info("Llama 3.3 70B via Groq")

    st.write("### Supported Files")

    st.write("📄 PDF")
    st.write("📝 DOCX")

    st.write("---")

    st.write("### Features")

    st.write("✅ Resume Analysis")
    st.write("✅ ATS Score")
    st.write("✅ Job Matching")
    st.write("✅ Skill Gap Analysis")
    st.write("✅ AI Improvements")
    st.write("✅ Interview Questions")


# --------------------------------------------------
# INPUT SECTION
# --------------------------------------------------

st.markdown(
    '<div class="section">📤 Upload Resume</div>',
    unsafe_allow_html=True
)

uploaded_file = st.file_uploader(
    "Upload your resume",
    type=["pdf", "docx"]
)

st.markdown(
    '<div class="section">💼 Job Description</div>',
    unsafe_allow_html=True
)

job_description = st.text_area(
    "Paste the target job description here",
    height=250,
    placeholder="Example: We are looking for a Python Developer with Machine Learning, SQL, FastAPI..."
)


# --------------------------------------------------
# ANALYZE BUTTON
# --------------------------------------------------

if st.button(
    "🚀 Analyze Resume",
    type="primary",
    use_container_width=True
):

    if uploaded_file is None:

        st.warning("Please upload your resume.")

    elif not job_description.strip():

        st.warning("Please enter a job description.")

    else:

        with st.spinner("📄 Reading resume..."):

            resume_text = extract_resume_text(uploaded_file)

        if not resume_text.strip():

            st.error("Could not extract text from the resume.")

        else:

            with st.spinner(
                "🤖 Llama 3.3 is analyzing your resume..."
            ):

                analysis = analyze_resume(
                    resume_text,
                    job_description
                )

            if analysis:

                st.session_state["analysis"] = analysis
                st.session_state["resume_text"] = resume_text


# --------------------------------------------------
# RESULTS
# --------------------------------------------------

if "analysis" in st.session_state:

    analysis = st.session_state["analysis"]

    st.markdown("---")

    st.markdown(
        '<div class="section">📊 Resume Score</div>',
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Overall Score",
            f"{analysis.get('overall_score', 0)}/100"
        )

    with col2:

        st.metric(
            "ATS Score",
            f"{analysis.get('ats_score', 0)}/100"
        )

    with col3:

        st.metric(
            "Job Match",
            f"{analysis.get('job_match_score', 0)}%"
        )

    # ------------------------------------------------
    # SUMMARY
    # ------------------------------------------------

    st.markdown(
        '<div class="section">👤 Candidate Summary</div>',
        unsafe_allow_html=True
    )

    st.write(
        analysis.get(
            "candidate_summary",
            "No summary available."
        )
    )

    # ------------------------------------------------
    # SKILLS
    # ------------------------------------------------

    st.markdown(
        '<div class="section">🛠️ Skills</div>',
        unsafe_allow_html=True
    )

    skills = analysis.get("skills", [])

    if skills:

        st.write(
            " • ".join(
                [f"`{skill}`" for skill in skills]
            )
        )

    # ------------------------------------------------
    # MATCHING SKILLS
    # ------------------------------------------------

    col1, col2 = st.columns(2)

    with col1:

        st.subheader("✅ Matching Skills")

        matching = analysis.get(
            "matching_skills",
            []
        )

        for skill in matching:
            st.success(skill)

    with col2:

        st.subheader("❌ Missing Skills")

        missing = analysis.get(
            "missing_skills",
            []
        )

        for skill in missing:
            st.error(skill)

    # ------------------------------------------------
    # EDUCATION
    # ------------------------------------------------

    st.markdown(
        '<div class="section">🎓 Education Analysis</div>',
        unsafe_allow_html=True
    )

    st.write(
        analysis.get(
            "education_analysis",
            ""
        )
    )

    # ------------------------------------------------
    # EXPERIENCE
    # ------------------------------------------------

    st.markdown(
        '<div class="section">💼 Experience Analysis</div>',
        unsafe_allow_html=True
    )

    st.write(
        analysis.get(
            "experience_analysis",
            ""
        )
    )

    # ------------------------------------------------
    # PROJECTS
    # ------------------------------------------------

    st.markdown(
        '<div class="section">🚀 Projects Analysis</div>',
        unsafe_allow_html=True
    )

    st.write(
        analysis.get(
            "projects_analysis",
            ""
        )
    )

    # ------------------------------------------------
    # STRENGTHS / WEAKNESSES
    # ------------------------------------------------

    col1, col2 = st.columns(2)

    with col1:

        st.subheader("💪 Strengths")

        for item in analysis.get(
            "strengths",
            []
        ):
            st.success(item)

    with col2:

        st.subheader("⚠️ Weaknesses")

        for item in analysis.get(
            "weaknesses",
            []
        ):
            st.warning(item)

    # ------------------------------------------------
    # ATS ISSUES
    # ------------------------------------------------

    st.markdown(
        '<div class="section">🤖 ATS Analysis</div>',
        unsafe_allow_html=True
    )

    ats_issues = analysis.get(
        "ats_issues",
        []
    )

    if ats_issues:

        for issue in ats_issues:
            st.warning(issue)

    else:

        st.success(
            "No major ATS issues detected."
        )

    # ------------------------------------------------
    # KEYWORDS
    # ------------------------------------------------

    st.markdown(
        '<div class="section">🔑 Recommended Keywords</div>',
        unsafe_allow_html=True
    )

    keywords = analysis.get(
        "recommended_keywords",
        []
    )

    for keyword in keywords:

        st.code(keyword)

    # ------------------------------------------------
    # SKILLS TO LEARN
    # ------------------------------------------------

    st.markdown(
        '<div class="section">📚 Skills to Learn</div>',
        unsafe_allow_html=True
    )

    for skill in analysis.get(
        "skills_to_learn",
        []
    ):

        st.info(skill)

    # ------------------------------------------------
    # RESUME IMPROVEMENTS
    # ------------------------------------------------

    st.markdown(
        '<div class="section">✨ Resume Improvements</div>',
        unsafe_allow_html=True
    )

    improvements = analysis.get(
        "resume_improvements",
        []
    )

    for improvement in improvements:

        st.write(
            f"👉 {improvement}"
        )

    # ------------------------------------------------
    # IMPROVED SUMMARY
    # ------------------------------------------------

    st.markdown(
        '<div class="section">✍️ Improved Professional Summary</div>',
        unsafe_allow_html=True
    )

    st.info(
        analysis.get(
            "improved_summary",
            ""
        )
    )

    # ------------------------------------------------
    # PROJECT BULLETS
    # ------------------------------------------------

    st.markdown(
        '<div class="section">🚀 Improved Project Bullet Points</div>',
        unsafe_allow_html=True
    )

    bullets = analysis.get(
        "improved_project_bullet_points",
        []
    )

    for bullet in bullets:

        st.write(
            f"• {bullet}"
        )

    # ------------------------------------------------
    # INTERVIEW QUESTIONS
    # ------------------------------------------------

    st.markdown(
        '<div class="section">🎯 AI Interview Questions</div>',
        unsafe_allow_html=True
    )

    questions = analysis.get(
        "interview_questions",
        []
    )

    for i, question in enumerate(
        questions,
        start=1
    ):

        st.write(
            f"**{i}. {question}**"
        )

    # ------------------------------------------------
    # DOWNLOAD REPORT
    # ------------------------------------------------

    report = json.dumps(
        analysis,
        indent=4
    )

    st.download_button(
        label="📥 Download Analysis",
        data=report,
        file_name="resume_analysis.json",
        mime="application/json"
    )

# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.markdown("---")

st.caption(
    "AI Resume Analyzer | Streamlit + Python + Groq + Llama 3.3"
)
