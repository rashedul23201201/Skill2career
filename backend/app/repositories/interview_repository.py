from typing import Optional, List, Tuple, Dict
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, func, desc, or_
from datetime import datetime, timezone

from app.models.interview import InterviewRequest, InterviewSlot, InterviewStatus, InterviewFeedback
from app.models.audit_log import AuditLog


class InterviewRepository:
    def create_interview_request(self, db: Session, request: InterviewRequest) -> InterviewRequest:
        db.add(request)
        db.commit()
        db.refresh(request)
        return request

    def get_by_id(self, db: Session, interview_id: int) -> Optional[InterviewRequest]:
        stmt = (
            select(InterviewRequest)
            .where(InterviewRequest.id == interview_id)
            .options(
                joinedload(InterviewRequest.slots),
                joinedload(InterviewRequest.job),
                joinedload(InterviewRequest.company),
                joinedload(InterviewRequest.candidate),
                joinedload(InterviewRequest.application),
            )
        )
        return db.execute(stmt).unique().scalar_one_or_none()

    def get_by_application_id(self, db: Session, application_id: int) -> Optional[InterviewRequest]:
        stmt = (
            select(InterviewRequest)
            .where(InterviewRequest.application_id == application_id)
            .order_by(desc(InterviewRequest.created_at))
            .options(
                joinedload(InterviewRequest.slots),
                joinedload(InterviewRequest.job),
                joinedload(InterviewRequest.company),
                joinedload(InterviewRequest.candidate),
            )
        )
        return db.execute(stmt).scalars().first()

    def list_for_candidate(
        self,
        db: Session,
        candidate_id: int,
        status: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> Tuple[List[InterviewRequest], int]:
        base_stmt = select(InterviewRequest).where(InterviewRequest.candidate_id == candidate_id)
        count_stmt = select(func.count(InterviewRequest.id)).where(InterviewRequest.candidate_id == candidate_id)

        if status and status.upper() != "ALL":
            base_stmt = base_stmt.where(InterviewRequest.status == status.upper())
            count_stmt = count_stmt.where(InterviewRequest.status == status.upper())

        total = db.scalar(count_stmt) or 0
        items_stmt = (
            base_stmt.order_by(desc(InterviewRequest.created_at))
            .offset(offset)
            .limit(limit)
            .options(
                joinedload(InterviewRequest.slots),
                joinedload(InterviewRequest.job),
                joinedload(InterviewRequest.company),
                joinedload(InterviewRequest.candidate),
            )
        )
        items = db.execute(items_stmt).unique().scalars().all()
        return list(items), total

    def list_for_company(
        self,
        db: Session,
        company_id: int,
        status: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> Tuple[List[InterviewRequest], int]:
        base_stmt = select(InterviewRequest).where(InterviewRequest.company_id == company_id)
        count_stmt = select(func.count(InterviewRequest.id)).where(InterviewRequest.company_id == company_id)

        if status and status.upper() != "ALL":
            base_stmt = base_stmt.where(InterviewRequest.status == status.upper())
            count_stmt = count_stmt.where(InterviewRequest.status == status.upper())

        total = db.scalar(count_stmt) or 0
        items_stmt = (
            base_stmt.order_by(desc(InterviewRequest.created_at))
            .offset(offset)
            .limit(limit)
            .options(
                joinedload(InterviewRequest.slots),
                joinedload(InterviewRequest.job),
                joinedload(InterviewRequest.company),
                joinedload(InterviewRequest.candidate),
            )
        )
        items = db.execute(items_stmt).unique().scalars().all()
        return list(items), total

    def get_counts(self, db: Session, user_id: int, is_company: bool = False) -> Dict[str, int]:
        filter_col = InterviewRequest.company_id if is_company else InterviewRequest.candidate_id
        records = db.execute(
            select(InterviewRequest.status, func.count(InterviewRequest.id))
            .where(filter_col == user_id)
            .group_by(InterviewRequest.status)
        ).all()

        counts = {
            "upcoming": 0,
            "pending": 0,
            "completed": 0,
            "cancelled": 0,
        }
        for st, c in records:
            if st == InterviewStatus.SCHEDULED.value:
                counts["upcoming"] += c
            elif st in (InterviewStatus.PENDING.value, InterviewStatus.RESCHEDULE_REQUESTED.value):
                counts["pending"] += c
            elif st == InterviewStatus.COMPLETED.value:
                counts["completed"] += c
            elif st == InterviewStatus.CANCELLED.value:
                counts["cancelled"] += c
        return counts

    def get_slot_by_id(self, db: Session, slot_id: int) -> Optional[InterviewSlot]:
        stmt = select(InterviewSlot).where(InterviewSlot.id == slot_id)
        return db.scalar(stmt)

    def save(self, db: Session, instance: InterviewRequest) -> InterviewRequest:
        db.add(instance)
        db.commit()
        db.refresh(instance)
        return instance

    def delete(self, db: Session, instance: InterviewRequest) -> None:
        db.delete(instance)
        db.commit()

    def create_feedback(self, db: Session, feedback: InterviewFeedback) -> InterviewFeedback:
        db.add(feedback)
        db.commit()
        db.refresh(feedback)
        return feedback

    def get_feedback_by_id(self, db: Session, feedback_id: int) -> Optional[InterviewFeedback]:
        stmt = (
            select(InterviewFeedback)
            .where(InterviewFeedback.id == feedback_id)
            .options(
                joinedload(InterviewFeedback.interviewer),
                joinedload(InterviewFeedback.interview_request),
                joinedload(InterviewFeedback.application),
            )
        )
        return db.execute(stmt).unique().scalar_one_or_none()

    def get_feedback_by_interviewer(
        self, db: Session, interview_id: int, interviewer_id: int
    ) -> Optional[InterviewFeedback]:
        stmt = (
            select(InterviewFeedback)
            .where(
                InterviewFeedback.interview_id == interview_id,
                InterviewFeedback.interviewer_id == interviewer_id,
            )
            .options(
                joinedload(InterviewFeedback.interviewer),
                joinedload(InterviewFeedback.interview_request),
            )
        )
        return db.execute(stmt).unique().scalar_one_or_none()

    def get_feedbacks_by_interview_id(
        self, db: Session, interview_id: int, only_shared: bool = False
    ) -> List[InterviewFeedback]:
        stmt = select(InterviewFeedback).where(InterviewFeedback.interview_id == interview_id)
        if only_shared:
            stmt = stmt.where(InterviewFeedback.is_shared_with_candidate == True)
        stmt = stmt.order_by(desc(InterviewFeedback.created_at)).options(
            joinedload(InterviewFeedback.interviewer),
            joinedload(InterviewFeedback.interview_request),
        )
        return list(db.execute(stmt).unique().scalars().all())

    def get_feedbacks_by_application_id(
        self, db: Session, application_id: int, only_shared: bool = False
    ) -> List[InterviewFeedback]:
        stmt = select(InterviewFeedback).where(InterviewFeedback.application_id == application_id)
        if only_shared:
            stmt = stmt.where(InterviewFeedback.is_shared_with_candidate == True)
        stmt = stmt.order_by(desc(InterviewFeedback.created_at)).options(
            joinedload(InterviewFeedback.interviewer),
            joinedload(InterviewFeedback.interview_request),
        )
        return list(db.execute(stmt).unique().scalars().all())

    def save_feedback(self, db: Session, feedback: InterviewFeedback) -> InterviewFeedback:
        db.add(feedback)
        db.commit()
        db.refresh(feedback)
        return feedback

    def delete_feedback(self, db: Session, feedback: InterviewFeedback) -> None:
        db.delete(feedback)
        db.commit()

    def list_feedback_audit_logs(
        self, db: Session, interview_id: Optional[int] = None, limit: int = 50, offset: int = 0
    ) -> Tuple[List[AuditLog], int]:
        stmt = select(AuditLog).where(AuditLog.action.like("%INTERVIEW_FEEDBACK%"))
        count_stmt = select(func.count(AuditLog.id)).where(AuditLog.action.like("%INTERVIEW_FEEDBACK%"))
        if interview_id:
            stmt = stmt.where(AuditLog.details["interview_id"].as_integer() == interview_id)
            count_stmt = count_stmt.where(AuditLog.details["interview_id"].as_integer() == interview_id)
        total = db.scalar(count_stmt) or 0
        items = list(db.execute(stmt.order_by(desc(AuditLog.created_at)).offset(offset).limit(limit)).scalars().all())
        return items, total
