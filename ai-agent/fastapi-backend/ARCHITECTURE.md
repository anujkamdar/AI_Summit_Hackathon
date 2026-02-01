# Student Artifact System - Architecture Diagram

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND (React)                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Signup Form                                              │  │
│  │  - Email, Password                                        │  │
│  │  - Resume Upload (PDF) *Required*                         │  │
│  │  - FAQ Questions (Optional)                               │  │
│  │    • Work Authorization                                   │  │
│  │    • Location Preference                                  │  │
│  │    • Remote Preference                                    │  │
│  │    • Start Date                                           │  │
│  │    • Relocation                                           │  │
│  │    • Salary Expectation                                   │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │ POST /api/auth/signup
                             │ (multipart/form-data)
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FASTAPI BACKEND                              │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  routers/auth.py - Signup Endpoint                        │  │
│  │  1. Validate email, password                              │  │
│  │  2. Check existing user                                   │  │
│  │  3. Process resume → temp file                            │  │
│  │  4. Call agent.py                    ┌────────────────┐   │  │
│  │     └────────────────────────────────► agent.py        │   │  │
│  │                                       │ Generate_      │   │  │
│  │                                       │ artifact()     │   │  │
│  │  5. Store artifact in MongoDB        └────────┬───────┘   │  │
│  │  6. Create user with artifact_id              │           │  │
│  │  7. Return JWT + artifact_id                  │           │  │
│  └────────────────────────────┬──────────────────┼──────────┘  │
└───────────────────────────────┼──────────────────┼─────────────┘
                                │                  │
                                ▼                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                      MONGODB DATABASE                           │
│  ┌──────────────────────┐    ┌───────────────────────────────┐ │
│  │  users collection    │    │  student_artifacts collection │ │
│  │  ─────────────────   │    │  ────────────────────────────  │ │
│  │  {                   │    │  {                            │ │
│  │    _id: ObjectId     │    │    _id: ObjectId              │ │
│  │    email: string     │    │    user_email: string         │ │
│  │    password: hash    │    │    artifact_data: {           │ │
│  │    resume: base64    │    │      student_profile: {       │ │
│  │    artifact_id: ref ─┼────┼────►   education: []          │ │
│  │    faq_answers: {    │    │         experience: []        │ │
│  │      work_auth: str  │    │         projects: []          │ │
│  │      location: str   │    │         skills: {}            │ │
│  │      ...             │    │         links: []             │ │
│  │    }                 │    │       }                       │ │
│  │    created_at: date  │    │       bullet_bank: []         │ │
│  │  }                   │    │       answer_library: {}      │ │
│  │                      │    │       proof_pack: []          │ │
│  │                      │    │     }                         │ │
│  │                      │    │     created_at: date          │ │
│  │                      │    │     updated_at: date          │ │
│  │                      │    │   }                           │ │
│  └──────────────────────┘    └───────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘

                                ▲
                                │
                                │ GET /api/auth/artifact/{email}
                                │
┌─────────────────────────────────────────────────────────────────┐
│                      ARTIFACT RETRIEVAL                         │
│  Frontend or other services can retrieve the artifact for:     │
│  • Job application auto-fill                                    │
│  • Profile generation                                           │
│  • Job matching                                                 │
│  • Resume analysis                                              │
└─────────────────────────────────────────────────────────────────┘
```

## Agent Processing Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     agent.py - Generate_artifact()              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Resume PDF                                                     │
│      │                                                          │
│      ▼                                                          │
│  ┌────────────────┐                                            │
│  │  PDFReader     │ Chunk size: 500                            │
│  │  (chunk=True)  │                                            │
│  └───────┬────────┘                                            │
│          │                                                      │
│          ▼                                                      │
│  ┌────────────────┐                                            │
│  │  Extract Text  │ Documents → Text                           │
│  └───────┬────────┘                                            │
│          │                                                      │
│          ▼                                                      │
│  ┌─────────────────────────────────────────┐                  │
│  │  Groq AI Agent                           │                  │
│  │  Model: llama-3.3-70b-versatile          │                  │
│  │  Temperature: 0.1 (factual)              │                  │
│  │                                          │                  │
│  │  Instructions:                           │                  │
│  │  - Extract facts only                    │                  │
│  │  - No hallucinations                     │                  │
│  │  - Ground in resume content              │                  │
│  │  - Use output schema                     │                  │
│  └─────────────┬───────────────────────────┘                  │
│                │                                                │
│                ▼                                                │
│  ┌──────────────────────────────────────────┐                 │
│  │  schema.py - UserArtifactPack            │                 │
│  │  ────────────────────────────────        │                 │
│  │  • StudentProfile                        │                 │
│  │    - Education entries                   │                 │
│  │    - Experience entries                  │                 │
│  │    - Project entries                     │                 │
│  │    - Skills (categorized)                │                 │
│  │    - Links                               │                 │
│  │                                          │                 │
│  │  • BulletBank                            │                 │
│  │    - Pre-written bullets                 │                 │
│  │    - Evidence strength rating            │                 │
│  │    - Source tracking                     │                 │
│  │                                          │                 │
│  │  • AnswerLibrary                         │                 │
│  │    - Common questions                    │                 │
│  │    - Pre-filled answers                  │                 │
│  │                                          │                 │
│  │  • ProofPack                             │                 │
│  │    - Supporting links                    │                 │
│  │    - Evidence references                 │                 │
│  └─────────────┬────────────────────────────┘                 │
│                │                                                │
│                ▼                                                │
│        Structured JSON                                          │
│        └──► Return to FastAPI                                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## API Endpoints

### 1. Signup with Artifact Generation

```http
POST /api/auth/signup
Content-Type: multipart/form-data

Fields:
  - email: string (required)
  - password: string (required, min 6 chars)
  - resume: file (required, PDF)
  - work_authorization: string (optional)
  - location_preference: string (optional)
  - remote_preference: string (optional)
  - start_date: string (optional)
  - relocation: string (optional)
  - salary_expectation: string (optional)

Response:
{
  "access_token": "jwt_token",
  "token_type": "bearer",
  "user": {
    "id": "user_id",
    "email": "user@example.com",
    "artifact_id": "artifact_id",
    "has_artifact": true,
    "created_at": "2026-02-01T10:30:00"
  }
}
```

### 2. Retrieve Artifact

```http
GET /api/auth/artifact/{user_email}

Response:
{
  "user_email": "user@example.com",
  "artifact": {
    "student_profile": {...},
    "bullet_bank": [...],
    "answer_library": {...},
    "proof_pack": [...]
  },
  "created_at": "2026-02-01T10:30:00",
  "updated_at": "2026-02-01T10:30:00"
}
```

### 3. Signin (Unchanged)

```http
POST /api/auth/signin
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password"
}

Response:
{
  "access_token": "jwt_token",
  "token_type": "bearer",
  "user": {
    "id": "user_id",
    "email": "user@example.com",
    "created_at": "2026-02-01T10:30:00"
  }
}
```

## Data Flow Summary

1. **User submits signup form** → Frontend sends multipart form data
2. **FastAPI receives request** → Validates and processes
3. **Resume processing** → Saves to temp file
4. **AI Agent called** → agent.py processes PDF
5. **Artifact generation** → LLM extracts structured data
6. **Store in MongoDB** → Two collections (users + student_artifacts)
7. **Return response** → JWT token + artifact_id
8. **Future retrieval** → GET endpoint returns full artifact

## Error Handling

```
┌─────────────────────────────────────┐
│  Error Scenarios                    │
├─────────────────────────────────────┤
│  ❌ Email exists                    │
│     → 400 Bad Request                │
│                                     │
│  ❌ Password < 6 chars              │
│     → 400 Bad Request                │
│                                     │
│  ❌ No resume uploaded              │
│     → 400 Bad Request                │
│                                     │
│  ⚠️  Agent fails                    │
│     → Log error, continue signup    │
│     → User created without artifact │
│                                     │
│  ⚠️  Import error                   │
│     → agent.py not available        │
│     → Signup continues without AI   │
└─────────────────────────────────────┘
```

## Security Considerations

- ✅ Passwords hashed with bcrypt
- ✅ JWT tokens for authentication
- ✅ Resume stored as base64 in MongoDB
- ✅ Temp files cleaned up after processing
- ✅ Error logging without exposing sensitive data
- ✅ Email validation
- ✅ File type validation (PDF only)

## Performance Notes

- Resume processing is synchronous but fast (~2-5 seconds)
- Artifact generation uses efficient chunking
- Temp files automatically cleaned
- MongoDB indexes recommended on:
  - users.email
  - student_artifacts.user_email

---

**Status**: System architecture complete and documented
**Last Updated**: February 1, 2026
