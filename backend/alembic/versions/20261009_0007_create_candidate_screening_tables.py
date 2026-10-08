"""Create screening_questions and candidate_evaluations tables for Candidate Screening Module (SKL-8)

Revision ID: 20261009_0007
Revises: 20261009_0006
Create Date: 2026-10-09 02:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "20261009_0007"
down_revision: Union[str, None] = "20261009_0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "screening_questions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column("question_text", sa.String(length=500), nullable=False),
        sa.Column("question_type", sa.String(length=50), nullable=False, server_default="TEXT"),
        sa.Column("options", sa.JSON(), nullable=True),
        sa.Column("expected_answer", sa.String(length=255), nullable=True),
        sa.Column("is_required", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("is_deal_breaker", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("deal_breaker_rule", sa.String(length=50), nullable=True),
        sa.Column("deal_breaker_value", sa.String(length=255), nullable=True),
        sa.Column("deal_breaker_label", sa.String(length=255), nullable=True),
        sa.Column("weight", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["job_postings.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_screening_questions_id"), "screening_questions", ["id"], unique=False)
    op.create_index(op.f("ix_screening_questions_job_id"), "screening_questions", ["job_id"], unique=False)
    op.create_index(op.f("ix_screening_questions_is_deal_breaker"), "screening_questions", ["is_deal_breaker"], unique=False)
    op.create_index(op.f("ix_screening_questions_order_index"), "screening_questions", ["order_index"], unique=False)

    op.create_table(
        "candidate_evaluations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column("candidate_id", sa.Integer(), nullable=True),
        sa.Column("candidate_name", sa.String(length=150), nullable=False),
        sa.Column("candidate_email", sa.String(length=150), nullable=False),
        sa.Column("candidate_avatar_url", sa.String(length=255), nullable=True),
        sa.Column("match_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("deal_breaker_passed", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("deal_breaker_failed_reason", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="APPLIED"),
        sa.Column("answers", sa.JSON(), nullable=True),
        sa.Column("key_answers_preview", sa.String(length=500), nullable=True),
        sa.Column("resume_url", sa.String(length=255), nullable=True),
        sa.Column("reviewed_by", sa.Integer(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["job_postings.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["candidate_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["reviewed_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_candidate_evaluations_id"), "candidate_evaluations", ["id"], unique=False)
    op.create_index(op.f("ix_candidate_evaluations_job_id"), "candidate_evaluations", ["job_id"], unique=False)
    op.create_index(op.f("ix_candidate_evaluations_candidate_id"), "candidate_evaluations", ["candidate_id"], unique=False)
    op.create_index(op.f("ix_candidate_evaluations_match_score"), "candidate_evaluations", ["match_score"], unique=False)
    op.create_index(op.f("ix_candidate_evaluations_deal_breaker_passed"), "candidate_evaluations", ["deal_breaker_passed"], unique=False)
    op.create_index(op.f("ix_candidate_evaluations_status"), "candidate_evaluations", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_candidate_evaluations_status"), table_name="candidate_evaluations")
    op.drop_index(op.f("ix_candidate_evaluations_deal_breaker_passed"), table_name="candidate_evaluations")
    op.drop_index(op.f("ix_candidate_evaluations_match_score"), table_name="candidate_evaluations")
    op.drop_index(op.f("ix_candidate_evaluations_candidate_id"), table_name="candidate_evaluations")
    op.drop_index(op.f("ix_candidate_evaluations_job_id"), table_name="candidate_evaluations")
    op.drop_index(op.f("ix_candidate_evaluations_id"), table_name="candidate_evaluations")
    op.drop_table("candidate_evaluations")

    op.drop_index(op.f("ix_screening_questions_order_index"), table_name="screening_questions")
    op.drop_index(op.f("ix_screening_questions_is_deal_breaker"), table_name="screening_questions")
    op.drop_index(op.f("ix_screening_questions_job_id"), table_name="screening_questions")
    op.drop_index(op.f("ix_screening_questions_id"), table_name="screening_questions")
    op.drop_table("screening_questions")
