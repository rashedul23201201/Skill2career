"""Create forum tables for Discussion Forum (SKL-14)

Revision ID: 20261009_0008
Revises: 20261009_0007
Create Date: 2026-10-09 03:20:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "20261009_0008"
down_revision: Union[str, None] = "20261009_0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. forum_categories
    op.create_table(
        "forum_categories",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("icon", sa.String(length=50), nullable=True),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index("ix_forum_categories_id", "forum_categories", ["id"], unique=False)
    op.create_index("ix_forum_categories_name", "forum_categories", ["name"], unique=False)
    op.create_index("ix_forum_categories_slug", "forum_categories", ["slug"], unique=False)

    # 2. forum_posts
    op.create_table(
        "forum_posts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("author_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("views_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("likes_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("replies_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("has_instructor_reply", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("instructor_reply_name", sa.String(length=150), nullable=True),
        sa.Column("is_pinned", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_locked", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["category_id"], ["forum_categories.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_forum_posts_id", "forum_posts", ["id"], unique=False)
    op.create_index("ix_forum_posts_category_id", "forum_posts", ["category_id"], unique=False)
    op.create_index("ix_forum_posts_author_id", "forum_posts", ["author_id"], unique=False)
    op.create_index("ix_forum_posts_title", "forum_posts", ["title"], unique=False)
    op.create_index("ix_forum_posts_has_instructor_reply", "forum_posts", ["has_instructor_reply"], unique=False)

    # 3. forum_comments
    op.create_table(
        "forum_comments",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("post_id", sa.Integer(), nullable=False),
        sa.Column("author_id", sa.Integer(), nullable=False),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("is_instructor_reply", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("likes_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["post_id"], ["forum_posts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["parent_id"], ["forum_comments.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_forum_comments_id", "forum_comments", ["id"], unique=False)
    op.create_index("ix_forum_comments_post_id", "forum_comments", ["post_id"], unique=False)
    op.create_index("ix_forum_comments_author_id", "forum_comments", ["author_id"], unique=False)
    op.create_index("ix_forum_comments_parent_id", "forum_comments", ["parent_id"], unique=False)

    # 4. forum_likes
    op.create_table(
        "forum_likes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("post_id", sa.Integer(), nullable=True),
        sa.Column("comment_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["post_id"], ["forum_posts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["comment_id"], ["forum_comments.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_forum_likes_id", "forum_likes", ["id"], unique=False)
    op.create_index("ix_forum_likes_user_id", "forum_likes", ["user_id"], unique=False)
    op.create_index("ix_forum_likes_post_id", "forum_likes", ["post_id"], unique=False)
    op.create_index("ix_forum_likes_comment_id", "forum_likes", ["comment_id"], unique=False)
    op.create_index("idx_user_post_like", "forum_likes", ["user_id", "post_id"], unique=False)
    op.create_index("idx_user_comment_like", "forum_likes", ["user_id", "comment_id"], unique=False)

    # 5. forum_reports
    op.create_table(
        "forum_reports",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("reporter_id", sa.Integer(), nullable=False),
        sa.Column("post_id", sa.Integer(), nullable=True),
        sa.Column("comment_id", sa.Integer(), nullable=True),
        sa.Column("reason", sa.String(length=100), nullable=False),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="PENDING"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["reporter_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["post_id"], ["forum_posts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["comment_id"], ["forum_comments.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_forum_reports_id", "forum_reports", ["id"], unique=False)
    op.create_index("ix_forum_reports_reporter_id", "forum_reports", ["reporter_id"], unique=False)
    op.create_index("ix_forum_reports_post_id", "forum_reports", ["post_id"], unique=False)
    op.create_index("ix_forum_reports_comment_id", "forum_reports", ["comment_id"], unique=False)
    op.create_index("ix_forum_reports_status", "forum_reports", ["status"], unique=False)


def downgrade() -> None:
    op.drop_table("forum_reports")
    op.drop_table("forum_likes")
    op.drop_table("forum_comments")
    op.drop_table("forum_posts")
    op.drop_table("forum_categories")
