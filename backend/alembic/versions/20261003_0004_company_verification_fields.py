"""Add verification dossier and admin review fields to company_profiles (SKL-2)

Revision ID: 20261003_0004
Revises: 20261003_0003
Create Date: 2026-10-03 16:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20261004_0004"
down_revision: Union[str, None] = "20261003_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add SKL-2 company verification dossier fields
    op.add_column("company_profiles", sa.Column("location", sa.String(length=150), nullable=True))
    op.add_column("company_profiles", sa.Column("registration_number", sa.String(length=100), nullable=True))
    op.add_column("company_profiles", sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("company_profiles", sa.Column("verified_by_admin_id", sa.Integer(), nullable=True))
    op.add_column("company_profiles", sa.Column("verification_notes", sa.Text(), nullable=True))

    op.create_foreign_key(
        "fk_company_profiles_verified_by_admin_id_users",
        "company_profiles",
        "users",
        ["verified_by_admin_id"],
        ["id"],
        ondelete="SET NULL"
    )


def downgrade() -> None:
    op.drop_constraint("fk_company_profiles_verified_by_admin_id_users", "company_profiles", type_="foreignkey")
    op.drop_column("company_profiles", "verification_notes")
    op.drop_column("company_profiles", "verified_by_admin_id")
    op.drop_column("company_profiles", "verified_at")
    op.drop_column("company_profiles", "registration_number")
    op.drop_column("company_profiles", "location")
