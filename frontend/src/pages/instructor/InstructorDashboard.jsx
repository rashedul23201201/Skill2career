import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../../hooks/useAuth";
import instructorService from "../../services/instructorService";
import Button from "../../components/forms/Button";
import { ROUTES } from "../../constants";
import {
  GraduationCap,
  BookOpen,
  Users,
  Calendar,
  CheckCircle2,
  Clock,
  AlertCircle,
  ExternalLink,
  Edit3,
  Video,
  FileCheck,
  Plus,
  RefreshCw,
  X,
  Sparkles,
  ArrowRight,
  TrendingUp,
  UserCheck,
} from "lucide-react";

export const InstructorDashboard = () => {
  const { user } = useAuth();
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [editForm, setEditForm] = useState({
    designation: "",
    institution: "",
    qualification: "",
    expertise_domain: "",
    years_experience: "",
    intro_video_url: "",
    bio: "",
    linkedin_url: "",
  });
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  const fetchDashboardData = async (isManual = false) => {
    try {
      if (isManual) setRefreshing(true);
      else setLoading(true);
      setError(null);

      const [summaryRes, profileRes] = await Promise.allSettled([
        instructorService.getDashboardSummary(),
        instructorService.getProfile(),
      ]);

      if (summaryRes.status === "fulfilled" && summaryRes.value?.data) {
        setSummary(summaryRes.value.data);
      } else if (summaryRes.status === "rejected") {
        console.error("Failed to load instructor dashboard summary:", summaryRes.reason);
        setError("Unable to retrieve instructor workspace telemetry. Please check server connectivity.");
      }

      if (profileRes.status === "fulfilled" && profileRes.value?.data) {
        const p = profileRes.value.data;
        setEditForm({
          designation: p.designation || "",
          institution: p.institution || "",
          qualification: p.qualification || "",
          expertise_domain: p.expertise_domain || "",
          years_experience: p.years_experience || "",
          intro_video_url: p.intro_video_url || "",
          bio: p.bio || "",
          linkedin_url: p.linkedin_url || "",
        });
      }
    } catch (err) {
      console.error("Failed to load instructor dashboard:", err);
      setError("Unable to retrieve instructor workspace telemetry. Please check server connectivity.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const handleEditSubmit = async (e) => {
    e.preventDefault();
    try {
      setSaving(true);
      const res = await instructorService.updateProfile(editForm);
      if (res?.data) {
        setSaveSuccess(true);
        setTimeout(() => {
          setSaveSuccess(false);
          setIsEditModalOpen(false);
          fetchDashboardData(true);
        }, 1200);
      }
    } catch (err) {
      console.error("Failed to update instructor profile:", err);
      alert(err.response?.data?.message || "Failed to update profile.");
    } finally {
      setSaving(false);
    }
  };

  // Metrics with mock design fallbacks
  const metrics = summary?.metrics;
  const activeCoursesCount = metrics?.active_courses ?? 6;
  const totalLearnersCount = metrics?.total_learners ?? 248;
  const mockTestsCount = metrics?.mock_tests ?? 12;
  const upcomingInterviewsCount = metrics?.upcoming_interviews ?? 4;

  // Profile details
  const profile = summary?.profile;
  const instructorName = `${user?.first_name || profile?.first_name || "Jubair"} ${user?.last_name || profile?.last_name || "Bin Hasan"}`.trim();
  const designationText = profile?.designation || "CSE Instructor";
  const specializationText = profile?.specialization || "Software Engineering";
  const publishedCount = profile?.published_courses ?? activeCoursesCount;
  const profileCompletionPct = profile?.profile_completion_pct ?? 90;
  const onboardingStatus = profile?.onboarding_status || "APPROVED";

  // Courses list
  const coursesList = summary?.my_courses && summary.my_courses.length > 0
    ? summary.my_courses
    : [
        {
          id: 1,
          title: "Software Engineering",
          enrolled_learners: 128,
          average_progress: 78,
          status: "PUBLISHED",
        },
        {
          id: 2,
          title: "Web Programming",
          enrolled_learners: 84,
          average_progress: 65,
          status: "PUBLISHED",
        },
      ];

  // Learner Performance
  const learnerPerf = summary?.learner_performance;
  const avgCourseProgress = learnerPerf?.average_course_progress !== undefined && learnerPerf.average_course_progress > 0
    ? Math.round(learnerPerf.average_course_progress)
    : 72;
  const avgTestScore = learnerPerf?.average_test_score !== undefined && learnerPerf.average_test_score > 0
    ? Math.round(learnerPerf.average_test_score)
    : 78;
  const completedLearners = learnerPerf?.completed_courses_learners !== undefined && learnerPerf.completed_courses_learners > 0
    ? learnerPerf.completed_courses_learners
    : 94;

  // Upcoming Interview
  const interview = summary?.upcoming_interview;
  const interviewTopic = interview?.topic_or_role || "Backend Development";
  const interviewCandidate = interview?.candidate_name || "Rashedul Islam";
  const interviewScheduleText = interview?.scheduled_at
    ? `${new Date(interview.scheduled_at).toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric", hour: "numeric", minute: "2-digit" })} • ${interview.meeting_platform || "Google Meet"}`
    : "Tomorrow · 3:00 PM (BST) · Google Meet";

  // Recent Activity
  const activityList = summary?.recent_activities && summary.recent_activities.length > 0
    ? summary.recent_activities
    : [
        {
          id: "act-1",
          event_type: "NEW_ENROLLMENT",
          title: "New learner enrolled in Software Engineering",
          description: "2 hours ago",
        },
        {
          id: "act-2",
          event_type: "TEST_SUBMITTED",
          title: "Mock Test submitted by 12 learners",
          description: "Today",
        },
      ];

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-20 text-center">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600 mb-4" />
        <p className="text-slate-600 text-sm font-medium">Loading instructor workspace...</p>
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

      {/* Top Welcome Banner with Profile Card (Matching Instructors dashboard.png) */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
        <div>
          <h1 className="text-3xl sm:text-4xl font-extrabold text-navy-950 font-heading tracking-tight">
            Welcome back, {instructorName}!
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Manage your courses, assessments, and learners from one place.
          </p>
        </div>

        {/* Instructor Profile Summary Badge */}
        <div className="bg-white rounded-2xl border border-slate-200 p-4 sm:p-5 shadow-xs flex items-center justify-between gap-4 max-w-lg w-full">
          <div className="flex items-center space-x-3.5 min-w-0">
            <div className="w-12 h-12 rounded-full overflow-hidden bg-slate-100 border border-slate-200 flex items-center justify-center text-navy-900 font-bold flex-shrink-0 text-sm shadow-xs">
              {profile?.profile_photo_url ? (
                <img
                  src={profile.profile_photo_url}
                  alt={instructorName}
                  className="w-full h-full object-cover"
                />
              ) : (
                <span>
                  {user?.first_name?.[0] || "J"}
                  {user?.last_name?.[0] || "H"}
                </span>
              )}
            </div>

            <div className="min-w-0">
              <div className="text-sm font-bold text-navy-950 truncate font-heading">
                {instructorName}
                <span className="font-normal text-slate-500 text-xs ml-1.5">
                  · {designationText}
                </span>
              </div>
              <p className="text-xs text-slate-500 truncate font-medium mt-0.5">
                Specialization: {specializationText} | Published: {publishedCount}
              </p>
              <div className="flex items-center space-x-2 mt-1.5">
                <div className="w-24 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-emerald-500 rounded-full"
                    style={{ width: `${profileCompletionPct}%` }}
                  />
                </div>
                <span className="text-[11px] font-bold text-emerald-600 whitespace-nowrap">
                  {profileCompletionPct}% profile
                </span>
              </div>
            </div>
          </div>

          <div className="flex items-center space-x-2 flex-shrink-0">
            <button
              type="button"
              onClick={() => setIsEditModalOpen(true)}
              className="px-3 py-1.5 text-xs font-semibold rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 transition-colors shadow-xs"
            >
              Edit Profile
            </button>
          </div>
        </div>
      </div>

      {/* 4 Metric Cards (Matching Instructors dashboard.png) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {/* Metric 1: Active Courses */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs flex items-center justify-between">
          <div>
            <span className="text-xs font-semibold text-slate-500">
              Active Courses
            </span>
            <h3 className="text-3xl font-extrabold text-navy-950 font-heading mt-2">
              {activeCoursesCount}
            </h3>
          </div>
          <div className="w-11 h-11 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center flex-shrink-0">
            <BookOpen className="w-5 h-5" />
          </div>
        </div>

        {/* Metric 2: Total Learners */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs flex items-center justify-between">
          <div>
            <span className="text-xs font-semibold text-slate-500">
              Total Learners
            </span>
            <h3 className="text-3xl font-extrabold text-navy-950 font-heading mt-2">
              {totalLearnersCount}
            </h3>
          </div>
          <div className="w-11 h-11 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center flex-shrink-0">
            <Users className="w-5 h-5" />
          </div>
        </div>

        {/* Metric 3: Mock Tests */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs flex items-center justify-between">
          <div>
            <span className="text-xs font-semibold text-slate-500">
              Mock Tests
            </span>
            <h3 className="text-3xl font-extrabold text-navy-950 font-heading mt-2">
              {mockTestsCount}
            </h3>
          </div>
          <div className="w-11 h-11 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center flex-shrink-0">
            <FileCheck className="w-5 h-5" />
          </div>
        </div>

        {/* Metric 4: Upcoming Interviews */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs flex items-center justify-between">
          <div>
            <span className="text-xs font-semibold text-slate-500">
              Upcoming Interviews
            </span>
            <h3 className="text-3xl font-extrabold text-navy-950 font-heading mt-2">
              {upcomingInterviewsCount}
            </h3>
          </div>
          <div className="w-11 h-11 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center flex-shrink-0">
            <Video className="w-5 h-5" />
          </div>
        </div>
      </div>

      {/* Middle Row: My Courses & Learner Performance */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Card: My Courses */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6 sm:p-7 shadow-xs flex flex-col justify-between space-y-6">
          <div className="space-y-4">
            <div className="flex items-center justify-between">
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

            <div className="space-y-3">
              {coursesList.map((crs) => (
                <div
                  key={crs.id}
                  className="p-4 rounded-xl border border-slate-100 bg-slate-50/60 hover:bg-slate-50 transition-colors flex items-center justify-between gap-4"
                >
                  <div className="space-y-2 min-w-0 flex-1">
                    <h4 className="text-sm font-bold text-navy-950 truncate font-heading">
                      {crs.title}
                    </h4>
                    <p className="text-xs text-slate-500">
                      {crs.enrolled_learners || 0} learners · Progress: {Math.round(crs.average_progress || 0)}%
                    </p>
                    <div className="w-48 h-1.5 bg-slate-200 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-blue-600 rounded-full"
                        style={{ width: `${Math.min(100, Math.max(0, crs.average_progress || 0))}%` }}
                      />
                    </div>
                  </div>

                  <Link
                    to={`/courses/${crs.id}/manage`}
                    className="px-3.5 py-1.5 text-xs font-semibold rounded-lg bg-navy-950 hover:bg-navy-900 text-white shadow-xs flex items-center space-x-1 flex-shrink-0"
                  >
                    <span>Manage Course</span>
                  </Link>
                </div>
              ))}
            </div>
          </div>

          <div className="pt-2 text-xs text-slate-400 flex items-center space-x-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-slate-400" />
            <span>Syllabus audits for the summer semester conclude on Friday.</span>
          </div>
        </div>

        {/* Right Card: Learner Performance */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6 sm:p-7 shadow-xs flex flex-col justify-between space-y-6">
          <div className="space-y-5">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-bold text-navy-950 font-heading">
                Learner Performance
              </h3>
              <span className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-slate-100 text-slate-600">
                Batch 2026
              </span>
            </div>

            {/* Average Course Progress Bar */}
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs font-semibold">
                <span className="text-slate-600">Average Course Progress</span>
                <span className="text-emerald-600 font-bold">{avgCourseProgress}%</span>
              </div>
              <div className="w-full h-2 rounded-full bg-slate-100 overflow-hidden">
                <div
                  className="h-full bg-emerald-500 rounded-full transition-all duration-500"
                  style={{ width: `${avgCourseProgress}%` }}
                />
              </div>
            </div>

            {/* Average Test Score Bar */}
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs font-semibold">
                <span className="text-slate-600">Average Test Score</span>
                <span className="text-blue-600 font-bold">{avgTestScore}%</span>
              </div>
              <div className="w-full h-2 rounded-full bg-slate-100 overflow-hidden">
                <div
                  className="h-full bg-blue-600 rounded-full transition-all duration-500"
                  style={{ width: `${avgTestScore}%` }}
                />
              </div>
            </div>

            {/* Completed Courses Tile */}
            <div className="p-4 rounded-xl bg-blue-50/70 border border-blue-100 flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="w-9 h-9 rounded-lg bg-blue-600 text-white flex items-center justify-center">
                  <GraduationCap className="w-5 h-5" />
                </div>
                <div>
                  <span className="text-xs font-semibold text-slate-600">Completed Courses</span>
                  <p className="text-lg font-bold text-navy-950 font-heading">{completedLearners} learners</p>
                </div>
              </div>
            </div>
          </div>

          <div className="pt-2 text-xs text-slate-500 flex items-center space-x-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500" />
            <span>Overall cohort completion rate is steady across active modules.</span>
          </div>
        </div>
      </div>

      {/* Third Row: Upcoming Interview & Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Card: Upcoming Interview */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs flex flex-col justify-between space-y-5">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                Upcoming Interview
              </span>
              <span className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-blue-50 text-blue-600">
                Mock Interview
              </span>
            </div>

            <div className="p-4 rounded-xl bg-slate-50/80 border border-slate-100 space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-base font-bold text-navy-950 font-heading">
                    {interviewTopic}
                  </h4>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Candidate: <span className="font-semibold text-navy-900">{interviewCandidate}</span>
                  </p>
                </div>
                <div className="w-9 h-9 rounded-full bg-emerald-100 text-emerald-800 font-bold flex items-center justify-center text-xs">
                  {interviewCandidate[0]}
                </div>
              </div>

              <div className="pt-2 border-t border-slate-200/60 flex items-center space-x-2 text-xs text-slate-600">
                <Clock className="w-4 h-4 text-slate-400" />
                <span>{interviewScheduleText}</span>
              </div>
            </div>
          </div>

          <div className="flex justify-end">
            <button
              onClick={() => alert(`Opening interview room for ${interviewTopic}...`)}
              className="px-4 py-2 text-xs font-bold rounded-lg bg-blue-50 text-blue-700 hover:bg-blue-100 transition-colors flex items-center space-x-1"
            >
              <span>View Details</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Right Card: Recent Activity */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs flex flex-col justify-between space-y-4">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-bold text-navy-950 font-heading">
                Recent Activity
              </h3>
              <Link
                to={ROUTES.MESSAGES || "/messages"}
                className="text-xs font-semibold text-blue-600 hover:text-blue-800"
              >
                View All
              </Link>
            </div>

            <div className="space-y-3">
              {activityList.map((act) => (
                <div
                  key={act.id}
                  className="flex items-start space-x-3 p-3 rounded-xl bg-slate-50/60 border border-slate-100"
                >
                  <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5 ${
                    act.event_type === "NEW_ENROLLMENT"
                      ? "bg-blue-100 text-blue-600"
                      : "bg-emerald-100 text-emerald-600"
                  }`}>
                    {act.event_type === "NEW_ENROLLMENT" ? (
                      <Users className="w-4 h-4" />
                    ) : (
                      <CheckCircle2 className="w-4 h-4" />
                    )}
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-xs font-bold text-navy-950 truncate">
                      {act.title}
                    </p>
                    <p className="text-[11px] text-slate-500 mt-0.5">
                      {act.description}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Bar: Quick Actions (Matching Instructors dashboard.png) */}
      <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center space-x-2 text-sm font-bold text-navy-950 font-heading">
          <Sparkles className="w-4 h-4 text-emerald-500" />
          <span>Quick Actions</span>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <Link
            to={ROUTES.COURSE_NEW}
            className="inline-flex items-center space-x-1.5 px-4 py-2 text-xs font-semibold rounded-lg bg-navy-950 hover:bg-navy-900 text-white shadow-xs"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Create Course</span>
          </Link>
          <Link
            to={ROUTES.MOCK_TEST_NEW || "/mock-tests/new"}
            className="inline-flex items-center space-x-1.5 px-4 py-2 text-xs font-semibold rounded-lg border border-slate-200 hover:bg-slate-50 text-slate-700 shadow-xs"
          >
            <FileCheck className="w-3.5 h-3.5" />
            <span>Create Mock Test</span>
          </Link>
          <Link
            to={ROUTES.INSTRUCTOR_COURSES || "/instructor/courses"}
            className="inline-flex items-center space-x-1.5 px-4 py-2 text-xs font-semibold rounded-lg bg-blue-50 text-blue-700 hover:bg-blue-100 shadow-xs"
          >
            <Users className="w-3.5 h-3.5" />
            <span>View Learners</span>
          </Link>
        </div>
      </div>

      {/* Edit Profile Modal */}
      {isEditModalOpen && (
        <div className="fixed inset-0 z-50 overflow-y-auto bg-navy-950/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-2xl w-full p-6 sm:p-8 shadow-2xl relative border border-slate-200">
            <button
              onClick={() => setIsEditModalOpen(false)}
              className="absolute top-6 right-6 text-slate-400 hover:text-slate-600"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="space-y-1 mb-6">
              <h3 className="text-xl font-bold text-navy-950 font-heading">
                Update Instructor Credentials
              </h3>
              <p className="text-xs text-slate-500">
                Keep your academic affiliations, expertise domains, and introductory video updated.
              </p>
            </div>

            {saveSuccess && (
              <div className="mb-4 p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl text-xs font-semibold flex items-center space-x-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                <span>Credentials successfully saved!</span>
              </div>
            )}

            <form onSubmit={handleEditSubmit} className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-navy-900 mb-1">
                    Professional Designation
                  </label>
                  <input
                    type="text"
                    required
                    value={editForm.designation}
                    onChange={(e) => setEditForm({ ...editForm, designation: e.target.value })}
                    placeholder="e.g. Senior Software Architect / Lecturer"
                    className="w-full px-3 py-2 border border-slate-300 rounded-xl text-xs focus:ring-2 focus:ring-emerald-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-navy-900 mb-1">
                    Institution / Organization
                  </label>
                  <input
                    type="text"
                    required
                    value={editForm.institution}
                    onChange={(e) => setEditForm({ ...editForm, institution: e.target.value })}
                    placeholder="e.g. BUET / Brain Station 23"
                    className="w-full px-3 py-2 border border-slate-300 rounded-xl text-xs focus:ring-2 focus:ring-emerald-500 focus:outline-none"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-navy-900 mb-1">
                    Highest Academic Degree
                  </label>
                  <input
                    type="text"
                    value={editForm.qualification}
                    onChange={(e) => setEditForm({ ...editForm, qualification: e.target.value })}
                    placeholder="e.g. M.Sc. in Computer Science"
                    className="w-full px-3 py-2 border border-slate-300 rounded-xl text-xs focus:ring-2 focus:ring-emerald-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-navy-900 mb-1">
                    Expertise Domain
                  </label>
                  <input
                    type="text"
                    value={editForm.expertise_domain}
                    onChange={(e) => setEditForm({ ...editForm, expertise_domain: e.target.value })}
                    placeholder="e.g. Full-Stack Web, AI/ML, Cloud DevOps"
                    className="w-full px-3 py-2 border border-slate-300 rounded-xl text-xs focus:ring-2 focus:ring-emerald-500 focus:outline-none"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-navy-900 mb-1">
                    Years of Experience
                  </label>
                  <input
                    type="text"
                    value={editForm.years_experience}
                    onChange={(e) => setEditForm({ ...editForm, years_experience: e.target.value })}
                    placeholder="e.g. 6+ years"
                    className="w-full px-3 py-2 border border-slate-300 rounded-xl text-xs focus:ring-2 focus:ring-emerald-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-navy-900 mb-1">
                    LinkedIn / Portfolio URL
                  </label>
                  <input
                    type="url"
                    value={editForm.linkedin_url}
                    onChange={(e) => setEditForm({ ...editForm, linkedin_url: e.target.value })}
                    placeholder="https://linkedin.com/in/username"
                    className="w-full px-3 py-2 border border-slate-300 rounded-xl text-xs focus:ring-2 focus:ring-emerald-500 focus:outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-navy-900 mb-1">
                  Introductory Lecture / Sample Video URL
                </label>
                <input
                  type="url"
                  value={editForm.intro_video_url}
                  onChange={(e) => setEditForm({ ...editForm, intro_video_url: e.target.value })}
                  placeholder="https://youtube.com/watch?v=..."
                  className="w-full px-3 py-2 border border-slate-300 rounded-xl text-xs focus:ring-2 focus:ring-emerald-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-navy-900 mb-1">
                  Teaching Philosophy & Professional Biography
                </label>
                <textarea
                  rows={4}
                  value={editForm.bio}
                  onChange={(e) => setEditForm({ ...editForm, bio: e.target.value })}
                  placeholder="Describe your practical teaching approach and accomplishments..."
                  className="w-full px-3 py-2 border border-slate-300 rounded-xl text-xs focus:ring-2 focus:ring-emerald-500 focus:outline-none"
                />
              </div>

              <div className="flex items-center justify-end space-x-3 pt-3 border-t border-slate-100">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setIsEditModalOpen(false)}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  variant="primary"
                  size="sm"
                  disabled={saving}
                  className="bg-emerald-600 hover:bg-emerald-700 text-white"
                >
                  {saving ? "Saving..." : "Save Credentials"}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default InstructorDashboard;
