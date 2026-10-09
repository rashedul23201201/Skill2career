from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class ApplicationCreateRequest(BaseModel):
    resume_url: Optional[str] = None
    resume_filename: Optional[str] = None
    cover_letter: Optional[str] = None
    screening_answers: Optional[Dict[str, Any]] = Field(default_factory=dict)
    use_profile_resume: bool = False


class ApplicationStatusUpdateRequest(BaseModel):
    status: str
    notes: Optional[str] = None


class JobApplicationResponse(BaseModel):
    id: int
    job_id: int
    learner_id: int
    resume_url: Optional[str] = None
    resume_filename: Optional[str] = None
    cover_letter: Optional[str] = None
    screening_answers: Optional[Dict[str, Any]] = None
    screening_score: int = 0
    deal_breaker_passed: bool = True
    deal_breaker_failed_reason: Optional[str] = None
    status: str
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None
    applied_at: datetime
    created_at: datetime
    updated_at: datetime

    job_title: Optional[str] = None
    company_name: Optional[str] = None
    company_logo_url: Optional[str] = None
    location: Optional[str] = None
    work_mode: Optional[str] = None
    compensation: Optional[str] = None
    posting_type: Optional[str] = None
    candidate_name: Optional[str] = None
    candidate_email: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PaginatedApplicationResponse(BaseModel):
    items: List[JobApplicationResponse]
    total: int
    page: int
    size: int
    total_pages: int
    active_count: int = 0
    submitted_count: int = 0
    under_review_count: int = 0
    shortlisted_count: int = 0
    interview_count: int = 0
    offered_count: int = 0
    withdrawn_count: int = 0
    rejected_count: int = 0


class ApplicationCheckResponse(BaseModel):
    has_applied: bool
    application: Optional[JobApplicationResponse] = None
