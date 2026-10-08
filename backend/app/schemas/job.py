from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field, ConfigDict, field_validator
from app.models.job import JobPostingType, JobWorkMode, JobStatus, JobExperienceLevel


def _coerce_enum(enum_cls: Any, val: Any) -> Any:
    if val is None or isinstance(val, enum_cls):
        return val
    val_str = str(val).strip().replace("-", "_").lower()
    for member in enum_cls:
        if (
            member.value.lower() == str(val).strip().lower()
            or member.name.lower() == val_str
            or member.value.lower().replace("-", "_") == val_str
        ):
            return member
    return val


class JobPostingCreateRequest(BaseModel):
    """Request payload to author a job or internship vacancy (SKL-4)."""
    title: str = Field(min_length=3, max_length=200, description="Title of the role")
    posting_type: JobPostingType = Field(default=JobPostingType.JOB, description="Type: Job or Internship")
    work_mode: JobWorkMode = Field(default=JobWorkMode.ON_SITE, description="Work mode: On-site, Remote, Hybrid")
    location: str = Field(min_length=2, max_length=150, default="Dhaka", description="Work location")
    description: str = Field(min_length=10, description="Comprehensive role overview and expectations")
    requirements: str = Field(min_length=5, description="Required competencies, degrees, or qualifications")
    skills: Optional[List[str]] = Field(default=[], description="List of required key skills/tags")
    compensation: str = Field(min_length=2, max_length=100, description="Salary bracket or stipend range")
    duration: Optional[str] = Field(default=None, max_length=100, description="Internship duration (e.g. 3 Months)")
    experience_level: JobExperienceLevel = Field(default=JobExperienceLevel.ENTRY_LEVEL, description="Seniority level")
    category: str = Field(default="Software Engineering", min_length=2, max_length=100, description="Domain category")
    deadline: Optional[datetime] = Field(default=None, description="Application closing timestamp")
    status: JobStatus = Field(default=JobStatus.ACTIVE, description="Initial publication status")

    model_config = ConfigDict(extra="ignore")

    @field_validator("posting_type", mode="before")
    @classmethod
    def validate_posting_type(cls, v: Any) -> Any:
        return _coerce_enum(JobPostingType, v)

    @field_validator("work_mode", mode="before")
    @classmethod
    def validate_work_mode(cls, v: Any) -> Any:
        return _coerce_enum(JobWorkMode, v)

    @field_validator("experience_level", mode="before")
    @classmethod
    def validate_experience_level(cls, v: Any) -> Any:
        return _coerce_enum(JobExperienceLevel, v)

    @field_validator("status", mode="before")
    @classmethod
    def validate_status(cls, v: Any) -> Any:
        return _coerce_enum(JobStatus, v)


class JobPostingUpdateRequest(BaseModel):
    """Request payload to update an existing vacancy (SKL-4)."""
    title: Optional[str] = Field(default=None, min_length=3, max_length=200)
    posting_type: Optional[JobPostingType] = None
    work_mode: Optional[JobWorkMode] = None
    location: Optional[str] = Field(default=None, min_length=2, max_length=150)
    description: Optional[str] = Field(default=None, min_length=10)
    requirements: Optional[str] = Field(default=None, min_length=5)
    skills: Optional[List[str]] = None
    compensation: Optional[str] = Field(default=None, min_length=2, max_length=100)
    duration: Optional[str] = None
    experience_level: Optional[JobExperienceLevel] = None
    category: Optional[str] = Field(default=None, min_length=2, max_length=100)
    deadline: Optional[datetime] = None
    status: Optional[JobStatus] = None

    model_config = ConfigDict(extra="ignore")

    @field_validator("posting_type", mode="before")
    @classmethod
    def validate_posting_type(cls, v: Any) -> Any:
        return _coerce_enum(JobPostingType, v)

    @field_validator("work_mode", mode="before")
    @classmethod
    def validate_work_mode(cls, v: Any) -> Any:
        return _coerce_enum(JobWorkMode, v)

    @field_validator("experience_level", mode="before")
    @classmethod
    def validate_experience_level(cls, v: Any) -> Any:
        return _coerce_enum(JobExperienceLevel, v)

    @field_validator("status", mode="before")
    @classmethod
    def validate_status(cls, v: Any) -> Any:
        return _coerce_enum(JobStatus, v)


class JobPostingStatusUpdateRequest(BaseModel):
    """Request payload for updating vacancy lifecycle or admin moderation (SKL-4 AC-3, AC-5)."""
    status: JobStatus
    reason: Optional[str] = Field(default=None, max_length=500, description="Administrative or recruiter note")


class JobPostingResponse(BaseModel):
    """Card and catalog representation of a vacancy matching Jobs and internships.png."""
    id: int
    company_id: int
    company_name: str
    company_logo_url: Optional[str] = None
    company_location: Optional[str] = None
    company_industry: Optional[str] = None
    company_website: Optional[str] = None
    title: str
    posting_type: str
    work_mode: str
    location: str
    description: str
    requirements: str
    skills: Optional[List[str]] = []
    compensation: str
    duration: Optional[str] = None
    experience_level: str
    category: str
    deadline: Optional[datetime] = None
    status: str
    applications_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaginatedJobPostingResponse(BaseModel):
    """Paginated collection of job postings."""
    items: List[JobPostingResponse]
    total: int
    page: int
    size: int
    total_pages: int
