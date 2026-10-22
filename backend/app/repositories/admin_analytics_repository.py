"""Repository aggregating platform-wide executive analytics, financial telemetry, and recruitment pipelines (SKL-23)."""

from datetime import datetime, timezone
from typing import Dict, Any, List
from sqlalchemy import select, func, desc
from sqlalchemy.orm import Session, joinedload

from app.models.user import User, UserRole
from app.models.profile import CompanyProfile, InstructorProfile
from app.models.course import Course, CourseStatus
from app.models.enrollment import CourseEnrollment
from app.models.job import JobPosting, JobStatus
from app.models.application import JobApplication, ApplicationStatus
from app.models.interview import InterviewRequest, InterviewStatus
from app.models.subscription import (
    PaymentTransaction,
    PaymentStatus,
    UserSubscription,
    SubscriptionStatus,
    SubscriptionPlan,
)
from app.models.audit_log import AuditLog
from app.schemas.admin import (
    AdminAnalyticsUserOverview,
    AdminAnalyticsCompanyOverview,
    AdminAnalyticsCourseOverview,
    AdminAnalyticsRecruitmentOverview,
    AdminAnalyticsRevenueOverview,
    AdminAnalyticsModerationOverview,
    PlatformActivityItem,
    AdminOverviewAnalyticsResponse,
    GatewayRevenueItem,
    PlanRevenueItem,
    RecentTransactionAnalyticsItem,
    AdminRevenueAnalyticsResponse,
    TopHiringCompanyItem,
    RecentJobPostingItem,
    AdminRecruitmentSummaryResponse,
)


class AdminAnalyticsRepository:
    """Provides high-performance aggregation queries for central executive admin monitoring."""

    @staticmethod
    def get_overview_analytics(db: Session) -> AdminOverviewAnalyticsResponse:
        """Aggregate platform KPIs, user distribution, recruitment volume, live revenue, and moderation backlogs."""
        # 1. Users Breakdown
        total_users = db.execute(select(func.count(User.id))).scalar() or 0
        active_users = db.execute(select(func.count(User.id)).where(User.is_active == True)).scalar() or 0  # noqa: E712
        inactive_users = total_users - active_users

        role_rows = db.execute(select(User.role, func.count(User.id)).group_by(User.role)).all()
        role_dict = {"LEARNER": 0, "INSTRUCTOR": 0, "COMPANY": 0, "ADMIN": 0}
        for r, count in role_rows:
            key = r.value if hasattr(r, "value") else str(r)
            role_dict[key] = count

        users_overview = AdminAnalyticsUserOverview(
            total=total_users,
            active=active_users,
            inactive=inactive_users,
            role_breakdown=role_dict,
        )

        # 2. Company Verification Status
        total_companies = db.execute(select(func.count(CompanyProfile.id))).scalar() or 0
        verified_companies = (
            db.execute(
                select(func.count(CompanyProfile.id)).where(CompanyProfile.verification_status == "APPROVED")
            ).scalar()
            or 0
        )
        pending_companies = (
            db.execute(
                select(func.count(CompanyProfile.id)).where(CompanyProfile.verification_status == "PENDING")
            ).scalar()
            or 0
        )
        rejected_companies = (
            db.execute(
                select(func.count(CompanyProfile.id)).where(CompanyProfile.verification_status == "REJECTED")
            ).scalar()
            or 0
        )

        companies_overview = AdminAnalyticsCompanyOverview(
            total=total_companies,
            verified=verified_companies,
            pending_verification=pending_companies,
            rejected=rejected_companies,
        )

        # 3. Courses & Learning Modules
        total_courses = db.execute(select(func.count(Course.id))).scalar() or 0
        published_courses = (
            db.execute(select(func.count(Course.id)).where(Course.status == CourseStatus.PUBLISHED.value)).scalar()
            or 0
        )
        draft_courses = (
            db.execute(select(func.count(Course.id)).where(Course.status == CourseStatus.DRAFT.value)).scalar() or 0
        )
        total_enrollments = db.execute(select(func.count(CourseEnrollment.id))).scalar() or 0

        courses_overview = AdminAnalyticsCourseOverview(
            total=total_courses,
            published=published_courses,
            draft=draft_courses,
            total_enrollments=total_enrollments,
        )

        # 4. Recruitment & Jobs Pipeline
        total_jobs = db.execute(select(func.count(JobPosting.id))).scalar() or 0
        active_jobs = (
            db.execute(select(func.count(JobPosting.id)).where(JobPosting.status == JobStatus.ACTIVE.value)).scalar()
            or 0
        )
        total_applications = db.execute(select(func.count(JobApplication.id))).scalar() or 0

        recruitment_overview = AdminAnalyticsRecruitmentOverview(
            total_jobs=total_jobs,
            active_jobs=active_jobs,
            total_applications=total_applications,
        )

        # 5. Live Revenue & Monetization
        total_revenue_raw = db.execute(
            select(func.coalesce(func.sum(PaymentTransaction.amount), 0)).where(
                PaymentTransaction.status == PaymentStatus.SUCCESS.value
            )
        ).scalar()
        total_revenue = float(total_revenue_raw or 0.0)

        successful_transactions = (
            db.execute(
                select(func.count(PaymentTransaction.id)).where(
                    PaymentTransaction.status == PaymentStatus.SUCCESS.value
                )
            ).scalar()
            or 0
        )

        active_subscriptions = (
            db.execute(
                select(func.count(UserSubscription.id)).where(
                    UserSubscription.status == SubscriptionStatus.ACTIVE.value
                )
            ).scalar()
            or 0
        )

        revenue_overview = AdminAnalyticsRevenueOverview(
            total_revenue=total_revenue,
            currency="BDT",
            successful_transactions=successful_transactions,
            active_subscriptions=active_subscriptions,
        )

        # 6. Moderation Backlogs
        pending_instructors = (
            db.execute(
                select(func.count(InstructorProfile.id)).where(
                    InstructorProfile.onboarding_status == "PENDING_REVIEW"
                )
            ).scalar()
            or 0
        )

        pending_courses = (
            db.execute(
                select(func.count(Course.id)).where(Course.moderation_status == "PENDING_REVIEW")
            ).scalar()
            or 0
        )

        pending_approvals = pending_companies + pending_instructors + pending_courses

        moderation_overview = AdminAnalyticsModerationOverview(
            pending_approvals=pending_approvals,
            pending_companies=pending_companies,
            pending_instructors=pending_instructors,
            pending_courses=pending_courses,
        )

        # 7. Recent Platform Activity Stream (matching Admin Dashboard.png)
        activity_items: List[PlatformActivityItem] = []

        # Latest Company Registrations
        recent_comps = (
            db.execute(select(CompanyProfile).order_by(CompanyProfile.created_at.desc()).limit(4))
            .scalars()
            .all()
        )
        for c in recent_comps:
            activity_items.append(
                PlatformActivityItem(
                    id=f"company-{c.id}",
                    activity_type="COMPANY_REGISTRATION",
                    title=f"New company registration — {c.company_name}",
                    description=f"Industry: {c.industry or 'General'} · Status: {c.verification_status}",
                    timestamp=c.created_at,
                    badge_color="green",
                )
            )

        # Latest Job Postings
        recent_jobs = (
            db.execute(select(JobPosting).order_by(JobPosting.created_at.desc()).limit(4))
            .scalars()
            .all()
        )
        for j in recent_jobs:
            activity_items.append(
                PlatformActivityItem(
                    id=f"job-{j.id}",
                    activity_type="JOB_POSTING",
                    title=f"New job post awaiting approval — {j.title}",
                    description=f"Type: {j.posting_type} · Mode: {j.work_mode} · Status: {j.status}",
                    timestamp=j.created_at,
                    badge_color="blue",
                )
            )

        # Latest Courses
        recent_courses = (
            db.execute(select(Course).order_by(Course.created_at.desc()).limit(4))
            .scalars()
            .all()
        )
        for crs in recent_courses:
            activity_items.append(
                PlatformActivityItem(
                    id=f"course-{crs.id}",
                    activity_type="COURSE_PUBLISHED",
                    title=f"New course published — {crs.title}",
                    description=f"Category: {crs.category} · Status: {crs.status}",
                    timestamp=crs.created_at,
                    badge_color="blue",
                )
            )

        # Latest Successful Transactions
        recent_txs = (
            db.execute(
                select(PaymentTransaction)
                .where(PaymentTransaction.status == PaymentStatus.SUCCESS.value)
                .order_by(PaymentTransaction.created_at.desc())
                .limit(4)
            )
            .scalars()
            .all()
        )
        for tx in recent_txs:
            activity_items.append(
                PlatformActivityItem(
                    id=f"txn-{tx.id}",
                    activity_type="TRANSACTION",
                    title=f"Payment received — ৳{float(tx.amount):,.2f}",
                    description=f"Ref: {tx.transaction_ref} via {tx.gateway}",
                    timestamp=tx.created_at,
                    badge_color="emerald",
                )
            )

        # Latest Administrative Audits
        recent_audits = (
            db.execute(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(3))
            .scalars()
            .all()
        )
        for a in recent_audits:
            reason = a.details.get("reason", "Administrative action") if a.details else "Security audit record"
            activity_items.append(
                PlatformActivityItem(
                    id=f"audit-{a.id}",
                    activity_type="AUDIT_ACTION",
                    title=f"Administrative action — {a.action.replace('_', ' ').title()}",
                    description=reason,
                    timestamp=a.created_at,
                    badge_color="purple",
                )
            )

        # Sort all activities by timestamp descending and take top 10
        activity_items.sort(key=lambda x: x.timestamp, reverse=True)
        top_activities = activity_items[:10]

        return AdminOverviewAnalyticsResponse(
            users=users_overview,
            companies=companies_overview,
            courses=courses_overview,
            recruitment=recruitment_overview,
            revenue=revenue_overview,
            moderation=moderation_overview,
            recent_activity=top_activities,
        )

    @staticmethod
    def get_revenue_analytics(db: Session) -> AdminRevenueAnalyticsResponse:
        """Compute platform-wide financial revenue, gateway distributions, and subscription plans (SKL-20/SKL-23)."""
        # Overall Revenue & Counts
        total_rev_raw = db.execute(
            select(func.coalesce(func.sum(PaymentTransaction.amount), 0)).where(
                PaymentTransaction.status == PaymentStatus.SUCCESS.value
            )
        ).scalar()
        total_revenue = float(total_rev_raw or 0.0)

        total_tx = db.execute(select(func.count(PaymentTransaction.id))).scalar() or 0
        successful_tx = (
            db.execute(
                select(func.count(PaymentTransaction.id)).where(
                    PaymentTransaction.status == PaymentStatus.SUCCESS.value
                )
            ).scalar()
            or 0
        )
        pending_tx = (
            db.execute(
                select(func.count(PaymentTransaction.id)).where(
                    PaymentTransaction.status == PaymentStatus.PENDING.value
                )
            ).scalar()
            or 0
        )
        failed_tx = (
            db.execute(
                select(func.count(PaymentTransaction.id)).where(
                    PaymentTransaction.status.in_([PaymentStatus.FAILED.value, PaymentStatus.REVERSED.value])
                )
            ).scalar()
            or 0
        )

        success_rate = round((successful_tx / total_tx * 100), 2) if total_tx > 0 else 0.0

        # Subscriptions Breakdown
        active_subs = (
            db.execute(
                select(func.count(UserSubscription.id)).where(
                    UserSubscription.status == SubscriptionStatus.ACTIVE.value
                )
            ).scalar()
            or 0
        )

        sub_rows = db.execute(
            select(UserSubscription.status, func.count(UserSubscription.id)).group_by(UserSubscription.status)
        ).all()
        subs_by_status = {"ACTIVE": 0, "EXPIRED": 0, "CANCELLED": 0}
        for s, count in sub_rows:
            subs_by_status[str(s).upper()] = count

        # Gateway Revenue Distribution
        gw_rows = db.execute(
            select(
                PaymentTransaction.gateway,
                func.count(PaymentTransaction.id),
                func.coalesce(func.sum(PaymentTransaction.amount), 0),
            )
            .where(PaymentTransaction.status == PaymentStatus.SUCCESS.value)
            .group_by(PaymentTransaction.gateway)
        ).all()

        gateway_list = [
            GatewayRevenueItem(
                gateway=str(gw or "UNKNOWN"),
                count=int(cnt),
                total_amount=float(amt),
            )
            for gw, cnt, amt in gw_rows
        ]

        # Plan Distribution
        plans = db.execute(select(SubscriptionPlan)).scalars().all()
        plan_list: List[PlanRevenueItem] = []
        for p in plans:
            sub_count = (
                db.execute(select(func.count(UserSubscription.id)).where(UserSubscription.plan_id == p.id)).scalar()
                or 0
            )
            rev_raw = (
                db.execute(
                    select(func.coalesce(func.sum(PaymentTransaction.amount), 0))
                    .join(UserSubscription, PaymentTransaction.subscription_id == UserSubscription.id)
                    .where(
                        UserSubscription.plan_id == p.id,
                        PaymentTransaction.status == PaymentStatus.SUCCESS.value,
                    )
                ).scalar()
                or 0.0
            )
            plan_list.append(
                PlanRevenueItem(
                    plan_code=p.code,
                    plan_name=p.name,
                    subscriber_count=int(sub_count),
                    total_revenue=float(rev_raw),
                )
            )

        # Recent 10 Transactions
        txns = (
            db.execute(
                select(PaymentTransaction)
                .options(joinedload(PaymentTransaction.user))
                .order_by(PaymentTransaction.created_at.desc())
                .limit(10)
            )
            .scalars()
            .all()
        )

        recent_tx_list = [
            RecentTransactionAnalyticsItem(
                id=t.id,
                transaction_ref=t.transaction_ref,
                user_name=f"{t.user.first_name} {t.user.last_name}".strip() if t.user else "Platform User",
                user_email=t.user.email if t.user else "user@example.com",
                amount=float(t.amount),
                currency=t.currency or "BDT",
                gateway=t.gateway or "UNKNOWN",
                status=t.status,
                created_at=t.created_at,
            )
            for t in txns
        ]

        return AdminRevenueAnalyticsResponse(
            total_revenue=total_revenue,
            currency="BDT",
            total_transactions=total_tx,
            successful_transactions=successful_tx,
            pending_transactions=pending_tx,
            failed_transactions=failed_tx,
            success_rate=success_rate,
            active_subscriptions=active_subs,
            subscriptions_by_status=subs_by_status,
            revenue_by_gateway=gateway_list,
            revenue_by_plan=plan_list,
            recent_transactions=recent_tx_list,
        )

    @staticmethod
    def get_recruitment_summary(db: Session) -> AdminRecruitmentSummaryResponse:
        """Aggregate platform recruitment activity, application funnel, and hiring partner metrics (SKL-23)."""
        # Job counts
        total_jobs = db.execute(select(func.count(JobPosting.id))).scalar() or 0
        active_jobs = (
            db.execute(select(func.count(JobPosting.id)).where(JobPosting.status == JobStatus.ACTIVE.value)).scalar()
            or 0
        )
        closed_jobs = (
            db.execute(select(func.count(JobPosting.id)).where(JobPosting.status == JobStatus.CLOSED.value)).scalar()
            or 0
        )
        draft_jobs = (
            db.execute(select(func.count(JobPosting.id)).where(JobPosting.status == JobStatus.DRAFT.value)).scalar()
            or 0
        )

        # Application counts and status distribution
        total_applications = db.execute(select(func.count(JobApplication.id))).scalar() or 0

        app_rows = db.execute(
            select(JobApplication.status, func.count(JobApplication.id)).group_by(JobApplication.status)
        ).all()
        app_status_dict = {
            "SUBMITTED": 0,
            "UNDER_REVIEW": 0,
            "SHORTLISTED": 0,
            "INTERVIEW_SCHEDULED": 0,
            "OFFERED": 0,
            "REJECTED": 0,
            "WITHDRAWN": 0,
        }
        for s, cnt in app_rows:
            key = str(s).upper()
            if key in app_status_dict:
                app_status_dict[key] = cnt
            else:
                app_status_dict[key] = cnt

        # Interview counts and status distribution
        total_interviews = db.execute(select(func.count(InterviewRequest.id))).scalar() or 0
        int_rows = db.execute(
            select(InterviewRequest.status, func.count(InterviewRequest.id)).group_by(InterviewRequest.status)
        ).all()
        int_status_dict = {
            "PENDING": 0,
            "SCHEDULED": 0,
            "RESCHEDULE_REQUESTED": 0,
            "COMPLETED": 0,
            "CANCELLED": 0,
        }
        for s, cnt in int_rows:
            key = str(s).upper()
            if key in int_status_dict:
                int_status_dict[key] = cnt
            else:
                int_status_dict[key] = cnt

        # Top 5 Hiring Companies by Job and Application volume
        comp_rows = (
            db.execute(
                select(
                    User.id,
                    CompanyProfile.company_name,
                    func.count(JobPosting.id).label("job_count"),
                )
                .join(CompanyProfile, CompanyProfile.user_id == User.id)
                .join(JobPosting, JobPosting.company_id == User.id, isouter=True)
                .group_by(User.id, CompanyProfile.company_name)
                .order_by(desc("job_count"))
                .limit(5)
            )
            .all()
        )

        top_companies: List[TopHiringCompanyItem] = []
        for uid, cname, jcnt in comp_rows:
            app_cnt = (
                db.execute(
                    select(func.count(JobApplication.id))
                    .join(JobPosting, JobApplication.job_id == JobPosting.id)
                    .where(JobPosting.company_id == uid)
                ).scalar()
                or 0
            )
            active_jcnt = (
                db.execute(
                    select(func.count(JobPosting.id)).where(
                        JobPosting.company_id == uid, JobPosting.status == JobStatus.ACTIVE.value
                    )
                ).scalar()
                or 0
            )
            top_companies.append(
                TopHiringCompanyItem(
                    company_id=uid,
                    company_name=cname or "Employer",
                    active_jobs=int(active_jcnt),
                    total_applications=int(app_cnt),
                )
            )

        # Recent 10 Job Postings
        jobs = (
            db.execute(
                select(JobPosting)
                .options(joinedload(JobPosting.company))
                .order_by(JobPosting.created_at.desc())
                .limit(10)
            )
            .scalars()
            .all()
        )

        recent_jobs_list: List[RecentJobPostingItem] = []
        for j in jobs:
            comp_name = "Company"
            if j.company and hasattr(j.company, "company_profile") and j.company.company_profile:
                comp_name = j.company.company_profile.company_name
            elif j.company:
                comp_name = f"{j.company.first_name} {j.company.last_name}".strip()

            apps_cnt = (
                db.execute(select(func.count(JobApplication.id)).where(JobApplication.job_id == j.id)).scalar()
                or 0
            )

            recent_jobs_list.append(
                RecentJobPostingItem(
                    id=j.id,
                    title=j.title,
                    company_name=comp_name,
                    posting_type=j.posting_type,
                    category=j.category,
                    work_mode=j.work_mode,
                    status=j.status,
                    applications_count=int(apps_cnt),
                    created_at=j.created_at,
                )
            )

        return AdminRecruitmentSummaryResponse(
            total_jobs=total_jobs,
            active_jobs=active_jobs,
            closed_jobs=closed_jobs,
            draft_jobs=draft_jobs,
            total_applications=total_applications,
            applications_by_status=app_status_dict,
            total_interviews=total_interviews,
            interviews_by_status=int_status_dict,
            top_hiring_companies=top_companies,
            recent_job_postings=recent_jobs_list,
        )
