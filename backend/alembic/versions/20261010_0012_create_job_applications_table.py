"""Create job_applications table for SKL-7

Revision ID: 20261010_0012
Revises: 20261010_0011
Create Date: 2026-10-10 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "20261010_0012"
down_revision: Union[str, None] = "20261010_0011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "job_applications",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column("learner_id", sa.Integer(), nullable=False),
        sa.Column("resume_url", sa.String(length=255), nullable=True),
        sa.Column("resume_filename", sa.String(length=255), nullable=True),
        sa.Column("cover_letter", sa.Text(), nullable=True),
        sa.Column("screening_answers", sa.JSON(), nullable=True),
        sa.Column("screening_score", sa.Integer(), server_default="0", nullable=False),
        sa.Column("deal_breaker_passed", sa.Boolean(), server_default=sa.text("1"), nullable=False),
        sa.Column("deal_breaker_failed_reason", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=50), server_default="SUBMITTED", nullable=False),
        sa.Column("reviewed_by", sa.Integer(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("applied_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["job_postings.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["learner_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reviewed_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_job_applications_id"), "job_applications", ["id"], unique=False)
    op.create_index(op.f("ix_job_applications_job_id"), "job_applications", ["job_id"], unique=False)
    op.create_index(op.f("ix_job_applications_learner_id"), "job_applications", ["learner_id"], unique=False)
    op.create_index(op.f("ix_job_applications_status"), "job_applications", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_job_applications_status"), table_name="job_applications")
    op.drop_index(op.f("ix_job_applications_learner_id"), table_name="job_applications")
    op.drop_index(op.f("ix_job_applications_job_id"), table_name="job_applications")
    op.drop_index(op.f("ix_job_applications_id"), table_name="job_applications")
    op.drop_table("job_applications")
