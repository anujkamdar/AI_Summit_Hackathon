# 12 hour AI Summit Hackathon - Autonomous Job Search & Auto-Apply Agent

A fully autonomous AI-powered job search and application system that automatically finds, ranks, and applies to job opportunities based on user profiles. Built for the AI Summit Hackathon 2026.
<img width="1918" height="940" alt="Screenshot 2026-02-02 180056" src="https://github.com/user-attachments/assets/3129a957-2b62-4f9c-b1bc-4ff7b373397a" />


## 🎯 Project Overview

This project implements a complete end-to-end autonomous job application system with three main components:

1. **AI Agent Backend** - Intelligent job matching, ranking, and application generation
2. **Frontend Dashboard** - Real-time monitoring and control interface
3. **Sandbox Portal** - Mock job board for safe testing and demonstration

### Core Features

- ✅ **Zero Human-in-the-Loop**: Fully autonomous job search and application process
- ✅ **AI-Powered Resume Analysis**: Extracts structured data from PDF resumes using LLM
- ✅ **Intelligent Job Matching**: Vector similarity search for finding relevant opportunities
- ✅ **Personalized Applications**: Generates tailored cover letters grounded in resume facts
- ✅ **Real-time Dashboard**: WebSocket-based live updates and monitoring
- ✅ **Job Queue Management**: Track and manage application status
- ✅ **Safety Controls**: Kill switch and policy enforcement
- ✅ **Truthfulness Guarantee**: No hallucination - all claims grounded in actual resume data

## 🤖 Agent Workflow

The system uses multiple specialized AI agents working together to automate the entire job application process. Here's how it works:

### Complete Agent Workflow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    AUTONOMOUS JOB APPLICATION WORKFLOW                  │
└─────────────────────────────────────────────────────────────────────────┘

PHASE 1: USER SIGNUP & ARTIFACT GENERATION
───────────────────────────────────────────
User Uploads Resume PDF
         │
         ▼
┌────────────────────┐
│  Artifact Agent    │
│  (Generate_artifact)│
├────────────────────┤
│ • Parses PDF       │
│ • Extracts facts   │
│ • No hallucination │
│ • Creates artifact │
└─────────┬──────────┘
          │
          ▼
┌─────────────────────────────────────────┐
│  Student Artifact Pack                  │
│  ────────────────────────               │
│  • Student Profile                      │
│    - Education, Experience, Projects    │
│    - Skills (languages, frameworks)     │
│    - Links, Constraints                 │
│  • Bullet Bank                          │
│    - Pre-written achievement bullets   │
│    - Evidence strength ratings          │
│  • Answer Library                       │
│    - Common Q&A pairs                   │
│  • Proof Pack                           │
│    - Supporting links & references       │
└─────────────────────────────────────────┘
          │
          ▼
    Stored in MongoDB
    (student_artifacts collection)


PHASE 2: JOB RANKING & MATCHING
───────────────────────────────
User Triggers Auto-Apply
         │
         ▼
┌────────────────────┐
│  Ranking Agent     │
│  (Ranking_agent)   │
├────────────────────┤
│ 1. Load artifact   │
│ 2. Generate        │
│    embeddings      │
│ 3. Vector search   │
│    in MongoDB      │
│ 4. Find top matches│
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│ Batch Reasoning    │
│ Agent              │
│ (Batch_Reasoning)  │
├────────────────────┤
│ • Analyzes each    │
│   job match        │
│ • Calculates       │
│   match scores     │
│ • Identifies       │
│   skill matches    │
│ • Justifies scores │
└─────────┬──────────┘
          │
          ▼
┌─────────────────────────────────────────┐
│  Ranked Jobs (Top N)                   │
│  ────────────────────────               │
│  • Job ID, Title, Company               │
│  • Match Score (0-100)                  │
│  • Matched Skills                       │
│  • Location, Salary                     │
└─────────────────────────────────────────┘
          │
          ▼
    Added to Job Queue
    (job_queue collection)


PHASE 3: AUTO-APPLY PROCESS
────────────────────────────
For each job in queue:
         │
         ▼
┌────────────────────┐
│  Application Agent │
│  (Application_agent)│
├────────────────────┤
│ Input:             │
│ • Job listing      │
│ • Student artifact │
│                    │
│ Process:           │
│ • Generate tailored│
│   cover letter     │
│ • Ground in facts  │
│ • No hallucination │
│                    │
│ Output:            │
│ • Personalized     │
│   cover letter     │
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│  Submit to Portal  │
│  (Sandbox/Real)    │
├────────────────────┤
│ • POST /api/apply  │
│ • Include resume   │
│ • Include cover     │
│   letter           │
│ • Handle retries    │
│   (chaos mode)     │
└─────────┬──────────┘
          │
          ▼
    Status: SUBMITTED
    (or FAILED with retry)
```
<img width="1917" height="998" alt="Screenshot 2026-02-02 180220" src="https://github.com/user-attachments/assets/d11f4e13-27da-4987-abef-f0dc836ac125" />


### Agent Types

#### 1. **Artifact Agent** (`Generate_artifact`)
**Purpose**: Extract structured data from resume PDF

**Process**:
1. Reads PDF using PDFReader (chunked, 500 chars)
2. Uses Groq LLM (llama-3.3-70b-versatile) with strict instructions
3. Extracts ONLY verifiable facts from resume
4. Creates structured artifact pack

**Safety Rules**:
- ❌ NO invention, inference, or guessing
- ❌ NO metrics unless explicitly stated
- ❌ NO skills not explicitly listed
- ✅ Truthfulness over completeness

**Output Schema**: `UserArtifactPack`
- Student Profile (education, experience, projects, skills)
- Bullet Bank (achievement statements with evidence strength)
- Answer Library (common application questions)
- Proof Pack (supporting links)

#### 2. **Ranking Agent** (`Ranking_agent`)
**Purpose**: Find most relevant jobs using vector similarity

**Process**:
1. Converts student artifact to text
2. Generates embeddings using HuggingFace (all-MiniLM-L6-v2)
3. Performs vector search in MongoDB jobs collection
4. Returns top N matches with similarity scores

**Technology**:
- Vector Database: MongoDB Atlas Vector Search
- Embeddings: Sentence Transformers
- Search Type: Cosine similarity

**Output**: List of job matches with:
- Job ID
- Vector similarity score
- Match reasoning (from Batch Reasoning Agent)

#### 3. **Batch Reasoning Agent** (`Batch_Reasoning_Agent`)
**Purpose**: Analyze and justify job matches

**Process**:
1. Takes ranked job results from vector search
2. Analyzes each job against student artifact
3. Calculates detailed match scores:
   - Skill Match Score (0-100)
   - Experience Fit
   - Overall Match Score
4. Provides reasoning for each match

**Scoring Logic**:
- **Skill Match**: Looks for core technologies AND conceptual equivalents
- **Experience Fit**: Measures how projects demonstrate required work habits
- **Domain Transfer**: Recognizes engineering rigor across domains

**Output**: `BatchJobMatch` with detailed analysis for each job

#### 4. **Application Agent** (`Application_agent`)
**Purpose**: Generate personalized cover letters

**Process**:
1. Takes job listing (title, company, description, skills)
2. Takes student artifact (facts only)
3. Uses Groq LLM to generate tailored cover letter
4. Grounds ALL claims in actual resume data

**Safety Rules**:
- ❌ ZERO hallucination
- ❌ NO invented experience or numbers
- ✅ Every claim must be traceable to artifact
- ✅ Truthfulness prioritized over persuasion

**Output**: Personalized cover letter paragraph

### Auto-Apply Workflow Phases
<img width="1918" height="942" alt="Screenshot 2026-02-02 180246" src="https://github.com/user-attachments/assets/25354990-7d0b-412b-b484-8c71372f356e" />

When a user triggers auto-apply (`POST /api/auto-apply/start`), the system executes:

#### **Phase 1: Initialization**
- Load user's resume artifact from MongoDB
- Validate artifact exists
- Initialize embedder (singleton)
- Stream status via WebSocket

#### **Phase 2: Ranking**
- Run Ranking Agent to find matching jobs
- Process results with Batch Reasoning Agent
- Calculate match scores and skill overlaps
- Stream each ranked job in real-time
- Limit to top N jobs (default: 10)

#### **Phase 3: Queuing**
- Add ranked jobs to application queue
- Check for duplicates
- Set status: `IN_PROGRESS`
- Stream queue updates via WebSocket

#### **Phase 4: Auto-Apply** (if enabled)
For each job in queue:
1. Update status: `APPLYING`
2. Fetch full job details from sandbox portal
3. Run Application Agent to generate cover letter
4. Submit application to portal
5. Handle retries on failure (chaos mode)
6. Update status: `SUBMITTED` or `FAILED`
7. Stream progress via WebSocket

#### **Phase 5: Completion**
- Send final summary (applied/failed counts)
- Update queue status
- Set agent status: `idle`
- Stream completion message

### Real-time Updates

All phases stream progress via WebSocket (`/ws/dashboard`):

**Message Types**:
- `log`: Text log messages (info, success, error, warning)
- `queue_update`: Job queue state changes
- `status_update`: Agent status (idle, running, error)
- `job_update`: Individual job status changes
- `process_update`: Progress updates (phase, current/total)

**Example Flow**:
```javascript
// Connect to WebSocket
ws = new WebSocket('ws://localhost:8000/ws/dashboard?token=JWT_TOKEN');

// Receive updates
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  switch(data.type) {
    case 'log':
      console.log(data.message); // "🚀 Starting Auto-Apply workflow..."
      break;
    case 'queue_update':
      updateJobQueue(data.queue); // Real-time queue updates
      break;
    case 'job_update':
      updateJobStatus(data.job); // Individual job status
      break;
    case 'process_update':
      updateProgress(data); // Progress bar updates
      break;
  }
};
```

### Workflow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER SIGNUP                                  │
│  Upload Resume PDF → Artifact Agent → Store Artifact            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AUTO-APPLY TRIGGER                           │
│  POST /api/auto-apply/start                                     │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 1: INITIALIZATION                                        │
│  • Load artifact                                                │
│  • Validate data                                                │
│  • Initialize agents                                            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 2: RANKING                                               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │ Ranking      │───▶│ Batch        │───▶│ Top N Jobs   │      │
│  │ Agent        │    │ Reasoning    │    │ Ranked       │      │
│  │ (Vector      │    │ Agent        │    │              │      │
│  │  Search)     │    │ (Analysis)   │    │              │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 3: QUEUING                                               │
│  • Add jobs to queue                                            │
│  • Set status: IN_PROGRESS                                      │
│  • Check duplicates                                             │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 4: AUTO-APPLY (if enabled)                               │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ For each job:                                            │  │
│  │  1. Application Agent → Generate Cover Letter            │  │
│  │  2. Submit to Portal (Sandbox/Real)                     │  │
│  │  3. Handle Retries (Chaos Mode)                        │  │
│  │  4. Update Status: SUBMITTED / FAILED                  │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 5: COMPLETION                                            │
│  • Send summary                                                 │
│  • Update final queue state                                     │
│  • Set agent status: idle                                       │
└─────────────────────────────────────────────────────────────────┘
```

## 🏗️ Architecture

The system consists of three independent applications:

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (React)                         │
│                  Port: 5173                                 │
│  - Landing Page                                             │
│  - Authentication                                           │
│  - Real-time Dashboard                                      │
│  - WebSocket Connection                                     │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        │ HTTP/WebSocket
                        │
┌───────────────────────▼─────────────────────────────────────┐
│              FASTAPI BACKEND (Python)                       │
│                  Port: 8000                                 │
│  - REST API                                                 │
│  - Authentication (JWT)                                     │
│  - Job Ranking Agent                                        │
│  - Application Agent                                        │
│  - Artifact Generation                                      │
│  - MongoDB Integration                                      │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        │ HTTP API
                        │
┌───────────────────────▼─────────────────────────────────────┐
│            SANDBOX PORTAL (Node.js)                        │
│                  Port: 4000                                 │
│  - Mock Job Board                                           │
│  - Application Submission                                   │
│  - Chaos Mode (20% failure rate)                           │
└─────────────────────────────────────────────────────────────┘
```

## 🛠️ Tech Stack

### Backend (FastAPI)
- **Framework**: FastAPI 0.109.0
- **Database**: MongoDB (Motor async driver)
- **Authentication**: JWT (python-jose), bcrypt
- **AI/ML**: 
  - Groq LLM (llama-3.3-70b-versatile)
  - Agno Agent Framework
  - Sentence Transformers (HuggingFace embeddings)
  - PyTorch
- **Other**: Uvicorn, Pydantic, python-multipart

### Frontend (React)
- **Framework**: React 19.2.0 with Vite
- **Routing**: React Router DOM 7.13.0
- **Styling**: Tailwind CSS 4.1.18
- **HTTP Client**: Axios 1.13.4
- **Icons**: Lucide React
- **3D Graphics**: OGL

### Sandbox Portal (Node.js)
- **Runtime**: Node.js
- **Framework**: Express
- **Database**: MongoDB (Mongoose)
- **Features**: Chaos mode for testing resilience

## 📁 Project Structure

```
AI_Summit_Hackathon/
├── ai-agent/
│   ├── agent.py                    # AI agent functions (artifact generation, ranking, application)
│   ├── Embed_Vector_DB.py          # Vector database embedding utilities
│   ├── schema.py                   # Pydantic schemas for artifacts
│   └── fastapi-backend/
│       ├── main.py                 # FastAPI app entry point
│       ├── models.py               # Pydantic models
│       ├── auth.py                 # Authentication utilities
│       ├── database.py             # MongoDB connection
│       ├── websocket_manager.py    # WebSocket connection management
│       ├── requirements.txt        # Python dependencies
│       ├── routers/
│       │   ├── auth.py             # Authentication endpoints
│       │   ├── users.py            # User management endpoints
│       │   ├── jobs.py             # Job ranking and queue endpoints
│       │   └── auto_apply.py       # Auto-apply functionality
│       ├── API_DOCUMENTATION.md    # API reference
│       ├── ARCHITECTURE.md         # System architecture details
│       └── README.md               # Backend-specific documentation
│
├── FrontEnd/
│   ├── src/
│   │   ├── App.jsx                 # Main app component with routing
│   │   ├── main.jsx                # React entry point
│   │   ├── component/
│   │   │   ├── LandingPage.jsx     # Landing page component
│   │   │   ├── AuthPage.jsx        # Authentication UI
│   │   │   ├── Dashboard.jsx       # Main dashboard
│   │   │   └── Galaxy.jsx          # 3D background component
│   │   └── index.css               # Global styles
│   ├── package.json                # Node dependencies
│   └── vite.config.js              # Vite configuration
│
├── sandbox-portal/
│   ├── src/
│   │   └── server.js               # Express server for mock job board
│   └── package.json                # Node dependencies
│
├── copilot_instructions.md         # Development guidelines
└── README.md                        # This file
```

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- Node.js 16+
- MongoDB Atlas account (or local MongoDB instance)
- Groq API key ([Get one here](https://console.groq.com/))

### Installation

#### 1. Clone the Repository

```bash
git clone <repository-url>
cd AI_Summit_Hackathon
```

#### 2. Backend Setup

```bash
cd ai-agent/fastapi-backend

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### 3. Frontend Setup

```bash
cd ../../FrontEnd

# Install dependencies
npm install
```

#### 4. Sandbox Portal Setup

```bash
cd ../sandbox-portal

# Install dependencies
npm install
```

### Environment Variables

#### Backend (.env in `ai-agent/fastapi-backend/`)

Create a `.env` file with the following variables:

```env
# MongoDB Connection
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/database_name

# JWT Secret Key (generate a secure random string)
SECRET_KEY=your-secret-key-here

# Groq API Key
GROQ_API_KEY=your-groq-api-key-here
```

#### Sandbox Portal (.env in `sandbox-portal/`)

```env
# MongoDB Connection (can be same as backend or different)
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/sandbox_db
```

## 🏃 Running the Application

### Start All Services

You'll need three terminal windows/tabs:

#### Terminal 1: Backend Server

```bash
cd ai-agent/fastapi-backend
uvicorn main:app --reload
```

Backend will be available at: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

#### Terminal 2: Frontend

```bash
cd FrontEnd
npm run dev
```

Frontend will be available at: `http://localhost:5173`

#### Terminal 3: Sandbox Portal

```bash
cd sandbox-portal
node src/server.js
```

Sandbox Portal will be available at: `http://localhost:4000`

### Seed the Sandbox Portal

Visit `http://localhost:4000` and click "Seed Database" to populate 50 sample jobs, or use:

```bash
curl -X POST http://localhost:4000/seed
```

## 📡 API Documentation

### Authentication Endpoints

#### Sign Up
```http
POST /api/auth/signup
Content-Type: multipart/form-data

Fields:
  - email (required)
  - password (required, min 6 chars)
  - resume (required, PDF file)
  - work_authorization (optional)
  - location_preference (optional)
  - remote_preference (optional)
  - start_date (optional)
  - relocation (optional)
  - salary_expectation (optional)
```

#### Sign In
```http
POST /api/auth/signin
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}
```

### Job Management Endpoints

#### Rank Jobs
```http
POST /api/jobs/rank
Authorization: Bearer <token>
Content-Type: application/json

{
  "user_email": "user@example.com",
  "max_results": 50
}
```

#### Get Queue Status
```http
GET /api/jobs/queue/status
Authorization: Bearer <token>
```

#### Add Jobs to Queue
```http
POST /api/jobs/queue/add-batch
Authorization: Bearer <token>
Content-Type: application/json

{
  "jobs": [
    {"job_id": "123", "match_score": 85.5},
    {"job_id": "456", "match_score": 78.2}
  ]
}
```

#### Apply to Job
```http
POST /api/jobs/queue/{queue_item_id}/apply
Authorization: Bearer <token>
```

### Auto-Apply Endpoint

#### Start Auto-Apply Workflow
```http
POST /api/auto-apply/start
Authorization: Bearer <token>
Content-Type: application/json

{
  "max_jobs": 10,
  "auto_apply": true
}
```

This endpoint:
1. Ranks jobs based on user's artifact
2. Adds top jobs to queue
3. Auto-applies to each job (generates cover letters)
4. Streams progress via WebSocket

### WebSocket Connection

Connect to real-time updates:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/dashboard?token=YOUR_JWT_TOKEN');
```

Message types:
- `log`: Real-time log messages
- `queue_update`: Job queue updates
- `status_update`: Agent status changes
- `job_update`: Individual job status changes
- `process_update`: Progress updates during auto-apply

For complete API documentation, see:
- [API_DOCUMENTATION.md](ai-agent/fastapi-backend/API_DOCUMENTATION.md)
- Interactive docs: `http://localhost:8000/docs`

## 🔑 Key Features Explained

### 1. Student Artifact Generation

When a user signs up with a resume, the system:
1. Parses the PDF resume using PDFReader
2. Extracts structured information using Groq LLM
3. Creates a reusable artifact pack containing:
   - Student Profile (education, experience, projects, skills)
   - Bullet Bank (pre-formatted achievement statements)
   - Answer Library (common application questions)
   - Proof Pack (supporting links and references)

**Safety**: The agent is instructed to extract ONLY facts from the resume - no hallucinations.

### 2. Job Ranking System

Uses vector similarity search:
1. Converts student artifact to embeddings using HuggingFace models
2. Searches MongoDB vector index for similar job descriptions
3. Returns ranked jobs with match scores (0-100)
4. Highlights matched skills

### 3. Application Agent

Generates personalized cover letters:
- Takes job listing and student artifact as input
- Uses Groq LLM to create tailored cover letter
- All claims grounded in actual resume data
- No fabrication of experience or achievements

### 4. Real-time Dashboard

- WebSocket connection for live updates
- Job queue visualization
- Application status tracking
- Real-time logs
- Agent control (start/stop)

### 5. Sandbox Portal

Mock job board for testing:
- 50+ dummy job listings
- Application submission endpoint
- Chaos mode: 20% random failures (HTTP 500/429/503)
- Tests agent retry logic and resilience

## 🔒 Security Features

- ✅ Password hashing with bcrypt
- ✅ JWT token authentication
- ✅ CORS protection
- ✅ Input validation with Pydantic
- ✅ File type validation (PDF only)
- ✅ Secure environment variable management

## 🧪 Testing

### Test Backend API

```bash
# Health check
curl http://localhost:8000/health

# Test signup (replace with actual file path)
curl -X POST "http://localhost:8000/api/auth/signup" \
  -F "email=test@example.com" \
  -F "password=test123" \
  -F "resume=@/path/to/resume.pdf"
```

### Test Sandbox Portal

```bash
# Get all jobs
curl http://localhost:4000/api/jobs

# Submit application
curl -X POST http://localhost:4000/api/apply \
  -H "Content-Type: application/json" \
  -d '{
    "jobId": "job_id_here",
    "applicantName": "Test User",
    "resumeText": "Resume content...",
    "coverLetter": "Cover letter content..."
  }'
```

## 📊 Database Collections

### MongoDB Collections

1. **users**: User accounts and authentication
   - email, password hash, resume (base64), artifact_id, FAQ answers

2. **student_artifacts**: AI-generated resume artifacts
   - user_email, artifact_data (structured profile), timestamps

3. **job_queue**: User job application queue
   - user_email, job_id, status, match_score, cover_letter, timestamps

4. **jobs**: Available job listings (in sandbox portal)
   - title, company, location, description, requiredSkills, salary

5. **applications**: Submitted applications (in sandbox portal)
   - jobId, applicantName, resumeText, coverLetter, status

## 🎨 Frontend Components

- **LandingPage**: Welcome page with project overview
- **AuthPage**: Sign up and sign in forms with resume upload
- **Dashboard**: Main interface with:
  - Real-time job queue
  - Application status
  - Live logs
  - Agent controls
  - Statistics

## 🚧 Development Notes

### Known Limitations

- Resume processing is synchronous (may take 2-5 seconds)
- Vector embeddings require initial model download
- Sandbox portal uses hardcoded MongoDB connection (update for production)
- Auto-apply to external portals requires portal-specific integrations

### Future Enhancements

- [ ] Async resume processing
- [ ] Support for multiple resume formats
- [ ] Integration with real job boards (LinkedIn, Indeed, etc.)
- [ ] Advanced filtering and search
- [ ] Email notifications
- [ ] Application tracking and analytics
- [ ] Multi-user support with roles

## 📝 Additional Documentation

- [Backend README](ai-agent/fastapi-backend/README.md)
- [Architecture Details](ai-agent/fastapi-backend/ARCHITECTURE.md)
- [API Documentation](ai-agent/fastapi-backend/API_DOCUMENTATION.md)
- [Integration Summary](ai-agent/fastapi-backend/INTEGRATION_SUMMARY.md)
- [Ranking Queue Integration](ai-agent/fastapi-backend/RANKING_QUEUE_INTEGRATION.md)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project was created for the AI Summit Hackathon 2026.

## 👥 Authors

Built by the AI Summit Hackathon team.

## 🙏 Acknowledgments

- Groq for LLM API access
- MongoDB for database hosting
- FastAPI and React communities for excellent frameworks
- Agno framework for agent capabilities

---

**Status**: 🚀 Active Development

For questions or issues, please open an issue on the repository.
