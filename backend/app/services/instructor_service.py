import logging
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from app.core.exceptions import (
    NotFoundException,
    BadRequestException,
)
from app.models.profile import InstructorProfile
from app.models.user import User, UserRole
from app.models.audit_log import AuditLog
from app.repositories.instructor_repository import InstructorRepository
from app.repositories.user_repository import UserRepository
from app.repositories.audit_log_repository import AuditLogRepository
from app.schemas.instructor import (
    InstructorApplicationRequest,
    InstructorProfileUpdateRequest,
    InstructorProfileResponse,
    InstructorDashboardStats,
)

logger = logging.getLogger(__name__)

VALID_STATUSES = {"APPROVED", "REJECTED", "SUSPENDED", "PENDING_REVIEW"}


class InstructorService:
    """Business logic for Instructor Account Management and Admin Review (SKL-52)."""

    def __init__(
        self,
        instructor_repo: InstructorRepository = InstructorRepository(),
        user_repo: UserRepository = UserRepository(),
        audit_repo: AuditLogRepository = AuditLogRepository(),
    ):
        self.instructor_repo = instructor_repo
        self.user_repo = user_repo
        self.audit_repo = audit_repo

    def _serialize(self, profile: InstructorProfile, user: Optional[User] = None) -> InstructorProfileResponse:
        """Map ORM InstructorProfile and linked User to InstructorProfileResponse."""
        owner = user or profile.user
        return InstructorProfileResponse(
            id=profile.id,
            user_id=profile.user_id,
            email=owner.email if owner else "",
            first_name=owner.first_name if owner else "",
            last_name=owner.last_name if owner else "",
            role=owner.role.value if owner and hasattr(owner.role, "value") else str(owner.role if owner else "INSTRUCTOR"),
            is_verified=owner.is_verified if owner else False,
            designation=profile.designation,
            institution=profile.institution,
            qualification=profile.qualification,
            expertise_domain=profile.expertise_domain,
            years_experience=profile.years_experience,
            certificates=profile.certificates,
            intro_video_url=profile.intro_video_url,
            bio=profile.bio,
            linkedin_url=profile.linkedin_url,
            onboarding_status=profile.onboarding_status,
            created_at=profile.created_at,
            updated_at=profile.updated_at,
        )

    def apply_as_instructor(
        self,
        db: Session,
        user: User,
        payload: InstructorApplicationRequest
    ) -> InstructorProfileResponse:
        """Submit or update an instructor application with PENDING_REVIEW status (SKL-52)."""
        profile = self.instructor_repo.get_by_user_id(db, user.id)

        certificates_val = payload.certificates
        if isinstance(certificates_val, list):
            certificates_val = {"items": certificates_val}

        if profile:
            # Update existing application
            if payload.designation is not None:
                profile.designation = payload.designation
            if payload.institution is not None:
                profile.institution = payload.institution
            if payload.qualification is not None:
                profile.qualification = payload.qualification
            if payload.expertise_domain is not None:
                profile.expertise_domain = payload.expertise_domain
            if payload.years_experience is not None:
                profile.years_experience = payload.years_experience
            if payload.certificates is not None:
                profile.certificates = certificates_val
            if payload.intro_video_url is not None:
                profile.intro_video_url = payload.intro_video_url
            if payload.bio is not None:
                profile.bio = payload.bio
            if payload.linkedin_url is not None:
                profile.linkedin_url = payload.linkedin_url

            profile.onboarding_status = "PENDING_REVIEW"
            updated = self.instructor_repo.update(db, profile)
            logger.info("User ID %s resubmitted instructor application. Status set to PENDING_REVIEW", user.id)
            return self._serialize(updated, user)

        # Create new application
        new_profile = InstructorProfile(
            user_id=user.id,
            designation=payload.designation,
            institution=payload.institution,
            qualification=payload.qualification,
            expertise_domain=payload.expertise_domain,
            years_experience=payload.years_experience,
            certificates=certificates_val,
            intro_video_url=payload.intro_video_url,
            bio=payload.bio,
            linkedin_url=payload.linkedin_url,
            onboarding_status="PENDING_REVIEW"
        )
        created = self.instructor_repo.create(db, new_profile)
        logger.info("New instructor application submitted for user ID %s. Status set to PENDING_REVIEW", user.id)
        return self._serialize(created, user)

    def get_profile(self, db: Session, user: User) -> InstructorProfileResponse:
        """Retrieve instructor profile for the current user."""
        profile = self.instructor_repo.get_by_user_id(db, user.id)
        if not profile:
            # If user has INSTRUCTOR role, auto-initialize an initial profile
            if user.role == UserRole.INSTRUCTOR:
                new_profile = InstructorProfile(
                    user_id=user.id,
                    onboarding_status="APPROVED"
                )
                profile = self.instructor_repo.create(db, new_profile)
            else:
                raise NotFoundException(
                    message="Instructor profile not found. Please apply to become an instructor.",
                    error_code="INSTRUCTOR_PROFILE_NOT_FOUND"
                )
        return self._serialize(profile, user)

    def update_profile(
        self,
        db: Session,
        user: User,
        payload: InstructorProfileUpdateRequest
    ) -> InstructorProfileResponse:
        """Update fields on an existing instructor profile."""
        profile = self.instructor_repo.get_by_user_id(db, user.id)
        if not profile:
            raise NotFoundException(
                message="Instructor profile not found. Please apply to become an instructor.",
                error_code="INSTRUCTOR_PROFILE_NOT_FOUND"
            )

        certificates_val = payload.certificates
        if isinstance(certificates_val, list):
            certificates_val = {"items": certificates_val}

        if payload.designation is not None:
            profile.designation = payload.designation
        if payload.institution is not None:
            profile.institution = payload.institution
        if payload.qualification is not None:
            profile.qualification = payload.qualification
        if payload.expertise_domain is not None:
            profile.expertise_domain = payload.expertise_domain
        if payload.years_experience is not None:
            profile.years_experience = payload.years_experience
        if payload.certificates is not None:
            profile.certificates = certificates_val
        if payload.intro_video_url is not None:
            profile.intro_video_url = payload.intro_video_url
        if payload.bio is not None:
            profile.bio = payload.bio
        if payload.linkedin_url is not None:
            profile.linkedin_url = payload.linkedin_url

        updated = self.instructor_repo.update(db, profile)
        return self._serialize(updated, user)

    def get_pending_instructors(self, db: Session, skip: int = 0, limit: int = 50) -> List[InstructorProfileResponse]:
        """Fetch all instructor applications with PENDING_REVIEW status for Admin review."""
        profiles = self.instructor_repo.get_pending_applications(db, skip=skip, limit=limit)
        return [self._serialize(p) for p in profiles]

    def update_instructor_status(
        self,
        db: Session,
        admin_user: User,
        profile_id: int,
        new_status: str,
        reason: Optional[str] = None,
        ip_address: str = "unknown"
    ) -> InstructorProfileResponse:
        """Admin audit action: approve or reject instructor onboarding (SKL-52)."""
        normalized_status = new_status.strip().upper()
        if normalized_status not in VALID_STATUSES:
            raise BadRequestException(
                message=f"Invalid status '{new_status}'. Allowed values: {sorted(list(VALID_STATUSES))}",
                error_code="INVALID_INSTRUCTOR_STATUS"
            )

        profile = self.instructor_repo.get_by_id(db, profile_id)
        if not profile:
            raise NotFoundException(
                message="Instructor profile not found",
                error_code="INSTRUCTOR_PROFILE_NOT_FOUND"
            )

        old_status = profile.onboarding_status
        profile.onboarding_status = normalized_status

        # If approved, elevate user role to INSTRUCTOR and mark as verified
        if normalized_status == "APPROVED":
            profile.user.role = UserRole.INSTRUCTOR
            profile.user.is_verified = True
            logger.info("Admin ID %s approved instructor application ID %s. User ID %s elevated to INSTRUCTOR",
                        admin_user.id, profile.id, profile.user_id)

        # Audit logging (SKL-50 / SKL-52)
        self.audit_repo.create(
            db=db,
            admin_id=admin_user.id,
            target_user_id=profile.user_id,
            action=f"INSTRUCTOR_STATUS_{normalized_status}",
            details={
                "profile_id": profile.id,
                "previous_status": old_status,
                "new_status": normalized_status,
                "target_email": profile.user.email if profile.user else "",
                "reason": reason or "Administrative review"
            },
            ip_address=ip_address
        )
        db.commit()
        db.refresh(profile)

        return self._serialize(profile)

    def get_dashboard_stats(self, db: Session, user: User) -> InstructorDashboardStats:
        """Fetch dashboard counters for the instructor workspace (SKL-52)."""
        profile = self.instructor_repo.get_by_user_id(db, user.id)
        serialized_profile = self._serialize(profile, user) if profile else None
        status = profile.onboarding_status if profile else "PENDING_REVIEW"

        return InstructorDashboardStats(
            active_courses=0,
            total_learners=0,
            mock_tests=0,
            upcoming_interviews=0,
            onboarding_status=status,
            profile=serialized_profile
        )
