import os
import re
import math
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple
from fastapi import UploadFile
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.exceptions import (
    NotFoundException,
    ForbiddenException,
    BadRequestException,
)
from app.models.user import User, UserRole
from app.models.job import JobPosting, JobStatus
from app.models.application import JobApplication, ApplicationStatus
from app.models.screening import (
    ScreeningQuestion,
    CandidateEvaluation,
    CandidateStatus,
    DealBreakerRule,
)
from app.repositories.job_repository import JobRepository
from app.repositories.application_repository import ApplicationRepository
from app.repositories.screening_repository import ScreeningRepository
from app.repositories.audit_log_repository import AuditLogRepository
from app.schemas.application import (
    ApplicationCreateRequest,
    ApplicationStatusUpdateRequest,
    JobApplicationResponse,
    PaginatedApplicationResponse,
    ApplicationCheckResponse,
)

logger = logging.getLogger(__name__)

UPLOAD_DIR = Path("uploads/resumes")
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


def _extract_number(val: Any) -> Optional[float]:
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    match = re.search(r"[-+]?\d*\.?\d+", str(val).strip())
    if match:
        try:
            return float(match.group(0))
        except ValueError:
            return None
    return None


class ApplicationService:
    def __init__(
        self,
        application_repo: ApplicationRepository = ApplicationRepository(),
        job_repo: JobRepository = JobRepository(),
        screening_repo: ScreeningRepository = ScreeningRepository(),
        audit_repo: AuditLogRepository = AuditLogRepository(),
    ):
        self.application_repo = application_repo
        self.job_repo = job_repo
        self.screening_repo = screening_repo
        self.audit_repo = audit_repo

    def _format_application_response(self, app: JobApplication) -> JobApplicationResponse:
        job = app.job
        company = job.company if job else None
        company_profile = getattr(company, "company_profile", None) if company else None
        learner = app.learner

        company_name = (
            getattr(company_profile, "company_name", None)
            or (f"{company.first_name} {company.last_name}" if company else "Company")
        )
        company_logo = getattr(company_profile, "logo_url", None)

        candidate_name = (
            f"{learner.first_name} {learner.last_name}"
            if learner else "Candidate"
        )
        candidate_email = learner.email if learner else None

        return JobApplicationResponse(
            id=app.id,
            job_id=app.job_id,
            learner_id=app.learner_id,
            resume_url=app.resume_url,
            resume_filename=app.resume_filename,
            cover_letter=app.cover_letter,
            screening_answers=app.screening_answers,
            screening_score=app.screening_score,
            deal_breaker_passed=app.deal_breaker_passed,
            deal_breaker_failed_reason=app.deal_breaker_failed_reason,
            status=app.status,
            reviewed_by=app.reviewed_by,
            reviewed_at=app.reviewed_at,
            review_notes=app.review_notes,
            applied_at=app.applied_at,
            created_at=app.created_at,
            updated_at=app.updated_at,
            job_title=job.title if job else None,
            company_name=company_name,
            company_logo_url=company_logo,
            location=job.location if job else None,
            work_mode=job.work_mode if job else None,
            compensation=job.compensation if job else None,
            posting_type=job.posting_type if job else None,
            candidate_name=candidate_name,
            candidate_email=candidate_email,
        )

    def apply_for_job(
        self,
        db: Session,
        current_user: User,
        job_id: int,
        request: ApplicationCreateRequest,
        resume_file: Optional[UploadFile] = None,
    ) -> JobApplicationResponse:
        if current_user.role not in (UserRole.LEARNER, UserRole.ADMIN):
            raise ForbiddenException("Only registered learners can submit job applications.")

        job = self.job_repo.get_by_id(db=db, job_id=job_id)
        if not job:
            raise NotFoundException("Job posting not found.")

        if job.status != JobStatus.ACTIVE.value:
            raise BadRequestException("This job listing is not currently accepting applications.")

        existing = self.application_repo.get_by_job_and_learner(
            db=db, job_id=job_id, learner_id=current_user.id
        )
        if existing:
            raise BadRequestException(
                "An application is already active for this vacancy.",
                error_code="DUPLICATE_APPLICATION",
            )

        resume_url = request.resume_url
        resume_filename = request.resume_filename

        if resume_file and resume_file.filename:
            file_ext = Path(resume_file.filename).suffix.lower()
            if file_ext not in {".pdf", ".docx", ".doc"}:
                raise BadRequestException(
                    "Only PDF or DOCX files are accepted for resume submissions.",
                    error_code="INVALID_FILE_TYPE",
                )

            contents = resume_file.file.read()
            if len(contents) > MAX_FILE_SIZE:
                raise BadRequestException(
                    "Resume file exceeds the maximum allowed limit of 5MB.",
                    error_code="FILE_TOO_LARGE",
                )

            is_pdf = contents.startswith(b"%PDF")
            is_docx = contents.startswith(b"PK\x03\x04")
            if not (is_pdf or is_docx):
                raise BadRequestException(
                    "File content does not match a valid PDF or Word document.",
                    error_code="INVALID_DOCUMENT_STRUCTURE",
                )

            UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
            safe_name = f"job_{job_id}_user_{current_user.id}_resume{file_ext}"
            file_path = UPLOAD_DIR / safe_name
            with open(file_path, "wb") as f:
                f.write(contents)

            resume_url = f"/uploads/resumes/{safe_name}"
            resume_filename = resume_file.filename

        elif request.use_profile_resume or not resume_url:
            learner_profile = getattr(current_user, "learner_profile", None)
            if learner_profile and learner_profile.resume_url:
                resume_url = learner_profile.resume_url
                resume_filename = learner_profile.resume_filename or "Profile_Resume.pdf"
            elif request.resume_url:
                resume_url = request.resume_url
                resume_filename = request.resume_filename or "Resume.pdf"
            else:
                raise BadRequestException(
                    "Please attach a valid resume document or ensure your profile has an uploaded resume.",
                    error_code="RESUME_REQUIRED",
                )

        questions = self.screening_repo.get_questions_by_job_id(db=db, job_id=job_id)
        screening_answers = request.screening_answers or {}

        deal_breaker_passed = True
        failed_reasons = []
        earned_points = 0
        total_possible_points = sum(q.weight for q in questions) if questions else 100
        preview_snippets = []

        for q in questions:
            raw_answer = screening_answers.get(str(q.id))
            if raw_answer is None:
                raw_answer = screening_answers.get(q.id)

            ans_str = str(raw_answer).strip() if raw_answer is not None else ""
            if ans_str:
                short_val = ans_str if len(ans_str) <= 30 else ans_str[:27] + "..."
                preview_snippets.append(short_val)

            question_earned = 0

            if q.is_deal_breaker:
                rule = q.deal_breaker_rule or "MANDATORY"
                target_val = q.deal_breaker_value or q.expected_answer or ""

                if rule in ("MANDATORY", "EQUALS"):
                    if not ans_str or (target_val and ans_str.lower() != target_val.lower()):
                        deal_breaker_passed = False
                        failed_reasons.append(f"Failed '{q.question_text}' (Required: {target_val}, Received: {ans_str})")
                    else:
                        question_earned = q.weight

                elif rule == "GTE":
                    num_ans = _extract_number(ans_str)
                    num_req = _extract_number(target_val)
                    if num_ans is None or (num_req is not None and num_ans < num_req):
                        deal_breaker_passed = False
                        failed_reasons.append(f"Failed '{q.question_text}' (Minimum: {target_val}, Received: {ans_str})")
                    else:
                        question_earned = q.weight

                elif rule == "LTE":
                    num_ans = _extract_number(ans_str)
                    num_req = _extract_number(target_val)
                    if num_ans is None or (num_req is not None and num_ans > num_req):
                        deal_breaker_passed = False
                        failed_reasons.append(f"Failed '{q.question_text}' (Maximum: {target_val}, Received: {ans_str})")
                    else:
                        question_earned = q.weight

                elif rule == "CONTAINS":
                    if target_val.lower() not in ans_str.lower():
                        deal_breaker_passed = False
                        failed_reasons.append(f"Failed '{q.question_text}' (Expected keyword: {target_val})")
                    else:
                        question_earned = q.weight
            else:
                if q.expected_answer:
                    if ans_str.lower() == q.expected_answer.lower():
                        question_earned = q.weight
                    elif ans_str:
                        question_earned = int(q.weight * 0.7)
                elif ans_str:
                    question_earned = q.weight

            earned_points += question_earned

        if total_possible_points > 0:
            raw_pct = (earned_points / total_possible_points) * 100.0
            match_score = min(100, max(0, int(round(raw_pct))))
        else:
            match_score = 80

        if not deal_breaker_passed:
            match_score = min(match_score, 45)

        preview_text = " • ".join(preview_snippets) if preview_snippets else "Screening responses submitted"
        if len(preview_text) > 490:
            preview_text = preview_text[:487] + "..."

        failed_reason_text = " | ".join(failed_reasons) if failed_reasons else None

        application = JobApplication(
            job_id=job_id,
            learner_id=current_user.id,
            resume_url=resume_url,
            resume_filename=resume_filename,
            cover_letter=request.cover_letter.strip() if request.cover_letter else None,
            screening_answers=screening_answers,
            screening_score=match_score,
            deal_breaker_passed=deal_breaker_passed,
            deal_breaker_failed_reason=failed_reason_text,
            status=ApplicationStatus.SUBMITTED.value,
        )
        saved = self.application_repo.create(db=db, application=application)

        evaluation_status = (
            CandidateStatus.DISQUALIFIED.value
            if not deal_breaker_passed
            else (CandidateStatus.SHORTLISTED.value if match_score >= 80 else CandidateStatus.UNDER_REVIEW.value)
        )

        candidate_name = f"{current_user.first_name} {current_user.last_name}"
        evaluation = CandidateEvaluation(
            job_id=job_id,
            candidate_id=current_user.id,
            candidate_name=candidate_name,
            candidate_email=current_user.email,
            match_score=match_score,
            deal_breaker_passed=deal_breaker_passed,
            deal_breaker_failed_reason=failed_reason_text,
            status=evaluation_status,
            answers=screening_answers,
            key_answers_preview=preview_text,
            resume_url=resume_url,
        )
        self.screening_repo.create_evaluation(db=db, evaluation=evaluation)

        job.applications_count = (job.applications_count or 0) + 1
        db.commit()

        reloaded = self.application_repo.get_by_id(db=db, application_id=saved.id)
        return self._format_application_response(reloaded or saved)

    def get_learner_applications(
        self,
        db: Session,
        current_user: User,
        status: Optional[str] = None,
        page: int = 1,
        size: int = 10,
    ) -> PaginatedApplicationResponse:
        items, total, counts = self.application_repo.get_by_learner_paginated(
            db=db,
            learner_id=current_user.id,
            status=status,
            page=page,
            size=size,
        )

        total_pages = math.ceil(total / size) if total > 0 else 1
        formatted_items = [self._format_application_response(app) for app in items]

        return PaginatedApplicationResponse(
            items=formatted_items,
            total=total,
            page=page,
            size=size,
            total_pages=total_pages,
            active_count=counts.get("active", 0),
            submitted_count=counts.get("submitted", 0),
            under_review_count=counts.get("under_review", 0),
            shortlisted_count=counts.get("shortlisted", 0),
            interview_count=counts.get("interview", 0),
            offered_count=counts.get("offered", 0),
            withdrawn_count=counts.get("withdrawn", 0),
            rejected_count=counts.get("rejected", 0),
        )

    def get_application_by_id(
        self, db: Session, current_user: User, application_id: int
    ) -> JobApplicationResponse:
        app = self.application_repo.get_by_id(db=db, application_id=application_id)
        if not app:
            raise NotFoundException("Job application record not found.")

        if current_user.role == UserRole.LEARNER and app.learner_id != current_user.id:
            raise ForbiddenException("You are not authorized to view this application.")

        if current_user.role == UserRole.COMPANY and app.job.company_id != current_user.id:
            raise ForbiddenException("You are not authorized to view this candidate application.")

        return self._format_application_response(app)

    def withdraw_application(
        self, db: Session, current_user: User, application_id: int
    ) -> JobApplicationResponse:
        app = self.application_repo.get_by_id(db=db, application_id=application_id)
        if not app:
            raise NotFoundException("Job application record not found.")

        if current_user.role != UserRole.ADMIN and app.learner_id != current_user.id:
            raise ForbiddenException("You can only withdraw your own applications.")

        if app.status == ApplicationStatus.WITHDRAWN.value:
            raise BadRequestException("Application is already withdrawn.")

        app.status = ApplicationStatus.WITHDRAWN.value
        updated = self.application_repo.update(db=db, application=app)

        if app.job and (app.job.applications_count or 0) > 0:
            app.job.applications_count = max(0, app.job.applications_count - 1)

        eval_stmt = select(CandidateEvaluation).where(
            CandidateEvaluation.job_id == app.job_id,
            CandidateEvaluation.candidate_id == app.learner_id,
        )
        existing_eval = db.execute(eval_stmt).scalars().first()
        if existing_eval:
            existing_eval.status = CandidateStatus.DISQUALIFIED.value
            existing_eval.deal_breaker_failed_reason = "Application withdrawn by candidate"

        db.commit()
        return self._format_application_response(updated)

    def update_application_status(
        self,
        db: Session,
        current_user: User,
        application_id: int,
        request: ApplicationStatusUpdateRequest,
    ) -> JobApplicationResponse:
        app = self.application_repo.get_by_id(db=db, application_id=application_id)
        if not app:
            raise NotFoundException("Job application record not found.")

        if current_user.role != UserRole.ADMIN:
            if current_user.role != UserRole.COMPANY or app.job.company_id != current_user.id:
                raise ForbiddenException("You are not authorized to update status for this application.")

        valid_statuses = {s.value for s in ApplicationStatus}
        new_status = request.status.upper()
        if new_status not in valid_statuses:
            raise BadRequestException(f"Invalid status: {request.status}. Valid statuses: {valid_statuses}")

        app.status = new_status
        app.reviewed_by = current_user.id
        app.reviewed_at = datetime.now(timezone.utc)
        if request.notes:
            app.review_notes = request.notes

        eval_stmt = select(CandidateEvaluation).where(
            CandidateEvaluation.job_id == app.job_id,
            CandidateEvaluation.candidate_id == app.learner_id,
        )
        existing_eval = db.execute(eval_stmt).scalars().first()
        if existing_eval:
            if new_status == ApplicationStatus.SHORTLISTED.value:
                existing_eval.status = CandidateStatus.SHORTLISTED.value
            elif new_status == ApplicationStatus.REJECTED.value:
                existing_eval.status = CandidateStatus.DISQUALIFIED.value
            elif new_status == ApplicationStatus.UNDER_REVIEW.value:
                existing_eval.status = CandidateStatus.UNDER_REVIEW.value
            elif new_status == ApplicationStatus.WITHDRAWN.value:
                existing_eval.status = CandidateStatus.DISQUALIFIED.value
                existing_eval.deal_breaker_failed_reason = "Application withdrawn by candidate"

        updated = self.application_repo.update(db=db, application=app)
        return self._format_application_response(updated)

    def check_application_status(
        self, db: Session, current_user: User, job_id: int
    ) -> ApplicationCheckResponse:
        app = self.application_repo.get_by_job_and_learner(
            db=db, job_id=job_id, learner_id=current_user.id
        )
        if not app:
            return ApplicationCheckResponse(has_applied=False, application=None)

        return ApplicationCheckResponse(
            has_applied=True,
            application=self._format_application_response(app),
        )

    def get_job_applications(
        self,
        db: Session,
        current_user: User,
        job_id: int,
        status: Optional[str] = None,
        page: int = 1,
        size: int = 10,
    ) -> PaginatedApplicationResponse:
        job = self.job_repo.get_by_id(db=db, job_id=job_id)
        if not job:
            raise NotFoundException("Job posting not found.")

        if current_user.role != UserRole.ADMIN:
            if current_user.role != UserRole.COMPANY or job.company_id != current_user.id:
                raise ForbiddenException("You are not authorized to view applications for this vacancy.")

        items, total = self.application_repo.get_by_job_paginated(
            db=db,
            job_id=job_id,
            status=status,
            page=page,
            size=size,
        )

        total_pages = math.ceil(total / size) if total > 0 else 1
        formatted_items = [self._format_application_response(app) for app in items]

        return PaginatedApplicationResponse(
            items=formatted_items,
            total=total,
            page=page,
            size=size,
            total_pages=total_pages,
        )
