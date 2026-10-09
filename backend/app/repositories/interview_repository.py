from typing import Optional, List, Tuple, Dict
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, func, desc, or_
from datetime import datetime, timezone

from app.models.interview import InterviewRequest, InterviewSlot, InterviewStatus


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
