from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field, HttpUrl, ConfigDict


class CompanyVerificationRequest(BaseModel):
    """Payload for submitting or updating company verification dossier (SKL-2)."""
    company_name: Optional[str] = Field(None, min_length=2, max_length=150, description="Official registered company name")
    trade_license_url: str = Field(..., min_length=5, max_length=255, description="URL or reference to uploaded official trade license")
    registration_number: Optional[str] = Field(None, max_length=100, description="Government or corporate registration / TIN / BIN number")
    industry: Optional[str] = Field(None, max_length=100, description="Industry sector")
    location: Optional[str] = Field(None, max_length=150, description="Operating city / country")
    company_size: Optional[str] = Field(None, max_length=50, description="Team size bracket")
    website_url: Optional[str] = Field(None, max_length=255, description="Official company website")
    office_address: Optional[str] = Field(None, max_length=255, description="Physical office address")
    contact_person: Optional[str] = Field(None, max_length=100, description="Designated hiring / verification representative")
    contact_phone: Optional[str] = Field(None, max_length=50, description="Official contact phone number")
    description: Optional[str] = Field(None, description="Company overview and mission")


class CompanyVerificationStatusResponse(BaseModel):
    """Status details for authenticated company's verification dossier (SKL-2)."""
    model_config = ConfigDict(from_attributes=True)

    company_id: int
    user_id: int
    company_name: str
    is_verified: bool
    verification_status: str  # PENDING, APPROVED, REJECTED
    trade_license_url: Optional[str] = None
    registration_number: Optional[str] = None
    industry: Optional[str] = None
    location: Optional[str] = None
    company_size: Optional[str] = None
    website_url: Optional[str] = None
    office_address: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    description: Optional[str] = None
    verified_at: Optional[datetime] = None
    verified_by_admin_id: Optional[int] = None
    verification_notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class AdminCompanyVerificationAction(BaseModel):
    """Payload for Admin review approval or rejection of company verification (SKL-2)."""
    action: Literal["APPROVE", "REJECT"] = Field(..., description="Decision action: APPROVE or REJECT")
    notes: Optional[str] = Field(None, max_length=1000, description="Feedback or reason for decision")


class PendingCompanyVerificationItem(BaseModel):
    """Item structure for Admin pending company verifications list (SKL-2)."""
    model_config = ConfigDict(from_attributes=True)

    company_id: int
    user_id: int
    email: str
    company_name: str
    trade_license_url: Optional[str] = None
    registration_number: Optional[str] = None
    industry: Optional[str] = None
    location: Optional[str] = None
    company_size: Optional[str] = None
    website_url: Optional[str] = None
    office_address: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    verification_status: str
    verification_notes: Optional[str] = None
    submitted_at: Optional[datetime] = None


class JobCreateRequest(BaseModel):
    """Simulated job post request for testing gatekeeper authorization (SKL-2)."""
    title: str = Field(..., min_length=3, max_length=150)
    description: str = Field(..., min_length=10)
    job_type: Optional[str] = Field("Full-time", max_length=50)
    location: Optional[str] = Field("Dhaka, Bangladesh", max_length=100)
    salary_range: Optional[str] = Field(None, max_length=100)
