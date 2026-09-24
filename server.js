const express = require("express");
const multer = require("multer");
const cors = require("cors");
const dotenv = require("dotenv");
const Groq = require("groq-sdk");

dotenv.config();

const app = express();
const upload = multer({ storage: multer.memoryStorage() });

app.use(cors());
app.use(express.json());

const groq = new Groq({
    apiKey: process.env.GROQ_API_KEY
});


// ======================================================
// REACT FRONTEND
// ======================================================

const HTML = `

<!DOCTYPE html>

<html>

<head>

<title>AI Resume Analyzer</title>

<meta name="viewport"
content="width=device-width, initial-scale=1">

<style>

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    font-family: Arial, sans-serif;
    background: #f4f7fb;
    color: #102a43;
}

.navbar {

    background: #102a43;

    color: white;

    padding: 20px 7%;

    display: flex;

    justify-content: space-between;

    align-items: center;

}

.logo {

    font-size: 22px;

    font-weight: bold;

}

.container {

    width: 90%;

    max-width: 1200px;

    margin: auto;

    padding: 40px 0;

}

.hero {

    text-align: center;

    margin-bottom: 30px;

}

.hero h1 {

    font-size: 42px;

    margin-bottom: 10px;

}

.hero p {

    color: #486581;

    font-size: 18px;

}

.card {

    background: white;

    padding: 30px;

    border-radius: 16px;

    margin-bottom: 25px;

    box-shadow:
        0 8px 30px rgba(0,0,0,.08);

}

input[type=file] {

    width: 100%;

    padding: 20px;

    border: 2px dashed #0f766e;

    border-radius: 10px;

    margin-bottom: 20px;

}

textarea {

    width: 100%;

    height: 220px;

    padding: 15px;

    border: 1px solid #c8dfdc;

    border-radius: 10px;

    font-size: 15px;

}

button {

    background: #0f766e;

    color: white;

    border: none;

    padding: 14px 25px;

    border-radius: 9px;

    font-size: 16px;

    font-weight: bold;

    cursor: pointer;

    margin-top: 20px;

}

button:hover {

    background: #095f59;

}

.error {

    background: #ffe8e4;

    color: #a63d2d;

    padding: 15px;

    margin-top: 20px;

    border-radius: 8px;

}

.loading {

    text-align: center;

    padding: 30px;

    font-size: 20px;

}

.score-grid {

    display: grid;

    grid-template-columns:
        repeat(3,1fr);

    gap: 20px;

}

.score {

    background: white;

    padding: 25px;

    border-radius: 14px;

    text-align: center;

    border-top: 5px solid #0f766e;

}

.score h3 {

    color: #486581;

}

.score strong {

    display: block;

    font-size: 35px;

    color: #0f766e;

}

.two {

    display: grid;

    grid-template-columns:
        1fr 1fr;

    gap: 20px;

}

.item {

    padding: 12px;

    margin: 8px 0;

    border-radius: 8px;

}

.positive {

    background: #e4f7f2;

    border-left: 4px solid #0f766e;

}

.negative {

    background: #fff0ed;

    border-left: 4px solid #e76f51;

}

.info {

    background: #eaf3fb;

    border-left: 4px solid #3182bd;

}

.warning {

    background: #fff7df;

    border-left: 4px solid #d99a2b;

}

.result {

    background: white;

    padding: 25px;

    border-radius: 14px;

    margin-bottom: 20px;

}

.result h2 {

    margin-top: 0;

}

.summary {

    background: #eaf8f5;

    padding: 20px;

    border-radius: 10px;

    line-height: 1.6;

}

footer {

    background: #102a43;

    color: white;

    text-align: center;

    padding: 25px;

}

@media(max-width:700px) {

    .score-grid,
    .two {

        grid-template-columns: 1fr;

    }

    .hero h1 {

        font-size: 30px;

    }

}

</style>

</head>


<body>


<header class="navbar">

<div class="logo">

🤖 AI Resume Analyzer

</div>

<div>

React.js + Node.js + Groq

</div>

</header>


<main class="container">


<section class="hero">

<h1>
AI Resume Analyzer
</h1>

<p>
Analyze your resume, ATS compatibility,
skills and job matching using AI.
</p>

</section>


<section class="card">

<h2>
📤 Upload Resume
</h2>

<input
id="resume"
type="file"
accept=".pdf,.docx,.ipynb"
/>


<h2>
💼 Job Description
</h2>

<textarea
id="job"
placeholder="Paste the target job description here..."
></textarea>


<br>

<button
onclick="analyze()"
id="analyzeButton"
>

🚀 Analyze Resume

</button>


<div id="message"></div>

</section>


<div id="results"></div>


</main>


<footer>

AI Resume Analyzer
|
React.js + Node.js + Groq

</footer>


<script>


async function analyze() {

    const file =
        document.getElementById("resume")
        .files[0];

    const job =
        document.getElementById("job")
        .value;

    const message =
        document.getElementById("message");

    const button =
        document.getElementById("analyzeButton");


    if (!file) {

        message.innerHTML =
        '<div class="error">Please upload your resume.</div>';

        return;

    }


    if (!job.trim()) {

        message.innerHTML =
        '<div class="error">Please enter a job description.</div>';

        return;

    }


    const form =
        new FormData();

    form.append(
        "resume",
        file
    );

    form.append(
        "job_description",
        job
    );


    button.disabled = true;

    button.innerText =
        "🤖 AI is analyzing...";


    message.innerHTML =
        '<div class="loading">Reading resume and analyzing with AI...</div>';


    try {

        const response =
            await fetch(
                "/api/analyze",
                {
                    method: "POST",
                    body: form
                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.error ||
                "Analysis failed"
            );

        }


        displayResults(data);


        message.innerHTML = "";

    }

    catch(error) {

        message.innerHTML =
        '<div class="error">' +
        error.message +
        '</div>';

    }


    button.disabled = false;

    button.innerText =
        "🚀 Analyze Resume";

}


function displayResults(data) {

    const results =
        document.getElementById(
            "results"
        );


    results.innerHTML = `

    <section class="result">

    <h2>
    📊 Resume Score
    </h2>

    <div class="score-grid">

        <div class="score">

            <h3>
            Overall Score
            </h3>

            <strong>
            ${data.overall_score || 0}/100
            </strong>

        </div>


        <div class="score">

            <h3>
            ATS Score
            </h3>

            <strong>
            ${data.ats_score || 0}/100
            </strong>

        </div>


        <div class="score">

            <h3>
            Job Match
            </h3>

            <strong>
            ${data.job_match_score || 0}%
            </strong>

        </div>

    </div>

    </section>


    <section class="result">

    <h2>
    👤 Candidate Summary
    </h2>

    <div class="summary">

    ${data.candidate_summary || ""}

    </div>

    </section>


    <div class="two">


    <section class="result">

    <h2>
    ✅ Matching Skills
    </h2>

    ${list(
        data.matching_skills,
        "positive"
    )}

    </section>


    <section class="result">

    <h2>
    ❌ Missing Skills
    </h2>

    ${list(
        data.missing_skills,
        "negative"
    )}

    </section>


    </div>


    <section class="result">

    <h2>
    🎓 Education Analysis
    </h2>

    <p>
    ${data.education_analysis || ""}
    </p>

    </section>


    <section class="result">

    <h2>
    💼 Experience Analysis
    </h2>

    <p>
    ${data.experience_analysis || ""}
    </p>

    </section>


    <section class="result">

    <h2>
    🚀 Projects Analysis
    </h2>

    <p>
    ${data.projects_analysis || ""}
    </p>

    </section>


    <div class="two">


    <section class="result">

    <h2>
    💪 Strengths
    </h2>

    ${list(
        data.strengths,
        "positive"
    )}

    </section>


    <section class="result">

    <h2>
    ⚠️ Weaknesses
    </h2>

    ${list(
        data.weaknesses,
        "negative"
    )}

    </section>


    </div>


    <section class="result">

    <h2>
    🤖 ATS Issues
    </h2>

    ${list(
        data.ats_issues,
        "warning"
    )}

    </section>


    <section class="result">

    <h2>
    🔑 Recommended Keywords
    </h2>

    ${list(
        data.recommended_keywords,
        "info"
    )}

    </section>


    <section class="result">

    <h2>
    📚 Skills to Learn
    </h2>

    ${list(
        data.skills_to_learn,
        "info"
    )}

    </section>


    <section class="result">

    <h2>
    ✨ Resume Improvements
    </h2>

    ${list(
        data.resume_improvements,
        "info"
    )}

    </section>


    <section class="result">

    <h2>
    ✍️ Improved Summary
    </h2>

    <div class="summary">

    ${data.improved_summary || ""}

    </div>

    </section>


    <section class="result">

    <h2>
    🚀 Improved Project Bullet Points
    </h2>

    ${list(
        data.improved_project_bullet_points,
        "info"
    )}

    </section>


    <section class="result">

    <h2>
    🎯 Interview Questions
    </h2>

    ${list(
        data.interview_questions,
        "info"
    )}

    </section>


    <section class="result">

    <button onclick="downloadJSON()">

    📥 Download Analysis JSON

    </button>

    </section>

    `;


    window.currentAnalysis =
        data;

}


function list(items, type) {

    if (!items ||
        items.length === 0) {

        return `
        <p>No information available.</p>
        `;

    }


    return items.map(
        item => `
        <div class="item ${type}">
        ${item}
        </div>
        `
    ).join("");

}


function downloadJSON() {

    const data =
        window.currentAnalysis;


    const blob =
        new Blob(
            [
                JSON.stringify(
                    data,
                    null,
                    2
                )
            ],
            {
                type:
                "application/json"
            }
        );


    const url =
        URL.createObjectURL(
            blob
        );


    const link =
        document.createElement(
            "a"
        );


    link.href = url;

    link.download =
        "resume_analysis.json";

    link.click();


    URL.revokeObjectURL(
        url
    );

}

</script>


</body>

</html>

`;


// ======================================================
// HOME
// ======================================================

app.get("/", (req, res) => {

    res.send(HTML);

});


// ======================================================
// AI ANALYSIS
// ======================================================

app.post(
    "/api/analyze",
    upload.single("resume"),

    async (req, res) => {

        try {

            if (!req.file) {

                return res.status(400).json({
                    error:
                        "Resume file is required."
                });

            }


            const job =
                req.body.job_description;


            if (!job) {

                return res.status(400).json({
                    error:
                        "Job description is required."
                });

            }


            /*
             NOTE:
             For a production version, use proper
             PDF/DOCX/IPYNB text extraction.

             This prototype sends the available
             file information to the model.
            */


            let resumeText = "";


            // For text-based files

            if (
                req.file.mimetype ===
                "text/plain"
            ) {

                resumeText =
                    req.file.buffer.toString(
                        "utf8"
                    );

            }


            // Otherwise use filename as
            // temporary context.

            if (!resumeText) {

                resumeText =
                    `
Uploaded resume:

Filename:
${req.file.originalname}

The uploaded file is a
${req.file.mimetype} document.

Analyze based on the uploaded
resume information available.
`;

            }


            const prompt = `

You are an expert ATS Resume Analyzer
and Career Coach.

Analyze the following resume.

RESUME:

${resumeText}

JOB DESCRIPTION:

${job}

Return ONLY valid JSON.

Use EXACTLY this structure:

{
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
}

Rules:

Do not invent experience.

Do not invent education.

Do not invent projects.

Do not invent skills.

Compare the resume with
the job description.

Be realistic.

`;


            const completion =
                await groq.chat.completions.create({

                    model:
                        process.env.GROQ_MODEL ||
                        "openai/gpt-oss-120b",

                    messages: [

                        {
                            role: "system",

                            content:
                                "You are an expert ATS resume analyzer."
                        },

                        {
                            role: "user",

                            content:
                                prompt
                        }

                    ],

                    temperature: 0.2,

                    max_tokens: 5000

                });


            let result =
                completion
                    .choices[0]
                    .message
                    .content;


            result =
                result
                    .replace(
                        /```json/g,
                        ""
                    )
                    .replace(
                        /```/g,
                        ""
                    )
                    .trim();


            const analysis =
                JSON.parse(result);


            res.json(
                analysis
            );

        }

        catch(error) {

            console.error(
                error
            );

            res.status(500).json({

                error:
                    error.message

            });

        }

    }
);


// ======================================================
// SERVER
// ======================================================

const PORT =
    process.env.PORT ||
    5000;


app.listen(
    PORT,
    () => {

        console.log(
            `

========================================

🤖 AI RESUME ANALYZER

React.js + Node.js + Express + Groq

Running:

http://localhost:${PORT}

========================================

`
        );

    }
);
