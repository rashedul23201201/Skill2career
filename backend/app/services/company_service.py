import logging
import os
import re
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
from fastapi import UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.exceptions import (
    BadRequestException,
    NotFoundException,
    ForbiddenException,
)
from app.models.user import User, UserRole
from app.models.profile import CompanyProfile
from app.repositories.company_repository import CompanyRepository
from app.repositories.user_repository import UserRepository
from app.repositories.audit_log_repository import AuditLogRepository
from app.schemas.company import (
    CompanyProfileUpdateRequest,
    CompanyProfileResponse,
    PublicCompanyProfileResponse,
    AssetUploadResponse,
    CompanyModerationRequest,
)

logger = logging.getLogger(__name__)

# Branding asset upload configuration (SKL-3)
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5 MB
ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
ALLOWED_MIME_TYPES = {
    "image/png",
    "image/jpeg",
    "image/pjpeg",
    "image/webp",
    "image/x-png",
}

BASE_UPLOAD_DIR = Path("uploads/companies")
LOGOS_DIR = BASE_UPLOAD_DIR / "logos"
BANNERS_DIR = BASE_UPLOAD_DIR / "banners"


class CompanyService:
    """Service handling Company Profile Management, Branding Assets, Public Views, and Moderation (SKL-3)."""

    def __init__(
        self,
        company_repo: CompanyRepository = CompanyRepository(),
        user_repo: UserRepository = UserRepository(),
        audit_repo: AuditLogRepository = AuditLogRepository(),
    ):
        self.company_repo = company_repo
        self.user_repo = user_repo
        self.audit_repo = audit_repo

    @staticmethod
    def _validate_image_file(file: UploadFile) -> bytes:
        """
        Validate image extension, MIME type, size <= 5MB, and binary magic bytes.
        Returns the raw contents bytes.
        """
        filename = file.filename or "asset.png"
        file_ext = Path(filename).suffix.lower()

        # 1. Extension inspection
        if file_ext not in ALLOWED_EXTENSIONS:
            logger.warning("Asset rejected: unsupported extension '%s'", file_ext)
            raise BadRequestException(
                message=f"Unsupported file extension '{file_ext}'. Only PNG, JPG/JPEG, and WEBP formats are accepted.",
                error_code="INVALID_FILE_EXTENSION",
            )

        # 2. Content-type header check
        content_type = (file.content_type or "").lower()
        if content_type and content_type not in ALLOWED_MIME_TYPES:
            logger.warning("Asset rejected: unsupported MIME type '%s'", content_type)
            raise BadRequestException(
                message=f"Unsupported MIME type '{content_type}'. Only PNG, JPEG, and WEBP images are allowed.",
                error_code="INVALID_MIME_TYPE",
            )

        # 3. Read content and validate size
        try:
            contents = file.file.read()
        except Exception as e:
            logger.error("Failed to read uploaded image asset: %s", e)
            raise BadRequestException(message="Failed to read uploaded image asset.", error_code="FILE_READ_ERROR")

        file_size = len(contents)
        if file_size == 0:
            raise BadRequestException(message="Uploaded image file is empty (0 bytes).", error_code="EMPTY_FILE")

        if file_size > MAX_IMAGE_SIZE:
            logger.warning("Asset rejected: file size %d exceeds %d bytes limit", file_size, MAX_IMAGE_SIZE)
            raise BadRequestException(
                message="File size exceeds maximum allowable limit of 5MB.",
                error_code="FILE_TOO_LARGE",
            )

        # 4. Deep binary magic bytes inspection
        # PNG: \x89PNG\r\n\x1a\n
        # JPEG: \xff\xd8\xff
        # WEBP: RIFF....WEBP
        is_png = contents.startswith(b"\x89PNG\r\n\x1a\n")
        is_jpeg = contents.startswith(b"\xff\xd8\xff")
        is_webp = contents.startswith(b"RIFF") and len(contents) >= 12 and contents[8:12] == b"WEBP"

        if file_ext == ".png" and not is_png:
            raise BadRequestException(
                message="File content does not match a valid PNG image structure.",
                error_code="INVALID_IMAGE_HEADER",
            )
        if file_ext in {".jpg", ".jpeg"} and not is_jpeg:
            raise BadRequestException(
                message="File content does not match a valid JPEG image structure.",
                error_code="INVALID_IMAGE_HEADER",
            )
        if file_ext == ".webp" and not is_webp:
            raise BadRequestException(
                message="File content does not match a valid WEBP image structure.",
                error_code="INVALID_IMAGE_HEADER",
            )
        if not (is_png or is_jpeg or is_webp):
            raise BadRequestException(
                message="File contents do not match accepted PNG, JPG, or WEBP image formats.",
                error_code="INVALID_IMAGE_STRUCTURE",
            )

        return contents

    def get_or_create_profile(self, db: Session, user: User) -> CompanyProfile:
        """Fetch the company profile for the authenticated user, or initialize a default profile."""
        profile = self.company_repo.get_by_user_id(db, user.id)
        if not profile:
            company_name = f"{user.first_name}'s Organization" if user.first_name else "Organization"
            profile = self.company_repo.create(
                db=db,
                user_id=user.id,
                company_name=company_name,
                industry=None,
                company_size=None,
                contact_person=f"{user.first_name} {user.last_name}".strip() or None,
                contact_phone=None,
                website_url=None,
                office_address=None,
                tagline=None,
                description=None,
                logo_url=None,
                banner_url=None,
                social_links={},
                verification_status="PENDING",
            )
        return profile

    def serialize_profile(self, user: User, profile: CompanyProfile) -> CompanyProfileResponse:
        """Convert CompanyProfile model and associated User into serialized response schema."""
        socials = profile.social_links if isinstance(profile.social_links, dict) else {}
        is_verified = (profile.verification_status == "APPROVED") or bool(user and user.is_verified)

        return CompanyProfileResponse(
            id=profile.id,
            user_id=profile.user_id,
            email=user.email if user else "",
            company_name=profile.company_name,
            tagline=profile.tagline,
            description=profile.description,
            industry=profile.industry,
            company_size=profile.company_size,
            contact_person=profile.contact_person,
            contact_phone=profile.contact_phone,
            website_url=profile.website_url,
            office_address=profile.office_address,
            logo_url=profile.logo_url,
            banner_url=profile.banner_url,
            social_links=socials,
            trade_license_url=profile.trade_license_url,
            verification_status=profile.verification_status,
            is_verified=is_verified,
            created_at=profile.created_at,
            updated_at=profile.updated_at,
        )

    def get_profile(self, db: Session, user: User) -> CompanyProfileResponse:
        """Retrieve authenticated company's complete profile."""
        profile = self.get_or_create_profile(db, user)
        return self.serialize_profile(user, profile)

    def update_profile(
        self,
        db: Session,
        user: User,
        payload: CompanyProfileUpdateRequest
    ) -> CompanyProfileResponse:
        """Update company profile fields and persist to MySQL (SKL-3)."""
        profile = self.get_or_create_profile(db, user)

        if payload.company_name is not None:
            cleaned_name = payload.company_name.strip()
            if cleaned_name:
                profile.company_name = cleaned_name

        if payload.tagline is not None:
            profile.tagline = payload.tagline.strip() if payload.tagline else None

        if payload.description is not None:
            profile.description = payload.description.strip() if payload.description else None

        if payload.industry is not None:
            profile.industry = payload.industry.strip() if payload.industry else None

        if payload.company_size is not None:
            profile.company_size = payload.company_size.strip() if payload.company_size else None

        if payload.contact_person is not None:
            profile.contact_person = payload.contact_person.strip() if payload.contact_person else None

        if payload.contact_phone is not None:
            profile.contact_phone = payload.contact_phone.strip() if payload.contact_phone else None

        if payload.website_url is not None:
            profile.website_url = payload.website_url.strip() if payload.website_url else None

        if payload.office_address is not None:
            profile.office_address = payload.office_address.strip() if payload.office_address else None

        if payload.social_links is not None:
            existing_socials = profile.social_links if isinstance(profile.social_links, dict) else {}
            merged_socials = {**existing_socials, **payload.social_links}
            # Clean empty keys
            cleaned_socials = {k: v for k, v in merged_socials.items() if v}
            profile.social_links = cleaned_socials

        updated = self.company_repo.update(db, profile)
        logger.info("Updated company profile id=%d for user_id=%d", updated.id, user.id)
        return self.serialize_profile(user, updated)

    def upload_logo(self, db: Session, user: User, file: UploadFile) -> AssetUploadResponse:
        """Upload and store company logo image (PNG/JPG/WEBP, max 5MB)."""
        contents = self._validate_image_file(file)
        profile = self.get_or_create_profile(db, user)

        LOGOS_DIR.mkdir(parents=True, exist_ok=True)
        file_ext = Path(file.filename or "logo.png").suffix.lower()
        safe_name = f"company_{profile.id}_logo{file_ext}"
        target_path = LOGOS_DIR / safe_name

        try:
            with open(target_path, "wb") as f:
                f.write(contents)
        except Exception as e:
            logger.error("Failed to write company logo to disk: %s", e)
            raise BadRequestException(message="Failed to persist logo to storage.", error_code="STORAGE_ERROR")

        asset_url = f"/api/v1/companies/assets/logo/{safe_name}"
        profile.logo_url = asset_url
        self.company_repo.update(db, profile)

        logger.info("Uploaded company logo for company_id=%d, path=%s", profile.id, asset_url)
        return AssetUploadResponse(
            message="Company logo uploaded and verified successfully",
            asset_url=asset_url,
            asset_type="logo",
            filename=safe_name,
        )

    def upload_banner(self, db: Session, user: User, file: UploadFile) -> AssetUploadResponse:
        """Upload and store company cover banner image (PNG/JPG/WEBP, max 5MB)."""
        contents = self._validate_image_file(file)
        profile = self.get_or_create_profile(db, user)

        BANNERS_DIR.mkdir(parents=True, exist_ok=True)
        file_ext = Path(file.filename or "banner.png").suffix.lower()
        safe_name = f"company_{profile.id}_banner{file_ext}"
        target_path = BANNERS_DIR / safe_name

        try:
            with open(target_path, "wb") as f:
                f.write(contents)
        except Exception as e:
            logger.error("Failed to write company banner to disk: %s", e)
            raise BadRequestException(message="Failed to persist banner to storage.", error_code="STORAGE_ERROR")

        asset_url = f"/api/v1/companies/assets/banner/{safe_name}"
        profile.banner_url = asset_url
        self.company_repo.update(db, profile)

        logger.info("Uploaded company banner for company_id=%d, path=%s", profile.id, asset_url)
        return AssetUploadResponse(
            message="Company cover banner uploaded and verified successfully",
            asset_url=asset_url,
            asset_type="banner",
            filename=safe_name,
        )

    def get_public_profile(self, db: Session, company_id: int) -> PublicCompanyProfileResponse:
        """
        Public company profile endpoint accessible by Learners/Guests (SKL-3).
        Sanitizes sensitive information (no contact person, phone number, trade license, or user email).
        """
        profile = self.company_repo.get_by_id(db, company_id)
        if not profile:
            raise NotFoundException(
                message=f"Company profile with ID {company_id} was not found",
                error_code="COMPANY_NOT_FOUND"
            )

        socials = profile.social_links if isinstance(profile.social_links, dict) else {}
        is_verified = (profile.verification_status == "APPROVED") or bool(profile.user and profile.user.is_verified)

        return PublicCompanyProfileResponse(
            id=profile.id,
            company_name=profile.company_name,
            tagline=profile.tagline,
            description=profile.description,
            industry=profile.industry,
            company_size=profile.company_size,
            location=profile.office_address,
            office_address=profile.office_address,
            website_url=profile.website_url,
            logo_url=profile.logo_url,
            banner_url=profile.banner_url,
            social_links=socials,
            verification_status=profile.verification_status,
            is_verified=is_verified,
            active_jobs=[],  # Sprint 1 placeholder, populated in Sprint 3
            created_at=profile.created_at,
        )

    def moderate_company(
        self,
        db: Session,
        admin_user: User,
        company_id: int,
        payload: CompanyModerationRequest,
        ip_address: Optional[str] = None
    ) -> CompanyProfileResponse:
        """
        Admin endpoint for company content moderation and verification governance (SKL-3 / SKL-50).
        Records audit logs for compliance tracking.
        """
        profile = self.company_repo.get_by_id(db, company_id)
        if not profile:
            raise NotFoundException(
                message=f"Company with ID {company_id} was not found for moderation",
                error_code="COMPANY_NOT_FOUND"
            )

        # 1. Action / Verification status moderation
        action_name = payload.action.upper() if payload.action else "MODERATION_UPDATE"

        if action_name == "APPROVE" or (payload.verification_status and payload.verification_status.upper() == "APPROVED"):
            profile.verification_status = "APPROVED"
            if profile.user:
                profile.user.is_verified = True
        elif action_name == "REJECT" or (payload.verification_status and payload.verification_status.upper() == "REJECTED"):
            profile.verification_status = "REJECTED"
            if profile.user:
                profile.user.is_verified = False
        elif payload.verification_status:
            profile.verification_status = payload.verification_status.upper()

        if payload.is_verified is not None and profile.user:
            profile.user.is_verified = payload.is_verified

        # 2. Content moderation
        if payload.tagline is not None:
            profile.tagline = payload.tagline.strip() if payload.tagline else None

        if payload.description is not None:
            profile.description = payload.description.strip() if payload.description else None

        updated = self.company_repo.update(db, profile)
        if profile.user:
            db.add(profile.user)
            db.commit()

        # 3. Create administrative audit trail (SKL-50)
        self.audit_repo.create(
            db=db,
            admin_id=admin_user.id,
            target_user_id=profile.user_id,
            action=f"COMPANY_{action_name}",
            details={
                "company_id": company_id,
                "company_name": profile.company_name,
                "verification_status": profile.verification_status,
                "notes": payload.notes,
            },
            ip_address=ip_address,
        )

        logger.info("Admin %d moderated company %d: action=%s", admin_user.id, company_id, action_name)
        return self.serialize_profile(profile.user, updated)

    def serve_asset(self, asset_type: str, filename: str) -> FileResponse:
        """Deliver company branding asset with path-traversal prevention."""
        cleaned_type = asset_type.lower().strip()
        if cleaned_type not in {"logo", "banner"}:
            raise BadRequestException(message="Invalid asset category.", error_code="INVALID_ASSET_TYPE")

        # Sanitize filename
        safe_filename = os.path.basename(filename)
        target_dir = LOGOS_DIR if cleaned_type == "logo" else BANNERS_DIR
        target_path = target_dir / safe_filename

        if not target_path.exists() or not target_path.is_file():
            raise NotFoundException(message="Requested image asset was not found.", error_code="ASSET_NOT_FOUND")

        file_ext = target_path.suffix.lower()
        if file_ext == ".png":
            media_type = "image/png"
        elif file_ext in {".jpg", ".jpeg"}:
            media_type = "image/jpeg"
        elif file_ext == ".webp":
            media_type = "image/webp"
        else:
            media_type = "application/octet-stream"

        return FileResponse(path=str(target_path), media_type=media_type)
