"""Add job search indexes and salary range fields for SKL-5

Revision ID: 20261016_0017
Revises: 20261016_0016
Create Date: 2026-10-16 01:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "20261016_0017"
down_revision: Union[str, None] = "20261016_0016"
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


def upgrade() -> None:
    # 1. Salary fields on job_postings for numeric sorting & filtering
    if not _column_exists("job_postings", "salary_min"):
        op.add_column("job_postings", sa.Column("salary_min", sa.Integer(), nullable=True, server_default="0"))
    if not _column_exists("job_postings", "salary_max"):
        op.add_column("job_postings", sa.Column("salary_max", sa.Integer(), nullable=True, server_default="0"))

    # 2. Indexes for search and multi-attribute filtering (SKL-5)
    if not _index_exists("job_postings", "ix_job_postings_salary_min"):
        op.create_index("ix_job_postings_salary_min", "job_postings", ["salary_min"], unique=False)
    if not _index_exists("job_postings", "ix_job_postings_salary_max"):
        op.create_index("ix_job_postings_salary_max", "job_postings", ["salary_max"], unique=False)
    if not _index_exists("job_postings", "ix_job_postings_search_composite"):
        op.create_index(
            "ix_job_postings_search_composite",
            "job_postings",
            ["status", "posting_type", "work_mode", "location"],
            unique=False,
        )
    if not _index_exists("job_postings", "ix_job_postings_search_attrs"):
        op.create_index(
            "ix_job_postings_search_attrs",
            "job_postings",
            ["title", "work_mode", "location", "status"],
            unique=False,
        )


def downgrade() -> None:
    if _index_exists("job_postings", "ix_job_postings_search_attrs"):
        op.drop_index("ix_job_postings_search_attrs", table_name="job_postings")
    if _index_exists("job_postings", "ix_job_postings_search_composite"):
        op.drop_index("ix_job_postings_search_composite", table_name="job_postings")
    if _index_exists("job_postings", "ix_job_postings_salary_max"):
        op.drop_index("ix_job_postings_salary_max", table_name="job_postings")
    if _index_exists("job_postings", "ix_job_postings_salary_min"):
        op.drop_index("ix_job_postings_salary_min", table_name="job_postings")
    if _column_exists("job_postings", "salary_max"):
        op.drop_column("job_postings", "salary_max")
    if _column_exists("job_postings", "salary_min"):
        op.drop_column("job_postings", "salary_min")
