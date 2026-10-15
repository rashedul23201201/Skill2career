from typing import List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_user, require_role
from app.models.user import User, UserRole
from app.schemas.auth import ApiResponse
from app.schemas.subscription import (
    PaymentTransactionResponse,
    TransactionVerifyRequest,
    InvoiceResponse,
)
from app.services.subscription_service import SubscriptionService

router = APIRouter(prefix="/transactions", tags=["Transaction History & Verification (SKL-21)"])
admin_router = APIRouter(prefix="/admin/transactions", tags=["Admin Transaction Audit (SKL-21)"])

subscription_service = SubscriptionService()


@router.get(
    "/my-history",
    response_model=ApiResponse[List[PaymentTransactionResponse]],
    status_code=status.HTTP_200_OK,
    summary="Get authenticated user's transaction history (SKL-21)",
)
def get_my_transaction_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[List[PaymentTransactionResponse]]:
    """Fetch personal transaction ledger restricted strictly to the calling user."""
    transactions = subscription_service.get_my_transactions(db=db, current_user=current_user)
    return ApiResponse[List[PaymentTransactionResponse]](
        success=True,
        message="User transaction history retrieved successfully",
        data=transactions,
    )


@router.post(
    "/verify",
    response_model=ApiResponse[PaymentTransactionResponse],
    status_code=status.HTTP_200_OK,
    summary="Idempotent transaction verification (SKL-21)",
)
def verify_transaction(
    request: TransactionVerifyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[PaymentTransactionResponse]:
    """Verify transaction reference idempotently without duplicate charges."""
    verified = subscription_service.verify_transaction(db=db, current_user=current_user, request=request)
    return ApiResponse[PaymentTransactionResponse](
        success=True,
        message="Transaction verified successfully",
        data=verified,
    )


@router.get(
    "/{transaction_id}/invoice",
    response_model=ApiResponse[InvoiceResponse],
    status_code=status.HTTP_200_OK,
    summary="Download transaction tax invoice receipt (SKL-21)",
)
def get_transaction_invoice(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[InvoiceResponse]:
    """Retrieve full tax invoice and billing details for a specific transaction."""
    invoice = subscription_service.get_invoice(db=db, current_user=current_user, transaction_id=transaction_id)
    return ApiResponse[InvoiceResponse](
        success=True,
        message="Tax invoice retrieved successfully",
        data=invoice,
    )


@admin_router.get(
    "",
    response_model=ApiResponse[List[PaymentTransactionResponse]],
    status_code=status.HTTP_200_OK,
    summary="Admin platform-wide transaction audit log (SKL-21)",
)
def get_admin_transaction_audit(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
) -> ApiResponse[List[PaymentTransactionResponse]]:
    """Retrieve platform-wide transactions log with RBAC administrator guard."""
    txns = subscription_service.get_admin_transactions(
        db=db, current_user=current_user, limit=limit, offset=offset
    )
    return ApiResponse[List[PaymentTransactionResponse]](
        success=True,
        message="Global transaction audit log retrieved successfully",
        data=txns,
    )
