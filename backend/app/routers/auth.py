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
    ApiResponse,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])
auth_service = AuthService()


@router.post(
    "/register",
    response_model=ApiResponse[UserResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account"
)
def register(
    payload: UserRegisterRequest,
    db: Session = Depends(get_db)
) -> ApiResponse[UserResponse]:
    """Register a new user with email, password, full name, and selected role."""
    new_user = auth_service.register_user(db, payload)
    return ApiResponse[UserResponse](
        success=True,
        message="User registered successfully",
        data=UserResponse.model_validate(new_user)
    )


@router.post(
    "/login",
    response_model=ApiResponse[TokenResponse],
    status_code=status.HTTP_200_OK,
    summary="User login with email and password"
)
def login(
    payload: UserLoginRequest,
    db: Session = Depends(get_db)
) -> ApiResponse[TokenResponse]:
    """Authenticate user credentials and issue a JWT access token."""
    token_response = auth_service.authenticate_user(db, payload)
    return ApiResponse[TokenResponse](
        success=True,
        message="Authentication successful",
        data=token_response
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
