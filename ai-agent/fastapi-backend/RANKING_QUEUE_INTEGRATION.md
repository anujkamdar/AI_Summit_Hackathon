# Ranking Agent & Queue System Integration

## Overview
This document describes the integration of the ranking agent, job queue system, and **Application Agent (auto-apply)** into the FastAPI backend.

## What's Been Integrated

### 1. Ranking Agent (`agent.py`)
The `Ranking_agent` function uses MongoDB vector search with HuggingFace embeddings to find the most relevant jobs for a student based on their artifact (resume data).

**How it works:**
- Takes student artifact (parsed resume data) as input
- Converts artifact to text and generates embeddings
- Performs vector similarity search in MongoDB jobs collection
- Returns top matching jobs ranked by relevance

### 2. Job Queue System
A complete queue management system for tracking job applications.

**Features:**
- Add individual jobs to queue
- Batch add multiple jobs
- View queue status
- Update job status (IN_PROGRESS, APPLYING, SUBMITTED, FAILED, etc.)
- Remove jobs from queue

### 3. Application Agent (Auto-Apply) ✅ NEW
The `Application_agent` generates tailored cover letters for job applications.

**How it works:**
- Takes job listing and student artifact as input
- Uses Groq LLM (llama-3.3-70b-versatile) to generate personalized cover letter
- Grounds all claims in the student's actual resume data (no hallucination)
- Returns a tailored cover letter paragraph for the specific role

## New API Endpoints

All endpoints require authentication (JWT token).

### 1. Rank Jobs
```
POST /api/jobs/rank
```

**Request Body:**
```json
{
  "user_email": "user@example.com",
  "artifact_id": "optional-artifact-id",
  "max_results": 50
}
```

**Response:**
```json
{
  "user_email": "user@example.com",
  "ranked_jobs": [
    {
      "job_id": "123",
      "title": "Software Engineer",
      "company": "TechCorp",
      "location": "San Francisco, CA",
      "match_score": 85.5,
      "matched_skills": ["Python", "FastAPI", "React"],
      "description": "Job description...",
      "salary": "$120k - $180k"
    }
  ],
  "total_jobs": 25,
  "timestamp": "2026-02-01T10:00:00Z"
}
```

### 2. Add Job to Queue
```
POST /api/jobs/queue/add?job_id=123&match_score=85.5
```

**Response:**
```json
{
  "message": "Job added to queue successfully",
  "queue_item_id": "queue-item-id"
}
```

### 3. Add Multiple Jobs to Queue
```
POST /api/jobs/queue/add-batch
```

**Request Body:**
```json
{
  "jobs": [
    {"job_id": "123", "match_score": 85.5},
    {"job_id": "456", "match_score": 78.2}
  ]
}
```

**Response:**
```json
{
  "message": "Batch operation completed",
  "added": 15,
  "skipped": 5
}
```

### 4. Get Queue Status
```
GET /api/jobs/queue/status
```

**Response:**
```json
{
  "user_email": "user@example.com",
  "total_in_queue": 10,
  "by_status": {
    "IN_PROGRESS": 5,
    "SUBMITTED": 3,
    "FAILED": 2
  },
  "jobs": [
    {
      "id": "queue-item-id",
      "user_email": "user@example.com",
      "job_id": "123",
      "job_title": "Software Engineer",
      "company": "TechCorp",
      "match_score": 85.5,
      "status": "IN_PROGRESS",
      "created_at": "2026-02-01T10:00:00Z",
      "updated_at": "2026-02-01T10:00:00Z",
      "cover_letter": null,
      "error_message": null
    }
  ]
}
```

### 5. Update Queue Item Status
```
PATCH /api/jobs/queue/{queue_item_id}/status?new_status=SUBMITTED
```

**Response:**
```json
{
  "message": "Queue item status updated successfully"
}
```

### 6. Remove from Queue
```
DELETE /api/jobs/queue/{queue_item_id}
```

**Response:**
```json
{
  "message": "Job removed from queue successfully"
}
```

### 7. Apply to Single Job ✅ NEW
```
POST /api/jobs/queue/{queue_item_id}/apply
```

**Description:** Generates a tailored cover letter using the Application Agent and marks job as applied.

**Response:**
```json
{
  "queue_item_id": "queue-item-id",
  "job_id": "job-123",
  "job_title": "Software Engineer",
  "company": "TechCorp",
  "status": "SUBMITTED",
  "cover_letter": "I am excited to apply for the Software Engineer position at TechCorp. Based on my experience with Python and FastAPI...",
  "message": "Successfully generated cover letter and applied to job",
  "applied_at": "2026-02-02T10:00:00Z"
}
```

### 8. Batch Apply to Multiple Jobs ✅ NEW
```
POST /api/jobs/queue/apply-batch
```

**Request Body:**
```json
{
  "queue_item_ids": ["id1", "id2", "id3"]
}
```

**Response:**
```json
{
  "message": "Batch application completed",
  "total_processed": 3,
  "successful_count": 2,
  "failed_count": 1,
  "skipped_count": 0,
  "results": {
    "successful": [
      {
        "queue_item_id": "id1",
        "job_id": "job-123",
        "job_title": "Software Engineer",
        "company": "TechCorp"
      }
    ],
    "failed": [
      {
        "queue_item_id": "id3",
        "error": "Job listing not found"
      }
    ],
    "skipped": []
  }
}
```

## New Models Added

### JobQueueItem
Represents a job in the user's application queue.

### RankingRequest/Response
For requesting and receiving ranked jobs.

### RankedJob
A job with match score and matched skills.

### QueueStatusResponse
Complete queue status for a user.

## Database Collections Used

### `artifacts`
Stores user resume artifacts generated by the artifact agent.

### `jobs`
Stores available job listings (needs vector embeddings for search).

### `job_queue`
Stores user's job application queue items.

## Required Environment Variables

Make sure `.env` file contains:
```
MONGO_URI=mongodb+srv://your-connection-string
GROQ_API_KEY=your-groq-api-key
```

## Installation

Install new dependencies:
```bash
pip install -r requirements.txt
```

This will install:
- `agno` - Agent framework
- `sentence-transformers` - For embeddings
- `torch` - Required by transformers
- `transformers` - NLP models
- `pymongo` - MongoDB sync client

## Usage Flow

1. **User uploads resume** → Artifact is generated and stored
2. **User requests job ranking** → Ranking agent finds best matches
3. **User adds jobs to queue** → Jobs are queued for application
4. **User monitors queue** → Check status of applications
5. **Manual/Auto application** → Jobs are applied to (auto-apply not yet integrated)

## What's NOT Integrated

- **Automated application submission to external portals**: The system generates cover letters but does not submit to external job portals (requires portal-specific integrations)

## Application Agent Details

### How the Application Agent Works

1. **Input**: Job listing (title, company, description, required skills) + Student artifact (resume data)
2. **Processing**: Groq LLM generates a tailored cover letter grounded ONLY in resume facts
3. **Output**: Personalized cover letter paragraph

### Safety Rules
- **ZERO HALLUCINATION**: Never invents experience, numbers, titles, or achievements
- **GROUNDING**: Every claim must be traceable to the student's artifact
- **TRUTHFULNESS**: Prioritizes accuracy over persuasion

### Example Usage Flow
1. User calls `/api/jobs/rank` → Gets list of matched jobs
2. User adds jobs to queue via `/api/jobs/queue/add-batch`
3. User views queue via `/api/jobs/queue/status`
4. User applies to job via `/api/jobs/queue/{id}/apply` → Application Agent generates cover letter
5. Queue item status updates to SUBMITTED with cover letter stored

## Testing

Start the server:
```bash
cd ai-agent/fastapi-backend
uvicorn main:app --reload
```

Test ranking endpoint:
```bash
curl -X POST "http://localhost:8000/api/jobs/rank" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"user_email": "test@example.com", "max_results": 10}'
```

## Notes

- The ranking agent uses HuggingFace embeddings which may take time on first load (model download)
- MongoDB must have a vector index on the jobs collection for efficient search
- Match scores are calculated based on vector similarity (0-100 scale)
- Queue system is ready for future automation integration
