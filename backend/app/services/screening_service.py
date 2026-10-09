import re
import math
import logging
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from app.core.exceptions import (
    NotFoundException,
    ForbiddenException,
    BadRequestException,
)
from app.models.user import User, UserRole
from app.models.job import JobPosting
from app.models.screening import (
    ScreeningQuestion,
    CandidateEvaluation,
    QuestionType,
    DealBreakerRule,
    CandidateStatus,
)
from app.models.application import JobApplication, ApplicationStatus
from sqlalchemy import select
from app.repositories.job_repository import JobRepository
from app.repositories.screening_repository import ScreeningRepository
from app.repositories.audit_log_repository import AuditLogRepository
from app.schemas.screening import (
    ScreeningQuestionCreateRequest,
    ScreeningQuestionUpdateRequest,
    ScreeningQuestionResponse,
    CandidateEvaluationCreateRequest,
    CandidateEvaluationResponse,
    PaginatedCandidateEvaluationResponse,
)

logger = logging.getLogger(__name__)


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


class ScreeningService:
    def __init__(
        self,
        screening_repo: ScreeningRepository = ScreeningRepository(),
        job_repo: JobRepository = JobRepository(),
        audit_repo: AuditLogRepository = AuditLogRepository(),
    ):
        self.screening_repo = screening_repo
        self.job_repo = job_repo
        self.audit_repo = audit_repo

    def _check_job_access(self, job: JobPosting, user: User) -> None:
        if user.role == UserRole.ADMIN:
            return
        if user.role != UserRole.COMPANY or job.company_id != user.id:
            raise ForbiddenException("You are not authorized to manage screening for this vacancy.")

    def add_question(
        self,
        db: Session,
        current_user: User,
        job_id: int,
        request: ScreeningQuestionCreateRequest,
    ) -> ScreeningQuestionResponse:
        job = self.job_repo.get_by_id(db=db, job_id=job_id)
        if not job:
            raise NotFoundException("Job posting not found.")

        self._check_job_access(job, current_user)

        if current_user.role == UserRole.COMPANY:
            profile = getattr(current_user, "company_profile", None)
            if not profile or profile.verification_status != "APPROVED":
                raise ForbiddenException("COMPANY_NOT_VERIFIED")

        deal_label = request.deal_breaker_label
        if request.is_deal_breaker and not deal_label:
            if request.deal_breaker_rule == DealBreakerRule.GTE and request.deal_breaker_value:
                deal_label = f"Auto-Disqualify if < {request.deal_breaker_value}"
            elif request.deal_breaker_rule == DealBreakerRule.MANDATORY:
                deal_label = "Mandatory"
            else:
                deal_label = "Deal-Breaker Requirement"

        question = ScreeningQuestion(
            job_id=job_id,
            question_text=request.question_text.strip(),
            question_type=request.question_type.value,
            options=request.options,
            expected_answer=request.expected_answer.strip() if request.expected_answer else None,
            is_required=request.is_required,
            is_deal_breaker=request.is_deal_breaker,
            deal_breaker_rule=request.deal_breaker_rule.value if request.deal_breaker_rule else None,
            deal_breaker_value=request.deal_breaker_value.strip() if request.deal_breaker_value else None,
            deal_breaker_label=deal_label,
            weight=request.weight,
            order_index=request.order_index,
        )

        saved = self.screening_repo.create_question(db=db, question=question)
        return ScreeningQuestionResponse.model_validate(saved)

    def get_questions(self, db: Session, job_id: int) -> List[ScreeningQuestionResponse]:
        job = self.job_repo.get_by_id(db=db, job_id=job_id)
        if not job:
            raise NotFoundException("Job posting not found.")

        questions = self.screening_repo.get_questions_by_job_id(db=db, job_id=job_id)
        return [ScreeningQuestionResponse.model_validate(q) for q in questions]

    def update_question(
        self,
        db: Session,
        current_user: User,
        question_id: int,
        request: ScreeningQuestionUpdateRequest,
    ) -> ScreeningQuestionResponse:
        question = self.screening_repo.get_question_by_id(db=db, question_id=question_id)
        if not question:
            raise NotFoundException("Screening question not found.")

        job = self.job_repo.get_by_id(db=db, job_id=question.job_id)
        if not job:
            raise NotFoundException("Associated job posting not found.")

        self._check_job_access(job, current_user)

        if current_user.role == UserRole.ADMIN and job.company_id != current_user.id:
            self.audit_repo.create(
                db=db,
                admin_id=current_user.id,
                target_user_id=job.company_id,
                action="AUDIT_UPDATE_SCREENING_QUESTION",
                details={
                    "message": f"Admin audited and modified screening question ID={question_id} for Job ID={job.id}",
                    "job_id": job.id,
                    "question_id": question_id,
                },
            )

        if request.question_text is not None:
            question.question_text = request.question_text.strip()
        if request.question_type is not None:
            question.question_type = request.question_type.value
        if request.options is not None:
            question.options = request.options
        if request.expected_answer is not None:
            question.expected_answer = request.expected_answer.strip()
        if request.is_required is not None:
            question.is_required = request.is_required
        if request.is_deal_breaker is not None:
            question.is_deal_breaker = request.is_deal_breaker
        if request.deal_breaker_rule is not None:
            question.deal_breaker_rule = request.deal_breaker_rule.value
        if request.deal_breaker_value is not None:
            question.deal_breaker_value = request.deal_breaker_value.strip()
        if request.deal_breaker_label is not None:
            question.deal_breaker_label = request.deal_breaker_label.strip()
        if request.weight is not None:
            question.weight = request.weight
        if request.order_index is not None:
            question.order_index = request.order_index

        updated = self.screening_repo.update_question(db=db, question=question)
        return ScreeningQuestionResponse.model_validate(updated)

    def delete_question(self, db: Session, current_user: User, question_id: int) -> None:
        question = self.screening_repo.get_question_by_id(db=db, question_id=question_id)
        if not question:
            raise NotFoundException("Screening question not found.")

        job = self.job_repo.get_by_id(db=db, job_id=question.job_id)
        if not job:
            raise NotFoundException("Associated job posting not found.")

        self._check_job_access(job, current_user)

        if current_user.role == UserRole.ADMIN and job.company_id != current_user.id:
            self.audit_repo.create(
                db=db,
                admin_id=current_user.id,
                target_user_id=job.company_id,
                action="AUDIT_DELETE_SCREENING_QUESTION",
                details={
                    "message": f"Admin removed non-compliant screening question ID={question_id} for Job ID={job.id}",
                    "job_id": job.id,
                    "question_id": question_id,
                },
            )

        self.screening_repo.delete_question(db=db, question=question)

    def evaluate_candidate(
        self,
        db: Session,
        job_id: int,
        request: CandidateEvaluationCreateRequest,
        candidate_user: Optional[User] = None,
    ) -> CandidateEvaluationResponse:
        job = self.job_repo.get_by_id(db=db, job_id=job_id)
        if not job:
            raise NotFoundException("Job posting not found.")

        questions = self.screening_repo.get_questions_by_job_id(db=db, job_id=job_id)

        deal_breaker_passed = True
        failed_reasons = []
        earned_points = 0
        total_possible_points = sum(q.weight for q in questions) if questions else 100

        preview_snippets = []

        for q in questions:
            raw_answer = request.answers.get(str(q.id))
            if raw_answer is None:
                raw_answer = request.answers.get(q.id)

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
            status = CandidateStatus.DISQUALIFIED.value
        else:
            status = CandidateStatus.SHORTLISTED.value if match_score >= 80 else CandidateStatus.UNDER_REVIEW.value

        preview_text = " • ".join(preview_snippets) if preview_snippets else "Screening responses submitted"
        if len(preview_text) > 490:
            preview_text = preview_text[:487] + "..."

        failed_reason_text = " | ".join(failed_reasons) if failed_reasons else None

        evaluation = CandidateEvaluation(
            job_id=job_id,
            candidate_id=candidate_user.id if candidate_user else None,
            candidate_name=request.candidate_name.strip(),
            candidate_email=request.candidate_email.strip(),
            candidate_avatar_url=request.candidate_avatar_url,
            match_score=match_score,
            deal_breaker_passed=deal_breaker_passed,
            deal_breaker_failed_reason=failed_reason_text,
            status=status,
            answers=request.answers,
            key_answers_preview=preview_text,
            resume_url=request.resume_url,
        )

        saved = self.screening_repo.create_evaluation(db=db, evaluation=evaluation)
        job.applications_count = (job.applications_count or 0) + 1
        db.commit()

        return CandidateEvaluationResponse.model_validate(saved)

    def list_candidates(
        self,
        db: Session,
        current_user: User,
        job_id: int,
        page: int = 1,
        size: int = 10,
        min_score: Optional[int] = None,
        deal_breaker_passed: Optional[bool] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> PaginatedCandidateEvaluationResponse:
        job = self.job_repo.get_by_id(db=db, job_id=job_id)
        if not job:
            raise NotFoundException("Job posting not found.")

        self._check_job_access(job, current_user)

        items, total, passed_count, disqualified_count, avg_score = (
            self.screening_repo.get_evaluations_paginated(
                db=db,
                job_id=job_id,
                page=page,
                size=size,
                min_score=min_score,
                deal_breaker_passed=deal_breaker_passed,
                status=status,
                search=search,
            )
        )

        total_pages = math.ceil(total / size) if total > 0 else 1

        return PaginatedCandidateEvaluationResponse(
            items=[CandidateEvaluationResponse.model_validate(it) for it in items],
            total=total,
            page=page,
            size=size,
            total_pages=total_pages,
            passed_count=passed_count,
            disqualified_count=disqualified_count,
            avg_match_score=avg_score,
        )

    def update_candidate_status(
        self,
        db: Session,
        current_user: User,
        evaluation_id: int,
        status: str,
        notes: Optional[str] = None,
    ) -> CandidateEvaluationResponse:
        evaluation = self.screening_repo.get_evaluation_by_id(db=db, evaluation_id=evaluation_id)
        if not evaluation:
            raise NotFoundException("Candidate evaluation record not found.")

        job = self.job_repo.get_by_id(db=db, job_id=evaluation.job_id)
        if not job:
            raise NotFoundException("Associated job posting not found.")

        self._check_job_access(job, current_user)

        evaluation.status = status.upper()
        evaluation.reviewed_by = current_user.id
        evaluation.reviewed_at = evaluation.updated_at

        if evaluation.candidate_id:
            app_stmt = select(JobApplication).where(
                JobApplication.job_id == evaluation.job_id,
                JobApplication.learner_id == evaluation.candidate_id,
            )
            job_app = db.execute(app_stmt).scalars().first()
            if job_app:
                status_upper = status.upper()
                if status_upper == CandidateStatus.SHORTLISTED.value:
                    job_app.status = ApplicationStatus.SHORTLISTED.value
                elif status_upper == CandidateStatus.DISQUALIFIED.value:
                    job_app.status = ApplicationStatus.REJECTED.value
                elif status_upper == CandidateStatus.UNDER_REVIEW.value:
                    job_app.status = ApplicationStatus.UNDER_REVIEW.value
                elif status_upper == CandidateStatus.APPLIED.value:
                    job_app.status = ApplicationStatus.SUBMITTED.value
                job_app.reviewed_by = current_user.id
                job_app.reviewed_at = evaluation.updated_at

        updated = self.screening_repo.update_evaluation(db=db, evaluation=evaluation)
        return CandidateEvaluationResponse.model_validate(updated)
