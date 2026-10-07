import logging
from typing import Callable, Optional
import jwt
from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.security import decode_access_token
from app.core.exceptions import UnauthorizedException, ForbiddenException
from app.database.session import get_db
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository

logger = logging.getLogger("security.audit")

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login",
    auto_error=False
)


def get_current_user(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Dependency that extracts and validates the JWT Bearer token and returns the current user."""
    client_ip = request.client.host if request.client else "unknown"
    path = request.url.path
    method = request.method

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

    # Token revocation check: if an Admin deactivates an account, immediately invalidate active sessions (SKL-50)
    if not user.is_active:
        logger.warning(
            "Security 403 Forbidden: Inactive user ID %s attempted to access %s [%s] from IP %s",
            user.id, path, method, client_ip
        )
        raise ForbiddenException(
            message="User account is deactivated. Please contact platform administration.",
            error_code="ACCOUNT_INACTIVE"
        )

    # Token revocation check: if an Admin changes a role, immediately invalidate active sessions with stale token claims (SKL-50)
    token_role = payload.get("role")
    if token_role and token_role != user.role.value:
        logger.warning(
            "Security 401 Unauthorized: User ID %s token role '%s' differs from current database role '%s' on %s [%s] from IP %s",
            user.id, token_role, user.role.value, path, method, client_ip
        )
        raise UnauthorizedException(
            message="User role permissions have changed. Please log in again to refresh your session.",
            error_code="SESSION_ROLE_REVOKED"
        )

    return user


def get_optional_current_user(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Dependency that returns current user if authenticated, or None if anonymous."""
    if not token:
        return None
    try:
        payload = decode_access_token(token)
        user_id_str = payload.get("sub")
        if not user_id_str:
            return None
        user = UserRepository.get_by_id(db, int(user_id_str))
        if not user or not user.is_active:
            return None
        return user
    except Exception:
        return None



def require_role(*allowed_roles: UserRole) -> Callable[..., User]:
    """Dependency factory enforcing that the authenticated user possesses at least one of the allowed roles.
    Includes custom security audit logging when HTTP 403 Forbidden is raised (SKL-50)."""
    def role_dependency(
        request: Request,
        current_user: User = Depends(get_current_user)
    ) -> User:
        if current_user.role not in allowed_roles:
            client_ip = request.client.host if request.client else "unknown"
            path = request.url.path
            method = request.method
            expected = ", ".join(role.value for role in allowed_roles)
            logger.warning(
                "Security 403 Forbidden: User ID %s (role: %s) denied access to %s [%s] from IP %s. Required roles: [%s]",
                current_user.id, current_user.role.value, path, method, client_ip, expected
            )
            raise ForbiddenException(
                message=f"Access denied. Required role: [{expected}], current role: [{current_user.role.value}]",
                error_code="INSUFFICIENT_ROLE_PERMISSIONS"
            )
        return current_user

    return role_dependency


# Granular RBAC dependency guards (SKL-50)
require_admin = require_role(UserRole.ADMIN)
require_learner = require_role(UserRole.LEARNER)
require_instructor = require_role(UserRole.INSTRUCTOR)
require_company = require_role(UserRole.COMPANY)
