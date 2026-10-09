"""Create interview_requests and interview_slots tables for SKL-9

Revision ID: 20261011_0013
Revises: 20261010_0012
Create Date: 2026-10-11 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "20261011_0013"
down_revision: Union[str, None] = "20261010_0012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "interview_requests",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("application_id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("candidate_id", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column("interview_type", sa.String(length=100), server_default="Company Interview", nullable=False),
        sa.Column("meeting_platform", sa.String(length=100), server_default="Google Meet", nullable=False),
        sa.Column("meeting_link", sa.String(length=500), nullable=True),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("duration_minutes", sa.Integer(), server_default="45", nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=50), server_default="PENDING", nullable=False),
        sa.Column("selected_slot_id", sa.Integer(), nullable=True),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reschedule_reason", sa.Text(), nullable=True),
        sa.Column("rescheduled_by", sa.Integer(), nullable=True),
        sa.Column("reschedule_preferred_time", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["application_id"], ["job_applications.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["company_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["candidate_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["job_id"], ["job_postings.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["rescheduled_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_interview_requests_id"), "interview_requests", ["id"], unique=False)
    op.create_index(op.f("ix_interview_requests_application_id"), "interview_requests", ["application_id"], unique=False)
    op.create_index(op.f("ix_interview_requests_company_id"), "interview_requests", ["company_id"], unique=False)
    op.create_index(op.f("ix_interview_requests_candidate_id"), "interview_requests", ["candidate_id"], unique=False)
    op.create_index(op.f("ix_interview_requests_job_id"), "interview_requests", ["job_id"], unique=False)
    op.create_index(op.f("ix_interview_requests_status"), "interview_requests", ["status"], unique=False)

    op.create_table(
        "interview_slots",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("interview_request_id", sa.Integer(), nullable=False),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_selected", sa.Boolean(), server_default=sa.text("0"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["interview_request_id"], ["interview_requests.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_interview_slots_id"), "interview_slots", ["id"], unique=False)
    op.create_index(op.f("ix_interview_slots_interview_request_id"), "interview_slots", ["interview_request_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_interview_slots_interview_request_id"), table_name="interview_slots")
    op.drop_index(op.f("ix_interview_slots_id"), table_name="interview_slots")
    op.drop_table("interview_slots")

    op.drop_index(op.f("ix_interview_requests_status"), table_name="interview_requests")
    op.drop_index(op.f("ix_interview_requests_job_id"), table_name="interview_requests")
    op.drop_index(op.f("ix_interview_requests_candidate_id"), table_name="interview_requests")
    op.drop_index(op.f("ix_interview_requests_company_id"), table_name="interview_requests")
    op.drop_index(op.f("ix_interview_requests_application_id"), table_name="interview_requests")
    op.drop_index(op.f("ix_interview_requests_id"), table_name="interview_requests")
    op.drop_table("interview_requests")
