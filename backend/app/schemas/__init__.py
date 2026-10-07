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

from app.schemas.course import (
    CourseLevel,
    CourseStatus,
    CourseCreateRequest,
    CourseUpdateRequest,
    CourseStatusUpdateRequest,
    CourseResponse,
    CourseDetailResponse,
    CourseModuleSchema,
    LessonSchema,
    CurriculumSyncRequest,
    PaginatedCourseResponse,
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
    "CourseLevel",
    "CourseStatus",
    "CourseCreateRequest",
    "CourseUpdateRequest",
    "CourseStatusUpdateRequest",
    "CourseResponse",
    "CourseDetailResponse",
    "CourseModuleSchema",
    "LessonSchema",
    "CurriculumSyncRequest",
    "PaginatedCourseResponse",
]

