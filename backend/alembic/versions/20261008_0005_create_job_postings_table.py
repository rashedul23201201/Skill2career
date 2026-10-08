"""Create job_postings table for Recruitment Pipeline (SKL-4)

Revision ID: 20261008_0005
Revises: 20261007_0004
Create Date: 2026-10-08 21:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20261008_0005"
down_revision: Union[str, None] = "20261007_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "job_postings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("posting_type", sa.String(length=50), nullable=False, server_default="Job"),
        sa.Column("work_mode", sa.String(length=50), nullable=False, server_default="On-site"),
        sa.Column("location", sa.String(length=150), nullable=False, server_default="Dhaka"),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("requirements", sa.Text(), nullable=False),
        sa.Column("skills", sa.JSON(), nullable=True),
        sa.Column("compensation", sa.String(length=100), nullable=False),
        sa.Column("duration", sa.String(length=100), nullable=True),
        sa.Column("experience_level", sa.String(length=50), nullable=False, server_default="Entry Level"),
        sa.Column("category", sa.String(length=100), nullable=False, server_default="Software Engineering"),
        sa.Column("deadline", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="ACTIVE"),
        sa.Column("applications_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_job_postings_id"), "job_postings", ["id"], unique=False)
    op.create_index(op.f("ix_job_postings_company_id"), "job_postings", ["company_id"], unique=False)
    op.create_index(op.f("ix_job_postings_title"), "job_postings", ["title"], unique=False)
    op.create_index(op.f("ix_job_postings_posting_type"), "job_postings", ["posting_type"], unique=False)
    op.create_index(op.f("ix_job_postings_work_mode"), "job_postings", ["work_mode"], unique=False)
    op.create_index(op.f("ix_job_postings_location"), "job_postings", ["location"], unique=False)
    op.create_index(op.f("ix_job_postings_category"), "job_postings", ["category"], unique=False)
    op.create_index(op.f("ix_job_postings_status"), "job_postings", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_job_postings_status"), table_name="job_postings")
    op.drop_index(op.f("ix_job_postings_category"), table_name="job_postings")
    op.drop_index(op.f("ix_job_postings_location"), table_name="job_postings")
    op.drop_index(op.f("ix_job_postings_work_mode"), table_name="job_postings")
    op.drop_index(op.f("ix_job_postings_posting_type"), table_name="job_postings")
    op.drop_index(op.f("ix_job_postings_title"), table_name="job_postings")
    op.drop_index(op.f("ix_job_postings_company_id"), table_name="job_postings")
    op.drop_index(op.f("ix_job_postings_id"), table_name="job_postings")
    op.drop_table("job_postings")
