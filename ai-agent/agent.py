from agno.agent import Agent
from agno.models.groq import Groq
from agno.knowledge.knowledge import Knowledge
from agno.vectordb.mongodb import MongoVectorDb, SearchType
from agno.knowledge.reader.pdf_reader import PDFReader
from agno.knowledge.embedder.huggingface import HuggingfaceCustomEmbedder

from dotenv import load_dotenv
import logging
import json
import os

import schema

load_dotenv() 
GROQ_API = os.getenv("GROQ_API_KEY")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


def Generate_artifact(pdf_path):
    logger.info("Beginning Artifact Agent workflow...")
    reader = PDFReader(chunk=True, chunk_size=500)
    documents = reader.read(pdf_path)

    pdf_text = "\n\n".join([doc.content for doc in documents])

    logger.info("Finished parsing pdf file...")
    SYSTEM_PROMPT = """You are a Student Artifact Pack Generator Agent.

Your responsibility is to extract only verifiable, explicitly stated facts from the provided resume PDF knowledge source and produce a reusable, facts-only application artifact pack.

This artifact pack is the single source of truth for all downstream job-search and auto-apply agents.

========================
AUTHORITATIVE SOURCE RULE
========================

- The resume PDF provided as knowledge is the ONLY authoritative source for:
  education, experience, projects, skills, dates, titles, employers, and achievements.
- If explicit student-provided overrides are passed in the input payload, they may be used ONLY for constraints.
- If a fact cannot be directly retrieved from the resume knowledge, it DOES NOT EXIST and MUST NOT appear in the output.

================
HARD SAFETY RULES
================

You MUST NOT:
- Invent, infer, guess, or assume any information
- Add or estimate metrics, numbers, impact, or scope
- Add skills not explicitly listed or clearly demonstrated
- Merge facts across unrelated resume sections or roles
- Strengthen, normalize, optimize, or reword claims beyond factual clarity
- Use world knowledge, typical student patterns, or prior assumptions

If information is missing or ambiguous:
- Omit it, OR
- Output exactly: "Not specified by student"

Truthfulness always overrides completeness or usefulness.

====================
REQUIRED OUTPUT MODE
====================

- Output MUST conform exactly to the provided output schema
- Output MUST be structured only (no prose, no explanations, no markdown)
- Do NOT include commentary or reasoning
- Do NOT ask clarifying questions

=====================
ARTIFACT REQUIREMENTS
=====================

1. Structured Student Profile (facts only)
   - Preserve original titles, dates, and wording conservatively
   - No inferred seniority or responsibility

2. Bullet Bank
   - Each bullet must map to exactly ONE project or role
   - No metrics unless explicitly stated
   - Assign evidence_strength:
     - high: clearly and explicitly stated
     - medium: stated but brief or vague
     - low: implied but still explicit

3. Answer Library
   - Use resume content only
   - If not stated, return "Not specified by student"

4. Proof Pack
   - Use ONLY links explicitly present in the resume
   - Each link must support at least one claim

====================
BEHAVIORAL CONSTRAINT
====================

- Do not personalize for jobs
- Do not rank or evaluate suitability
- Do not store or recall memory
- Do not optimize for ATS or persuasion

Your sole objective is accuracy, consistency, and grounding.
"""

    agent_Artifact = Agent(
    name="student_artifact_pack_generator",
    model=Groq(id="llama-3.3-70b-versatile", api_key=GROQ_API, temperature=0.1),
    instructions=SYSTEM_PROMPT,
    output_schema=schema.UserArtifactPack,
    )

    USER_PROMPT = f"""Generate a facts-only student application artifact pack using the following PDF content:
{pdf_text}

Extract and return:
- A structured student profile
- A normalized bullet bank
- A reusable answer library
- A proof pack of supporting links

Use only information that can be directly retrieved from the resume knowledge.
If any information is missing or unclear, omit it or return "Not specified by student".

Return output strictly in the required structured format.
"""
    response = agent_Artifact.run(USER_PROMPT)
    logger.info("Received response from agent...")
    return response.content.model_dump(mode='json')

def Ranking_agent(mdb_connection_string, student_artifact, embedder):
    knowledge_base = Knowledge(
    vector_db=MongoVectorDb(
        collection_name="jobs",
        db_url=mdb_connection_string,
        search_type=SearchType.vector,
        embedder=embedder,
        wait_until_index_ready_in_seconds=60,
        wait_after_insert_in_seconds=300
    ),
    )

    artifact_text = json.dumps(
        student_artifact,
        separators=(",", ":"),
        ensure_ascii=False
    )

    results = knowledge_base.search(
        query=artifact_text, 
        max_results=50
    )

    logger.info("Received ranking response...")

    json_list = []
    for doc in results:
        doc_dict = {
            "id": doc.content,
            "score": doc.meta_data.get('score')
        }
        json_list.append(doc_dict)
    return json_list

def Application_agent(job_listing, student_artifact):
    logger.info(f"Generating tailored cover letter for: {job_listing.get('title', 'Unknown Role')}")

    SYSTEM_PROMPT = """You are a Job Application Tailoring Agent. 
Your sole objective is to write a short recruiter note or cover letter-style paragraph for a student. 

========================
AUTONOMY & SAFETY RULES
========================
- ZERO HALLUCINATION: You must not invent experience, numbers, titles, or achievements. 
- GROUNDING: If you cannot ground a claim in the student profile, you must not use it. 
- TRUTHFULNESS: The goal is to stay truthful and relevant, even at high volume. 

========================
OUTPUT REQUIREMENTS
========================
- Create a short recruiter note or cover letter style paragraph. 
- It must explain how the student's specific skills and projects from the Artifact Pack meet the job requirements. 
- Output MUST be a single string (the cover letter). No preamble or extra commentary.
"""

    agent = Agent(
        name="application_cover_letter_agent",
        model=Groq(id="llama-3.3-70b-versatile", api_key=GROQ_API, temperature=0.1),
        instructions=SYSTEM_PROMPT,
        # We use a simple string output here as you only want the letter for now
    )

    USER_PROMPT = f"""
    JOB LISTING REQUIREMENTS:
    {json.dumps(job_listing)}

    STUDENT ARTIFACT PACK (FACTS ONLY):
    {json.dumps(student_artifact)}

    Based ONLY on these facts, write a tailored cover letter paragraph for this role.
    If no match exists for a requirement, ignore that requirement
    """

    response = agent.run(USER_PROMPT)
    return response.content

Mongo=r"mongodb+srv://anujkamdar2006_db_user:UlaKG5HA8btbBmvm@sandboxportal.gsimmxy.mongodb.net/?retryWrites=true&w=majority"
Resume_link= r"C:\Users\joset\Desktop\I_can_do_this_all_day\Helem_Thekkumvilayil_Jose_CV_pdf.pdf"

job= {
      "_id": "697f7e1b31377768af1c5b46",
      "title": "Security Engineer",
      "company": "Apple",
      "location": "Austin, TX",
      "type": "Full-time",
      "salary": "$108k - $160k",
      "description": "We are seeking a talented Security Engineer to join our Apple team in Austin, TX. You will work on cutting-edge projects, collaborate with world-class engineers, and have the opportunity to make a significant impact. This is a full-time position with competitive compensation and benefits.",
      "requiredSkills": [
        "C++",
        "System Design",
        "Linux",
        "Performance"
      ],
      "visa_sponsorship": False,
      "createdAt": "2026-02-01T16:23:55.438Z",
      "__v": 0
    }

#artifact = {'student_profile': {'education': [{'institution': 'Indian Institute of Technology (ISM), Dhanbad', 'degree': 'B.Tech in Electrical Engineering', 'dates': 'Expected 2028', 'reference': {'page': 1, 'section': 'Education'}}, {'institution': 'Sunrise English Private School, Abu Dhabi', 'degree': 'High School (CBSE)', 'dates': '2024', 'reference': {'page': 1, 'section': 'Education'}}], 'experience': [{'role': 'Machine Learning Intern', 'organization': 'LaunchED Global', 'dates': 'May – June 2025', 'description': 'Developed a machine learning model to determine expected employee compensation with R/two.superior Score > 90% and prediction error of Rs 20,000.', 'reference': {'page': 1, 'section': 'Experience'}}], 'projects': [{'name': 'AI Email Assistant – VibeMail', 'description': 'Designed and built an AI-powered email assistant that analyzes past emails to learn user writing style and generate context-aware replies.', 'technologies': ['Python', 'FastAPI', 'SQLAlchemy', 'HTML', 'CSS', 'JavaScript', 'Flask'], 'reference': {'page': 2, 'section': 'Projects'}}, {'name': 'Salary-Prediction-ML-App', 'description': 'Developed a machine learning model to determine expected employee compensation with R/two.superior Score > 90% and prediction error of Rs 20,000.', 'technologies': ['Python', 'Pandas', 'Scikit-learn', 'Streamlit', 'Git'], 'reference': {'page': 1, 'section': 'Experience'}}], 'skills': {'languages': ['C++', 'Python', 'C', 'HTML', 'JavaScript', 'CSS'], 'frameworks': ['FastAPI', 'Flask', 'NumPy', 'Pandas', 'Scikit-learn', 'TensorFlow', 'Matplotlib'], 'tools': [], 'other': ['SQLAlchemy', 'MySQL (basic)']}, 'links': ['linkedin.com/in/helem-jose-9521b3321', 'github.com/Helem-Jose/Salary-Prediction-ML-App', 'github.com/Helem-Jose/VibeMail'], 'constraints': {}}, 'bullet_bank': [{'bullet': 'Developed a machine learning model to determine expected employee compensation with R/two.superior Score > 90% and prediction error of Rs 20,000.', 'source': 'Machine Learning Intern, LaunchED Global', 'evidence_strength': 'high', 'reference': {'page': 1, 'section': 'Experience'}}, {'bullet': 'Applied exploratory data analysis and feature engineering to improve model performance.', 'source': 'Machine Learning Intern, LaunchED Global', 'evidence_strength': 'high', 'reference': {'page': 1, 'section': 'Experience'}}, {'bullet': 'Trained and evaluated six different models to find the best performing one.', 'source': 'Machine Learning Intern, LaunchED Global', 'evidence_strength': 'high', 'reference': {'page': 1, 'section': 'Experience'}}, {'bullet': 'Developed an interactive web dashboard using Streamlit for real-time predictions.', 'source': 'Machine Learning Intern, LaunchED Global', 'evidence_strength': 'high', 'reference': {'page': 1, 'section': 'Experience'}}, {'bullet': 'Designed and built an AI-powered email assistant that analyzes past emails to learn user writing style and generate context-aware replies.', 'source': 'AI Email Assistant – VibeMail', 'evidence_strength': 'high', 'reference': {'page': 2, 'section': 'Projects'}}, {'bullet': 'Architected a modular backend with agent-based workflows for summarization, style extraction, and response generation.', 'source': 'AI Email Assistant – VibeMail', 'evidence_strength': 'high', 'reference': {'page': 2, 'section': 'Projects'}}, {'bullet': 'Implemented RESTful APIs using FastAPI with structured request-response schemas.', 'source': 'AI Email Assistant – VibeMail', 'evidence_strength': 'high', 'reference': {'page': 2, 'section': 'Projects'}}, {'bullet': 'Integrated LLM inference via APIs with attention to latency, scalability, and maintainability.', 'source': 'AI Email Assistant – VibeMail', 'evidence_strength': 'high', 'reference': {'page': 2, 'section': 'Projects'}}], 'answer_library': {'work_authorization': 'Not specified by student', 'location_preference': 'Not specified by student', 'remote_preference': 'Not specified by student', 'start_date': 'Not specified by student', 'relocation': 'Not specified by student', 'salary_expectation': 'Not specified by student'}, 'proof_pack': [{'link': 'linkedin.com/in/helem-jose-9521b3321', 'supports': ['Professional profile']}, {'link': 'github.com/Helem-Jose/Salary-Prediction-ML-App', 'supports': ['Salary-Prediction-ML-App project']}, {'link': 'github.com/Helem-Jose/VibeMail', 'supports': ['AI Email Assistant – VibeMail project']}]}
artifact = Generate_artifact(Resume_link)
embedder = HuggingfaceCustomEmbedder("sentence-transformers/all-MiniLM-L6-v2")
print(Ranking_agent(Mongo, artifact, embedder))
