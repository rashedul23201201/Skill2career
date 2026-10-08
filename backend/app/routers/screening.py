from typing import Optional, List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_user, get_optional_current_user, require_role
from app.models.user import User, UserRole
from app.schemas.auth import ApiResponse
from app.schemas.screening import (
    ScreeningQuestionCreateRequest,
    ScreeningQuestionUpdateRequest,
    ScreeningQuestionResponse,
    CandidateEvaluationCreateRequest,
    CandidateEvaluationStatusUpdateRequest,
    CandidateEvaluationResponse,
    PaginatedCandidateEvaluationResponse,
)
from app.services.screening_service import ScreeningService

router = APIRouter(tags=["Candidate Screening & Qualification (Recruitment)"])
screening_service = ScreeningService()


@router.post(
    "/jobs/{job_id}/screening-questions",
    response_model=ApiResponse[ScreeningQuestionResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Configure a screening question for a job posting (SKL-8 AC-1)",
)
def add_screening_question(
    job_id: int,
    request: ScreeningQuestionCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.COMPANY, UserRole.ADMIN)),
) -> ApiResponse[ScreeningQuestionResponse]:
    created = screening_service.add_question(
        db=db, current_user=current_user, job_id=job_id, request=request
    )
    return ApiResponse[ScreeningQuestionResponse](
        success=True,
        message="Screening question added successfully",
        data=created,
    )


@router.get(
    "/jobs/{job_id}/screening-questions",
    response_model=ApiResponse[List[ScreeningQuestionResponse]],
    status_code=status.HTTP_200_OK,
    summary="Get all screening questions configured for a vacancy (SKL-8)",
)
def get_screening_questions(
    job_id: int,
    db: Session = Depends(get_db),
) -> ApiResponse[List[ScreeningQuestionResponse]]:
    questions = screening_service.get_questions(db=db, job_id=job_id)
    return ApiResponse[List[ScreeningQuestionResponse]](
        success=True,
        message="Screening questions retrieved successfully",
        data=questions,
    )


@router.put(
    "/screening-questions/{question_id}",
    response_model=ApiResponse[ScreeningQuestionResponse],
    status_code=status.HTTP_200_OK,
    summary="Update screening question parameters (SKL-8 AC-1, AC-5)",
)
def update_screening_question(
    question_id: int,
    request: ScreeningQuestionUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[ScreeningQuestionResponse]:
    updated = screening_service.update_question(
        db=db, current_user=current_user, question_id=question_id, request=request
    )
    return ApiResponse[ScreeningQuestionResponse](
        success=True,
        message="Screening question updated successfully",
        data=updated,
    )


@router.delete(
    "/screening-questions/{question_id}",
    response_model=ApiResponse[dict],
    status_code=status.HTTP_200_OK,
    summary="Remove a screening question (SKL-8 AC-5)",
)
def delete_screening_question(
    question_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[dict]:
    screening_service.delete_question(
        db=db, current_user=current_user, question_id=question_id
    )
    return ApiResponse[dict](
        success=True,
        message="Screening question deleted successfully",
        data={"question_id": question_id},
    )


@router.post(
    "/jobs/{job_id}/screen-candidate",
    response_model=ApiResponse[CandidateEvaluationResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Submit candidate screening answers with automated qualification scoring (SKL-8 AC-2, AC-4)",
)
def screen_candidate(
    job_id: int,
    request: CandidateEvaluationCreateRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
) -> ApiResponse[CandidateEvaluationResponse]:
    evaluation = screening_service.evaluate_candidate(
        db=db, job_id=job_id, request=request, candidate_user=current_user
    )
    return ApiResponse[CandidateEvaluationResponse](
        success=True,
        message="Candidate screening answers evaluated successfully",
        data=evaluation,
    )


@router.get(
    "/jobs/{job_id}/applicants",
    response_model=ApiResponse[PaginatedCandidateEvaluationResponse],
    status_code=status.HTTP_200_OK,
    summary="Candidate evaluation pool filterable by score & deal-breaker status (SKL-8 AC-3, Candidate Screening & Qualification.png)",
)
def list_job_applicants(
    job_id: int,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=10, ge=1, le=100),
    min_score: Optional[int] = Query(default=None, ge=0, le=100),
    deal_breaker_passed: Optional[bool] = Query(default=None),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    search: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[PaginatedCandidateEvaluationResponse]:
    result = screening_service.list_candidates(
        db=db,
        current_user=current_user,
        job_id=job_id,
        page=page,
        size=size,
        min_score=min_score,
        deal_breaker_passed=deal_breaker_passed,
        status=status_filter,
        search=search,
    )
    return ApiResponse[PaginatedCandidateEvaluationResponse](
        success=True,
        message="Candidate evaluations retrieved successfully",
        data=result,
    )


@router.patch(
    "/applicants/{evaluation_id}/status",
    response_model=ApiResponse[CandidateEvaluationResponse],
    status_code=status.HTTP_200_OK,
    summary="Update candidate qualification status (Shortlist / Disqualify) (SKL-8 AC-3)",
)
@router.patch(
    "/jobs/{job_id}/applicants/{evaluation_id}/status",
    response_model=ApiResponse[CandidateEvaluationResponse],
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
def update_candidate_status(
    evaluation_id: int,
    payload: CandidateEvaluationStatusUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    job_id: Optional[int] = None,
) -> ApiResponse[CandidateEvaluationResponse]:
    updated = screening_service.update_candidate_status(
        db=db,
        current_user=current_user,
        evaluation_id=evaluation_id,
        status=payload.status.value,
        notes=payload.notes,
    )
    return ApiResponse[CandidateEvaluationResponse](
        success=True,
        message=f"Candidate status updated to {payload.status.value}",
        data=updated,
    )
