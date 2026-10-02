from datetime import datetime
from typing import Optional, Generic, TypeVar, List
from pydantic import BaseModel, EmailStr, Field, ConfigDict, model_validator
from typing import Optional, Generic, TypeVar, List, Any
from app.models.user import UserRole

T = TypeVar("T")


class UserRegisterRequest(BaseModel):
    """Schema for user registration supporting common and role-specific fields."""
    email: EmailStr
    password: str = Field(min_length=8, description="Password must be at least 8 characters long")
    first_name: Optional[str] = Field(default="User", max_length=100)
    last_name: str = Field(default="", max_length=100)
    full_name: Optional[str] = Field(default=None, max_length=200)
    role: UserRole = Field(default=UserRole.LEARNER, description="User role in the ecosystem")

    @model_validator(mode="before")
    @classmethod
    def populate_name_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if data.get("full_name") and not data.get("first_name"):
                parts = data["full_name"].strip().split(" ", 1)
                data["first_name"] = parts[0]
                data["last_name"] = parts[1] if len(parts) > 1 else ""
        return data

    # Learner-specific registration fields (Learner reg.png)
    institution: Optional[str] = Field(default=None, max_length=150)
    department: Optional[str] = Field(default=None, max_length=150)
    target_role: Optional[str] = Field(default=None, max_length=100)

    # Instructor-specific registration fields (Instructor reg.png)
    qualification: Optional[str] = Field(default=None, max_length=150)
    expertise: Optional[str] = Field(default=None, max_length=150)
    years_experience: Optional[str] = Field(default=None, max_length=50)

    # Company-specific registration fields (Company reg.png)
    company_name: Optional[str] = Field(default=None, max_length=150)
    industry: Optional[str] = Field(default=None, max_length=100)
    contact_phone: Optional[str] = Field(default=None, max_length=50)
    website_url: Optional[str] = Field(default=None, max_length=255)
    office_address: Optional[str] = Field(default=None, max_length=255)

    terms_accepted: bool = Field(default=True)

    model_config = ConfigDict(extra="ignore")


class UserLoginRequest(BaseModel):
    """Schema for user authentication request."""
    email: EmailStr
    password: str
    remember_me: bool = False

    model_config = ConfigDict(extra="forbid")


class UserResponse(BaseModel):
    """Schema for serialized user representation (never exposing hashed password)."""
    id: int
    email: EmailStr
    role: UserRole
    first_name: str
    last_name: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    """Schema for successful authentication response with JWT access and refresh tokens."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class RefreshTokenRequest(BaseModel):
    """Schema for refreshing access tokens using a valid refresh token."""
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    """Schema for requesting a password reset email."""
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Schema for resetting password with a validated reset token."""
    token: str
    new_password: str = Field(min_length=8, description="New password must be at least 8 characters long")


class VerifyEmailRequest(BaseModel):
    """Schema for email verification."""
    token: str


class RegisterResponseData(BaseModel):
    """Payload returned upon user registration."""
    user: UserResponse
    verification_token: Optional[str] = None
    verification_required: bool = True


class ApiResponse(BaseModel, Generic[T]):
    """Standardized API response wrapper."""
    success: bool = True
    message: str = "Operation successful"
    data: Optional[T] = None
