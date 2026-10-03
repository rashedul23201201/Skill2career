from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, ConfigDict


class InstructorApplicationRequest(BaseModel):
    """Payload for submitting an instructor onboarding application (SKL-52)."""
    designation: Optional[str] = Field(default=None, max_length=100, description="Current professional title")
    institution: Optional[str] = Field(default=None, max_length=150, description="University, Institute or Company")
    qualification: Optional[str] = Field(default=None, max_length=150, description="Highest academic degree or credential")
    expertise_domain: Optional[str] = Field(default=None, max_length=150, description="Primary domain of teaching expertise")
    years_experience: Optional[str] = Field(default=None, max_length=50, description="Years of professional or teaching experience")
    certificates: Optional[Union[List[str], Dict[str, Any], str]] = Field(default=None, description="Certificates or credentials list/json")
    intro_video_url: Optional[str] = Field(default=None, max_length=255, description="Link to introduction or sample lecture video")
    bio: Optional[str] = Field(default=None, description="Detailed instructor biography and teaching philosophy")
    linkedin_url: Optional[str] = Field(default=None, max_length=255, description="LinkedIn profile or public portfolio link")


class InstructorProfileUpdateRequest(BaseModel):
    """Payload for updating an existing instructor profile (SKL-52)."""
    designation: Optional[str] = Field(default=None, max_length=100)
    institution: Optional[str] = Field(default=None, max_length=150)
    qualification: Optional[str] = Field(default=None, max_length=150)
    expertise_domain: Optional[str] = Field(default=None, max_length=150)
    years_experience: Optional[str] = Field(default=None, max_length=50)
    certificates: Optional[Union[List[str], Dict[str, Any], str]] = None
    intro_video_url: Optional[str] = Field(default=None, max_length=255)
    bio: Optional[str] = None
    linkedin_url: Optional[str] = Field(default=None, max_length=255)


class InstructorProfileResponse(BaseModel):
    """Serialized Instructor profile representation."""
    id: int
    user_id: int
    email: str
    first_name: str
    last_name: str
    role: str
    is_verified: bool
    designation: Optional[str] = None
    institution: Optional[str] = None
    qualification: Optional[str] = None
    expertise_domain: Optional[str] = None
    years_experience: Optional[str] = None
    certificates: Optional[Any] = None
    intro_video_url: Optional[str] = None
    bio: Optional[str] = None
    linkedin_url: Optional[str] = None
    onboarding_status: str = "PENDING_REVIEW"
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InstructorStatusUpdateRequest(BaseModel):
    """Admin payload to approve, reject, or suspend an instructor account."""
    status: str = Field(..., description="Target onboarding status: APPROVED, REJECTED, SUSPENDED, PENDING_REVIEW")
    reason: Optional[str] = Field(default=None, max_length=500, description="Optional administrative notes or rejection reason")


class InstructorDashboardStats(BaseModel):
    """Instructor telemetry for dashboard (SKL-52)."""
    active_courses: int = 0
    total_learners: int = 0
    mock_tests: int = 0
    upcoming_interviews: int = 0
    onboarding_status: str = "PENDING_REVIEW"
    profile: Optional[InstructorProfileResponse] = None
