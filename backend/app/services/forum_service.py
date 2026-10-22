import math
from datetime import datetime, timezone
from typing import Optional, List, Tuple, Set
from sqlalchemy.orm import Session
from app.core.exceptions import NotFoundException, ForbiddenException, BadRequestException
from app.models.forum import ForumCategory, ForumPost, ForumComment, ForumReport
from app.models.user import User, UserRole
from app.repositories.forum_repository import ForumRepository
from app.schemas.forum import (
    ForumCategoryResponse,
    ForumAuthorResponse,
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
)


class ForumService:
    """Service handling business logic, permissions, and moderation for Discussion Forum (SKL-14 & SKL-15)."""

    def __init__(self, repository: Optional[ForumRepository] = None):
        self.repo = repository or ForumRepository()

    def _build_author_response(self, user: Optional[User]) -> Optional[ForumAuthorResponse]:
        if not user:
            return None
        name = f"{user.first_name} {user.last_name}".strip()
        avatar = getattr(user, "avatar_url", None)
        designation = None
        institution = None
        if hasattr(user, "instructor_profile") and user.instructor_profile:
            designation = user.instructor_profile.designation
            institution = user.instructor_profile.institution

        return ForumAuthorResponse(
            id=user.id,
            name=name if name else user.email.split("@")[0],
            email=user.email,
            role=user.role,
            avatar_url=avatar,
            designation=designation,
            institution=institution,
        )

    def _build_post_response(
        self,
        post: ForumPost,
        liked_post_ids: Optional[Set[int]] = None,
    ) -> ForumPostResponse:
        is_liked = False
        if liked_post_ids is not None:
            is_liked = post.id in liked_post_ids

        category_name = post.category.name if post.category else "General"
        return ForumPostResponse(
            id=post.id,
            category_id=post.category_id,
            category_name=category_name,
            author=self._build_author_response(post.author),
            title=post.title,
            content=post.content,
            views_count=post.views_count,
            likes_count=post.likes_count,
            replies_count=post.replies_count,
            has_instructor_reply=post.has_instructor_reply,
            instructor_reply_name=post.instructor_reply_name,
            has_verified_answer=post.has_verified_answer,
            is_pinned=post.is_pinned,
            is_locked=post.is_locked,
            is_liked_by_me=is_liked,
            created_at=post.created_at,
            updated_at=post.updated_at,
        )

    def _build_comment_response(
        self,
        comment: ForumComment,
        liked_comment_ids: Optional[Set[int]] = None,
    ) -> ForumCommentResponse:
        is_liked = False
        if liked_comment_ids is not None:
            is_liked = comment.id in liked_comment_ids

        verified_by_author = None
        if comment.verified_by:
            verified_by_author = self._build_author_response(comment.verified_by)

        return ForumCommentResponse(
            id=comment.id,
            post_id=comment.post_id,
            author=self._build_author_response(comment.author),
            parent_id=comment.parent_id,
            content=comment.content,
            is_instructor_reply=comment.is_instructor_reply,
            is_verified=comment.is_verified,
            verified_by=verified_by_author,
            verified_at=comment.verified_at,
            likes_count=comment.likes_count,
            is_liked_by_me=is_liked,
            created_at=comment.created_at,
            updated_at=comment.updated_at,
        )

    def get_categories(self, db: Session) -> List[ForumCategoryResponse]:
        raw = self.repo.get_all_categories_with_counts(db)
        results = []
        for cat, cnt in raw:
            results.append(
                ForumCategoryResponse(
                    id=cat.id,
                    name=cat.name,
                    slug=cat.slug,
                    description=cat.description,
                    icon=cat.icon,
                    order_index=cat.order_index,
                    posts_count=cnt,
                )
            )
        return results

    def get_posts_paginated(
        self,
        db: Session,
        page: int = 1,
        size: int = 10,
        category_id: Optional[int] = None,
        search: Optional[str] = None,
        has_verified_answer: Optional[bool] = None,
        current_user: Optional[User] = None,
    ) -> PaginatedForumPostResponse:
        page = max(1, page)
        size = min(max(1, size), 100)

        posts, total = self.repo.get_posts_paginated(
            db=db,
            page=page,
            size=size,
            category_id=category_id,
            search=search,
            has_verified_answer=has_verified_answer,
        )

        liked_ids: Set[int] = set()
        if current_user:
            post_ids = [p.id for p in posts]
            liked_ids = self.repo.get_user_liked_post_ids(db, current_user.id, post_ids)

        items = [self._build_post_response(p, liked_ids) for p in posts]
        total_pages = math.ceil(total / size) if total > 0 else 1

        # Also compile category counts for UI badges
        raw_cats = self.repo.get_all_categories_with_counts(db)
        total_all = self.repo.get_total_posts_count(db)
        cat_counts = {"All": total_all}
        for cat, cnt in raw_cats:
            cat_counts[str(cat.id)] = cnt

        return PaginatedForumPostResponse(
            items=items,
            total=total,
            page=page,
            size=size,
            total_pages=total_pages,
            category_counts=cat_counts,
        )

    def get_post_detail(
        self,
        db: Session,
        post_id: int,
        current_user: Optional[User] = None,
        increment_views: bool = True,
    ) -> ForumPostDetailResponse:
        post = self.repo.get_post_by_id(db, post_id)
        if not post:
            raise NotFoundException("Discussion post not found")

        if increment_views:
            self.repo.increment_views(db, post)

        # Get post like status
        is_post_liked = False
        liked_comment_ids: Set[int] = set()
        if current_user:
            like_stmt = self.repo.get_post_like(db, current_user.id, post.id)
            is_post_liked = like_stmt is not None

            # Get comments
            comments = self.repo.get_comments_by_post(db, post_id)
            c_ids = [c.id for c in comments]
            liked_comment_ids = self.repo.get_user_liked_comment_ids(db, current_user.id, c_ids)
        else:
            comments = self.repo.get_comments_by_post(db, post_id)

        comment_responses = [
            self._build_comment_response(c, liked_comment_ids) for c in comments
        ]

        category_name = post.category.name if post.category else "General"
        return ForumPostDetailResponse(
            id=post.id,
            category_id=post.category_id,
            category_name=category_name,
            author=self._build_author_response(post.author),
            title=post.title,
            content=post.content,
            views_count=post.views_count,
            likes_count=post.likes_count,
            replies_count=post.replies_count,
            has_instructor_reply=post.has_instructor_reply,
            instructor_reply_name=post.instructor_reply_name,
            has_verified_answer=post.has_verified_answer,
            is_pinned=post.is_pinned,
            is_locked=post.is_locked,
            is_liked_by_me=is_post_liked,
            created_at=post.created_at,
            updated_at=post.updated_at,
            comments=comment_responses,
        )

    def create_post(
        self,
        db: Session,
        current_user: User,
        request: ForumPostCreate,
    ) -> ForumPostResponse:
        category = self.repo.get_category_by_id(db, request.category_id)
        if not category:
            raise NotFoundException("Forum category not found")

        post = ForumPost(
            category_id=request.category_id,
            author_id=current_user.id,
            title=request.title.strip(),
            content=request.content.strip(),
        )
        created = self.repo.create_post(db, post)
        return self._build_post_response(created)

    def update_post(
        self,
        db: Session,
        post_id: int,
        current_user: User,
        request: ForumPostUpdate,
    ) -> ForumPostResponse:
        post = self.repo.get_post_by_id(db, post_id)
        if not post:
            raise NotFoundException("Discussion post not found")

        # AC-4 & AC-7: Only author or admin can edit
        if post.author_id != current_user.id and current_user.role != UserRole.ADMIN:
            raise ForbiddenException(
                "You do not have permission to modify this post",
                error_code="FORBIDDEN_ACTION",
            )

        if request.category_id is not None:
            cat = self.repo.get_category_by_id(db, request.category_id)
            if not cat:
                raise NotFoundException("Forum category not found")
            post.category_id = request.category_id

        if request.title is not None and request.title.strip():
            post.title = request.title.strip()

        if request.content is not None and request.content.strip():
            post.content = request.content.strip()

        updated = self.repo.update_post(db, post)
        return self._build_post_response(updated)

    def delete_post(
        self,
        db: Session,
        post_id: int,
        current_user: User,
    ) -> None:
        post = self.repo.get_post_by_id(db, post_id)
        if not post:
            raise NotFoundException("Discussion post not found")

        # AC-4 & AC-7: Only author or admin can delete
        if post.author_id != current_user.id and current_user.role != UserRole.ADMIN:
            raise ForbiddenException(
                "You do not have permission to delete this post",
                error_code="FORBIDDEN_ACTION",
            )

        self.repo.delete_post(db, post)

    def add_comment(
        self,
        db: Session,
        post_id: int,
        current_user: User,
        request: ForumCommentCreate,
    ) -> ForumCommentResponse:
        post = self.repo.get_post_by_id(db, post_id)
        if not post:
            raise NotFoundException("Discussion post not found")

        if post.is_locked:
            raise ForbiddenException("This discussion is locked and replies are closed.")

        if request.parent_id is not None:
            parent = self.repo.get_comment_by_id(db, request.parent_id)
            if not parent or parent.post_id != post_id:
                raise NotFoundException("Parent comment not found in this post thread")

        # AC-3: Check if comment author is Instructor
        is_instructor = (current_user.role == UserRole.INSTRUCTOR)
        is_verified = False
        verified_by_id = None
        verified_at = None

        if request.mark_as_verified:
            # AC-5: Given a user without Instructor or Admin permission, when they attempt to create or mark a verified answer, then the system shall reject the request.
            if current_user.role not in [UserRole.INSTRUCTOR, UserRole.ADMIN]:
                raise ForbiddenException(
                    "Only verified instructors and administrators can create or mark verified answers",
                    error_code="FORBIDDEN_ACTION",
                )
            is_verified = True
            verified_by_id = current_user.id
            verified_at = datetime.now(timezone.utc)

        comment = ForumComment(
            post_id=post_id,
            author_id=current_user.id,
            parent_id=request.parent_id,
            content=request.content.strip(),
            is_instructor_reply=is_instructor,
            is_verified=is_verified,
            verified_by_id=verified_by_id,
            verified_at=verified_at,
        )
        created = self.repo.create_comment(db, comment)
        return self._build_comment_response(created)

    def verify_comment(
        self,
        db: Session,
        comment_id: int,
        current_user: User,
        is_verified: bool = True,
    ) -> ForumCommentResponse:
        """Mark or unmark a comment as verified (SKL-15 AC-2, AC-5)."""
        # AC-5: Given a user without Instructor or Admin permission, when they attempt to create or mark a verified answer, then the system shall reject the request.
        if current_user.role not in [UserRole.INSTRUCTOR, UserRole.ADMIN]:
            raise ForbiddenException(
                "Only verified instructors and administrators can mark answers as verified",
                error_code="FORBIDDEN_ACTION",
            )

        comment = self.repo.get_comment_by_id(db, comment_id)
        if not comment:
            raise NotFoundException("Comment not found")

        updated = self.repo.verify_comment(
            db=db,
            comment=comment,
            verifier=current_user,
            is_verified=is_verified,
        )

        # Event-driven Notification for comment author (SKL-17 AC-1)
        if is_verified and comment.author_id and comment.author_id != current_user.id:
            try:
                from app.models.notification import Notification
                post_title = comment.post.title if comment.post else "Discussion"
                notif = Notification(
                    recipient_id=comment.author_id,
                    event_type="FORUM_VERIFIED_ANSWER",
                    title="Answer Verified by Instructor",
                    message=f"Your answer on discussion post '{post_title}' has been verified by an instructor!",
                    link_url=f"/forum/{comment.post_id}",
                    is_read=False,
                    email_sent=False,
                )
                db.add(notif)
                db.commit()
            except Exception as notif_err:
                pass

        return self._build_comment_response(updated)

    def update_comment(
        self,
        db: Session,
        comment_id: int,
        current_user: User,
        request: ForumCommentUpdate,
    ) -> ForumCommentResponse:
        comment = self.repo.get_comment_by_id(db, comment_id)
        if not comment:
            raise NotFoundException("Comment not found")

        # AC-4 & AC-7: Only author or admin can edit
        if comment.author_id != current_user.id and current_user.role != UserRole.ADMIN:
            raise ForbiddenException(
                "You do not have permission to modify this comment",
                error_code="FORBIDDEN_ACTION",
            )

        comment.content = request.content.strip()
        updated = self.repo.update_comment(db, comment)
        return self._build_comment_response(updated)

    def delete_comment(
        self,
        db: Session,
        comment_id: int,
        current_user: User,
    ) -> None:
        comment = self.repo.get_comment_by_id(db, comment_id)
        if not comment:
            raise NotFoundException("Comment not found")

        # AC-4 & AC-7: Only author or admin can delete
        if comment.author_id != current_user.id and current_user.role != UserRole.ADMIN:
            raise ForbiddenException(
                "You do not have permission to delete this comment",
                error_code="FORBIDDEN_ACTION",
            )

        self.repo.delete_comment(db, comment)

    def toggle_post_like(
        self,
        db: Session,
        post_id: int,
        current_user: User,
    ) -> ForumLikeToggleResponse:
        post = self.repo.get_post_by_id(db, post_id)
        if not post:
            raise NotFoundException("Discussion post not found")

        is_liked, count = self.repo.toggle_post_like(db, current_user.id, post_id)
        return ForumLikeToggleResponse(is_liked=is_liked, likes_count=count)

    def toggle_comment_like(
        self,
        db: Session,
        comment_id: int,
        current_user: User,
    ) -> ForumLikeToggleResponse:
        comment = self.repo.get_comment_by_id(db, comment_id)
        if not comment:
            raise NotFoundException("Comment not found")

        is_liked, count = self.repo.toggle_comment_like(db, current_user.id, comment_id)
        return ForumLikeToggleResponse(is_liked=is_liked, likes_count=count)

    def create_report(
        self,
        db: Session,
        current_user: User,
        request: ForumReportCreate,
    ) -> ForumReportResponse:
        if not request.post_id and not request.comment_id:
            raise BadRequestException("Either post_id or comment_id must be provided to submit a report")

        if request.post_id:
            post = self.repo.get_post_by_id(db, request.post_id)
            if not post:
                raise NotFoundException("Target post not found")

        if request.comment_id:
            comment = self.repo.get_comment_by_id(db, request.comment_id)
            if not comment:
                raise NotFoundException("Target comment not found")

        report = ForumReport(
            reporter_id=current_user.id,
            post_id=request.post_id,
            comment_id=request.comment_id,
            reason=request.reason.strip(),
            details=request.details.strip() if request.details else None,
            status="PENDING",
        )
        created = self.repo.create_report(db, report)
        return ForumReportResponse(
            id=created.id,
            reporter=self._build_author_response(current_user),
            post_id=created.post_id,
            comment_id=created.comment_id,
            reason=created.reason,
            details=created.details,
            status=created.status,
            created_at=created.created_at,
        )

    def get_reports_for_admin(
        self,
        db: Session,
        current_user: User,
        page: int = 1,
        size: int = 20,
        status: Optional[str] = None,
    ) -> Tuple[List[ForumReportResponse], int]:
        if current_user.role != UserRole.ADMIN:
            raise ForbiddenException("Only administrators can review reports")

        reports, total = self.repo.get_reports_paginated(db, page=page, size=size, status=status)
        results = [
            ForumReportResponse(
                id=r.id,
                reporter=self._build_author_response(r.reporter),
                post_id=r.post_id,
                comment_id=r.comment_id,
                reason=r.reason,
                details=r.details,
                status=r.status,
                created_at=r.created_at,
            )
            for r in reports
        ]
        return results, total

    def update_report_status(
        self,
        db: Session,
        report_id: int,
        current_user: User,
        new_status: str,
    ) -> ForumReportResponse:
        if current_user.role != UserRole.ADMIN:
            raise ForbiddenException("Only administrators can update report status")

        report = self.repo.get_report_by_id(db, report_id)
        if not report:
            raise NotFoundException("Report not found")

        updated = self.repo.update_report_status(db, report, new_status)
        return ForumReportResponse(
            id=updated.id,
            reporter=self._build_author_response(updated.reporter),
            post_id=updated.post_id,
            comment_id=updated.comment_id,
            reason=updated.reason,
            details=updated.details,
            status=updated.status,
            created_at=updated.created_at,
        )
