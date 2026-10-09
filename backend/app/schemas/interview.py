from datetime import datetime
from typing import Optional, List
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
