"""Create interview_feedbacks table for SKL-10

Revision ID: 20261011_0014
Revises: 20261011_0013
Create Date: 2026-10-11 15:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "20261011_0014"
down_revision: Union[str, None] = "20261011_0013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "interview_feedbacks",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("interview_id", sa.Integer(), nullable=False),
        sa.Column("application_id", sa.Integer(), nullable=False),
        sa.Column("interviewer_id", sa.Integer(), nullable=False),
        sa.Column("overall_score", sa.Integer(), nullable=False),
        sa.Column("technical_score", sa.Integer(), server_default="75", nullable=False),
        sa.Column("communication_score", sa.Integer(), server_default="75", nullable=False),
        sa.Column("problem_solving_score", sa.Integer(), server_default="75", nullable=False),
        sa.Column("recommendation", sa.String(length=50), server_default="HIRE", nullable=False),
        sa.Column("strengths", sa.JSON(), nullable=True),
        sa.Column("improvement_areas", sa.JSON(), nullable=True),
        sa.Column("competency_breakdown", sa.JSON(), nullable=True),
        sa.Column("feedback_notes", sa.Text(), nullable=True),
        sa.Column("internal_notes", sa.Text(), nullable=True),
        sa.Column("suggested_next_action", sa.String(length=50), nullable=True),
        sa.Column("is_shared_with_candidate", sa.Boolean(), server_default=sa.text("0"), nullable=False),
        sa.Column("shared_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["interview_id"], ["interview_requests.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["application_id"], ["job_applications.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["interviewer_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_interview_feedbacks_id"), "interview_feedbacks", ["id"], unique=False)
    op.create_index(op.f("ix_interview_feedbacks_interview_id"), "interview_feedbacks", ["interview_id"], unique=False)
    op.create_index(op.f("ix_interview_feedbacks_application_id"), "interview_feedbacks", ["application_id"], unique=False)
    op.create_index(op.f("ix_interview_feedbacks_interviewer_id"), "interview_feedbacks", ["interviewer_id"], unique=False)
    op.create_index(op.f("ix_interview_feedbacks_recommendation"), "interview_feedbacks", ["recommendation"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_interview_feedbacks_recommendation"), table_name="interview_feedbacks")
    op.drop_index(op.f("ix_interview_feedbacks_interviewer_id"), table_name="interview_feedbacks")
    op.drop_index(op.f("ix_interview_feedbacks_application_id"), table_name="interview_feedbacks")
    op.drop_index(op.f("ix_interview_feedbacks_interview_id"), table_name="interview_feedbacks")
    op.drop_index(op.f("ix_interview_feedbacks_id"), table_name="interview_feedbacks")
    op.drop_table("interview_feedbacks")
