"""Pydantic schemas for Company Recruitment Dashboard (SKL-11)."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class GrowthMetric(BaseModel):
    """Percentage growth comparison metric."""
    value: str = Field(..., description="Formatted growth string, e.g. '+12%' or '-5%'")
    direction: str = Field(default="UP", description="'UP', 'DOWN', or 'NEUTRAL'")
    period: str = Field(default="vs last month", description="Comparison timeframe")


class DashboardStageBreakdown(BaseModel):
    """Pipeline candidate volume per hiring stage (SKL-11 AC-2)."""
    applied: int = Field(default=0, description="Applications in SUBMITTED or UNDER_REVIEW state")
    shortlisted: int = Field(default=0, description="Applications in SHORTLISTED state")
    interview_scheduled: int = Field(default=0, description="Candidates with scheduled/in-progress interviews")
    offered: int = Field(default=0, description="Candidates extended an offer")
    rejected: int = Field(default=0, description="Disqualified or rejected candidates")
    withdrawn: int = Field(default=0, description="Withdrawn applications")


class CompanyDashboardMetricsResponse(BaseModel):
    """Aggregated recruitment metrics for authenticated company (SKL-11 AC-1)."""
    model_config = ConfigDict(from_attributes=True)

    active_jobs: int = Field(..., description="Count of currently ACTIVE vacancies")
    total_applications: int = Field(..., description="Total candidate applications received across all postings")
    shortlisted: int = Field(..., description="Total candidates currently in SHORTLISTED stage")
    scheduled_interviews: int = Field(..., description="Total upcoming or active scheduled interviews")
    pending_reviews: int = Field(default=0, description="Applications awaiting initial recruiter screening")

    stage_breakdown: DashboardStageBreakdown = Field(
        default_factory=DashboardStageBreakdown,
        description="Comprehensive pipeline stage breakdown"
    )

    growth_indicators: Dict[str, str] = Field(
        default_factory=lambda: {
            "active_jobs_growth": "+12%",
            "applications_growth": "+24%",
            "shortlisted_growth": "+8%",
            "interviews_growth": "+15%",
        },
        description="Month-over-month growth indicators for KPI cards"
    )


class VacancyStageCounts(BaseModel):
    """Candidate volume per hiring stage for a single vacancy."""
    applied: int = 0
    shortlisted: int = 0
    interview_scheduled: int = 0
    offered: int = 0
    rejected: int = 0


class CompanyDashboardVacancyItem(BaseModel):
    """Active vacancy item with hiring stage breakdown (SKL-11 AC-2)."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    posting_type: str = "Job"
    work_mode: str = "On-site"
    location: str = "Dhaka"
    status: str = "ACTIVE"
    compensation: str
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    experience_level: Optional[str] = "Entry Level"
    category: Optional[str] = "Software Engineering"
    applications_count: int = 0
    deadline: Optional[datetime] = None
    created_at: datetime
    stages: VacancyStageCounts = Field(default_factory=VacancyStageCounts)


class CompanyDashboardVacanciesResponse(BaseModel):
    """Paginated or listed active vacancies with stage breakdowns."""
    items: List[CompanyDashboardVacancyItem]
    total: int
    active_count: int


class CandidateActivityEvent(BaseModel):
    """Chronological event stream item for candidate activity feed (SKL-11 AC-3)."""
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Unique event identifier")
    type: str = Field(
        ...,
        description="Event type: APPLICATION_SUBMITTED, APPLICATION_SHORTLISTED, INTERVIEW_ACCEPTED, INTERVIEW_SCHEDULED, etc."
    )
    candidate_id: int
    candidate_name: str
    candidate_initials: str
    candidate_email: Optional[str] = None
    job_id: int
    job_title: str
    status: str = Field(..., description="Status pill label, e.g. 'Applied', 'Shortlisted', 'Scheduled'")
    timestamp: datetime
    description: str = Field(..., description="Human-readable event summary, e.g. 'Applied for Junior Software Developer'")
    application_id: Optional[int] = None
    interview_id: Optional[int] = None


class CompanyDashboardActivityResponse(BaseModel):
    """Activity feed stream response."""
    items: List[CandidateActivityEvent]
    total: int


class CompanyDashboardProfileStatusResponse(BaseModel):
    """Status details for recruiter overview and verification alert banner (SKL-11 AC-4)."""
    model_config = ConfigDict(from_attributes=True)

    company_id: int
    user_id: int
    company_name: str
    verification_status: str = Field(..., description="'PENDING', 'APPROVED', or 'REJECTED'")
    is_verified: bool = Field(..., description="True if verification_status == 'APPROVED'")
    requires_verification: bool = Field(
        ...,
        description="True if unverified, signaling frontend to render persistent alert banner"
    )
    verification_notes: Optional[str] = None
    trade_license_url: Optional[str] = None
    has_submitted_dossier: bool = False
    profile_complete: bool = False
    industry: Optional[str] = "Technology Company"
    location: Optional[str] = "Dhaka, Bangladesh"
    company_size: Optional[str] = None
    office_address: Optional[str] = None
    website_url: Optional[str] = None
    logo_url: Optional[str] = None
    banner_url: Optional[str] = None
    active_jobs_count: int = 0
    total_applications_count: int = 0


class CompanyDashboardUpcomingInterviewItem(BaseModel):
    """Upcoming interview session for the dashboard card."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    application_id: int
    candidate_id: int
    candidate_name: str
    candidate_initials: str
    job_id: int
    job_title: str
    interview_type: str = "Technical Interview"
    meeting_platform: str = "Google Meet"
    meeting_link: Optional[str] = None
    location: Optional[str] = None
    duration_minutes: int = 45
    scheduled_at: Optional[datetime] = None
    status: str = "SCHEDULED"
    notes: Optional[str] = None
