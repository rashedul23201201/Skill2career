import logging
import math
from datetime import datetime, timezone
from typing import Tuple, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    generate_time_sensitive_token,
    hash_token,
)
from app.core.exceptions import (
    ConflictException,
    UnauthorizedException,
    ForbiddenException,
    NotFoundException,
    BadRequestException,
    TooManyRequestsException,
)
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository
from app.repositories.token_repository import TokenRepository
from app.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    TokenResponse,
    UserResponse,
    RegisterResponseData,
)

logger = logging.getLogger(__name__)


class AuthService:
    """Service implementing business logic for authentication, security tokens, and account lifecycle (SKL-49)."""

    def __init__(
        self,
        user_repo: UserRepository = UserRepository(),
        token_repo: TokenRepository = TokenRepository(),
    ):
        self.user_repo = user_repo
        self.token_repo = token_repo

    def register_user(self, db: Session, payload: UserRegisterRequest) -> RegisterResponseData:
        """Register a new user account with initial role-specific profile and verification token (AC-1)."""
        normalized_email = payload.email.strip().lower()
        existing_user = self.user_repo.get_by_email(db, normalized_email)
        if existing_user:
            logger.warning("Registration conflict: email '%s' already exists", normalized_email)
            raise ConflictException(
                message="An account with this email address already exists",
                error_code="EMAIL_ALREADY_EXISTS"
            )

        hashed_pw = hash_password(payload.password)
        first_name = payload.first_name.strip()
        last_name = payload.last_name.strip() if payload.last_name else ""

        # Default fallback for single full_name field from UI
        if not last_name and " " in first_name:
            parts = first_name.split(" ", 1)
            first_name = parts[0]
            last_name = parts[1]

        new_user = User(
            email=normalized_email,
            hashed_password=hashed_pw,
            role=payload.role,
            first_name=first_name,
            last_name=last_name,
            is_active=True,
            is_verified=False,  # Unverified until email verification link is processed (AC-1)
            failed_login_attempts=0
        )
        created_user = self.user_repo.create(db, new_user)

        # Initialize role-specific profile data if supplied from registration forms
        if payload.role == UserRole.LEARNER:
            self.user_repo.create_learner_profile(
                db,
                user_id=created_user.id,
                institution=payload.institution,
                department=payload.department,
                target_role=payload.target_role,
            )
        elif payload.role == UserRole.INSTRUCTOR:
            self.user_repo.create_instructor_profile(
                db,
                user_id=created_user.id,
                qualification=payload.qualification,
                expertise=payload.expertise,
                years_experience=payload.years_experience,
            )
        elif payload.role == UserRole.COMPANY:
            company_name = payload.company_name or f"{created_user.first_name}'s Organization"
            self.user_repo.create_company_profile(
                db,
                user_id=created_user.id,
                company_name=company_name,
                industry=payload.industry,
                contact_phone=payload.contact_phone,
                website_url=payload.website_url,
                office_address=payload.office_address,
            )

        # Generate email verification token (AC-1)
        raw_token, token_hash, expires_at = generate_time_sensitive_token(
            expires_in_hours=settings.EMAIL_VERIFICATION_EXPIRE_HOURS
        )
        self.token_repo.create_email_verification(db, created_user.id, token_hash, expires_at)

        logger.info("User registered: ID=%d, email=%s, role=%s", created_user.id, created_user.email, created_user.role)
        return RegisterResponseData(
            user=UserResponse.model_validate(created_user),
            verification_token=raw_token,
            verification_required=True
        )

    def authenticate_user(self, db: Session, payload: UserLoginRequest) -> TokenResponse:
        """Authenticate user credentials, enforce rate-limiting lockout, and issue access + refresh tokens (AC-2, AC-3)."""
        normalized_email = payload.email.strip().lower()
        user = self.user_repo.get_by_email(db, normalized_email)

        # Check for account existence
        if not user:
            logger.warning("Login failed: email '%s' not found", normalized_email)
            raise UnauthorizedException(
                message="Invalid email or password",
                error_code="INVALID_CREDENTIALS"
            )

        now = datetime.now(timezone.utc)

        # 1. Enforce rate limiting lockout (AC-3: Rate-limits failed attempts after 5 consecutive tries)
        if user.locked_until:
            # Handle timezone awareness
            locked_until_utc = user.locked_until if user.locked_until.tzinfo else user.locked_until.replace(tzinfo=timezone.utc)
            if locked_until_utc > now:
                seconds_remaining = (locked_until_utc - now).total_seconds()
                minutes_remaining = max(1, math.ceil(seconds_remaining / 60))
                logger.warning("Locked account login attempt: user_id=%d, minutes_left=%d", user.id, minutes_remaining)
                raise TooManyRequestsException(
                    message=f"Account temporarily locked due to 5 consecutive failed login attempts. Please try again in {minutes_remaining} minute(s).",
                    error_code="ACCOUNT_LOCKED"
                )
            else:
                # Lockout period expired; reset
                self.user_repo.reset_failed_logins(db, user)

        # 2. Verify password
        if not verify_password(payload.password, user.hashed_password):
            attempts = self.user_repo.record_failed_login(db, user)
            logger.warning("Failed login attempt #%d for user_id=%d", attempts, user.id)

            if attempts >= settings.MAX_FAILED_LOGIN_ATTEMPTS:
                raise TooManyRequestsException(
                    message=f"Too many failed login attempts. Your account has been temporarily locked for {settings.ACCOUNT_LOCKOUT_MINUTES} minutes for security.",
                    error_code="ACCOUNT_LOCKED"
                )

            raise UnauthorizedException(
                message="Invalid email or password",
                error_code="INVALID_CREDENTIALS"
            )

        # 3. Successful password check: clear any failed login counters
        self.user_repo.reset_failed_logins(db, user)

        # 4. Check active account status
        if not user.is_active:
            logger.warning("Login blocked for inactive user: user_id=%d", user.id)
            raise ForbiddenException(
                message="This account has been deactivated. Please contact platform administration.",
                error_code="ACCOUNT_INACTIVE"
            )

        # 5. Generate Access Token & Refresh Token (AC-2)
        access_token = create_access_token(
            subject=user.id,
            claims={"email": user.email, "role": user.role.value}
        )

        raw_refresh_token, refresh_hash, refresh_expires_at = create_refresh_token(
            subject=user.id,
            remember_me=payload.remember_me
        )
        self.token_repo.create_refresh_token(db, user.id, refresh_hash, refresh_expires_at)

        logger.info("User authenticated: ID=%d, email=%s, role=%s", user.id, user.email, user.role)
        return TokenResponse(
            access_token=access_token,
            refresh_token=raw_refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse.model_validate(user)
        )

    def refresh_access_token(self, db: Session, raw_refresh_token: str) -> TokenResponse:
        """Validate an active refresh token, rotate it, and issue a fresh access token."""
        token_hash = hash_token(raw_refresh_token)
        stored_token = self.token_repo.get_active_refresh_token(db, token_hash)

        if not stored_token:
            logger.warning("Invalid or expired refresh token presented")
            raise UnauthorizedException(
                message="Refresh token is invalid, expired, or has been revoked. Please log in again.",
                error_code="INVALID_REFRESH_TOKEN"
            )

        user = self.user_repo.get_by_id(db, stored_token.user_id)
        if not user or not user.is_active:
            raise UnauthorizedException(
                message="User account no longer active",
                error_code="ACCOUNT_INACTIVE"
            )

        # Rotate refresh token: revoke current and issue new
        self.token_repo.revoke_refresh_token(db, stored_token)

        new_access_token = create_access_token(
            subject=user.id,
            claims={"email": user.email, "role": user.role.value}
        )

        new_raw_refresh, new_refresh_hash, new_refresh_expires = create_refresh_token(subject=user.id)
        self.token_repo.create_refresh_token(db, user.id, new_refresh_hash, new_refresh_expires)

        logger.info("Rotated refresh token for user_id=%d", user.id)
        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_raw_refresh,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse.model_validate(user)
        )

    def request_password_reset(self, db: Session, email: str) -> Dict[str, Any]:
        """Initiate password reset workflow by generating a 1-hour secure reset token (AC-4)."""
        normalized_email = email.strip().lower()
        user = self.user_repo.get_by_email(db, normalized_email)

        # Prevent user enumeration: always return success message even if email doesn't exist
        if not user:
            logger.info("Password reset requested for non-existent email: %s", normalized_email)
            return {
                "message": "If an account with that email exists, password reset instructions have been sent.",
                "reset_token": None
            }

        raw_token, token_hash, expires_at = generate_time_sensitive_token(
            expires_in_hours=settings.PASSWORD_RESET_EXPIRE_HOURS
        )
        self.token_repo.create_password_reset(db, user.id, token_hash, expires_at)

        logger.info("Password reset token generated for user_id=%d", user.id)
        return {
            "message": "Password reset instructions have been generated.",
            "reset_token": raw_token  # Returned for direct API/frontend consumption during sprint testing
        }

    def reset_password(self, db: Session, raw_token: str, new_password: str) -> Dict[str, str]:
        """Validate reset token and update user password, invalidating active sessions (AC-4)."""
        token_hash = hash_token(raw_token)
        reset_record = self.token_repo.get_valid_password_reset(db, token_hash)

        if not reset_record:
            logger.warning("Invalid or expired password reset token presented")
            raise BadRequestException(
                message="Password reset link is invalid or has expired. Please request a new one.",
                error_code="INVALID_RESET_TOKEN"
            )

        user = self.user_repo.get_by_id(db, reset_record.user_id)
        if not user:
            raise NotFoundException("User not found", "USER_NOT_FOUND")

        new_hashed_password = hash_password(new_password)
        self.user_repo.update_password(db, user, new_hashed_password)
        self.token_repo.mark_password_reset_used(db, reset_record)

        # Invalidate all active refresh sessions for security
        self.token_repo.revoke_all_user_refresh_tokens(db, user.id)

        logger.info("Password reset successfully for user_id=%d", user.id)
        return {"message": "Your password has been reset successfully. Please log in with your new password."}

    def verify_email(self, db: Session, raw_token: str) -> UserResponse:
        """Validate email verification token and update account status to verified (AC-1)."""
        token_hash = hash_token(raw_token)
        verification_record = self.token_repo.get_valid_email_verification(db, token_hash)

        if not verification_record:
            raise BadRequestException(
                message="Email verification link is invalid or has expired.",
                error_code="INVALID_VERIFICATION_TOKEN"
            )

        user = self.user_repo.get_by_id(db, verification_record.user_id)
        if not user:
            raise NotFoundException("User not found", "USER_NOT_FOUND")

        verified_user = self.user_repo.verify_email(db, user)
        self.token_repo.mark_email_verification_used(db, verification_record)

        logger.info("Email verified for user_id=%d", verified_user.id)
        return UserResponse.model_validate(verified_user)

    def get_user_by_id(self, db: Session, user_id: int) -> User:
        """Fetch user by ID or raise NotFoundException."""
        user = self.user_repo.get_by_id(db, user_id)
        if not user:
            raise NotFoundException(
                message=f"User with ID {user_id} was not found",
                error_code="USER_NOT_FOUND"
            )
        return user
