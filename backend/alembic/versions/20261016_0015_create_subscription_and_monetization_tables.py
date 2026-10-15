"""Create subscription_plans, user_subscriptions, payment_transactions and extend mock_tests for SKL-19 and SKL-21

Revision ID: 20261016_0015
Revises: 20261011_0014
Create Date: 2026-10-16 00:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column

revision: str = "20261016_0015"
down_revision: Union[str, None] = "20261011_0014"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create subscription_plans table (SKL-19)
    op.create_table(
        "subscription_plans",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("price", sa.Numeric(precision=10, scale=2), nullable=False, server_default="0.00"),
        sa.Column("billing_cycle", sa.String(length=50), nullable=False, server_default="MONTHLY"),
        sa.Column("features", sa.JSON(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("1"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_subscription_plans_code"),
    )
    op.create_index(op.f("ix_subscription_plans_id"), "subscription_plans", ["id"], unique=False)
    op.create_index(op.f("ix_subscription_plans_code"), "subscription_plans", ["code"], unique=True)

    # 2. Create user_subscriptions table (SKL-19)
    op.create_table(
        "user_subscriptions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("plan_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=50), server_default="ACTIVE", nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("auto_renew", sa.Boolean(), server_default=sa.text("1"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["plan_id"], ["subscription_plans.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_user_subscriptions_id"), "user_subscriptions", ["id"], unique=False)
    op.create_index(op.f("ix_user_subscriptions_user_id"), "user_subscriptions", ["user_id"], unique=False)
    op.create_index(op.f("ix_user_subscriptions_plan_id"), "user_subscriptions", ["plan_id"], unique=False)
    op.create_index(op.f("ix_user_subscriptions_status"), "user_subscriptions", ["status"], unique=False)

    # 3. Create payment_transactions table (SKL-21 ledger & idempotency)
    op.create_table(
        "payment_transactions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("transaction_ref", sa.String(length=100), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("subscription_id", sa.Integer(), nullable=True),
        sa.Column("amount", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=10), server_default="BDT", nullable=False),
        sa.Column("gateway", sa.String(length=50), server_default="SIMULATED", nullable=False),
        sa.Column("status", sa.String(length=50), server_default="SUCCESS", nullable=False),
        sa.Column("raw_response", sa.JSON(), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verified_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["subscription_id"], ["user_subscriptions.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["verified_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("transaction_ref", name="uq_payment_transactions_transaction_ref"),
    )
    op.create_index(op.f("ix_payment_transactions_id"), "payment_transactions", ["id"], unique=False)
    op.create_index(op.f("ix_payment_transactions_transaction_ref"), "payment_transactions", ["transaction_ref"], unique=True)
    op.create_index(op.f("ix_payment_transactions_user_id"), "payment_transactions", ["user_id"], unique=False)
    op.create_index(op.f("ix_payment_transactions_status"), "payment_transactions", ["status"], unique=False)

    # 4. Add is_premium column to mock_tests table for entitlement gating (SKL-19)
    with op.batch_alter_table("mock_tests", schema=None) as batch_op:
        batch_op.add_column(sa.Column("is_premium", sa.Boolean(), server_default=sa.text("0"), nullable=False))
        batch_op.create_index("ix_mock_tests_is_premium", ["is_premium"], unique=False)

    # 5. Seed default subscription plans: FREE, PRO_MONTHLY, PRO_YEARLY
    plans_table = table(
        "subscription_plans",
        column("name", sa.String),
        column("code", sa.String),
        column("description", sa.Text),
        column("price", sa.Numeric),
        column("billing_cycle", sa.String),
        column("features", sa.JSON),
        column("is_active", sa.Boolean),
    )

    op.bulk_insert(
        plans_table,
        [
            {
                "name": "Free",
                "code": "FREE",
                "description": "Essential resources for initial preparation and self-guided revision.",
                "price": 0.00,
                "billing_cycle": "FREE",
                "features": [
                    "Free courses",
                    "Limited mock tests",
                    "Forum access"
                ],
                "is_active": True,
            },
            {
                "name": "Monthly",
                "code": "PRO_MONTHLY",
                "description": "Complete monthly access for dedicated BCS, bank, and tech job seekers.",
                "price": 499.00,
                "billing_cycle": "MONTHLY",
                "features": [
                    "Full course access",
                    "Mock tests",
                    "Interview preparation",
                    "Advanced analytics"
                ],
                "is_active": True,
            },
            {
                "name": "Yearly",
                "code": "PRO_YEARLY",
                "description": "Best value for sustained 12-month career transformation and continuous exam series.",
                "price": 4999.00,
                "billing_cycle": "YEARLY",
                "features": [
                    "Full course access",
                    "Mock tests",
                    "Interview preparation",
                    "Advanced analytics",
                    "Priority support"
                ],
                "is_active": True,
            },
        ],
    )


def downgrade() -> None:
    with op.batch_alter_table("mock_tests", schema=None) as batch_op:
        batch_op.drop_index("ix_mock_tests_is_premium")
        batch_op.drop_column("is_premium")

    op.drop_index(op.f("ix_payment_transactions_status"), table_name="payment_transactions")
    op.drop_index(op.f("ix_payment_transactions_user_id"), table_name="payment_transactions")
    op.drop_index(op.f("ix_payment_transactions_transaction_ref"), table_name="payment_transactions")
    op.drop_index(op.f("ix_payment_transactions_id"), table_name="payment_transactions")
    op.drop_table("payment_transactions")

    op.drop_index(op.f("ix_user_subscriptions_status"), table_name="user_subscriptions")
    op.drop_index(op.f("ix_user_subscriptions_plan_id"), table_name="user_subscriptions")
    op.drop_index(op.f("ix_user_subscriptions_user_id"), table_name="user_subscriptions")
    op.drop_index(op.f("ix_user_subscriptions_id"), table_name="user_subscriptions")
    op.drop_table("user_subscriptions")

    op.drop_index(op.f("ix_subscription_plans_code"), table_name="subscription_plans")
    op.drop_index(op.f("ix_subscription_plans_id"), table_name="subscription_plans")
    op.drop_table("subscription_plans")
