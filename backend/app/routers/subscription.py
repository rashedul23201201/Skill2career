from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.auth import ApiResponse
from app.schemas.subscription import (
    SubscriptionPlanResponse,
    UserSubscriptionResponse,
    SelectPlanRequest,
    EntitlementsResponse,
    CancelSubscriptionRequest,
)
from app.services.subscription_service import SubscriptionService

router = APIRouter(prefix="/subscriptions", tags=["Subscription Plans & Entitlements (SKL-19)"])
subscription_service = SubscriptionService()


@router.get(
    "/plans",
    response_model=ApiResponse[List[SubscriptionPlanResponse]],
    status_code=status.HTTP_200_OK,
    summary="List all active subscription plans (SKL-19)",
)
def get_subscription_plans(
    db: Session = Depends(get_db),
) -> ApiResponse[List[SubscriptionPlanResponse]]:
    """Fetch public pricing catalog with Free, Pro Monthly, and Pro Yearly tiers."""
    plans = subscription_service.get_plans(db=db)
    return ApiResponse[List[SubscriptionPlanResponse]](
        success=True,
        message="Subscription plans retrieved successfully",
        data=plans,
    )


@router.get(
    "/my-subscription",
    response_model=ApiResponse[UserSubscriptionResponse],
    status_code=status.HTTP_200_OK,
    summary="Get authenticated user's active subscription tier (SKL-19)",
)
def get_my_subscription(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[UserSubscriptionResponse]:
    """Return active plan details with expiration and renewal dates (auto-fallbacks to Free tier)."""
    sub = subscription_service.get_my_subscription(db=db, current_user=current_user)
    return ApiResponse[UserSubscriptionResponse](
        success=True,
        message="Active user subscription retrieved successfully",
        data=sub,
    )


@router.post(
    "/select-plan",
    response_model=ApiResponse[UserSubscriptionResponse],
    status_code=status.HTTP_200_OK,
    summary="Subscribe to or switch subscription plan (SKL-19)",
)
def select_plan(
    request: SelectPlanRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[UserSubscriptionResponse]:
    """Select a new plan tier, set active subscription dates, and record transaction ledger."""
    sub = subscription_service.select_plan(db=db, current_user=current_user, request=request)
    return ApiResponse[UserSubscriptionResponse](
        success=True,
        message="Subscription plan activated successfully",
        data=sub,
    )


@router.get(
    "/entitlements",
    response_model=ApiResponse[EntitlementsResponse],
    status_code=status.HTTP_200_OK,
    summary="Get user feature entitlements and Pro status (SKL-19)",
)
def get_my_entitlements(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[EntitlementsResponse]:
    """Inspect current permission flags for premium mock tests and advanced analytics."""
    entitlements = subscription_service.get_user_entitlements(db=db, current_user=current_user)
    return ApiResponse[EntitlementsResponse](
        success=True,
        message="User entitlements retrieved successfully",
        data=entitlements,
    )


@router.post(
    "/cancel",
    response_model=ApiResponse[UserSubscriptionResponse],
    status_code=status.HTTP_200_OK,
    summary="Cancel active paid subscription (SKL-19)",
)
def cancel_subscription(
    request: Optional[CancelSubscriptionRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[UserSubscriptionResponse]:
    """Cancel paid subscription and revert account to Free tier."""
    sub = subscription_service.cancel_my_subscription(db=db, current_user=current_user)
    return ApiResponse[UserSubscriptionResponse](
        success=True,
        message="Subscription cancelled and account reverted to Free tier",
        data=sub,
    )


@router.get(
    "/analytics/advanced",
    response_model=ApiResponse[dict],
    status_code=status.HTTP_200_OK,
    summary="Advanced analytics overview (SKL-19 Pro Entitlement Gated)",
)
def get_advanced_analytics_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[dict]:
    """Access platform-wide deep analytics overview, strictly guarded by Pro entitlement."""
    entitlements = subscription_service.get_user_entitlements(db=db, current_user=current_user)
    if not entitlements.is_pro:
        from app.core.exceptions import ForbiddenException
        raise ForbiddenException("Advanced analytics requires an active Pro subscription. Upgrade to Pro to unlock.")

    return ApiResponse[dict](
        success=True,
        message="Advanced performance analytics unlocked",
        data={
            "pro_features_unlocked": True,
            "percentile_ranking": "Top 15% across all assessments",
            "weak_topics": ["Dynamic Programming", "Graph Traversal"],
            "strong_topics": ["SQL Indexing", "Authentication & Security"],
            "recommended_focus": "System Design & Distributed State",
        },
    )
