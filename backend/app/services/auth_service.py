import logging
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.security import hash_password, verify_password, create_access_token
from app.core.exceptions import ConflictException, UnauthorizedException, ForbiddenException, NotFoundException
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import UserRegisterRequest, UserLoginRequest, TokenResponse

logger = logging.getLogger(__name__)


class AuthService:
    """Service handling business logic for authentication and user accounts."""

    def __init__(self, user_repo: UserRepository = UserRepository()):
        self.user_repo = user_repo

    def register_user(self, db: Session, payload: UserRegisterRequest) -> User:
        """Register a new user in the system after validating uniqueness."""
        normalized_email = payload.email.strip().lower()
        existing_user = self.user_repo.get_by_email(db, normalized_email)
        if existing_user:
            logger.warning("Registration attempt with already existing email: %s", normalized_email)
            raise ConflictException(
                message="An account with this email address already exists",
                error_code="EMAIL_ALREADY_EXISTS"
            )

        hashed_pw = hash_password(payload.password)
        new_user = User(
            email=normalized_email,
            hashed_password=hashed_pw,
            role=payload.role,
            first_name=payload.first_name.strip(),
            last_name=payload.last_name.strip(),
            is_active=True,
            is_verified=False
        )

        created_user = self.user_repo.create(db, new_user)
        logger.info("New user registered successfully: ID=%d, Role=%s", created_user.id, created_user.role)
        return created_user

    def authenticate_user(self, db: Session, payload: UserLoginRequest) -> TokenResponse:
        """Verify user credentials and generate a JWT access token."""
        normalized_email = payload.email.strip().lower()
        user = self.user_repo.get_by_email(db, normalized_email)

        if not user or not verify_password(payload.password, user.hashed_password):
            logger.warning("Failed login attempt for email: %s", normalized_email)
            raise UnauthorizedException(
                message="Invalid email or password",
                error_code="INVALID_CREDENTIALS"
            )

        if not user.is_active:
            logger.warning("Login attempt for deactivated user: ID=%d", user.id)
            raise ForbiddenException(
                message="This account has been deactivated. Please contact support.",
                error_code="ACCOUNT_INACTIVE"
            )

        token = create_access_token(
            subject=user.id,
            claims={
                "email": user.email,
                "role": user.role.value
            }
        )

        logger.info("User authenticated successfully: ID=%d", user.id)
        return TokenResponse(
            access_token=token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )

    def get_user_by_id(self, db: Session, user_id: int) -> User:
        """Fetch user by ID or raise NotFoundException."""
        user = self.user_repo.get_by_id(db, user_id)
        if not user:
            raise NotFoundException(
                message=f"User with ID {user_id} was not found",
                error_code="USER_NOT_FOUND"
            )
        return user
