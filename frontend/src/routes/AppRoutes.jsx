import React from "react";
import { Routes, Route } from "react-router-dom";
import MainLayout from "../layouts/MainLayout";
import Home from "../pages/Home";
import Login from "../pages/Login";
import Register from "../pages/Register";
import ResetPassword from "../pages/ResetPassword";
import VerifyEmail from "../pages/VerifyEmail";
import Dashboard from "../pages/Dashboard";
import AdminDashboard from "../pages/admin/AdminDashboard";
import UserManagement from "../pages/admin/UserManagement";
import Courses from "../pages/Courses";
import CourseDetails from "../pages/CourseDetails";
import CourseManagement from "../pages/CourseManagement";
import CourseLearning from "../pages/CourseLearning";
import CompanyVerifications from "../pages/admin/CompanyVerifications";
import LearnerProfile from "../pages/learner/LearnerProfile";
import { CompanyDashboard, CompanyPublicProfile } from "../pages/company";
import CompanyVerification from "../pages/company/CompanyVerification";
import LearnerApplications from "../pages/learner/LearnerApplications";
import InstructorDashboard from "../pages/instructor/InstructorDashboard";
import InstructorApply from "../pages/instructor/InstructorApply";
import Jobs from "../pages/Jobs";
import JobDetails from "../pages/JobDetails";
import JobManagement from "../pages/JobManagement";
import CandidateScreening from "../pages/CandidateScreening";
import MockTests from "../pages/MockTests";
import MockTestManagement from "../pages/MockTestManagement";
import MockTestAttempt from "../pages/MockTestAttempt";
import TestResult from "../pages/TestResult";
import Forum from "../pages/Forum";
import ForumPostDetail from "../pages/ForumPostDetail";
import NotFound from "../pages/NotFound";
import ProtectedRoute from "../components/common/ProtectedRoute";
import { ROUTES, USER_ROLES } from "../constants";

// Modular placeholder for future sprint navigation items
const FeaturePlaceholder = ({ title, sprint, description }) => (
  <div className="max-w-4xl mx-auto px-4 py-16 text-center space-y-4">
    <div className="inline-flex px-3 py-1 rounded-full text-xs font-bold bg-blue-50 text-blue-700 uppercase">
      {sprint} Feature
    </div>
    <h1 className="text-3xl font-extrabold text-navy-950 font-heading">{title}</h1>
    <p className="text-slate-600 max-w-lg mx-auto text-sm">{description}</p>
  </div>
);

export const AppRoutes = () => {
  return (
    <Routes>
      <Route path={ROUTES.HOME} element={<MainLayout />}>
        {/* Public Routes */}
        <Route index element={<Home />} />
        <Route path={ROUTES.LOGIN} element={<Login />} />
        <Route path={ROUTES.REGISTER} element={<Register />} />
        <Route path={ROUTES.RESET_PASSWORD} element={<ResetPassword />} />
        <Route path={ROUTES.VERIFY_EMAIL} element={<VerifyEmail />} />

        {/* Sprint 2 LMS Course & Lesson Learning Routes (SKL-53 / SKL-55) */}
        <Route path={ROUTES.COURSES} element={<Courses />} />
        <Route path={ROUTES.COURSE_DETAILS} element={<CourseDetails />} />
        <Route path={ROUTES.COURSE_LEARN} element={<CourseLearning />} />
        <Route path={ROUTES.COURSE_LEARN_LESSON} element={<CourseLearning />} />
        <Route
          path={ROUTES.COURSE_NEW}
          element={
            <ProtectedRoute allowedRoles={[USER_ROLES.INSTRUCTOR, USER_ROLES.ADMIN]}>
              <CourseManagement />
            </ProtectedRoute>
          }
        />
        <Route
          path={ROUTES.COURSE_MANAGE}
          element={
            <ProtectedRoute allowedRoles={[USER_ROLES.INSTRUCTOR, USER_ROLES.ADMIN]}>
              <CourseManagement />
            </ProtectedRoute>
          }
        />
        <Route
          path={ROUTES.INSTRUCTOR_COURSES}
          element={
            <ProtectedRoute allowedRoles={[USER_ROLES.INSTRUCTOR, USER_ROLES.ADMIN]}>
              <Courses />
            </ProtectedRoute>
          }
        />

        {/* Sprint 2 Recruitment Routes (SKL-4) */}
        <Route path={ROUTES.JOBS} element={<Jobs />} />
        <Route path={ROUTES.JOB_DETAILS} element={<JobDetails />} />
        <Route
          path={ROUTES.JOB_NEW}
          element={
            <ProtectedRoute allowedRoles={[USER_ROLES.COMPANY, USER_ROLES.ADMIN]}>
              <JobManagement />
            </ProtectedRoute>
          }
        />
        <Route
          path={ROUTES.JOB_MANAGE}
          element={
            <ProtectedRoute allowedRoles={[USER_ROLES.COMPANY, USER_ROLES.ADMIN]}>
              <JobManagement />
            </ProtectedRoute>
          }
        />
        <Route
          path={ROUTES.JOB_SCREENING}
          element={
            <ProtectedRoute allowedRoles={[USER_ROLES.COMPANY, USER_ROLES.ADMIN]}>
              <CandidateScreening />
            </ProtectedRoute>
          }
        />
        <Route
          path={ROUTES.COMPANY_JOBS}
          element={
            <ProtectedRoute allowedRoles={[USER_ROLES.COMPANY, USER_ROLES.ADMIN]}>
              <Jobs />
            </ProtectedRoute>
          }
        />
        {/* Sprint 2 Community Forum & Discussions Routes (SKL-14) */}
        <Route path={ROUTES.FORUM} element={<Forum />} />
        <Route path={ROUTES.FORUM_POST_DETAILS} element={<ForumPostDetail />} />
        <Route path="/forum/posts/:id" element={<ForumPostDetail />} />
        {/* Sprint 2 Assessment Mock Test Routes (SKL-56 / SKL-57) */}
        <Route path={ROUTES.MOCK_TESTS} element={<MockTests />} />
        <Route
          path={ROUTES.MOCK_TEST_TAKE}
          element={
            <ProtectedRoute>
              <MockTestAttempt />
            </ProtectedRoute>
          }
        />
        <Route
          path="/mock-tests/:id/attempt"
          element={
            <ProtectedRoute>
              <MockTestAttempt />
            </ProtectedRoute>
          }
        />
        {/* Sprint 2 Test Results & Performance Analysis Route (SKL-58) */}
        <Route
          path={ROUTES.MOCK_TEST_RESULT}
          element={
            <ProtectedRoute>
              <TestResult />
            </ProtectedRoute>
          }
        />
        <Route
          path={ROUTES.TEST_RESULT}
          element={
            <ProtectedRoute>
              <TestResult />
            </ProtectedRoute>
          }
        />
        <Route
          path="/mock-tests/:id/results"
          element={
            <ProtectedRoute>
              <TestResult />
            </ProtectedRoute>
          }
        />
        <Route
          path={ROUTES.MOCK_TEST_NEW}
          element={
            <ProtectedRoute allowedRoles={[USER_ROLES.INSTRUCTOR, USER_ROLES.ADMIN]}>
              <MockTestManagement />
            </ProtectedRoute>
          }
        />
        <Route
          path={ROUTES.MOCK_TEST_MANAGE}
          element={
            <ProtectedRoute allowedRoles={[USER_ROLES.INSTRUCTOR, USER_ROLES.ADMIN]}>
              <MockTestManagement />
            </ProtectedRoute>
          }
        />

        {/* General Protected Dashboard Route */}
        <Route
          path={ROUTES.DASHBOARD}
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          }
        />

        {/* Protected Learner Profile Routes (SKL-51) */}
        <Route
          path={ROUTES.LEARNER_PROFILE}
          element={
            <ProtectedRoute allowedRoles={[USER_ROLES.LEARNER, USER_ROLES.ADMIN]}>
              <LearnerProfile />
            </ProtectedRoute>
          }
        />
        <Route
          path={ROUTES.PROFILE}
          element={
            <ProtectedRoute allowedRoles={[USER_ROLES.LEARNER, USER_ROLES.ADMIN]}>
              <LearnerProfile />
            </ProtectedRoute>
          }
        />
        <Route
          path={ROUTES.LEARNER_APPLICATIONS}
          element={
            <ProtectedRoute allowedRoles={[USER_ROLES.LEARNER, USER_ROLES.ADMIN]}>
              <LearnerApplications />
            </ProtectedRoute>
          }
        />
        <Route
          path={ROUTES.APPLICATIONS}
          element={
            <ProtectedRoute allowedRoles={[USER_ROLES.LEARNER, USER_ROLES.ADMIN]}>
              <LearnerApplications />
            </ProtectedRoute>
          }
        />

        {/* Protected Company Verification Routes (SKL-2) */}
        <Route
          path={ROUTES.COMPANY_VERIFICATION}
          element={
            <ProtectedRoute allowedRoles={[USER_ROLES.COMPANY, USER_ROLES.ADMIN]}>
              <CompanyVerification />
            </ProtectedRoute>
          }
        />

        {/* Instructor Application Route (SKL-52) */}
        <Route path={ROUTES.INSTRUCTOR_APPLY} element={<InstructorApply />} />

        {/* Protected Instructor Routes (SKL-52) */}
        <Route
          path={ROUTES.INSTRUCTOR_DASHBOARD}
          element={
            <ProtectedRoute allowedRoles={[USER_ROLES.INSTRUCTOR, USER_ROLES.ADMIN]}>
              <InstructorDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path={ROUTES.INSTRUCTOR_PROFILE}
          element={
            <ProtectedRoute allowedRoles={[USER_ROLES.INSTRUCTOR, USER_ROLES.ADMIN]}>
              <InstructorDashboard />
            </ProtectedRoute>
          }
        />

        {/* Protected Admin Routes (SKL-50 / SKL-24 / SKL-2 / SKL-52) */}
        <Route
          path={ROUTES.ADMIN_DASHBOARD}
          element={
            <ProtectedRoute allowedRoles={[USER_ROLES.ADMIN]}>
              <AdminDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path={ROUTES.ADMIN_USERS}
          element={
            <ProtectedRoute allowedRoles={[USER_ROLES.ADMIN]}>
              <UserManagement />
            </ProtectedRoute>
          }
        />
        <Route
          path={ROUTES.ADMIN_VERIFICATIONS}
          element={
            <ProtectedRoute allowedRoles={[USER_ROLES.ADMIN]}>
              <CompanyVerifications />
            </ProtectedRoute>
          }
        />

        {/* Protected Company Dashboard Route (SKL-3) */}
        <Route
          path={ROUTES.COMPANY_DASHBOARD}
          element={
            <ProtectedRoute allowedRoles={[USER_ROLES.COMPANY, USER_ROLES.ADMIN]}>
              <CompanyDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/company/dashboard"
          element={
            <ProtectedRoute allowedRoles={[USER_ROLES.COMPANY, USER_ROLES.ADMIN]}>
              <CompanyDashboard />
            </ProtectedRoute>
          }
        />

        {/* Public Company Profile Route (SKL-3) */}
        <Route path="/companies/:id" element={<CompanyPublicProfile />} />
        <Route path="/company/:id" element={<CompanyPublicProfile />} />

        {/* 404 Route */}
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  );
};

export default AppRoutes;
