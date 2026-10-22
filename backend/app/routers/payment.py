from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, Request, Header, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.auth import ApiResponse
from app.schemas.payment import (
    PaymentInitiateRequest,
    PaymentInitiateResponse,
    SSLCommerzIPNPayload,
    GlobalWebhookPayload,
    PaymentVerificationResult,
)
from app.schemas.subscription import PaymentTransactionResponse
from app.services.payment_service import PaymentService

router = APIRouter(prefix="/payments", tags=["Payment Gateways & Subscriptions (SKL-20)"])
payment_service = PaymentService()


async def _extract_payload_dict(request: Request) -> Dict[str, Any]:
    """Helper to cleanly extract dictionary payload from either Form data, Query params, or JSON body."""
    content_type = request.headers.get("content-type", "").lower()
    if "application/json" in content_type:
        try:
            return await request.json()
        except Exception:
            return {}
    elif "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
        form = await request.form()
        return dict(form)
    else:
        # Fallback to query params or try json
        if request.query_params:
            return dict(request.query_params)
        try:
            return await request.json()
        except Exception:
            return {}


def _is_browser_redirect_request(request: Request) -> bool:
    """Detect if request is a direct browser navigation or form submission expecting a page redirect."""
    accept = request.headers.get("accept", "").lower()
    content_type = request.headers.get("content-type", "").lower()
    if "text/html" in accept or "application/x-www-form-urlencoded" in content_type:
        return True
    return False


@router.post(
    "/initiate",
    response_model=ApiResponse[PaymentInitiateResponse],
    status_code=status.HTTP_200_OK,
    summary="Initiate payment session with SSLCommerz or Global Gateway (SKL-20)",
)
def initiate_payment(
    request: PaymentInitiateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[PaymentInitiateResponse]:
    """Create a gateway session, generate immutable transaction ref, and return payment redirect URL."""
    res = payment_service.initiate_payment(db=db, current_user=current_user, request=request)
    return ApiResponse[PaymentInitiateResponse](
        success=True,
        message=f"Payment session initiated successfully with {res.gateway_type}",
        data=res,
    )


@router.post(
    "/sslcommerz/ipn",
    response_model=ApiResponse[PaymentVerificationResult],
    status_code=status.HTTP_200_OK,
    summary="SSLCommerz Instant Payment Notification webhook (SKL-20)",
)
async def sslcommerz_ipn(
    request: Request,
    db: Session = Depends(get_db),
) -> ApiResponse[PaymentVerificationResult]:
    """Server-to-server IPN listener from SSLCommerz for asynchronous transaction verification."""
    payload = await _extract_payload_dict(request)
    result = payment_service.verify_sslcommerz_payment(db=db, payload=payload)
    return ApiResponse[PaymentVerificationResult](
        success=result.verified,
        message="SSLCommerz IPN processed successfully" if result.verified else f"Payment verification failed: {result.error_reason}",
        data=result,
    )


@router.post(
    "/sslcommerz/success",
    status_code=status.HTTP_200_OK,
    summary="SSLCommerz success redirect and callback handler (SKL-20)",
)
async def sslcommerz_success(
    request: Request,
    db: Session = Depends(get_db),
):
    """Handle success callback when user completes payment on SSLCommerz gateway."""
    payload = await _extract_payload_dict(request)
    result = payment_service.verify_sslcommerz_payment(db=db, payload=payload)

    # If browser form submission, redirect user back to frontend billing portal with query params
    if _is_browser_redirect_request(request):
        frontend_url = settings.FRONTEND_URL.rstrip("/")
        redirect_url = f"{frontend_url}/subscription?payment=success&tran_id={result.transaction_ref}"
        return RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)

    return ApiResponse[PaymentVerificationResult](
        success=result.verified,
        message="Payment verified successfully" if result.verified else f"Payment verification failed: {result.error_reason}",
        data=result,
    )


@router.post(
    "/sslcommerz/fail",
    status_code=status.HTTP_200_OK,
    summary="SSLCommerz failure callback handler (SKL-20)",
)
async def sslcommerz_fail(
    request: Request,
    db: Session = Depends(get_db),
):
    """Handle payment failure callback from SSLCommerz gateway (AC-5: subscription not activated)."""
    payload = await _extract_payload_dict(request)
    tran_id = payload.get("tran_id", "")
    reason = payload.get("error") or "Payment failed or rejected by user's bank"
    result = payment_service.handle_sslcommerz_fail_or_cancel(db=db, tran_id=tran_id, reason=reason)

    if _is_browser_redirect_request(request):
        frontend_url = settings.FRONTEND_URL.rstrip("/")
        redirect_url = f"{frontend_url}/subscription?payment=failed&tran_id={tran_id}"
        return RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)

    return ApiResponse[PaymentVerificationResult](
        success=False,
        message=f"Payment failed: {result.error_reason}",
        data=result,
    )


@router.post(
    "/sslcommerz/cancel",
    status_code=status.HTTP_200_OK,
    summary="SSLCommerz cancellation callback handler (SKL-20)",
)
async def sslcommerz_cancel(
    request: Request,
    db: Session = Depends(get_db),
):
    """Handle payment cancellation callback when user aborts payment (AC-5: subscription not activated)."""
    payload = await _extract_payload_dict(request)
    tran_id = payload.get("tran_id", "")
    reason = "Payment cancelled by user"
    result = payment_service.handle_sslcommerz_fail_or_cancel(db=db, tran_id=tran_id, reason=reason)

    if _is_browser_redirect_request(request):
        frontend_url = settings.FRONTEND_URL.rstrip("/")
        redirect_url = f"{frontend_url}/subscription?payment=cancelled&tran_id={tran_id}"
        return RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)

    return ApiResponse[PaymentVerificationResult](
        success=False,
        message="Payment was cancelled by user",
        data=result,
    )


@router.post(
    "/global/webhook",
    response_model=ApiResponse[PaymentVerificationResult],
    status_code=status.HTTP_200_OK,
    summary="Global payment gateway (Stripe) webhook event handler (SKL-20)",
)
async def global_gateway_webhook(
    request: Request,
    stripe_signature: Optional[str] = Header(None, alias="Stripe-Signature"),
    db: Session = Depends(get_db),
) -> ApiResponse[PaymentVerificationResult]:
    """Handle asynchronous webhook event from configured Global Payment Gateway (Stripe)."""
    raw_body = await request.body()
    try:
        import json
        payload = json.loads(raw_body.decode("utf-8")) if raw_body else {}
    except Exception:
        payload = {}

    result = payment_service.verify_global_webhook(
        db=db,
        payload=payload,
        signature_header=stripe_signature,
        raw_body=raw_body,
    )

    return ApiResponse[PaymentVerificationResult](
        success=result.verified,
        message="Global gateway webhook processed successfully",
        data=result,
    )


@router.get(
    "/{transaction_ref}/status",
    response_model=ApiResponse[PaymentTransactionResponse],
    status_code=status.HTTP_200_OK,
    summary="Inspect status of a payment transaction (SKL-20)",
)
def get_payment_status(
    transaction_ref: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[PaymentTransactionResponse]:
    """Retrieve up-to-date transaction status and gateway verification record."""
    txn = payment_service.get_payment_status(db=db, transaction_ref=transaction_ref, current_user=current_user)
    return ApiResponse[PaymentTransactionResponse](
        success=True,
        message="Payment transaction status retrieved successfully",
        data=txn,
    )
