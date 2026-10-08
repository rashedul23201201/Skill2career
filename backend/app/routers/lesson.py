from typing import Optional
from fastapi import APIRouter, Depends, status, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_user, get_optional_current_user
from app.models.user import User
from app.schemas.auth import ApiResponse
from app.schemas.course import (
    LessonSchema,
    LessonUpdateRequest,
    StudyMaterialUploadResponse,
)
from app.services.course_service import CourseService

router = APIRouter(prefix="/lessons", tags=["Lesson & Study Material Management (SKL-55)"])
course_service = CourseService()


@router.get(
    "/{lesson_id}",
    response_model=ApiResponse[LessonSchema],
    status_code=status.HTTP_200_OK,
    summary="Get single lesson details and study materials (SKL-55 AC-3)",
)
def get_lesson(
    lesson_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
) -> ApiResponse[LessonSchema]:
    """Retrieve details for a single lesson including study materials and video stream."""
    lesson = course_service.get_lesson_by_id(
        db=db, lesson_id=lesson_id, current_user=current_user
    )
    return ApiResponse[LessonSchema](
        success=True,
        message="Lesson retrieved successfully",
        data=lesson,
    )


@router.put(
    "/{lesson_id}",
    response_model=ApiResponse[LessonSchema],
    status_code=status.HTTP_200_OK,
    summary="Update lesson content and study materials (SKL-55 AC-2)",
)
def update_lesson(
    lesson_id: int,
    request: LessonUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[LessonSchema]:
    """Update lesson metadata, title, duration, video URL, or study materials."""
    updated = course_service.update_lesson(
        db=db, lesson_id=lesson_id, current_user=current_user, request=request
    )
    return ApiResponse[LessonSchema](
        success=True,
        message="Lesson updated successfully",
        data=updated,
    )


@router.delete(
    "/{lesson_id}",
    response_model=ApiResponse[dict],
    status_code=status.HTTP_200_OK,
    summary="Delete a lesson (SKL-55 AC-5)",
)
def delete_lesson(
    lesson_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[dict]:
    """Remove a lesson. Permitted only for authoring instructor or platform admin."""
    result = course_service.delete_lesson(
        db=db, lesson_id=lesson_id, current_user=current_user
    )
    return ApiResponse[dict](
        success=True,
        message="Lesson deleted successfully",
        data=result,
    )


@router.post(
    "/{lesson_id}/materials",
    response_model=ApiResponse[StudyMaterialUploadResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Upload study material document to a lesson (SKL-55 AC-2)",
)
def upload_study_material(
    lesson_id: int,
    file: UploadFile = File(..., description="Study material file (PDF, DOCX, PPTX, TXT, ZIP, max 25MB)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[StudyMaterialUploadResponse]:
    """Upload study material (e.g. PDF lecture notes) and attach it to the lesson."""
    result = course_service.upload_lesson_material(
        db=db, lesson_id=lesson_id, current_user=current_user, file=file
    )
    return ApiResponse[StudyMaterialUploadResponse](
        success=True,
        message=result.message,
        data=result,
    )


@router.get(
    "/{lesson_id}/materials/{filename}/download",
    status_code=status.HTTP_200_OK,
    summary="Download lesson study material (SKL-55 AC-3)",
)
def download_study_material(
    lesson_id: int,
    filename: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
) -> FileResponse:
    """Download study material file for an available course lesson."""
    return course_service.download_lesson_material(
        db=db, lesson_id=lesson_id, filename=filename, current_user=current_user
    )


@router.delete(
    "/{lesson_id}/materials/{filename}",
    response_model=ApiResponse[LessonSchema],
    status_code=status.HTTP_200_OK,
    summary="Delete a study material attachment from a lesson",
)
def delete_study_material(
    lesson_id: int,
    filename: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[LessonSchema]:
    """Remove an attached study material from a lesson."""
    updated = course_service.delete_lesson_material(
        db=db, lesson_id=lesson_id, filename=filename, current_user=current_user
    )
    return ApiResponse[LessonSchema](
        success=True,
        message="Material removed successfully",
        data=updated,
    )
