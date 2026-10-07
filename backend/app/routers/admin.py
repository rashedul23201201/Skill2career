from typing import Optional, List
from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import require_admin
from app.models.user import User, UserRole
from app.schemas.auth import ApiResponse, UserResponse
from app.schemas.admin import (
    AdminOverviewStats,
    PaginatedUserResponse,
    UserStatusUpdateRequest,
    UserRoleUpdateRequest,
    AuditLogResponse,
)
from app.schemas.company import (
    PendingCompanyVerificationItem,
    AdminCompanyVerificationAction,
    CompanyVerificationStatusResponse,
)
from app.schemas.instructor import (
    InstructorProfileResponse,
    InstructorStatusUpdateRequest,
)
from app.services.admin_service import AdminService
from app.services.company_service import CompanyService
from app.schemas.company import CompanyModerationRequest, CompanyProfileResponse
from app.services.instructor_service import InstructorService

router = APIRouter(prefix="/admin", tags=["Admin Management"])
admin_service = AdminService()
company_service = CompanyService()
instructor_service = InstructorService()


@router.get(
    "/overview-stats",
    response_model=ApiResponse[AdminOverviewStats],
    status_code=status.HTTP_200_OK,
    summary="Get system overview metrics for Admin Dashboard"
)
def get_overview_stats(
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
) -> ApiResponse[AdminOverviewStats]:
    """Retrieve system counters: total users, companies, active courses, pending approvals, and user breakdown."""
    stats = admin_service.get_overview_stats(db)
    return ApiResponse[AdminOverviewStats](
        success=True,
        message="System overview stats retrieved successfully",
        data=stats
    )


@router.get(
    "/users",
    response_model=ApiResponse[PaginatedUserResponse],
    status_code=status.HTTP_200_OK,
    summary="List paginated users with filters and search (SKL-50/SKL-24)"
)
def get_users(
    page: int = Query(default=1, ge=1, description="Page number"),
    size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    role: Optional[UserRole] = Query(default=None, description="Filter by user role"),
    is_active: Optional[bool] = Query(default=None, description="Filter by active status"),
    is_verified: Optional[bool] = Query(default=None, description="Filter by email verification status"),
    search: Optional[str] = Query(default=None, description="Search term for email or name"),
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
) -> ApiResponse[PaginatedUserResponse]:
    """Retrieve a filterable, paginated directory of platform users for administrative management."""
    result = admin_service.get_users_paginated(
        db=db,
        page=page,
        size=size,
        role=role,
        is_active=is_active,
        is_verified=is_verified,
        search=search
    )
    return ApiResponse[PaginatedUserResponse](
        success=True,
        message="Users retrieved successfully",
        data=result
    )


@router.get(
    "/users/{user_id}",
    response_model=ApiResponse[UserResponse],
    status_code=status.HTTP_200_OK,
    summary="Get user details by ID"
)
def get_user_by_id(
    user_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
) -> ApiResponse[UserResponse]:
    """Retrieve detailed user entity by ID."""
    user = admin_service.get_user_by_id(db, user_id)
    return ApiResponse[UserResponse](
        success=True,
        message="User retrieved successfully",
        data=UserResponse.model_validate(user)
    )


@router.patch(
    "/users/{user_id}/status",
    response_model=ApiResponse[UserResponse],
    status_code=status.HTTP_200_OK,
    summary="Activate or deactivate a user account"
)
def update_user_status(
    user_id: int,
    payload: UserStatusUpdateRequest,
    request: Request,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
) -> ApiResponse[UserResponse]:
    """Toggle user account active status. Deactivation immediately revokes active user sessions."""
    client_ip = request.client.host if request.client else "unknown"
    updated_user = admin_service.update_user_status(
        db=db,
        admin_user=admin_user,
        user_id=user_id,
        is_active=payload.is_active,
        reason=payload.reason,
        ip_address=client_ip
    )
    status_str = "activated" if payload.is_active else "deactivated"
    return ApiResponse[UserResponse](
        success=True,
        message=f"User account successfully {status_str}",
        data=UserResponse.model_validate(updated_user)
    )


@router.patch(
    "/users/{user_id}/role",
    response_model=ApiResponse[UserResponse],
    status_code=status.HTTP_200_OK,
    summary="Modify a user's system role"
)
def update_user_role(
    user_id: int,
    payload: UserRoleUpdateRequest,
    request: Request,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
) -> ApiResponse[UserResponse]:
    """Reassign user role. Triggers immediate active session revocation and security audit logging."""
    client_ip = request.client.host if request.client else "unknown"
    updated_user = admin_service.update_user_role(
        db=db,
        admin_user=admin_user,
        user_id=user_id,
        new_role=payload.role,
        reason=payload.reason,
        ip_address=client_ip
    )
    return ApiResponse[UserResponse](
        success=True,
        message=f"User role successfully updated to {payload.role.value}",
        data=UserResponse.model_validate(updated_user)
    )


@router.get(
    "/audit-logs",
    response_model=ApiResponse[List[AuditLogResponse]],
    status_code=status.HTTP_200_OK,
    summary="Get recent security and administrative audit logs"
)
def get_audit_logs(
    limit: int = Query(default=15, ge=1, le=50, description="Max logs to return"),
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
) -> ApiResponse[List[AuditLogResponse]]:
    """Retrieve recent administrative actions and security overrides for activity feed."""
    logs = admin_service.get_recent_audit_logs(db, limit=limit)
    return ApiResponse[List[AuditLogResponse]](
        success=True,
        message="Audit logs retrieved successfully",
        data=logs
    )


@router.patch(
    "/companies/{company_id}/moderate",
    response_model=ApiResponse[CompanyProfileResponse],
    status_code=status.HTTP_200_OK,
    summary="Admin moderation for company profile and verification (SKL-3 / SKL-50)"
)
def moderate_company(
    company_id: int,
    payload: CompanyModerationRequest,
    request: Request,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
) -> ApiResponse[CompanyProfileResponse]:
    """Moderate company profile details, verification status, and log administrative audit trail."""
    client_ip = request.client.host if request.client else None
    result = company_service.moderate_company(
        db=db,
        admin_user=admin_user,
        company_id=company_id,
        payload=payload,
        ip_address=client_ip
    )
    return ApiResponse[CompanyProfileResponse](
        success=True,
        message="Company profile successfully moderated",
        data=result
    )


@router.get(
    "/companies/pending-verifications",
    response_model=ApiResponse[List[PendingCompanyVerificationItem]],
    status_code=status.HTTP_200_OK,
    summary="Get all pending company verification requests (SKL-2)"
)
def get_pending_company_verifications(
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
) -> ApiResponse[List[PendingCompanyVerificationItem]]:
    """Retrieve all employer organizations currently awaiting verification review."""
    items = company_service.get_pending_verifications(db=db)
    return ApiResponse[List[PendingCompanyVerificationItem]](
        success=True,
        message="Pending company verifications retrieved successfully",
        data=items
    )


@router.post(
    "/companies/{company_id}/verify",
    response_model=ApiResponse[CompanyVerificationStatusResponse],
    status_code=status.HTTP_200_OK,
    summary="Approve or reject company verification dossier (SKL-2)"
)
def verify_company(
    company_id: int,
    payload: AdminCompanyVerificationAction,
    request: Request,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
) -> ApiResponse[CompanyVerificationStatusResponse]:
    """Admin decision point: Approve or reject verification dossier with optional feedback notes."""
    client_ip = request.client.host if request.client else "unknown"
    result = company_service.process_verification(
        db=db,
        admin_user=admin_user,
        company_id=company_id,
        action=payload.action,
        notes=payload.notes,
        ip_address=client_ip
    )
    decision = "approved" if payload.action.upper() == "APPROVE" else "rejected"
    return ApiResponse[CompanyVerificationStatusResponse](
        success=True,
        message=f"Company verification dossier successfully {decision}",
        data=result
    )


@router.get(
    "/instructors/pending",
    response_model=ApiResponse[List[InstructorProfileResponse]],
    status_code=status.HTTP_200_OK,
    summary="List pending instructor applications for administrative review (SKL-52)"
)
def get_pending_instructors(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
) -> ApiResponse[List[InstructorProfileResponse]]:
    """Retrieve instructor onboarding applications awaiting review."""
    pending = instructor_service.get_pending_instructors(db, skip=skip, limit=limit)
    return ApiResponse[List[InstructorProfileResponse]](
        success=True,
        message="Pending instructor applications retrieved successfully",
        data=pending
    )


@router.patch(
    "/instructors/{profile_id}/status",
    response_model=ApiResponse[InstructorProfileResponse],
    status_code=status.HTTP_200_OK,
    summary="Approve, reject, or suspend an instructor account (SKL-52)"
)
def update_instructor_status(
    profile_id: int,
    payload: InstructorStatusUpdateRequest,
    request: Request,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
) -> ApiResponse[InstructorProfileResponse]:
    """Approve or reject instructor credentials. Approval automatically promotes the user role to INSTRUCTOR."""
    client_ip = request.client.host if request.client else "unknown"
    updated = instructor_service.update_instructor_status(
        db=db,
        admin_user=admin_user,
        profile_id=profile_id,
        new_status=payload.status,
        reason=payload.reason,
        ip_address=client_ip
    )
    return ApiResponse[InstructorProfileResponse](
        success=True,
        message=f"Instructor onboarding status successfully updated to {payload.status.upper()}",
        data=updated
    )
