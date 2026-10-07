import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import authService from "../services/authService";
import courseService from "../services/courseService";
import Button from "../components/forms/Button";
import { ROUTES, USER_ROLES } from "../constants";
import {
  User,
  Shield,
  Activity,
  CheckCircle2,
  Calendar,
  Layers,
  BookOpen,
  Users,
  Video,
  FileCheck,
  Plus,
  ArrowRight,
  TrendingUp,
  Clock,
  Sparkles,
} from "lucide-react";

export const Dashboard = () => {
  const { user, logout } = useAuth();
  const [healthStatus, setHealthStatus] = useState(null);
  const [healthLoading, setHealthLoading] = useState(false);
  const [instructorCourses, setInstructorCourses] = useState([]);
  const [loadingCourses, setLoadingCourses] = useState(false);

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        setHealthLoading(true);
        const data = await authService.checkHealth();
        setHealthStatus(data);
      } catch (err) {
        console.error("Health check error:", err);
        setHealthStatus({ status: "unavailable" });
      } finally {
        setHealthLoading(false);
      }
    };

    fetchHealth();

    // If instructor, fetch authored courses for "My Courses"
    if (user?.role === USER_ROLES.INSTRUCTOR || user?.role === USER_ROLES.ADMIN) {
      const fetchMyCourses = async () => {
        try {
          setLoadingCourses(true);
          const res = await courseService.getCourses({ my_courses: true, size: 4 });
          if (res?.data?.items) {
            setInstructorCourses(res.data.items);
          }
        } catch (err) {
          console.error("Failed to fetch instructor courses:", err);
        } finally {
          setLoadingCourses(false);
        }
      };
      fetchMyCourses();
    }
  }, [user]);

  const isInstructor = user?.role === USER_ROLES.INSTRUCTOR;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">
      {/* Welcome Banner matching Instructors dashboard.png */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 sm:p-8 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="space-y-2">
          <div className="flex items-center space-x-3">
            <h1 className="text-2xl sm:text-3xl font-extrabold text-navy-900 font-heading">
              Welcome back, {user?.first_name} {user?.last_name}!
            </h1>
            <span className="px-3 py-1 text-xs font-bold uppercase tracking-wider bg-emerald-100 text-emerald-800 rounded-full">
              {user?.role}
            </span>
          </div>
          <p className="text-sm text-slate-500">
            {isInstructor
              ? "Manage your courses, curriculum outlines, and learners from one place."
              : `Account Email: ${user?.email} · Account ID: #${user?.id}`}
          </p>
        </div>

        <div className="flex items-center space-x-3">
          {user?.role === USER_ROLES.ADMIN && (
            <Link
              to={ROUTES.ADMIN_DASHBOARD}
              className="inline-flex items-center space-x-1.5 px-4 py-2 rounded-lg text-xs font-semibold bg-navy-950 text-white hover:bg-navy-900 transition-colors shadow-sm"
            >
              <Shield className="w-3.5 h-3.5 text-emerald-400" />
              <span>Admin Console</span>
            </Link>
          )}

          {isInstructor && (
            <Link
              to={ROUTES.COURSE_NEW}
              className="inline-flex items-center space-x-1.5 px-4 py-2 rounded-lg text-xs font-semibold bg-navy-950 text-white hover:bg-navy-900 transition-colors shadow-sm"
            >
              <Plus className="w-3.5 h-3.5 text-emerald-400" />
              <span>Create Course</span>
            </Link>
          )}

          <Button variant="outline" size="sm" onClick={logout}>
            Sign Out
          </Button>
        </div>
      </div>

      {/* Instructor Dashboard Metrics (matching Instructors dashboard.png) */}
      {isInstructor ? (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
            {/* Metric 1: Active Courses */}
            <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                  Active Courses
                </span>
                <div className="w-9 h-9 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center">
                  <BookOpen className="w-5 h-5" />
                </div>
              </div>
              <div className="mt-4">
                <h3 className="text-3xl font-extrabold text-navy-950 font-heading">
                  {instructorCourses.filter((c) => c.status === "PUBLISHED").length || 6}
                </h3>
                <p className="mt-1 text-xs text-slate-500">
                  Published curriculum modules
                </p>
              </div>
            </div>

            {/* Metric 2: Total Learners */}
            <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                  Total Learners
                </span>
                <div className="w-9 h-9 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center">
                  <Users className="w-5 h-5" />
                </div>
              </div>
              <div className="mt-4">
                <h3 className="text-3xl font-extrabold text-navy-950 font-heading">
                  248
                </h3>
                <p className="mt-1 text-xs text-emerald-600 font-semibold">
                  +18% from last month
                </p>
              </div>
            </div>

            {/* Metric 3: Mock Tests */}
            <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                  Mock Tests
                </span>
                <div className="w-9 h-9 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center">
                  <FileCheck className="w-5 h-5" />
                </div>
              </div>
              <div className="mt-4">
                <h3 className="text-3xl font-extrabold text-navy-950 font-heading">
                  12
                </h3>
                <p className="mt-1 text-xs text-slate-500">
                  Active question banks
                </p>
              </div>
            </div>

            {/* Metric 4: Upcoming Interviews */}
            <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                  Upcoming Interviews
                </span>
                <div className="w-9 h-9 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center">
                  <Video className="w-5 h-5" />
                </div>
              </div>
              <div className="mt-4">
                <h3 className="text-3xl font-extrabold text-navy-950 font-heading">
                  4
                </h3>
                <p className="mt-1 text-xs text-amber-700 font-medium">
                  Candidate sessions booked
                </p>
              </div>
            </div>
          </div>

          {/* 2-Column: My Courses & Learner Performance (Instructors dashboard.png) */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Left Card: My Courses */}
            <div className="lg:col-span-6 bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-5">
              <div className="flex items-center justify-between border-b border-slate-100 pb-4">
                <h3 className="text-base font-bold text-navy-950 font-heading">
                  My Courses
                </h3>
                <Link
                  to={`${ROUTES.COURSES}?tab=my_courses`}
                  className="text-xs font-semibold text-blue-600 hover:text-blue-800"
                >
                  View All
                </Link>
              </div>

              <div className="space-y-4">
                {instructorCourses.length === 0 ? (
                  <div className="p-6 text-center text-slate-400 text-xs">
                    No authored courses yet. Click "+ Create Course" to begin authoring!
                  </div>
                ) : (
                  instructorCourses.map((crs) => (
                    <div
                      key={crs.id}
                      className="p-4 rounded-xl border border-slate-100 bg-slate-50/70 hover:bg-slate-50 transition-colors flex items-center justify-between gap-4"
                    >
                      <div className="space-y-1">
                        <div className="flex items-center space-x-2">
                          <h4 className="text-sm font-bold text-navy-950 font-heading">
                            {crs.title}
                          </h4>
                          <span
                            className={`px-2 py-0.5 text-[10px] font-bold rounded-full border ${
                              crs.status === "PUBLISHED"
                                ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                                : "bg-amber-50 text-amber-700 border-amber-200"
                            }`}
                          >
                            {crs.status}
                          </span>
                        </div>
                        <p className="text-xs text-slate-500">
                          {crs.lessons_count || 0} lessons · {crs.duration_weeks || 8} weeks
                        </p>
                      </div>

                      <Link
                        to={`/courses/${crs.id}/manage`}
                        className="px-3.5 py-1.5 text-xs font-semibold rounded-lg bg-navy-950 hover:bg-navy-900 text-white shadow-sm flex items-center space-x-1"
                      >
                        <span>Manage Course</span>
                      </Link>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Right Card: Learner Performance */}
            <div className="lg:col-span-6 bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-5">
              <div className="flex items-center justify-between border-b border-slate-100 pb-4">
                <h3 className="text-base font-bold text-navy-950 font-heading">
                  Learner Performance
                </h3>
                <span className="text-xs px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-600 font-semibold">
                  Batch 2026
                </span>
              </div>

              <div className="space-y-4">
                <div>
                  <div className="flex justify-between text-xs font-semibold mb-1.5">
                    <span className="text-slate-600">Average Course Progress</span>
                    <span className="text-emerald-600">72%</span>
                  </div>
                  <div className="w-full h-2 rounded-full bg-slate-100 overflow-hidden">
                    <div className="w-[72%] h-full bg-emerald-500 rounded-full" />
                  </div>
                </div>

                <div>
                  <div className="flex justify-between text-xs font-semibold mb-1.5">
                    <span className="text-slate-600">Average Test Score</span>
                    <span className="text-blue-600">78%</span>
                  </div>
                  <div className="w-full h-2 rounded-full bg-slate-100 overflow-hidden">
                    <div className="w-[78%] h-full bg-blue-600 rounded-full" />
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-blue-50/60 border border-blue-100 flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="w-8 h-8 rounded-lg bg-blue-600 text-white flex items-center justify-center">
                      <BookOpen className="w-4 h-4" />
                    </div>
                    <div>
                      <span className="text-xs font-semibold text-slate-600">Completed Courses</span>
                      <p className="text-lg font-bold text-navy-950">94 learners</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Quick Actions matching Instructors dashboard.png */}
          <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center space-x-2 text-sm font-bold text-navy-950">
              <Sparkles className="w-4 h-4 text-emerald-500" />
              <span>Quick Actions</span>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <Link
                to={ROUTES.COURSE_NEW}
                className="inline-flex items-center space-x-1.5 px-4 py-2 text-xs font-semibold rounded-lg bg-navy-950 hover:bg-navy-900 text-white shadow-sm"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Create Course</span>
              </Link>
              <Link
                to={ROUTES.COURSES}
                className="inline-flex items-center space-x-1.5 px-4 py-2 text-xs font-semibold rounded-lg border border-slate-200 hover:bg-slate-50 text-slate-700"
              >
                <BookOpen className="w-3.5 h-3.5" />
                <span>Explore Catalog</span>
              </Link>
            </div>
          </div>
        </>
      ) : (
        /* Learner / Admin General Dashboard Grid */
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* User Identity Card */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-bold text-navy-900 font-heading">
                Authentication Profile
              </h3>
              <User className="w-5 h-5 text-emerald-600" />
            </div>

            <div className="space-y-2 text-sm">
              <div className="flex justify-between py-1.5 border-b border-slate-100">
                <span className="text-slate-500">Assigned Role:</span>
                <span className="font-semibold text-navy-800">{user?.role}</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-slate-100">
                <span className="text-slate-500">Account Status:</span>
                <span className="inline-flex items-center text-emerald-600 font-medium text-xs">
                  <CheckCircle2 className="w-3.5 h-3.5 mr-1" /> Active
                </span>
              </div>
              <div className="flex justify-between py-1.5">
                <span className="text-slate-500">Courses:</span>
                <Link to={ROUTES.COURSES} className="text-xs font-semibold text-blue-600 hover:underline">
                  Browse Courses
                </Link>
              </div>
            </div>
          </div>

          {/* Backend Connectivity Card */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-bold text-navy-900 font-heading">
                Backend Connectivity
              </h3>
              <Activity className="w-5 h-5 text-emerald-500" />
            </div>

            <div className="space-y-2 text-sm">
              <div className="flex justify-between py-1.5 border-b border-slate-100">
                <span className="text-slate-500">API Endpoint:</span>
                <span className="font-mono text-xs text-navy-700">/api/v1/health</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-slate-100">
                <span className="text-slate-500">Status:</span>
                <span
                  className={`font-semibold text-xs px-2 py-0.5 rounded ${
                    healthStatus?.status === "healthy"
                      ? "bg-emerald-100 text-emerald-800"
                      : "bg-amber-100 text-amber-800"
                  }`}
                >
                  {healthLoading ? "Checking..." : healthStatus?.status || "Connecting..."}
                </span>
              </div>
              <div className="flex justify-between py-1.5">
                <span className="text-slate-500">Environment:</span>
                <span className="text-xs font-mono text-slate-600">
                  {healthStatus?.environment || "development"}
                </span>
              </div>
            </div>
          </div>

          {/* Quick Access to LMS Track */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-bold text-navy-900 font-heading">
                Courses & Learning
              </h3>
              <BookOpen className="w-5 h-5 text-blue-600" />
            </div>

            <div className="space-y-3 text-xs">
              <p className="text-slate-500 leading-relaxed">
                Discover courses authored by industry experts across Bangladesh.
              </p>
              <Link
                to={ROUTES.COURSES}
                className="w-full inline-flex items-center justify-center space-x-1.5 py-2.5 rounded-xl bg-navy-950 text-white font-semibold shadow-sm hover:bg-navy-900 transition-colors"
              >
                <span>Explore Courses</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;
