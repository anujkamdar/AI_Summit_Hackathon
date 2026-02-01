# Student Artifact Integration API Documentation

## Overview
The signup process has been enhanced to generate student artifacts using AI. When a user signs up, their resume is processed by an AI agent that extracts structured information and stores it in a separate MongoDB collection.

## Updated Signup Endpoint

### POST `/api/auth/signup`

Register a new user with resume and FAQ answers. The system will automatically generate a student artifact from the resume.

#### Required Fields:
- `email` (string): User's email address
- `password` (string): Password (minimum 6 characters)
- `resume` (file): PDF resume file (required)

#### Optional FAQ Fields:
- `work_authorization` (string): Work authorization status
- `location_preference` (string): Preferred work location
- `remote_preference` (string): Remote work preference
- `start_date` (string): Available start date
- `relocation` (string): Willingness to relocate
- `salary_expectation` (string): Expected salary range

#### Example Request (using cURL):
```bash
curl -X POST "http://localhost:8000/api/auth/signup" \
  -F "email=student@example.com" \
  -F "password=securepass123" \
  -F "resume=@/path/to/resume.pdf" \
  -F "work_authorization=Authorized to work in US" \
  -F "location_preference=San Francisco Bay Area" \
  -F "remote_preference=Hybrid" \
  -F "start_date=June 2026" \
  -F "relocation=Open to relocation" \
  -F "salary_expectation=$80k-$100k"
```

#### Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "507f1f77bcf86cd799439011",
    "email": "student@example.com",
    "artifact_id": "507f1f77bcf86cd799439012",
    "has_artifact": true,
    "created_at": "2026-02-01T10:30:00"
  }
}
```

## New Endpoint: Get Student Artifact

### GET `/api/auth/artifact/{user_email}`

Retrieve the generated student artifact for a specific user.

#### Path Parameters:
- `user_email` (string): The email address of the user

#### Example Request:
```bash
curl -X GET "http://localhost:8000/api/auth/artifact/student@example.com"
```

#### Response:
```json
{
  "user_email": "student@example.com",
  "artifact": {
    "student_profile": {
      "education": [...],
      "experience": [...],
      "projects": [...],
      "skills": {...},
      "links": [...],
      "constraints": {}
    },
    "bullet_bank": [...],
    "answer_library": {...},
    "proof_pack": [...]
  },
  "created_at": "2026-02-01T10:30:00",
  "updated_at": "2026-02-01T10:30:00"
}
```

## Database Structure

### Collections:

1. **users** - User authentication and profile data
   - `email`: User email
   - `password`: Hashed password
   - `resume`: Base64 encoded resume
   - `artifact_id`: Reference to student artifact
   - `faq_answers`: Dictionary of FAQ responses
   - `created_at`: Timestamp

2. **student_artifacts** - Generated AI artifacts (separate collection)
   - `user_email`: Reference to user
   - `artifact_data`: Complete structured artifact from AI agent
   - `created_at`: Timestamp
   - `updated_at`: Timestamp

## Artifact Structure

The AI agent generates a structured artifact with:

- **Student Profile**: Education, experience, projects, skills, and links
- **Bullet Bank**: Pre-formatted bullet points with evidence strength ratings
- **Answer Library**: Common application questions and answers
- **Proof Pack**: Supporting links and references

## Error Handling

- Missing resume: Returns 400 error
- Artifact generation failure: Logs error but continues with signup
- User already exists: Returns 400 error
- Invalid credentials: Returns 401 error

## Notes

- Resume processing happens asynchronously during signup
- If artifact generation fails, the user is still created successfully
- Artifacts are stored in a separate collection for easy retrieval and updates
- All artifact operations are logged for debugging
