"""Create Sprint 1 tokens and profile tables

Revision ID: 20261002_0002
Revises: 20261002_0001
Create Date: 2026-10-02 21:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20261002_0002"
down_revision: Union[str, None] = "20261002_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Update users table with lockout fields
    op.add_column("users", sa.Column("failed_login_attempts", sa.Integer(), nullable=False, server_default=sa.text("0")))
    op.add_column("users", sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True))

    # 2. Refresh Tokens Table (SKL-49)
    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(length=255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_refresh_tokens_id"), "refresh_tokens", ["id"], unique=False)
    op.create_index(op.f("ix_refresh_tokens_user_id"), "refresh_tokens", ["user_id"], unique=False)
    op.create_index(op.f("ix_refresh_tokens_token_hash"), "refresh_tokens", ["token_hash"], unique=True)

    # 3. Password Resets Table (SKL-49)
    op.create_table(
        "password_resets",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(length=255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_password_resets_id"), "password_resets", ["id"], unique=False)
    op.create_index(op.f("ix_password_resets_user_id"), "password_resets", ["user_id"], unique=False)
    op.create_index(op.f("ix_password_resets_token_hash"), "password_resets", ["token_hash"], unique=True)

    # 4. Email Verifications Table (SKL-49)
    op.create_table(
        "email_verifications",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(length=255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_email_verifications_id"), "email_verifications", ["id"], unique=False)
    op.create_index(op.f("ix_email_verifications_user_id"), "email_verifications", ["user_id"], unique=False)
    op.create_index(op.f("ix_email_verifications_token_hash"), "email_verifications", ["token_hash"], unique=True)

    # 5. Learner Profiles Table
    op.create_table(
        "learner_profiles",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("phone_number", sa.String(length=50), nullable=True),
        sa.Column("location", sa.String(length=150), nullable=True),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("target_role", sa.String(length=100), nullable=True),
        sa.Column("primary_track", sa.String(length=100), nullable=True),
        sa.Column("institution", sa.String(length=150), nullable=True),
        sa.Column("department", sa.String(length=150), nullable=True),
        sa.Column("skills", sa.JSON(), nullable=True),
        sa.Column("resume_url", sa.String(length=255), nullable=True),
        sa.Column("resume_filename", sa.String(length=255), nullable=True),
        sa.Column("portfolio_links", sa.JSON(), nullable=True),
        sa.Column("completion_pct", sa.Integer(), nullable=False, server_default=sa.text("25")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index(op.f("ix_learner_profiles_id"), "learner_profiles", ["id"], unique=False)

    # 6. Instructor Profiles Table
    op.create_table(
        "instructor_profiles",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("designation", sa.String(length=100), nullable=True),
        sa.Column("institution", sa.String(length=150), nullable=True),
        sa.Column("qualification", sa.String(length=150), nullable=True),
        sa.Column("expertise_domain", sa.String(length=150), nullable=True),
        sa.Column("years_experience", sa.String(length=50), nullable=True),
        sa.Column("certificates", sa.JSON(), nullable=True),
        sa.Column("intro_video_url", sa.String(length=255), nullable=True),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("linkedin_url", sa.String(length=255), nullable=True),
        sa.Column("onboarding_status", sa.String(length=50), nullable=False, server_default="PENDING_REVIEW"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index(op.f("ix_instructor_profiles_id"), "instructor_profiles", ["id"], unique=False)

    # 7. Company Profiles Table
    op.create_table(
        "company_profiles",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("company_name", sa.String(length=150), nullable=False),
        sa.Column("industry", sa.String(length=100), nullable=True),
        sa.Column("company_size", sa.String(length=50), nullable=True),
        sa.Column("contact_person", sa.String(length=100), nullable=True),
        sa.Column("contact_phone", sa.String(length=50), nullable=True),
        sa.Column("website_url", sa.String(length=255), nullable=True),
        sa.Column("office_address", sa.String(length=255), nullable=True),
        sa.Column("tagline", sa.String(length=255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("logo_url", sa.String(length=255), nullable=True),
        sa.Column("banner_url", sa.String(length=255), nullable=True),
        sa.Column("trade_license_url", sa.String(length=255), nullable=True),
        sa.Column("verification_status", sa.String(length=50), nullable=False, server_default="PENDING"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index(op.f("ix_company_profiles_id"), "company_profiles", ["id"], unique=False)


def downgrade() -> None:
    op.drop_table("company_profiles")
    op.drop_table("instructor_profiles")
    op.drop_table("learner_profiles")
    op.drop_table("email_verifications")
    op.drop_table("password_resets")
    op.drop_table("refresh_tokens")
    op.drop_column("users", "locked_until")
    op.drop_column("users", "failed_login_attempts")
