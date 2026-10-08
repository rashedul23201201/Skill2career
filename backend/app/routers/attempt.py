from typing import Optional, List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.auth import ApiResponse
from app.schemas.mock_test import (
    TestAttemptStartResponse,
    TestAttemptResponse,
    TestAttemptSaveAnswersRequest,
    TestAttemptSubmitRequest,
)
from app.services.mock_test_service import MockTestService

router = APIRouter(prefix="/attempts", tags=["Test Attempts & Timer (SKL-57)"])
mock_test_service = MockTestService()


@router.get(
    "/{attempt_id}",
    response_model=ApiResponse[TestAttemptStartResponse],
    status_code=status.HTTP_200_OK,
    summary="Get active or completed attempt details and questions (SKL-57)",
)
def get_attempt_session(
    attempt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[TestAttemptStartResponse]:
    attempt = mock_test_service.get_attempt(db=db, attempt_id=attempt_id, current_user=current_user)
    return ApiResponse[TestAttemptStartResponse](
        success=True,
        message="Test attempt session retrieved successfully",
        data=attempt,
    )


@router.put(
    "/{attempt_id}/answers",
    response_model=ApiResponse[TestAttemptResponse],
    status_code=status.HTTP_200_OK,
    summary="Record intermediate answers (SKL-57 AC-2)",
)
def save_intermediate_answers(
    attempt_id: int,
    request: TestAttemptSaveAnswersRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[TestAttemptResponse]:
    saved = mock_test_service.save_attempt_answers(
        db=db, attempt_id=attempt_id, current_user=current_user, request=request
    )
    return ApiResponse[TestAttemptResponse](
        success=True,
        message="Answers recorded successfully",
        data=saved,
    )


@router.post(
    "/{attempt_id}/submit-answers",
    response_model=ApiResponse[TestAttemptResponse],
    status_code=status.HTTP_200_OK,
    summary="Submit test answers manually or upon timer expiry (SKL-57 AC-3, AC-4)",
)
def submit_test_answers(
    attempt_id: int,
    request: Optional[TestAttemptSubmitRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[TestAttemptResponse]:
    completed = mock_test_service.submit_attempt_answers(
        db=db, attempt_id=attempt_id, current_user=current_user, request=request
    )
    return ApiResponse[TestAttemptResponse](
        success=True,
        message="Test attempt submitted successfully",
        data=completed,
    )


@router.get(
    "",
    response_model=ApiResponse[List[TestAttemptResponse]],
    status_code=status.HTTP_200_OK,
    summary="Get current user test attempt history",
)
def get_my_attempts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[List[TestAttemptResponse]]:
    attempts = mock_test_service.get_learner_attempts(db=db, current_user=current_user)
    return ApiResponse[List[TestAttemptResponse]](
        success=True,
        message="Test attempts history retrieved successfully",
        data=attempts,
    )
