"""Add instructor verified answers fields to forum_comments and forum_posts for SKL-15

Revision ID: 20261016_0018
Revises: 20261016_0017
Create Date: 2026-10-16 02:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "20261016_0018"
down_revision: Union[str, None] = "20261016_0017"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_exists(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    return any(c["name"] == column_name for c in insp.get_columns(table_name))


def _index_exists(table_name: str, index_name: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    return any(ix["name"] == index_name for ix in insp.get_indexes(table_name))


def _foreign_key_exists(table_name: str, fk_name: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    return any(fk["name"] == fk_name for fk in insp.get_foreign_keys(table_name))


def upgrade() -> None:
    # 1. Add has_verified_answer to forum_posts
    if not _column_exists("forum_posts", "has_verified_answer"):
        op.add_column(
            "forum_posts",
            sa.Column("has_verified_answer", sa.Boolean(), server_default=sa.text("0"), nullable=False),
        )
    if not _index_exists("forum_posts", "ix_forum_posts_has_verified_answer"):
        op.create_index("ix_forum_posts_has_verified_answer", "forum_posts", ["has_verified_answer"])

    # 2. Add verified fields to forum_comments
    if not _column_exists("forum_comments", "is_verified"):
        op.add_column(
            "forum_comments",
            sa.Column("is_verified", sa.Boolean(), server_default=sa.text("0"), nullable=False),
        )
    if not _column_exists("forum_comments", "verified_by_id"):
        op.add_column(
            "forum_comments",
            sa.Column("verified_by_id", sa.Integer(), nullable=True),
        )
    if not _column_exists("forum_comments", "verified_at"):
        op.add_column(
            "forum_comments",
            sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        )

    if not _index_exists("forum_comments", "ix_forum_comments_is_verified"):
        op.create_index("ix_forum_comments_is_verified", "forum_comments", ["is_verified"])

    if not _foreign_key_exists("forum_comments", "fk_forum_comments_verified_by_id_users"):
        op.create_foreign_key(
            "fk_forum_comments_verified_by_id_users",
            "forum_comments",
            "users",
            ["verified_by_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    if _foreign_key_exists("forum_comments", "fk_forum_comments_verified_by_id_users"):
        op.drop_constraint("fk_forum_comments_verified_by_id_users", "forum_comments", type_="foreignkey")
    if _index_exists("forum_comments", "ix_forum_comments_is_verified"):
        op.drop_index("ix_forum_comments_is_verified", table_name="forum_comments")
    if _column_exists("forum_comments", "verified_at"):
        op.drop_column("forum_comments", "verified_at")
    if _column_exists("forum_comments", "verified_by_id"):
        op.drop_column("forum_comments", "verified_by_id")
    if _column_exists("forum_comments", "is_verified"):
        op.drop_column("forum_comments", "is_verified")

    if _index_exists("forum_posts", "ix_forum_posts_has_verified_answer"):
        op.drop_index("ix_forum_posts_has_verified_answer", table_name="forum_posts")
    if _column_exists("forum_posts", "has_verified_answer"):
        op.drop_column("forum_posts", "has_verified_answer")
