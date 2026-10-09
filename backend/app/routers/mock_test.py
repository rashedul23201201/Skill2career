from typing import Optional, List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_user, get_optional_current_user, require_role
from app.models.user import User, UserRole
from app.schemas.auth import ApiResponse
from app.schemas.mock_test import (
    MockTestCreateRequest,
    MockTestUpdateRequest,
    MockTestStatusUpdateRequest,
    MockTestResponse,
    MockTestDetailResponse,
    TestQuestionCreate,
    TestQuestionUpdate,
    TestQuestionResponse,
    MockTestSyncQuestionsRequest,
    PaginatedMockTestResponse,
    TestAttemptStartResponse,
    TestAttemptResponse,
    TestResultResponse,
)
from app.services.mock_test_service import MockTestService

router = APIRouter(prefix="/mock-tests", tags=["Mock Test Management (Assessments)"])
mock_test_service = MockTestService()


@router.post(
    "",
    response_model=ApiResponse[MockTestResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new mock test (SKL-56 AC-1)",
)
def create_mock_test(
    request: MockTestCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.INSTRUCTOR, UserRole.ADMIN)),
) -> ApiResponse[MockTestResponse]:
    created = mock_test_service.create_mock_test(db=db, current_user=current_user, request=request)
    return ApiResponse[MockTestResponse](
        success=True,
        message="Mock test created successfully",
        data=created,
    )


@router.get(
    "",
    response_model=ApiResponse[PaginatedMockTestResponse],
    status_code=status.HTTP_200_OK,
    summary="List or search mock tests (SKL-56 AC-3, Mock Tests.png)",
)
def list_mock_tests(
    page: int = Query(default=1, ge=1, description="Page number"),
    size: int = Query(default=10, ge=1, le=100, description="Items per page"),
    category: Optional[str] = Query(default=None, description="Category filter"),
    search: Optional[str] = Query(default=None, description="Search keyword"),
    my_tests: bool = Query(default=False, description="Filter only mock tests authored by current user"),
    status_filter: Optional[str] = Query(default=None, alias="status", description="Status filter"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
) -> ApiResponse[PaginatedMockTestResponse]:
    result = mock_test_service.list_mock_tests_paginated(
        db=db,
        page=page,
        size=size,
        category=category,
        search=search,
        my_tests=my_tests,
        status=status_filter,
        current_user=current_user,
    )
    return ApiResponse[PaginatedMockTestResponse](
        success=True,
        message="Mock tests retrieved successfully",
        data=result,
    )


@router.get(
    "/{test_id}",
    response_model=ApiResponse[MockTestDetailResponse],
    status_code=status.HTTP_200_OK,
    summary="Get mock test details and questions (SKL-56)",
)
def get_mock_test(
    test_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
) -> ApiResponse[MockTestDetailResponse]:
    test = mock_test_service.get_mock_test_by_id(db=db, test_id=test_id, current_user=current_user)
    return ApiResponse[MockTestDetailResponse](
        success=True,
        message="Mock test details retrieved successfully",
        data=test,
    )


@router.put(
    "/{test_id}",
    response_model=ApiResponse[MockTestResponse],
    status_code=status.HTTP_200_OK,
    summary="Update mock test metadata (SKL-56)",
)
def update_mock_test(
    test_id: int,
    request: MockTestUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[MockTestResponse]:
    updated = mock_test_service.update_mock_test(
        db=db, test_id=test_id, current_user=current_user, request=request
    )
    return ApiResponse[MockTestResponse](
        success=True,
        message="Mock test updated successfully",
        data=updated,
    )


@router.delete(
    "/{test_id}",
    response_model=ApiResponse[dict],
    status_code=status.HTTP_200_OK,
    summary="Delete a mock test (SKL-56)",
)
def delete_mock_test(
    test_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[dict]:
    mock_test_service.delete_mock_test(db=db, test_id=test_id, current_user=current_user)
    return ApiResponse[dict](
        success=True,
        message="Mock test deleted successfully",
        data={"test_id": test_id},
    )


@router.patch(
    "/{test_id}/status",
    response_model=ApiResponse[MockTestResponse],
    status_code=status.HTTP_200_OK,
    summary="Toggle mock test status (DRAFT / PUBLISHED / ARCHIVED) (SKL-56)",
)
def update_mock_test_status(
    test_id: int,
    request: MockTestStatusUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[MockTestResponse]:
    updated = mock_test_service.update_mock_test_status(
        db=db, test_id=test_id, current_user=current_user, status=request.status
    )
    return ApiResponse[MockTestResponse](
        success=True,
        message=f"Mock test status updated to {request.status.value}",
        data=updated,
    )


@router.post(
    "/{test_id}/questions",
    response_model=ApiResponse[TestQuestionResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Add a question to a mock test (SKL-56 AC-2)",
)
def add_question(
    test_id: int,
    request: TestQuestionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[TestQuestionResponse]:
    question = mock_test_service.add_question(
        db=db, test_id=test_id, current_user=current_user, request=request
    )
    return ApiResponse[TestQuestionResponse](
        success=True,
        message="Question added to mock test successfully",
        data=question,
    )


@router.get(
    "/{test_id}/questions",
    response_model=ApiResponse[List[TestQuestionResponse]],
    status_code=status.HTTP_200_OK,
    summary="List questions in a mock test (SKL-56)",
)
def list_questions(
    test_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
) -> ApiResponse[List[TestQuestionResponse]]:
    questions = mock_test_service.get_test_questions(
        db=db, test_id=test_id, current_user=current_user
    )
    return ApiResponse[List[TestQuestionResponse]](
        success=True,
        message="Test questions retrieved successfully",
        data=questions,
    )


@router.put(
    "/{test_id}/questions/{question_id}",
    response_model=ApiResponse[TestQuestionResponse],
    status_code=status.HTTP_200_OK,
    summary="Update a test question (SKL-56)",
)
def update_question(
    test_id: int,
    question_id: int,
    request: TestQuestionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[TestQuestionResponse]:
    updated = mock_test_service.update_question(
        db=db, test_id=test_id, question_id=question_id, current_user=current_user, request=request
    )
    return ApiResponse[TestQuestionResponse](
        success=True,
        message="Question updated successfully",
        data=updated,
    )


@router.delete(
    "/{test_id}/questions/{question_id}",
    response_model=ApiResponse[dict],
    status_code=status.HTTP_200_OK,
    summary="Delete a test question (SKL-56)",
)
def delete_question(
    test_id: int,
    question_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[dict]:
    mock_test_service.delete_question(
        db=db, test_id=test_id, question_id=question_id, current_user=current_user
    )
    return ApiResponse[dict](
        success=True,
        message="Question deleted successfully",
        data={"test_id": test_id, "question_id": question_id},
    )


@router.post(
    "/{test_id}/questions/sync",
    response_model=ApiResponse[List[TestQuestionResponse]],
    status_code=status.HTTP_200_OK,
    summary="Bulk sync questions for a mock test (SKL-56)",
)
def sync_questions(
    test_id: int,
    request: MockTestSyncQuestionsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[List[TestQuestionResponse]]:
    questions = mock_test_service.sync_questions(
        db=db, test_id=test_id, current_user=current_user, questions_data=request.questions
    )
    return ApiResponse[List[TestQuestionResponse]](
        success=True,
        message="Mock test questions synchronized successfully",
        data=questions,
    )


@router.post(
    "/{test_id}/start-attempt",
    response_model=ApiResponse[TestAttemptStartResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Start or resume a mock test attempt with timer (SKL-57 AC-1)",
)
def start_attempt(
    test_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[TestAttemptStartResponse]:
    attempt = mock_test_service.start_attempt(db=db, test_id=test_id, current_user=current_user)
    return ApiResponse[TestAttemptStartResponse](
        success=True,
        message="Test attempt session started successfully",
        data=attempt,
    )


@router.get(
    "/{test_id}/my-attempts",
    response_model=ApiResponse[List[TestAttemptResponse]],
    status_code=status.HTTP_200_OK,
    summary="Get user's attempts on this mock test (SKL-57)",
)
def get_my_attempts_for_test(
    test_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[List[TestAttemptResponse]]:
    attempts = mock_test_service.get_learner_attempts(db=db, current_user=current_user, test_id=test_id)
    return ApiResponse[List[TestAttemptResponse]](
        success=True,
        message="Test attempts retrieved successfully",
        data=attempts,
    )


@router.get(
    "/{test_id}/results",
    response_model=ApiResponse[List[TestResultResponse]],
    status_code=status.HTTP_200_OK,
    summary="Get learner results and performance analysis for a mock test (Instructor view) (SKL-58)",
)
def get_mock_test_results(
    test_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[List[TestResultResponse]]:
    results = mock_test_service.get_test_results_for_instructor(
        db=db, test_id=test_id, current_user=current_user
    )
    return ApiResponse[List[TestResultResponse]](
        success=True,
        message="Mock test results retrieved successfully",
        data=results,
    )


