"""Create notifications table for SKL-17

Revision ID: 20261022_0022
Revises: 20261022_0021
Create Date: 2026-10-22 16:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "20261022_0022"
down_revision: Union[str, None] = "20261022_0021"
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
    if not _table_exists("notifications"):
        op.create_table(
            "notifications",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
            sa.Column("recipient_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("event_type", sa.String(length=50), nullable=False),
            sa.Column("title", sa.String(length=150), nullable=False),
            sa.Column("message", sa.Text(), nullable=False),
            sa.Column("link_url", sa.String(length=255), nullable=True),
            sa.Column("is_read", sa.Boolean(), server_default=sa.text("0"), nullable=False),
            sa.Column("email_sent", sa.Boolean(), server_default=sa.text("0"), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
        op.create_index("ix_notifications_id", "notifications", ["id"])
        op.create_index("ix_notifications_recipient_id", "notifications", ["recipient_id"])
        op.create_index("ix_notifications_event_type", "notifications", ["event_type"])
        op.create_index("ix_notifications_is_read", "notifications", ["is_read"])
        op.create_index("ix_notifications_created_at", "notifications", ["created_at"])


def downgrade() -> None:
    if _table_exists("notifications"):
        for idx in [
            "ix_notifications_created_at",
            "ix_notifications_is_read",
            "ix_notifications_event_type",
            "ix_notifications_recipient_id",
            "ix_notifications_id",
        ]:
            if _index_exists("notifications", idx):
                op.drop_index(idx, table_name="notifications")
        op.drop_table("notifications")
