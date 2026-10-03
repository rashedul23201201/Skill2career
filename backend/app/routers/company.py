from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import require_company, require_verified_company
from app.models.user import User
from app.schemas.auth import ApiResponse
from app.schemas.company import (
    CompanyVerificationRequest,
    CompanyVerificationStatusResponse,
    JobCreateRequest,
)
from app.services.company_service import CompanyService

router = APIRouter(prefix="/companies", tags=["Company Verification & Profile"])
company_service = CompanyService()


@router.post(
    "/verification-request",
    response_model=ApiResponse[CompanyVerificationStatusResponse],
    status_code=status.HTTP_200_OK,
    summary="Submit or update company verification dossier (SKL-2)"
)
def submit_verification_request(
    payload: CompanyVerificationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_company),
) -> ApiResponse[CompanyVerificationStatusResponse]:
    """Submit company trade license, registration number, and corporate identity for administrative verification."""
    result = company_service.submit_verification_request(
        db=db,
        user=current_user,
        payload=payload
    )
    return ApiResponse[CompanyVerificationStatusResponse](
        success=True,
        message="Company verification dossier submitted successfully. An administrator will review your documents.",
        data=result
    )


@router.get(
    "/verification-status",
    response_model=ApiResponse[CompanyVerificationStatusResponse],
    status_code=status.HTTP_200_OK,
    summary="Get current company verification status (SKL-2)"
)
def get_verification_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_company),
) -> ApiResponse[CompanyVerificationStatusResponse]:
    """Retrieve the current verification approval status, submitted dossier links, and admin feedback."""
    result = company_service.get_verification_status(db=db, user=current_user)
    return ApiResponse[CompanyVerificationStatusResponse](
        success=True,
        message="Company verification status retrieved successfully",
        data=result
    )


@router.post(
    "/jobs",
    response_model=ApiResponse[Dict[str, Any]],
    status_code=status.HTTP_201_CREATED,
    summary="Publish job / internship post (Guarded by require_verified_company) (SKL-2)"
)
def create_job_post(
    payload: JobCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_verified_company),
) -> ApiResponse[Dict[str, Any]]:
    """Gatekeeper demonstration: Only verified companies with APPROVED status can publish jobs.
    Unverified accounts receive HTTP 403 Forbidden with COMPANY_NOT_VERIFIED."""
    return ApiResponse[Dict[str, Any]](
        success=True,
        message="Job post published successfully",
        data={
            "job_id": 101,
            "company_name": current_user.company_profile.company_name if current_user.company_profile else "Verified Partner",
            "title": payload.title,
            "job_type": payload.job_type,
            "location": payload.location,
            "salary_range": payload.salary_range,
            "is_published": True,
        }
    )
