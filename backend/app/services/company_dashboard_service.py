"""Recruitment operations and company dashboard aggregation service (SKL-11)."""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User, UserRole
from app.repositories.company_dashboard_repository import CompanyDashboardRepository
from app.schemas.company_dashboard import (
    CompanyDashboardMetricsResponse,
    CompanyDashboardVacanciesResponse,
    CompanyDashboardVacancyItem,
    CompanyDashboardActivityResponse,
    CandidateActivityEvent,
    CompanyDashboardProfileStatusResponse,
    CompanyDashboardUpcomingInterviewItem,
    DashboardStageBreakdown,
    VacancyStageCounts,
)


class CompanyDashboardService:
    """Coordinates business logic and metrics aggregation for Company Dashboard (SKL-11)."""

    def __init__(self, repository: Optional[CompanyDashboardRepository] = None):
        self.repo = repository or CompanyDashboardRepository()

    def _resolve_company_id(self, user: User, target_company_id: Optional[int] = None) -> int:
        """Resolve company ID: for company users, strictly own ID; for admin, allows override."""
        if user.role == UserRole.ADMIN and target_company_id:
            return target_company_id
        return user.id

    def get_metrics(
        self,
        db: Session,
        current_user: User,
        target_company_id: Optional[int] = None,
    ) -> CompanyDashboardMetricsResponse:
        """Fetch recruitment KPI metrics and stage volume breakdown (SKL-11 AC-1)."""
        company_id = self._resolve_company_id(current_user, target_company_id)
        raw_metrics = self.repo.get_recruitment_metrics(db=db, company_id=company_id)

        breakdown_data = raw_metrics.get("stage_breakdown", {})
        stage_breakdown = DashboardStageBreakdown(
            applied=breakdown_data.get("applied", 0),
            shortlisted=breakdown_data.get("shortlisted", 0),
            interview_scheduled=breakdown_data.get("interview_scheduled", 0),
            offered=breakdown_data.get("offered", 0),
            rejected=breakdown_data.get("rejected", 0),
            withdrawn=breakdown_data.get("withdrawn", 0),
        )

        return CompanyDashboardMetricsResponse(
            active_jobs=raw_metrics["active_jobs"],
            total_applications=raw_metrics["total_applications"],
            shortlisted=raw_metrics["shortlisted"],
            scheduled_interviews=raw_metrics["scheduled_interviews"],
            pending_reviews=raw_metrics["pending_reviews"],
            stage_breakdown=stage_breakdown,
            growth_indicators=raw_metrics["growth_indicators"],
        )

    def get_vacancies(
        self,
        db: Session,
        current_user: User,
        status: Optional[str] = "ACTIVE",
        limit: int = 50,
        offset: int = 0,
        target_company_id: Optional[int] = None,
    ) -> CompanyDashboardVacanciesResponse:
        """Fetch active/filtered vacancies with candidate volumes per hiring stage (SKL-11 AC-2)."""
        company_id = self._resolve_company_id(current_user, target_company_id)
        items_raw, total, active_count = self.repo.get_vacancies_with_stages(
            db=db,
            company_id=company_id,
            status=status,
            limit=limit,
            offset=offset,
        )

        items = [
            CompanyDashboardVacancyItem(
                id=item["id"],
                title=item["title"],
                posting_type=item["posting_type"],
                work_mode=item["work_mode"],
                location=item["location"],
                status=item["status"],
                compensation=item["compensation"],
                salary_min=item.get("salary_min"),
                salary_max=item.get("salary_max"),
                experience_level=item.get("experience_level"),
                category=item.get("category"),
                applications_count=item["applications_count"],
                deadline=item.get("deadline"),
                created_at=item["created_at"],
                stages=VacancyStageCounts(**item.get("stages", {})),
            )
            for item in items_raw
        ]

        return CompanyDashboardVacanciesResponse(
            items=items,
            total=total,
            active_count=active_count,
        )

    def get_recent_activity(
        self,
        db: Session,
        current_user: User,
        limit: int = 15,
        target_company_id: Optional[int] = None,
    ) -> CompanyDashboardActivityResponse:
        """Fetch chronological candidate activity event stream (SKL-11 AC-3)."""
        company_id = self._resolve_company_id(current_user, target_company_id)
        raw_events = self.repo.get_recent_activity(db=db, company_id=company_id, limit=limit)

        events = [
            CandidateActivityEvent(
                id=ev["id"],
                type=ev["type"],
                candidate_id=ev["candidate_id"],
                candidate_name=ev["candidate_name"],
                candidate_initials=ev["candidate_initials"],
                candidate_email=ev.get("candidate_email"),
                job_id=ev["job_id"],
                job_title=ev["job_title"],
                status=ev["status"],
                timestamp=ev["timestamp"],
                description=ev["description"],
                application_id=ev.get("application_id"),
                interview_id=ev.get("interview_id"),
            )
            for ev in raw_events
        ]

        return CompanyDashboardActivityResponse(
            items=events,
            total=len(events),
        )

    def get_profile_status(
        self,
        db: Session,
        current_user: User,
    ) -> CompanyDashboardProfileStatusResponse:
        """Fetch company identity details, verification state, and alert indicators (SKL-11 AC-4)."""
        status_data = self.repo.get_profile_status(db=db, user=current_user)
        return CompanyDashboardProfileStatusResponse(**status_data)

    def get_upcoming_interviews(
        self,
        db: Session,
        current_user: User,
        limit: int = 5,
        target_company_id: Optional[int] = None,
    ) -> List[CompanyDashboardUpcomingInterviewItem]:
        """Fetch scheduled upcoming interviews for company dashboard display."""
        company_id = self._resolve_company_id(current_user, target_company_id)
        raw_interviews = self.repo.get_upcoming_interviews(db=db, company_id=company_id, limit=limit)
        return [CompanyDashboardUpcomingInterviewItem(**item) for item in raw_interviews]
