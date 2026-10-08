import logging
from typing import Optional, List, Tuple
from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session
from app.models.screening import ScreeningQuestion, CandidateEvaluation

logger = logging.getLogger(__name__)


class ScreeningRepository:
    @staticmethod
    def create_question(db: Session, question: ScreeningQuestion) -> ScreeningQuestion:
        db.add(question)
        db.commit()
        db.refresh(question)
        return question

    @staticmethod
    def get_question_by_id(db: Session, question_id: int) -> Optional[ScreeningQuestion]:
        stmt = select(ScreeningQuestion).where(ScreeningQuestion.id == question_id)
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def get_questions_by_job_id(db: Session, job_id: int) -> List[ScreeningQuestion]:
        stmt = (
            select(ScreeningQuestion)
            .where(ScreeningQuestion.job_id == job_id)
            .order_by(ScreeningQuestion.order_index.asc(), ScreeningQuestion.id.asc())
        )
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def update_question(db: Session, question: ScreeningQuestion) -> ScreeningQuestion:
        db.commit()
        db.refresh(question)
        return question

    @staticmethod
    def delete_question(db: Session, question: ScreeningQuestion) -> None:
        db.delete(question)
        db.commit()

    @staticmethod
    def create_evaluation(db: Session, evaluation: CandidateEvaluation) -> CandidateEvaluation:
        db.add(evaluation)
        db.commit()
        db.refresh(evaluation)
        return evaluation

    @staticmethod
    def get_evaluation_by_id(db: Session, evaluation_id: int) -> Optional[CandidateEvaluation]:
        stmt = select(CandidateEvaluation).where(CandidateEvaluation.id == evaluation_id)
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def update_evaluation(db: Session, evaluation: CandidateEvaluation) -> CandidateEvaluation:
        db.commit()
        db.refresh(evaluation)
        return evaluation

    @staticmethod
    def get_evaluations_paginated(
        db: Session,
        job_id: int,
        page: int = 1,
        size: int = 10,
        min_score: Optional[int] = None,
        deal_breaker_passed: Optional[bool] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[CandidateEvaluation], int, int, int, float]:
        base_query = select(CandidateEvaluation).where(CandidateEvaluation.job_id == job_id)

        if min_score is not None:
            base_query = base_query.where(CandidateEvaluation.match_score >= min_score)

        if deal_breaker_passed is not None:
            base_query = base_query.where(CandidateEvaluation.deal_breaker_passed == deal_breaker_passed)

        if status:
            base_query = base_query.where(CandidateEvaluation.status == status.upper())

        if search:
            search_pattern = f"%{search.strip()}%"
            base_query = base_query.where(
                or_(
                    CandidateEvaluation.candidate_name.ilike(search_pattern),
                    CandidateEvaluation.candidate_email.ilike(search_pattern),
                    CandidateEvaluation.key_answers_preview.ilike(search_pattern),
                )
            )

        total = db.scalar(select(func.count()).select_from(base_query.subquery())) or 0
        passed_count = (
            db.scalar(
                select(func.count(CandidateEvaluation.id)).where(
                    CandidateEvaluation.job_id == job_id,
                    CandidateEvaluation.deal_breaker_passed.is_(True),
                )
            )
            or 0
        )
        disqualified_count = (
            db.scalar(
                select(func.count(CandidateEvaluation.id)).where(
                    CandidateEvaluation.job_id == job_id,
                    CandidateEvaluation.deal_breaker_passed.is_(False),
                )
            )
            or 0
        )
        avg_score = (
            db.scalar(
                select(func.avg(CandidateEvaluation.match_score)).where(
                    CandidateEvaluation.job_id == job_id
                )
            )
            or 0.0
        )

        offset = (page - 1) * size
        items_query = (
            base_query.order_by(
                CandidateEvaluation.deal_breaker_passed.desc(),
                CandidateEvaluation.match_score.desc(),
                CandidateEvaluation.created_at.desc(),
            )
            .offset(offset)
            .limit(size)
        )

        items = list(db.execute(items_query).scalars().all())
        return items, total, passed_count, disqualified_count, round(float(avg_score), 1)
