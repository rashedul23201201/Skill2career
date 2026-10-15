"""Router for Company Dashboard recruitment metrics, vacancy pipelines, and activity streams (SKL-11)."""

from typing import Optional, List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import require_role
from app.models.user import User, UserRole
from app.schemas.auth import ApiResponse
from app.schemas.company_dashboard import (
    CompanyDashboardMetricsResponse,
    CompanyDashboardVacanciesResponse,
    CompanyDashboardActivityResponse,
    CompanyDashboardProfileStatusResponse,
    CompanyDashboardUpcomingInterviewItem,
)
from app.services.company_dashboard_service import CompanyDashboardService

router = APIRouter(prefix="/companies/dashboard", tags=["Company Dashboard (SKL-11)"])
dashboard_service = CompanyDashboardService()


@router.get(
    "/metrics",
    response_model=ApiResponse[CompanyDashboardMetricsResponse],
    status_code=status.HTTP_200_OK,
    summary="Central recruitment metrics and hiring stage breakdown (SKL-11 AC-1)",
)
def get_dashboard_metrics(
    target_company_id: Optional[int] = Query(None, description="Admin override company ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.COMPANY, UserRole.ADMIN)),
) -> ApiResponse[CompanyDashboardMetricsResponse]:
    """Retrieve recruitment metrics: active job postings, total applications, pending reviews, scheduled interviews."""
    metrics = dashboard_service.get_metrics(
        db=db,
        current_user=current_user,
        target_company_id=target_company_id,
    )
    return ApiResponse[CompanyDashboardMetricsResponse](
        success=True,
        message="Recruitment metrics retrieved successfully",
        data=metrics,
    )


@router.get(
    "/vacancies",
    response_model=ApiResponse[CompanyDashboardVacanciesResponse],
    status_code=status.HTTP_200_OK,
    summary="Active vacancies with candidate stage volumes (SKL-11 AC-2)",
)
def get_dashboard_vacancies(
    status_filter: Optional[str] = Query("ACTIVE", alias="status", description="Filter by status: ACTIVE, ALL, CLOSED"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    target_company_id: Optional[int] = Query(None, description="Admin override company ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.COMPANY, UserRole.ADMIN)),
) -> ApiResponse[CompanyDashboardVacanciesResponse]:
    """Retrieve active postings showing candidate volume per hiring stage (APPLIED, SHORTLISTED, INTERVIEW, OFFERED)."""
    vacancies = dashboard_service.get_vacancies(
        db=db,
        current_user=current_user,
        status=status_filter,
        limit=limit,
        offset=offset,
        target_company_id=target_company_id,
    )
    return ApiResponse[CompanyDashboardVacanciesResponse](
        success=True,
        message="Dashboard vacancies retrieved successfully",
        data=vacancies,
    )


@router.get(
    "/recent-activity",
    response_model=ApiResponse[CompanyDashboardActivityResponse],
    status_code=status.HTTP_200_OK,
    summary="Chronological candidate activity event feed (SKL-11 AC-3)",
)
def get_recent_activity(
    limit: int = Query(15, ge=1, le=50, description="Max event stream items to return"),
    target_company_id: Optional[int] = Query(None, description="Admin override company ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.COMPANY, UserRole.ADMIN)),
) -> ApiResponse[CompanyDashboardActivityResponse]:
    """Retrieve chronological event stream aggregating new applicants, reviews, and interview acceptances."""
    activity = dashboard_service.get_recent_activity(
        db=db,
        current_user=current_user,
        limit=limit,
        target_company_id=target_company_id,
    )
    return ApiResponse[CompanyDashboardActivityResponse](
        success=True,
        message="Recent candidate activity stream retrieved successfully",
        data=activity,
    )


@router.get(
    "/profile-status",
    response_model=ApiResponse[CompanyDashboardProfileStatusResponse],
    status_code=status.HTTP_200_OK,
    summary="Recruiter overview and account verification alert status (SKL-11 AC-4)",
)
def get_dashboard_profile_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.COMPANY, UserRole.ADMIN)),
) -> ApiResponse[CompanyDashboardProfileStatusResponse]:
    """Retrieve company branding, profile completion, and unverified alert banner requirements."""
    profile_status = dashboard_service.get_profile_status(db=db, current_user=current_user)
    return ApiResponse[CompanyDashboardProfileStatusResponse](
        success=True,
        message="Company profile status retrieved successfully",
        data=profile_status,
    )


@router.get(
    "/upcoming-interviews",
    response_model=ApiResponse[List[CompanyDashboardUpcomingInterviewItem]],
    status_code=status.HTTP_200_OK,
    summary="Upcoming scheduled interview sessions for company dashboard widget",
)
def get_upcoming_interviews(
    limit: int = Query(5, ge=1, le=20),
    target_company_id: Optional[int] = Query(None, description="Admin override company ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.COMPANY, UserRole.ADMIN)),
) -> ApiResponse[List[CompanyDashboardUpcomingInterviewItem]]:
    """Retrieve upcoming interview sessions scheduled for candidates with meet links and times."""
    interviews = dashboard_service.get_upcoming_interviews(
        db=db,
        current_user=current_user,
        limit=limit,
        target_company_id=target_company_id,
    )
    return ApiResponse[List[CompanyDashboardUpcomingInterviewItem]](
        success=True,
        message="Upcoming interviews retrieved successfully",
        data=interviews,
    )
