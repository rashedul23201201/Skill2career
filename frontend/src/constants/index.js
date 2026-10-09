/**
 * SKILL2CAREER Application Constants
 */

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";

export const USER_ROLES = {
  LEARNER: "LEARNER",
  INSTRUCTOR: "INSTRUCTOR",
  COMPANY: "COMPANY",
  ADMIN: "ADMIN",
};

export const STORAGE_KEYS = {
  TOKEN: "skill2career_access_token",
  REFRESH_TOKEN: "skill2career_refresh_token",
  USER: "skill2career_user",
};

export const ROUTES = {
  HOME: "/",
  LOGIN: "/login",
  REGISTER: "/register",
  RESET_PASSWORD: "/reset-password",
  VERIFY_EMAIL: "/verify-email",
  DASHBOARD: "/dashboard",
  ADMIN_DASHBOARD: "/admin",
  ADMIN_USERS: "/admin/users",
  COURSES: "/courses",
  COURSE_NEW: "/courses/new",
  COURSE_DETAILS: "/courses/:id",
  COURSE_MANAGE: "/courses/:id/manage",
  COURSE_LEARN: "/courses/:id/learn",
  COURSE_LEARN_LESSON: "/courses/:id/learn/:lessonId",
  INSTRUCTOR_COURSES: "/instructor/courses",
  JOBS: "/jobs",
  JOB_NEW: "/jobs/new",
  JOB_DETAILS: "/jobs/:id",
  JOB_MANAGE: "/jobs/:id/manage",
  JOB_SCREENING: "/jobs/:id/screening",
  COMPANY_JOBS: "/company/jobs",
  FORUM: "/forum",
  FORUM_POST_DETAILS: "/forum/posts/:id",
  MOCK_TESTS: "/mock-tests",
  MOCK_TEST_NEW: "/mock-tests/new",
  MOCK_TEST_MANAGE: "/mock-tests/:id/manage",
  MOCK_TEST_TAKE: "/mock-tests/:id/take",
  MOCK_TEST_RESULT: "/mock-tests/attempts/:id/result",
  TEST_RESULT: "/attempts/:id/result",
  LEARNER_PROFILE: "/learner/profile",
  COMPANY_VERIFICATION: "/company/verification",
  ADMIN_VERIFICATIONS: "/admin/verifications",
  PROFILE: "/profile",
  COMPANY_DASHBOARD: "/company/dashboard",
  COMPANY_PUBLIC: "/companies/:id",
  INSTRUCTOR_DASHBOARD: "/instructor/dashboard",
  INSTRUCTOR_PROFILE: "/instructor/profile",
  INSTRUCTOR_APPLY: "/instructor/apply",
  LEARNER_APPLICATIONS: "/learner/applications",
  APPLICATIONS: "/applications",
  INTERVIEWS: "/learner/interviews",
  RECRUITMENT: "/interviews",
};

