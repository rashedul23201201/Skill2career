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
  JOBS: "/jobs",
  FORUM: "/forum",
  MOCK_TESTS: "/mock-tests",
  LEARNER_PROFILE: "/learner/profile",
  COMPANY_VERIFICATION: "/company/verification",
  ADMIN_VERIFICATIONS: "/admin/verifications",
  PROFILE: "/profile",
  COMPANY_DASHBOARD: "/company/dashboard",
  COMPANY_PUBLIC: "/companies/:id",
  INSTRUCTOR_DASHBOARD: "/instructor/dashboard",
  INSTRUCTOR_PROFILE: "/instructor/profile",
  INSTRUCTOR_APPLY: "/instructor/apply",
};
