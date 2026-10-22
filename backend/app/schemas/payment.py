from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class PaymentInitiateRequest(BaseModel):
    """Schema for payment session initiation (SKL-20)."""
    plan_id: Optional[int] = Field(default=None, description="Target SubscriptionPlan ID")
    plan_code: Optional[str] = Field(default=None, description="Target SubscriptionPlan code (e.g. PRO_MONTHLY, PRO_YEARLY)")
    gateway_type: str = Field(default="SSLCOMMERZ", description="Payment Gateway: SSLCOMMERZ or GLOBAL_GATEWAY")
    payment_method: Optional[str] = Field(default=None, description="Payment channel (e.g. bKash, Nagad, Rocket, Visa, Mastercard)")
    success_url: Optional[str] = Field(default=None, description="Custom return URL on success")
    fail_url: Optional[str] = Field(default=None, description="Custom return URL on failure")
    cancel_url: Optional[str] = Field(default=None, description="Custom return URL on cancellation")

    model_config = ConfigDict(extra="ignore")


class PaymentInitiateResponse(BaseModel):
    """Schema for payment initiation result with redirect URL."""
    transaction_ref: str
    gateway_type: str
    redirect_url: str
    session_id: Optional[str] = None
    amount: float
    currency: str = "BDT"
    plan_id: int
    plan_name: str
    status: str = "PENDING"

    model_config = ConfigDict(from_attributes=True)


class SSLCommerzIPNPayload(BaseModel):
    """Schema for incoming SSLCommerz IPN / Callback payload."""
    tran_id: str
    val_id: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = "BDT"
    card_type: Optional[str] = None
    store_amount: Optional[float] = None
    bank_tran_id: Optional[str] = None
    status: Optional[str] = None
    tran_date: Optional[str] = None
    verify_sign: Optional[str] = None
    verify_key: Optional[str] = None
    error: Optional[str] = None

    model_config = ConfigDict(extra="ignore")


class GlobalWebhookPayload(BaseModel):
    """Schema for Global Gateway (Stripe) webhook event."""
    id: Optional[str] = None
    type: str
    data: Dict[str, Any]

    model_config = ConfigDict(extra="ignore")


class PaymentVerificationResult(BaseModel):
    """Schema for payment verification outcome."""
    transaction_ref: str
    status: str
    verified: bool
    gateway_type: str
    amount: float
    currency: str
    subscription_activated: bool
    plan_name: Optional[str] = None
    expires_at: Optional[datetime] = None
    error_reason: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
