"""Pydantic schemas package."""

from app.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    TokenResponse,
    UserResponse,
    RefreshTokenRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    VerifyEmailRequest,
    RegisterResponseData,
    ApiResponse,
)
from app.schemas.admin import (
    AdminOverviewStats,
    UserStatusUpdateRequest,
    UserRoleUpdateRequest,
    PaginatedUserResponse,
    AuditLogResponse,
)

from app.schemas.learner import (
    LearnerProfileUpdateRequest,
    LearnerProfileResponse,
    ResumeUploadResponse,
    ProfileCompletionBreakdown,
)

__all__ = [
    "UserRegisterRequest",
    "UserLoginRequest",
    "TokenResponse",
    "UserResponse",
    "RefreshTokenRequest",
    "ForgotPasswordRequest",
    "ResetPasswordRequest",
    "VerifyEmailRequest",
    "RegisterResponseData",
    "ApiResponse",
    "AdminOverviewStats",
    "UserStatusUpdateRequest",
    "UserRoleUpdateRequest",
    "PaginatedUserResponse",
    "AuditLogResponse",
    "LearnerProfileUpdateRequest",
    "LearnerProfileResponse",
    "ResumeUploadResponse",
    "ProfileCompletionBreakdown",
]
