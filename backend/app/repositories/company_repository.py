from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload
from app.models.profile import CompanyProfile
from app.models.user import User
from app.schemas.company import CompanyVerificationRequest


class CompanyRepository:
    """Data-access repository for CompanyProfile and verification pipelines (SKL-2)."""

    @staticmethod
    def get_by_id(db: Session, company_id: int) -> Optional[CompanyProfile]:
        """Fetch CompanyProfile by its primary key ID."""
        stmt = select(CompanyProfile).options(joinedload(CompanyProfile.user)).where(CompanyProfile.id == company_id)
        return db.execute(stmt).scalars().first()

    @staticmethod
    def get_by_user_id(db: Session, user_id: int) -> Optional[CompanyProfile]:
        """Fetch CompanyProfile by user ID."""
        stmt = select(CompanyProfile).options(joinedload(CompanyProfile.user)).where(CompanyProfile.user_id == user_id)
        return db.execute(stmt).scalars().first()

    @staticmethod
    def get_pending_verifications(db: Session) -> List[CompanyProfile]:
        """Retrieve all company profiles awaiting administrative review."""
        stmt = (
            select(CompanyProfile)
            .options(joinedload(CompanyProfile.user))
            .where(CompanyProfile.verification_status == "PENDING")
            .order_by(CompanyProfile.created_at.desc())
        )
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def submit_verification(
        db: Session,
        profile: CompanyProfile,
        payload: CompanyVerificationRequest
    ) -> CompanyProfile:
        """Update verification dossier fields and flag verification_status as PENDING."""
        if payload.company_name:
            profile.company_name = payload.company_name.strip()
        if payload.trade_license_url:
            profile.trade_license_url = payload.trade_license_url.strip()
        if payload.registration_number is not None:
            profile.registration_number = payload.registration_number.strip() if payload.registration_number else None
        if payload.industry is not None:
            profile.industry = payload.industry.strip() if payload.industry else None
        if payload.location is not None:
            profile.location = payload.location.strip() if payload.location else None
        if payload.company_size is not None:
            profile.company_size = payload.company_size.strip() if payload.company_size else None
        if payload.website_url is not None:
            profile.website_url = payload.website_url.strip() if payload.website_url else None
        if payload.office_address is not None:
            profile.office_address = payload.office_address.strip() if payload.office_address else None
        if payload.contact_person is not None:
            profile.contact_person = payload.contact_person.strip() if payload.contact_person else None
        if payload.contact_phone is not None:
            profile.contact_phone = payload.contact_phone.strip() if payload.contact_phone else None
        if payload.description is not None:
            profile.description = payload.description.strip() if payload.description else None

        # Reset verification status to PENDING on new/updated dossier submission
        profile.verification_status = "PENDING"
        profile.verified_at = None
        profile.verified_by_admin_id = None
        profile.verification_notes = None

        db.commit()
        db.refresh(profile)
        return profile

    @staticmethod
    def verify_company(
        db: Session,
        profile: CompanyProfile,
        user: User,
        action: str,
        admin_id: int,
        notes: Optional[str] = None
    ) -> CompanyProfile:
        """Admin decision processor: updates verification_status and user.is_verified."""
        if action == "APPROVE":
            profile.verification_status = "APPROVED"
            profile.verified_at = datetime.now(timezone.utc)
            profile.verified_by_admin_id = admin_id
            profile.verification_notes = notes
            user.is_verified = True
        elif action == "REJECT":
            profile.verification_status = "REJECTED"
            profile.verified_at = None
            profile.verified_by_admin_id = admin_id
            profile.verification_notes = notes
            user.is_verified = False

        db.commit()
        db.refresh(profile)
        db.refresh(user)
        return profile
