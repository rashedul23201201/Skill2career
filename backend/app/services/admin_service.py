import logging
import math
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from app.core.exceptions import (
    NotFoundException,
    BadRequestException,
)
from app.models.user import User, UserRole
from app.models.audit_log import AuditLog
from app.repositories.user_repository import UserRepository
from app.repositories.token_repository import TokenRepository
from app.repositories.audit_log_repository import AuditLogRepository
from app.schemas.auth import UserResponse
from app.schemas.admin import (
    AdminOverviewStats,
    PaginatedUserResponse,
    AuditLogResponse,
)

logger = logging.getLogger(__name__)


class AdminService:
    """Service implementing administrative operations, RBAC governance, and security audit tracking (SKL-50/SKL-24)."""

    def __init__(
        self,
        user_repo: UserRepository = UserRepository(),
        token_repo: TokenRepository = TokenRepository(),
        audit_repo: AuditLogRepository = AuditLogRepository(),
    ):
        self.user_repo = user_repo
        self.token_repo = token_repo
        self.audit_repo = audit_repo

    def get_overview_stats(self, db: Session) -> AdminOverviewStats:
        """Fetch system-wide aggregated metrics for the Admin Dashboard overview."""
        stats = self.user_repo.get_overview_stats(db)
        return AdminOverviewStats(**stats)

    def get_users_paginated(
        self,
        db: Session,
        page: int = 1,
        size: int = 20,
        role: Optional[UserRole] = None,
        is_active: Optional[bool] = None,
        is_verified: Optional[bool] = None,
        search: Optional[str] = None
    ) -> PaginatedUserResponse:
        """Fetch filtered and paginated user list."""
        page = max(1, page)
        size = min(100, max(1, size))

        users, total = self.user_repo.get_users_paginated(
            db=db,
            page=page,
            size=size,
            role=role,
            is_active=is_active,
            is_verified=is_verified,
            search=search
        )
        total_pages = math.ceil(total / size) if size > 0 else 0

        return PaginatedUserResponse(
            items=[UserResponse.model_validate(u) for u in users],
            total=total,
            page=page,
            size=size,
            total_pages=total_pages
        )

    def get_user_by_id(self, db: Session, user_id: int) -> User:
        """Retrieve a specific user or raise 404."""
        user = self.user_repo.get_by_id(db, user_id)
        if not user:
            raise NotFoundException(
                message=f"User with ID {user_id} was not found",
                error_code="USER_NOT_FOUND"
            )
        return user

    def update_user_status(
        self,
        db: Session,
        admin_user: User,
        user_id: int,
        is_active: bool,
        reason: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> User:
        """Activate or deactivate a user account with security audit trail and session invalidation (SKL-50)."""
        target_user = self.get_user_by_id(db, user_id)

        # Prevent admin from deactivating their own account
        if admin_user.id == target_user.id and not is_active:
            raise BadRequestException(
                message="Administrators cannot deactivate their own administrative account",
                error_code="CANNOT_DEACTIVATE_SELF"
            )

        previous_is_active = target_user.is_active
        updated_user = self.user_repo.update_status(db, target_user, is_active)

        # Token revocation check: if deactivating account, immediately invalidate active refresh tokens
        if not is_active:
            self.token_repo.revoke_all_user_refresh_tokens(db, user_id)
            logger.info("Admin ID %d deactivated user ID %d. Active sessions revoked.", admin_user.id, user_id)

        # Record audit log
        self.audit_repo.create(
            db=db,
            admin_id=admin_user.id,
            target_user_id=user_id,
            action="STATUS_UPDATE",
            details={
                "previous_is_active": previous_is_active,
                "new_is_active": is_active,
                "target_email": target_user.email,
                "reason": reason or "Administrative status update"
            },
            ip_address=ip_address
        )

        return updated_user

    def update_user_role(
        self,
        db: Session,
        admin_user: User,
        user_id: int,
        new_role: UserRole,
        reason: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> User:
        """Modify user role with session revocation and audit logging (SKL-50)."""
        target_user = self.get_user_by_id(db, user_id)

        # Prevent admin from removing their own admin privileges
        if admin_user.id == target_user.id and new_role != UserRole.ADMIN:
            raise BadRequestException(
                message="Administrators cannot remove their own administrative privileges",
                error_code="CANNOT_DEMOTE_SELF"
            )

        previous_role = target_user.role.value
        updated_user = self.user_repo.update_role(db, target_user, new_role)

        # Token revocation check: when role changes, immediately invalidate all refresh tokens
        self.token_repo.revoke_all_user_refresh_tokens(db, user_id)
        logger.info(
            "Admin ID %d changed user ID %d role from %s to %s. Active sessions revoked.",
            admin_user.id, user_id, previous_role, new_role.value
        )

        # Record audit log
        self.audit_repo.create(
            db=db,
            admin_id=admin_user.id,
            target_user_id=user_id,
            action="ROLE_UPDATE",
            details={
                "previous_role": previous_role,
                "new_role": new_role.value,
                "target_email": target_user.email,
                "reason": reason or "Administrative role override"
            },
            ip_address=ip_address
        )

        return updated_user

    def get_recent_audit_logs(self, db: Session, limit: int = 15) -> List[AuditLogResponse]:
        """Fetch recent audit activity with enriched admin and target user information."""
        logs = self.audit_repo.get_recent(db, limit=limit)
        results = []
        for log in logs:
            admin_name = f"{log.admin.first_name} {log.admin.last_name}" if log.admin else "System"
            target_name = f"{log.target_user.first_name} {log.target_user.last_name}" if log.target_user else "User"
            results.append(
                AuditLogResponse(
                    id=log.id,
                    admin_id=log.admin_id,
                    admin_name=admin_name,
                    target_user_id=log.target_user_id,
                    target_user_name=target_name,
                    action=log.action,
                    details=log.details,
                    ip_address=log.ip_address,
                    created_at=log.created_at
                )
            )
        return results
