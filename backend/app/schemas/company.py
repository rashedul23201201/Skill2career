import re
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict, field_validator


URL_REGEX = re.compile(
    r"^https?://"  # http:// or https://
    r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # domain...
    r"localhost|"  # localhost...
    r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
    r"(?::\d+)?"  # optional port
    r"(?:/?|[/?]\S+)$",
    re.IGNORECASE
)


def validate_url_syntax(v: Optional[str]) -> Optional[str]:
    """Validate standard HTTP/HTTPS URI syntax."""
    if v is None:
        return None
    cleaned = v.strip()
    if not cleaned:
        return None
    if not URL_REGEX.match(cleaned):
        raise ValueError(
            f"Invalid URL format: '{v}'. Must be a valid HTTP/HTTPS URI (e.g., https://example.com or https://company.com/profile)."
        )
    return cleaned


class CompanyProfileUpdateRequest(BaseModel):
    """Schema for updating company profile fields (SKL-3)."""
    company_name: Optional[str] = Field(default=None, max_length=150, description="Official company trade name")
    tagline: Optional[str] = Field(default=None, max_length=255, description="Brief corporate tagline")
    description: Optional[str] = Field(default=None, max_length=5000, description="Detailed company overview and mission")
    industry: Optional[str] = Field(default=None, max_length=100, description="Industry sector (e.g. Software & IT, Fintech)")
    company_size: Optional[str] = Field(default=None, max_length=50, description="Company size range (e.g. 1-10, 11-50, 51-200, 201-500, 500+)")
    contact_person: Optional[str] = Field(default=None, max_length=100, description="Primary representative or hiring lead")
    contact_phone: Optional[str] = Field(default=None, max_length=50, description="Corporate contact phone number")
    website_url: Optional[str] = Field(default=None, max_length=255, description="Company official website URL")
    office_address: Optional[str] = Field(default=None, max_length=255, description="Physical headquarters / office address")
    social_links: Optional[Dict[str, Optional[str]]] = Field(
        default=None,
        description="Dictionary of verified social profiles (linkedin, facebook, twitter, github)"
    )

    model_config = ConfigDict(extra="ignore")

    @field_validator("website_url")
    @classmethod
    def validate_website(cls, v: Optional[str]) -> Optional[str]:
        return validate_url_syntax(v)

    @field_validator("social_links")
    @classmethod
    def validate_socials(cls, v: Optional[Dict[str, Optional[str]]]) -> Optional[Dict[str, Optional[str]]]:
        if not v:
            return v
        cleaned = {}
        for platform, url in v.items():
            if url:
                valid_url = validate_url_syntax(url)
                cleaned[platform.lower().strip()] = valid_url
            else:
                cleaned[platform.lower().strip()] = None
        return cleaned


class CompanyProfileResponse(BaseModel):
    """Serialized Company Profile response for authenticated company or admin (SKL-3)."""
    id: int
    user_id: int
    email: str
    company_name: str
    tagline: Optional[str] = None
    description: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    website_url: Optional[str] = None
    office_address: Optional[str] = None
    logo_url: Optional[str] = None
    banner_url: Optional[str] = None
    social_links: Optional[Dict[str, Any]] = Field(default_factory=dict)
    trade_license_url: Optional[str] = None
    verification_status: str = "PENDING"
    is_verified: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PublicCompanyProfileResponse(BaseModel):
    """
    Sanitized public view of Company Profile for Learners and Guests (SKL-3).
    Omits internal contact person, phone, and trade license documents for privacy & security.
    """
    id: int
    company_name: str
    tagline: Optional[str] = None
    description: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    location: Optional[str] = None
    office_address: Optional[str] = None
    website_url: Optional[str] = None
    logo_url: Optional[str] = None
    banner_url: Optional[str] = None
    social_links: Optional[Dict[str, Any]] = Field(default_factory=dict)
    verification_status: str = "PENDING"
    is_verified: bool = False
    active_jobs: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AssetUploadResponse(BaseModel):
    """Response returned upon company branding asset upload (logo or cover banner)."""
    message: str
    asset_url: str
    asset_type: str
    filename: str


class CompanyModerationRequest(BaseModel):
    """Schema for administrative company content moderation (SKL-3 / SKL-50)."""
    action: Optional[str] = Field(default=None, description="Moderation action: e.g. APPROVE, REJECT, SUSPEND, UPDATE")
    notes: Optional[str] = Field(default=None, description="Administrative audit remarks or moderation feedback")
    verification_status: Optional[str] = Field(default=None, description="PENDING, APPROVED, or REJECTED")
    is_verified: Optional[bool] = Field(default=None, description="Boolean verification flag override")
    tagline: Optional[str] = Field(default=None, description="Moderated tagline")
    description: Optional[str] = Field(default=None, description="Moderated description")

    model_config = ConfigDict(extra="ignore")
