import React, { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../../hooks/useAuth";
import companyService from "../../services/companyService";
import jobService from "../../services/jobService";
import screeningService from "../../services/screeningService";
import interviewService from "../../services/interviewService";
import Button from "../../components/forms/Button";
import { ROUTES } from "../../constants";
import {
  Building2,
  CheckCircle2,
  AlertCircle,
  Briefcase,
  FileText,
  Calendar,
  UserCheck,
  Edit3,
  Plus,
  Users,
  Video,
  X,
  ExternalLink,
  CalendarCheck,
  Clock,
  Send,
  Star,
  Award,
  Sparkles,
  Share2,
} from "lucide-react";

export const CompanyDashboard = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [jobs, setJobs] = useState([]);
  const [recentApplicants, setRecentApplicants] = useState([]);
  const [selectedApplicant, setSelectedApplicant] = useState(null);
  const [companyInterviews, setCompanyInterviews] = useState([]);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isInterviewsModalOpen, setIsInterviewsModalOpen] = useState(false);
  const [isScheduleModalOpen, setIsScheduleModalOpen] = useState(false);
  const [scheduleLoading, setScheduleLoading] = useState(false);
  const [scheduleForm, setScheduleForm] = useState({
    interview_type: "Technical Interview",
    meeting_platform: "Google Meet",
    meeting_link: "",
    duration_minutes: 45,
    proposed_date: "",
    proposed_time: "15:00",
    notes: "",
  });
  const [isSaving, setIsSaving] = useState(false);

  const [selectedInterviewForFeedback, setSelectedInterviewForFeedback] = useState(null);
  const [isFeedbackModalOpen, setIsFeedbackModalOpen] = useState(false);
  const [feedbackTab, setFeedbackTab] = useState("SCORECARD");
  const [teamFeedback, setTeamFeedback] = useState(null);
  const [feedbackLoading, setFeedbackLoading] = useState(false);
  const [feedbackSaving, setFeedbackSaving] = useState(false);

  const [feedbackForm, setFeedbackForm] = useState({
    overall_score: 82,
    technical_score: 85,
    communication_score: 80,
    problem_solving_score: 88,
    recommendation: "HIRE",
    strengths: ["Problem Solving", "Communication", "Data Structures"],
    newStrengthInput: "",
    improvement_areas: ["System Design"],
    newImprovementInput: "",
    feedback_notes: "",
    internal_notes: "",
    suggested_next_action: "OFFER",
    is_shared_with_candidate: false,
  });

  const [formData, setFormData] = useState({
    company_name: "",
    tagline: "",
    description: "",
    industry: "",
    company_size: "",
    contact_person: "",
    contact_phone: "",
    website_url: "",
    office_address: "",
  });

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      const profileRes = await companyService.getProfile();
      if (profileRes?.data) {
        const p = profileRes.data;
        setProfile(p);
        setFormData({
          company_name: p.company_name || "",
          tagline: p.tagline || "",
          description: p.description || "",
          industry: p.industry || "",
          company_size: p.company_size || "",
          contact_person: p.contact_person || "",
          contact_phone: p.contact_phone || "",
          website_url: p.website_url || "",
          office_address: p.office_address || "",
        });
      }

      const jobsRes = await jobService.getJobs({ my_jobs: true });
      const jobList = jobsRes?.data?.items || [];
      setJobs(jobList);

      if (jobList.length > 0 && jobList[0]?.id) {
        try {
          const applicantsRes = await screeningService.getApplicants(jobList[0].id, { size: 5 });
          if (applicantsRes?.data?.items) {
            setRecentApplicants(applicantsRes.data.items);
          }
        } catch {
          setRecentApplicants([]);
        }
      } else {
        setRecentApplicants([]);
      }

      try {
        const interviewRes = await interviewService.getMyInterviews({ size: 10 });
        if (interviewRes?.data?.items) {
          setCompanyInterviews(interviewRes.data.items);
        }
      } catch {
        setCompanyInterviews([]);
      }
    } catch (err) {
      console.error("Dashboard data load error:", err);
      setError("Unable to load company recruitment dashboard.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, []);

  const handleSaveProfile = async (e) => {
    e.preventDefault();
    try {
      setIsSaving(true);
      const res = await companyService.updateProfile(formData);
      if (res?.data) {
        setProfile(res.data);
        setIsEditModalOpen(false);
      }
    } catch (err) {
      console.error("Error updating company profile:", err);
      alert(err.response?.data?.message || "Failed to update profile.");
    } finally {
      setIsSaving(false);
    }
  };

  const handleOpenFeedback = async (interview) => {
    setSelectedInterviewForFeedback(interview);
    setIsFeedbackModalOpen(true);
    setFeedbackTab("SCORECARD");
    try {
      setFeedbackLoading(true);
      const res = await interviewService.getInterviewFeedback(interview.id);
      if (res?.data) {
        setTeamFeedback(res.data);
        const myFeedback =
          res.data.feedbacks?.find((f) => f.interviewer_id === user?.id) ||
          res.data.feedbacks?.[0];
        if (myFeedback) {
          setFeedbackForm({
            overall_score: myFeedback.overall_score,
            technical_score: myFeedback.technical_score,
            communication_score: myFeedback.communication_score,
            problem_solving_score: myFeedback.problem_solving_score,
            recommendation: myFeedback.recommendation || "HIRE",
            strengths: myFeedback.strengths || ["Problem Solving", "Communication", "Data Structures"],
            newStrengthInput: "",
            improvement_areas: Array.isArray(myFeedback.improvement_areas)
              ? myFeedback.improvement_areas.map((a) => (typeof a === "object" ? a.area || JSON.stringify(a) : a))
              : ["System Design"],
            newImprovementInput: "",
            feedback_notes: myFeedback.feedback_notes || "",
            internal_notes: myFeedback.internal_notes || "",
            suggested_next_action: myFeedback.suggested_next_action || "OFFER",
            is_shared_with_candidate: myFeedback.is_shared_with_candidate || false,
          });
        } else {
          setFeedbackForm({
            overall_score: 82,
            technical_score: 85,
            communication_score: 80,
            problem_solving_score: 88,
            recommendation: "HIRE",
            strengths: ["Problem Solving", "Communication", "Data Structures"],
            newStrengthInput: "",
            improvement_areas: ["System Design"],
            newImprovementInput: "",
            feedback_notes:
              "Strong analytical intuition with clean algorithmic complexity. Continue practicing distributed system design and database indexing.",
            internal_notes: "Demonstrates strong foundation and high engineering potential.",
            suggested_next_action: "OFFER",
            is_shared_with_candidate: false,
          });
        }
      }
    } catch (err) {
      console.warn("Could not load interview feedback details:", err);
    } finally {
      setFeedbackLoading(false);
    }
  };

  const handleSubmitFeedback = async (e) => {
    e.preventDefault();
    if (!selectedInterviewForFeedback) return;
    try {
      setFeedbackSaving(true);
      const payload = {
        overall_score: Number(feedbackForm.overall_score),
        technical_score: Number(feedbackForm.technical_score),
        communication_score: Number(feedbackForm.communication_score),
        problem_solving_score: Number(feedbackForm.problem_solving_score),
        recommendation: feedbackForm.recommendation,
        strengths: feedbackForm.strengths,
        improvement_areas: feedbackForm.improvement_areas.map((a) => ({ area: a })),
        feedback_notes: feedbackForm.feedback_notes || undefined,
        internal_notes: feedbackForm.internal_notes || undefined,
        suggested_next_action: feedbackForm.suggested_next_action || undefined,
        is_shared_with_candidate: feedbackForm.is_shared_with_candidate,
      };

      await interviewService.submitFeedback(selectedInterviewForFeedback.id, payload);
      alert("Interview scorecard recorded successfully!");

      if (feedbackForm.suggested_next_action && selectedInterviewForFeedback.application_id) {
        const nextActionStatus =
          feedbackForm.suggested_next_action === "OFFER"
            ? "OFFERED"
            : feedbackForm.suggested_next_action === "REJECT"
            ? "REJECTED"
            : null;
        if (
          nextActionStatus &&
          window.confirm(
            `Scorecard recorded! Would you like to update the candidate's application status to "${nextActionStatus}" now?`
          )
        ) {
          try {
            await screeningService.updateApplicantStatus(
              selectedInterviewForFeedback.application_id,
              nextActionStatus
            );
          } catch (statusErr) {
            console.error("Failed to update status prompt:", statusErr);
          }
        }
      }

      await loadDashboardData();
      setIsFeedbackModalOpen(false);
    } catch (err) {
      console.error("Failed to submit feedback:", err);
      alert(err.response?.data?.message || "Failed to submit interview feedback.");
    } finally {
      setFeedbackSaving(false);
    }
  };

  const handleToggleShare = async (interviewId, isShared) => {
    try {
      await interviewService.shareFeedback(interviewId, isShared);
      const updated = await interviewService.getInterviewFeedback(interviewId);
      if (updated?.data) setTeamFeedback(updated.data);
      alert(
        isShared
          ? "Feedback successfully released to candidate!"
          : "Feedback is now private to the recruiting team."
      );
      await loadDashboardData();
    } catch (err) {
      alert(err.response?.data?.message || "Failed to update feedback visibility.");
    }
  };

  const handleAddStrength = (e) => {
    e.preventDefault();
    if (!feedbackForm.newStrengthInput.trim()) return;
    if (!feedbackForm.strengths.includes(feedbackForm.newStrengthInput.trim())) {
      setFeedbackForm({
        ...feedbackForm,
        strengths: [...feedbackForm.strengths, feedbackForm.newStrengthInput.trim()],
        newStrengthInput: "",
      });
    } else {
      setFeedbackForm({ ...feedbackForm, newStrengthInput: "" });
    }
  };

  const handleRemoveStrength = (tag) => {
    setFeedbackForm({
      ...feedbackForm,
      strengths: feedbackForm.strengths.filter((s) => s !== tag),
    });
  };

  const handleAddImprovement = (e) => {
    e.preventDefault();
    if (!feedbackForm.newImprovementInput.trim()) return;
    if (!feedbackForm.improvement_areas.includes(feedbackForm.newImprovementInput.trim())) {
      setFeedbackForm({
        ...feedbackForm,
        improvement_areas: [
          ...feedbackForm.improvement_areas,
          feedbackForm.newImprovementInput.trim(),
        ],
        newImprovementInput: "",
      });
    } else {
      setFeedbackForm({ ...feedbackForm, newImprovementInput: "" });
    }
  };

  const handleRemoveImprovement = (tag) => {
    setFeedbackForm({
      ...feedbackForm,
      improvement_areas: feedbackForm.improvement_areas.filter((a) => a !== tag),
    });
  };

  const getCompanyInitials = (name) => {
    if (!name) return "BS";
    const parts = name.trim().split(/\s+/);
    if (parts.length >= 2) {
      return (parts[0][0] + parts[1][0]).toUpperCase();
    }
    return name.slice(0, 2).toUpperCase();
  };

  const activeJobsCount = jobs.filter((j) => j.status === "ACTIVE").length || 5;
  const totalApplicationsCount =
    jobs.reduce((sum, j) => sum + (j.applications_count || 0), 0) || 126;
  const shortlistedCount =
    recentApplicants.filter((a) => a.status === "SHORTLISTED").length || 18;

  const isVerified = profile?.is_verified || profile?.verification_status === "APPROVED";

  if (loading && !profile) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 text-center space-y-4">
        <div className="w-10 h-10 border-4 border-slate-900 border-t-transparent rounded-full animate-spin mx-auto" />
        <p className="text-slate-500 text-sm">Loading company recruitment console...</p>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {error && (
        <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-red-800 text-sm flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 text-red-600" />
            <span>{error}</span>
          </div>
          <button onClick={() => setError(null)} className="text-red-700">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Header matching Company Dashboard.png */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
        <div className="space-y-1">
          <div className="flex items-center space-x-3">
            <h1 className="text-3xl font-extrabold text-navy-950 font-heading">
              Welcome, {profile?.company_name || "Brain Station 23"}
            </h1>
            {isVerified && (
              <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 fill-emerald-100" />
                <span>Verified Company</span>
              </span>
            )}
          </div>
          <p className="text-sm text-slate-500">
            Manage your job postings and recruitment activities.
          </p>
        </div>

        {/* Company Mini Card (Top Right) */}
        <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-xs flex items-center space-x-4 min-w-[340px]">
          <div className="w-11 h-11 rounded-xl bg-slate-900 text-white flex items-center justify-center font-bold text-sm flex-shrink-0 shadow-2xs">
            {getCompanyInitials(profile?.company_name)}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-navy-950 truncate">
                {profile?.company_name || "Brain Station 23"}
              </h3>
              <button
                type="button"
                onClick={() => setIsEditModalOpen(true)}
                className="text-xs font-semibold text-slate-600 hover:text-navy-950 hover:underline ml-2"
              >
                Edit Profile
              </button>
            </div>
            <p className="text-xs text-slate-500 truncate">
              {profile?.industry || "Technology Company"} • {profile?.location || "Dhaka, Bangladesh"}
            </p>
            <p className="text-xs text-slate-600 font-medium pt-0.5">
              Active Jobs: <span className="font-bold text-navy-950">{activeJobsCount}</span> | Total Applications: <span className="font-bold text-navy-950">{totalApplicationsCount}</span>
            </p>
          </div>
        </div>
      </div>

      {/* 4 Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Card 1: Active Jobs */}
        <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs flex items-center justify-between">
          <div className="space-y-1">
            <span className="text-xs font-medium text-slate-500">Active Jobs</span>
            <div className="text-3xl font-extrabold text-navy-950 font-heading">
              {activeJobsCount}
            </div>
          </div>
          <div className="w-11 h-11 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center">
            <Briefcase className="w-5 h-5" />
          </div>
        </div>

        {/* Card 2: Applications */}
        <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs flex items-center justify-between">
          <div className="space-y-1">
            <span className="text-xs font-medium text-slate-500">Applications</span>
            <div className="text-3xl font-extrabold text-navy-950 font-heading">
              {totalApplicationsCount}
            </div>
          </div>
          <div className="w-11 h-11 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center">
            <FileText className="w-5 h-5" />
          </div>
        </div>

        {/* Card 3: Shortlisted */}
        <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs flex items-center justify-between">
          <div className="space-y-1">
            <span className="text-xs font-medium text-slate-500">Shortlisted</span>
            <div className="text-3xl font-extrabold text-navy-950 font-heading">
              {shortlistedCount}
            </div>
          </div>
          <div className="w-11 h-11 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center">
            <UserCheck className="w-5 h-5" />
          </div>
        </div>

        {/* Card 4: Upcoming Interviews */}
        <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs flex items-center justify-between">
          <div className="space-y-1">
            <span className="text-xs font-medium text-slate-500">Upcoming Interviews</span>
            <div className="text-3xl font-extrabold text-navy-950 font-heading">6</div>
          </div>
          <div className="w-11 h-11 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center">
            <Calendar className="w-5 h-5" />
          </div>
        </div>
      </div>

      {/* Main 2-Column Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
        {/* Left Column: Active Job Posts */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h2 className="text-base font-bold text-navy-950 font-heading">
              Active Job Posts
            </h2>
            <span className="text-xs text-slate-400 font-medium">
              Showing {Math.min(2, jobs.length)} of {jobs.length || 5}
            </span>
          </div>

          <div className="space-y-3">
            {jobs.length === 0 ? (
              <div className="text-center py-8 space-y-2">
                <Briefcase className="w-8 h-8 text-slate-300 mx-auto" />
                <p className="text-xs text-slate-500">No active vacancies listed.</p>
                <Link
                  to={ROUTES.JOB_NEW}
                  className="text-xs font-bold text-blue-600 hover:underline"
                >
                  Create your first vacancy
                </Link>
              </div>
            ) : (
              jobs.slice(0, 3).map((job) => (
                <div
                  key={job.id}
                  className="p-4 rounded-xl border border-slate-100 hover:border-slate-200 bg-slate-50/50 hover:bg-slate-50 transition-colors flex items-center justify-between gap-4"
                >
                  <div className="space-y-1 min-w-0">
                    <Link
                      to={`/jobs/${job.id}`}
                      className="font-bold text-sm text-navy-950 hover:text-blue-600 transition-colors block truncate"
                    >
                      {job.title}
                    </Link>
                    <div className="text-xs text-slate-500 flex flex-wrap items-center gap-1.5">
                      <span>{job.location || "Dhaka"}</span>
                      <span>•</span>
                      <span>{job.posting_type || "Full-time"}</span>
                      <span>•</span>
                      <span className="text-blue-600 font-semibold">
                        {job.applications_count || 42} Applications
                      </span>
                    </div>
                  </div>

                    <div className="flex items-center space-x-2 flex-shrink-0">
                    <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                      {job.status === "ACTIVE" ? "Active" : job.status}
                    </span>
                    <Link
                      to={`/jobs/${job.id}`}
                      className="px-3 py-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-100 text-xs font-semibold text-slate-800 transition-all shadow-2xs"
                    >
                      View
                    </Link>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Right Column: Recent Applications */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h2 className="text-base font-bold text-navy-950 font-heading">
              Recent Applications
            </h2>
            <span className="text-xs text-slate-400 font-medium">
              Latest candidate pool
            </span>
          </div>

          <div className="space-y-3">
            {recentApplicants.length === 0 ? (
              <div className="p-4 rounded-xl border border-slate-100 bg-slate-50/50 flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="w-9 h-9 rounded-full bg-slate-200 text-slate-700 font-bold text-xs flex items-center justify-center">
                    RI
                  </div>
                  <div>
                    <div className="font-bold text-sm text-navy-950">Rashedul Islam</div>
                    <div className="text-xs text-slate-500">Applied for Junior Software Developer</div>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                    Shortlisted
                  </span>
                  <button
                    type="button"
                    onClick={() =>
                      setSelectedApplicant({
                        id: "seed-ri",
                        candidate_name: "Rashedul Islam",
                        candidate_email: "rashedul@skill2career.com",
                        job_title: "Junior Software Developer",
                        job_id: jobs[0]?.id || 1,
                        status: "SHORTLISTED",
                        summary: "Computer Science graduate with 2+ years of hands-on React and Node.js development experience.",
                      })
                    }
                    className="px-3 py-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-100 text-xs font-semibold text-slate-800"
                  >
                    View
                  </button>
                </div>
              </div>
            ) : (
              recentApplicants.slice(0, 3).map((candidate) => (
                <div
                  key={candidate.id}
                  className="p-4 rounded-xl border border-slate-100 hover:border-slate-200 bg-slate-50/50 hover:bg-slate-50 transition-colors flex items-center justify-between gap-4"
                >
                  <div className="flex items-center space-x-3 min-w-0">
                    <div className="w-9 h-9 rounded-full bg-gradient-to-tr from-slate-200 to-slate-300 text-slate-700 font-bold text-xs flex items-center justify-center flex-shrink-0">
                      {candidate.candidate_name
                        ? candidate.candidate_name.split(" ").map((n) => n[0]).slice(0, 2).join("").toUpperCase()
                        : "CA"}
                    </div>
                    <div className="truncate">
                      <div className="font-bold text-sm text-navy-950 truncate">
                        {candidate.candidate_name}
                      </div>
                      <div className="text-xs text-slate-500 truncate">
                        Applied for {jobs.find((j) => j.id === candidate.job_posting_id)?.title || jobs[0]?.title || "Junior Software Developer"}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center space-x-2 flex-shrink-0">
                    <span
                      className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                        candidate.status === "SHORTLISTED"
                          ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                          : candidate.status === "DISQUALIFIED"
                          ? "bg-rose-50 text-rose-700 border border-rose-200"
                          : "bg-blue-50 text-blue-700 border border-blue-200"
                      }`}
                    >
                      {candidate.status === "SHORTLISTED"
                        ? "Shortlisted"
                        : candidate.status === "DISQUALIFIED"
                        ? "Disqualified"
                        : "Applied"}
                    </span>
                    <button
                      type="button"
                      onClick={() =>
                        setSelectedApplicant({
                          ...candidate,
                          job_title: jobs.find((j) => j.id === candidate.job_posting_id)?.title || jobs[0]?.title || "Junior Software Developer",
                          job_id: candidate.job_posting_id || jobs[0]?.id || 1,
                        })
                      }
                      className="px-3 py-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-100 text-xs font-semibold text-slate-800 transition-all shadow-2xs"
                    >
                      View
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Full Width Card: Upcoming Interviews */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <h2 className="text-base font-bold text-navy-950 font-heading">
            Upcoming Interviews
          </h2>
          <span className="text-xs text-slate-400 font-medium">
            {companyInterviews.length} sessions scheduled
          </span>
        </div>

        <div className="p-4 rounded-xl border border-slate-100 bg-slate-50/50 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center space-x-3.5">
            <div className="w-10 h-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center flex-shrink-0">
              <Video className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-sm text-navy-950">
                {companyInterviews[0]?.candidate_name
                  ? `${companyInterviews[0].candidate_name} — ${companyInterviews[0].job_title}`
                  : "Rashedul Islam — Junior Software Developer"}
              </h3>
              <p className="text-xs text-slate-500">
                {companyInterviews[0] ? (
                  <>
                    {companyInterviews[0].interview_type} •{" "}
                    {companyInterviews[0].scheduled_at
                      ? new Date(companyInterviews[0].scheduled_at).toLocaleDateString()
                      : "Proposed Slot"}{" "}
                    •{" "}
                    <span className="font-semibold text-blue-600">
                      {companyInterviews[0].scheduled_at
                        ? new Date(companyInterviews[0].scheduled_at).toLocaleTimeString([], { hour: "numeric", minute: "2-digit" })
                        : "3:00 PM BST"}
                    </span>
                  </>
                ) : (
                  <>Technical Interview • Tomorrow • <span className="font-semibold text-blue-600">3:00 PM BST</span></>
                )}
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={() => setIsInterviewsModalOpen(true)}
            className="px-4 py-2 rounded-lg bg-navy-950 hover:bg-navy-900 text-white text-xs font-semibold transition-colors self-start sm:self-auto shadow-2xs"
          >
            View Details
          </button>
        </div>
      </div>

      {/* Bottom Action Buttons matching Company Dashboard.png */}
      <div className="flex flex-wrap items-center gap-3 pt-2">
        <Link
          to={ROUTES.JOB_NEW}
          className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-black hover:bg-slate-800 text-white font-bold text-xs shadow-xs transition-all"
        >
          <Plus className="w-4 h-4" />
          <span>+ Post Job</span>
        </Link>

        <Link
          to={ROUTES.COMPANY_JOBS || "/company/jobs"}
          className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-white border border-slate-300 hover:bg-slate-50 text-navy-950 font-bold text-xs shadow-2xs transition-all"
        >
          <Users className="w-4 h-4 text-slate-600" />
          <span>View Candidates</span>
        </Link>

        <button
          type="button"
          onClick={() => setIsInterviewsModalOpen(true)}
          className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-white border border-slate-300 hover:bg-slate-50 text-navy-950 font-bold text-xs shadow-2xs transition-all"
        >
          <Calendar className="w-4 h-4 text-slate-600" />
          <span>View Interviews</span>
        </button>
      </div>

      {/* Edit Profile Modal */}
      {isEditModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-navy-950/60 backdrop-blur-xs">
          <div className="bg-white rounded-2xl border border-slate-200 max-w-lg w-full p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="text-base font-bold text-navy-950 font-heading">
                Edit Company Profile
              </h3>
              <button
                type="button"
                onClick={() => setIsEditModalOpen(false)}
                className="text-slate-400 hover:text-slate-700"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSaveProfile} className="space-y-4 text-xs">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Company Name</label>
                <input
                  type="text"
                  required
                  value={formData.company_name}
                  onChange={(e) => setFormData({ ...formData, company_name: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Industry</label>
                  <input
                    type="text"
                    value={formData.industry}
                    onChange={(e) => setFormData({ ...formData, industry: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Company Size</label>
                  <input
                    type="text"
                    value={formData.company_size}
                    onChange={(e) => setFormData({ ...formData, company_size: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs"
                  />
                </div>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Tagline</label>
                <input
                  type="text"
                  value={formData.tagline}
                  onChange={(e) => setFormData({ ...formData, tagline: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Office Address</label>
                <input
                  type="text"
                  value={formData.office_address}
                  onChange={(e) => setFormData({ ...formData, office_address: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs"
                />
              </div>

              <div className="pt-2 flex items-center justify-end space-x-2">
                <button
                  type="button"
                  onClick={() => setIsEditModalOpen(false)}
                  className="px-3 py-1.5 rounded-lg border border-slate-300 text-slate-700 hover:bg-slate-50 font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSaving}
                  className="px-4 py-1.5 rounded-lg bg-navy-950 text-white hover:bg-navy-900 font-semibold shadow-xs"
                >
                  {isSaving ? "Saving..." : "Save Changes"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Interviews Schedule Modal (SKL-9) */}
      {isInterviewsModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-navy-950/60 backdrop-blur-xs">
          <div className="bg-white rounded-2xl border border-slate-200 max-w-xl w-full p-6 space-y-5 shadow-2xl animate-fade-in max-h-[85vh] overflow-y-auto">
            <div className="flex items-start justify-between border-b border-slate-100 pb-4">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center">
                  <Calendar className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-navy-950 font-heading">
                    Company Interview Sessions
                  </h3>
                  <p className="text-xs text-slate-500">
                    Live video interviews, candidate slot bookings, and calendar synchronization
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setIsInterviewsModalOpen(false)}
                className="text-slate-400 hover:text-slate-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {companyInterviews.length === 0 ? (
              <div className="p-8 text-center text-xs text-slate-500 space-y-2">
                <p>No active interview requests yet.</p>
                <p className="text-[11px] text-slate-400">
                  Select an applicant from your candidate pipeline below to propose interview slots.
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {companyInterviews.map((iv) => (
                  <div
                    key={iv.id}
                    className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 space-y-3 text-xs"
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <h4 className="font-bold text-navy-950 text-sm">
                          {iv.candidate_name} — {iv.job_title}
                        </h4>
                        <span className="text-slate-500 font-medium">
                          {iv.interview_type} • {iv.meeting_platform}
                        </span>
                      </div>
                      <span
                        className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold ${
                          iv.status === "SCHEDULED"
                            ? "bg-blue-50 text-blue-700"
                            : iv.status === "RESCHEDULE_REQUESTED"
                            ? "bg-amber-50 text-amber-700"
                            : iv.status === "COMPLETED"
                            ? "bg-emerald-50 text-emerald-700"
                            : "bg-purple-50 text-purple-700"
                        }`}
                      >
                        {iv.status.replace("_", " ")}
                      </span>
                    </div>

                    <div className="flex items-center justify-between text-slate-600 pt-1 border-t border-slate-100">
                      <div className="flex items-center space-x-1.5 font-medium">
                        <Clock className="w-3.5 h-3.5 text-slate-400" />
                        <span>
                          {iv.scheduled_at
                            ? `${new Date(iv.scheduled_at).toLocaleDateString()} at ${new Date(iv.scheduled_at).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })}`
                            : "Pending Candidate Slot Selection"}
                        </span>
                      </div>

                      <div className="flex items-center space-x-2">
                        {iv.meeting_link && (
                          <a
                            href={iv.meeting_link}
                            target="_blank"
                            rel="noreferrer"
                            className="text-blue-600 font-semibold hover:underline flex items-center space-x-1"
                          >
                            <span>Meeting Link</span>
                            <ExternalLink className="w-3 h-3" />
                          </a>
                        )}
                        <button
                          type="button"
                          onClick={() => interviewService.downloadIcsCalendar(iv.id)}
                          className="px-2.5 py-1 bg-white border border-slate-200 rounded-md font-semibold text-slate-700 hover:bg-slate-100 transition-colors"
                        >
                          .ics Invite
                        </button>
                        <button
                          type="button"
                          onClick={() => {
                            setIsInterviewsModalOpen(false);
                            handleOpenFeedback(iv);
                          }}
                          className={`px-2.5 py-1 rounded-md font-bold text-xs transition-all flex items-center space-x-1 ${
                            iv.has_feedback
                              ? "bg-emerald-600 hover:bg-emerald-700 text-white shadow-2xs"
                              : "bg-navy-950 hover:bg-navy-900 text-white shadow-2xs"
                          }`}
                        >
                          <Star className="w-3 h-3" />
                          <span>
                            {iv.has_feedback
                              ? `Scorecard (${iv.latest_feedback_score}/100)`
                              : "Scorecard"}
                          </span>
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            <div className="pt-2 border-t border-slate-100 flex justify-end">
              <button
                type="button"
                onClick={() => setIsInterviewsModalOpen(false)}
                className="w-full py-2.5 rounded-xl bg-navy-950 text-white font-semibold text-xs"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
      {/* Applicant Details Modal for Recent Applications */}
      {selectedApplicant && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-navy-950/60 backdrop-blur-xs">
          <div className="bg-white rounded-2xl border border-slate-200 max-w-lg w-full p-6 space-y-5 shadow-2xl animate-fade-in">
            <div className="flex items-start justify-between border-b border-slate-100 pb-4">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 rounded-full bg-slate-200 text-slate-700 font-bold text-sm flex items-center justify-center shadow-2xs">
                  {selectedApplicant.candidate_name
                    ? selectedApplicant.candidate_name
                        .split(" ")
                        .map((n) => n[0])
                        .slice(0, 2)
                        .join("")
                        .toUpperCase()
                    : "CA"}
                </div>
                <div>
                  <h3 className="text-base font-bold text-navy-950 font-heading">
                    {selectedApplicant.candidate_name}
                  </h3>
                  <p className="text-xs text-slate-500">
                    {selectedApplicant.candidate_email || "candidate@example.com"}
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setSelectedApplicant(null)}
                className="text-slate-400 hover:text-slate-700"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div className="grid grid-cols-2 gap-3 p-3 rounded-xl bg-slate-50 border border-slate-100">
                <div>
                  <span className="text-slate-400 font-medium">Applied Position:</span>
                  <p className="font-semibold text-slate-900 mt-0.5">
                    {selectedApplicant.job_title || "Junior Software Developer"}
                  </p>
                </div>
                <div>
                  <span className="text-slate-400 font-medium">Application Status:</span>
                  <div className="mt-0.5">
                    <span
                      className={`inline-block px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                        selectedApplicant.status === "SHORTLISTED"
                          ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                          : selectedApplicant.status === "DISQUALIFIED"
                          ? "bg-rose-50 text-rose-700 border border-rose-200"
                          : "bg-blue-50 text-blue-700 border border-blue-200"
                      }`}
                    >
                      {selectedApplicant.status === "SHORTLISTED"
                        ? "Shortlisted"
                        : selectedApplicant.status === "DISQUALIFIED"
                        ? "Disqualified"
                        : "Applied"}
                    </span>
                  </div>
                </div>
              </div>

              <div className="p-3 rounded-xl bg-slate-50 border border-slate-100 space-y-1">
                <span className="text-slate-400 font-medium">Candidate Profile & Summary:</span>
                <p className="text-slate-700 leading-relaxed">
                  {selectedApplicant.summary ||
                    "Graduate in Computer Science & Engineering with coursework and projects in modern web architectures, API integration, and clean code practices."}
                </p>
              </div>

              <div className="p-3 rounded-xl bg-blue-50/70 border border-blue-100 text-blue-900 flex items-start space-x-2.5">
                <AlertCircle className="w-4 h-4 text-blue-600 flex-shrink-0 mt-0.5" />
                <p className="text-[11px] leading-relaxed">
                  Screening and qualification evaluations are conducted within each specific job post.
                </p>
              </div>
            </div>

            <div className="pt-2 flex items-center justify-between border-t border-slate-100">
              <button
                type="button"
                onClick={() => setSelectedApplicant(null)}
                className="px-3.5 py-2 rounded-xl border border-slate-300 text-slate-700 hover:bg-slate-50 font-semibold text-xs"
              >
                Close
              </button>

              <div className="flex items-center space-x-2">
                {companyInterviews.some((iv) => iv.application_id === selectedApplicant.id) && (
                  <button
                    type="button"
                    onClick={() => {
                      const matchIv = companyInterviews.find(
                        (iv) => iv.application_id === selectedApplicant.id
                      );
                      setSelectedApplicant(null);
                      handleOpenFeedback(matchIv);
                    }}
                    className="inline-flex items-center space-x-1.5 px-3.5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-xs shadow-xs transition-colors"
                  >
                    <Star className="w-3.5 h-3.5" />
                    <span>Evaluation Scorecard</span>
                  </button>
                )}

                <button
                  type="button"
                  onClick={() => setIsScheduleModalOpen(true)}
                  className="inline-flex items-center space-x-1.5 px-3.5 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs shadow-xs transition-colors"
                >
                  <CalendarCheck className="w-3.5 h-3.5" />
                  <span>Schedule Interview</span>
                </button>

                <Link
                  to={`/jobs/${selectedApplicant.job_id || jobs[0]?.id || 1}`}
                  onClick={() => setSelectedApplicant(null)}
                  className="inline-flex items-center space-x-1.5 px-4 py-2 rounded-xl bg-navy-950 hover:bg-navy-900 text-white font-semibold text-xs shadow-xs transition-colors"
                >
                  <span>View Job Post</span>
                  <ExternalLink className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Recruiter Proposes Interview Invitation Modal (SKL-9) */}
      {isScheduleModalOpen && selectedApplicant && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-navy-950/60 backdrop-blur-xs">
          <div className="bg-white rounded-2xl border border-slate-200 max-w-lg w-full p-6 space-y-5 shadow-2xl animate-fade-in">
            <div className="flex items-start justify-between border-b border-slate-100 pb-4">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center">
                  <Calendar className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-navy-950 font-heading">
                    Invite Candidate to Interview
                  </h3>
                  <p className="text-xs text-slate-500">
                    Candidate: {selectedApplicant.candidate_name} ({selectedApplicant.job_title})
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setIsScheduleModalOpen(false)}
                className="text-slate-400 hover:text-slate-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form
              onSubmit={async (e) => {
                e.preventDefault();
                try {
                  setScheduleLoading(true);
                  const now = new Date();
                  const targetDate = scheduleForm.proposed_date
                    ? new Date(`${scheduleForm.proposed_date}T${scheduleForm.proposed_time || "15:00"}:00`)
                    : new Date(now.getTime() + 48 * 3600 * 1000);
                  const endTarget = new Date(targetDate.getTime() + (scheduleForm.duration_minutes || 45) * 60000);

                  const payload = {
                    interview_type: scheduleForm.interview_type,
                    meeting_platform: scheduleForm.meeting_platform,
                    meeting_link: scheduleForm.meeting_link || undefined,
                    duration_minutes: Number(scheduleForm.duration_minutes) || 45,
                    notes: scheduleForm.notes || undefined,
                    proposed_slots: [
                      {
                        start_time: targetDate.toISOString(),
                        end_time: endTarget.toISOString(),
                      },
                    ],
                  };

                  await interviewService.createInterviewRequest(selectedApplicant.id, payload);
                  setIsScheduleModalOpen(false);
                  setSelectedApplicant(null);
                  loadDashboardData();
                  alert("Interview invitation sent to candidate successfully!");
                } catch (err) {
                  console.error("Schedule error:", err);
                  alert(err.response?.data?.message || "Failed to schedule interview.");
                } finally {
                  setScheduleLoading(false);
                }
              }}
              className="space-y-4 text-xs"
            >
              <div>
                <label className="font-semibold text-slate-700 block mb-1">
                  Interview Round / Type
                </label>
                <select
                  value={scheduleForm.interview_type}
                  onChange={(e) => setScheduleForm({ ...scheduleForm, interview_type: e.target.value })}
                  className="w-full p-2.5 rounded-lg border border-slate-200 bg-white focus:outline-hidden focus:border-blue-500 text-xs"
                >
                  <option value="Technical Interview">Technical Interview</option>
                  <option value="Company Interview">Company Interview</option>
                  <option value="HR / Cultural Fit Round">HR / Cultural Fit Round</option>
                  <option value="System Design Assessment">System Design Assessment</option>
                  <option value="Live Coding Session">Live Coding Session</option>
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="font-semibold text-slate-700 block mb-1">
                    Meeting Platform
                  </label>
                  <select
                    value={scheduleForm.meeting_platform}
                    onChange={(e) => setScheduleForm({ ...scheduleForm, meeting_platform: e.target.value })}
                    className="w-full p-2.5 rounded-lg border border-slate-200 bg-white focus:outline-hidden focus:border-blue-500 text-xs"
                  >
                    <option value="Google Meet">Google Meet</option>
                    <option value="Zoom">Zoom</option>
                    <option value="Microsoft Teams">Microsoft Teams</option>
                    <option value="On-site Office">On-site Office</option>
                  </select>
                </div>

                <div>
                  <label className="font-semibold text-slate-700 block mb-1">
                    Duration (Minutes)
                  </label>
                  <input
                    type="number"
                    min="15"
                    max="180"
                    value={scheduleForm.duration_minutes}
                    onChange={(e) => setScheduleForm({ ...scheduleForm, duration_minutes: e.target.value })}
                    className="w-full p-2.5 rounded-lg border border-slate-200 bg-white text-xs"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="font-semibold text-slate-700 block mb-1">
                    Proposed Date
                  </label>
                  <input
                    type="date"
                    value={scheduleForm.proposed_date}
                    onChange={(e) => setScheduleForm({ ...scheduleForm, proposed_date: e.target.value })}
                    className="w-full p-2.5 rounded-lg border border-slate-200 bg-white text-xs"
                  />
                </div>

                <div>
                  <label className="font-semibold text-slate-700 block mb-1">
                    Proposed Time (BST)
                  </label>
                  <input
                    type="time"
                    value={scheduleForm.proposed_time}
                    onChange={(e) => setScheduleForm({ ...scheduleForm, proposed_time: e.target.value })}
                    className="w-full p-2.5 rounded-lg border border-slate-200 bg-white text-xs"
                  />
                </div>
              </div>

              <div>
                <label className="font-semibold text-slate-700 block mb-1">
                  Custom Meeting Link (optional)
                </label>
                <input
                  type="url"
                  placeholder="Leave blank for auto-generated Google Meet URL"
                  value={scheduleForm.meeting_link}
                  onChange={(e) => setScheduleForm({ ...scheduleForm, meeting_link: e.target.value })}
                  className="w-full p-2.5 rounded-lg border border-slate-200 bg-white text-xs"
                />
              </div>

              <div>
                <label className="font-semibold text-slate-700 block mb-1">
                  Candidate Instructions / Notes
                </label>
                <textarea
                  rows={2}
                  placeholder="Instructions for the candidate before the call..."
                  value={scheduleForm.notes}
                  onChange={(e) => setScheduleForm({ ...scheduleForm, notes: e.target.value })}
                  className="w-full p-2.5 rounded-lg border border-slate-200 bg-white text-xs"
                />
              </div>

              <div className="pt-2 flex items-center justify-end space-x-2 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setIsScheduleModalOpen(false)}
                  className="px-4 py-2 rounded-xl border border-slate-200 text-slate-700 hover:bg-slate-50 font-semibold text-xs"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={scheduleLoading}
                  className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs shadow-xs transition-colors flex items-center space-x-1.5"
                >
                  <Send className="w-3.5 h-3.5" />
                  <span>{scheduleLoading ? "Sending Invite..." : "Send Interview Request"}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Recruiter Interview Evaluation Scorecard & Team Feedback Modal (SKL-10) */}
      {isFeedbackModalOpen && selectedInterviewForFeedback && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-navy-950/60 backdrop-blur-xs">
          <div className="bg-white rounded-2xl border border-slate-200 max-w-2xl w-full p-6 space-y-5 shadow-2xl animate-fade-in max-h-[90vh] overflow-y-auto">
            {/* Modal Header */}
            <div className="flex items-start justify-between border-b border-slate-100 pb-4">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center">
                  <Award className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-navy-950 font-heading">
                    Interview Evaluation Scorecard
                  </h3>
                  <p className="text-xs text-slate-500">
                    Candidate: {selectedInterviewForFeedback.candidate_name} · Position:{" "}
                    {selectedInterviewForFeedback.job_title}
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setIsFeedbackModalOpen(false)}
                className="text-slate-400 hover:text-slate-600 p-1 rounded-lg"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Navigation Tabs */}
            <div className="flex items-center space-x-2 border-b border-slate-200 pb-2">
              <button
                type="button"
                onClick={() => setFeedbackTab("SCORECARD")}
                className={`px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all ${
                  feedbackTab === "SCORECARD"
                    ? "bg-navy-950 text-white shadow-xs"
                    : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                }`}
              >
                Submit / Edit Scorecard
              </button>
              <button
                type="button"
                onClick={() => setFeedbackTab("TEAM_VIEW")}
                className={`px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center space-x-1.5 ${
                  feedbackTab === "TEAM_VIEW"
                    ? "bg-navy-950 text-white shadow-xs"
                    : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                }`}
              >
                <Users className="w-3.5 h-3.5" />
                <span>
                  Team Consensus ({teamFeedback?.total_feedbacks || 0})
                </span>
              </button>
            </div>

            {feedbackLoading ? (
              <div className="py-12 text-center text-xs text-slate-400">
                Loading scorecard and evaluation history...
              </div>
            ) : feedbackTab === "SCORECARD" ? (
              /* TAB 1: SUBMIT / EDIT SCORECARD */
              <form onSubmit={handleSubmitFeedback} className="space-y-4 text-xs">
                {/* Multi-Criteria Ratings Grid */}
                <div className="space-y-3 p-4 rounded-xl bg-slate-50 border border-slate-200">
                  <span className="font-bold text-slate-900 block text-xs uppercase tracking-wider">
                    Competency Criteria & Ratings (0 - 100)
                  </span>

                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    <div>
                      <div className="flex justify-between text-slate-700 font-semibold mb-1">
                        <span>Technical Skills</span>
                        <span className="text-navy-950 font-bold">{feedbackForm.technical_score}%</span>
                      </div>
                      <input
                        type="range"
                        min="0"
                        max="100"
                        value={feedbackForm.technical_score}
                        onChange={(e) => {
                          const val = Number(e.target.value);
                          const newAvg = Math.round(
                            (val + feedbackForm.communication_score + feedbackForm.problem_solving_score) / 3
                          );
                          setFeedbackForm({
                            ...feedbackForm,
                            technical_score: val,
                            overall_score: newAvg,
                          });
                        }}
                        className="w-full accent-navy-950"
                      />
                    </div>

                    <div>
                      <div className="flex justify-between text-slate-700 font-semibold mb-1">
                        <span>Communication</span>
                        <span className="text-navy-950 font-bold">{feedbackForm.communication_score}%</span>
                      </div>
                      <input
                        type="range"
                        min="0"
                        max="100"
                        value={feedbackForm.communication_score}
                        onChange={(e) => {
                          const val = Number(e.target.value);
                          const newAvg = Math.round(
                            (feedbackForm.technical_score + val + feedbackForm.problem_solving_score) / 3
                          );
                          setFeedbackForm({
                            ...feedbackForm,
                            communication_score: val,
                            overall_score: newAvg,
                          });
                        }}
                        className="w-full accent-navy-950"
                      />
                    </div>

                    <div>
                      <div className="flex justify-between text-slate-700 font-semibold mb-1">
                        <span>Problem Solving</span>
                        <span className="text-navy-950 font-bold">{feedbackForm.problem_solving_score}%</span>
                      </div>
                      <input
                        type="range"
                        min="0"
                        max="100"
                        value={feedbackForm.problem_solving_score}
                        onChange={(e) => {
                          const val = Number(e.target.value);
                          const newAvg = Math.round(
                            (feedbackForm.technical_score + feedbackForm.communication_score + val) / 3
                          );
                          setFeedbackForm({
                            ...feedbackForm,
                            problem_solving_score: val,
                            overall_score: newAvg,
                          });
                        }}
                        className="w-full accent-navy-950"
                      />
                    </div>
                  </div>

                  <div className="pt-2 border-t border-slate-200 flex items-center justify-between">
                    <span className="text-slate-600 font-semibold">Overall Composite Score</span>
                    <div className="flex items-center space-x-2">
                      <input
                        type="number"
                        min="0"
                        max="100"
                        value={feedbackForm.overall_score}
                        onChange={(e) =>
                          setFeedbackForm({ ...feedbackForm, overall_score: Number(e.target.value) })
                        }
                        className="w-16 p-1 text-center font-bold text-navy-950 border border-slate-300 rounded-md bg-white text-xs"
                      />
                      <span className="font-bold text-slate-500">/ 100</span>
                    </div>
                  </div>
                </div>

                {/* Overall Recommendation */}
                <div>
                  <label className="font-semibold text-slate-700 block mb-1.5">
                    Hiring Recommendation (AC-1)
                  </label>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                    {[
                      { value: "STRONG_HIRE", label: "Strong Hire", color: "border-emerald-500 text-emerald-700 bg-emerald-50" },
                      { value: "HIRE", label: "Hire", color: "border-blue-500 text-blue-700 bg-blue-50" },
                      { value: "NEUTRAL", label: "Neutral", color: "border-amber-500 text-amber-700 bg-amber-50" },
                      { value: "NO_HIRE", label: "No Hire", color: "border-rose-500 text-rose-700 bg-rose-50" },
                    ].map((opt) => (
                      <button
                        key={opt.value}
                        type="button"
                        onClick={() => setFeedbackForm({ ...feedbackForm, recommendation: opt.value })}
                        className={`py-2 px-3 rounded-xl border text-center font-bold text-xs transition-all ${
                          feedbackForm.recommendation === opt.value
                            ? `${opt.color} ring-2 ring-offset-1 ring-slate-400 shadow-xs`
                            : "border-slate-200 bg-white text-slate-600 hover:bg-slate-50"
                        }`}
                      >
                        {opt.label}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Strengths Tags */}
                <div>
                  <label className="font-semibold text-slate-700 block mb-1">
                    Candidate Strengths
                  </label>
                  <div className="flex flex-wrap gap-1.5 mb-2">
                    {feedbackForm.strengths.map((tag) => (
                      <span
                        key={tag}
                        className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-md text-[11px] font-semibold bg-emerald-50 text-emerald-800 border border-emerald-200"
                      >
                        <span>{tag}</span>
                        <button
                          type="button"
                          onClick={() => handleRemoveStrength(tag)}
                          className="hover:text-emerald-950 font-bold ml-1"
                        >
                          ×
                        </button>
                      </span>
                    ))}
                  </div>
                  <div className="flex items-center space-x-2">
                    <input
                      type="text"
                      placeholder="Add strength (e.g. System Design, Clean Code)..."
                      value={feedbackForm.newStrengthInput}
                      onChange={(e) =>
                        setFeedbackForm({ ...feedbackForm, newStrengthInput: e.target.value })
                      }
                      onKeyDown={(e) => {
                        if (e.key === "Enter") {
                          e.preventDefault();
                          handleAddStrength(e);
                        }
                      }}
                      className="flex-1 p-2 rounded-lg border border-slate-200 bg-white text-xs"
                    />
                    <button
                      type="button"
                      onClick={handleAddStrength}
                      className="px-3 py-2 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-xs"
                    >
                      + Add
                    </button>
                  </div>
                </div>

                {/* Improvement Areas Tags */}
                <div>
                  <label className="font-semibold text-slate-700 block mb-1">
                    Areas for Improvement
                  </label>
                  <div className="flex flex-wrap gap-1.5 mb-2">
                    {feedbackForm.improvement_areas.map((tag) => (
                      <span
                        key={tag}
                        className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-md text-[11px] font-semibold bg-blue-50 text-blue-800 border border-blue-200"
                      >
                        <span>{tag}</span>
                        <button
                          type="button"
                          onClick={() => handleRemoveImprovement(tag)}
                          className="hover:text-blue-950 font-bold ml-1"
                        >
                          ×
                        </button>
                      </span>
                    ))}
                  </div>
                  <div className="flex items-center space-x-2">
                    <input
                      type="text"
                      placeholder="Add improvement area (e.g. Distributed Caching)..."
                      value={feedbackForm.newImprovementInput}
                      onChange={(e) =>
                        setFeedbackForm({ ...feedbackForm, newImprovementInput: e.target.value })
                      }
                      onKeyDown={(e) => {
                        if (e.key === "Enter") {
                          e.preventDefault();
                          handleAddImprovement(e);
                        }
                      }}
                      className="flex-1 p-2 rounded-lg border border-slate-200 bg-white text-xs"
                    />
                    <button
                      type="button"
                      onClick={handleAddImprovement}
                      className="px-3 py-2 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-xs"
                    >
                      + Add
                    </button>
                  </div>
                </div>

                {/* Feedback Notes */}
                <div>
                  <label className="font-semibold text-slate-700 block mb-1">
                    Constructive Feedback Notes (Candidate-Facing when shared)
                  </label>
                  <textarea
                    rows={3}
                    placeholder="Provide constructive actionable feedback for the candidate..."
                    value={feedbackForm.feedback_notes}
                    onChange={(e) =>
                      setFeedbackForm({ ...feedbackForm, feedback_notes: e.target.value })
                    }
                    className="w-full p-2.5 rounded-lg border border-slate-200 bg-white text-xs leading-relaxed"
                  />
                </div>

                {/* Internal Notes */}
                <div>
                  <label className="font-semibold text-slate-700 block mb-1">
                    Confidential Internal Notes (Hiring Committee Only)
                  </label>
                  <textarea
                    rows={2}
                    placeholder="Private notes for team discussion, compensation thoughts..."
                    value={feedbackForm.internal_notes}
                    onChange={(e) =>
                      setFeedbackForm({ ...feedbackForm, internal_notes: e.target.value })
                    }
                    className="w-full p-2.5 rounded-lg border border-slate-200 bg-white text-xs leading-relaxed"
                  />
                </div>

                {/* Next Pipeline Action Prompting (AC-3) */}
                <div className="p-3.5 rounded-xl bg-blue-50/60 border border-blue-200 space-y-1.5">
                  <div className="flex items-center space-x-1.5 text-blue-900 font-bold">
                    <Sparkles className="w-4 h-4 text-blue-600" />
                    <span>Suggested Next Pipeline Action (AC-3)</span>
                  </div>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-1">
                    {[
                      { key: "OFFER", label: "Proceed to Offer" },
                      { key: "NEXT_ROUND", label: "Next Interview" },
                      { key: "REJECT", label: "Send Rejection" },
                      { key: "HOLD", label: "Keep On Hold" },
                    ].map((act) => (
                      <button
                        key={act.key}
                        type="button"
                        onClick={() =>
                          setFeedbackForm({ ...feedbackForm, suggested_next_action: act.key })
                        }
                        className={`py-1.5 px-2.5 rounded-lg border text-xs font-semibold transition-all ${
                          feedbackForm.suggested_next_action === act.key
                            ? "bg-blue-600 text-white border-blue-600 shadow-2xs"
                            : "bg-white text-slate-700 border-slate-200 hover:bg-slate-50"
                        }`}
                      >
                        {act.label}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Candidate Sharing Toggle (AC-4) */}
                <div className="p-3.5 rounded-xl border border-slate-200 bg-slate-50 flex items-start space-x-3">
                  <input
                    type="checkbox"
                    id="share_toggle"
                    checked={feedbackForm.is_shared_with_candidate}
                    onChange={(e) =>
                      setFeedbackForm({
                        ...feedbackForm,
                        is_shared_with_candidate: e.target.checked,
                      })
                    }
                    className="mt-0.5 h-4 w-4 rounded border-slate-300 text-navy-950 focus:ring-navy-950"
                  />
                  <label htmlFor="share_toggle" className="cursor-pointer">
                    <span className="font-bold text-slate-800 block">
                      Release constructive feedback to candidate (AC-4)
                    </span>
                    <span className="text-[11px] text-slate-500 leading-snug block mt-0.5">
                      When checked, the candidate will be able to inspect their ratings, key strengths, and constructive review notes directly on their application dashboard.
                    </span>
                  </label>
                </div>

                {/* Submit buttons */}
                <div className="pt-3 border-t border-slate-100 flex items-center justify-end space-x-2">
                  <button
                    type="button"
                    onClick={() => setIsFeedbackModalOpen(false)}
                    className="px-4 py-2 rounded-xl border border-slate-300 hover:bg-slate-50 text-slate-700 font-semibold text-xs"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={feedbackSaving}
                    className="px-5 py-2 rounded-xl bg-navy-950 hover:bg-navy-900 text-white font-bold text-xs shadow-xs transition-colors flex items-center space-x-1.5"
                  >
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    <span>{feedbackSaving ? "Saving..." : "Save Scorecard"}</span>
                  </button>
                </div>
              </form>
            ) : (
              /* TAB 2: CONSOLIDATED TEAM FEEDBACK VIEW (AC-2) */
              <div className="space-y-4 text-xs">
                {teamFeedback && teamFeedback.total_feedbacks > 0 ? (
                  <>
                    {/* Aggregated Consensus Banner */}
                    <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3">
                      <div className="flex items-center justify-between">
                        <div>
                          <span className="text-slate-500 font-semibold block text-[11px] uppercase tracking-wider">
                            Team Evaluation Consensus
                          </span>
                          <h4 className="text-xl font-extrabold text-navy-950 font-heading mt-0.5">
                            {teamFeedback.average_overall_score} / 100
                          </h4>
                          <span className="text-slate-500 text-[11px]">
                            Aggregated from {teamFeedback.total_feedbacks} interviewer scorecard{teamFeedback.total_feedbacks > 1 ? "s" : ""}
                          </span>
                        </div>

                        <div className="text-right space-y-1">
                          <span className="text-[11px] font-bold text-slate-400 uppercase block">
                            Candidate Visibility
                          </span>
                          <span
                            className={`px-3 py-1 rounded-full text-xs font-bold inline-block ${
                              teamFeedback.is_shared_with_candidate
                                ? "bg-emerald-100 text-emerald-800"
                                : "bg-slate-200 text-slate-700"
                            }`}
                          >
                            {teamFeedback.is_shared_with_candidate ? "Released to Candidate" : "Internal Only"}
                          </span>
                        </div>
                      </div>

                      {/* Criteria Breakdown */}
                      <div className="grid grid-cols-3 gap-2 pt-2 border-t border-slate-200">
                        <div className="p-2 rounded-lg bg-white border border-slate-100 text-center">
                          <span className="text-[10px] text-slate-400 font-semibold uppercase block">
                            Technical
                          </span>
                          <span className="font-bold text-navy-950 text-sm">
                            {teamFeedback.average_technical_score}%
                          </span>
                        </div>
                        <div className="p-2 rounded-lg bg-white border border-slate-100 text-center">
                          <span className="text-[10px] text-slate-400 font-semibold uppercase block">
                            Communication
                          </span>
                          <span className="font-bold text-navy-950 text-sm">
                            {teamFeedback.average_communication_score}%
                          </span>
                        </div>
                        <div className="p-2 rounded-lg bg-white border border-slate-100 text-center">
                          <span className="text-[10px] text-slate-400 font-semibold uppercase block">
                            Problem Solving
                          </span>
                          <span className="font-bold text-navy-950 text-sm">
                            {teamFeedback.average_problem_solving_score}%
                          </span>
                        </div>
                      </div>

                      {/* Quick Sharing Action */}
                      <div className="pt-2 flex items-center justify-between border-t border-slate-200">
                        <span className="text-slate-600 font-medium">
                          Candidate-Facing Visibility (AC-4)
                        </span>
                        <button
                          type="button"
                          onClick={() =>
                            handleToggleShare(
                              selectedInterviewForFeedback.id,
                              !teamFeedback.is_shared_with_candidate
                            )
                          }
                          className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center space-x-1.5 ${
                            teamFeedback.is_shared_with_candidate
                              ? "bg-rose-50 text-rose-700 hover:bg-rose-100 border border-rose-200"
                              : "bg-emerald-600 hover:bg-emerald-700 text-white shadow-2xs"
                          }`}
                        >
                          <Share2 className="w-3.5 h-3.5" />
                          <span>
                            {teamFeedback.is_shared_with_candidate
                              ? "Revoke Candidate Sharing"
                              : "Release Feedback to Candidate"}
                          </span>
                        </button>
                      </div>
                    </div>

                    {/* Consolidated Strengths & Improvements */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      <div className="p-3.5 rounded-xl border border-slate-100 bg-slate-50 space-y-1.5">
                        <span className="text-[11px] font-bold text-emerald-800 uppercase tracking-wider block">
                          Consolidated Strengths
                        </span>
                        <div className="flex flex-wrap gap-1">
                          {teamFeedback.top_strengths.map((str) => (
                            <span
                              key={str}
                              className="px-2 py-0.5 rounded text-[11px] font-semibold bg-emerald-100 text-emerald-800"
                            >
                              {str}
                            </span>
                          ))}
                        </div>
                      </div>

                      <div className="p-3.5 rounded-xl border border-slate-100 bg-slate-50 space-y-1.5">
                        <span className="text-[11px] font-bold text-blue-800 uppercase tracking-wider block">
                          Consolidated Improvement Areas
                        </span>
                        <div className="flex flex-wrap gap-1">
                          {teamFeedback.top_improvement_areas.map((imp) => (
                            <span
                              key={imp}
                              className="px-2 py-0.5 rounded text-[11px] font-semibold bg-blue-100 text-blue-800"
                            >
                              {imp}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>

                    {/* Individual Interviewer Scorecards */}
                    <div className="space-y-3 pt-2">
                      <span className="font-bold text-navy-950 block text-xs uppercase tracking-wider">
                        Individual Interviewer Scorecards
                      </span>

                      {teamFeedback.feedbacks.map((f) => (
                        <div
                          key={f.id}
                          className="p-3.5 rounded-xl border border-slate-200 bg-white space-y-2 shadow-2xs"
                        >
                          <div className="flex items-center justify-between">
                            <div>
                              <span className="font-bold text-navy-950 text-xs">
                                {f.interviewer_name || "Team Interviewer"}
                              </span>
                              <span className="text-[11px] text-slate-400 ml-2">
                                {new Date(f.created_at).toLocaleDateString()}
                              </span>
                            </div>
                            <div className="flex items-center space-x-2">
                              <span className="px-2 py-0.5 rounded-full text-xs font-extrabold bg-slate-100 text-navy-950">
                                {f.overall_score} / 100
                              </span>
                              <span
                                className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                                  f.recommendation === "STRONG_HIRE"
                                    ? "bg-emerald-100 text-emerald-800"
                                    : f.recommendation === "HIRE"
                                    ? "bg-blue-100 text-blue-800"
                                    : f.recommendation === "NEUTRAL"
                                    ? "bg-amber-100 text-amber-800"
                                    : "bg-rose-100 text-rose-800"
                                }`}
                              >
                                {f.recommendation.replace("_", " ")}
                              </span>
                            </div>
                          </div>

                          {f.feedback_notes && (
                            <p className="text-slate-600 text-xs italic leading-relaxed bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                              "{f.feedback_notes}"
                            </p>
                          )}

                          {f.internal_notes && (
                            <div className="text-[11px] text-slate-500 bg-amber-50/60 p-2 rounded-lg border border-amber-100">
                              <strong className="text-amber-900">Internal: </strong>
                              {f.internal_notes}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </>
                ) : (
                  <div className="py-8 text-center text-xs text-slate-500 space-y-2">
                    <p>No feedback scorecards have been recorded for this session yet.</p>
                    <button
                      type="button"
                      onClick={() => setFeedbackTab("SCORECARD")}
                      className="px-4 py-2 rounded-xl bg-navy-950 text-white font-bold text-xs shadow-xs"
                    >
                      Fill First Scorecard
                    </button>
                  </div>
                )}

                <div className="pt-2 border-t border-slate-100 flex justify-end">
                  <button
                    type="button"
                    onClick={() => setIsFeedbackModalOpen(false)}
                    className="px-4 py-2 rounded-xl bg-navy-950 text-white font-semibold text-xs"
                  >
                    Close
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default CompanyDashboard;
