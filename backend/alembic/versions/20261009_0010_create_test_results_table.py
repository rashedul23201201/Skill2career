"""Create test_results table and add topic/difficulty to questions for SKL-58

Revision ID: 20261009_0010
Revises: 20261009_0009
Create Date: 2026-10-09 03:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "20261009_0010"
down_revision: Union[str, None] = "20261009_0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add optional topic and difficulty columns to test_questions
    op.add_column("test_questions", sa.Column("topic", sa.String(length=100), nullable=True))
    op.add_column("test_questions", sa.Column("difficulty", sa.String(length=50), nullable=True))

    # 2. Create test_results table
    op.create_table(
        "test_results",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("attempt_id", sa.Integer(), nullable=False),
        sa.Column("total_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("total_marks", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("percentage", sa.Float(), nullable=False, server_default="0"),
        sa.Column("accuracy", sa.Float(), nullable=False, server_default="0"),
        sa.Column("is_passed", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("time_taken_seconds", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("percentile_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("percentile_label", sa.String(length=100), nullable=False, server_default="Top 20% Candidate"),
        sa.Column("topic_breakdown", sa.JSON(), nullable=True),
        sa.Column("difficulty_analysis", sa.JSON(), nullable=True),
        sa.Column("question_reviews", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["attempt_id"], ["test_attempts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("attempt_id", name="uq_test_results_attempt_id"),
    )
    op.create_index(op.f("ix_test_results_id"), "test_results", ["id"], unique=False)
    op.create_index(op.f("ix_test_results_attempt_id"), "test_results", ["attempt_id"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_test_results_attempt_id"), table_name="test_results")
    op.drop_index(op.f("ix_test_results_id"), table_name="test_results")
    op.drop_table("test_results")
    op.drop_column("test_questions", "difficulty")
    op.drop_column("test_questions", "topic")
