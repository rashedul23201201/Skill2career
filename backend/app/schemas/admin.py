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


# --- SKL-23: Executive Dashboard & Analytics Schemas ---

class AdminAnalyticsUserOverview(BaseModel):
    total: int
    active: int
    inactive: int
    role_breakdown: Dict[str, int]


class AdminAnalyticsCompanyOverview(BaseModel):
    total: int
    verified: int
    pending_verification: int
    rejected: int


class AdminAnalyticsCourseOverview(BaseModel):
    total: int
    published: int
    draft: int
    total_enrollments: int


class AdminAnalyticsRecruitmentOverview(BaseModel):
    total_jobs: int
    active_jobs: int
    total_applications: int


class AdminAnalyticsRevenueOverview(BaseModel):
    total_revenue: float
    currency: str = "BDT"
    successful_transactions: int
    active_subscriptions: int


class AdminAnalyticsModerationOverview(BaseModel):
    pending_approvals: int
    pending_companies: int
    pending_instructors: int
    pending_courses: int


class PlatformActivityItem(BaseModel):
    id: str
    activity_type: str
    title: str
    description: str
    timestamp: datetime
    badge_color: str = "blue"

    model_config = ConfigDict(from_attributes=True)


class AdminOverviewAnalyticsResponse(BaseModel):
    users: AdminAnalyticsUserOverview
    companies: AdminAnalyticsCompanyOverview
    courses: AdminAnalyticsCourseOverview
    recruitment: AdminAnalyticsRecruitmentOverview
    revenue: AdminAnalyticsRevenueOverview
    moderation: AdminAnalyticsModerationOverview
    recent_activity: List[PlatformActivityItem]


class GatewayRevenueItem(BaseModel):
    gateway: str
    count: int
    total_amount: float


class PlanRevenueItem(BaseModel):
    plan_code: str
    plan_name: str
    subscriber_count: int
    total_revenue: float


class RecentTransactionAnalyticsItem(BaseModel):
    id: int
    transaction_ref: str
    user_name: str
    user_email: str
    amount: float
    currency: str
    gateway: str
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AdminRevenueAnalyticsResponse(BaseModel):
    total_revenue: float
    currency: str = "BDT"
    total_transactions: int
    successful_transactions: int
    pending_transactions: int
    failed_transactions: int
    success_rate: float
    active_subscriptions: int
    subscriptions_by_status: Dict[str, int]
    revenue_by_gateway: List[GatewayRevenueItem]
    revenue_by_plan: List[PlanRevenueItem]
    recent_transactions: List[RecentTransactionAnalyticsItem]


class TopHiringCompanyItem(BaseModel):
    company_id: int
    company_name: str
    active_jobs: int
    total_applications: int


class RecentJobPostingItem(BaseModel):
    id: int
    title: str
    company_name: str
    posting_type: str
    category: str
    work_mode: str
    status: str
    applications_count: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AdminRecruitmentSummaryResponse(BaseModel):
    total_jobs: int
    active_jobs: int
    closed_jobs: int
    draft_jobs: int
    total_applications: int
    applications_by_status: Dict[str, int]
    total_interviews: int
    interviews_by_status: Dict[str, int]
    top_hiring_companies: List[TopHiringCompanyItem]
    recent_job_postings: List[RecentJobPostingItem]

