"""Create saved_jobs table for SKL-6

Revision ID: 20261016_0019
Revises: 20261016_0018
Create Date: 2026-10-16 03:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "20261016_0019"
down_revision: Union[str, None] = "20261016_0018"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    return table_name in insp.get_table_names()


def _index_exists(table_name: str, index_name: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    return any(ix["name"] == index_name for ix in insp.get_indexes(table_name))


def upgrade() -> None:
    if not _table_exists("saved_jobs"):
        op.create_table(
            "saved_jobs",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
            sa.Column("learner_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("job_id", sa.Integer(), sa.ForeignKey("job_postings.id", ondelete="CASCADE"), nullable=False),
            sa.Column("saved_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.UniqueConstraint("learner_id", "job_id", name="uq_saved_jobs_learner_job"),
        )
        op.create_index("ix_saved_jobs_id", "saved_jobs", ["id"])
        op.create_index("ix_saved_jobs_learner_id", "saved_jobs", ["learner_id"])
        op.create_index("ix_saved_jobs_job_id", "saved_jobs", ["job_id"])
        op.create_index("ix_saved_jobs_learner_saved_at", "saved_jobs", ["learner_id", "saved_at"])


def downgrade() -> None:
    if _table_exists("saved_jobs"):
        if _index_exists("saved_jobs", "ix_saved_jobs_learner_saved_at"):
            op.drop_index("ix_saved_jobs_learner_saved_at", table_name="saved_jobs")
        if _index_exists("saved_jobs", "ix_saved_jobs_job_id"):
            op.drop_index("ix_saved_jobs_job_id", table_name="saved_jobs")
        if _index_exists("saved_jobs", "ix_saved_jobs_learner_id"):
            op.drop_index("ix_saved_jobs_learner_id", table_name="saved_jobs")
        if _index_exists("saved_jobs", "ix_saved_jobs_id"):
            op.drop_index("ix_saved_jobs_id", table_name="saved_jobs")
        op.drop_table("saved_jobs")
