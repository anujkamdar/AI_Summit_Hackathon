from agno.agent import Agent
from agno.models.groq import Groq
from agno.knowledge.knowledge import Knowledge
from agno.vectordb.mongodb import MongoVectorDb
from agno.knowledge.reader.pdf_reader import PDFReader
from dotenv import load_dotenv
import logging
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

def Ranking_agent(mdb_connection_string):
    pass


Mongo=r"mongodb+srv://anujkamdar2006_db_user:UlaKG5HA8btbBmvm@sandboxportal.gsimmxy.mongodb.net/sandboxportal"


