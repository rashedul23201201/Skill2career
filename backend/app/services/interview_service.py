import logging
import math
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session

from app.core.exceptions import (
    NotFoundException,
    ForbiddenException,
    BadRequestException,
)
from app.models.user import User, UserRole
from app.models.application import JobApplication, ApplicationStatus
from app.models.interview import InterviewRequest, InterviewSlot, InterviewStatus, InterviewFeedback, InterviewRecommendation
from app.repositories.interview_repository import InterviewRepository
from app.repositories.application_repository import ApplicationRepository
from app.repositories.audit_log_repository import AuditLogRepository
from app.schemas.interview import (
    InterviewRequestCreate,
    InterviewSelectSlotRequest,
    InterviewRescheduleRequest,
    InterviewStatusUpdateRequest,
    InterviewRequestResponse,
    InterviewSlotResponse,
    PaginatedInterviewResponse,
    InterviewFeedbackCreate,
    InterviewFeedbackUpdate,
    InterviewFeedbackResponse,
    ConsolidatedTeamFeedbackResponse,
    FeedbackAuditLogResponse,
)
from app.utils.calendar import generate_ics_calendar

logger = logging.getLogger(__name__)


class InterviewService:
    def __init__(
        self,
        interview_repo: InterviewRepository = InterviewRepository(),
        application_repo: ApplicationRepository = ApplicationRepository(),
        audit_repo: AuditLogRepository = AuditLogRepository(),
    ):
        self.interview_repo = interview_repo
        self.application_repo = application_repo
        self.audit_repo = audit_repo

    def _format_interview_response(self, interview: InterviewRequest) -> InterviewRequestResponse:
        job = interview.job
        company = interview.company
        company_profile = getattr(company, "company_profile", None) if company else None
        candidate = interview.candidate

        company_name = (
            getattr(company_profile, "company_name", None)
            or (f"{company.first_name} {company.last_name}" if company else "Hiring Company")
        )
        company_logo_url = getattr(company_profile, "logo_url", None) if company_profile else None
        candidate_name = f"{candidate.first_name} {candidate.last_name}" if candidate else "Candidate"
        candidate_email = getattr(candidate, "email", None)
        job_title = getattr(job, "title", "Job Position") if job else "Job Position"

        slot_responses: List[InterviewSlotResponse] = []
        selected_slot_resp: Optional[InterviewSlotResponse] = None

        if interview.slots:
            for slot in interview.slots:
                resp = InterviewSlotResponse.model_validate(slot)
                slot_responses.append(resp)
                if slot.id == interview.selected_slot_id or slot.is_selected:
                    selected_slot_resp = resp

        feedbacks = getattr(interview, "feedbacks", None) or []
        feedbacks_count = len(feedbacks)
        has_feedback = feedbacks_count > 0
        latest_feedback_score = feedbacks[0].overall_score if feedbacks else None
        is_feedback_shared = any(getattr(f, "is_shared_with_candidate", False) for f in feedbacks)

        return InterviewRequestResponse(
            id=interview.id,
            application_id=interview.application_id,
            company_id=interview.company_id,
            candidate_id=interview.candidate_id,
            job_id=interview.job_id,
            interview_type=interview.interview_type,
            meeting_platform=interview.meeting_platform,
            meeting_link=interview.meeting_link,
            location=interview.location,
            duration_minutes=interview.duration_minutes,
            notes=interview.notes,
            status=interview.status,
            selected_slot_id=interview.selected_slot_id,
            scheduled_at=interview.scheduled_at,
            reschedule_reason=interview.reschedule_reason,
            rescheduled_by=interview.rescheduled_by,
            reschedule_preferred_time=interview.reschedule_preferred_time,
            created_at=interview.created_at,
            updated_at=interview.updated_at,
            job_title=job_title,
            company_name=company_name,
            company_logo_url=company_logo_url,
            candidate_name=candidate_name,
            candidate_email=candidate_email,
            slots=slot_responses,
            selected_slot=selected_slot_resp,
            feedbacks_count=feedbacks_count,
            has_feedback=has_feedback,
            latest_feedback_score=latest_feedback_score,
            is_feedback_shared=is_feedback_shared,
        )

    def _format_feedback_response(
        self, feedback: InterviewFeedback, hide_internal: bool = False
    ) -> InterviewFeedbackResponse:
        interviewer = getattr(feedback, "interviewer", None)
        interviewer_name = (
            f"{interviewer.first_name} {interviewer.last_name}" if interviewer else "Interviewer"
        )
        interviewer_email = getattr(interviewer, "email", None) if not hide_internal else None

        interview_req = getattr(feedback, "interview_request", None)
        job = getattr(interview_req, "job", None) if interview_req else None
        company = getattr(interview_req, "company", None) if interview_req else None
        company_profile = getattr(company, "company_profile", None) if company else None
        candidate = getattr(interview_req, "candidate", None) if interview_req else None

        job_title = getattr(job, "title", "Job Position") if job else None
        company_name = (
            getattr(company_profile, "company_name", None)
            or (f"{company.first_name} {company.last_name}" if company else None)
        )
        candidate_name = (
            f"{candidate.first_name} {candidate.last_name}" if candidate else None
        )

        return InterviewFeedbackResponse(
            id=feedback.id,
            interview_id=feedback.interview_id,
            application_id=feedback.application_id,
            interviewer_id=feedback.interviewer_id,
            interviewer_name=interviewer_name,
            interviewer_email=interviewer_email,
            overall_score=feedback.overall_score,
            technical_score=feedback.technical_score,
            communication_score=feedback.communication_score,
            problem_solving_score=feedback.problem_solving_score,
            recommendation=feedback.recommendation,
            strengths=feedback.strengths or [],
            improvement_areas=feedback.improvement_areas or [],
            competency_breakdown=feedback.competency_breakdown or [],
            feedback_notes=feedback.feedback_notes,
            internal_notes=None if hide_internal else feedback.internal_notes,
            suggested_next_action=feedback.suggested_next_action,
            is_shared_with_candidate=feedback.is_shared_with_candidate,
            shared_at=feedback.shared_at,
            created_at=feedback.created_at,
            updated_at=feedback.updated_at,
            job_title=job_title,
            company_name=company_name,
            candidate_name=candidate_name,
        )

    def _format_consolidated_feedback(
        self,
        interview: InterviewRequest,
        feedbacks: List[InterviewFeedback],
        hide_internal: bool = False,
    ) -> ConsolidatedTeamFeedbackResponse:
        job = getattr(interview, "job", None)
        company = getattr(interview, "company", None)
        company_profile = getattr(company, "company_profile", None) if company else None
        candidate = getattr(interview, "candidate", None)

        job_title = getattr(job, "title", "Job Position") if job else None
        company_name = (
            getattr(company_profile, "company_name", None)
            or (f"{company.first_name} {company.last_name}" if company else None)
        )
        candidate_name = f"{candidate.first_name} {candidate.last_name}" if candidate else None

        total = len(feedbacks)
        if total > 0:
            avg_overall = round(sum(f.overall_score for f in feedbacks) / total, 1)
            avg_tech = round(sum(f.technical_score for f in feedbacks) / total, 1)
            avg_comm = round(sum(f.communication_score for f in feedbacks) / total, 1)
            avg_prob = round(sum(f.problem_solving_score for f in feedbacks) / total, 1)
        else:
            avg_overall = 0.0
            avg_tech = 0.0
            avg_comm = 0.0
            avg_prob = 0.0

        rec_counts: Dict[str, int] = {}
        all_strengths: List[str] = []
        all_improvements: List[str] = []

        for f in feedbacks:
            rec_counts[f.recommendation] = rec_counts.get(f.recommendation, 0) + 1
            if isinstance(f.strengths, list):
                for s in f.strengths:
                    if isinstance(s, str) and s not in all_strengths:
                        all_strengths.append(s)
            if isinstance(f.improvement_areas, list):
                for imp in f.improvement_areas:
                    area_name = imp.get("area") if isinstance(imp, dict) else str(imp)
                    if area_name and area_name not in all_improvements:
                        all_improvements.append(area_name)

        suggested_action = None
        for f in feedbacks:
            if f.suggested_next_action:
                suggested_action = f.suggested_next_action
                break

        if not suggested_action and total > 0:
            if avg_overall >= 80:
                suggested_action = "OFFER"
            elif avg_overall >= 60:
                suggested_action = "NEXT_ROUND"
            else:
                suggested_action = "REJECT"

        is_shared = any(f.is_shared_with_candidate for f in feedbacks)
        feedback_responses = [
            self._format_feedback_response(f, hide_internal=hide_internal) for f in feedbacks
        ]

        return ConsolidatedTeamFeedbackResponse(
            interview_id=interview.id,
            application_id=interview.application_id,
            job_title=job_title,
            company_name=company_name,
            candidate_name=candidate_name,
            total_feedbacks=total,
            average_overall_score=avg_overall,
            average_technical_score=avg_tech,
            average_communication_score=avg_comm,
            average_problem_solving_score=avg_prob,
            recommendations_breakdown=rec_counts,
            top_strengths=all_strengths,
            top_improvement_areas=all_improvements,
            suggested_pipeline_action=suggested_action,
            is_shared_with_candidate=is_shared,
            feedbacks=feedback_responses,
        )

    def create_interview_request(
        self,
        db: Session,
        current_user: User,
        application_id: int,
        request: InterviewRequestCreate,
    ) -> InterviewRequestResponse:
        application = self.application_repo.get_by_id(db, application_id)
        if not application:
            raise NotFoundException(f"Job application {application_id} not found")

        job = application.job
        if not job:
            raise NotFoundException("Associated job posting not found")

        is_company_owner = job.company_id == current_user.id
        is_admin = current_user.role == UserRole.ADMIN

        if not (is_company_owner or is_admin):
            raise ForbiddenException("Only the company that posted the job or an admin can invite candidate to interview")

        if application.status in (ApplicationStatus.WITHDRAWN.value, ApplicationStatus.REJECTED.value):
            raise BadRequestException(f"Cannot schedule interview for application with status '{application.status}'")

        meeting_link = request.meeting_link
        if not meeting_link:
            platform_lower = request.meeting_platform.lower()
            if "meet" in platform_lower:
                meeting_link = f"https://meet.google.com/s2c-{application.id:03d}-{int(datetime.now().timestamp()) % 1000:03d}"
            elif "zoom" in platform_lower:
                meeting_link = f"https://zoom.us/j/{application.id:04d}{int(datetime.now().timestamp()) % 10000:04d}"
            else:
                meeting_link = "https://meet.google.com/s2c-session"

        interview_request = InterviewRequest(
            application_id=application.id,
            company_id=job.company_id,
            candidate_id=application.learner_id,
            job_id=job.id,
            interview_type=request.interview_type or "Company Interview",
            meeting_platform=request.meeting_platform or "Google Meet",
            meeting_link=meeting_link,
            location=request.location or "Online / Virtual",
            duration_minutes=request.duration_minutes or 45,
            notes=request.notes,
            status=InterviewStatus.PENDING.value,
        )

        db.add(interview_request)
        db.flush()

        slots_to_add: List[InterviewSlot] = []
        if request.proposed_slots and len(request.proposed_slots) > 0:
            for s in request.proposed_slots:
                slots_to_add.append(
                    InterviewSlot(
                        interview_request_id=interview_request.id,
                        start_time=s.start_time,
                        end_time=s.end_time,
                        is_selected=False,
                    )
                )
        else:
            now = datetime.now(timezone.utc)
            slot1_start = now + timedelta(days=2, hours=3)
            slot1_end = slot1_start + timedelta(minutes=interview_request.duration_minutes)
            slot2_start = now + timedelta(days=3, hours=5)
            slot2_end = slot2_start + timedelta(minutes=interview_request.duration_minutes)
            slots_to_add.extend([
                InterviewSlot(interview_request_id=interview_request.id, start_time=slot1_start, end_time=slot1_end),
                InterviewSlot(interview_request_id=interview_request.id, start_time=slot2_start, end_time=slot2_end),
            ])

        for s in slots_to_add:
            db.add(s)

        if application.status == ApplicationStatus.SUBMITTED.value:
            application.status = ApplicationStatus.SHORTLISTED.value

        db.commit()
        db.refresh(interview_request)

        self.audit_repo.create(
            db=db,
            admin_id=current_user.id if current_user.role == UserRole.ADMIN else None,
            target_user_id=application.learner_id,
            action="INTERVIEW_REQUEST_CREATED",
            details={
                "application_id": application.id,
                "candidate_id": application.learner_id,
                "interview_type": interview_request.interview_type,
                "slots_count": len(slots_to_add),
            },
        )

        logger.info(
            f"[Notification Simulation] Email sent to candidate {application.learner.email} "
            f"with interview invitation from {job.company.email} for '{job.title}'"
        )

        return self._format_interview_response(interview_request)

    def get_my_interviews(
        self,
        db: Session,
        current_user: User,
        status: Optional[str] = None,
        page: int = 1,
        size: int = 10,
    ) -> PaginatedInterviewResponse:
        offset = (page - 1) * size

        if current_user.role == UserRole.LEARNER:
            items, total = self.interview_repo.list_for_candidate(
                db=db, candidate_id=current_user.id, status=status, limit=size, offset=offset
            )
            counts = self.interview_repo.get_counts(db=db, user_id=current_user.id, is_company=False)
        else:
            items, total = self.interview_repo.list_for_company(
                db=db, company_id=current_user.id, status=status, limit=size, offset=offset
            )
            counts = self.interview_repo.get_counts(db=db, user_id=current_user.id, is_company=True)

        total_pages = math.ceil(total / size) if size > 0 else 1
        formatted = [self._format_interview_response(item) for item in items]

        return PaginatedInterviewResponse(
            items=formatted,
            total=total,
            page=page,
            size=size,
            total_pages=total_pages,
            upcoming_count=counts.get("upcoming", 0),
            pending_count=counts.get("pending", 0),
            completed_count=counts.get("completed", 0),
            cancelled_count=counts.get("cancelled", 0),
        )

    def get_interview_by_id(
        self,
        db: Session,
        current_user: User,
        interview_id: int,
    ) -> InterviewRequestResponse:
        interview = self.interview_repo.get_by_id(db, interview_id)
        if not interview:
            raise NotFoundException(f"Interview {interview_id} not found")

        is_participant = current_user.id in (interview.candidate_id, interview.company_id)
        is_admin = current_user.role == UserRole.ADMIN
        if not (is_participant or is_admin):
            raise ForbiddenException("Access denied to this interview session")

        return self._format_interview_response(interview)

    def get_interview_for_application(
        self,
        db: Session,
        current_user: User,
        application_id: int,
    ) -> Optional[InterviewRequestResponse]:
        application = self.application_repo.get_by_id(db, application_id)
        if not application:
            raise NotFoundException(f"Job application {application_id} not found")

        is_participant = current_user.id in (application.learner_id, application.job.company_id)
        is_admin = current_user.role == UserRole.ADMIN
        if not (is_participant or is_admin):
            raise ForbiddenException("Access denied to this application's interview")

        interview = self.interview_repo.get_by_application_id(db, application_id)
        if not interview:
            return None

        return self._format_interview_response(interview)

    def select_slot(
        self,
        db: Session,
        current_user: User,
        interview_id: int,
        request: InterviewSelectSlotRequest,
    ) -> InterviewRequestResponse:
        interview = self.interview_repo.get_by_id(db, interview_id)
        if not interview:
            raise NotFoundException(f"Interview {interview_id} not found")

        is_candidate = current_user.id == interview.candidate_id
        is_admin = current_user.role == UserRole.ADMIN
        if not (is_candidate or is_admin):
            raise ForbiddenException("Only the invited candidate can select a time slot")

        target_slot: Optional[InterviewSlot] = None
        for s in interview.slots:
            if s.id == request.slot_id:
                target_slot = s
                s.is_selected = True
            else:
                s.is_selected = False

        if not target_slot:
            raise NotFoundException(f"Slot {request.slot_id} not found in this interview request")

        interview.selected_slot_id = target_slot.id
        interview.scheduled_at = target_slot.start_time
        interview.status = InterviewStatus.SCHEDULED.value

        if interview.application:
            interview.application.status = ApplicationStatus.INTERVIEW_SCHEDULED.value

        db.commit()
        db.refresh(interview)

        self.audit_repo.create(
            db=db,
            admin_id=current_user.id if current_user.role == UserRole.ADMIN else None,
            target_user_id=interview.candidate_id,
            action="INTERVIEW_SLOT_SELECTED",
            details={
                "slot_id": target_slot.id,
                "scheduled_at": str(target_slot.start_time),
            },
        )

        logger.info(
            f"[Notification Simulation] Calendar invite & confirmation email generated for "
            f"candidate {interview.candidate.email} and recruiter {interview.company.email}. "
            f"Confirmed date: {target_slot.start_time}"
        )

        return self._format_interview_response(interview)

    def request_reschedule(
        self,
        db: Session,
        current_user: User,
        interview_id: int,
        request: InterviewRescheduleRequest,
    ) -> InterviewRequestResponse:
        interview = self.interview_repo.get_by_id(db, interview_id)
        if not interview:
            raise NotFoundException(f"Interview {interview_id} not found")

        is_participant = current_user.id in (interview.candidate_id, interview.company_id)
        is_admin = current_user.role == UserRole.ADMIN
        if not (is_participant or is_admin):
            raise ForbiddenException("Access denied to reschedule this interview")

        if not request.reason.strip():
            raise BadRequestException("Please specify a reason for the reschedule request")

        interview.status = InterviewStatus.RESCHEDULE_REQUESTED.value
        interview.reschedule_reason = request.reason.strip()
        interview.reschedule_preferred_time = request.preferred_time
        interview.rescheduled_by = current_user.id

        db.commit()
        db.refresh(interview)

        self.audit_repo.create(
            db=db,
            admin_id=current_user.id if current_user.role == UserRole.ADMIN else None,
            target_user_id=interview.company_id if current_user.id == interview.candidate_id else interview.candidate_id,
            action="INTERVIEW_RESCHEDULE_REQUESTED",
            details={
                "reason": request.reason,
                "preferred_time": request.preferred_time,
            },
        )

        logger.info(
            f"[Notification Simulation] Reschedule alert sent: User {current_user.email} "
            f"requested rescheduling for interview {interview.id}. Reason: {request.reason}"
        )

        return self._format_interview_response(interview)

    def update_status(
        self,
        db: Session,
        current_user: User,
        interview_id: int,
        request: InterviewStatusUpdateRequest,
    ) -> InterviewRequestResponse:
        interview = self.interview_repo.get_by_id(db, interview_id)
        if not interview:
            raise NotFoundException(f"Interview {interview_id} not found")

        is_participant = current_user.id in (interview.candidate_id, interview.company_id)
        is_company = current_user.id == interview.company_id
        is_admin = current_user.role == UserRole.ADMIN

        if not (is_participant or is_admin):
            raise ForbiddenException("Access denied to update interview status")

        valid_statuses = [s.value for s in InterviewStatus]
        new_status = request.status.upper()
        if new_status not in valid_statuses:
            raise BadRequestException(f"Invalid status '{request.status}'. Must be one of {valid_statuses}")

        if new_status != InterviewStatus.CANCELLED.value and not (is_company or is_admin):
            raise ForbiddenException("Only the recruiter or an admin can mark interview as completed or active")

        interview.status = new_status
        if new_status == InterviewStatus.CANCELLED.value:
            if interview.application and interview.application.status == ApplicationStatus.INTERVIEW_SCHEDULED.value:
                interview.application.status = ApplicationStatus.SHORTLISTED.value
            if request.notes:
                interview.reschedule_reason = f"Cancelled: {request.notes}"

        if request.notes:
            interview.notes = (interview.notes or "") + f"\n[Status update note]: {request.notes}"

        db.commit()
        db.refresh(interview)

        self.audit_repo.create(
            db=db,
            admin_id=current_user.id if current_user.role == UserRole.ADMIN else None,
            target_user_id=interview.candidate_id,
            action="INTERVIEW_STATUS_UPDATED",
            details={"status": new_status},
        )

        return self._format_interview_response(interview)

    def generate_ics_for_interview(
        self,
        db: Session,
        current_user: User,
        interview_id: int,
    ) -> Tuple[str, str]:
        interview = self.interview_repo.get_by_id(db, interview_id)
        if not interview:
            raise NotFoundException(f"Interview {interview_id} not found")

        is_participant = current_user.id in (interview.candidate_id, interview.company_id)
        is_admin = current_user.role == UserRole.ADMIN
        if not (is_participant or is_admin):
            raise ForbiddenException("Access denied to calendar download")

        ics_content = generate_ics_calendar(interview)
        filename = f"interview-{interview.id}.ics"
        return ics_content, filename

    def submit_interview_feedback(
        self,
        db: Session,
        current_user: User,
        interview_id: int,
        request: InterviewFeedbackCreate,
    ) -> InterviewFeedbackResponse:
        interview = self.interview_repo.get_by_id(db, interview_id)
        if not interview:
            raise NotFoundException(f"Interview session {interview_id} not found")

        is_company = current_user.id == interview.company_id or current_user.role == UserRole.COMPANY
        is_admin = current_user.role == UserRole.ADMIN
        if not (is_company or is_admin):
            raise ForbiddenException("Only verified recruiters or hiring team members can submit interview scorecards")

        existing_feedback = self.interview_repo.get_feedback_by_interviewer(
            db, interview_id=interview.id, interviewer_id=current_user.id
        )

        now = datetime.now(timezone.utc)
        shared_at = now if request.is_shared_with_candidate else None

        if existing_feedback:
            existing_feedback.overall_score = request.overall_score
            existing_feedback.technical_score = request.technical_score
            existing_feedback.communication_score = request.communication_score
            existing_feedback.problem_solving_score = request.problem_solving_score
            existing_feedback.recommendation = request.recommendation.upper()
            existing_feedback.strengths = request.strengths or []
            existing_feedback.improvement_areas = request.improvement_areas or []
            existing_feedback.competency_breakdown = request.competency_breakdown or []
            existing_feedback.feedback_notes = request.feedback_notes
            existing_feedback.internal_notes = request.internal_notes
            existing_feedback.suggested_next_action = request.suggested_next_action
            existing_feedback.is_shared_with_candidate = request.is_shared_with_candidate
            if request.is_shared_with_candidate and not existing_feedback.shared_at:
                existing_feedback.shared_at = shared_at
            feedback = self.interview_repo.save_feedback(db, existing_feedback)
            action_name = "AUDIT_UPDATE_INTERVIEW_FEEDBACK"
        else:
            feedback = InterviewFeedback(
                interview_id=interview.id,
                application_id=interview.application_id,
                interviewer_id=current_user.id,
                overall_score=request.overall_score,
                technical_score=request.technical_score,
                communication_score=request.communication_score,
                problem_solving_score=request.problem_solving_score,
                recommendation=request.recommendation.upper(),
                strengths=request.strengths or [],
                improvement_areas=request.improvement_areas or [],
                competency_breakdown=request.competency_breakdown or [],
                feedback_notes=request.feedback_notes,
                internal_notes=request.internal_notes,
                suggested_next_action=request.suggested_next_action,
                is_shared_with_candidate=request.is_shared_with_candidate,
                shared_at=shared_at,
            )
            feedback = self.interview_repo.create_feedback(db, feedback)
            action_name = "AUDIT_SUBMIT_INTERVIEW_FEEDBACK"

        if interview.status in (InterviewStatus.SCHEDULED.value, InterviewStatus.PENDING.value):
            interview.status = InterviewStatus.COMPLETED.value
            db.commit()
            db.refresh(interview)

        self.audit_repo.create(
            db=db,
            admin_id=current_user.id if current_user.role == UserRole.ADMIN else None,
            target_user_id=interview.candidate_id,
            action=action_name,
            details={
                "feedback_id": feedback.id,
                "interview_id": interview.id,
                "application_id": interview.application_id,
                "interviewer_id": current_user.id,
                "overall_score": feedback.overall_score,
                "recommendation": feedback.recommendation,
                "is_shared": feedback.is_shared_with_candidate,
                "suggested_next_action": feedback.suggested_next_action,
            },
        )

        return self._format_feedback_response(feedback)

    def get_interview_feedback(
        self,
        db: Session,
        current_user: User,
        interview_id: int,
    ) -> ConsolidatedTeamFeedbackResponse:
        interview = self.interview_repo.get_by_id(db, interview_id)
        if not interview:
            raise NotFoundException(f"Interview session {interview_id} not found")

        is_candidate = current_user.id == interview.candidate_id
        is_company = current_user.id == interview.company_id or current_user.role == UserRole.COMPANY
        is_admin = current_user.role == UserRole.ADMIN

        if not (is_candidate or is_company or is_admin):
            raise ForbiddenException("Access denied to interview evaluation")

        if is_candidate:
            feedbacks = self.interview_repo.get_feedbacks_by_interview_id(
                db, interview_id=interview.id, only_shared=True
            )
            return self._format_consolidated_feedback(interview, feedbacks, hide_internal=True)
        else:
            feedbacks = self.interview_repo.get_feedbacks_by_interview_id(
                db, interview_id=interview.id, only_shared=False
            )
            return self._format_consolidated_feedback(interview, feedbacks, hide_internal=False)

    def get_application_feedback(
        self,
        db: Session,
        current_user: User,
        application_id: int,
    ) -> Optional[ConsolidatedTeamFeedbackResponse]:
        application = self.application_repo.get_by_id(db, application_id)
        if not application:
            raise NotFoundException(f"Job application {application_id} not found")

        is_candidate = current_user.id == application.learner_id
        is_company = (
            application.job and current_user.id == application.job.company_id
        ) or current_user.role == UserRole.COMPANY
        is_admin = current_user.role == UserRole.ADMIN

        if not (is_candidate or is_company or is_admin):
            raise ForbiddenException("Access denied to application feedback")

        interview = self.interview_repo.get_by_application_id(db, application_id)
        if not interview:
            return None

        return self.get_interview_feedback(db, current_user, interview.id)

    def update_interview_feedback(
        self,
        db: Session,
        current_user: User,
        feedback_id: int,
        request: InterviewFeedbackUpdate,
    ) -> InterviewFeedbackResponse:
        feedback = self.interview_repo.get_feedback_by_id(db, feedback_id)
        if not feedback:
            raise NotFoundException(f"Interview feedback {feedback_id} not found")

        interview = feedback.interview_request
        is_interviewer = current_user.id == feedback.interviewer_id
        is_company_owner = interview and current_user.id == interview.company_id
        is_admin = current_user.role == UserRole.ADMIN

        if not (is_interviewer or is_company_owner or is_admin):
            raise ForbiddenException("You cannot edit this evaluation record")

        if request.overall_score is not None:
            feedback.overall_score = request.overall_score
        if request.technical_score is not None:
            feedback.technical_score = request.technical_score
        if request.communication_score is not None:
            feedback.communication_score = request.communication_score
        if request.problem_solving_score is not None:
            feedback.problem_solving_score = request.problem_solving_score
        if request.recommendation is not None:
            feedback.recommendation = request.recommendation.upper()
        if request.strengths is not None:
            feedback.strengths = request.strengths
        if request.improvement_areas is not None:
            feedback.improvement_areas = request.improvement_areas
        if request.competency_breakdown is not None:
            feedback.competency_breakdown = request.competency_breakdown
        if request.feedback_notes is not None:
            feedback.feedback_notes = request.feedback_notes
        if request.internal_notes is not None:
            feedback.internal_notes = request.internal_notes
        if request.suggested_next_action is not None:
            feedback.suggested_next_action = request.suggested_next_action
        if request.is_shared_with_candidate is not None:
            feedback.is_shared_with_candidate = request.is_shared_with_candidate
            if request.is_shared_with_candidate and not feedback.shared_at:
                feedback.shared_at = datetime.now(timezone.utc)

        updated = self.interview_repo.save_feedback(db, feedback)

        self.audit_repo.create(
            db=db,
            admin_id=current_user.id if current_user.role == UserRole.ADMIN else None,
            target_user_id=interview.candidate_id if interview else None,
            action="AUDIT_UPDATE_INTERVIEW_FEEDBACK",
            details={
                "feedback_id": feedback.id,
                "interview_id": feedback.interview_id,
                "overall_score": feedback.overall_score,
                "recommendation": feedback.recommendation,
                "is_shared": feedback.is_shared_with_candidate,
            },
        )

        return self._format_feedback_response(updated)

    def share_interview_feedback(
        self,
        db: Session,
        current_user: User,
        interview_id: int,
        is_shared: bool = True,
    ) -> ConsolidatedTeamFeedbackResponse:
        interview = self.interview_repo.get_by_id(db, interview_id)
        if not interview:
            raise NotFoundException(f"Interview session {interview_id} not found")

        is_company = current_user.id == interview.company_id or current_user.role == UserRole.COMPANY
        is_admin = current_user.role == UserRole.ADMIN

        if not (is_company or is_admin):
            raise ForbiddenException("Only hiring companies or admins can release feedback")

        feedbacks = self.interview_repo.get_feedbacks_by_interview_id(
            db, interview_id=interview.id, only_shared=False
        )
        if not feedbacks:
            raise BadRequestException("No evaluation scorecard found to share")

        now = datetime.now(timezone.utc)
        for f in feedbacks:
            f.is_shared_with_candidate = is_shared
            if is_shared and not f.shared_at:
                f.shared_at = now
            self.interview_repo.save_feedback(db, f)

        self.audit_repo.create(
            db=db,
            admin_id=current_user.id if current_user.role == UserRole.ADMIN else None,
            target_user_id=interview.candidate_id,
            action="AUDIT_SHARE_INTERVIEW_FEEDBACK",
            details={
                "interview_id": interview.id,
                "application_id": interview.application_id,
                "shared": is_shared,
                "feedbacks_count": len(feedbacks),
            },
        )

        return self._format_consolidated_feedback(interview, feedbacks, hide_internal=False)

    def get_feedback_audit_logs(
        self,
        db: Session,
        current_user: User,
        interview_id: Optional[int] = None,
        page: int = 1,
        size: int = 50,
    ) -> Dict[str, Any]:
        if current_user.role != UserRole.ADMIN:
            raise ForbiddenException("Administrative privileges required for compliance logs")

        offset = (page - 1) * size
        items, total = self.interview_repo.list_feedback_audit_logs(
            db, interview_id=interview_id, limit=size, offset=offset
        )
        responses = [
            FeedbackAuditLogResponse(
                id=item.id,
                action=item.action,
                admin_id=item.admin_id,
                details=item.details,
                created_at=item.created_at,
            )
            for item in items
        ]
        return {
            "items": responses,
            "total": total,
            "page": page,
            "size": size,
            "total_pages": math.ceil(total / size) if size > 0 else 0,
        }
