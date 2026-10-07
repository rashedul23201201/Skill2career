"""Create courses, course_modules, and lessons tables for LMS Module (SKL-53)

Revision ID: 20261007_0004
Revises: 20261003_0003
Create Date: 2026-10-07 18:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20261007_0004"
down_revision: Union[str, None] = "20261003_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create courses table
    op.create_table(
        "courses",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("instructor_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.Column("level", sa.String(length=50), nullable=False, server_default="Beginner"),
        sa.Column("price", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("is_free", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="DRAFT"),
        sa.Column("thumbnail_url", sa.String(length=255), nullable=True),
        sa.Column("duration_weeks", sa.Integer(), nullable=False, server_default="8"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["instructor_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_courses_id"), "courses", ["id"], unique=False)
    op.create_index(op.f("ix_courses_instructor_id"), "courses", ["instructor_id"], unique=False)
    op.create_index(op.f("ix_courses_title"), "courses", ["title"], unique=False)
    op.create_index(op.f("ix_courses_category"), "courses", ["category"], unique=False)
    op.create_index(op.f("ix_courses_status"), "courses", ["status"], unique=False)

    # 2. Create course_modules table
    op.create_table(
        "course_modules",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("course_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_course_modules_id"), "course_modules", ["id"], unique=False)
    op.create_index(op.f("ix_course_modules_course_id"), "course_modules", ["course_id"], unique=False)

    # 3. Create lessons table
    op.create_table(
        "lessons",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("course_id", sa.Integer(), nullable=False),
        sa.Column("module_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("content_type", sa.String(length=50), nullable=False, server_default="video"),
        sa.Column("video_url", sa.String(length=500), nullable=True),
        sa.Column("study_material_url", sa.String(length=500), nullable=True),
        sa.Column("attachments", sa.JSON(), nullable=True),
        sa.Column("duration_minutes", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["module_id"], ["course_modules.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_lessons_id"), "lessons", ["id"], unique=False)
    op.create_index(op.f("ix_lessons_course_id"), "lessons", ["course_id"], unique=False)
    op.create_index(op.f("ix_lessons_module_id"), "lessons", ["module_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_lessons_module_id"), table_name="lessons")
    op.drop_index(op.f("ix_lessons_course_id"), table_name="lessons")
    op.drop_index(op.f("ix_lessons_id"), table_name="lessons")
    op.drop_table("lessons")

    op.drop_index(op.f("ix_course_modules_course_id"), table_name="course_modules")
    op.drop_index(op.f("ix_course_modules_id"), table_name="course_modules")
    op.drop_table("course_modules")

    op.drop_index(op.f("ix_courses_status"), table_name="courses")
    op.drop_index(op.f("ix_courses_category"), table_name="courses")
    op.drop_index(op.f("ix_courses_title"), table_name="courses")
    op.drop_index(op.f("ix_courses_instructor_id"), table_name="courses")
    op.drop_index(op.f("ix_courses_id"), table_name="courses")
    op.drop_table("courses")
