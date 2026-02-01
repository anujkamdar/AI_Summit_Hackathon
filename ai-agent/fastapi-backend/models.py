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
