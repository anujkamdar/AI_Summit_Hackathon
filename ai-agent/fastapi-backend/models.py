from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from enum import Enum
from typing import List, Optional


# ============== ENUMS ==============

class JobStatus(str, Enum):
    QUEUED = "QUEUED"
    APPLYING = "APPLYING"
    SUBMITTED = "SUBMITTED"
    FAILED = "FAILED"


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
    created_at: datetime


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)


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
