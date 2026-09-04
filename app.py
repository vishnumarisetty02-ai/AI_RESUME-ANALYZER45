import streamlit as st
import pymupdf
import os
import json
import html
import hmac
import hashlib
import secrets
import re
import textwrap
import zipfile
import xml.etree.ElementTree as ET
from dotenv import load_dotenv
from groq import Groq
from docx import Document

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------

st.set_page_config(
    page_title="AI Resume Analyzer",
    page_icon="📄",
    layout="wide"
)

load_dotenv()

USER_STORE = os.path.join(os.path.dirname(__file__), "users.json")


def load_users():
    try:
        with open(USER_STORE, "r", encoding="utf-8") as user_file:
            users = json.load(user_file)
            return users if isinstance(users, dict) else {}
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_users(users):
    with open(USER_STORE, "w", encoding="utf-8") as user_file:
        json.dump(users, user_file, indent=2)


def hash_password(password, salt=None):
    salt = salt or secrets.token_hex(16)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        120_000,
    ).hex()
    return salt, password_hash


def password_matches(password, salt, expected_hash):
    _, password_hash = hash_password(password, salt)
    return hmac.compare_digest(password_hash, expected_hash)


def valid_email(email):
    return re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email) is not None


def show_output_item(value, style):
    safe_value = html.escape(str(value))
    st.markdown(
        f'<div class="output-item output-{style}">{safe_value}</div>',
        unsafe_allow_html=True,
    )


users = load_users()
configured_email = os.getenv("LOGIN_EMAIL", "").strip().lower()
configured_password = os.getenv("LOGIN_PASSWORD", "")

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.title("AI Resume Analyzer")

    login_tab, register_tab = st.tabs(["Sign in", "Create account"])

    with login_tab:
        with st.form("login_form"):
            email = st.text_input("Email address", placeholder="you@example.com")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Sign in", type="primary")

        if submitted:
            normalized_email = email.strip().lower()
            registered_user = users.get(normalized_email)
            registered_login = registered_user and password_matches(
                password,
                registered_user["salt"],
                registered_user["password_hash"],
            )
            configured_login = (
                configured_email
                and configured_password
                and hmac.compare_digest(normalized_email, configured_email)
                and hmac.compare_digest(password, configured_password)
            )

            if registered_login or configured_login:
                st.session_state["authenticated"] = True
                st.session_state["user_email"] = normalized_email
                st.rerun()
            else:
                st.error("Invalid email or password.")

    with register_tab:
        with st.form("register_form"):
            new_email = st.text_input("Email address", key="register_email")
            new_password = st.text_input("Password", type="password", key="register_password")
            confirm_password = st.text_input("Confirm password", type="password")
            register_submitted = st.form_submit_button("Create account", type="primary")

        if register_submitted:
            normalized_email = new_email.strip().lower()

            if not valid_email(normalized_email):
                st.error("Enter a valid email address.")
            elif len(new_password) < 8:
                st.error("Password must contain at least 8 characters.")
            elif new_password != confirm_password:
                st.error("Passwords do not match.")
            elif normalized_email in users or normalized_email == configured_email:
                st.error("An account with this email already exists.")
            else:
                salt, password_hash = hash_password(new_password)
                users[normalized_email] = {
                    "salt": salt,
                    "password_hash": password_hash,
                }
                save_users(users)
                st.success("Account created. Open the Sign in tab to continue.")

    st.stop()

API_KEY = os.getenv("GROQ_API_KEY")

if not API_KEY:
    st.error("GROQ_API_KEY is missing. Add it to your .env file.")
    st.stop()

client = Groq(api_key=API_KEY)

MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

# --------------------------------------------------
# CUSTOM CSS
# --------------------------------------------------

st.markdown("""
<style>
:root {
    --ink: #102a43;
    --ink-soft: #486581;
    --ink-muted: #6b8294;
    --surface: #ffffff;
    --surface-soft: #f4faf9;
    --line: #c8dfdc;
    --teal: #0f766e;
    --teal-light: #ccfbf1;
    --coral: #e76f51;
    --coral-light: #fff1eb;
    --gold: #d99a2b;
}

[data-testid="stAppViewContainer"] {
    background-color: #fbfdfc;
    background-image:
        radial-gradient(circle at 90% 0%, rgba(231, 111, 81, 0.12), transparent 25rem),
        linear-gradient(135deg, #eaf8f5 0%, #fbfdfc 52%, #fff3ec 100%);
    background-size: 100% 100%;
}

[data-testid="stAppViewContainer"] > .main {
    background: radial-gradient(circle at 88% 6%, rgba(231, 111, 81, 0.10), transparent 26rem);
}

[data-testid="stMainBlockContainer"] {
    padding-top: 2.5rem;
    padding-bottom: 4rem;
    max-width: 1180px;
}

[data-testid="stHeader"] {
    background: rgba(255, 255, 255, 0.9);
}

[data-testid="stSidebar"] {
    background: #102a43;
}

[data-testid="stSidebar"] * {
    color: #f1fbf8 !important;
}

[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stMarkdown {
    color: #f1fbf8 !important;
}

[data-testid="stSidebar"] [data-testid="stAlert"] {
    background: #1d4f78;
    border: 1px solid #36769d;
}

/* Lines ~210–230 — UNIQUE LOGOUT BUTTON */

[data-testid="stSidebar"] button[kind="secondary"] {
    background: linear-gradient(135deg, #7c3aed, #4f46e5) !important;
    color: #ffffff !important;
    border: 1px solid #8b5cf6 !important;
    border-radius: 12px !important;
    font-weight: 700 !important;
    padding: 0.55rem 1.2rem !important;
    box-shadow: 0 4px 14px rgba(124, 58, 237, 0.35) !important;
    transition: all 0.25s ease-in-out !important;
}

[data-testid="stSidebar"] button[kind="secondary"]:hover {
    background: linear-gradient(135deg, #9333ea, #6366f1) !important;
    color: #ffffff !important;
    border-color: #a78bfa !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 7px 20px rgba(139, 92, 246, 0.5) !important;
}

.main-title {
    color: var(--ink);
    font-family: Georgia, "Times New Roman", serif;
    font-size: 3rem;
    font-weight: 800;
    margin-bottom: 0.25rem;
}

.subtitle {
    color: var(--ink-soft);
    font-size: 1.05rem;
    margin-bottom: 2rem;
}

.section {
    color: var(--ink);
    font-size: 1.35rem;
    font-weight: 750;
    margin-top: 1.5rem;
    padding: 0.65rem 0 0.45rem 0.85rem;
    border-left: 5px solid var(--coral);
    background: linear-gradient(90deg, var(--coral-light) 0%, rgba(255, 241, 235, 0) 78%);
}

.section:first-letter {
    color: var(--coral);
}

.result-intro {
    background: linear-gradient(110deg, #12304a, #117c83);
    border-radius: 12px;
    color: #ffffff;
    padding: 1.15rem 1.35rem;
    margin: 1rem 0 1.4rem;
}

.result-intro h3,
[data-testid="stAppViewContainer"] .stMarkdown .result-intro h3 {
    color: #ffffff !important;
    margin: 0;
}

.result-intro p,
[data-testid="stAppViewContainer"] .stMarkdown .result-intro p {
    color: #e8fbf8 !important;
    margin: 0.35rem 0 0;
}

.report-label {
    color: var(--ink-soft);
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

[data-testid="stAppViewContainer"] .stMarkdown p,
[data-testid="stAppViewContainer"] .stMarkdown li,
[data-testid="stAppViewContainer"] .stMarkdown strong,
[data-testid="stAppViewContainer"] h1,
[data-testid="stAppViewContainer"] h2,
[data-testid="stAppViewContainer"] h3,
[data-testid="stAppViewContainer"] h4 {
    color: var(--ink);
}

[data-testid="stMetricLabel"] {
    color: var(--ink-soft) !important;
    font-weight: 700;
}

[data-testid="stMetricValue"] {
    color: var(--teal) !important;
    font-weight: 800;
}

[data-testid="stMetric"] {
    background: var(--surface);
    border: 1px solid var(--line);
    border-top: 4px solid var(--teal);
    border-radius: 12px;
    box-shadow: 0 8px 20px rgba(16, 42, 67, 0.06);
    padding: 1rem 1.1rem;
}

[data-testid="stMetricDelta"] {
    color: var(--coral) !important;
}

[data-testid="stAlert"] p {
    color: inherit !important;
}

[data-testid="stAlert"] {
    border-radius: 10px;
}

.output-item {
    border-radius: 9px;
    margin: 0.4rem 0;
    padding: 0.65rem 0.85rem;
    font-weight: 600;
}

.output-positive {
    background: #e4f7f2;
    border-left: 4px solid var(--teal);
    color: #075e59;
}

.output-negative {
    background: #fff0ed;
    border-left: 4px solid var(--coral);
    color: #a63d2d;
}

.output-warning {
    background: #fff7df;
    border-left: 4px solid var(--gold);
    color: #795510;
}

.output-info {
    background: #eaf3fb;
    border-left: 4px solid #3182bd;
    color: #205a83;
}

[data-testid="stCodeBlock"] code,
[data-testid="stJson"] {
    color: var(--ink) !important;
}

div[data-testid="stTextArea"] textarea {
    color: var(--ink) !important;
    caret-color: var(--coral);
}

div[data-testid="stFileUploader"] section {
    background: #ffffff;
    border: 1px solid #b7d8d2;
    border-radius: 12px;
}

div[data-testid="stFileUploader"] section * {
    color: var(--ink);
}

div[data-testid="stFileUploader"] section small,
div[data-testid="stFileUploader"] section [data-testid="stFileUploaderDropzoneInstructions"] div {
    color: var(--ink-soft) !important;
}

div[data-testid="stFileUploader"] [data-testid="stFileUploaderFileName"] {
    color: var(--ink) !important;
    font-weight: 650;
}

div[data-testid="stFileUploader"] [data-testid="stFileUploaderFile"] {
    background: #eaf8f5 !important;
    border: 1px solid #b7d8d2 !important;
    border-radius: 10px !important;
}

div[data-testid="stFileUploader"] [data-testid="stFileUploaderFile"] button {
    background: #ffffff !important;
    color: var(--ink) !important;
    border: 1px solid var(--line) !important;
}

div[data-testid="stFileUploader"] [data-testid="stFileUploaderFile"] small {
    color: var(--ink-soft) !important;
}

div[data-testid="stFileUploader"] label,
div[data-testid="stTextArea"] label,
div[data-testid="stTextInput"] label {
    color: var(--ink) !important;
    font-weight: 650;
}

div[data-testid="stTextArea"] textarea::placeholder,
div[data-testid="stTextInput"] input::placeholder {
    color: #78909c;
    opacity: 1;
}

div[data-testid="stTextArea"] textarea,
div[data-baseweb="input"] input {
    background: var(--surface);
    border: 1px solid var(--line);
    color: var(--ink);
    border-radius: 10px;
}

div[data-baseweb="input"] input:focus,
div[data-testid="stTextArea"] textarea:focus {
    border-color: var(--teal);
    box-shadow: 0 0 0 2px var(--teal-light);
}

button[kind="primary"] {
    background: var(--coral) !important;
    border-color: var(--coral) !important;
}

button[kind="primary"]:hover {
    background: #c9573d !important;
    border-color: #c9573d !important;
}

button[kind="secondary"] {
    color: var(--ink) !important;
    border: 1px solid var(--line) !important;
    background: var(--surface) !important;
}

button[kind="secondary"]:hover {
    color: var(--teal) !important;
    border-color: var(--teal) !important;
    background: var(--teal-light) !important;
}

[data-baseweb="tab-list"] {
    gap: 0.35rem;
    border-bottom: 1px solid var(--line);
}

[data-baseweb="tab"] {
    color: var(--ink-soft);
    font-weight: 700;
}

[aria-selected="true"][data-baseweb="tab"] {
    color: var(--teal) !important;
}

[data-baseweb="tab-highlight"] {
    background: var(--coral) !important;
}

div[data-testid="stDownloadButton"] button {
    color: var(--ink);
    border-color: var(--line);
    background: var(--surface);
}

div[data-testid="stDownloadButton"] button:hover {
    color: var(--teal);
    border-color: var(--teal);
    background: var(--teal-light);
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
        if getattr(e, "status_code", None) == 401:
            st.error(
                "Groq rejected the API key. Create a new Groq key, update GROQ_API_KEY in .env, "
                "and restart Streamlit."
            )
        else:
            st.error(f"AI analysis failed: {e}")
        return None


# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

with st.sidebar:

    st.header("⚙️ Settings")

    if st.button("Log out"):
        st.session_state["authenticated"] = False
        st.session_state.pop("analysis", None)
        st.rerun()

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
            show_output_item(skill, "positive")

    with col2:

        st.subheader("❌ Missing Skills")

        missing = analysis.get(
            "missing_skills",
            []
        )

        for skill in missing:
            show_output_item(skill, "negative")

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
            show_output_item(item, "positive")

    with col2:

        st.subheader("⚠️ Weaknesses")

        for item in analysis.get(
            "weaknesses",
            []
        ):
            show_output_item(item, "negative")

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
            show_output_item(issue, "warning")

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

        show_output_item(skill, "info")

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
