from typing import Optional
from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_user, require_role
from app.models.user import User, UserRole
from app.schemas.auth import ApiResponse
from app.schemas.interview import (
    InterviewRequestCreate,
    InterviewSelectSlotRequest,
    InterviewRescheduleRequest,
    InterviewStatusUpdateRequest,
    InterviewRequestResponse,
    PaginatedInterviewResponse,
)
from app.services.interview_service import InterviewService

router = APIRouter(tags=["Interview Request & Scheduling (SKL-9)"])
interview_service = InterviewService()


@router.post(
    "/applications/{application_id}/interview-request",
    response_model=ApiResponse[InterviewRequestResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Company proposes interview slots & meeting link (SKL-9 Deliverable)",
)
def create_interview_request(
    application_id: int,
    request: InterviewRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[InterviewRequestResponse]:
    created = interview_service.create_interview_request(
        db=db,
        current_user=current_user,
        application_id=application_id,
        request=request,
    )
    return ApiResponse[InterviewRequestResponse](
        success=True,
        message="Interview request sent successfully to candidate",
        data=created,
    )


@router.get(
    "/interviews/me",
    response_model=ApiResponse[PaginatedInterviewResponse],
    status_code=status.HTTP_200_OK,
    summary="Get user interview sessions (Candidate / Company) (SKL-9 Deliverable)",
)
def get_my_interviews(
    status: Optional[str] = Query(default=None, description="Filter by status (PENDING, SCHEDULED, RESCHEDULE_REQUESTED, COMPLETED, CANCELLED)"),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[PaginatedInterviewResponse]:
    result = interview_service.get_my_interviews(
        db=db,
        current_user=current_user,
        status=status,
        page=page,
        size=size,
    )
    return ApiResponse[PaginatedInterviewResponse](
        success=True,
        message="Interview sessions retrieved successfully",
        data=result,
    )


@router.get(
    "/interviews/{interview_id}",
    response_model=ApiResponse[InterviewRequestResponse],
    status_code=status.HTTP_200_OK,
    summary="Get interview session details",
)
def get_interview(
    interview_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[InterviewRequestResponse]:
    result = interview_service.get_interview_by_id(
        db=db, current_user=current_user, interview_id=interview_id
    )
    return ApiResponse[InterviewRequestResponse](
        success=True,
        message="Interview details retrieved",
        data=result,
    )


@router.get(
    "/applications/{application_id}/interview",
    response_model=ApiResponse[Optional[InterviewRequestResponse]],
    status_code=status.HTTP_200_OK,
    summary="Get interview request for a specific application",
)
def get_application_interview(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[Optional[InterviewRequestResponse]]:
    result = interview_service.get_interview_for_application(
        db=db, current_user=current_user, application_id=application_id
    )
    return ApiResponse[Optional[InterviewRequestResponse]](
        success=True,
        message="Application interview retrieved",
        data=result,
    )


@router.post(
    "/interviews/{interview_id}/select-slot",
    response_model=ApiResponse[InterviewRequestResponse],
    status_code=status.HTTP_200_OK,
    summary="Candidate accepts preferred slot (SKL-9 Deliverable)",
)
def select_slot(
    interview_id: int,
    request: InterviewSelectSlotRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[InterviewRequestResponse]:
    result = interview_service.select_slot(
        db=db,
        current_user=current_user,
        interview_id=interview_id,
        request=request,
    )
    return ApiResponse[InterviewRequestResponse](
        success=True,
        message="Time slot selected and confirmed! Calendar invite generated.",
        data=result,
    )


@router.post(
    "/interviews/{interview_id}/reschedule",
    response_model=ApiResponse[InterviewRequestResponse],
    status_code=status.HTTP_200_OK,
    summary="Candidate or recruiter requests rescheduling (SKL-9 Deliverable)",
)
def request_reschedule(
    interview_id: int,
    request: InterviewRescheduleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[InterviewRequestResponse]:
    result = interview_service.request_reschedule(
        db=db,
        current_user=current_user,
        interview_id=interview_id,
        request=request,
    )
    return ApiResponse[InterviewRequestResponse](
        success=True,
        message="Reschedule request submitted successfully",
        data=result,
    )


@router.patch(
    "/interviews/{interview_id}/status",
    response_model=ApiResponse[InterviewRequestResponse],
    status_code=status.HTTP_200_OK,
    summary="Update interview session status (COMPLETED, CANCELLED)",
)
def update_interview_status(
    interview_id: int,
    request: InterviewStatusUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[InterviewRequestResponse]:
    result = interview_service.update_status(
        db=db,
        current_user=current_user,
        interview_id=interview_id,
        request=request,
    )
    return ApiResponse[InterviewRequestResponse](
        success=True,
        message="Interview status updated successfully",
        data=result,
    )


@router.get(
    "/interviews/{interview_id}/ics",
    status_code=status.HTTP_200_OK,
    summary="Download RFC 5545 iCalendar (.ics) invite file (SKL-9 Deliverable)",
)
def download_calendar_ics(
    interview_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ics_text, filename = interview_service.generate_ics_for_interview(
        db=db, current_user=current_user, interview_id=interview_id
    )
    return Response(
        content=ics_text,
        media_type="text/calendar; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-cache",
        },
    )
