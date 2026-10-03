import logging
from typing import Optional, List
from sqlalchemy.orm import Session

from app.core.exceptions import (
    NotFoundException,
    BadRequestException,
    ForbiddenException,
)
from app.models.user import User, UserRole
from app.models.profile import CompanyProfile
from app.repositories.company_repository import CompanyRepository
from app.repositories.audit_log_repository import AuditLogRepository
from app.schemas.company import (
    CompanyVerificationRequest,
    CompanyVerificationStatusResponse,
    PendingCompanyVerificationItem,
)

logger = logging.getLogger(__name__)


class CompanyService:
    """Business logic service for company registration, verification dossier pipelines, and admin review (SKL-2)."""

    def __init__(
        self,
        company_repo: CompanyRepository = CompanyRepository(),
        audit_repo: AuditLogRepository = AuditLogRepository(),
    ):
        self.company_repo = company_repo
        self.audit_repo = audit_repo

    def get_or_create_profile(self, db: Session, user: User) -> CompanyProfile:
        """Fetch existing company profile for user or initialize if absent."""
        profile = self.company_repo.get_by_user_id(db, user.id)
        if not profile:
            profile = CompanyProfile(
                user_id=user.id,
                company_name=f"{user.first_name}'s Organization",
                verification_status="PENDING",
            )
            db.add(profile)
            db.commit()
            db.refresh(profile)
        return profile

    def get_verification_status(self, db: Session, user: User) -> CompanyVerificationStatusResponse:
        """Retrieve current verification state and dossier details for company user."""
        profile = self.get_or_create_profile(db, user)
        return CompanyVerificationStatusResponse(
            company_id=profile.id,
            user_id=user.id,
            company_name=profile.company_name,
            is_verified=user.is_verified,
            verification_status=profile.verification_status,
            trade_license_url=profile.trade_license_url,
            registration_number=profile.registration_number,
            industry=profile.industry,
            location=profile.location,
            company_size=profile.company_size,
            website_url=profile.website_url,
            office_address=profile.office_address,
            contact_person=profile.contact_person,
            contact_phone=profile.contact_phone,
            description=profile.description,
            verified_at=profile.verified_at,
            verified_by_admin_id=profile.verified_by_admin_id,
            verification_notes=profile.verification_notes,
            created_at=profile.created_at,
            updated_at=profile.updated_at,
        )

    def submit_verification_request(
        self,
        db: Session,
        user: User,
        payload: CompanyVerificationRequest
    ) -> CompanyVerificationStatusResponse:
        """Process company submission of trade license and credentials dossier for verification."""
        profile = self.get_or_create_profile(db, user)

        if not payload.trade_license_url or not payload.trade_license_url.strip():
            raise BadRequestException(
                message="An official trade license URL or document reference is required for verification",
                error_code="TRADE_LICENSE_REQUIRED"
            )

        updated_profile = self.company_repo.submit_verification(db, profile, payload)

        logger.info(
            "Company verification dossier submitted for review: Company ID=%s, User ID=%s, Org='%s'",
            updated_profile.id, user.id, updated_profile.company_name
        )

        return CompanyVerificationStatusResponse(
            company_id=updated_profile.id,
            user_id=user.id,
            company_name=updated_profile.company_name,
            is_verified=user.is_verified,
            verification_status=updated_profile.verification_status,
            trade_license_url=updated_profile.trade_license_url,
            registration_number=updated_profile.registration_number,
            industry=updated_profile.industry,
            location=updated_profile.location,
            company_size=updated_profile.company_size,
            website_url=updated_profile.website_url,
            office_address=updated_profile.office_address,
            contact_person=updated_profile.contact_person,
            contact_phone=updated_profile.contact_phone,
            description=updated_profile.description,
            verified_at=updated_profile.verified_at,
            verified_by_admin_id=updated_profile.verified_by_admin_id,
            verification_notes=updated_profile.verification_notes,
            created_at=updated_profile.created_at,
            updated_at=updated_profile.updated_at,
        )

    def get_pending_verifications(self, db: Session) -> List[PendingCompanyVerificationItem]:
        """Fetch list of all companies currently awaiting administrative review."""
        pending_profiles = self.company_repo.get_pending_verifications(db)
        items: List[PendingCompanyVerificationItem] = []

        for p in pending_profiles:
            user_email = p.user.email if p.user else "unknown"
            items.append(
                PendingCompanyVerificationItem(
                    company_id=p.id,
                    user_id=p.user_id,
                    email=user_email,
                    company_name=p.company_name,
                    trade_license_url=p.trade_license_url,
                    registration_number=p.registration_number,
                    industry=p.industry,
                    location=p.location,
                    company_size=p.company_size,
                    website_url=p.website_url,
                    office_address=p.office_address,
                    contact_person=p.contact_person,
                    contact_phone=p.contact_phone,
                    verification_status=p.verification_status,
                    verification_notes=p.verification_notes,
                    submitted_at=p.updated_at or p.created_at,
                )
            )

        return items

    def process_verification(
        self,
        db: Session,
        admin_user: User,
        company_id: int,
        action: str,
        notes: Optional[str] = None,
        ip_address: str = "unknown"
    ) -> CompanyVerificationStatusResponse:
        """Admin execution to approve or reject a company verification dossier."""
        norm_action = action.strip().upper()
        if norm_action not in ("APPROVE", "REJECT"):
            raise BadRequestException(
                message=f"Invalid verification action '{action}'. Must be 'APPROVE' or 'REJECT'.",
                error_code="INVALID_VERIFICATION_ACTION"
            )

        profile = self.company_repo.get_by_id(db, company_id)
        if not profile:
            raise NotFoundException(
                message=f"Company profile with ID {company_id} does not exist",
                error_code="COMPANY_NOT_FOUND"
            )

        company_user = profile.user
        if not company_user:
            raise NotFoundException(
                message="Associated user account for company profile not found",
                error_code="USER_NOT_FOUND"
            )

        updated_profile = self.company_repo.verify_company(
            db=db,
            profile=profile,
            user=company_user,
            action=norm_action,
            admin_id=admin_user.id,
            notes=notes
        )

        audit_action = "COMPANY_VERIFICATION_APPROVED" if norm_action == "APPROVE" else "COMPANY_VERIFICATION_REJECTED"
        audit_reason = f"Decision: {norm_action}. Organization: '{updated_profile.company_name}'"
        if notes:
            audit_reason += f" | Notes: {notes}"

        self.audit_repo.create(
            db=db,
            admin_id=admin_user.id,
            target_user_id=company_user.id,
            action=audit_action,
            details={
                "decision": norm_action,
                "notes": notes,
                "company_id": updated_profile.id,
                "company_name": updated_profile.company_name,
            },
            ip_address=ip_address
        )

        logger.info(
            "Admin ID=%s executed %s on Company ID=%s (User ID=%s). Status now: %s",
            admin_user.id, norm_action, profile.id, company_user.id, updated_profile.verification_status
        )

        return CompanyVerificationStatusResponse(
            company_id=updated_profile.id,
            user_id=company_user.id,
            company_name=updated_profile.company_name,
            is_verified=company_user.is_verified,
            verification_status=updated_profile.verification_status,
            trade_license_url=updated_profile.trade_license_url,
            registration_number=updated_profile.registration_number,
            industry=updated_profile.industry,
            location=updated_profile.location,
            company_size=updated_profile.company_size,
            website_url=updated_profile.website_url,
            office_address=updated_profile.office_address,
            contact_person=updated_profile.contact_person,
            contact_phone=updated_profile.contact_phone,
            description=updated_profile.description,
            verified_at=updated_profile.verified_at,
            verified_by_admin_id=updated_profile.verified_by_admin_id,
            verification_notes=updated_profile.verification_notes,
            created_at=updated_profile.created_at,
            updated_at=updated_profile.updated_at,
        )
