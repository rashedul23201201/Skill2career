import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../../hooks/useAuth";
import courseService from "../../services/courseService";
import learnerService from "../../services/learnerService";
import { ROUTES } from "../../constants";
import {
  BookOpen,
  RotateCw,
  CheckSquare,
  Briefcase,
  Clock,
  ArrowRight,
  ExternalLink,
  Calendar,
  Video,
  Building2,
  SlidersHorizontal,
  CheckCircle2,
  ChevronRight,
} from "lucide-react";

export const LearnerCandidateDashboard = () => {
  const { user } = useAuth();
  const [profile, setProfile] = useState(null);
  const [enrollmentData, setEnrollmentData] = useState({
    items: [],
    total: 0,
    average_progress: 0,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;

    const fetchDashboardData = async () => {
      try {
        setLoading(true);
        const [profileRes, enrolledRes] = await Promise.allSettled([
          learnerService.getProfile(),
          courseService.getEnrolledCourses(),
        ]);

        if (!isMounted) return;

        if (profileRes.status === "fulfilled" && profileRes.value) {
          setProfile(profileRes.value);
        }

        if (enrolledRes.status === "fulfilled" && enrolledRes.value) {
          setEnrollmentData(enrolledRes.value);
        }
      } catch (err) {
        console.error("Failed to load candidate dashboard data:", err);
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    fetchDashboardData();

    return () => {
      isMounted = false;
    };
  }, []);

  const enrolledItems = enrollmentData.items || [];
  const activeCourse =
    enrolledItems.find(
      (c) =>
        c.status === "ACTIVE" ||
        (c.title || c.course_title)?.toLowerCase().includes("data structure")
    ) || enrolledItems[0];

  const enrolledCount = enrollmentData.total || (enrolledItems.length > 0 ? enrolledItems.length : 6);
  const averageProgress =
    enrollmentData.average_progress > 0
      ? Math.round(enrollmentData.average_progress)
      : (activeCourse?.progress_percentage ? Math.round(activeCourse.progress_percentage) : 72);

  const completionPct = profile?.completion_pct || 85;
  const institutionText =
    profile?.department && profile?.institution
      ? `${profile.department} @ ${profile.institution}`
      : profile?.institution || profile?.department || "CSE @ UAP";
  const targetRoleText = profile?.target_role || "Junior Software Developer";
  const skillsList =
    profile?.skills && profile.skills.length > 0
      ? profile.skills.slice(0, 5).join(" · ")
      : "Java · Python · SQL · Git";

  const courseTitle =
    activeCourse?.title ||
    activeCourse?.course_title ||
    "Data Structures & Algorithms";
  const courseDescription =
    activeCourse?.description ||
    activeCourse?.course_description ||
    "Comprehensive preparation covering Graphs, Dynamic Programming & System Complexity.";
  const completedLessons =
    activeCourse?.completed_lessons !== undefined
      ? activeCourse.completed_lessons
      : 24;
  const totalLessons =
    activeCourse?.total_lessons !== undefined
      ? activeCourse.total_lessons
      : 32;
  const courseProgressPct =
    activeCourse?.progress_percentage !== undefined
      ? Math.round(activeCourse.progress_percentage)
      : 75;
  const courseId = activeCourse?.course_id || 2;

  const lessonsRemaining = Math.max(1, totalLessons - completedLessons);
  const estHoursRemaining = `${lessonsRemaining > 0 ? lessonsRemaining : 4}h remaining`;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Top Header & Candidate Profile Card */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
        <div>
          <span className="text-xs font-extrabold uppercase tracking-wider text-blue-600">
            Candidate Dashboard
          </span>
          <h1 className="text-3xl sm:text-4xl font-extrabold text-navy-950 font-heading tracking-tight mt-1">
            Welcome back, {user?.first_name || "Rashedul"}!
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Continue learning and prepare for your next career opportunity.
          </p>
        </div>

        {/* Profile Summary Card */}
        <div className="bg-white rounded-2xl border border-slate-200 p-4 sm:p-5 shadow-xs flex items-center justify-between gap-4 max-w-md w-full">
          <div className="flex items-center space-x-3.5 min-w-0">
            <div className="w-12 h-12 rounded-full overflow-hidden bg-slate-100 border border-slate-200 flex items-center justify-center text-navy-900 font-bold flex-shrink-0 text-sm shadow-xs">
              {profile?.profile_photo_url ? (
                <img
                  src={profile.profile_photo_url}
                  alt={user?.first_name}
                  className="w-full h-full object-cover"
                />
              ) : (
                <span>
                  {user?.first_name?.[0] || "R"}
                  {user?.last_name?.[0] || "I"}
                </span>
              )}
            </div>

            <div className="min-w-0">
              <div className="text-sm font-bold text-navy-950 truncate font-heading">
                {user?.first_name} {user?.last_name}
                <span className="font-normal text-slate-500 text-xs ml-1.5">
                  · {institutionText}
                </span>
              </div>
              <p className="text-xs text-slate-600 truncate font-medium mt-0.5">
                {targetRoleText}
              </p>
              <div className="flex items-center space-x-2 mt-1.5">
                <div className="w-24 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-emerald-500 rounded-full"
                    style={{ width: `${completionPct}%` }}
                  />
                </div>
                <span className="text-[11px] font-bold text-emerald-600 whitespace-nowrap">
                  {completionPct}% Complete
                </span>
              </div>
            </div>
          </div>

          <Link
            to={ROUTES.LEARNER_PROFILE || "/learner/profile"}
            className="flex-shrink-0 px-3.5 py-1.5 text-xs font-semibold rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 transition-colors shadow-xs"
          >
            Edit Profile
          </Link>
        </div>
      </div>

      {/* 4 Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {/* Metric 1: Enrolled Courses */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs flex items-center justify-between">
          <div>
            <span className="text-xs font-semibold text-slate-500">
              Enrolled Courses
            </span>
            <h3 className="text-3xl font-extrabold text-navy-950 font-heading mt-2">
              {enrolledCount}
            </h3>
          </div>
          <div className="w-11 h-11 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center flex-shrink-0">
            <BookOpen className="w-5 h-5" />
          </div>
        </div>

        {/* Metric 2: Course Progress */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs flex items-center justify-between">
          <div>
            <span className="text-xs font-semibold text-slate-500">
              Course Progress
            </span>
            <h3 className="text-3xl font-extrabold text-navy-950 font-heading mt-2">
              {averageProgress}%
            </h3>
          </div>
          <div className="w-11 h-11 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center flex-shrink-0">
            <RotateCw className="w-5 h-5" />
          </div>
        </div>

        {/* Metric 3: Mock Test Score */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs flex items-center justify-between">
          <div>
            <span className="text-xs font-semibold text-slate-500">
              Mock Test Score
            </span>
            <h3 className="text-3xl font-extrabold text-navy-950 font-heading mt-2">
              82%
            </h3>
          </div>
          <div className="w-11 h-11 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center flex-shrink-0">
            <CheckSquare className="w-5 h-5" />
          </div>
        </div>

        {/* Metric 4: Applications */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs flex items-center justify-between">
          <div>
            <span className="text-xs font-semibold text-slate-500">
              Applications
            </span>
            <h3 className="text-3xl font-extrabold text-navy-950 font-heading mt-2">
              8
            </h3>
          </div>
          <div className="w-11 h-11 rounded-xl bg-slate-100 text-slate-700 flex items-center justify-center flex-shrink-0">
            <Briefcase className="w-5 h-5" />
          </div>
        </div>
      </div>

      {/* Middle Row: Active Curriculum & Interview Schedule */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Card: ACTIVE CURRICULUM */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6 sm:p-7 shadow-xs flex flex-col justify-between space-y-6">
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                Active Curriculum
              </span>
              <span className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-blue-50 text-blue-600">
                <span className="w-1.5 h-1.5 rounded-full bg-blue-600" />
                <span>Live Track</span>
              </span>
            </div>

            <div>
              <h3 className="text-xl font-extrabold text-navy-950 font-heading">
                {courseTitle}
              </h3>
              <p className="text-xs sm:text-sm text-slate-500 mt-1.5 leading-relaxed">
                {courseDescription}
              </p>
            </div>

            {/* Progress Container */}
            <div className="p-4 rounded-xl bg-blue-50/50 border border-blue-100/80 space-y-2.5">
              <div className="flex items-center justify-between text-xs font-bold">
                <span className="text-slate-700">
                  {completedLessons} of {totalLessons} modules finished
                </span>
                <span className="text-emerald-600">{courseProgressPct}%</span>
              </div>
              <div className="w-full h-2.5 bg-slate-200/80 rounded-full overflow-hidden">
                <div
                  className="h-full bg-emerald-500 rounded-full transition-all duration-500"
                  style={{ width: `${courseProgressPct}%` }}
                />
              </div>
            </div>
          </div>

          <div className="pt-2 flex items-center justify-between">
            <div className="flex items-center space-x-1.5 text-xs text-slate-500 font-medium">
              <Clock className="w-4 h-4 text-slate-400" />
              <span>Est. {estHoursRemaining}</span>
            </div>

            <Link
              to={`/courses/${courseId}/learn`}
              className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl text-xs font-bold bg-navy-950 hover:bg-navy-900 text-white shadow-sm transition-all"
            >
              <span>Continue Learning</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>

        {/* Right Card: INTERVIEW SCHEDULE */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6 sm:p-7 shadow-xs flex flex-col justify-between space-y-6">
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                Interview Schedule
              </span>
              <span className="px-3 py-1 rounded-full text-xs font-semibold bg-blue-50 text-blue-600">
                Technical Interview
              </span>
            </div>

            <div>
              <h3 className="text-xl font-extrabold text-navy-950 font-heading">
                Junior Software Developer
              </h3>
              <p className="text-sm font-semibold text-slate-600 mt-1">
                Brain Station 23
              </p>
            </div>

            {/* Time / Room Container */}
            <div className="p-4 rounded-xl bg-blue-50/50 border border-blue-100/80 flex items-center space-x-3.5">
              <div className="w-10 h-10 rounded-xl bg-white border border-blue-100 text-blue-600 flex items-center justify-center flex-shrink-0 shadow-xs">
                <Calendar className="w-5 h-5" />
              </div>
              <div>
                <p className="text-sm font-bold text-navy-950">
                  Tomorrow · 3:00 PM (BST)
                </p>
                <p className="text-xs text-slate-500 mt-0.5">
                  Live Coding round via Google Meet
                </p>
              </div>
            </div>
          </div>

          <div className="pt-2 flex items-center justify-between">
            <div className="flex items-center space-x-1.5 text-xs text-slate-500 font-medium">
              <Video className="w-4 h-4 text-slate-400" />
              <span>Link active 15m prior</span>
            </div>

            <Link
              to={ROUTES.JOBS || "/jobs"}
              className="inline-flex items-center space-x-1 text-xs font-bold text-navy-950 hover:text-blue-600 transition-colors"
            >
              <span>View Details</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      </div>

      {/* Third Row: Mock Test Result & Application Status */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: DSA Mock Test Passed */}
        <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs flex items-center justify-between">
          <div className="flex items-center space-x-3.5">
            <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center flex-shrink-0">
              <CheckCircle2 className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h4 className="text-sm font-bold text-navy-950 font-heading">
                  DSA Mock Test
                </h4>
                <span className="px-2 py-0.5 text-[10px] font-bold rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                  ✓ Passed
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                Score: <span className="font-semibold text-navy-900">82%</span> · Evaluated yesterday
              </p>
            </div>
          </div>

          <Link
            to={ROUTES.MOCK_TESTS || "/mock-tests"}
            className="text-xs font-bold text-blue-600 hover:text-blue-800 flex items-center space-x-1"
          >
            <span>View Result</span>
            <ChevronRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {/* Right: Job Application Shortlisted */}
        <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs flex items-center justify-between">
          <div className="flex items-center space-x-3.5">
            <div className="w-10 h-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center flex-shrink-0">
              <Building2 className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h4 className="text-sm font-bold text-navy-950 font-heading">
                  Junior Software Developer
                </h4>
                <span className="px-2 py-0.5 text-[10px] font-bold rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                  Shortlisted
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                Brain Station 23 · Applied 4 days ago
              </p>
            </div>
          </div>

          <Link
            to={ROUTES.JOBS || "/jobs"}
            className="text-xs font-bold text-blue-600 hover:text-blue-800 flex items-center space-x-1"
          >
            <span>View Application</span>
            <ChevronRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </div>

      {/* Bottom Row: Career Profile Summary */}
      <div className="bg-white rounded-2xl border border-slate-200 p-5 sm:p-6 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="space-y-2">
          <div className="flex items-center space-x-2 text-sm font-bold text-navy-950 font-heading">
            <Briefcase className="w-4 h-4 text-navy-900" />
            <span>Career Profile</span>
          </div>

          <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-slate-600">
            <span>
              <span className="font-semibold text-slate-800">Education:</span>{" "}
              {profile?.department || "B.Sc. in Computer Science & Engineering"}
            </span>
            <span className="text-slate-300">·</span>
            <span>
              <span className="font-semibold text-slate-800">Experience:</span> 1 year
            </span>
            <span className="text-slate-300">·</span>
            <span>
              <span className="font-semibold text-slate-800">Target Job:</span>{" "}
              {targetRoleText}
            </span>
            <span className="text-slate-300">·</span>
            <span>
              <span className="font-semibold text-slate-800">Skills:</span>{" "}
              {skillsList}
            </span>
          </div>
        </div>

        <Link
          to={ROUTES.LEARNER_PROFILE || "/learner/profile"}
          className="inline-flex items-center space-x-2 px-4 py-2 text-xs font-semibold rounded-xl border border-slate-200 hover:bg-slate-50 text-slate-700 transition-colors shadow-xs flex-shrink-0 self-start md:self-auto"
        >
          <SlidersHorizontal className="w-3.5 h-3.5" />
          <span>Edit Profile</span>
        </Link>
      </div>
    </div>
  );
};

export default LearnerCandidateDashboard;
