from typing import Optional, List, Dict, Any
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload
from app.models.profile import CompanyProfile


class CompanyRepository:
    """Repository handling database operations for the CompanyProfile entity (SKL-3)."""

    @staticmethod
    def get_by_id(db: Session, company_id: int) -> Optional[CompanyProfile]:
        """Retrieve company profile by primary key ID with associated user record."""
        statement = (
            select(CompanyProfile)
            .options(joinedload(CompanyProfile.user))
            .where(CompanyProfile.id == company_id)
        )
        return db.execute(statement).scalar_one_or_none()

    @staticmethod
    def get_by_user_id(db: Session, user_id: int) -> Optional[CompanyProfile]:
        """Retrieve company profile by associated User ID."""
        statement = (
            select(CompanyProfile)
            .options(joinedload(CompanyProfile.user))
            .where(CompanyProfile.user_id == user_id)
        )
        return db.execute(statement).scalar_one_or_none()

    @staticmethod
    def create(
        db: Session,
        user_id: int,
        company_name: str,
        industry: Optional[str] = None,
        company_size: Optional[str] = None,
        contact_person: Optional[str] = None,
        contact_phone: Optional[str] = None,
        website_url: Optional[str] = None,
        office_address: Optional[str] = None,
        tagline: Optional[str] = None,
        description: Optional[str] = None,
        logo_url: Optional[str] = None,
        banner_url: Optional[str] = None,
        social_links: Optional[Dict[str, Any]] = None,
        trade_license_url: Optional[str] = None,
        verification_status: str = "PENDING",
    ) -> CompanyProfile:
        """Create and persist a new CompanyProfile record."""
        profile = CompanyProfile(
            user_id=user_id,
            company_name=company_name,
            industry=industry,
            company_size=company_size,
            contact_person=contact_person,
            contact_phone=contact_phone,
            website_url=website_url,
            office_address=office_address,
            tagline=tagline,
            description=description,
            logo_url=logo_url,
            banner_url=banner_url,
            social_links=social_links or {},
            trade_license_url=trade_license_url,
            verification_status=verification_status,
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
        return profile

    @staticmethod
    def update(db: Session, profile: CompanyProfile) -> CompanyProfile:
        """Persist updates to an existing CompanyProfile."""
        db.commit()
        db.refresh(profile)
        return profile

    @staticmethod
    def list_public(db: Session, limit: int = 50, offset: int = 0) -> List[CompanyProfile]:
        """List company profiles for public discovery."""
        statement = (
            select(CompanyProfile)
            .options(joinedload(CompanyProfile.user))
            .order_by(CompanyProfile.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(db.execute(statement).scalars().all())
