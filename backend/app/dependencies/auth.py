from typing import Callable, Optional
import jwt
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.security import decode_access_token
from app.core.exceptions import UnauthorizedException, ForbiddenException
from app.database.session import get_db
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login",
    auto_error=False
)


def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Dependency that extracts and validates the JWT Bearer token and returns the current user."""
    if not token:
        raise UnauthorizedException(
            message="Authentication credentials were not provided",
            error_code="NOT_AUTHENTICATED"
        )

    try:
        payload = decode_access_token(token)
        user_id_str: Optional[str] = payload.get("sub")
        if not user_id_str:
            raise UnauthorizedException(
                message="Invalid authentication token payload",
                error_code="INVALID_TOKEN"
            )
        user_id = int(user_id_str)
    except jwt.ExpiredSignatureError:
        raise UnauthorizedException(
            message="Authentication token has expired. Please log in again.",
            error_code="TOKEN_EXPIRED"
        )
    except (jwt.PyJWTError, ValueError):
        raise UnauthorizedException(
            message="Could not validate authentication credentials",
            error_code="INVALID_TOKEN"
        )

    user = UserRepository.get_by_id(db, user_id)
    if not user:
        raise UnauthorizedException(
            message="User associated with token no longer exists",
            error_code="USER_NOT_FOUND"
        )

    if not user.is_active:
        raise ForbiddenException(
            message="User account is deactivated",
            error_code="ACCOUNT_INACTIVE"
        )

    return user


def require_role(*allowed_roles: UserRole) -> Callable[[User], User]:
    """Dependency factory enforcing that the authenticated user possesses at least one of the allowed roles."""
    def role_dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            expected = ", ".join(role.value for role in allowed_roles)
            raise ForbiddenException(
                message=f"Access denied. Required role: [{expected}], current role: [{current_user.role.value}]",
                error_code="INSUFFICIENT_ROLE_PERMISSIONS"
            )
        return current_user

    return role_dependency
