"""
Database Seeder Script for SKILL2CAREER
Creates initial system users (Admin, Learner, Instructor, Company) with verified profiles.
Usage:
    python seed.py
"""
import sys
import logging
from sqlalchemy import select
from app.database.session import SessionLocal
from app.models.user import User, UserRole
from app.models.profile import LearnerProfile, InstructorProfile, CompanyProfile
from app.core.security import hash_password

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("seed")


def seed_database():
    db = SessionLocal()
    try:
        logger.info("Checking database for existing seed accounts...")

        users_to_create = [
            {
                "email": "admin@skill2career.com",
                "password": "Admin12345!",
                "first_name": "Platform",
                "last_name": "Admin",
                "role": UserRole.ADMIN,
                "is_verified": True,
                "is_active": True,
            },
            {
                "email": "learner@skill2career.com",
                "password": "Learner12345!",
                "first_name": "Tanvir",
                "last_name": "Hasan",
                "role": UserRole.LEARNER,
                "is_verified": True,
                "is_active": True,
                "profile": {
                    "type": "learner",
                    "institution": "Dhaka University",
                    "department": "Computer Science & Engineering",
                    "target_role": "Full-Stack Software Engineer",
                }
            },
            {
                "email": "instructor@skill2career.com",
                "password": "Instructor12345!",
                "first_name": "Dr. Farhana",
                "last_name": "Kabir",
                "role": UserRole.INSTRUCTOR,
                "is_verified": True,
                "is_active": True,
                "profile": {
                    "type": "instructor",
                    "qualification": "Ph.D. in Computer Science",
                    "expertise_domain": "System Design, Algorithms & Python",
                    "years_experience": "10+ Years",
                    "onboarding_status": "APPROVED",
                }
            },
            {
                "email": "company@skill2career.com",
                "password": "Company12345!",
                "first_name": "Lead",
                "last_name": "Recruiter",
                "role": UserRole.COMPANY,
                "is_verified": True,
                "is_active": True,
                "profile": {
                    "type": "company",
                    "company_name": "Brain Station 23 Ltd.",
                    "tagline": "Global Digital Solutions & Enterprise Engineering Partner",
                    "description": "Leading custom software development and IT solutions provider in Bangladesh, serving global Fortune 500 and enterprise clients with 700+ engineers.",
                    "industry": "Enterprise Software & Cloud",
                    "company_size": "500+",
                    "contact_phone": "+8801700000000",
                    "website_url": "https://brainstation-23.com",
                    "office_address": "8th Floor, Plot 2, Block A, Dhaka 1206",
                    "social_links": {
                        "linkedin": "https://linkedin.com/company/brainstation23",
                        "github": "https://github.com/brainstation-23",
                        "facebook": "https://facebook.com/brainstation23",
                    },
                    "trade_license_url": "https://storage.skill2career.com/licenses/bs23_license.pdf",
                    "registration_number": "TRAD/DNCC/001122/2024",
                    "verification_status": "APPROVED",
                }
            },
            {
                "email": "pending.company@skill2career.com",
                "password": "Company12345!",
                "first_name": "Sabbir",
                "last_name": "Hossain",
                "role": UserRole.COMPANY,
                "is_verified": False,
                "is_active": True,
                "profile": {
                    "type": "company",
                    "company_name": "Chaldal Technologies Ltd.",
                    "industry": "E-Commerce & Logistics",
                    "contact_person": "Sabbir Hossain, Head of Talent",
                    "contact_phone": "+8801711223344",
                    "website_url": "https://chaldal.tech",
                    "office_address": "House 12, Road 5, Dhanmondi, Dhaka",
                    "location": "Dhaka, Bangladesh",
                    "company_size": "51-200",
                    "trade_license_url": "https://storage.skill2career.com/licenses/chaldal_trade_lic_2026.pdf",
                    "registration_number": "TRAD/DSCC/098765/2026",
                    "verification_status": "PENDING",
                }
            }
        ]

        created_count = 0
        for udata in users_to_create:
            existing = db.execute(select(User).where(User.email == udata["email"])).scalar_one_or_none()
            if existing:
                logger.info("User already exists: %s (%s)", existing.email, existing.role.value)
                continue

            user = User(
                email=udata["email"],
                hashed_password=hash_password(udata["password"]),
                first_name=udata["first_name"],
                last_name=udata["last_name"],
                role=udata["role"],
                is_verified=udata["is_verified"],
                is_active=udata["is_active"],
            )
            db.add(user)
            db.commit()
            db.refresh(user)

            # Profile creation
            profile_data = udata.get("profile")
            if profile_data:
                ptype = profile_data.get("type")
                if ptype == "learner":
                    profile = LearnerProfile(
                        user_id=user.id,
                        institution=profile_data["institution"],
                        department=profile_data["department"],
                        target_role=profile_data["target_role"],
                        completion_pct=85,
                    )
                    db.add(profile)
                elif ptype == "instructor":
                    profile = InstructorProfile(
                        user_id=user.id,
                        qualification=profile_data["qualification"],
                        expertise_domain=profile_data["expertise_domain"],
                        years_experience=profile_data["years_experience"],
                        onboarding_status=profile_data["onboarding_status"],
                    )
                    db.add(profile)
                elif ptype == "company":
                    profile = CompanyProfile(
                        user_id=user.id,
                        company_name=profile_data["company_name"],
                        tagline=profile_data.get("tagline"),
                        description=profile_data.get("description"),
                        industry=profile_data.get("industry"),
                        contact_person=profile_data.get("contact_person"),
                        contact_phone=profile_data.get("contact_phone"),
                        website_url=profile_data.get("website_url"),
                        office_address=profile_data.get("office_address"),
                        location=profile_data.get("location"),
                        company_size=profile_data.get("company_size"),
                        social_links=profile_data.get("social_links", {}),
                        trade_license_url=profile_data.get("trade_license_url"),
                        registration_number=profile_data.get("registration_number"),
                        verification_status=profile_data["verification_status"],
                    )
                    db.add(profile)
                db.commit()

            created_count += 1
            logger.info("Created user: %s (Password: %s, Role: %s)", udata["email"], udata["password"], udata["role"].value)

        logger.info("Database seeding complete. %d user(s) created.", created_count)

    except Exception as e:
        db.rollback()
        logger.error("Seeding failed: %s", str(e))
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
