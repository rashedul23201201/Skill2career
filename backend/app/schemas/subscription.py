from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field, ConfigDict


class SubscriptionPlanResponse(BaseModel):
    """Schema for subscription tier representation."""
    id: int
    name: str
    code: str
    description: Optional[str] = None
    price: float
    billing_cycle: str
    features: List[str] = []
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserSubscriptionResponse(BaseModel):
    """Schema for user active or historical subscription."""
    id: int
    user_id: int
    plan_id: int
    plan: Optional[SubscriptionPlanResponse] = None
    status: str
    starts_at: datetime
    expires_at: Optional[datetime] = None
    auto_renew: bool
    is_pro: bool = False
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SelectPlanRequest(BaseModel):
    """Schema for subscribing or upgrading to a plan tier."""
    plan_code: Optional[str] = Field(default=None, description="Plan code e.g. FREE, PRO_MONTHLY, PRO_YEARLY")
    plan_id: Optional[int] = Field(default=None, description="Plan ID")
    payment_gateway: Optional[str] = Field(default="SIMULATED", description="Gateway e.g. BKASH, NAGAD, SIMULATED")
    payment_method: Optional[str] = Field(default="bKash Auto-Debit", description="Payment method label")

    model_config = ConfigDict(extra="ignore")


class EntitlementsResponse(BaseModel):
    """Schema for current user's entitlement permissions."""
    plan_code: str
    plan_name: str
    is_pro: bool
    can_access_premium_mock_tests: bool
    can_access_advanced_analytics: bool
    expires_at: Optional[datetime] = None
    status: str


class PaymentTransactionResponse(BaseModel):
    """Schema for transaction ledger record."""
    id: int
    transaction_ref: str
    user_id: int
    subscription_id: Optional[int] = None
    plan_name: Optional[str] = None
    user_email: Optional[str] = None
    user_name: Optional[str] = None
    amount: float
    currency: str = "BDT"
    gateway: str
    status: str
    raw_response: Optional[dict] = None
    verified_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TransactionVerifyRequest(BaseModel):
    """Schema for transaction verification check."""
    transaction_ref: str
    status: Optional[str] = "SUCCESS"


class CancelSubscriptionRequest(BaseModel):
    """Schema for subscription cancellation."""
    reason: Optional[str] = None


class InvoiceResponse(BaseModel):
    """Schema for tax invoice representation."""
    invoice_number: str
    transaction_ref: str
    user_name: str
    user_email: str
    date: datetime
    plan_name: str
    amount: float
    currency: str = "BDT"
    payment_method: str
    status: str
