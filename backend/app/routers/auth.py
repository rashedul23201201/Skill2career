from typing import Dict, Any
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
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
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])
auth_service = AuthService()


@router.post(
    "/register",
    response_model=ApiResponse[RegisterResponseData],
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account (AC-1)"
)
def register(
    payload: UserRegisterRequest,
    db: Session = Depends(get_db)
) -> ApiResponse[RegisterResponseData]:
    """Register a new user across Learner, Instructor, or Company roles with verification token generation."""
    registration_data = auth_service.register_user(db, payload)
    return ApiResponse[RegisterResponseData](
        success=True,
        message="Registration successful. Please verify your email to unlock all features.",
        data=registration_data
    )


@router.post(
    "/login",
    response_model=ApiResponse[TokenResponse],
    status_code=status.HTTP_200_OK,
    summary="User login with email and password (AC-2, AC-3)"
)
def login(
    payload: UserLoginRequest,
    db: Session = Depends(get_db)
) -> ApiResponse[TokenResponse]:
    """Authenticate user credentials, enforce 5-attempt rate-limiting lockout, and return access + refresh tokens."""
    token_response = auth_service.authenticate_user(db, payload)
    return ApiResponse[TokenResponse](
        success=True,
        message="Authentication successful",
        data=token_response
    )


@router.post(
    "/refresh",
    response_model=ApiResponse[TokenResponse],
    status_code=status.HTTP_200_OK,
    summary="Rotate refresh token and issue new access token"
)
def refresh_token(
    payload: RefreshTokenRequest,
    db: Session = Depends(get_db)
) -> ApiResponse[TokenResponse]:
    """Exchange a valid refresh token for a rotated refresh token and fresh access token."""
    token_response = auth_service.refresh_access_token(db, payload.refresh_token)
    return ApiResponse[TokenResponse](
        success=True,
        message="Token refreshed successfully",
        data=token_response
    )


@router.post(
    "/forgot-password",
    response_model=ApiResponse[Dict[str, Any]],
    status_code=status.HTTP_200_OK,
    summary="Request password reset token (AC-4)"
)
def forgot_password(
    payload: ForgotPasswordRequest,
    db: Session = Depends(get_db)
) -> ApiResponse[Dict[str, Any]]:
    """Initiate password reset flow by sending/generating a 1-hour secure reset token."""
    result = auth_service.request_password_reset(db, payload.email)
    return ApiResponse[Dict[str, Any]](
        success=True,
        message=result["message"],
        data=result
    )


@router.post(
    "/reset-password",
    response_model=ApiResponse[Dict[str, str]],
    status_code=status.HTTP_200_OK,
    summary="Reset password using reset token (AC-4)"
)
def reset_password(
    payload: ResetPasswordRequest,
    db: Session = Depends(get_db)
) -> ApiResponse[Dict[str, str]]:
    """Verify reset token and update account password."""
    result = auth_service.reset_password(db, payload.token, payload.new_password)
    return ApiResponse[Dict[str, str]](
        success=True,
        message=result["message"],
        data=result
    )


@router.post(
    "/verify-email",
    response_model=ApiResponse[UserResponse],
    status_code=status.HTTP_200_OK,
    summary="Verify user email address (AC-1)"
)
def verify_email(
    payload: VerifyEmailRequest,
    db: Session = Depends(get_db)
) -> ApiResponse[UserResponse]:
    """Process email verification token and update account status to verified."""
    verified_user = auth_service.verify_email(db, payload.token)
    return ApiResponse[UserResponse](
        success=True,
        message="Email verified successfully. Your account is now fully active.",
        data=verified_user
    )


@router.get(
    "/me",
    response_model=ApiResponse[UserResponse],
    status_code=status.HTTP_200_OK,
    summary="Retrieve current authenticated user profile"
)
def get_me(
    current_user: User = Depends(get_current_user)
) -> ApiResponse[UserResponse]:
    """Return profile details of currently authenticated user."""
    return ApiResponse[UserResponse](
        success=True,
        message="User profile retrieved successfully",
        data=UserResponse.model_validate(current_user)
    )
