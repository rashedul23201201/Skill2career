"""Create content moderation tables and columns for SKL-25

Revision ID: 20261016_0016
Revises: 20261016_0015
Create Date: 2026-10-16 00:16:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "20261016_0016"
down_revision: Union[str, None] = "20261016_0015"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_exists(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    return any(c["name"] == column_name for c in insp.get_columns(table_name))


def _table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    return table_name in insp.get_table_names()


def upgrade() -> None:
    # 1. Add moderation columns to courses
    if not _column_exists("courses", "moderation_status"):
        op.add_column("courses", sa.Column("moderation_status", sa.String(length=50), server_default="APPROVED", nullable=False))
        op.create_index(op.f("ix_courses_moderation_status"), "courses", ["moderation_status"], unique=False)
    if not _column_exists("courses", "moderated_by"):
        op.add_column("courses", sa.Column("moderated_by", sa.Integer(), nullable=True))
        op.create_foreign_key("fk_courses_moderated_by_users", "courses", "users", ["moderated_by"], ["id"], ondelete="SET NULL")
    if not _column_exists("courses", "moderation_notes"):
        op.add_column("courses", sa.Column("moderation_notes", sa.Text(), nullable=True))
    if not _column_exists("courses", "moderated_at"):
        op.add_column("courses", sa.Column("moderated_at", sa.DateTime(timezone=True), nullable=True))

    # 2. Add moderation columns to lessons
    if not _column_exists("lessons", "moderation_status"):
        op.add_column("lessons", sa.Column("moderation_status", sa.String(length=50), server_default="APPROVED", nullable=False))
    if not _column_exists("lessons", "moderated_by"):
        op.add_column("lessons", sa.Column("moderated_by", sa.Integer(), nullable=True))
        op.create_foreign_key("fk_lessons_moderated_by_users", "lessons", "users", ["moderated_by"], ["id"], ondelete="SET NULL")
    if not _column_exists("lessons", "moderation_notes"):
        op.add_column("lessons", sa.Column("moderation_notes", sa.Text(), nullable=True))
    if not _column_exists("lessons", "moderated_at"):
        op.add_column("lessons", sa.Column("moderated_at", sa.DateTime(timezone=True), nullable=True))

    # 3. Add moderation columns to mock_tests
    if not _column_exists("mock_tests", "moderation_status"):
        op.add_column("mock_tests", sa.Column("moderation_status", sa.String(length=50), server_default="APPROVED", nullable=False))
        op.create_index(op.f("ix_mock_tests_moderation_status"), "mock_tests", ["moderation_status"], unique=False)
    if not _column_exists("mock_tests", "moderated_by"):
        op.add_column("mock_tests", sa.Column("moderated_by", sa.Integer(), nullable=True))
        op.create_foreign_key("fk_mock_tests_moderated_by_users", "mock_tests", "users", ["moderated_by"], ["id"], ondelete="SET NULL")
    if not _column_exists("mock_tests", "moderation_notes"):
        op.add_column("mock_tests", sa.Column("moderation_notes", sa.Text(), nullable=True))
    if not _column_exists("mock_tests", "moderated_at"):
        op.add_column("mock_tests", sa.Column("moderated_at", sa.DateTime(timezone=True), nullable=True))

    # 4. Create content_moderation_logs table
    if not _table_exists("content_moderation_logs"):
        op.create_table(
            "content_moderation_logs",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("content_type", sa.String(length=50), nullable=False),
            sa.Column("content_id", sa.Integer(), nullable=False),
            sa.Column("admin_id", sa.Integer(), nullable=True),
            sa.Column("action", sa.String(length=50), nullable=False),
            sa.Column("reason", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["admin_id"], ["users.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_content_moderation_logs_id"), "content_moderation_logs", ["id"], unique=False)
        op.create_index(op.f("ix_content_moderation_logs_content_type"), "content_moderation_logs", ["content_type"], unique=False)
        op.create_index(op.f("ix_content_moderation_logs_content_id"), "content_moderation_logs", ["content_id"], unique=False)
        op.create_index(op.f("ix_content_moderation_logs_admin_id"), "content_moderation_logs", ["admin_id"], unique=False)
        op.create_index(op.f("ix_content_moderation_logs_action"), "content_moderation_logs", ["action"], unique=False)
        op.create_index(op.f("ix_content_moderation_logs_created_at"), "content_moderation_logs", ["created_at"], unique=False)


def downgrade() -> None:
    # 1. Drop content_moderation_logs
    op.drop_index(op.f("ix_content_moderation_logs_created_at"), table_name="content_moderation_logs")
    op.drop_index(op.f("ix_content_moderation_logs_action"), table_name="content_moderation_logs")
    op.drop_index(op.f("ix_content_moderation_logs_admin_id"), table_name="content_moderation_logs")
    op.drop_index(op.f("ix_content_moderation_logs_content_id"), table_name="content_moderation_logs")
    op.drop_index(op.f("ix_content_moderation_logs_content_type"), table_name="content_moderation_logs")
    op.drop_index(op.f("ix_content_moderation_logs_id"), table_name="content_moderation_logs")
    op.drop_table("content_moderation_logs")

    # 2. Drop mock_tests columns
    op.drop_constraint("fk_mock_tests_moderated_by_users", "mock_tests", type_="foreignkey")
    op.drop_index(op.f("ix_mock_tests_moderation_status"), table_name="mock_tests")
    op.drop_column("mock_tests", "moderated_at")
    op.drop_column("mock_tests", "moderation_notes")
    op.drop_column("mock_tests", "moderated_by")
    op.drop_column("mock_tests", "moderation_status")

    # 3. Drop lessons columns
    op.drop_constraint("fk_lessons_moderated_by_users", "lessons", type_="foreignkey")
    op.drop_column("lessons", "moderated_at")
    op.drop_column("lessons", "moderation_notes")
    op.drop_column("lessons", "moderated_by")
    op.drop_column("lessons", "moderation_status")

    # 4. Drop courses columns
    op.drop_constraint("fk_courses_moderated_by_users", "courses", type_="foreignkey")
    op.drop_index(op.f("ix_courses_moderation_status"), table_name="courses")
    op.drop_column("courses", "moderated_at")
    op.drop_column("courses", "moderation_notes")
    op.drop_column("courses", "moderated_by")
    op.drop_column("courses", "moderation_status")
