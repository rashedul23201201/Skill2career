"""Create chat_conversations and chat_messages tables for SKL-16

Revision ID: 20261022_0020
Revises: 20261016_0019
Create Date: 2026-10-22 03:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "20261022_0020"
down_revision: Union[str, None] = "20261016_0019"
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
    # 1. Create chat_conversations table
    if not _table_exists("chat_conversations"):
        op.create_table(
            "chat_conversations",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
            sa.Column("learner_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("instructor_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
            sa.UniqueConstraint("learner_id", "instructor_id", name="uq_chat_conversations_learner_instructor"),
        )
        op.create_index("ix_chat_conversations_id", "chat_conversations", ["id"])
        op.create_index("ix_chat_conversations_learner_id", "chat_conversations", ["learner_id"])
        op.create_index("ix_chat_conversations_instructor_id", "chat_conversations", ["instructor_id"])
        op.create_index("ix_chat_conversations_updated_at", "chat_conversations", ["updated_at"])

    # 2. Create chat_messages table
    if not _table_exists("chat_messages"):
        op.create_table(
            "chat_messages",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
            sa.Column("conversation_id", sa.Integer(), sa.ForeignKey("chat_conversations.id", ondelete="CASCADE"), nullable=False),
            sa.Column("sender_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("message_text", sa.Text(), nullable=False),
            sa.Column("is_read", sa.Boolean(), server_default=sa.text("0"), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
        op.create_index("ix_chat_messages_id", "chat_messages", ["id"])
        op.create_index("ix_chat_messages_conversation_id", "chat_messages", ["conversation_id"])
        op.create_index("ix_chat_messages_sender_id", "chat_messages", ["sender_id"])
        op.create_index("ix_chat_messages_is_read", "chat_messages", ["is_read"])
        op.create_index("ix_chat_messages_created_at", "chat_messages", ["created_at"])


def downgrade() -> None:
    if _table_exists("chat_messages"):
        for idx in [
            "ix_chat_messages_created_at",
            "ix_chat_messages_is_read",
            "ix_chat_messages_sender_id",
            "ix_chat_messages_conversation_id",
            "ix_chat_messages_id",
        ]:
            if _index_exists("chat_messages", idx):
                op.drop_index(idx, table_name="chat_messages")
        op.drop_table("chat_messages")

    if _table_exists("chat_conversations"):
        for idx in [
            "ix_chat_conversations_updated_at",
            "ix_chat_conversations_instructor_id",
            "ix_chat_conversations_learner_id",
            "ix_chat_conversations_id",
        ]:
            if _index_exists("chat_conversations", idx):
                op.drop_index(idx, table_name="chat_conversations")
        op.drop_table("chat_conversations")
