from datetime import datetime
from typing import Optional, Generic, TypeVar
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from app.models.user import UserRole

T = TypeVar("T")


class UserRegisterRequest(BaseModel):
    """Schema for new user registration."""
    email: EmailStr
    password: str = Field(min_length=8, description="Password must be at least 8 characters long")
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    role: UserRole = Field(default=UserRole.LEARNER, description="User role in the ecosystem")

    model_config = ConfigDict(extra="forbid")


class UserLoginRequest(BaseModel):
    """Schema for user authentication request."""
    email: EmailStr
    password: str

    model_config = ConfigDict(extra="forbid")


class TokenResponse(BaseModel):
    """Schema for successful authentication response with JWT access token."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


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


class ApiResponse(BaseModel, Generic[T]):
    """Standardized API response wrapper."""
    success: bool = True
    message: str = "Operation successful"
    data: Optional[T] = None
