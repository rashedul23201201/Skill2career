"""Create mock_tests and test_questions tables for Assessment Module (SKL-56)

Revision ID: 20261009_0006
Revises: 20261008_0005
Create Date: 2026-10-09 00:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "20261009_0006"
down_revision: Union[str, None] = "20261008_0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "mock_tests",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("instructor_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(length=100), nullable=False, server_default="Programming"),
        sa.Column("duration_minutes", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("passing_score", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("total_questions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="DRAFT"),
        sa.Column("is_published", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["instructor_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_mock_tests_id"), "mock_tests", ["id"], unique=False)
    op.create_index(op.f("ix_mock_tests_instructor_id"), "mock_tests", ["instructor_id"], unique=False)
    op.create_index(op.f("ix_mock_tests_title"), "mock_tests", ["title"], unique=False)
    op.create_index(op.f("ix_mock_tests_category"), "mock_tests", ["category"], unique=False)
    op.create_index(op.f("ix_mock_tests_status"), "mock_tests", ["status"], unique=False)

    op.create_table(
        "test_questions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("test_id", sa.Integer(), nullable=False),
        sa.Column("question_text", sa.Text(), nullable=False),
        sa.Column("options", sa.JSON(), nullable=False),
        sa.Column("correct_option", sa.String(length=10), nullable=False),
        sa.Column("marks", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["test_id"], ["mock_tests.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_test_questions_id"), "test_questions", ["id"], unique=False)
    op.create_index(op.f("ix_test_questions_test_id"), "test_questions", ["test_id"], unique=False)
    op.create_index(op.f("ix_test_questions_order_index"), "test_questions", ["order_index"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_test_questions_order_index"), table_name="test_questions")
    op.drop_index(op.f("ix_test_questions_test_id"), table_name="test_questions")
    op.drop_index(op.f("ix_test_questions_id"), table_name="test_questions")
    op.drop_table("test_questions")

    op.drop_index(op.f("ix_mock_tests_status"), table_name="mock_tests")
    op.drop_index(op.f("ix_mock_tests_category"), table_name="mock_tests")
    op.drop_index(op.f("ix_mock_tests_title"), table_name="mock_tests")
    op.drop_index(op.f("ix_mock_tests_instructor_id"), table_name="mock_tests")
    op.drop_index(op.f("ix_mock_tests_id"), table_name="mock_tests")
    op.drop_table("mock_tests")
