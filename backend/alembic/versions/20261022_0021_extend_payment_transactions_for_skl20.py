"""Extend payment_transactions table with gateway tokens and validation columns for SKL-20

Revision ID: 20261022_0021
Revises: 20261022_0020
Create Date: 2026-10-22 15:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "20261022_0021"
down_revision: Union[str, None] = "20261022_0020"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    return table_name in insp.get_table_names()


def _column_exists(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    return any(c["name"] == column_name for c in insp.get_columns(table_name))


def _index_exists(table_name: str, index_name: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    return any(ix["name"] == index_name for ix in insp.get_indexes(table_name))


def upgrade() -> None:
    if _table_exists("payment_transactions"):
        with op.batch_alter_table("payment_transactions", schema=None) as batch_op:
            if not _column_exists("payment_transactions", "gateway_type"):
                batch_op.add_column(
                    sa.Column("gateway_type", sa.String(length=50), server_default="SSLCOMMERZ", nullable=False)
                )
            if not _column_exists("payment_transactions", "gateway_session_key"):
                batch_op.add_column(
                    sa.Column("gateway_session_key", sa.String(length=255), nullable=True)
                )
            if not _column_exists("payment_transactions", "gateway_val_id"):
                batch_op.add_column(
                    sa.Column("gateway_val_id", sa.String(length=255), nullable=True)
                )
            if not _column_exists("payment_transactions", "bank_tran_id"):
                batch_op.add_column(
                    sa.Column("bank_tran_id", sa.String(length=255), nullable=True)
                )
            if not _column_exists("payment_transactions", "card_type"):
                batch_op.add_column(
                    sa.Column("card_type", sa.String(length=50), nullable=True)
                )
            if not _column_exists("payment_transactions", "error_reason"):
                batch_op.add_column(
                    sa.Column("error_reason", sa.Text(), nullable=True)
                )

        if not _index_exists("payment_transactions", "ix_payment_transactions_gateway_val_id"):
            op.create_index(
                "ix_payment_transactions_gateway_val_id",
                "payment_transactions",
                ["gateway_val_id"],
                unique=False,
            )


def downgrade() -> None:
    if _table_exists("payment_transactions"):
        if _index_exists("payment_transactions", "ix_payment_transactions_gateway_val_id"):
            op.drop_index("ix_payment_transactions_gateway_val_id", table_name="payment_transactions")

        with op.batch_alter_table("payment_transactions", schema=None) as batch_op:
            if _column_exists("payment_transactions", "error_reason"):
                batch_op.drop_column("error_reason")
            if _column_exists("payment_transactions", "card_type"):
                batch_op.drop_column("card_type")
            if _column_exists("payment_transactions", "bank_tran_id"):
                batch_op.drop_column("bank_tran_id")
            if _column_exists("payment_transactions", "gateway_val_id"):
                batch_op.drop_column("gateway_val_id")
            if _column_exists("payment_transactions", "gateway_session_key"):
                batch_op.drop_column("gateway_session_key")
            if _column_exists("payment_transactions", "gateway_type"):
                batch_op.drop_column("gateway_type")
