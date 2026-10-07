"""
Database Seeder Script for SKILL2CAREER
Creates initial system users (Admin, Learner, Instructor, Company) with verified profiles.
Usage:
    python seed.py
"""
import sys
import logging
from sqlalchemy import select, func
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
                    "industry": "Enterprise Software & Cloud",
                    "contact_phone": "+8801700000000",
                    "website_url": "https://brainstation-23.com",
                    "office_address": "8th Floor, Plot 2, Block A, Dhaka 1206",
                    "verification_status": "APPROVED",
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
                        industry=profile_data["industry"],
                        contact_phone=profile_data["contact_phone"],
                        website_url=profile_data["website_url"],
                        office_address=profile_data["office_address"],
                        verification_status=profile_data["verification_status"],
                    )
                    db.add(profile)
                db.commit()

            created_count += 1
            logger.info("Created user: %s (Password: %s, Role: %s)", udata["email"], udata["password"], udata["role"].value)

        logger.info("Database seeding complete. %d user(s) created.", created_count)

        # LMS Course Seeding (SKL-53)
        from app.models.course import Course, CourseModule, Lesson, CourseStatus, CourseLevel
        instructor_user = db.execute(select(User).where(User.email == "instructor@skill2career.com")).scalar_one_or_none()
        if instructor_user:
            courses_count = db.execute(select(func.count(Course.id))).scalar() or 0
            if courses_count == 0:
                logger.info("Seeding initial courses and curriculum...")
                sample_courses = [
                    {
                        "title": "Software Engineering",
                        "description": "Learn software development principles, requirements, design, testing, and project practices.",
                        "category": "Software Engineering",
                        "level": CourseLevel.BEGINNER.value,
                        "duration_weeks": 8,
                        "status": CourseStatus.PUBLISHED.value,
                        "modules": [
                            {
                                "title": "Module 1: SDLC & Agile Methodologies",
                                "lessons": [
                                    {"title": "Software Development Life Cycles", "duration": 30, "type": "video", "video_url": "https://www.youtube.com/embed/dQw4w9WgXcQ"},
                                    {"title": "Scrum Ceremonies & Jira Tracking", "duration": 45, "type": "video", "video_url": "https://www.youtube.com/embed/dQw4w9WgXcQ"},
                                ]
                            },
                            {
                                "title": "Module 2: Clean Architecture & Design Patterns",
                                "lessons": [
                                    {"title": "SOLID Principles in Practice", "duration": 50, "type": "video"},
                                    {"title": "Design Patterns: Factory & Observer", "duration": 40, "type": "reading"},
                                ]
                            }
                        ]
                    },
                    {
                        "title": "Data Structures & Algorithms",
                        "description": "Learn fundamental data structures and algorithms for technical interviews.",
                        "category": "Programming",
                        "level": CourseLevel.INTERMEDIATE.value,
                        "duration_weeks": 10,
                        "status": CourseStatus.PUBLISHED.value,
                        "modules": [
                            {
                                "title": "Module 1: Foundations of Algorithms",
                                "lessons": [
                                    {"title": "Asymptotic Analysis & Big O", "duration": 35, "type": "video"},
                                    {"title": "Recursion & Divide and Conquer", "duration": 40, "type": "video"},
                                ]
                            },
                            {
                                "title": "Module 2: Linear Data Structures",
                                "lessons": [
                                    {"title": "Lesson: Linked Lists", "duration": 30, "type": "video"},
                                    {"title": "Lesson: Theory Trees", "duration": 40, "type": "video"},
                                    {"title": "Binary Trees and Traversal Strategies", "duration": 45, "type": "video", "video_url": "https://www.youtube.com/embed/dQw4w9WgXcQ", "attachments": [{"name": "Lecture_Notes_Trees.pdf", "size": "2.4 MB"}]},
                                    {"title": "Lesson: Retrenchobe Lists", "duration": 25, "type": "reading"},
                                ]
                            },
                            {
                                "title": "Module 3: Solved Strategies",
                                "lessons": [
                                    {"title": "Dynamic Programming Fundamentals", "duration": 60, "type": "video"},
                                    {"title": "Graph Traversal: BFS & DFS", "duration": 55, "type": "video"},
                                ]
                            }
                        ]
                    },
                    {
                        "title": "Web Development",
                        "description": "Learn the fundamentals of modern web development.",
                        "category": "Web Development",
                        "level": CourseLevel.BEGINNER.value,
                        "duration_weeks": 8,
                        "status": CourseStatus.PUBLISHED.value,
                        "modules": [
                            {
                                "title": "Module 1: Modern JavaScript & React",
                                "lessons": [
                                    {"title": "ES6+ Modern JavaScript", "duration": 40, "type": "video"},
                                    {"title": "React Hooks & State Management", "duration": 50, "type": "video"},
                                ]
                            }
                        ]
                    },
                    {
                        "title": "Database Management",
                        "description": "Learn SQL, database design, and database management concepts.",
                        "category": "Database",
                        "level": CourseLevel.INTERMEDIATE.value,
                        "duration_weeks": 6,
                        "status": CourseStatus.PUBLISHED.value,
                        "modules": [
                            {
                                "title": "Module 1: Relational Modeling & SQL",
                                "lessons": [
                                    {"title": "Relational Modeling & 3NF", "duration": 45, "type": "video"},
                                    {"title": "Indexing, Query Plans & Optimization", "duration": 50, "type": "video"},
                                ]
                            }
                        ]
                    },
                    {
                        "title": "Data Structures & Algorithms in Python",
                        "description": "Complete Python-focused DSA masterclass tailored for technical screening assessments.",
                        "category": "Programming",
                        "level": CourseLevel.INTERMEDIATE.value,
                        "duration_weeks": 10,
                        "status": CourseStatus.DRAFT.value,
                        "modules": [
                            {
                                "title": "Module 1: Foundations of Algorithms",
                                "lessons": [
                                    {"title": "Algorithm Analysis in Python", "duration": 30, "type": "video"},
                                ]
                            },
                            {
                                "title": "Module 2: Linear Data Structures",
                                "lessons": [
                                    {"title": "Lesson: Linked Lists", "duration": 35, "type": "video"},
                                    {"title": "Lesson: Theory Trees", "duration": 40, "type": "video"},
                                    {"title": "Binary Trees and Traversal Strategies", "duration": 45, "type": "video", "attachments": [{"name": "Lecture_Notes_Trees.pdf", "size": "2.4 MB"}]},
                                ]
                            }
                        ]
                    }
                ]

                for c_data in sample_courses:
                    course = Course(
                        instructor_id=instructor_user.id,
                        title=c_data["title"],
                        description=c_data["description"],
                        category=c_data["category"],
                        level=c_data["level"],
                        price=0.0,
                        is_free=True,
                        duration_weeks=c_data["duration_weeks"],
                        status=c_data["status"],
                    )
                    db.add(course)
                    db.flush()

                    for m_idx, m_data in enumerate(c_data["modules"]):
                        module = CourseModule(
                            course_id=course.id,
                            title=m_data["title"],
                            order_index=m_idx,
                        )
                        db.add(module)
                        db.flush()

                        for l_idx, l_data in enumerate(m_data["lessons"]):
                            lesson = Lesson(
                                course_id=course.id,
                                module_id=module.id,
                                title=l_data["title"],
                                content_type=l_data.get("type", "video"),
                                video_url=l_data.get("video_url"),
                                attachments=l_data.get("attachments", []),
                                duration_minutes=l_data.get("duration", 30),
                                order_index=l_idx,
                            )
                            db.add(lesson)

                db.commit()
                logger.info("Successfully seeded %d sample courses with curriculum.", len(sample_courses))

    except Exception as e:
        db.rollback()
        logger.error("Seeding failed: %s", str(e))
        sys.exit(1)
    finally:
        db.close()



if __name__ == "__main__":
    seed_database()
