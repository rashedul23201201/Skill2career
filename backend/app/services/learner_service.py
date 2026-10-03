import logging
import os
from pathlib import Path
from typing import Tuple, List, Dict, Any, Optional
from datetime import datetime
from fastapi import UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestException, NotFoundException, ForbiddenException
from app.models.user import User, UserRole
from app.models.profile import LearnerProfile
from app.repositories.learner_repository import LearnerRepository
from app.schemas.learner import (
    LearnerProfileUpdateRequest,
    LearnerProfileResponse,
    ResumeUploadResponse,
    ProfileCompletionBreakdown,
    CompletionSectionStatus,
)

logger = logging.getLogger(__name__)

# Upload configuration
MAX_RESUME_SIZE = 5 * 1024 * 1024  # 5 MB
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc"}
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
    "application/octet-stream",
}
UPLOAD_DIR = Path("uploads/resumes")


class LearnerService:
    """Service handling Learner Profile logic, Dynamic Completion Algorithm, and Resume Management (SKL-51)."""

    def __init__(self, learner_repo: LearnerRepository = LearnerRepository()):
        self.learner_repo = learner_repo

    @staticmethod
    def extract_skills_list(raw_skills: Any) -> List[str]:
        """Normalize skills stored in JSON column to a unique list of non-empty strings."""
        if not raw_skills:
            return []
        if isinstance(raw_skills, list):
            items = raw_skills
        elif isinstance(raw_skills, dict):
            items = raw_skills.get("items") or raw_skills.get("skills") or []
        else:
            return []

        cleaned: List[str] = []
        for s in items:
            if isinstance(s, str) and s.strip():
                clean_s = s.strip()
                if clean_s not in cleaned:
                    cleaned.append(clean_s)
        return cleaned

    @classmethod
    def calculate_completion(cls, user: User, profile: LearnerProfile) -> Tuple[int, ProfileCompletionBreakdown]:
        """
        Dynamic Profile Completion Algorithm (SKL-51):
        - Basic Info (name, email, phone, location) = 25%
        - Educational Background (institution, degree/department) = 25%
        - Career & Skills (target role, primary track, >=3 skills) = 25%
        - Uploaded Resume/CV = 25%
        """
        # 1. Basic Info (25%)
        has_name = bool(user.first_name and user.first_name.strip())
        has_email = bool(user.email and user.email.strip())
        has_phone = bool(profile.phone_number and profile.phone_number.strip())
        has_location = bool(profile.location and profile.location.strip())
        basic_info_complete = has_name and has_email and has_phone and has_location
        basic_info_status = CompletionSectionStatus(
            label="Basic Information",
            weight=25,
            is_complete=basic_info_complete,
            description="Full name, registered email, active phone number, and current location",
        )

        # 2. Educational Background (25%)
        has_institution = bool(profile.institution and profile.institution.strip())
        portfolio_dict = profile.portfolio_links if isinstance(profile.portfolio_links, dict) else {}
        has_department = bool(profile.department and profile.department.strip()) or bool(
            portfolio_dict.get("degree") and str(portfolio_dict.get("degree")).strip()
        )
        education_complete = has_institution and has_department
        education_status = CompletionSectionStatus(
            label="Educational Background",
            weight=25,
            is_complete=education_complete,
            description="College/University institution and academic department or degree major",
        )

        # 3. Career & Skills (25%)
        has_target_role = bool(profile.target_role and profile.target_role.strip())
        has_primary_track = bool(profile.primary_track and profile.primary_track.strip())
        skills_list = cls.extract_skills_list(profile.skills)
        has_min_skills = len(skills_list) >= 3
        career_complete = has_target_role and has_primary_track and has_min_skills
        career_status = CompletionSectionStatus(
            label="Career & Skills",
            weight=25,
            is_complete=career_complete,
            description="Target job role, primary career track, and at least 3 tagged competency skills",
        )

        # 4. Uploaded Resume/CV (25%)
        resume_complete = bool(
            (profile.resume_url and profile.resume_url.strip())
            or (profile.resume_filename and profile.resume_filename.strip())
        )
        resume_status = CompletionSectionStatus(
            label="Curriculum Vitae (CV) / Resume",
            weight=25,
            is_complete=resume_complete,
            description="Validated PDF or DOCX resume document uploaded to platform",
        )

        total_score = 0
        if basic_info_complete:
            total_score += 25
        if education_complete:
            total_score += 25
        if career_complete:
            total_score += 25
        if resume_complete:
            total_score += 25

        breakdown = ProfileCompletionBreakdown(
            percentage=total_score,
            basic_info=basic_info_status,
            education=education_status,
            career_skills=career_status,
            resume=resume_status,
        )

        return total_score, breakdown

    def get_or_create_profile(self, db: Session, user: User) -> LearnerProfile:
        """Fetch the learner profile or initialize a new default profile if one does not exist yet."""
        profile = self.learner_repo.get_by_user_id(db, user.id)
        if not profile:
            profile = self.learner_repo.create(
                db=db,
                user_id=user.id,
                phone_number=None,
                location=None,
                bio=None,
                target_role=None,
                primary_track=None,
                institution=None,
                department=None,
                skills=[],
                portfolio_links={},
                completion_pct=0,
            )
        return profile

    def serialize_profile(self, user: User, profile: LearnerProfile) -> LearnerProfileResponse:
        """Convert LearnerProfile model into serialized response schema with calculated breakdown."""
        score, breakdown = self.calculate_completion(user, profile)
        skills_list = self.extract_skills_list(profile.skills)
        portfolio_dict = profile.portfolio_links if isinstance(profile.portfolio_links, dict) else {}

        return LearnerProfileResponse(
            id=profile.id,
            user_id=profile.user_id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            role=user.role.value if hasattr(user.role, "value") else str(user.role),
            is_verified=user.is_verified,
            phone_number=profile.phone_number,
            location=profile.location,
            bio=profile.bio,
            target_role=profile.target_role,
            primary_track=profile.primary_track,
            institution=profile.institution,
            department=profile.department,
            skills=skills_list,
            resume_url=profile.resume_url,
            resume_filename=profile.resume_filename,
            portfolio_links=portfolio_dict,
            completion_pct=score,
            completion_breakdown=breakdown,
            created_at=profile.created_at,
            updated_at=profile.updated_at,
        )

    def get_profile(self, db: Session, user: User) -> LearnerProfileResponse:
        """Retrieve authenticated learner's complete profile with dynamic completion score."""
        profile = self.get_or_create_profile(db, user)
        score, _ = self.calculate_completion(user, profile)
        if profile.completion_pct != score:
            profile.completion_pct = score
            self.learner_repo.update(db, profile)

        return self.serialize_profile(user, profile)

    def update_profile(
        self,
        db: Session,
        user: User,
        payload: LearnerProfileUpdateRequest
    ) -> LearnerProfileResponse:
        """Update learner profile fields, recalculate completion score, and persist."""
        profile = self.get_or_create_profile(db, user)

        if payload.phone_number is not None:
            profile.phone_number = payload.phone_number.strip() if payload.phone_number else None
        if payload.location is not None:
            profile.location = payload.location.strip() if payload.location else None
        if payload.bio is not None:
            profile.bio = payload.bio.strip() if payload.bio else None
        if payload.target_role is not None:
            profile.target_role = payload.target_role.strip() if payload.target_role else None
        if payload.primary_track is not None:
            profile.primary_track = payload.primary_track.strip() if payload.primary_track else None
        if payload.institution is not None:
            profile.institution = payload.institution.strip() if payload.institution else None
        if payload.department is not None:
            profile.department = payload.department.strip() if payload.department else None

        if payload.skills is not None:
            cleaned_skills = []
            for s in payload.skills:
                if isinstance(s, str) and s.strip():
                    item = s.strip()
                    if item not in cleaned_skills:
                        cleaned_skills.append(item)
            profile.skills = {"items": cleaned_skills}

        if payload.portfolio_links is not None:
            profile.portfolio_links = payload.portfolio_links

        # Dynamically recalculate completion score
        score, breakdown = self.calculate_completion(user, profile)
        profile.completion_pct = score

        updated_profile = self.learner_repo.update(db, profile)
        return self.serialize_profile(user, updated_profile)

    def upload_resume(self, db: Session, user: User, file: UploadFile) -> ResumeUploadResponse:
        """
        Validate and store uploaded resume document with MIME inspection (AC-2).
        Requires PDF or DOCX under 5MB.
        """
        filename = file.filename or "resume.pdf"
        file_ext = Path(filename).suffix.lower()

        # 1. Extension validation
        if file_ext not in ALLOWED_EXTENSIONS:
            logger.warning("Resume rejected: unsupported extension '%s' for user %s", file_ext, user.id)
            raise BadRequestException(
                message=f"Unsupported file extension '{file_ext}'. Only PDF (.pdf) and Word documents (.docx, .doc) are accepted.",
                error_code="INVALID_FILE_EXTENSION",
            )

        # 2. Content-type header check
        content_type = file.content_type or ""
        if content_type and content_type not in ALLOWED_MIME_TYPES:
            logger.warning("Resume rejected: unsupported MIME type '%s' for user %s", content_type, user.id)
            raise BadRequestException(
                message=f"Unsupported MIME type '{content_type}'. Only PDF and DOCX files are allowed.",
                error_code="INVALID_MIME_TYPE",
            )

        # 3. Read content and validate size
        try:
            contents = file.file.read()
        except Exception as e:
            logger.error("Failed to read uploaded resume for user %s: %s", user.id, e)
            raise BadRequestException(message="Failed to read uploaded file.", error_code="FILE_READ_ERROR")

        file_size = len(contents)
        if file_size == 0:
            raise BadRequestException(message="Uploaded file is empty (0 bytes).", error_code="EMPTY_FILE")

        if file_size > MAX_RESUME_SIZE:
            logger.warning("Resume rejected: file size %s exceeds %s for user %s", file_size, MAX_RESUME_SIZE, user.id)
            raise BadRequestException(
                message="File size exceeds maximum allowable limit of 5MB.",
                error_code="FILE_TOO_LARGE",
            )

        # 4. Deep magic-bytes validation
        # PDF magic bytes: starts with b"%PDF"
        # DOCX/ZIP magic bytes: starts with b"PK\x03\x04"
        is_pdf = contents.startswith(b"%PDF")
        is_docx = contents.startswith(b"PK\x03\x04") or contents.startswith(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1")  # legacy .doc compound binary

        if file_ext == ".pdf" and not is_pdf:
            raise BadRequestException(
                message="File content does not match a valid PDF document structure.",
                error_code="INVALID_FILE_HEADER",
            )
        if file_ext in {".docx", ".doc"} and not is_docx:
            raise BadRequestException(
                message="File content does not match a valid Word document structure.",
                error_code="INVALID_FILE_HEADER",
            )
        if not (is_pdf or is_docx):
            raise BadRequestException(
                message="File contents do not match accepted PDF or DOCX formats.",
                error_code="INVALID_DOCUMENT_STRUCTURE",
            )

        # 5. Persist document to disk
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        safe_name = f"user_{user.id}_resume{file_ext}"
        target_path = UPLOAD_DIR / safe_name

        try:
            with open(target_path, "wb") as f:
                f.write(contents)
        except Exception as e:
            logger.error("Failed to write resume to disk: %s", e)
            raise BadRequestException(message="Failed to save resume file to server storage.", error_code="STORAGE_ERROR")

        # 6. Update database record
        profile = self.get_or_create_profile(db, user)
        download_url = "/api/v1/learners/resume/download"
        profile.resume_url = download_url
        profile.resume_filename = filename

        # Recalculate completion score
        score, breakdown = self.calculate_completion(user, profile)
        profile.completion_pct = score

        self.learner_repo.update(db, profile)

        return ResumeUploadResponse(
            message="Resume document uploaded and verified successfully",
            resume_url=download_url,
            resume_filename=filename,
            completion_pct=score,
            completion_breakdown=breakdown,
        )

    def download_resume(self, db: Session, user: User) -> FileResponse:
        """Retrieve uploaded resume document for authenticated user."""
        profile = self.learner_repo.get_by_user_id(db, user.id)
        if not profile or not profile.resume_filename:
            raise NotFoundException(message="No resume has been uploaded for this account.", error_code="RESUME_NOT_FOUND")

        file_ext = Path(profile.resume_filename).suffix.lower()
        target_path = UPLOAD_DIR / f"user_{user.id}_resume{file_ext}"

        if not target_path.exists():
            raise NotFoundException(message="Resume file not found on server storage.", error_code="FILE_NOT_FOUND")

        media_type = "application/pdf" if file_ext == ".pdf" else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        return FileResponse(
            path=str(target_path),
            filename=profile.resume_filename,
            media_type=media_type,
        )

    def delete_resume(self, db: Session, user: User) -> LearnerProfileResponse:
        """Remove resume from learner profile and decrement completion score accordingly."""
        profile = self.get_or_create_profile(db, user)
        if profile.resume_filename:
            file_ext = Path(profile.resume_filename).suffix.lower()
            target_path = UPLOAD_DIR / f"user_{user.id}_resume{file_ext}"
            if target_path.exists():
                try:
                    os.remove(target_path)
                except Exception as e:
                    logger.warning("Could not delete resume file %s: %s", target_path, e)

        profile.resume_url = None
        profile.resume_filename = None

        score, _ = self.calculate_completion(user, profile)
        profile.completion_pct = score
        updated_profile = self.learner_repo.update(db, profile)

        return self.serialize_profile(user, updated_profile)
