from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum


class Job(BaseModel):
    skill_fit: int
    experience_fit: int


class EvidenceStrength(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"


class ResumeReference(BaseModel):
    page: int = Field(..., description="Page number in resume PDF")
    section: str = Field(..., description="Section name if identifiable")


class EducationEntry(BaseModel):
    institution: str
    degree: str
    dates: str
    reference: ResumeReference


class ExperienceEntry(BaseModel):
    role: str
    organization: str
    dates: str
    description: str
    reference: ResumeReference


class ProjectEntry(BaseModel):
    name: str
    description: str
    technologies: List[str] = Field(default_factory=list)
    reference: ResumeReference


class Skills(BaseModel):
    languages: List[str] = Field(default_factory=list)
    frameworks: List[str] = Field(default_factory=list)
    tools: List[str] = Field(default_factory=list)
    other: List[str] = Field(default_factory=list)


class BulletEntry(BaseModel):
    bullet: str
    source: str
    evidence_strength: EvidenceStrength
    reference: ResumeReference


class ProofEntry(BaseModel):
    link: str
    supports: List[str] = Field(default_factory=list)


class AnswerLibrary(BaseModel):
    work_authorization: str = "Not specified by student"
    location_preference: str = "Not specified by student"
    remote_preference: str = "Not specified by student"
    start_date: str = "Not specified by student"
    relocation: str = "Not specified by student"
    salary_expectation: str = "Not specified by student"


class StudentProfile(BaseModel):
    education: List[EducationEntry] = Field(default_factory=list)
    experience: List[ExperienceEntry] = Field(default_factory=list)
    projects: List[ProjectEntry] = Field(default_factory=list)
    skills: Skills = Skills()
    links: List[str] = Field(default_factory=list)
    constraints: dict = Field(default_factory=dict)


class UserArtifactPack(BaseModel):
    student_profile: StudentProfile
    bullet_bank: List[BulletEntry] = Field(default_factory=list)
    answer_library: AnswerLibrary
    proof_pack: List[ProofEntry] = Field(default_factory=list)
