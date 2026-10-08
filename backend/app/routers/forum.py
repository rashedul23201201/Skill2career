from typing import Optional, List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_user, get_optional_current_user, require_role
from app.models.user import User, UserRole
from app.schemas.auth import ApiResponse
from app.schemas.forum import (
    ForumCategoryResponse,
    ForumPostCreate,
    ForumPostUpdate,
    ForumPostResponse,
    ForumPostDetailResponse,
    PaginatedForumPostResponse,
    ForumCommentCreate,
    ForumCommentUpdate,
    ForumCommentResponse,
    ForumLikeToggleResponse,
    ForumReportCreate,
    ForumReportResponse,
    ForumReportStatusUpdate,
)
from app.services.forum_service import ForumService

router = APIRouter(prefix="/forum", tags=["Discussion Forum (SKL-14)"])
forum_service = ForumService()


@router.get(
    "/categories",
    response_model=ApiResponse[List[ForumCategoryResponse]],
    status_code=status.HTTP_200_OK,
    summary="List all forum categories with topic counts (SKL-14 AC-1)",
)
def get_categories(
    db: Session = Depends(get_db),
) -> ApiResponse[List[ForumCategoryResponse]]:
    categories = forum_service.get_categories(db=db)
    return ApiResponse[List[ForumCategoryResponse]](
        success=True,
        message="Forum categories retrieved successfully",
        data=categories,
    )


@router.get(
    "/posts",
    response_model=ApiResponse[PaginatedForumPostResponse],
    status_code=status.HTTP_200_OK,
    summary="List paginated discussion posts with filters and search (SKL-14 AC-1, AC-5)",
)
def get_posts(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Items per page"),
    category_id: Optional[int] = Query(None, description="Optional category filter"),
    search: Optional[str] = Query(None, description="Search term for title, content, or author"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
) -> ApiResponse[PaginatedForumPostResponse]:
    result = forum_service.get_posts_paginated(
        db=db,
        page=page,
        size=size,
        category_id=category_id,
        search=search,
        current_user=current_user,
    )
    return ApiResponse[PaginatedForumPostResponse](
        success=True,
        message="Discussion posts retrieved successfully",
        data=result,
    )


@router.post(
    "/posts",
    response_model=ApiResponse[ForumPostResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new discussion post (SKL-14 AC-2)",
)
def create_post(
    request: ForumPostCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[ForumPostResponse]:
    post = forum_service.create_post(db=db, current_user=current_user, request=request)
    return ApiResponse[ForumPostResponse](
        success=True,
        message="Discussion post created successfully",
        data=post,
    )


@router.get(
    "/posts/{id}",
    response_model=ApiResponse[ForumPostDetailResponse],
    status_code=status.HTTP_200_OK,
    summary="Get discussion post thread details and comments (SKL-14 AC-1, AC-3)",
)
def get_post_detail(
    id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
) -> ApiResponse[ForumPostDetailResponse]:
    post = forum_service.get_post_detail(db=db, post_id=id, current_user=current_user)
    return ApiResponse[ForumPostDetailResponse](
        success=True,
        message="Post detail retrieved successfully",
        data=post,
    )


@router.put(
    "/posts/{id}",
    response_model=ApiResponse[ForumPostResponse],
    status_code=status.HTTP_200_OK,
    summary="Edit own discussion post or moderate as Admin (SKL-14 AC-4, AC-7)",
)
def update_post(
    id: int,
    request: ForumPostUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[ForumPostResponse]:
    updated = forum_service.update_post(db=db, post_id=id, current_user=current_user, request=request)
    return ApiResponse[ForumPostResponse](
        success=True,
        message="Discussion post updated successfully",
        data=updated,
    )


@router.delete(
    "/posts/{id}",
    response_model=ApiResponse[None],
    status_code=status.HTTP_200_OK,
    summary="Delete own discussion post or moderate as Admin (SKL-14 AC-4, AC-7)",
)
def delete_post(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[None]:
    forum_service.delete_post(db=db, post_id=id, current_user=current_user)
    return ApiResponse[None](
        success=True,
        message="Discussion post deleted successfully",
        data=None,
    )


@router.post(
    "/posts/{id}/like",
    response_model=ApiResponse[ForumLikeToggleResponse],
    status_code=status.HTTP_200_OK,
    summary="Toggle like on a discussion post (SKL-14 AC-5)",
)
def toggle_post_like(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[ForumLikeToggleResponse]:
    result = forum_service.toggle_post_like(db=db, post_id=id, current_user=current_user)
    return ApiResponse[ForumLikeToggleResponse](
        success=True,
        message="Post like updated successfully",
        data=result,
    )


@router.post(
    "/posts/{id}/comments",
    response_model=ApiResponse[ForumCommentResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Add a comment to discussion post (SKL-14 AC-3)",
)
def add_comment(
    id: int,
    request: ForumCommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[ForumCommentResponse]:
    comment = forum_service.add_comment(db=db, post_id=id, current_user=current_user, request=request)
    return ApiResponse[ForumCommentResponse](
        success=True,
        message="Comment added successfully",
        data=comment,
    )


@router.put(
    "/comments/{id}",
    response_model=ApiResponse[ForumCommentResponse],
    status_code=status.HTTP_200_OK,
    summary="Edit own comment or moderate as Admin (SKL-14 AC-4, AC-7)",
)
def update_comment(
    id: int,
    request: ForumCommentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[ForumCommentResponse]:
    updated = forum_service.update_comment(db=db, comment_id=id, current_user=current_user, request=request)
    return ApiResponse[ForumCommentResponse](
        success=True,
        message="Comment updated successfully",
        data=updated,
    )


@router.delete(
    "/comments/{id}",
    response_model=ApiResponse[None],
    status_code=status.HTTP_200_OK,
    summary="Delete own comment or moderate as Admin (SKL-14 AC-4, AC-7)",
)
def delete_comment(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[None]:
    forum_service.delete_comment(db=db, comment_id=id, current_user=current_user)
    return ApiResponse[None](
        success=True,
        message="Comment deleted successfully",
        data=None,
    )


@router.post(
    "/comments/{id}/like",
    response_model=ApiResponse[ForumLikeToggleResponse],
    status_code=status.HTTP_200_OK,
    summary="Toggle like on a comment (SKL-14 AC-5)",
)
def toggle_comment_like(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[ForumLikeToggleResponse]:
    result = forum_service.toggle_comment_like(db=db, comment_id=id, current_user=current_user)
    return ApiResponse[ForumLikeToggleResponse](
        success=True,
        message="Comment like updated successfully",
        data=result,
    )


@router.post(
    "/reports",
    response_model=ApiResponse[ForumReportResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Report inappropriate post or comment (SKL-14 AC-6)",
)
def create_report(
    request: ForumReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[ForumReportResponse]:
    report = forum_service.create_report(db=db, current_user=current_user, request=request)
    return ApiResponse[ForumReportResponse](
        success=True,
        message="Report submitted successfully for admin review",
        data=report,
    )


@router.get(
    "/reports",
    response_model=ApiResponse[List[ForumReportResponse]],
    status_code=status.HTTP_200_OK,
    summary="Admin review of forum reports (SKL-14 AC-6)",
)
def get_reports(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    report_status: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
) -> ApiResponse[List[ForumReportResponse]]:
    reports, _ = forum_service.get_reports_for_admin(
        db=db, current_user=current_user, page=page, size=size, status=report_status
    )
    return ApiResponse[List[ForumReportResponse]](
        success=True,
        message="Forum reports retrieved successfully",
        data=reports,
    )


@router.patch(
    "/reports/{id}",
    response_model=ApiResponse[ForumReportResponse],
    status_code=status.HTTP_200_OK,
    summary="Admin update report status (SKL-14 AC-6)",
)
def update_report_status(
    id: int,
    request: ForumReportStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
) -> ApiResponse[ForumReportResponse]:
    updated = forum_service.update_report_status(
        db=db, report_id=id, current_user=current_user, new_status=request.status
    )
    return ApiResponse[ForumReportResponse](
        success=True,
        message="Report status updated successfully",
        data=updated,
    )
