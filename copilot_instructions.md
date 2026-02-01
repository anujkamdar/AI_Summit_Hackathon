# Project: Autonomous Job Search & Auto-Apply Agent (Hackathon 2026)

## 1. Project Overview & Goal
**Objective:** Build a fully autonomous AI agent that searches for jobs, personalizes applications, and submits them without human intervention.
**Core Constraints:**
* [cite_start]**Zero Human-in-the-Loop:** The agent must run end-to-end (Search → Rank → Apply) automatically[cite: 8].
* [cite_start]**Truthfulness:** The agent must never invent credentials; all claims must be grounded in the `StudentProfile`[cite: 9, 27].
* [cite_start]**Safety:** The agent must strictly adhere to an "Apply Policy" (max apps, blocked companies) and include a "Kill Switch"[cite: 60, 67].

## 2. Architecture & Components
The system is divided into three distinct applications:

### A. The Brain: `ai-agent/fastapi-backend` (Port 8000)
* **Role:** The central intelligence and orchestrator.
* **Stack:** Python, FastAPI, Motor (Async MongoDB), LangChain (future integration).
* **Responsibilities:**
    * Runs the `agent_loop` background task (Search & Apply cycles).
    * Manages the MongoDB Atlas database.
    * Serves the API consumed by the Frontend.

### B. The Cockpit: `FrontEnd` (Port 5173)
* **Role:** The user interface for monitoring and control.
* **Stack:** React (Vite), Tailwind CSS, Lucide Icons.
* **Responsibilities:**
    * [cite_start]**Live Dashboard:** Visualizes the "Job Queue" and real-time "Logs".
    * [cite_start]**Policy Control:** Allows the user to toggle the "Kill Switch" and set constraints.
    * **Polling:** Fetches updates from the FastAPI backend every 2 seconds.

### C. The Target: `sandbox-portal` (Port 4000)
* [cite_start]**Role:** A mock external job board to safely demonstrate autonomy[cite: 53, 88].
* **Stack:** Node.js, Express, Mongoose.
* **Responsibilities:**
    * [cite_start]**Jobs Feed:** `GET /api/jobs` provides 50+ dummy job listings[cite: 90].
    * [cite_start]**Submission Endpoint:** `POST /api/apply` accepts applications[cite: 91].
    * [cite_start]**Chaos Mode:** Randomly fails 20% of requests (HTTP 500/429) to test the Agent's retry logic.

---

## 3. Directory Structure & Key Files
```text
/
├── ai-agent/
│   └── fastapi-backend/
│       ├── main.py             # Entry point, API routes, and Background Tasks
│       ├── models.py           # Pydantic models (Job, Policy, Log)
│       ├── database.py         # MongoDB Connection (Motor)
│       └── .env                # Contains MONGO_URI
│
├── FrontEnd/
│   ├── src/
│   │   ├── App.jsx             # Main Dashboard View (Status, Queue, Logs)
│   │   └── api.js              # Axios configuration
│   └── tailwind.config.js
│
└── sandbox-portal/
    ├── server.js               # Express API with Chaos Mode
    ├── seed.js                 # Script to generate dummy jobs


