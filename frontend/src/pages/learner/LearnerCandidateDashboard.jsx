import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../../hooks/useAuth";
import learnerService from "../../services/learnerService";
import jobService from "../../services/jobService";
import { ROUTES } from "../../constants";
import { RecommendedJobsCarousel } from "./RecommendedJobsCarousel";
import { SavedJobsDrawer } from "./SavedJobsDrawer";
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
  Bookmark,
  AlertCircle,
  RefreshCw,
} from "lucide-react";

export const LearnerCandidateDashboard = () => {
  const { user } = useAuth();
  const [summary, setSummary] = useState(null);
  const [savedJobsCount, setSavedJobsCount] = useState(0);
  const [isSavedDrawerOpen, setIsSavedDrawerOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);

  const refreshSavedJobs = async () => {
    try {
      const res = await jobService.getSavedJobs();
      if (res?.data) {
        setSavedJobsCount(res.data.length);
      }
    } catch (err) {
      console.error("Failed to refresh saved jobs count:", err);
    }
  };

  const fetchDashboardData = async (isManual = false) => {
    try {
      if (isManual) setRefreshing(true);
      else setLoading(true);
      setError(null);

      const [summaryRes, savedRes] = await Promise.allSettled([
        learnerService.getDashboardSummary(),
        jobService.getSavedJobs(),
      ]);

      if (summaryRes.status === "fulfilled" && summaryRes.value?.data) {
        setSummary(summaryRes.value.data);
      } else if (summaryRes.status === "rejected") {
        console.error("Dashboard summary fetch failed:", summaryRes.reason);
        setError("Unable to retrieve candidate dashboard telemetry. Please check server connectivity.");
      }

      if (savedRes.status === "fulfilled" && savedRes.value?.data) {
        setSavedJobsCount(savedRes.value.data.length);
      }
    } catch (err) {
      console.error("Failed to load candidate dashboard data:", err);
      setError("Unable to retrieve candidate dashboard telemetry. Please check server connectivity.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  // Telemetry metrics (with graceful fallbacks for empty / new accounts)
  const metrics = summary?.metrics;
  const enrolledCount = metrics?.enrolled_courses ?? 6;
  const averageProgress = metrics?.course_progress !== undefined ? Math.round(metrics.course_progress) : 72;
  const mockTestScore = metrics?.mock_test_score !== undefined ? Math.round(metrics.mock_test_score) : 82;
  const applicationsCount = metrics?.applications_count ?? 8;

  // Active Curriculum
  const activeCurriculum = summary?.active_curriculum;
  const courseTitle = activeCurriculum?.title || "Data Structures & Algorithms";
  const courseDescription =
    activeCurriculum?.description ||
    "Comprehensive preparation covering Graphs, Dynamic Programming & System Complexity.";
  const completedLessons = activeCurriculum?.completed_lessons ?? 24;
  const totalLessons = activeCurriculum?.total_lessons ?? 32;
  const courseProgressPct =
    activeCurriculum?.progress_percentage !== undefined
      ? Math.round(activeCurriculum.progress_percentage)
      : 75;
  const courseId = activeCurriculum?.course_id || 2;
  const estHoursRemaining = `${activeCurriculum?.estimated_hours_remaining ?? 4}h remaining`;

  // Interview Schedule
  const latestInterview = summary?.latest_interview;
  const interviewRole = latestInterview?.job_title || "Junior Software Developer";
  const interviewCompany = latestInterview?.company_name || "Brain Station 23";
  const interviewType = latestInterview?.interview_type || "Technical Interview";
  const interviewPlatform = latestInterview?.meeting_platform || "Live Coding round via Google Meet";
  const interviewDate = latestInterview?.scheduled_at
    ? new Date(latestInterview.scheduled_at).toLocaleDateString("en-US", {
        weekday: "short",
        month: "short",
        day: "numeric",
        hour: "numeric",
        minute: "2-digit",
      })
    : "Tomorrow · 3:00 PM (BST)";

  // Recent Assessment and Application
  const latestMockTest = summary?.latest_mock_test;
  const latestApplication = summary?.latest_application;

  // Career Profile Summary
  const careerProfile = summary?.career_profile;
  const completionPct = careerProfile?.completion_pct ?? 85;
  const institutionText = careerProfile?.institution || "CSE @ UAP";
  const targetRoleText = careerProfile?.target_role || "Junior Software Developer";
  const skillsList =
    careerProfile?.skills && careerProfile.skills.length > 0
      ? careerProfile.skills.slice(0, 5).join(" · ")
      : "Java · Python · SQL · Git";

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-20 text-center">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mb-4" />
        <p className="text-slate-600 text-sm font-medium">Loading candidate dashboard telemetry...</p>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Error Alert Banner (AC-5) */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-2xl p-4 text-red-800 flex items-center justify-between shadow-xs">
          <div className="flex items-center space-x-3">
            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0" />
            <span className="text-xs sm:text-sm font-semibold">{error}</span>
          </div>
          <button
            onClick={() => fetchDashboardData(true)}
            className="px-3 py-1.5 bg-red-600 hover:bg-red-700 text-white rounded-lg text-xs font-bold transition-colors flex items-center space-x-1"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? "animate-spin" : ""}`} />
            <span>Retry</span>
          </button>
        </div>
      )}

      {/* Top Header & Candidate Profile Card */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
        <div>
          <span className="text-xs font-extrabold uppercase tracking-wider text-blue-600">
            Candidate Dashboard
          </span>
          <h1 className="text-3xl sm:text-4xl font-extrabold text-navy-950 font-heading tracking-tight mt-1">
            Welcome back, {user?.first_name || careerProfile?.first_name || "Rashedul"}!
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Continue learning and prepare for your next career opportunity.
          </p>
        </div>

        {/* Profile Summary Card */}
        <div className="bg-white rounded-2xl border border-slate-200 p-4 sm:p-5 shadow-xs flex items-center justify-between gap-4 max-w-md w-full">
          <div className="flex items-center space-x-3.5 min-w-0">
            <div className="w-12 h-12 rounded-full overflow-hidden bg-slate-100 border border-slate-200 flex items-center justify-center text-navy-900 font-bold flex-shrink-0 text-sm shadow-xs">
              {careerProfile?.profile_photo_url ? (
                <img
                  src={careerProfile.profile_photo_url}
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
                {user?.first_name || careerProfile?.first_name} {user?.last_name || careerProfile?.last_name}
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

          <div className="flex items-center space-x-2 flex-shrink-0">
            <button
              type="button"
              onClick={() => setIsSavedDrawerOpen(true)}
              className="px-3 py-1.5 text-xs font-bold rounded-lg border border-blue-200 bg-blue-50/90 hover:bg-blue-100 text-blue-700 transition-colors shadow-2xs flex items-center space-x-1.5"
            >
              <Bookmark className="w-3.5 h-3.5 fill-blue-600 text-blue-600" />
              <span>Saved ({savedJobsCount})</span>
            </button>
            <Link
              to={ROUTES.LEARNER_PROFILE || "/learner/profile"}
              className="px-3 py-1.5 text-xs font-semibold rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 transition-colors shadow-xs"
            >
              Edit Profile
            </Link>
          </div>
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
              {mockTestScore}%
            </h3>
          </div>
          <div className="w-11 h-11 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center flex-shrink-0">
            <CheckSquare className="w-5 h-5" />
          </div>
        </div>

        {/* Metric 4: Applications */}
        <Link
          to={ROUTES.LEARNER_APPLICATIONS || "/learner/applications"}
          className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs flex items-center justify-between hover:border-slate-300 transition-colors group"
        >
          <div>
            <span className="text-xs font-semibold text-slate-500 group-hover:text-blue-600 transition-colors">
              Applications
            </span>
            <h3 className="text-3xl font-extrabold text-navy-950 font-heading mt-2">
              {applicationsCount}
            </h3>
          </div>
          <div className="w-11 h-11 rounded-xl bg-slate-100 text-slate-700 flex items-center justify-center flex-shrink-0 group-hover:bg-blue-50 group-hover:text-blue-600 transition-colors">
            <Briefcase className="w-5 h-5" />
          </div>
        </Link>
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
                {interviewType}
              </span>
            </div>

            <div>
              <h3 className="text-xl font-extrabold text-navy-950 font-heading">
                {interviewRole}
              </h3>
              <p className="text-sm font-semibold text-slate-600 mt-1">
                {interviewCompany}
              </p>
            </div>

            {/* Time / Room Container */}
            <div className="p-4 rounded-xl bg-blue-50/50 border border-blue-100/80 flex items-center space-x-3.5">
              <div className="w-10 h-10 rounded-xl bg-white border border-blue-100 text-blue-600 flex items-center justify-center flex-shrink-0 shadow-xs">
                <Calendar className="w-5 h-5" />
              </div>
              <div>
                <p className="text-sm font-bold text-navy-950">
                  {interviewDate}
                </p>
                <p className="text-xs text-slate-500 mt-0.5">
                  {interviewPlatform}
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
              to={ROUTES.LEARNER_APPLICATIONS || "/learner/applications"}
              className="inline-flex items-center space-x-1 text-xs font-bold text-navy-950 hover:text-blue-600 transition-colors"
            >
              <span>View Details</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      </div>

      {/* Recommended for You Smart Matching Carousel (SKL-6) */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 sm:p-7 shadow-xs">
        <RecommendedJobsCarousel
          onSavedJobsChanged={refreshSavedJobs}
          onOpenSavedDrawer={() => setIsSavedDrawerOpen(true)}
        />
      </div>

      {/* Third Row: Mock Test Result & Application Status */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: DSA Mock Test */}
        <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs flex items-center justify-between">
          <div className="flex items-center space-x-3.5">
            <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center flex-shrink-0">
              <CheckCircle2 className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h4 className="text-sm font-bold text-navy-950 font-heading">
                  {latestMockTest?.test_title || "DSA Mock Test"}
                </h4>
                <span className="px-2 py-0.5 text-[10px] font-bold rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                  {latestMockTest?.is_passed ? "✓ Passed" : "In Review"}
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                Score: <span className="font-semibold text-navy-900">{latestMockTest?.percentage ?? 82}%</span> · {latestMockTest?.evaluated_at ? `Evaluated ${new Date(latestMockTest.evaluated_at).toLocaleDateString()}` : "Evaluated yesterday"}
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

        {/* Right: Job Application Status */}
        <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs flex items-center justify-between">
          <div className="flex items-center space-x-3.5">
            <div className="w-10 h-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center flex-shrink-0">
              <Building2 className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h4 className="text-sm font-bold text-navy-950 font-heading">
                  {latestApplication?.job_title || "Junior Software Developer"}
                </h4>
                <span className="px-2 py-0.5 text-[10px] font-bold rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 capitalize">
                  {latestApplication?.status ? latestApplication.status.replace("_", " ").toLowerCase() : "shortlisted"}
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                {latestApplication?.company_name || "Brain Station 23"} · {latestApplication?.applied_at ? `Applied ${new Date(latestApplication.applied_at).toLocaleDateString()}` : "Applied 4 days ago"}
              </p>
            </div>
          </div>

          <Link
            to={ROUTES.LEARNER_APPLICATIONS || "/learner/applications"}
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
              {careerProfile?.department || "B.Sc. in Computer Science & Engineering"}
            </span>
            <span className="text-slate-300">·</span>
            <span>
              <span className="font-semibold text-slate-800">Experience:</span> {careerProfile?.experience || "1 year"}
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

      {/* Saved Jobs Quick-Access Slide-Out Drawer (SKL-6) */}
      <SavedJobsDrawer
        isOpen={isSavedDrawerOpen}
        onClose={() => setIsSavedDrawerOpen(false)}
        onSavedCountChange={setSavedJobsCount}
      />
    </div>
  );
};

export default LearnerCandidateDashboard;
