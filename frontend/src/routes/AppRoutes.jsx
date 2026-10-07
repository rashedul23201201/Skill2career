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

        {/* Sprint 2 LMS Course Routes (SKL-53) */}
        <Route path={ROUTES.COURSES} element={<Courses />} />
        <Route path={ROUTES.COURSE_DETAILS} element={<CourseDetails />} />
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

        <Route
          path={ROUTES.JOBS}
          element={
            <FeaturePlaceholder
              title="Jobs & Internships"
              sprint="Sprint 3"
              description="Direct placement pipeline matching validated learner competencies with vetted hiring companies."
            />
          }
        />
        <Route
          path={ROUTES.FORUM}
          element={
            <FeaturePlaceholder
              title="Community Forum & Discussions"
              sprint="Sprint 4"
              description="Collaborative peer forum and mentorship channels for university students and career switchers."
            />
          }
        />
        <Route
          path={ROUTES.MOCK_TESTS}
          element={
            <FeaturePlaceholder
              title="Mock Tests & Coding Assessments"
              sprint="Sprint 2"
              description="Real exam simulations and technical assessments with instant grading and badge credentials."
            />
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

        {/* Protected Admin Routes (SKL-50 / SKL-24) */}
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

        {/* 404 Route */}
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  );
};

export default AppRoutes;
