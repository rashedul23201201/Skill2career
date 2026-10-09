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
from app.models.job import JobPosting, JobStatus
from app.models.screening import (
    ScreeningQuestion,
    CandidateEvaluation,
    QuestionType,
    DealBreakerRule,
    CandidateStatus,
)
from app.models.forum import ForumCategory, ForumPost, ForumComment
from app.models.enrollment import CourseEnrollment, LessonProgress, EnrollmentStatus
from app.models.application import JobApplication, ApplicationStatus
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
                        resume_url="/uploads/resumes/Tanvir_Hasan_Resume.pdf",
                        resume_filename="Tanvir_Hasan_Resume.pdf",
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

        # Recruitment Job Posting Seeding (SKL-4)
        from app.models.job import JobPosting, JobStatus, JobPostingType, JobWorkMode, JobExperienceLevel
        company_user = db.execute(select(User).where(User.email == "company@skill2career.com")).scalar_one_or_none()
        if company_user:
            jobs_count = db.execute(select(func.count(JobPosting.id))).scalar() or 0
            if jobs_count == 0:
                logger.info("Seeding initial job postings matching UI designs...")
                sample_jobs = [
                    {
                        "title": "Junior Software Developer",
                        "posting_type": JobPostingType.JOB.value,
                        "work_mode": JobWorkMode.ON_SITE.value,
                        "location": "Dhaka",
                        "description": "We are looking for a passionate Junior Software Developer to join our core backend engineering team. You will build and scale high-throughput REST APIs and collaborate with senior architects.",
                        "requirements": "Strong foundation in data structures and object-oriented programming. Hands-on experience with Java or Python. Familiarity with SQL and relational database modeling.",
                        "skills": ["Java", "Python", "SQL"],
                        "compensation": "৳35K – ৳50K",
                        "experience_level": JobExperienceLevel.ENTRY_LEVEL.value,
                        "category": "Software Engineering",
                        "status": JobStatus.ACTIVE.value,
                        "applications_count": 42,
                    },
                    {
                        "title": "Software Engineering Intern",
                        "posting_type": JobPostingType.INTERNSHIP.value,
                        "work_mode": JobWorkMode.ON_SITE.value,
                        "location": "Dhaka",
                        "description": "A 3-month immersive internship for university undergraduates or recent graduates. Gain production experience with modern distributed systems and fintech pipelines.",
                        "requirements": "Proficiency in C++ or Python. Solid grasp of algorithmic problem-solving and version control using Git.",
                        "skills": ["C++", "Git", "Problem Solving"],
                        "compensation": "3 Months · ৳20K / month",
                        "duration": "3 Months",
                        "experience_level": JobExperienceLevel.INTERNSHIP.value,
                        "category": "Software Engineering",
                        "status": JobStatus.ACTIVE.value,
                        "applications_count": 31,
                    },
                    {
                        "title": "Frontend Developer",
                        "posting_type": JobPostingType.JOB.value,
                        "work_mode": JobWorkMode.HYBRID.value,
                        "location": "Dhaka",
                        "description": "Join our frontend engineering guild to build responsive, accessible, and high-performance web applications using React, TailwindCSS, and TypeScript.",
                        "requirements": "Demonstrated expertise with React 18/19, TailwindCSS, TypeScript, and state management. Strong eye for UI aesthetics and UX precision.",
                        "skills": ["React", "Tailwind", "TypeScript"],
                        "compensation": "৳50K – ৳70K",
                        "experience_level": JobExperienceLevel.JUNIOR.value,
                        "category": "Web Development",
                        "status": JobStatus.ACTIVE.value,
                        "applications_count": 19,
                    },
                    {
                        "title": "QA & Automation Intern",
                        "posting_type": JobPostingType.INTERNSHIP.value,
                        "work_mode": JobWorkMode.REMOTE.value,
                        "location": "Remote, Bangladesh",
                        "description": "6-month QA internship working directly with quality engineers to write automated test scripts, run API validation suites, and document regression test plans.",
                        "requirements": "Understanding of software testing lifecycles, basic Python scripting, Selenium or Playwright, and API testing with Postman.",
                        "skills": ["Python", "Selenium", "Postman"],
                        "compensation": "6 Months · ৳18K / month",
                        "duration": "6 Months",
                        "experience_level": JobExperienceLevel.INTERNSHIP.value,
                        "category": "QA & Automation",
                        "status": JobStatus.ACTIVE.value,
                        "applications_count": 12,
                    },
                    {
                        "title": "Senior Cloud Solutions Architect",
                        "posting_type": JobPostingType.JOB.value,
                        "work_mode": JobWorkMode.REMOTE.value,
                        "location": "Dhaka",
                        "description": "Architect and oversee enterprise cloud migrations and microservice deployments on AWS and Azure.",
                        "requirements": "5+ years of distributed systems design, Docker/Kubernetes orchestration, and CI/CD automation.",
                        "skills": ["AWS", "Docker", "Kubernetes"],
                        "compensation": "৳120K – ৳160K",
                        "experience_level": JobExperienceLevel.SENIOR.value,
                        "category": "Cloud & DevOps",
                        "status": JobStatus.DRAFT.value,
                        "applications_count": 0,
                    },
                ]

                for j_data in sample_jobs:
                    job = JobPosting(
                        company_id=company_user.id,
                        title=j_data["title"],
                        posting_type=j_data["posting_type"],
                        work_mode=j_data["work_mode"],
                        location=j_data["location"],
                        description=j_data["description"],
                        requirements=j_data["requirements"],
                        skills=j_data["skills"],
                        compensation=j_data["compensation"],
                        duration=j_data.get("duration"),
                        experience_level=j_data["experience_level"],
                        category=j_data["category"],
                        status=j_data["status"],
                        applications_count=j_data["applications_count"],
                    )
                    db.add(job)

                db.commit()
                logger.info("Successfully seeded %d sample job postings.", len(sample_jobs))

        # Assessment Mock Test Seeding (SKL-56)
        from app.models.mock_test import (
            MockTest,
            TestQuestion,
            MockTestStatus,
            TestAttempt,
            TestAttemptStatus,
            TestResult,
        )
        instructor_user = db.execute(select(User).where(User.email == "instructor@skill2career.com")).scalar_one_or_none()
        if instructor_user:
            tests_count = db.execute(select(func.count(MockTest.id))).scalar() or 0
            if tests_count == 0:
                logger.info("Seeding initial mock tests matching UI designs (SKL-56)...")
                sample_mock_tests = [
                    {
                        "title": "Data Structures & Algorithms",
                        "category": "Programming",
                        "description": "Practice common DSA questions for technical assessments.",
                        "duration_minutes": 60,
                        "passing_score": 50,
                        "status": MockTestStatus.PUBLISHED.value,
                        "is_published": True,
                        "questions": [
                            {
                                "question_text": "What is the worst-case time complexity of searching an element in a balanced Binary Search Tree (AVL / Red-Black Tree)?",
                                "options": ["O(1)", "O(log n)", "O(n)", "O(n log n)"],
                                "correct_option": "B",
                                "marks": 2,
                                "explanation": "In a height-balanced BST, the tree height is bounded by O(log n), making lookup operations O(log n).",
                            },
                            {
                                "question_text": "Which data structure follows the Last-In-First-Out (LIFO) property?",
                                "options": ["Queue", "Stack", "Priority Queue", "Circular Array"],
                                "correct_option": "B",
                                "marks": 1,
                                "explanation": "A Stack operates under the Last-In-First-Out (LIFO) order.",
                            },
                            {
                                "question_text": "What is the space complexity of Depth First Search (DFS) on a graph with V vertices and E edges implemented recursively?",
                                "options": ["O(1)", "O(V)", "O(V + E)", "O(E)"],
                                "correct_option": "B",
                                "marks": 2,
                                "explanation": "Recursive DFS consumes call stack frames proportional to the maximum tree depth, which is O(V).",
                            },
                            {
                                "question_text": "Which sorting algorithm achieves an average-case time complexity of O(n log n) and is stable?",
                                "options": ["Quick Sort", "Heap Sort", "Merge Sort", "Selection Sort"],
                                "correct_option": "C",
                                "marks": 2,
                                "explanation": "Merge Sort guarantees O(n log n) in all cases and preserves relative order of duplicate elements.",
                            },
                        ],
                    },
                    {
                        "title": "Database Fundamentals",
                        "category": "Database",
                        "description": "Test your knowledge on relational schema design, SQL queries, and normalization.",
                        "duration_minutes": 45,
                        "passing_score": 50,
                        "status": MockTestStatus.PUBLISHED.value,
                        "is_published": True,
                        "questions": [
                            {
                                "question_text": "Which normal form requires eliminating partial dependencies on a composite primary key?",
                                "options": ["1NF", "2NF", "3NF", "BCNF"],
                                "correct_option": "B",
                                "marks": 2,
                                "explanation": "Second Normal Form (2NF) enforces that all non-key attributes are fully functionally dependent on the primary key.",
                            },
                            {
                                "question_text": "Which SQL clause is used to filter aggregated group values?",
                                "options": ["WHERE", "HAVING", "GROUP BY", "ORDER BY"],
                                "correct_option": "B",
                                "marks": 1,
                                "explanation": "The HAVING clause filters groups created by GROUP BY, while WHERE filters individual rows.",
                            },
                            {
                                "question_text": "What does the 'I' in ACID transaction properties stand for?",
                                "options": ["Integrity", "Isolation", "Immutability", "Indexing"],
                                "correct_option": "B",
                                "marks": 1,
                                "explanation": "ACID stands for Atomicity, Consistency, Isolation, and Durability.",
                            },
                        ],
                    },
                    {
                        "title": "Web Development Basics",
                        "category": "Web Development",
                        "description": "Evaluate frontend essentials including HTML5 semantics, modern CSS, and DOM interactions.",
                        "duration_minutes": 45,
                        "passing_score": 50,
                        "status": MockTestStatus.PUBLISHED.value,
                        "is_published": True,
                        "questions": [
                            {
                                "question_text": "Which CSS display property establishes a flexible box formatting context for layout?",
                                "options": ["display: grid", "display: flex", "display: inline-block", "display: table"],
                                "correct_option": "B",
                                "marks": 1,
                                "explanation": "display: flex activates the Flexbox layout model for child items.",
                            },
                            {
                                "question_text": "What is the primary benefit of using semantic HTML5 elements such as <header>, <nav>, and <article>?",
                                "options": ["Faster CSS rendering", "Improved accessibility and SEO", "Automatic JavaScript binding", "Browser-level caching"],
                                "correct_option": "B",
                                "marks": 2,
                                "explanation": "Semantic tags allow screen readers, crawlers, and developers to understand the structure and role of content.",
                            },
                            {
                                "question_text": "In modern React, which hook is used to perform side effects such as data fetching?",
                                "options": ["useState", "useEffect", "useMemo", "useContext"],
                                "correct_option": "B",
                                "marks": 1,
                                "explanation": "useEffect synchronizes a component with external systems and performs side effects.",
                            },
                        ],
                    },
                    {
                        "title": "Object-Oriented Programming",
                        "category": "Programming",
                        "description": "Core concepts of OOP: classes, encapsulation, inheritance, polymorphism, and design patterns.",
                        "duration_minutes": 40,
                        "passing_score": 50,
                        "status": MockTestStatus.PUBLISHED.value,
                        "is_published": True,
                        "questions": [
                            {
                                "question_text": "Which OOP pillar restricts direct access to internal state and requires interactions via methods?",
                                "options": ["Inheritance", "Polymorphism", "Encapsulation", "Abstraction"],
                                "correct_option": "C",
                                "marks": 1,
                                "explanation": "Encapsulation bundles data and methods while restricting direct external modification.",
                            },
                            {
                                "question_text": "What principle in SOLID states that software entities should be open for extension but closed for modification?",
                                "options": ["Single Responsibility Principle", "Open/Closed Principle", "Liskov Substitution Principle", "Dependency Inversion Principle"],
                                "correct_option": "B",
                                "marks": 2,
                                "explanation": "The Open/Closed Principle (OCP) states modules should be open for extension but closed for modification.",
                            },
                            {
                                "question_text": "Which design pattern ensures that a class has only one instance and provides a global access point?",
                                "options": ["Factory Method", "Singleton", "Observer", "Adapter"],
                                "correct_option": "B",
                                "marks": 1,
                                "explanation": "Singleton restricts instantiation of a class to a single object.",
                            },
                        ],
                    },
                ]

                for t_data in sample_mock_tests:
                    mtest = MockTest(
                        instructor_id=instructor_user.id,
                        title=t_data["title"],
                        category=t_data["category"],
                        description=t_data["description"],
                        duration_minutes=t_data["duration_minutes"],
                        passing_score=t_data["passing_score"],
                        total_questions=len(t_data["questions"]),
                        status=t_data["status"],
                        is_published=t_data["is_published"],
                    )
                    db.add(mtest)
                    db.flush()

                    for idx, q_data in enumerate(t_data["questions"]):
                        question = TestQuestion(
                            test_id=mtest.id,
                            question_text=q_data["question_text"],
                            options=q_data["options"],
                            correct_option=q_data["correct_option"],
                            marks=q_data.get("marks", 1),
                            explanation=q_data.get("explanation"),
                            order_index=idx,
                            topic=q_data.get("topic"),
                            difficulty=q_data.get("difficulty"),
                        )
                        db.add(question)

                db.commit()
                logger.info("Successfully seeded %d sample mock tests with questions.", len(sample_mock_tests))

            # Seed sample assessment result matching UI design (SKL-58)
            learner_user = db.execute(select(User).where(User.email == "learner@skill2career.com")).scalar_one_or_none()
            dsa_test = db.execute(select(MockTest).where(MockTest.title == "Data Structures & Algorithms")).scalar_one_or_none()
            if learner_user and dsa_test:
                existing_attempt = db.execute(
                    select(TestAttempt).where(
                        TestAttempt.test_id == dsa_test.id,
                        TestAttempt.learner_id == learner_user.id,
                    )
                ).scalars().first()

                if not existing_attempt:
                    logger.info("Seeding sample completed attempt and test result for DSA assessment (SKL-58)...")
                    from datetime import datetime, timezone, timedelta
                    now = datetime.now(timezone.utc)
                    sample_attempt = TestAttempt(
                        test_id=dsa_test.id,
                        learner_id=learner_user.id,
                        started_at=now - timedelta(minutes=45),
                        submitted_at=now - timedelta(minutes=6, seconds=40),
                        status=TestAttemptStatus.SUBMITTED.value,
                        answers={"1": "B", "2": "B", "3": "B", "4": "C"},
                        marked_for_review=[],
                        score=84.0,
                        total_marks=100,
                        percentage=84.0,
                        is_passed=True,
                        time_taken_seconds=2300,
                    )
                    db.add(sample_attempt)
                    db.flush()

                    sample_result = TestResult(
                        attempt_id=sample_attempt.id,
                        total_score=84.0,
                        total_marks=100,
                        percentage=84.0,
                        accuracy=86.7,
                        is_passed=True,
                        time_taken_seconds=2300,
                        percentile_score=88.0,
                        percentile_label="Top 12% Candidate",
                        topic_breakdown=[
                            {"topic": "Binary Search Trees", "percentage": 100.0, "correct_count": 5, "total_count": 5, "correct_marks": 25.0, "total_marks": 25.0},
                            {"topic": "Graph Algorithms", "percentage": 80.0, "correct_count": 4, "total_count": 5, "correct_marks": 24.0, "total_marks": 30.0},
                            {"topic": "Dynamic Programming", "percentage": 70.0, "correct_count": 7, "total_count": 10, "correct_marks": 17.5, "total_marks": 25.0},
                            {"topic": "Sorting", "percentage": 90.0, "correct_count": 9, "total_count": 10, "correct_marks": 18.0, "total_marks": 20.0},
                        ],
                        difficulty_analysis=[
                            {"difficulty": "Easy", "correct_count": 10, "total_count": 10, "percentage": 100.0, "correct_marks": 20.0, "total_marks": 20.0},
                            {"difficulty": "Medium", "correct_count": 12, "total_count": 15, "percentage": 80.0, "correct_marks": 36.0, "total_marks": 45.0},
                            {"difficulty": "Hard", "correct_count": 3, "total_count": 5, "percentage": 60.0, "correct_marks": 21.0, "total_marks": 35.0},
                        ],
                        question_reviews=[
                            {
                                "question_id": 1,
                                "order_index": 0,
                                "question_text": "What is the worst-case time complexity of searching an element in a balanced Binary Search Tree (AVL / Red-Black Tree)?",
                                "options": ["O(1)", "O(log n)", "O(n)", "O(n log n)"],
                                "selected_option": "B",
                                "correct_option": "B",
                                "is_correct": True,
                                "marks": 2,
                                "marks_obtained": 2.0,
                                "explanation": "In a height-balanced BST, the tree height is bounded by O(log n), making lookup operations O(log n).",
                                "topic": "Binary Search Trees",
                                "difficulty": "Easy",
                            },
                            {
                                "question_id": 2,
                                "order_index": 1,
                                "question_text": "Which data structure follows the Last-In-First-Out (LIFO) property?",
                                "options": ["Queue", "Stack", "Priority Queue", "Circular Array"],
                                "selected_option": "B",
                                "correct_option": "B",
                                "is_correct": True,
                                "marks": 1,
                                "marks_obtained": 1.0,
                                "explanation": "A Stack operates under the Last-In-First-Out (LIFO) order.",
                                "topic": "Stacks & Queues",
                                "difficulty": "Easy",
                            },
                            {
                                "question_id": 3,
                                "order_index": 2,
                                "question_text": "What is the space complexity of Depth First Search (DFS) on a graph with V vertices and E edges implemented recursively?",
                                "options": ["O(1)", "O(V)", "O(V + E)", "O(E)"],
                                "selected_option": "B",
                                "correct_option": "B",
                                "is_correct": True,
                                "marks": 2,
                                "marks_obtained": 2.0,
                                "explanation": "Recursive DFS consumes call stack frames proportional to the maximum tree depth, which is O(V).",
                                "topic": "Graph Algorithms",
                                "difficulty": "Medium",
                            },
                            {
                                "question_id": 4,
                                "order_index": 3,
                                "question_text": "Which sorting algorithm achieves an average-case time complexity of O(n log n) and is stable?",
                                "options": ["Quick Sort", "Heap Sort", "Merge Sort", "Selection Sort"],
                                "selected_option": "C",
                                "correct_option": "C",
                                "is_correct": True,
                                "marks": 2,
                                "marks_obtained": 2.0,
                                "explanation": "Merge Sort guarantees O(n log n) in all cases and preserves relative order of duplicate elements.",
                                "topic": "Sorting",
                                "difficulty": "Medium",
                            },
                        ],
                    )
                    db.add(sample_result)
                    db.commit()
                    logger.info("Successfully seeded DSA attempt and performance analysis result.")


        job = db.execute(
            select(JobPosting).where(JobPosting.title == "Junior Software Developer")
        ).scalars().first()

        if job:
            existing_questions = db.execute(
                select(ScreeningQuestion).where(ScreeningQuestion.job_id == job.id)
            ).scalars().all()

            if not existing_questions:
                q1 = ScreeningQuestion(
                    job_id=job.id,
                    question_text="Years of hands-on React/Node experience?",
                    question_type=QuestionType.NUMERIC.value,
                    is_required=True,
                    is_deal_breaker=True,
                    deal_breaker_rule=DealBreakerRule.GTE.value,
                    deal_breaker_value="2",
                    deal_breaker_label="Deal-Breaker: Auto-Disqualify if < 2 Years",
                    weight=40,
                    order_index=1,
                )
                q2 = ScreeningQuestion(
                    job_id=job.id,
                    question_text="Are you comfortable working in hybrid mode in Dhaka?",
                    question_type=QuestionType.YES_NO.value,
                    options=["Yes", "No"],
                    expected_answer="Yes",
                    is_required=True,
                    is_deal_breaker=True,
                    deal_breaker_rule=DealBreakerRule.MANDATORY.value,
                    deal_breaker_value="Yes",
                    deal_breaker_label="Deal-Breaker: Mandatory",
                    weight=40,
                    order_index=2,
                )
                q3 = ScreeningQuestion(
                    job_id=job.id,
                    question_text="Link to your most complex GitHub repository",
                    question_type=QuestionType.TEXT.value,
                    is_required=False,
                    is_deal_breaker=False,
                    weight=20,
                    order_index=3,
                )
                db.add_all([q1, q2, q3])
                db.flush()

                sample_evaluations = [
                    {
                        "candidate_name": "Rashedul Islam",
                        "candidate_email": "23201201@uap-bd.edu",
                        "match_score": 94.0,
                        "deal_breaker_passed": True,
                        "deal_breaker_failed_reason": None,
                        "status": CandidateStatus.SHORTLISTED.value,
                        "key_answers_preview": "3 yrs React/Node • Hybrid Confirmed • github.com/rashedul/fullstack",
                        "answers": {
                            str(q1.id): "3 years",
                            str(q2.id): "Yes",
                            str(q3.id): "https://github.com/rashedul/fullstack-app",
                        },
                    },
                    {
                        "candidate_name": "Brain Station",
                        "candidate_email": "candidate.bs@test.com",
                        "match_score": 82.0,
                        "deal_breaker_passed": True,
                        "deal_breaker_failed_reason": None,
                        "status": CandidateStatus.SHORTLISTED.value,
                        "key_answers_preview": "2.5 yrs React/Node • Hybrid Confirmed • github.com/candidate/project",
                        "answers": {
                            str(q1.id): "2.5 years",
                            str(q2.id): "Yes",
                            str(q3.id): "https://github.com/candidate/project",
                        },
                    },
                    {
                        "candidate_name": "Rashedul Islam",
                        "candidate_email": "applicant3@test.com",
                        "match_score": 45.0,
                        "deal_breaker_passed": False,
                        "deal_breaker_failed_reason": "Failed deal-breaker: < 2 Years experience",
                        "status": CandidateStatus.DISQUALIFIED.value,
                        "key_answers_preview": "1 yr React/Node • Hybrid Confirmed • github.com/applicant/repo",
                        "answers": {
                            str(q1.id): "1 year",
                            str(q2.id): "Yes",
                            str(q3.id): "https://github.com/applicant/repo",
                        },
                    },
                    {
                        "candidate_name": "Brain Station",
                        "candidate_email": "applicant4@test.com",
                        "match_score": 45.0,
                        "deal_breaker_passed": False,
                        "deal_breaker_failed_reason": "Failed deal-breaker: Not comfortable with hybrid Dhaka",
                        "status": CandidateStatus.DISQUALIFIED.value,
                        "key_answers_preview": "2 yrs React/Node • Remote Only • github.com/applicant4/code",
                        "answers": {
                            str(q1.id): "2 years",
                            str(q2.id): "No",
                            str(q3.id): "https://github.com/applicant4/code",
                        },
                    },
                    {
                        "candidate_name": "Tanvir Hasan",
                        "candidate_email": "learner@skill2career.com",
                        "match_score": 90.0,
                        "deal_breaker_passed": True,
                        "deal_breaker_failed_reason": None,
                        "status": CandidateStatus.UNDER_REVIEW.value,
                        "key_answers_preview": "3 yrs React/Node • Hybrid Confirmed • github.com/tanvir/core",
                        "answers": {
                            str(q1.id): "3 years",
                            str(q2.id): "Yes",
                            str(q3.id): "https://github.com/tanvir/core",
                        },
                    },
                    {
                        "candidate_name": "Jubair Bin Hasan",
                        "candidate_email": "23201065@uap-bd.edu",
                        "match_score": 88.0,
                        "deal_breaker_passed": True,
                        "deal_breaker_failed_reason": None,
                        "status": CandidateStatus.UNDER_REVIEW.value,
                        "key_answers_preview": "2.5 yrs React/Node • Hybrid Confirmed • github.com/jubair/portfolio",
                        "answers": {
                            str(q1.id): "2.5 years",
                            str(q2.id): "Yes",
                            str(q3.id): "https://github.com/jubair/portfolio",
                        },
                    },
                    {
                        "candidate_name": "Kazi Sakib",
                        "candidate_email": "sakib@test.com",
                        "match_score": 38.0,
                        "deal_breaker_passed": False,
                        "deal_breaker_failed_reason": "Failed deal-breaker: < 2 Years experience",
                        "status": CandidateStatus.DISQUALIFIED.value,
                        "key_answers_preview": "0.5 yrs React/Node • Remote Only",
                        "answers": {
                            str(q1.id): "0.5 years",
                            str(q2.id): "No",
                            str(q3.id): "https://github.com/sakib/portfolio",
                        },
                    },
                    {
                        "candidate_name": "Sumaiya Akter",
                        "candidate_email": "sumaiya@test.com",
                        "match_score": 78.0,
                        "deal_breaker_passed": True,
                        "deal_breaker_failed_reason": None,
                        "status": CandidateStatus.UNDER_REVIEW.value,
                        "key_answers_preview": "2 yrs React/Node • Hybrid Confirmed • github.com/sumaiya/app",
                        "answers": {
                            str(q1.id): "2 years",
                            str(q2.id): "Yes",
                            str(q3.id): "https://github.com/sumaiya/app",
                        },
                    },
                ]

                for item in sample_evaluations:
                    ev = CandidateEvaluation(
                        job_id=job.id,
                        candidate_name=item["candidate_name"],
                        candidate_email=item["candidate_email"],
                        match_score=item["match_score"],
                        deal_breaker_passed=item["deal_breaker_passed"],
                        deal_breaker_failed_reason=item["deal_breaker_failed_reason"],
                        status=item["status"],
                        key_answers_preview=item["key_answers_preview"],
                        answers=item["answers"],
                    )
                    db.add(ev)

                job.applications_count = len(sample_evaluations)
                db.commit()
                logger.info("Successfully seeded screening questions and %d candidate evaluations for %s.", len(sample_evaluations), job.title)

        # 2. Frontend Developer
        fe_job = db.execute(select(JobPosting).where(JobPosting.title == "Frontend Developer")).scalars().first()
        if fe_job:
            existing_fe_qs = db.execute(select(ScreeningQuestion).where(ScreeningQuestion.job_id == fe_job.id)).scalars().all()
            if not existing_fe_qs:
                fe_q1 = ScreeningQuestion(
                    job_id=fe_job.id,
                    question_text="Years of hands-on React & modern JavaScript experience?",
                    question_type=QuestionType.NUMERIC.value,
                    is_required=True,
                    is_deal_breaker=True,
                    deal_breaker_rule=DealBreakerRule.GTE.value,
                    deal_breaker_value="2",
                    deal_breaker_label="Deal-Breaker: Auto-Disqualify if < 2 Years",
                    weight=40,
                    order_index=1,
                )
                fe_q2 = ScreeningQuestion(
                    job_id=fe_job.id,
                    question_text="Are you proficient with TailwindCSS and TypeScript?",
                    question_type=QuestionType.YES_NO.value,
                    options=["Yes", "No"],
                    expected_answer="Yes",
                    is_required=True,
                    is_deal_breaker=True,
                    deal_breaker_rule=DealBreakerRule.MANDATORY.value,
                    deal_breaker_value="Yes",
                    deal_breaker_label="Deal-Breaker: Mandatory",
                    weight=40,
                    order_index=2,
                )
                fe_q3 = ScreeningQuestion(
                    job_id=fe_job.id,
                    question_text="Link to your deployed portfolio or best frontend project",
                    question_type=QuestionType.TEXT.value,
                    is_required=False,
                    is_deal_breaker=False,
                    weight=20,
                    order_index=3,
                )
                db.add_all([fe_q1, fe_q2, fe_q3])
                db.flush()

                fe_candidates = [
                    {"name": "Rashedul Islam", "email": "23201201@uap-bd.edu", "score": 95.0, "pass": True, "reason": None, "status": CandidateStatus.SHORTLISTED.value, "preview": "3 yrs React • Tailwind/TS Confirmed • github.com/rashedul/ui-kit", "answers": {str(fe_q1.id): "3 years", str(fe_q2.id): "Yes", str(fe_q3.id): "https://github.com/rashedul/ui-kit"}},
                    {"name": "Lam-yea Chowdhury", "email": "candidate.lam@test.com", "score": 88.0, "pass": True, "reason": None, "status": CandidateStatus.SHORTLISTED.value, "preview": "2.5 yrs React • Tailwind/TS Confirmed • portfolio.lamyea.dev", "answers": {str(fe_q1.id): "2.5 years", str(fe_q2.id): "Yes", str(fe_q3.id): "https://portfolio.lamyea.dev"}},
                    {"name": "Asif Mahmud", "email": "asif@test.com", "score": 80.0, "pass": True, "reason": None, "status": CandidateStatus.UNDER_REVIEW.value, "preview": "2 yrs React • Tailwind/TS Confirmed • asif-portfolio.vercel.app", "answers": {str(fe_q1.id): "2 years", str(fe_q2.id): "Yes", str(fe_q3.id): "https://asif-portfolio.vercel.app"}},
                    {"name": "Candidate FrontEnd", "email": "frontend.junior@test.com", "score": 42.0, "pass": False, "reason": "Failed deal-breaker: < 2 Years experience", "status": CandidateStatus.DISQUALIFIED.value, "preview": "1 yr React • Tailwind/TS Confirmed • github.com/frontend/demo", "answers": {str(fe_q1.id): "1 year", str(fe_q2.id): "Yes", str(fe_q3.id): "https://github.com/frontend/demo"}},
                    {"name": "Muktadir Rahman", "email": "muktadir@test.com", "score": 40.0, "pass": False, "reason": "Failed deal-breaker: Not proficient with TypeScript", "status": CandidateStatus.DISQUALIFIED.value, "preview": "2 yrs React • No TS • github.com/muktadir/app", "answers": {str(fe_q1.id): "2 years", str(fe_q2.id): "No", str(fe_q3.id): "https://github.com/muktadir/app"}},
                ]
                for c in fe_candidates:
                    db.add(CandidateEvaluation(job_id=fe_job.id, candidate_name=c["name"], candidate_email=c["email"], match_score=c["score"], deal_breaker_passed=c["pass"], deal_breaker_failed_reason=c["reason"], status=c["status"], key_answers_preview=c["preview"], answers=c["answers"]))
                fe_job.applications_count = len(fe_candidates)
                db.commit()
                logger.info("Successfully seeded screening for Frontend Developer.")

        # 3. Software Engineering Intern
        se_job = db.execute(select(JobPosting).where(JobPosting.title == "Software Engineering Intern")).scalars().first()
        if se_job:
            existing_se_qs = db.execute(select(ScreeningQuestion).where(ScreeningQuestion.job_id == se_job.id)).scalars().all()
            if not existing_se_qs:
                se_q1 = ScreeningQuestion(
                    job_id=se_job.id,
                    question_text="Are you enrolled in or a graduate of a CS/Engineering degree program?",
                    question_type=QuestionType.YES_NO.value,
                    options=["Yes", "No"],
                    expected_answer="Yes",
                    is_required=True,
                    is_deal_breaker=True,
                    deal_breaker_rule=DealBreakerRule.MANDATORY.value,
                    deal_breaker_value="Yes",
                    deal_breaker_label="Deal-Breaker: Mandatory Degree Enrolled",
                    weight=40,
                    order_index=1,
                )
                se_q2 = ScreeningQuestion(
                    job_id=se_job.id,
                    question_text="Can you commit to a 3-month full-time internship in Dhaka?",
                    question_type=QuestionType.YES_NO.value,
                    options=["Yes", "No"],
                    expected_answer="Yes",
                    is_required=True,
                    is_deal_breaker=True,
                    deal_breaker_rule=DealBreakerRule.MANDATORY.value,
                    deal_breaker_value="Yes",
                    deal_breaker_label="Deal-Breaker: Full-time Commitment",
                    weight=40,
                    order_index=2,
                )
                se_q3 = ScreeningQuestion(
                    job_id=se_job.id,
                    question_text="Primary coding language & competitive programming profile link",
                    question_type=QuestionType.TEXT.value,
                    is_required=False,
                    is_deal_breaker=False,
                    weight=20,
                    order_index=3,
                )
                db.add_all([se_q1, se_q2, se_q3])
                db.flush()

                se_candidates = [
                    {"name": "Rashedul Islam", "email": "23201201@uap-bd.edu", "score": 96.0, "pass": True, "reason": None, "status": CandidateStatus.SHORTLISTED.value, "preview": "CS Final Year • Full-time Committed • codeforces.com/rashedul", "answers": {str(se_q1.id): "Yes", str(se_q2.id): "Yes", str(se_q3.id): "C++ • codeforces.com/rashedul"}},
                    {"name": "Saif Ahmed", "email": "saif@test.com", "score": 86.0, "pass": True, "reason": None, "status": CandidateStatus.SHORTLISTED.value, "preview": "CS 3rd Year • Full-time Committed • leetcode.com/saif", "answers": {str(se_q1.id): "Yes", str(se_q2.id): "Yes", str(se_q3.id): "Python • leetcode.com/saif"}},
                    {"name": "Farhan Tanvir", "email": "farhan@test.com", "score": 82.0, "pass": True, "reason": None, "status": CandidateStatus.UNDER_REVIEW.value, "preview": "SE Graduate • Full-time Committed • github.com/farhan", "answers": {str(se_q1.id): "Yes", str(se_q2.id): "Yes", str(se_q3.id): "Java • github.com/farhan"}},
                    {"name": "Applicant Intern", "email": "intern.cand@test.com", "score": 42.0, "pass": False, "reason": "Failed deal-breaker: Cannot commit to full-time", "status": CandidateStatus.DISQUALIFIED.value, "preview": "CS 2nd Year • Part-time Only", "answers": {str(se_q1.id): "Yes", str(se_q2.id): "No", str(se_q3.id): "Python"}},
                ]
                for c in se_candidates:
                    db.add(CandidateEvaluation(job_id=se_job.id, candidate_name=c["name"], candidate_email=c["email"], match_score=c["score"], deal_breaker_passed=c["pass"], deal_breaker_failed_reason=c["reason"], status=c["status"], key_answers_preview=c["preview"], answers=c["answers"]))
                se_job.applications_count = len(se_candidates)
                db.commit()
                logger.info("Successfully seeded screening for Software Engineering Intern.")

        # 4. QA & Automation Intern
        qa_job = db.execute(select(JobPosting).where(JobPosting.title == "QA & Automation Intern")).scalars().first()
        if qa_job:
            existing_qa_qs = db.execute(select(ScreeningQuestion).where(ScreeningQuestion.job_id == qa_job.id)).scalars().all()
            if not existing_qa_qs:
                qa_q1 = ScreeningQuestion(
                    job_id=qa_job.id,
                    question_text="Do you have hands-on experience with Python and Selenium or Playwright?",
                    question_type=QuestionType.YES_NO.value,
                    options=["Yes", "No"],
                    expected_answer="Yes",
                    is_required=True,
                    is_deal_breaker=True,
                    deal_breaker_rule=DealBreakerRule.MANDATORY.value,
                    deal_breaker_value="Yes",
                    deal_breaker_label="Deal-Breaker: Mandatory Testing Skills",
                    weight=50,
                    order_index=1,
                )
                qa_q2 = ScreeningQuestion(
                    job_id=qa_job.id,
                    question_text="Can you commit to a 6-month remote internship?",
                    question_type=QuestionType.YES_NO.value,
                    options=["Yes", "No"],
                    expected_answer="Yes",
                    is_required=True,
                    is_deal_breaker=True,
                    deal_breaker_rule=DealBreakerRule.MANDATORY.value,
                    deal_breaker_value="Yes",
                    deal_breaker_label="Deal-Breaker: 6-Month Commitment",
                    weight=30,
                    order_index=2,
                )
                qa_q3 = ScreeningQuestion(
                    job_id=qa_job.id,
                    question_text="Link to sample automation scripts or Postman collections",
                    question_type=QuestionType.TEXT.value,
                    is_required=False,
                    is_deal_breaker=False,
                    weight=20,
                    order_index=3,
                )
                db.add_all([qa_q1, qa_q2, qa_q3])
                db.flush()

                qa_candidates = [
                    {"name": "Rashedul Islam", "email": "23201201@uap-bd.edu", "score": 94.0, "pass": True, "reason": None, "status": CandidateStatus.SHORTLISTED.value, "preview": "Python/Selenium Confirmed • 6-Month Committed • github.com/rashedul/test-suite", "answers": {str(qa_q1.id): "Yes", str(qa_q2.id): "Yes", str(qa_q3.id): "https://github.com/rashedul/test-suite"}},
                    {"name": "Nusrat Jahan", "email": "nusrat@test.com", "score": 84.0, "pass": True, "reason": None, "status": CandidateStatus.SHORTLISTED.value, "preview": "Python/Playwright Confirmed • 6-Month Committed • postman.com/nusrat", "answers": {str(qa_q1.id): "Yes", str(qa_q2.id): "Yes", str(qa_q3.id): "https://postman.com/nusrat"}},
                    {"name": "Candidate QA", "email": "qa.dev@test.com", "score": 40.0, "pass": False, "reason": "Failed deal-breaker: No automated testing experience", "status": CandidateStatus.DISQUALIFIED.value, "preview": "Manual QA Only", "answers": {str(qa_q1.id): "No", str(qa_q2.id): "Yes", str(qa_q3.id): "N/A"}},
                ]
                for c in qa_candidates:
                    db.add(CandidateEvaluation(job_id=qa_job.id, candidate_name=c["name"], candidate_email=c["email"], match_score=c["score"], deal_breaker_passed=c["pass"], deal_breaker_failed_reason=c["reason"], status=c["status"], key_answers_preview=c["preview"], answers=c["answers"]))
                qa_job.applications_count = len(qa_candidates)
                db.commit()
                logger.info("Successfully seeded screening for QA & Automation Intern.")
        # Seed Forum Categories and Sample Discussions (SKL-14)
        logger.info("Checking forum categories and discussions...")
        categories_data = [
            {"name": "General Discussion", "slug": "general-discussion", "description": "Open community conversations, career guidance, and general tech chats.", "order_index": 1},
            {"name": "Programming", "slug": "programming", "description": "Algorithms, data structures, backend, frontend, and software engineering questions.", "order_index": 2},
            {"name": "Career & Jobs", "slug": "career-jobs", "description": "CV reviews, job search strategies, internship hunt, and industry transitions.", "order_index": 3},
            {"name": "Interview Preparation", "slug": "interview-preparation", "description": "Technical screening, system design, mock interview questions, and HR tips.", "order_index": 4},
            {"name": "Learning & Courses", "slug": "learning-courses", "description": "Course recommendations, study schedules, and academic exam prep.", "order_index": 5},
        ]

        cat_map = {}
        for cdata in categories_data:
            cat = db.execute(select(ForumCategory).where(ForumCategory.slug == cdata["slug"])).scalar_one_or_none()
            if not cat:
                cat = ForumCategory(
                    name=cdata["name"],
                    slug=cdata["slug"],
                    description=cdata["description"],
                    order_index=cdata["order_index"],
                )
                db.add(cat)
                db.flush()
                logger.info("Created forum category: %s", cat.name)
            cat_map[cat.slug] = cat
        db.commit()

        # Ensure forum author users exist
        forum_users_meta = [
            {"email": "rashedul@skill2career.com", "first_name": "Rashedul", "last_name": "Islam", "role": UserRole.LEARNER},
            {"email": "nayeema@skill2career.com", "first_name": "Nayeema", "last_name": "Sultana", "role": UserRole.INSTRUCTOR},
            {"email": "absiddique@skill2career.com", "first_name": "AB", "last_name": "Siddique", "role": UserRole.LEARNER},
            {"email": "lamyea@skill2career.com", "first_name": "Lam-Yea", "last_name": "Chowdhury", "role": UserRole.LEARNER},
            {"email": "moktadir@skill2career.com", "first_name": "Md.", "last_name": "Moktadir", "role": UserRole.LEARNER},
            {"email": "saif@skill2career.com", "first_name": "Saif Mehedi", "last_name": "Sami", "role": UserRole.LEARNER},
        ]
        user_cache = {}
        for fu in forum_users_meta:
            u = db.execute(select(User).where(User.email == fu["email"])).scalar_one_or_none()
            if not u:
                u = User(
                    email=fu["email"],
                    hashed_password=hash_password("Password123!"),
                    first_name=fu["first_name"],
                    last_name=fu["last_name"],
                    role=fu["role"],
                    is_verified=True,
                    is_active=True,
                )
                db.add(u)
                db.flush()
            user_cache[fu["email"]] = u
        db.commit()

        # Seed sample forum discussions matching Forum.png
        existing_posts_count = db.execute(select(func.count(ForumPost.id))).scalar() or 0
        if existing_posts_count == 0:
            posts_seed_data = [
                {
                    "title": "How should I prepare for a backend developer interview?",
                    "category_slug": "interview-preparation",
                    "author_email": "rashedul@skill2career.com",
                    "content": "I am preparing for junior to mid-level backend developer interviews focusing on Python (FastAPI/Django) and Node.js. What core areas should I prioritize? E.g., relational databases, indexing, caching with Redis, system design, or concurrency patterns?",
                    "likes_count": 25,
                    "views_count": 155,
                    "comments": [
                        {
                            "author_email": "instructor@skill2career.com",
                            "is_instructor_reply": True,
                            "content": "Focus heavily on relational database fundamentals: 3NF normalization, index internals (B-Tree vs Hash), ACID transactions, and query plan analysis with EXPLAIN. Interviewers love asking how you would debug a slow query.",
                        },
                        {
                            "author_email": "moktadir@skill2career.com",
                            "is_instructor_reply": False,
                            "content": "Understand caching strategies (Cache-Aside, Write-Through) with Redis, especially cache invalidation, cache stampede, and cache penetration.",
                        },
                        {
                            "author_email": "learner@skill2career.com",
                            "is_instructor_reply": False,
                            "content": "Be prepared to explain REST vs gRPC vs WebSockets and when to pick each for high-throughput microservices.",
                        },
                    ],
                },
                {
                    "title": "Best resources for learning Data Structures and Algorithms?",
                    "category_slug": "programming",
                    "author_email": "absiddique@skill2career.com",
                    "content": "Looking for high-yield resources to master trees, graphs, dynamic programming, and heaps. Any recommended platforms, curated sheets, or books that explain problem intuition clearly?",
                    "likes_count": 18,
                    "views_count": 210,
                    "comments": [
                        {
                            "author_email": "nayeema@skill2career.com",
                            "is_instructor_reply": True,
                            "content": "I strongly recommend starting with NeetCode 150 alongside 'Grokking Algorithms' for visual intuition. Focus on pattern recognition: two pointers, sliding window, topological sort, and BFS/DFS before jumping directly into complex dynamic programming.",
                        },
                        {
                            "author_email": "rashedul@skill2career.com",
                            "is_instructor_reply": False,
                            "content": "Striver's SDE sheet is also phenomenal for structured revision before technical rounds. It categorizes questions by difficulty and topic.",
                        },
                        {
                            "author_email": "absiddique@skill2career.com",
                            "is_instructor_reply": False,
                            "content": "Thanks for the suggestions! I found practicing visualization on Visualgo.net super helpful before coding.",
                        },
                    ],
                },
                {
                    "title": "How can I improve my CV for internships?",
                    "category_slug": "career-jobs",
                    "author_email": "lamyea@skill2career.com",
                    "content": "As an undergraduate seeking summer internships, what key sections do tech recruiters look for first? Should I put projects above education? How should I quantify impact if I don't have prior commercial experience?",
                    "likes_count": 32,
                    "views_count": 190,
                    "comments": [
                        {
                            "author_email": "company@skill2career.com",
                            "is_instructor_reply": False,
                            "content": "As a technical recruiter, the #1 thing I look for on student CVs is deployed projects with live demo links and clean GitHub READMEs. Keep your CV strictly 1 page, put your Projects and Tech Stack right below your Education, and avoid generic skill rating bars.",
                        },
                        {
                            "author_email": "instructor@skill2career.com",
                            "is_instructor_reply": True,
                            "content": "Quantify your bullet points with metrics wherever possible: for example, 'Built an automated grading engine handling 500+ submissions with 99.8% uptime' rather than just 'Worked on grading engine'. Impact metrics immediately catch a hiring manager's eye.",
                        },
                        {
                            "author_email": "saif@skill2career.com",
                            "is_instructor_reply": False,
                            "content": "Ensure your LinkedIn profile and GitHub are hyperlinked in the contact header. Also, tailor the keywords to match the specific internship description (e.g., React, FastAPI, Docker, SQL).",
                        },
                        {
                            "author_email": "moktadir@skill2career.com",
                            "is_instructor_reply": False,
                            "content": "Include hackathon participations or academic research if relevant. It demonstrates proactive problem solving outside of standard coursework.",
                        },
                    ],
                },
                {
                    "title": "Tips for mastering Object-Oriented Programming in Java for academic exams",
                    "category_slug": "learning-courses",
                    "author_email": "moktadir@skill2career.com",
                    "content": "Our university semester final includes in-depth design problems using OOP principles (encapsulation, polymorphism, abstract classes vs interfaces) and SOLID design patterns. Any tips on tackling coding exam questions efficiently?",
                    "likes_count": 22,
                    "views_count": 120,
                    "comments": [
                        {
                            "author_email": "instructor@skill2career.com",
                            "is_instructor_reply": True,
                            "content": "Be ready to write clean code explaining polymorphism, abstract classes vs interfaces, and constructor chaining by hand without an IDE. Professors often test edge cases in method overriding vs overloading and Java 8 default methods.",
                        },
                        {
                            "author_email": "absiddique@skill2career.com",
                            "is_instructor_reply": False,
                            "content": "Make sure you understand the SOLID principles with concrete code examples, especially Liskov Substitution Principle and Dependency Inversion Principle.",
                        },
                        {
                            "author_email": "learner@skill2career.com",
                            "is_instructor_reply": False,
                            "content": "Practicing previous years' university question papers and drawing UML class diagrams helped me score top marks in our semester final.",
                        },
                    ],
                },
                {
                    "title": "Networking and software engineering job prospects in Dhaka for fresh graduates",
                    "category_slug": "general-discussion",
                    "author_email": "saif@skill2career.com",
                    "content": "Let's share insights on local tech companies hiring fresh graduates in Dhaka, standard salary ranges, work culture, and how participating in local meetups, open-source communities, and hackathons helped you land opportunities.",
                    "likes_count": 45,
                    "views_count": 320,
                    "comments": [
                        {
                            "author_email": "company@skill2career.com",
                            "is_instructor_reply": False,
                            "content": "Software companies in Dhaka (Brain Station 23, Therap, Enosis, Selise, Kona SL, Kaz Software) are actively hiring fresh graduates. What stands out most during interviews is problem-solving ability, computer science fundamentals (OS, DBMS, OOP), and humility to learn.",
                        },
                        {
                            "author_email": "lamyea@skill2career.com",
                            "is_instructor_reply": False,
                            "content": "Attending local Dhaka dev meetups (Python Dhaka, React Bangladesh, DevOps Days) helped me connect directly with tech leads and obtain referral interviews.",
                        },
                        {
                            "author_email": "saif@skill2career.com",
                            "is_instructor_reply": False,
                            "content": "Junior developer salary ranges typically span BDT 35k to 70k depending on the company tier. Keep polishing DSA and build full-stack portfolio applications.",
                        },
                    ],
                },
            ]

            for p_seed in posts_seed_data:
                author_user = user_cache.get(p_seed["author_email"])
                cat_obj = cat_map.get(p_seed["category_slug"])
                if not author_user or not cat_obj:
                    continue

                post = ForumPost(
                    category_id=cat_obj.id,
                    author_id=author_user.id,
                    title=p_seed["title"],
                    content=p_seed["content"],
                    views_count=p_seed["views_count"],
                    replies_count=len(p_seed.get("comments", [])),
                    has_instructor_reply=any(c.get("is_instructor_reply") for c in p_seed.get("comments", [])),
                    instructor_reply_name=next(
                        (
                            f"{user_cache[c['author_email']].first_name} {user_cache[c['author_email']].last_name}".strip()
                            for c in p_seed.get("comments", [])
                            if c.get("is_instructor_reply") and c["author_email"] in user_cache
                        ),
                        None,
                    ),
                )
                db.add(post)
                db.flush()

                if "comments" in p_seed:
                    for c_seed in p_seed["comments"]:
                        c_author = user_cache.get(c_seed["author_email"])
                        if c_author:
                            comment = ForumComment(
                                post_id=post.id,
                                author_id=c_author.id,
                                content=c_seed["content"],
                                is_instructor_reply=c_seed["is_instructor_reply"],
                                likes_count=5,
                            )
                            db.add(comment)

            db.commit()
            logger.info("Successfully seeded %d sample forum discussions.", len(posts_seed_data))

        # Seed Course Enrollments and Lesson Progress for Learner (SKL-54)
        learner_user = db.execute(
            select(User).where(User.email == "learner@skill2career.com")
        ).scalar_one_or_none()
        if learner_user:
            courses = list(db.execute(select(Course)).scalars().all())
            for crs in courses:
                existing_enr = db.execute(
                    select(CourseEnrollment).where(
                        CourseEnrollment.user_id == learner_user.id,
                        CourseEnrollment.course_id == crs.id,
                    )
                ).scalar_one_or_none()
                if not existing_enr:
                    total_lessons = len(crs.lessons)
                    if "Data Structures & Algorithms" in crs.title and total_lessons >= 6:
                        completed_count = 6
                        prog_pct = 75.0
                    elif total_lessons > 0:
                        completed_count = max(1, total_lessons // 2)
                        prog_pct = round((completed_count / total_lessons) * 100.0, 1)
                    else:
                        completed_count = 0
                        prog_pct = 0.0

                    last_lesson = crs.lessons[completed_count - 1] if completed_count > 0 and crs.lessons else None
                    enr = CourseEnrollment(
                        user_id=learner_user.id,
                        course_id=crs.id,
                        status=EnrollmentStatus.ACTIVE.value,
                        progress_percentage=prog_pct,
                        completed_lessons_count=completed_count,
                        last_accessed_lesson_id=last_lesson.id if last_lesson else None,
                    )
                    db.add(enr)
                    db.flush()

                    for idx in range(completed_count):
                        les = crs.lessons[idx]
                        lp = LessonProgress(
                            user_id=learner_user.id,
                            course_id=crs.id,
                            lesson_id=les.id,
                            enrollment_id=enr.id,
                            is_completed=True,
                        )
                        db.add(lp)
            db.commit()
            logger.info("Successfully seeded course enrollments and progress for sample learner.")

            # Seed sample job applications for learner
            jobs = list(db.execute(select(JobPosting).order_by(JobPosting.id.asc())).scalars().all())
            if jobs:
                first_job = jobs[0]
                existing_app = db.execute(
                    select(JobApplication).where(
                        JobApplication.learner_id == learner_user.id,
                        JobApplication.job_id == first_job.id,
                    )
                ).scalar_one_or_none()
                if not existing_app:
                    app1 = JobApplication(
                        job_id=first_job.id,
                        learner_id=learner_user.id,
                        resume_url="/uploads/resumes/Tanvir_Hasan_Resume.pdf",
                        resume_filename="Tanvir_Hasan_Resume.pdf",
                        cover_letter="I am passionate about building robust backend architectures and scalable frontend applications.",
                        screening_answers={"1": "Yes", "2": "3", "3": "React, Python, FastAPI"},
                        screening_score=88,
                        deal_breaker_passed=True,
                        status=ApplicationStatus.SHORTLISTED.value,
                    )
                    db.add(app1)
                    first_job.applications_count = (first_job.applications_count or 0) + 1

                if len(jobs) > 1:
                    second_job = jobs[1]
                    existing_app2 = db.execute(
                        select(JobApplication).where(
                            JobApplication.learner_id == learner_user.id,
                            JobApplication.job_id == second_job.id,
                        )
                    ).scalar_one_or_none()
                    if not existing_app2:
                        app2 = JobApplication(
                            job_id=second_job.id,
                            learner_id=learner_user.id,
                            resume_url="/uploads/resumes/Tanvir_Hasan_Resume.pdf",
                            resume_filename="Tanvir_Hasan_Resume.pdf",
                            cover_letter="Looking forward to contributing to machine learning and cloud pipelines.",
                            screening_answers={},
                            screening_score=75,
                            deal_breaker_passed=True,
                            status=ApplicationStatus.UNDER_REVIEW.value,
                        )
                        db.add(app2)
                        second_job.applications_count = (second_job.applications_count or 0) + 1

                db.commit()
                logger.info("Successfully seeded job applications for sample learner.")

    except Exception as e:
        db.rollback()
        logger.error("Seeding failed: %s", str(e))
        sys.exit(1)
    finally:
        db.close()



if __name__ == "__main__":
    seed_database()
