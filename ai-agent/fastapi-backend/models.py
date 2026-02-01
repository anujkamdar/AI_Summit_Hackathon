from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from enum import Enum
from typing import List, Optional


# ============== ENUMS ==============

class JobStatus(str, Enum):
    IN_PROGRESS = "IN_PROGRESS"
    APPLYING = "APPLYING"
    SUBMITTED = "SUBMITTED"
    FAILED = "FAILED"
    RETRYING = "RETRYING"
    SKIPPED = "SKIPPED"


class LogType(str, Enum):
    info = "info"
    success = "success"
    error = "error"


# ============== JOB MODELS ==============

class Job(BaseModel):
    id: str
    company: str
    role: str
    match_score: int = Field(..., ge=0, le=100)
    status: JobStatus
    timestamp: datetime


# ============== LOG MODELS ==============

class Log(BaseModel):
    time: datetime
    type: LogType
    msg: str
    user_email: Optional[str] = None


# ============== USER MODELS ==============

class User(BaseModel):
    id: str
    email: EmailStr
    resume: Optional[str] = None  # Base64 encoded resume or file path
    artifact_id: Optional[str] = None  # Reference to student artifact
    created_at: datetime


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    work_authorization: Optional[str] = None
    location_preference: Optional[str] = None
    remote_preference: Optional[str] = None
    start_date: Optional[str] = None
    relocation: Optional[str] = None
    salary_expectation: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class UserMetrics(BaseModel):
    user_email: str
    total_jobs: int
    applied_jobs: int
    failed_jobs: int
    success_rate: str
    recent_jobs: List[dict]


# ============== STUDENT ARTIFACT MODELS ==============

class StudentArtifact(BaseModel):
    user_email: EmailStr
    artifact_data: dict  # The complete artifact from agent.py
    created_at: datetime
    updated_at: datetime


# ============== JOB RANKING & QUEUE MODELS ==============

class JobListing(BaseModel):
    id: Optional[str] = None
    title: str
    company: str
    location: str
    type: str = "Full-time"
    salary: Optional[str] = None
    description: str
    requiredSkills: List[str] = Field(default_factory=list)
    visa_sponsorship: bool = False
    createdAt: Optional[datetime] = None


class RankedJob(BaseModel):
    job_id: str
    title: str
    company: str
    location: str
    match_score: float = Field(..., ge=0, le=100, description="Relevance score 0-100")
    matched_skills: List[str] = Field(default_factory=list)
    description: str
    salary: Optional[str] = None


class RankingRequest(BaseModel):
    max_results: int = Field(50, ge=1, le=100, description="Maximum jobs to rank")


class RankingResponse(BaseModel):
    user_email: EmailStr
    ranked_jobs: List[RankedJob]
    total_jobs: int
    timestamp: datetime


class JobQueueItem(BaseModel):
    id: Optional[str] = None
    user_email: EmailStr
    job_id: str
    job_title: str
    company: str
    match_score: float
    status: JobStatus = JobStatus.IN_PROGRESS
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    cover_letter: Optional[str] = None  # For future auto-apply
    error_message: Optional[str] = None


class QueueStatusResponse(BaseModel):
    user_email: EmailStr
    total_in_queue: int
    by_status: dict
    jobs: List[JobQueueItem]


class ApplyResponse(BaseModel):
    """Response model for job application endpoint"""
    queue_item_id: str
    job_id: str
    job_title: str
    company: str
    status: JobStatus
    cover_letter: str
    message: str
    applied_at: datetime
