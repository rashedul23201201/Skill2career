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
from app.models.interview import InterviewRequest, InterviewSlot, InterviewStatus
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
