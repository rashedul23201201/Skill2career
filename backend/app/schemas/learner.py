from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class LearnerProfileUpdateRequest(BaseModel):
    """Schema for updating learner profile fields (SKL-51)."""
    phone_number: Optional[str] = Field(default=None, max_length=50, description="Contact phone number")
    location: Optional[str] = Field(default=None, max_length=150, description="City, Country")
    bio: Optional[str] = Field(default=None, max_length=2000, description="Personal bio and career objectives")
    target_role: Optional[str] = Field(default=None, max_length=100, description="Target career role (e.g. Backend Developer)")
    primary_track: Optional[str] = Field(default=None, max_length=100, description="Primary focus track")
    institution: Optional[str] = Field(default=None, max_length=150, description="College or University")
    department: Optional[str] = Field(default=None, max_length=150, description="Department or Degree major")
    skills: Optional[List[str]] = Field(default=None, description="List of competency skills")
    portfolio_links: Optional[Dict[str, Any]] = Field(default=None, description="Links to GitHub, LinkedIn, portfolio, etc.")

    model_config = ConfigDict(extra="ignore")


class CompletionSectionStatus(BaseModel):
    """Status breakdown of an individual completion section."""
    label: str
    weight: int
    is_complete: bool
    description: str


class ProfileCompletionBreakdown(BaseModel):
    """Transparent 4-tier completion rubric (SKL-51)."""
    percentage: int
    basic_info: CompletionSectionStatus
    education: CompletionSectionStatus
    career_skills: CompletionSectionStatus
    resume: CompletionSectionStatus


class LearnerProfileResponse(BaseModel):
    """Serialized Learner Profile response."""
    id: int
    user_id: int
    email: str
    first_name: str
    last_name: str
    role: str
    is_verified: bool
    phone_number: Optional[str] = None
    location: Optional[str] = None
    bio: Optional[str] = None
    target_role: Optional[str] = None
    primary_track: Optional[str] = None
    institution: Optional[str] = None
    department: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    resume_url: Optional[str] = None
    resume_filename: Optional[str] = None
    portfolio_links: Dict[str, Any] = Field(default_factory=dict)
    completion_pct: int = 25
    completion_breakdown: Optional[ProfileCompletionBreakdown] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ResumeUploadResponse(BaseModel):
    """Response returned upon resume document upload."""
    message: str
    resume_url: str
    resume_filename: str
    completion_pct: int
    completion_breakdown: Optional[ProfileCompletionBreakdown] = None
