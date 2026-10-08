from typing import Optional, List, Tuple, Set
from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session, joinedload
from app.models.forum import ForumCategory, ForumPost, ForumComment, ForumLike, ForumReport
from app.models.user import User, UserRole


class ForumRepository:
    """Repository managing database persistence for Forum entities (SKL-14)."""

    @staticmethod
    def create_category(db: Session, category: ForumCategory) -> ForumCategory:
        db.add(category)
        db.commit()
        db.refresh(category)
        return category

    @staticmethod
    def get_category_by_id(db: Session, category_id: int) -> Optional[ForumCategory]:
        return db.get(ForumCategory, category_id)

    @staticmethod
    def get_category_by_slug(db: Session, slug: str) -> Optional[ForumCategory]:
        stmt = select(ForumCategory).where(ForumCategory.slug == slug)
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def get_all_categories_with_counts(db: Session) -> List[Tuple[ForumCategory, int]]:
        subq = (
            select(ForumPost.category_id, func.count(ForumPost.id).label("cnt"))
            .group_by(ForumPost.category_id)
            .subquery()
        )
        stmt = (
            select(ForumCategory, func.coalesce(subq.c.cnt, 0))
            .outerjoin(subq, ForumCategory.id == subq.c.category_id)
            .order_by(ForumCategory.order_index.asc(), ForumCategory.name.asc())
        )
        return list(db.execute(stmt).all())

    @staticmethod
    def get_total_posts_count(db: Session) -> int:
        stmt = select(func.count(ForumPost.id))
        return db.execute(stmt).scalar() or 0

    @staticmethod
    def create_post(db: Session, post: ForumPost) -> ForumPost:
        db.add(post)
        db.commit()
        db.refresh(post)
        return post

    @staticmethod
    def get_post_by_id(db: Session, post_id: int) -> Optional[ForumPost]:
        stmt = (
            select(ForumPost)
            .options(
                joinedload(ForumPost.author),
                joinedload(ForumPost.category),
            )
            .where(ForumPost.id == post_id)
        )
        return db.execute(stmt).unique().scalar_one_or_none()

    @staticmethod
    def update_post(db: Session, post: ForumPost) -> ForumPost:
        db.commit()
        db.refresh(post)
        return post

    @staticmethod
    def delete_post(db: Session, post: ForumPost) -> None:
        db.delete(post)
        db.commit()

    @staticmethod
    def increment_views(db: Session, post: ForumPost) -> None:
        post.views_count += 1
        db.commit()

    @staticmethod
    def get_posts_paginated(
        db: Session,
        page: int = 1,
        size: int = 10,
        category_id: Optional[int] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[ForumPost], int]:
        base_stmt = select(ForumPost).options(
            joinedload(ForumPost.author),
            joinedload(ForumPost.category),
        )

        filters = []
        if category_id is not None:
            filters.append(ForumPost.category_id == category_id)

        if search and search.strip():
            term = f"%{search.strip()}%"
            # Match in post title, content, or author's name
            base_stmt = base_stmt.join(ForumPost.author)
            filters.append(
                or_(
                    ForumPost.title.ilike(term),
                    ForumPost.content.ilike(term),
                    User.first_name.ilike(term),
                    User.last_name.ilike(term),
                )
            )

        if filters:
            base_stmt = base_stmt.where(*filters)

        # Count total matching
        count_stmt = select(func.count(ForumPost.id))
        if search and search.strip():
            count_stmt = count_stmt.join(ForumPost.author)
        if filters:
            count_stmt = count_stmt.where(*filters)
        total = db.execute(count_stmt).scalar() or 0

        # Order by pinned first, then newest
        stmt = (
            base_stmt.order_by(ForumPost.is_pinned.desc(), ForumPost.created_at.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        items = list(db.execute(stmt).unique().scalars().all())
        return items, total

    @staticmethod
    def create_comment(db: Session, comment: ForumComment) -> ForumComment:
        db.add(comment)
        db.commit()
        db.refresh(comment)

        # Update post replies_count
        post = db.get(ForumPost, comment.post_id)
        if post:
            post.replies_count += 1
            if comment.is_instructor_reply:
                post.has_instructor_reply = True
                if comment.author:
                    author_name = f"{comment.author.first_name} {comment.author.last_name}".strip()
                    post.instructor_reply_name = author_name
            db.commit()
            db.refresh(post)

        return comment

    @staticmethod
    def get_comment_by_id(db: Session, comment_id: int) -> Optional[ForumComment]:
        stmt = (
            select(ForumComment)
            .options(joinedload(ForumComment.author))
            .where(ForumComment.id == comment_id)
        )
        return db.execute(stmt).unique().scalar_one_or_none()

    @staticmethod
    def get_comments_by_post(db: Session, post_id: int) -> List[ForumComment]:
        stmt = (
            select(ForumComment)
            .options(joinedload(ForumComment.author))
            .where(ForumComment.post_id == post_id)
            .order_by(ForumComment.created_at.asc())
        )
        return list(db.execute(stmt).unique().scalars().all())

    @staticmethod
    def update_comment(db: Session, comment: ForumComment) -> ForumComment:
        db.commit()
        db.refresh(comment)
        return comment

    @staticmethod
    def delete_comment(db: Session, comment: ForumComment) -> None:
        post_id = comment.post_id
        db.delete(comment)
        db.commit()

        # Recalculate post reply count and instructor reply flag
        post = db.get(ForumPost, post_id)
        if post:
            cnt_stmt = select(func.count(ForumComment.id)).where(ForumComment.post_id == post_id)
            post.replies_count = db.execute(cnt_stmt).scalar() or 0

            # Check if any instructor replies remain
            inst_stmt = (
                select(ForumComment)
                .options(joinedload(ForumComment.author))
                .where(ForumComment.post_id == post_id, ForumComment.is_instructor_reply.is_(True))
                .limit(1)
            )
            first_inst = db.execute(inst_stmt).unique().scalar_one_or_none()
            if first_inst:
                post.has_instructor_reply = True
                post.instructor_reply_name = f"{first_inst.author.first_name} {first_inst.author.last_name}".strip()
            else:
                post.has_instructor_reply = False
                post.instructor_reply_name = None

            db.commit()

    @staticmethod
    def get_post_like(db: Session, user_id: int, post_id: int) -> Optional[ForumLike]:
        stmt = select(ForumLike).where(ForumLike.user_id == user_id, ForumLike.post_id == post_id)
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def get_comment_like(db: Session, user_id: int, comment_id: int) -> Optional[ForumLike]:
        stmt = select(ForumLike).where(ForumLike.user_id == user_id, ForumLike.comment_id == comment_id)
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def toggle_post_like(db: Session, user_id: int, post_id: int) -> Tuple[bool, int]:
        post = db.get(ForumPost, post_id)
        if not post:
            return False, 0

        stmt = select(ForumLike).where(ForumLike.user_id == user_id, ForumLike.post_id == post_id)
        existing_like = db.execute(stmt).scalar_one_or_none()

        if existing_like:
            db.delete(existing_like)
            post.likes_count = max(0, post.likes_count - 1)
            is_liked = False
        else:
            new_like = ForumLike(user_id=user_id, post_id=post_id)
            db.add(new_like)
            post.likes_count += 1
            is_liked = True

        db.commit()
        db.refresh(post)
        return is_liked, post.likes_count

    @staticmethod
    def toggle_comment_like(db: Session, user_id: int, comment_id: int) -> Tuple[bool, int]:
        comment = db.get(ForumComment, comment_id)
        if not comment:
            return False, 0

        stmt = select(ForumLike).where(ForumLike.user_id == user_id, ForumLike.comment_id == comment_id)
        existing_like = db.execute(stmt).scalar_one_or_none()

        if existing_like:
            db.delete(existing_like)
            comment.likes_count = max(0, comment.likes_count - 1)
            is_liked = False
        else:
            new_like = ForumLike(user_id=user_id, comment_id=comment_id)
            db.add(new_like)
            comment.likes_count += 1
            is_liked = True

        db.commit()
        db.refresh(comment)
        return is_liked, comment.likes_count

    @staticmethod
    def get_user_liked_post_ids(db: Session, user_id: int, post_ids: List[int]) -> Set[int]:
        if not post_ids:
            return set()
        stmt = select(ForumLike.post_id).where(
            ForumLike.user_id == user_id,
            ForumLike.post_id.in_(post_ids)
        )
        return set(db.execute(stmt).scalars().all())

    @staticmethod
    def get_user_liked_comment_ids(db: Session, user_id: int, comment_ids: List[int]) -> Set[int]:
        if not comment_ids:
            return set()
        stmt = select(ForumLike.comment_id).where(
            ForumLike.user_id == user_id,
            ForumLike.comment_id.in_(comment_ids)
        )
        return set(db.execute(stmt).scalars().all())

    @staticmethod
    def create_report(db: Session, report: ForumReport) -> ForumReport:
        db.add(report)
        db.commit()
        db.refresh(report)
        return report

    @staticmethod
    def get_reports_paginated(
        db: Session,
        page: int = 1,
        size: int = 20,
        status: Optional[str] = None
    ) -> Tuple[List[ForumReport], int]:
        stmt = select(ForumReport).options(joinedload(ForumReport.reporter))
        if status:
            stmt = stmt.where(ForumReport.status == status)

        count_stmt = select(func.count(ForumReport.id))
        if status:
            count_stmt = count_stmt.where(ForumReport.status == status)
        total = db.execute(count_stmt).scalar() or 0

        stmt = stmt.order_by(ForumReport.created_at.desc()).offset((page - 1) * size).limit(size)
        items = list(db.execute(stmt).unique().scalars().all())
        return items, total

    @staticmethod
    def get_report_by_id(db: Session, report_id: int) -> Optional[ForumReport]:
        stmt = (
            select(ForumReport)
            .options(joinedload(ForumReport.reporter))
            .where(ForumReport.id == report_id)
        )
        return db.execute(stmt).unique().scalar_one_or_none()

    @staticmethod
    def update_report_status(db: Session, report: ForumReport, new_status: str) -> ForumReport:
        report.status = new_status
        db.commit()
        db.refresh(report)
        return report
