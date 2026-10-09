from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class InterviewSlotCreate(BaseModel):
    start_time: datetime
    end_time: datetime


class InterviewSlotResponse(BaseModel):
    id: int
    interview_request_id: int
    start_time: datetime
    end_time: datetime
    is_selected: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InterviewRequestCreate(BaseModel):
    interview_type: str = Field(default="Company Interview")
    meeting_platform: str = Field(default="Google Meet")
    meeting_link: Optional[str] = None
    location: Optional[str] = None
    duration_minutes: int = Field(default=45, ge=15, le=180)
    notes: Optional[str] = None
    proposed_slots: List[InterviewSlotCreate] = Field(default_factory=list)


class InterviewSelectSlotRequest(BaseModel):
    slot_id: int


class InterviewRescheduleRequest(BaseModel):
    reason: str
    preferred_time: Optional[str] = None


class InterviewStatusUpdateRequest(BaseModel):
    status: str
    notes: Optional[str] = None


class InterviewFeedbackCreate(BaseModel):
    overall_score: int = Field(..., ge=0, le=100)
    technical_score: int = Field(default=75, ge=0, le=100)
    communication_score: int = Field(default=75, ge=0, le=100)
    problem_solving_score: int = Field(default=75, ge=0, le=100)
    recommendation: str = Field(default="HIRE")
    strengths: Optional[List[str]] = Field(default_factory=list)
    improvement_areas: Optional[Any] = None
    competency_breakdown: Optional[List[Dict[str, Any]]] = None
    feedback_notes: Optional[str] = None
    internal_notes: Optional[str] = None
    suggested_next_action: Optional[str] = None
    is_shared_with_candidate: bool = False


class InterviewFeedbackUpdate(BaseModel):
    overall_score: Optional[int] = Field(default=None, ge=0, le=100)
    technical_score: Optional[int] = Field(default=None, ge=0, le=100)
    communication_score: Optional[int] = Field(default=None, ge=0, le=100)
    problem_solving_score: Optional[int] = Field(default=None, ge=0, le=100)
    recommendation: Optional[str] = None
    strengths: Optional[List[str]] = None
    improvement_areas: Optional[Any] = None
    competency_breakdown: Optional[List[Dict[str, Any]]] = None
    feedback_notes: Optional[str] = None
    internal_notes: Optional[str] = None
    suggested_next_action: Optional[str] = None
    is_shared_with_candidate: Optional[bool] = None


class InterviewFeedbackShareRequest(BaseModel):
    is_shared_with_candidate: bool = True


class InterviewFeedbackResponse(BaseModel):
    id: int
    interview_id: int
    application_id: int
    interviewer_id: int
    interviewer_name: Optional[str] = None
    interviewer_email: Optional[str] = None
    overall_score: int
    technical_score: int
    communication_score: int
    problem_solving_score: int
    recommendation: str
    strengths: Optional[List[str]] = Field(default_factory=list)
    improvement_areas: Optional[Any] = None
    competency_breakdown: Optional[List[Dict[str, Any]]] = None
    feedback_notes: Optional[str] = None
    internal_notes: Optional[str] = None
    suggested_next_action: Optional[str] = None
    is_shared_with_candidate: bool
    shared_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    candidate_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ConsolidatedTeamFeedbackResponse(BaseModel):
    interview_id: int
    application_id: int
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    candidate_name: Optional[str] = None
    total_feedbacks: int = 0
    average_overall_score: float = 0.0
    average_technical_score: float = 0.0
    average_communication_score: float = 0.0
    average_problem_solving_score: float = 0.0
    recommendations_breakdown: Dict[str, int] = Field(default_factory=dict)
    top_strengths: List[str] = Field(default_factory=list)
    top_improvement_areas: List[str] = Field(default_factory=list)
    suggested_pipeline_action: Optional[str] = None
    is_shared_with_candidate: bool = False
    feedbacks: List[InterviewFeedbackResponse] = Field(default_factory=list)


class FeedbackAuditLogResponse(BaseModel):
    id: int
    action: str
    admin_id: Optional[int] = None
    details: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InterviewRequestResponse(BaseModel):
    id: int
    application_id: int
    company_id: int
    candidate_id: int
    job_id: int
    interview_type: str
    meeting_platform: str
    meeting_link: Optional[str] = None
    location: Optional[str] = None
    duration_minutes: int = 45
    notes: Optional[str] = None
    status: str
    selected_slot_id: Optional[int] = None
    scheduled_at: Optional[datetime] = None
    reschedule_reason: Optional[str] = None
    rescheduled_by: Optional[int] = None
    reschedule_preferred_time: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    job_title: Optional[str] = None
    company_name: Optional[str] = None
    company_logo_url: Optional[str] = None
    candidate_name: Optional[str] = None
    candidate_email: Optional[str] = None
    slots: List[InterviewSlotResponse] = Field(default_factory=list)
    selected_slot: Optional[InterviewSlotResponse] = None
    feedbacks_count: int = 0
    has_feedback: bool = False
    latest_feedback_score: Optional[int] = None
    is_feedback_shared: bool = False

    model_config = ConfigDict(from_attributes=True)


class PaginatedInterviewResponse(BaseModel):
    items: List[InterviewRequestResponse]
    total: int
    page: int
    size: int
    total_pages: int
    upcoming_count: int = 0
    pending_count: int = 0
    completed_count: int = 0
    cancelled_count: int = 0
