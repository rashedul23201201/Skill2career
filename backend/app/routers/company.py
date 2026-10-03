from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, UploadFile, File, Request, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import (
    require_role,
    require_admin,
    require_company,
    require_verified_company,
)
from app.models.user import User, UserRole
from app.schemas.auth import ApiResponse
from app.schemas.company import (
    CompanyProfileUpdateRequest,
    CompanyProfileResponse,
    PublicCompanyProfileResponse,
    AssetUploadResponse,
    CompanyModerationRequest,
    CompanyVerificationRequest,
    CompanyVerificationStatusResponse,
    JobCreateRequest,
)
from app.services.company_service import CompanyService

router = APIRouter(prefix="/companies", tags=["Company Profile & Verification"])
company_service = CompanyService()


# ==========================================
# SKL-3: Profile Management & Branding Assets
# ==========================================

@router.get(
    "/profile/me",
    response_model=ApiResponse[CompanyProfileResponse],
    status_code=status.HTTP_200_OK,
    summary="Get authenticated company's complete profile (SKL-3)"
)
@router.get(
    "/profile",
    response_model=ApiResponse[CompanyProfileResponse],
    status_code=status.HTTP_200_OK,
    include_in_schema=False
)
def get_company_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.COMPANY, UserRole.ADMIN)),
) -> ApiResponse[CompanyProfileResponse]:
    """Retrieve full company profile for the authenticated company organization."""
    data = company_service.get_profile(db=db, user=current_user)
    return ApiResponse[CompanyProfileResponse](
        success=True,
        message="Company profile retrieved successfully",
        data=data,
    )


@router.put(
    "/profile/me",
    response_model=ApiResponse[CompanyProfileResponse],
    status_code=status.HTTP_200_OK,
    summary="Update company profile details with strict URI validation (SKL-3)"
)
@router.put(
    "/profile",
    response_model=ApiResponse[CompanyProfileResponse],
    status_code=status.HTTP_200_OK,
    include_in_schema=False
)
def update_company_profile(
    payload: CompanyProfileUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.COMPANY, UserRole.ADMIN)),
) -> ApiResponse[CompanyProfileResponse]:
    """Update company details (tagline, size, address, social links, website) and persist to database."""
    updated = company_service.update_profile(db=db, user=current_user, payload=payload)
    return ApiResponse[CompanyProfileResponse](
        success=True,
        message="Company profile updated successfully",
        data=updated,
    )


@router.post(
    "/profile/logo",
    response_model=ApiResponse[AssetUploadResponse],
    status_code=status.HTTP_200_OK,
    summary="Upload company brand logo image (PNG/JPG/WEBP, max 5MB) (SKL-3)"
)
def upload_company_logo(
    file: UploadFile = File(..., description="Logo image in PNG, JPG, or WEBP format (max 5MB)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.COMPANY, UserRole.ADMIN)),
) -> ApiResponse[AssetUploadResponse]:
    """Upload company logo with binary header validation, size limitation, and storage persistence."""
    result = company_service.upload_logo(db=db, user=current_user, file=file)
    return ApiResponse[AssetUploadResponse](
        success=True,
        message=result.message,
        data=result,
    )


@router.post(
    "/profile/banner",
    response_model=ApiResponse[AssetUploadResponse],
    status_code=status.HTTP_200_OK,
    summary="Upload company cover banner image (PNG/JPG/WEBP, max 5MB) (SKL-3)"
)
def upload_company_banner(
    file: UploadFile = File(..., description="Cover banner image in PNG, JPG, or WEBP format (max 5MB)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.COMPANY, UserRole.ADMIN)),
) -> ApiResponse[AssetUploadResponse]:
    """Upload company cover banner image with binary header validation and storage persistence."""
    result = company_service.upload_banner(db=db, user=current_user, file=file)
    return ApiResponse[AssetUploadResponse](
        success=True,
        message=result.message,
        data=result,
    )


@router.get(
    "/{company_id}/public",
    response_model=ApiResponse[PublicCompanyProfileResponse],
    status_code=status.HTTP_200_OK,
    summary="Public company profile view accessible by learners and guests (SKL-3)"
)
def get_public_company_profile(
    company_id: int,
    db: Session = Depends(get_db),
) -> ApiResponse[PublicCompanyProfileResponse]:
    """
    Public endpoint displaying verified company details, branding assets,
    and active job listings without exposing internal contact information.
    """
    public_data = company_service.get_public_profile(db=db, company_id=company_id)
    return ApiResponse[PublicCompanyProfileResponse](
        success=True,
        message="Public company profile retrieved successfully",
        data=public_data,
    )


@router.get(
    "/assets/{asset_type}/{filename}",
    status_code=status.HTTP_200_OK,
    summary="Serve uploaded company branding images (logo / banner)"
)
def serve_company_asset(
    asset_type: str,
    filename: str,
) -> FileResponse:
    """Serve company logo or banner asset securely."""
    return company_service.serve_asset(asset_type=asset_type, filename=filename)


@router.patch(
    "/{company_id}/moderate",
    response_model=ApiResponse[CompanyProfileResponse],
    status_code=status.HTTP_200_OK,
    summary="Admin moderation for company profile and verification (SKL-3 / SKL-50)"
)
def moderate_company_via_company_route(
    company_id: int,
    payload: CompanyModerationRequest,
    request: Request,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
) -> ApiResponse[CompanyProfileResponse]:
    """Administrative content moderation endpoint directly within the company router."""
    client_ip = request.client.host if request.client else None
    result = company_service.moderate_company(
        db=db,
        admin_user=admin_user,
        company_id=company_id,
        payload=payload,
        ip_address=client_ip
    )
    return ApiResponse[CompanyProfileResponse](
        success=True,
        message="Company moderated successfully",
        data=result,
    )


# ===============================================
# SKL-2: Company Registration & Verification APIs
# ===============================================

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
