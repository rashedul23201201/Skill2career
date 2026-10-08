import React, { useState, useEffect } from "react";
import { useParams, Link, useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import jobService from "../services/jobService";
import screeningService from "../services/screeningService";
import { ROUTES, USER_ROLES } from "../constants";
import {
  ArrowLeft,
  Building2,
  MapPin,
  Briefcase,
  CheckCircle2,
  XCircle,
  Edit3,
  Trash2,
  ExternalLink,
  Layers,
  Users,
  Plus,
  X,
  Sparkles,
  Send,
} from "lucide-react";

export const JobDetails = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useAuth();

  const [job, setJob] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [actionLoading, setActionLoading] = useState(false);
  const [applyModalOpen, setApplyModalOpen] = useState(false);

  // Tabs: "overview" | "screening"
  const [activeTab, setActiveTab] = useState(
    location.hash === "#screening" ? "screening" : "overview"
  );

  // Screening state for this specific vacancy
  const [screeningQuestions, setScreeningQuestions] = useState([]);
  const [applicantsData, setApplicantsData] = useState({
    items: [],
    total: 0,
    passed_count: 0,
    disqualified_count: 0,
    avg_match_score: 0,
  });
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [selectedCandidate, setSelectedCandidate] = useState(null);
  const [isAddQuestionOpen, setIsAddQuestionOpen] = useState(false);
  const [isTestScreeningOpen, setIsTestScreeningOpen] = useState(false);
  const [newQuestion, setNewQuestion] = useState({
    question_text: "",
    question_type: "NUMERIC",
    options: "",
    is_required: true,
    is_deal_breaker: true,
    deal_breaker_rule: "GTE",
    deal_breaker_value: "2",
    deal_breaker_label: "",
    weight: 20,
  });
  const [testSubmission, setTestSubmission] = useState({
    candidate_name: user ? `${user.first_name || ""} ${user.last_name || ""}`.trim() : "Test Applicant",
    candidate_email: user?.email || "applicant@example.com",
    answers: {},
  });

  const isOwner = Boolean(
    user && (job?.company_id === user.id || (user.role === USER_ROLES.COMPANY && (!job?.company_id || job?.company_id === user.id)))
  );
  const canManage = isOwner || user?.role === USER_ROLES.ADMIN;

  const fetchJobData = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await jobService.getJobById(id);
      if (res?.data) {
        setJob(res.data);
      }
    } catch (err) {
      console.error("Error fetching job details:", err);
      setError("Unable to load job details. This vacancy may be closed or does not exist.");
    } finally {
      setLoading(false);
    }
  };

  const fetchScreeningData = async () => {
    if (!id) return;
    try {
      const [questionsRes, applicantsRes] = await Promise.all([
        screeningService.getScreeningQuestions(id),
        screeningService.getApplicants(id, {
          deal_breaker_passed:
            statusFilter === "PASSED" ? true : statusFilter === "DISQUALIFIED" ? false : undefined,
        }),
      ]);
      if (questionsRes?.data) setScreeningQuestions(questionsRes.data);
      if (applicantsRes?.data) setApplicantsData(applicantsRes.data);
    } catch (err) {
      console.error("Failed to load vacancy screening data:", err);
    }
  };

  useEffect(() => {
    fetchJobData();
  }, [id]);

  useEffect(() => {
    if (canManage) {
      fetchScreeningData();
    }
  }, [id, canManage, statusFilter]);

  const handleToggleStatus = async () => {
    if (!job) return;
    try {
      setActionLoading(true);
      const newStatus = job.status === "ACTIVE" ? "CLOSED" : "ACTIVE";
      const res = await jobService.updateJobStatus(job.id, {
        status: newStatus,
        reason: "Recruiter manual status toggle",
      });
      if (res?.data) {
        setJob(res.data);
      }
    } catch (err) {
      console.error("Status update error:", err);
      alert("Failed to update status. Please try again.");
    } finally {
      setActionLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!job) return;
    if (!window.confirm("Are you sure you want to permanently delete this job posting?")) {
      return;
    }
    try {
      setActionLoading(true);
      await jobService.deleteJob(job.id);
      navigate(ROUTES.JOBS);
    } catch (err) {
      console.error("Delete error:", err);
      alert("Failed to delete job posting.");
    } finally {
      setActionLoading(false);
    }
  };

  const handleStatusUpdate = async (candidateId, nextStatus) => {
    try {
      setActionLoading(true);
      await screeningService.updateApplicantStatus(candidateId, nextStatus);
      await fetchScreeningData();
      if (selectedCandidate?.id === candidateId) {
        setSelectedCandidate((prev) => (prev ? { ...prev, status: nextStatus } : null));
      }
    } catch (err) {
      console.error("Failed to update candidate status:", err);
      alert(err.response?.data?.message || "Failed to update status.");
    } finally {
      setActionLoading(false);
    }
  };

  const handleCreateQuestion = async (e) => {
    e.preventDefault();
    if (!newQuestion.question_text.trim()) return;
    try {
      setActionLoading(true);
      const payload = {
        question_text: newQuestion.question_text.trim(),
        question_type: newQuestion.question_type,
        options:
          newQuestion.question_type === "MULTIPLE_CHOICE"
            ? newQuestion.options.split(",").map((s) => s.trim()).filter(Boolean)
            : null,
        is_required: newQuestion.is_required,
        is_deal_breaker: newQuestion.is_deal_breaker,
        deal_breaker_rule: newQuestion.is_deal_breaker ? newQuestion.deal_breaker_rule : null,
        deal_breaker_value: newQuestion.is_deal_breaker ? newQuestion.deal_breaker_value : null,
        deal_breaker_label: newQuestion.deal_breaker_label.trim() || undefined,
        weight: Number(newQuestion.weight) || 10,
        order_index: screeningQuestions.length + 1,
      };

      await screeningService.addScreeningQuestion(id, payload);
      setIsAddQuestionOpen(false);
      setNewQuestion({
        question_text: "",
        question_type: "NUMERIC",
        options: "",
        is_required: true,
        is_deal_breaker: true,
        deal_breaker_rule: "GTE",
        deal_breaker_value: "2",
        deal_breaker_label: "",
        weight: 20,
      });
      await fetchScreeningData();
    } catch (err) {
      console.error("Failed to add question:", err);
      alert(err.response?.data?.message || "Failed to add question.");
    } finally {
      setActionLoading(false);
    }
  };

  const handleDeleteQuestion = async (questionId) => {
    if (!window.confirm("Remove this screening question from this vacancy?")) return;
    try {
      setActionLoading(true);
      await screeningService.deleteScreeningQuestion(questionId);
      await fetchScreeningData();
    } catch (err) {
      console.error("Failed to delete question:", err);
      alert(err.response?.data?.message || "Failed to delete question.");
    } finally {
      setActionLoading(false);
    }
  };

  const handleSimulateScreening = async (e) => {
    e.preventDefault();
    try {
      setActionLoading(true);
      const res = await screeningService.screenCandidate(id, testSubmission);
      setIsTestScreeningOpen(false);
      await fetchScreeningData();
      if (res?.data) {
        setSelectedCandidate(res.data);
      }
    } catch (err) {
      console.error("Simulation error:", err);
      alert(err.response?.data?.message || "Evaluation failed.");
    } finally {
      setActionLoading(false);
    }
  };

  const getScoreBadgeClass = (score) => {
    if (score >= 80) return "bg-emerald-50 text-emerald-700 font-bold border border-emerald-200";
    if (score >= 60) return "bg-blue-50 text-blue-700 font-bold border border-blue-200";
    return "bg-slate-100 text-slate-700 font-bold border border-slate-200";
  };

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 text-center space-y-4">
        <div className="w-10 h-10 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto" />
        <p className="text-slate-500 text-sm">Loading vacancy details...</p>
      </div>
    );
  }

  if (error || !job) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-16 text-center space-y-4">
        <h2 className="text-2xl font-bold text-navy-950 font-heading">
          Vacancy Not Available
        </h2>
        <p className="text-sm text-slate-500">{error || "This posting does not exist."}</p>
        <Link
          to={ROUTES.JOBS}
          className="inline-flex items-center space-x-2 px-4 py-2 text-xs font-semibold rounded-lg bg-navy-950 text-white"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Jobs</span>
        </Link>
      </div>
    );
  }

  const isInternship = (job.posting_type || "").toLowerCase() === "internship";

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Top Navigation */}
      <div className="flex items-center justify-between">
        <Link
          to={ROUTES.JOBS}
          className="inline-flex items-center space-x-1.5 text-xs font-semibold text-slate-500 hover:text-navy-950 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to All Vacancies</span>
        </Link>

        {canManage && (
          <div className="flex items-center space-x-2">
            <button
              type="button"
              onClick={handleToggleStatus}
              disabled={actionLoading}
              className={`px-3 py-1.5 text-xs font-semibold rounded-lg border transition-colors ${
                job.status === "ACTIVE"
                  ? "border-amber-300 bg-amber-50 text-amber-800 hover:bg-amber-100"
                  : "border-emerald-300 bg-emerald-50 text-emerald-800 hover:bg-emerald-100"
              }`}
            >
              {job.status === "ACTIVE" ? "Close Listing" : "Re-activate Listing"}
            </button>
            <Link
              to={`/jobs/${job.id}/manage`}
              className="inline-flex items-center space-x-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-navy-950 hover:bg-navy-900 text-white shadow-sm transition-all"
            >
              <Edit3 className="w-3.5 h-3.5" />
              <span>Edit Vacancy</span>
            </Link>
            <button
              type="button"
              onClick={handleDelete}
              disabled={actionLoading}
              className="p-2 text-slate-400 hover:text-red-600 rounded-lg hover:bg-red-50 transition-colors"
              title="Delete vacancy"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>

      {/* Hero Header Card */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 sm:p-8 shadow-sm flex flex-col md:flex-row justify-between gap-6">
        <div className="space-y-4 max-w-3xl">
          <div className="flex flex-wrap items-center gap-2">
            <span className="px-3 py-1 text-xs font-semibold rounded-full bg-blue-50 text-blue-700 border border-blue-100">
              {job.posting_type}
            </span>
            <span className="px-3 py-1 text-xs font-semibold rounded-full bg-slate-100 text-slate-700">
              {job.work_mode}
            </span>
            <span className="px-3 py-1 text-xs font-semibold rounded-full bg-emerald-50 text-emerald-700 border border-emerald-100">
              {job.experience_level}
            </span>
            {job.status !== "ACTIVE" && (
              <span className="px-3 py-1 text-xs font-bold rounded-full bg-amber-50 text-amber-700 border border-amber-200">
                {job.status}
              </span>
            )}
          </div>

          <h1 className="text-2xl sm:text-4xl font-extrabold text-navy-950 font-heading">
            {job.title}
          </h1>

          <div className="flex flex-wrap items-center gap-4 text-sm text-slate-600">
            <div className="flex items-center space-x-2">
              <Building2 className="w-4 h-4 text-slate-400" />
              <span className="font-semibold text-navy-950">
                {job.company_name}
              </span>
            </div>

            <div className="flex items-center space-x-1.5 text-slate-500">
              <MapPin className="w-4 h-4 text-slate-400" />
              <span>{job.location}</span>
            </div>

            <div className="flex items-center space-x-1.5 text-slate-500">
              <Layers className="w-4 h-4 text-slate-400" />
              <span>{job.category}</span>
            </div>
          </div>
        </div>

        {/* Compensation & Apply / Recruiter Stats Card */}
        <div className="w-full md:w-80 bg-slate-50 rounded-xl border border-slate-200 p-5 flex flex-col justify-between space-y-4">
          <div className="space-y-1">
            <span className="text-xs uppercase tracking-wider text-slate-400 font-bold">
              {isInternship ? "Stipend & Duration" : "Compensation"}
            </span>
            <div className="text-2xl font-black text-navy-950">
              {job.compensation}
            </div>
            {isInternship && job.duration && (
              <p className="text-xs text-slate-600 font-medium">
                Internship Duration: {job.duration}
              </p>
            )}
            <p className="text-[11px] text-slate-400">
              {job.deadline
                ? `Deadline: ${new Date(job.deadline).toLocaleDateString()}`
                : "Applications reviewed on rolling basis"}
            </p>
          </div>

          {canManage ? (
            <button
              type="button"
              onClick={() => setActiveTab(activeTab === "screening" ? "overview" : "screening")}
              className="w-full py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs shadow-sm transition-all text-center flex items-center justify-center space-x-2"
            >
              <Users className="w-4 h-4" />
              <span>
                {activeTab === "screening"
                  ? "View Vacancy Overview"
                  : `Screen Candidates (${applicantsData.total ?? 0})`}
              </span>
            </button>
          ) : (
            <button
              type="button"
              onClick={() => setApplyModalOpen(true)}
              className="w-full py-2.5 rounded-xl bg-navy-950 hover:bg-navy-900 text-white font-semibold text-xs shadow-sm transition-all text-center"
            >
              Apply to Vacancy
            </button>
          )}
        </div>
      </div>

      {/* Recruiter Tabs: Overview vs Screening */}
      {canManage && (
        <div className="flex items-center space-x-2 border-b border-slate-200">
          <button
            type="button"
            onClick={() => setActiveTab("overview")}
            className={`pb-3 px-4 text-xs font-bold transition-all border-b-2 flex items-center space-x-2 ${
              activeTab === "overview"
                ? "border-navy-950 text-navy-950"
                : "border-transparent text-slate-400 hover:text-slate-700"
            }`}
          >
            <Briefcase className="w-4 h-4" />
            <span>Job Overview & Requirements</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("screening")}
            className={`pb-3 px-4 text-xs font-bold transition-all border-b-2 flex items-center space-x-2 ${
              activeTab === "screening"
                ? "border-blue-600 text-blue-600"
                : "border-transparent text-slate-400 hover:text-slate-700"
            }`}
          >
            <Users className="w-4 h-4" />
            <span>Candidate Screening & Applicants</span>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-extrabold bg-blue-50 text-blue-700 border border-blue-200">
              {applicantsData.total ?? 0}
            </span>
          </button>
        </div>
      )}

      {/* TAB 1: OVERVIEW */}
      {activeTab === "overview" && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <div className="lg:col-span-8 bg-white rounded-2xl border border-slate-200 p-6 sm:p-8 shadow-sm space-y-8">
            {job.skills && job.skills.length > 0 && (
              <div className="space-y-3">
                <h3 className="text-base font-bold text-navy-950 font-heading">
                  Required Key Skills
                </h3>
                <div className="flex flex-wrap gap-2">
                  {job.skills.map((skill, idx) => (
                    <span
                      key={idx}
                      className="px-3 py-1 text-xs font-semibold rounded-lg bg-blue-50 text-blue-700 border border-blue-100"
                    >
                      {skill}
                    </span>
                  ))}
                </div>
              </div>
            )}

            <div className="space-y-3">
              <h3 className="text-base font-bold text-navy-950 font-heading">
                Role Description
              </h3>
              <p className="text-sm text-slate-600 leading-relaxed whitespace-pre-line">
                {job.description}
              </p>
            </div>

            <div className="space-y-3 pt-4 border-t border-slate-100">
              <h3 className="text-base font-bold text-navy-950 font-heading">
                Candidate Requirements & Qualifications
              </h3>
              <p className="text-sm text-slate-600 leading-relaxed whitespace-pre-line">
                {job.requirements}
              </p>
            </div>
          </div>

          <div className="lg:col-span-4 space-y-6 self-start">
            <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-6">
              <div className="space-y-2 border-b border-slate-100 pb-4">
                <h3 className="text-base font-bold text-navy-950 font-heading">
                  About the Company
                </h3>
                <div className="flex items-center space-x-2 text-sm font-semibold text-navy-900">
                  <Building2 className="w-4 h-4 text-blue-600" />
                  <span>{job.company_name}</span>
                </div>
                {job.company_industry && (
                  <p className="text-xs text-slate-500">{job.company_industry}</p>
                )}
                {job.company_location && (
                  <p className="text-xs text-slate-500 flex items-center space-x-1">
                    <MapPin className="w-3.5 h-3.5 text-slate-400" />
                    <span>{job.company_location}</span>
                  </p>
                )}
              </div>

              <div className="space-y-3 text-xs text-slate-600">
                <p className="leading-relaxed">
                  Verified corporate hiring partner on SKILL2CAREER connecting top engineering talent with leading industries in Bangladesh.
                </p>

                {job.company_website && (
                  <a
                    href={job.company_website}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center space-x-1 text-blue-600 hover:underline font-semibold"
                  >
                    <span>Visit Company Website</span>
                    <ExternalLink className="w-3.5 h-3.5" />
                  </a>
                )}
              </div>
            </div>

            {canManage && (
              <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-4">
                <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                  <div>
                    <h3 className="text-base font-bold text-navy-950 font-heading">
                      Candidates Applied ({applicantsData.total || job.applications_count || 0})
                    </h3>
                    <p className="text-xs text-slate-500">
                      Who applied for this vacancy
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => setActiveTab("screening")}
                    className="px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs shadow-xs transition-colors"
                  >
                    Screen Candidates
                  </button>
                </div>

                {applicantsData.items && applicantsData.items.length > 0 ? (
                  <div className="divide-y divide-slate-100">
                    {applicantsData.items.slice(0, 4).map((cand) => (
                      <div key={cand.id} className="py-2.5 flex items-center justify-between">
                        <div className="flex items-center space-x-2.5 min-w-0">
                          <div className="w-7 h-7 rounded-full bg-slate-200 text-slate-700 font-bold text-[10px] flex items-center justify-center flex-shrink-0">
                            {cand.candidate_name
                              ? cand.candidate_name
                                  .split(" ")
                                  .map((n) => n[0])
                                  .slice(0, 2)
                                  .join("")
                                  .toUpperCase()
                              : "CA"}
                          </div>
                          <div className="truncate">
                            <div className="text-xs font-semibold text-navy-950 truncate">
                              {cand.candidate_name}
                            </div>
                            <div className="text-[10px] text-slate-400 truncate">
                              {cand.candidate_email}
                            </div>
                          </div>
                        </div>
                        <span
                          className={`px-2 py-0.5 rounded-full text-[10px] font-semibold flex-shrink-0 ${
                            cand.status === "SHORTLISTED"
                              ? "bg-emerald-50 text-emerald-700"
                              : cand.status === "DISQUALIFIED"
                              ? "bg-rose-50 text-rose-700"
                              : "bg-blue-50 text-blue-700"
                          }`}
                        >
                          {cand.status}
                        </span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-slate-400 py-2">No applicants recorded yet for this job post.</p>
                )}

                <button
                  type="button"
                  onClick={() => setActiveTab("screening")}
                  className="w-full py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-navy-950 font-semibold text-xs transition-colors text-center"
                >
                  Open Candidate Screening Pipeline &rarr;
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 2: CANDIDATE SCREENING PIPELINE FOR THIS SPECIFIC JOB (SKL-8) */}
      {activeTab === "screening" && canManage && (
        <div className="space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h2 className="text-xl font-bold text-navy-950 font-heading">
                Recruitment Pipeline: {job.title}
              </h2>
              <p className="text-xs text-slate-500">
                Screen applicants who applied for this vacancy using automated scoring & deal-breaker rules
              </p>
            </div>

            <div className="flex items-center space-x-2">
              <button
                type="button"
                onClick={() => setIsTestScreeningOpen(true)}
                className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg border border-slate-300 text-slate-700 hover:bg-slate-50 text-xs font-semibold shadow-2xs transition-colors"
              >
                <Sparkles className="w-3.5 h-3.5 text-blue-600" />
                <span>Simulate Screening</span>
              </button>

              <button
                type="button"
                onClick={() => setIsAddQuestionOpen(true)}
                className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-navy-950 hover:bg-navy-900 text-white text-xs font-semibold shadow-xs transition-colors"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Add Question</span>
              </button>
            </div>
          </div>

          {/* Two-Column Screening Layout matching Candidate Screening & Qualification.png */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
            {/* Left: Screening Questions & Deal-Breaker Rules */}
            <div className="lg:col-span-5 bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-6">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <h3 className="text-base font-bold text-navy-950 font-heading">
                  Screening Questions & Deal-Breaker Rules Configuration
                </h3>
              </div>

              {screeningQuestions.length === 0 ? (
                <div className="text-center py-8 space-y-2">
                  <p className="text-xs text-slate-400">No screening questions configured yet.</p>
                  <button
                    type="button"
                    onClick={() => setIsAddQuestionOpen(true)}
                    className="text-xs font-semibold text-blue-600 hover:underline"
                  >
                    Configure first screening question
                  </button>
                </div>
              ) : (
                <div className="divide-y divide-slate-100">
                  {screeningQuestions.map((q, idx) => (
                    <div key={q.id} className="py-4 first:pt-0 last:pb-0 space-y-2 group">
                      <div className="flex items-center justify-between text-xs text-slate-400">
                        <span className="font-medium">Question {idx + 1}:</span>
                        <button
                          type="button"
                          onClick={() => handleDeleteQuestion(q.id)}
                          className="opacity-0 group-hover:opacity-100 text-slate-400 hover:text-red-600 transition-opacity p-1"
                          title="Remove question"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>

                      <p className="text-sm font-semibold text-slate-900 leading-snug">
                        {q.question_text}
                      </p>

                      {q.is_deal_breaker && (
                        <div>
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-50 text-red-600 border border-red-200/80">
                            {q.deal_breaker_label || "Deal-Breaker Requirement"}
                          </span>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Right: Candidate Evaluation Table */}
            <div className="lg:col-span-7 bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-4">
                <h3 className="text-base font-bold text-navy-950 font-heading">
                  Candidate Evaluation Table
                </h3>

                <div className="flex items-center space-x-1.5 bg-slate-50 p-1 rounded-xl border border-slate-200/80 text-xs font-semibold">
                  <button
                    type="button"
                    onClick={() => setStatusFilter("ALL")}
                    className={`px-3 py-1 rounded-lg transition-all ${
                      statusFilter === "ALL"
                        ? "bg-white text-navy-950 shadow-2xs font-bold"
                        : "text-slate-500 hover:text-navy-950"
                    }`}
                  >
                    All ({(applicantsData.passed_count || 0) + (applicantsData.disqualified_count || 0) || applicantsData.total || 0})
                  </button>
                  <button
                    type="button"
                    onClick={() => setStatusFilter("PASSED")}
                    className={`px-3 py-1 rounded-lg transition-all ${
                      statusFilter === "PASSED"
                        ? "bg-emerald-600 text-white shadow-2xs font-bold"
                        : "text-slate-500 hover:text-emerald-700"
                    }`}
                  >
                    Passed ({applicantsData.passed_count})
                  </button>
                  <button
                    type="button"
                    onClick={() => setStatusFilter("DISQUALIFIED")}
                    className={`px-3 py-1 rounded-lg transition-all ${
                      statusFilter === "DISQUALIFIED"
                        ? "bg-rose-600 text-white shadow-2xs font-bold"
                        : "text-slate-500 hover:text-rose-700"
                    }`}
                  >
                    Disqualified ({applicantsData.disqualified_count})
                  </button>
                </div>
              </div>

              {applicantsData.items.length === 0 ? (
                <div className="text-center py-12 space-y-2">
                  <Users className="w-8 h-8 text-slate-300 mx-auto" />
                  <p className="text-sm font-semibold text-slate-700">No applicants for this vacancy yet</p>
                  <p className="text-xs text-slate-400">
                    Candidates who apply for this vacancy will be evaluated against deal-breaker rules and shown here.
                  </p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead>
                      <tr className="border-b border-slate-100 text-slate-800 font-semibold text-xs">
                        <th className="py-3 px-3">Candidate Name</th>
                        <th className="py-3 px-3">Match Score</th>
                        <th className="py-3 px-3">Deal-Breaker Status</th>
                        <th className="py-3 px-3">Key Answers Preview</th>
                        <th className="py-3 px-3 text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 font-medium">
                      {applicantsData.items.map((candidate) => (
                        <tr
                          key={candidate.id}
                          className="hover:bg-slate-50/75 transition-colors group cursor-pointer"
                          onClick={() => setSelectedCandidate(candidate)}
                        >
                          <td className="py-3 px-3">
                            <div className="flex items-center space-x-2.5">
                              <div className="w-8 h-8 rounded-full bg-slate-200 text-slate-700 font-bold text-xs flex items-center justify-center flex-shrink-0 shadow-2xs">
                                {candidate.candidate_name
                                  ? candidate.candidate_name.split(" ").map((n) => n[0]).slice(0, 2).join("").toUpperCase()
                                  : "CA"}
                              </div>
                              <div>
                                <div className="font-semibold text-slate-900 text-xs">
                                  {candidate.candidate_name}
                                </div>
                                <div className="text-[10px] text-slate-400">
                                  {candidate.candidate_email}
                                </div>
                              </div>
                            </div>
                          </td>

                          <td className="py-3 px-3">
                            <span
                              className={`inline-block px-2.5 py-0.5 rounded-full text-xs font-semibold ${getScoreBadgeClass(
                                candidate.match_score
                              )}`}
                            >
                              {Math.round(candidate.match_score)}%
                            </span>
                          </td>

                          <td className="py-3 px-3">
                            {candidate.deal_breaker_passed ? (
                              <div className="inline-flex items-center space-x-1.5 text-emerald-600 font-semibold text-xs">
                                <CheckCircle2 className="w-4 h-4 fill-emerald-600 text-white" />
                                <span>Passed</span>
                              </div>
                            ) : (
                              <div className="inline-flex items-center space-x-1.5 text-rose-600 font-semibold text-xs">
                                <XCircle className="w-4 h-4 fill-rose-600 text-white" />
                                <span>Disqualified</span>
                              </div>
                            )}
                          </td>

                          <td className="py-3 px-3">
                            <span
                              className="text-slate-600 truncate block max-w-[140px] hover:text-slate-900 hover:underline"
                              title={candidate.key_answers_preview || "View answers"}
                            >
                              {candidate.key_answers_preview || "Key Answers Previ..."}
                            </span>
                          </td>

                          <td
                            className="py-3 px-3 text-right space-x-1.5 whitespace-nowrap"
                            onClick={(e) => e.stopPropagation()}
                          >
                            <button
                              type="button"
                              onClick={() => handleStatusUpdate(candidate.id, "SHORTLISTED")}
                              disabled={actionLoading || candidate.status === "SHORTLISTED"}
                              className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${
                                candidate.status === "SHORTLISTED"
                                  ? "bg-slate-200 text-slate-500 cursor-default"
                                  : "bg-black text-white hover:bg-slate-800 shadow-2xs"
                              }`}
                            >
                              Shortlist
                            </button>
                            <button
                              type="button"
                              onClick={() => handleStatusUpdate(candidate.id, "DISQUALIFIED")}
                              disabled={actionLoading || candidate.status === "DISQUALIFIED"}
                              className={`px-3 py-1.5 rounded-md text-xs font-semibold border transition-all ${
                                candidate.status === "DISQUALIFIED"
                                  ? "border-slate-200 text-slate-400 bg-slate-50 cursor-default"
                                  : "border-slate-300 text-slate-800 hover:bg-slate-100"
                              }`}
                            >
                              Disqualify
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Candidate Response Review Modal */}
      {selectedCandidate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-navy-950/60 backdrop-blur-xs">
          <div className="bg-white rounded-2xl border border-slate-200 max-w-lg w-full p-6 space-y-5 shadow-2xl animate-fade-in">
            <div className="flex items-start justify-between border-b border-slate-100 pb-4">
              <div className="space-y-1">
                <div className="flex items-center space-x-2">
                  <h3 className="text-lg font-bold text-navy-950 font-heading">
                    {selectedCandidate.candidate_name}
                  </h3>
                  <span
                    className={`px-2 py-0.5 rounded-full text-xs font-bold ${getScoreBadgeClass(
                      selectedCandidate.match_score
                    )}`}
                  >
                    {Math.round(selectedCandidate.match_score)}% Match
                  </span>
                </div>
                <p className="text-xs text-slate-500">{selectedCandidate.candidate_email}</p>
              </div>
              <button
                onClick={() => setSelectedCandidate(null)}
                className="text-slate-400 hover:text-slate-700 p-1"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div
              className={`p-3 rounded-xl border text-xs flex items-center space-x-2.5 ${
                selectedCandidate.deal_breaker_passed
                  ? "bg-emerald-50 border-emerald-200 text-emerald-800"
                  : "bg-rose-50 border-rose-200 text-rose-800"
              }`}
            >
              {selectedCandidate.deal_breaker_passed ? (
                <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
              ) : (
                <XCircle className="w-4 h-4 text-rose-600 flex-shrink-0" />
              )}
              <span className="font-medium">
                {selectedCandidate.deal_breaker_passed
                  ? "Candidate passed all mandatory deal-breaker requirements."
                  : selectedCandidate.deal_breaker_failed_reason ||
                    "Candidate failed deal-breaker criteria and was automatically flagged."}
              </span>
            </div>

            <div className="space-y-3 max-h-72 overflow-y-auto pr-1">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                Submitted Screening Responses
              </h4>
              {screeningQuestions.map((q) => {
                const answer =
                  selectedCandidate.answers?.[String(q.id)] ||
                  selectedCandidate.answers?.[q.id] ||
                  "No response recorded";
                return (
                  <div key={q.id} className="p-3 rounded-xl bg-slate-50 border border-slate-100 space-y-1">
                    <div className="flex items-center justify-between text-[11px] text-slate-500 font-medium">
                      <span>{q.question_text}</span>
                      {q.is_deal_breaker && (
                        <span className="text-[10px] font-bold text-rose-600 uppercase">
                          Deal-Breaker
                        </span>
                      )}
                    </div>
                    <div className="text-xs font-semibold text-navy-950">{String(answer)}</div>
                  </div>
                );
              })}
            </div>

            <div className="pt-2 border-t border-slate-100 flex items-center justify-between">
              <div className="text-xs font-semibold text-slate-500">
                Status: <span className="font-bold text-slate-800">{selectedCandidate.status}</span>
              </div>
              <div className="flex items-center space-x-2">
                <button
                  type="button"
                  onClick={() => handleStatusUpdate(selectedCandidate.id, "SHORTLISTED")}
                  disabled={actionLoading}
                  className="px-3 py-1.5 rounded-lg bg-black text-white hover:bg-slate-800 text-xs font-semibold"
                >
                  Shortlist
                </button>
                <button
                  type="button"
                  onClick={() => handleStatusUpdate(selectedCandidate.id, "DISQUALIFIED")}
                  disabled={actionLoading}
                  className="px-3 py-1.5 rounded-lg border border-slate-300 text-slate-700 hover:bg-slate-100 text-xs font-semibold"
                >
                  Disqualify
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Add Screening Question Modal */}
      {isAddQuestionOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-navy-950/60 backdrop-blur-xs">
          <div className="bg-white rounded-2xl border border-slate-200 max-w-md w-full p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="text-base font-bold text-navy-950 font-heading">
                Configure Screening Question
              </h3>
              <button
                onClick={() => setIsAddQuestionOpen(false)}
                className="text-slate-400 hover:text-slate-700"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreateQuestion} className="space-y-4 text-xs">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Question Prompt</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Years of hands-on React/Node experience?"
                  value={newQuestion.question_text}
                  onChange={(e) => setNewQuestion({ ...newQuestion, question_text: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Answer Format</label>
                  <select
                    value={newQuestion.question_type}
                    onChange={(e) => setNewQuestion({ ...newQuestion, question_type: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs"
                  >
                    <option value="NUMERIC">Numeric Input</option>
                    <option value="YES_NO">Yes / No</option>
                    <option value="MULTIPLE_CHOICE">Multiple Choice</option>
                    <option value="TEXT">Short Text</option>
                  </select>
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Points Weight</label>
                  <input
                    type="number"
                    min="1"
                    max="100"
                    value={newQuestion.weight}
                    onChange={(e) => setNewQuestion({ ...newQuestion, weight: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs"
                  />
                </div>
              </div>

              {newQuestion.question_type === "MULTIPLE_CHOICE" && (
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Options (comma-separated)</label>
                  <input
                    type="text"
                    value={newQuestion.options}
                    onChange={(e) => setNewQuestion({ ...newQuestion, options: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs"
                  />
                </div>
              )}

              <div className="p-3 rounded-xl bg-slate-50 border border-slate-200/80 space-y-3">
                <label className="flex items-center space-x-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={newQuestion.is_deal_breaker}
                    onChange={(e) => setNewQuestion({ ...newQuestion, is_deal_breaker: e.target.checked })}
                    className="rounded border-slate-300 text-navy-950"
                  />
                  <span className="font-bold text-slate-800">
                    Deal-Breaker (Auto-Disqualification Rule)
                  </span>
                </label>

                {newQuestion.is_deal_breaker && (
                  <div className="space-y-2 pt-1 border-t border-slate-200/60">
                    <div className="grid grid-cols-2 gap-2">
                      <div>
                        <label className="block text-[11px] font-semibold text-slate-600 mb-0.5">Rule</label>
                        <select
                          value={newQuestion.deal_breaker_rule}
                          onChange={(e) => setNewQuestion({ ...newQuestion, deal_breaker_rule: e.target.value })}
                          className="w-full px-2 py-1.5 border border-slate-300 rounded-md text-xs"
                        >
                          <option value="GTE">Must be ≥ Value</option>
                          <option value="MANDATORY">Mandatory Answer</option>
                          <option value="EQUALS">Must Equal Exactly</option>
                        </select>
                      </div>
                      <div>
                        <label className="block text-[11px] font-semibold text-slate-600 mb-0.5">Threshold</label>
                        <input
                          type="text"
                          value={newQuestion.deal_breaker_value}
                          onChange={(e) => setNewQuestion({ ...newQuestion, deal_breaker_value: e.target.value })}
                          className="w-full px-2 py-1.5 border border-slate-300 rounded-md text-xs"
                        />
                      </div>
                    </div>
                    <div>
                      <label className="block text-[11px] font-semibold text-slate-600 mb-0.5">Badge Label</label>
                      <input
                        type="text"
                        placeholder="Deal-Breaker: Auto-Disqualify if < 2 Years"
                        value={newQuestion.deal_breaker_label}
                        onChange={(e) => setNewQuestion({ ...newQuestion, deal_breaker_label: e.target.value })}
                        className="w-full px-2 py-1.5 border border-slate-300 rounded-md text-xs"
                      />
                    </div>
                  </div>
                )}
              </div>

              <div className="pt-2 flex items-center justify-end space-x-2">
                <button
                  type="button"
                  onClick={() => setIsAddQuestionOpen(false)}
                  className="px-3 py-1.5 rounded-lg border border-slate-300 text-slate-700 hover:bg-slate-50 font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionLoading}
                  className="px-4 py-1.5 rounded-lg bg-navy-950 text-white hover:bg-navy-900 font-semibold shadow-xs"
                >
                  {actionLoading ? "Saving..." : "Save Question"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Test Simulation Modal */}
      {isTestScreeningOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-navy-950/60 backdrop-blur-xs">
          <div className="bg-white rounded-2xl border border-slate-200 max-w-lg w-full p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="text-base font-bold text-navy-950 font-heading">
                Simulate Candidate Application for {job.title}
              </h3>
              <button
                onClick={() => setIsTestScreeningOpen(false)}
                className="text-slate-400 hover:text-slate-700"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSimulateScreening} className="space-y-4 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Candidate Name</label>
                  <input
                    type="text"
                    required
                    value={testSubmission.candidate_name}
                    onChange={(e) => setTestSubmission({ ...testSubmission, candidate_name: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Candidate Email</label>
                  <input
                    type="email"
                    required
                    value={testSubmission.candidate_email}
                    onChange={(e) => setTestSubmission({ ...testSubmission, candidate_email: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs"
                  />
                </div>
              </div>

              <div className="space-y-3 pt-2 border-t border-slate-100">
                <h4 className="font-bold text-slate-800 text-xs">Screening Questions</h4>
                {screeningQuestions.map((q) => (
                  <div key={q.id} className="space-y-1">
                    <label className="block font-semibold text-slate-700">
                      {q.question_text}{" "}
                      {q.is_deal_breaker && (
                        <span className="text-[10px] text-rose-600 font-bold uppercase">
                          (Deal-Breaker)
                        </span>
                      )}
                    </label>
                    {q.question_type === "YES_NO" ? (
                      <select
                        value={testSubmission.answers[q.id] || ""}
                        onChange={(e) =>
                          setTestSubmission({
                            ...testSubmission,
                            answers: { ...testSubmission.answers, [q.id]: e.target.value },
                          })
                        }
                        className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs"
                      >
                        <option value="">Select option</option>
                        <option value="Yes">Yes</option>
                        <option value="No">No</option>
                      </select>
                    ) : q.question_type === "MULTIPLE_CHOICE" && Array.isArray(q.options) && q.options.length > 0 ? (
                      <select
                        value={testSubmission.answers[q.id] || ""}
                        onChange={(e) =>
                          setTestSubmission({
                            ...testSubmission,
                            answers: { ...testSubmission.answers, [q.id]: e.target.value },
                          })
                        }
                        className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs"
                      >
                        <option value="">Select option</option>
                        {q.options.map((opt) => (
                          <option key={opt} value={opt}>
                            {opt}
                          </option>
                        ))}
                      </select>
                    ) : (
                      <input
                        type="text"
                        placeholder={q.question_type === "NUMERIC" ? "e.g. 3 years" : "Enter response"}
                        value={testSubmission.answers[q.id] || ""}
                        onChange={(e) =>
                          setTestSubmission({
                            ...testSubmission,
                            answers: { ...testSubmission.answers, [q.id]: e.target.value },
                          })
                        }
                        className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs"
                      />
                    )}
                  </div>
                ))}
              </div>

              <div className="pt-2 flex items-center justify-end space-x-2">
                <button
                  type="button"
                  onClick={() => setIsTestScreeningOpen(false)}
                  className="px-3 py-1.5 rounded-lg border border-slate-300 text-slate-700 hover:bg-slate-50 font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionLoading}
                  className="inline-flex items-center space-x-1.5 px-4 py-1.5 rounded-lg bg-navy-950 text-white hover:bg-navy-900 font-semibold shadow-xs"
                >
                  <Send className="w-3.5 h-3.5" />
                  <span>{actionLoading ? "Evaluating..." : "Submit & Evaluate"}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Application Notice Modal (for non-company candidates) */}
      {applyModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-navy-950/60 backdrop-blur-xs">
          <div className="bg-white rounded-2xl border border-slate-200 max-w-md w-full p-6 space-y-4 shadow-xl text-center">
            <div className="w-12 h-12 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center mx-auto">
              <Briefcase className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-navy-950 font-heading">
              Apply to {job.title}
            </h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Direct resume submission with custom screening questions is part of Sprint 2 Ticket <strong>SKL-7: Job Application & Tracking</strong> (assigned to Saif).
            </p>
            <button
              type="button"
              onClick={() => setApplyModalOpen(false)}
              className="w-full py-2.5 rounded-xl bg-navy-950 text-white font-semibold text-xs"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default JobDetails;
