from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field
from app.models.user import UserRole
from app.schemas.auth import UserResponse


class AdminOverviewStats(BaseModel):
    """Schema for platform overview KPI metrics (SKL-50/SKL-24)."""
    total_users: int
    total_companies: int
    active_courses: int
    pending_approvals: int
    active_users: int
    inactive_users: int
    role_breakdown: Dict[str, int]


class UserStatusUpdateRequest(BaseModel):
    """Schema for toggling user account active/inactive status."""
    is_active: bool
    reason: Optional[str] = Field(default=None, max_length=255)


class UserRoleUpdateRequest(BaseModel):
    """Schema for administrative role reassignment."""
    role: UserRole
    reason: Optional[str] = Field(default=None, max_length=255)


class PaginatedUserResponse(BaseModel):
    """Schema for paginated user list."""
    items: List[UserResponse]
    total: int
    page: int
    size: int
    total_pages: int


class AuditLogResponse(BaseModel):
    """Schema for administrative audit log entries."""
    id: int
    admin_id: Optional[int] = None
    admin_name: Optional[str] = None
    target_user_id: Optional[int] = None
    target_user_name: Optional[str] = None
    action: str
    details: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
