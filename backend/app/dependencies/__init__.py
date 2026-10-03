"""API dependencies package."""

from app.dependencies.auth import (
    get_current_user,
    require_role,
    require_admin,
    require_learner,
    require_instructor,
    require_company,
    require_verified_company,
)

__all__ = [
    "get_current_user",
    "require_role",
    "require_admin",
    "require_learner",
    "require_instructor",
    "require_company",
    "require_verified_company",
]
