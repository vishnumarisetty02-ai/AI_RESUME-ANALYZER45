import streamlit as st
import pymupdf
import os
import json
import re
import textwrap
import zipfile
import xml.etree.ElementTree as ET
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

MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

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
    color: #17324d;
    font-size: 2.8rem;
    font-weight: 800;
    letter-spacing: -0.02em;
    margin-bottom: 0.25rem;
}

.subtitle {
    color: #607286;
    font-size: 1.05rem;
    margin-bottom: 2rem;
}

.section {
    color: #17324d;
    font-size: 1.35rem;
    font-weight: 750;
    margin-top: 1.5rem;
    padding: 0.65rem 0 0.45rem 0.85rem;
    border-left: 5px solid #e07a5f;
    background: linear-gradient(90deg, #fff3ed 0%, rgba(255, 243, 237, 0) 75%);
}

.result-intro {
    background: #17324d;
    border-radius: 12px;
    color: BLUE;
    padding: 1.15rem 1.35rem;
    margin: 1rem 0 1.4rem;
}

.result-intro h3 {
    color: white;
    margin: 0;
}

.result-intro p {
    color: #d9e7ef;
    margin: 0.35rem 0 0;
}

.report-label {
    color: #607286;
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
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
        pdf = pymupdf.open(stream=file.read(), filetype="pdf")

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
        # A corrupt embedded image can prevent python-docx from loading the
        # package even when the document XML and its text are still readable.
        try:
            file.seek(0)
            with zipfile.ZipFile(file) as archive:
                document_xml = archive.read("word/document.xml")

            root = ET.fromstring(document_xml)
            namespace = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
            paragraphs = []
            for paragraph in root.iter(f"{namespace}p"):
                paragraphs.append(
                    "".join(
                        node.text or ""
                        for node in paragraph.iter(f"{namespace}t")
                    )
                )

            text = "\n".join(paragraphs)
            st.warning(
                "Some embedded DOCX content is damaged, but the resume text was recovered."
            )
        except Exception:
            st.error(f"DOCX extraction error: {e}")

    return text


def extract_ipynb_text(file):
    """Extract markdown and code cells from a Jupyter Notebook."""

    try:
        notebook = json.loads(file.getvalue().decode("utf-8"))
        sections = []

        for cell in notebook.get("cells", []):
            cell_type = cell.get("cell_type", "")
            source = "".join(cell.get("source", []))

            if source.strip() and cell_type in {"markdown", "code"}:
                sections.append(f"[{cell_type.upper()} CELL]\n{source.strip()}")

        return "\n\n".join(sections)

    except (UnicodeDecodeError, json.JSONDecodeError, AttributeError) as error:
        st.error(f"Jupyter Notebook extraction error: {error}")
        return ""


def extract_resume_text(uploaded_file):

    file_type = uploaded_file.name.lower()

    if file_type.endswith(".pdf"):
        return extract_pdf_text(uploaded_file)

    elif file_type.endswith(".docx"):
        return extract_docx_text(uploaded_file)

    elif file_type.endswith(".ipynb"):
        return extract_ipynb_text(uploaded_file)

    else:
        return ""


def create_pdf_report(analysis):
    """Create a structured PDF report instead of printing raw JSON."""

    pdf = pymupdf.open()
    page = pdf.new_page()
    margin = 54
    y_position = margin
    navy = (0.09, 0.20, 0.30)
    coral = (0.88, 0.29, 0.20)
    body = (0.18, 0.22, 0.25)

    def write_lines(lines, fontsize=10, color=body, spacing=14, bold=False):
        nonlocal page, y_position

        for line in lines:
            if y_position > page.rect.height - margin:
                page = pdf.new_page()
                y_position = margin

            page.insert_text(
                (margin, y_position),
                line,
                fontsize=fontsize,
                fontname="helv",
                color=color,
            )
            y_position += spacing

    def write_section(title, value):
        nonlocal y_position
        y_position += 10
        write_lines([title.upper()], fontsize=12, color=coral, spacing=18, bold=True)

        values = value if isinstance(value, list) else [value]
        for item in values:
            item_lines = textwrap.wrap(str(item), width=95) or [""]
            write_lines([f"- {item_lines[0]}"])
            if len(item_lines) > 1:
                write_lines([f"  {line}" for line in item_lines[1:]])

    write_lines(["AI RESUME ANALYSIS REPORT"], fontsize=22, color=navy, spacing=28, bold=True)
    write_lines(["A structured review of resume quality, ATS readiness, and job fit."], color=(0.38, 0.45, 0.51), spacing=22)

    score_lines = [
        f"Overall score: {analysis.get('overall_score', 0)}/100",
        f"ATS score: {analysis.get('ats_score', 0)}/100",
        f"Job match score: {analysis.get('job_match_score', 0)}%",
    ]
    write_section("Score overview", score_lines)

    sections = [
        ("Candidate summary", analysis.get("candidate_summary", "")),
        ("Skills", analysis.get("skills", [])),
        ("Matching skills", analysis.get("matching_skills", [])),
        ("Missing skills", analysis.get("missing_skills", [])),
        ("Education analysis", analysis.get("education_analysis", "")),
        ("Experience analysis", analysis.get("experience_analysis", "")),
        ("Projects analysis", analysis.get("projects_analysis", "")),
        ("Strengths", analysis.get("strengths", [])),
        ("Weaknesses", analysis.get("weaknesses", [])),
        ("ATS issues", analysis.get("ats_issues", [])),
        ("Recommended keywords", analysis.get("recommended_keywords", [])),
        ("Skills to learn", analysis.get("skills_to_learn", [])),
        ("Resume improvements", analysis.get("resume_improvements", [])),
        ("Improved summary", analysis.get("improved_summary", "")),
        ("Improved project bullet points", analysis.get("improved_project_bullet_points", [])),
        ("Interview questions", analysis.get("interview_questions", [])),
    ]

    for title, value in sections:
        if value:
            write_section(title, value)

    return pdf.tobytes()


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

    st.info(f"{MODEL} via Groq")

    st.write("### Supported Files")

    st.write("📄 PDF")
    st.write("📝 DOCX")
    st.write("📓 IPYNB")

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
    type=["pdf", "docx", "ipynb"]
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

    st.markdown(
        '<div class="result-intro"><h3>Your resume analysis is ready</h3>'
        '<p>Review the score, identify skill gaps, and use the recommendations to strengthen your application.</p></div>',
        unsafe_allow_html=True
    )

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

    st.download_button(
        label="📄 Download PDF Report",
        data=create_pdf_report(analysis),
        file_name="resume_analysis.pdf",
        mime="application/pdf"
    )

    with st.expander("View raw JSON"):
        st.json(analysis)

# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.markdown("---")

st.caption(
    "AI Resume Analyzer | Streamlit + Python + Groq + Llama 3.3"
)