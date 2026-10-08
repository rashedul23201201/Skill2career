"""Create test_attempts table for Test Attempt & Timer (SKL-57)

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
        "test_attempts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("test_id", sa.Integer(), nullable=False),
        sa.Column("learner_id", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="ACTIVE"),
        sa.Column("answers", sa.JSON(), nullable=True),
        sa.Column("marked_for_review", sa.JSON(), nullable=True),
        sa.Column("score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("total_marks", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("percentage", sa.Float(), nullable=False, server_default="0"),
        sa.Column("is_passed", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("time_taken_seconds", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["test_id"], ["mock_tests.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["learner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_test_attempts_id"), "test_attempts", ["id"], unique=False)
    op.create_index(op.f("ix_test_attempts_test_id"), "test_attempts", ["test_id"], unique=False)
    op.create_index(op.f("ix_test_attempts_learner_id"), "test_attempts", ["learner_id"], unique=False)
    op.create_index(op.f("ix_test_attempts_status"), "test_attempts", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_test_attempts_status"), table_name="test_attempts")
    op.drop_index(op.f("ix_test_attempts_learner_id"), table_name="test_attempts")
    op.drop_index(op.f("ix_test_attempts_test_id"), table_name="test_attempts")
    op.drop_index(op.f("ix_test_attempts_id"), table_name="test_attempts")
    op.drop_table("test_attempts")
