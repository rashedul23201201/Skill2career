import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../../hooks/useAuth";
import applicationService from "../../services/applicationService";
import { ROUTES } from "../../constants";
import {
  Briefcase,
  Building2,
  MapPin,
  Calendar,
  CheckCircle2,
  Clock,
  AlertCircle,
  XCircle,
  FileText,
  ArrowRight,
  ChevronRight,
  Search,
  SlidersHorizontal,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  RotateCcw,
  Sparkles,
} from "lucide-react";

const STATUS_CONFIG = {
  SUBMITTED: {
    label: "Submitted",
    badgeClass: "bg-blue-50 text-blue-700 border-blue-200",
    dotClass: "bg-blue-600",
    stepIndex: 1,
  },
  UNDER_REVIEW: {
    label: "Under Review",
    badgeClass: "bg-amber-50 text-amber-700 border-amber-200",
    dotClass: "bg-amber-500",
    stepIndex: 2,
  },
  SHORTLISTED: {
    label: "Shortlisted",
    badgeClass: "bg-emerald-50 text-emerald-700 border-emerald-200",
    dotClass: "bg-emerald-600",
    stepIndex: 3,
  },
  INTERVIEW_SCHEDULED: {
    label: "Interview Scheduled",
    badgeClass: "bg-purple-50 text-purple-700 border-purple-200",
    dotClass: "bg-purple-600",
    stepIndex: 3,
  },
  OFFERED: {
    label: "Offer Extended",
    badgeClass: "bg-green-50 text-green-700 border-green-200",
    dotClass: "bg-green-600",
    stepIndex: 4,
  },
  REJECTED: {
    label: "Not Selected",
    badgeClass: "bg-rose-50 text-rose-700 border-rose-200",
    dotClass: "bg-rose-600",
    stepIndex: 4,
  },
  WITHDRAWN: {
    label: "Withdrawn",
    badgeClass: "bg-slate-100 text-slate-600 border-slate-200",
    dotClass: "bg-slate-400",
    stepIndex: 0,
  },
};

const PIPELINE_STEPS = [
  { id: 1, title: "Applied", desc: "Submitted & Received" },
  { id: 2, title: "Review", desc: "Screening Evaluation" },
  { id: 3, title: "Shortlisted", desc: "Interview Pipeline" },
  { id: 4, title: "Decision", desc: "Final Offer or Result" },
];

export const LearnerApplications = () => {
  const { user } = useAuth();
  const [applications, setApplications] = useState([]);
  const [stats, setStats] = useState({
    total: 0,
    active_count: 0,
    submitted_count: 0,
    under_review_count: 0,
    shortlisted_count: 0,
    interview_count: 0,
    offered_count: 0,
    withdrawn_count: 0,
    rejected_count: 0,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [statusFilter, setStatusFilter] = useState("ALL");
  const [searchQuery, setSearchQuery] = useState("");
  const [expandedAppId, setExpandedAppId] = useState(null);

  const [withdrawModalApp, setWithdrawModalApp] = useState(null);
  const [withdrawLoading, setWithdrawLoading] = useState(false);
  const [notification, setNotification] = useState(null);

  const fetchApplications = async () => {
    try {
      setLoading(true);
      setError(null);
      const params = {};
      if (statusFilter !== "ALL") {
        params.status = statusFilter;
      }
      const res = await applicationService.getMyApplications(params);
      if (res?.data) {
        setApplications(res.data.items || []);
        setStats({
          total: res.data.total || 0,
          active_count: res.data.active_count || 0,
          submitted_count: res.data.submitted_count || 0,
          under_review_count: res.data.under_review_count || 0,
          shortlisted_count: res.data.shortlisted_count || 0,
          interview_count: res.data.interview_count || 0,
          offered_count: res.data.offered_count || 0,
          withdrawn_count: res.data.withdrawn_count || 0,
          rejected_count: res.data.rejected_count || 0,
        });
      }
    } catch (err) {
      console.error("Failed to load applications:", err);
      setError("Unable to load job applications. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchApplications();
  }, [statusFilter]);

  const handleWithdraw = async () => {
    if (!withdrawModalApp) return;
    try {
      setWithdrawLoading(true);
      await applicationService.withdrawApplication(withdrawModalApp.id);
      setNotification({
        type: "success",
        message: `Application for "${withdrawModalApp.job_title}" has been withdrawn.`,
      });
      setWithdrawModalApp(null);
      await fetchApplications();
    } catch (err) {
      console.error("Withdraw error:", err);
      setNotification({
        type: "error",
        message: err.response?.data?.message || "Failed to withdraw application.",
      });
    } finally {
      setWithdrawLoading(false);
    }
  };

  const filteredApps = applications.filter((app) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    const titleMatch = (app.job_title || "").toLowerCase().includes(q);
    const companyMatch = (app.company_name || "").toLowerCase().includes(q);
    const locationMatch = (app.location || "").toLowerCase().includes(q);
    return titleMatch || companyMatch || locationMatch;
  });

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <span className="text-xs font-extrabold uppercase tracking-wider text-blue-600">
              Career Management · SKL-7
            </span>
          </div>
          <h1 className="text-3xl font-extrabold text-navy-950 font-heading tracking-tight mt-1">
            Job Applications & Tracking
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Monitor real-time recruiter reviews, screening results, and hiring stage transitions.
          </p>
        </div>

        <Link
          to={ROUTES.JOBS || "/jobs"}
          className="inline-flex items-center space-x-2 px-4 py-2.5 rounded-xl bg-navy-950 hover:bg-navy-900 text-white font-semibold text-xs shadow-sm transition-all self-start md:self-auto"
        >
          <Briefcase className="w-4 h-4" />
          <span>Explore More Vacancies</span>
        </Link>
      </div>

      {/* Notification Banner */}
      {notification && (
        <div
          className={`p-4 rounded-xl border flex items-center justify-between transition-all ${
            notification.type === "success"
              ? "bg-emerald-50 border-emerald-200 text-emerald-800"
              : "bg-rose-50 border-rose-200 text-rose-800"
          }`}
        >
          <div className="flex items-center space-x-2 text-xs font-semibold">
            {notification.type === "success" ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
            ) : (
              <AlertCircle className="w-4 h-4 text-rose-600" />
            )}
            <span>{notification.message}</span>
          </div>
          <button
            type="button"
            onClick={() => setNotification(null)}
            className="text-xs font-bold hover:opacity-75"
          >
            ✕
          </button>
        </div>
      )}

      {/* Metrics Row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs">
          <span className="text-xs font-semibold text-slate-500">Active Applications</span>
          <div className="flex items-center justify-between mt-2">
            <h3 className="text-2xl font-extrabold text-navy-950 font-heading">
              {stats.active_count}
            </h3>
            <div className="w-9 h-9 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center">
              <Briefcase className="w-4 h-4" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs">
          <span className="text-xs font-semibold text-slate-500">Under Review</span>
          <div className="flex items-center justify-between mt-2">
            <h3 className="text-2xl font-extrabold text-navy-950 font-heading">
              {stats.under_review_count}
            </h3>
            <div className="w-9 h-9 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center">
              <Clock className="w-4 h-4" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs">
          <span className="text-xs font-semibold text-slate-500">Shortlisted</span>
          <div className="flex items-center justify-between mt-2">
            <h3 className="text-2xl font-extrabold text-navy-950 font-heading">
              {stats.shortlisted_count + stats.interview_count}
            </h3>
            <div className="w-9 h-9 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center">
              <CheckCircle2 className="w-4 h-4" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs">
          <span className="text-xs font-semibold text-slate-500">Offers Extended</span>
          <div className="flex items-center justify-between mt-2">
            <h3 className="text-2xl font-extrabold text-navy-950 font-heading">
              {stats.offered_count}
            </h3>
            <div className="w-9 h-9 rounded-xl bg-green-50 text-green-600 flex items-center justify-center">
              <Sparkles className="w-4 h-4" />
            </div>
          </div>
        </div>
      </div>

      {/* Filter Tabs & Search */}
      <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        {/* Status Filter Tabs */}
        <div className="flex items-center space-x-1.5 overflow-x-auto pb-2 md:pb-0 text-xs">
          {[
            { id: "ALL", label: "All Applications" },
            { id: "SUBMITTED", label: "Submitted" },
            { id: "UNDER_REVIEW", label: "In Review" },
            { id: "SHORTLISTED", label: "Shortlisted" },
            { id: "OFFERED", label: "Offered" },
            { id: "WITHDRAWN", label: "Withdrawn" },
            { id: "REJECTED", label: "Rejected" },
          ].map((tab) => (
            <button
              key={tab.id}
              type="button"
              onClick={() => setStatusFilter(tab.id)}
              className={`px-3 py-1.5 rounded-lg font-semibold transition-all whitespace-nowrap ${
                statusFilter === tab.id
                  ? "bg-navy-950 text-white shadow-xs"
                  : "bg-slate-100 text-slate-600 hover:bg-slate-200"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Search */}
        <div className="relative w-full md:w-64">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search role or company..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 rounded-lg border border-slate-200 text-xs focus:outline-hidden focus:border-blue-500"
          />
        </div>
      </div>

      {/* Applications List */}
      {loading ? (
        <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center text-slate-500 text-xs">
          Loading your application pipeline...
        </div>
      ) : error ? (
        <div className="bg-white rounded-2xl border border-rose-200 p-8 text-center space-y-3">
          <AlertCircle className="w-8 h-8 text-rose-500 mx-auto" />
          <p className="text-xs text-rose-700 font-semibold">{error}</p>
          <button
            type="button"
            onClick={fetchApplications}
            className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-lg"
          >
            Retry
          </button>
        </div>
      ) : filteredApps.length === 0 ? (
        <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center space-y-4">
          <div className="w-12 h-12 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center mx-auto">
            <Briefcase className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-base font-bold text-navy-950 font-heading">
              No applications found
            </h3>
            <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
              {statusFilter !== "ALL"
                ? `You have no applications with status "${statusFilter}". Try choosing "All Applications".`
                : "You haven't submitted any job applications yet. Discover verified vacancies and apply with 1 click."}
            </p>
          </div>
          <Link
            to={ROUTES.JOBS || "/jobs"}
            className="inline-flex items-center space-x-1.5 px-4 py-2 rounded-xl bg-navy-950 text-white font-semibold text-xs shadow-xs hover:bg-navy-900 transition-colors"
          >
            <span>Browse Job Vacancies</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredApps.map((app) => {
            const config = STATUS_CONFIG[app.status] || STATUS_CONFIG.SUBMITTED;
            const isExpanded = expandedAppId === app.id;
            const appliedDate = app.applied_at
              ? new Date(app.applied_at).toLocaleDateString(undefined, {
                  year: "numeric",
                  month: "short",
                  day: "numeric",
                })
              : "Recently";

            return (
              <div
                key={app.id}
                className="bg-white rounded-2xl border border-slate-200 p-5 sm:p-6 shadow-xs hover:border-slate-300 transition-all space-y-6"
              >
                {/* Top Role / Company Row */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div className="flex items-start space-x-3.5">
                    {/* Company Avatar / Logo */}
                    <div className="w-12 h-12 rounded-xl bg-slate-100 border border-slate-200 flex items-center justify-center text-slate-700 font-bold text-sm flex-shrink-0 overflow-hidden">
                      {app.company_logo_url ? (
                        <img
                          src={app.company_logo_url}
                          alt={app.company_name}
                          className="w-full h-full object-cover"
                        />
                      ) : (
                        <Building2 className="w-6 h-6 text-slate-400" />
                      )}
                    </div>

                    <div>
                      <div className="flex flex-wrap items-center gap-2">
                        <h3 className="text-base font-bold text-navy-950 font-heading">
                          {app.job_title}
                        </h3>
                        <span className="px-2 py-0.5 text-[10px] font-bold rounded-md bg-slate-100 text-slate-700">
                          {app.posting_type || "Job"}
                        </span>
                      </div>

                      <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-slate-500 mt-1">
                        <span className="font-semibold text-navy-900">
                          {app.company_name}
                        </span>
                        {app.location && (
                          <span className="flex items-center space-x-1">
                            <MapPin className="w-3 h-3 text-slate-400" />
                            <span>{app.location}</span>
                          </span>
                        )}
                        {app.compensation && (
                          <span>· {app.compensation}</span>
                        )}
                        <span>· Applied on {appliedDate}</span>
                      </div>
                    </div>
                  </div>

                  {/* Status Badge & Actions */}
                  <div className="flex items-center space-x-2.5 self-start sm:self-auto">
                    <span
                      className={`inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-bold border ${config.badgeClass}`}
                    >
                      <span className={`w-1.5 h-1.5 rounded-full ${config.dotClass}`} />
                      <span>{config.label}</span>
                    </span>

                    <Link
                      to={`/jobs/${app.job_id}`}
                      className="p-2 rounded-lg border border-slate-200 hover:bg-slate-50 text-slate-600 text-xs font-semibold"
                      title="View job listing"
                    >
                      <ExternalLink className="w-3.5 h-3.5" />
                    </Link>
                  </div>
                </div>

                {/* 4-Step Recruitment Pipeline Stepper */}
                {app.status !== "WITHDRAWN" && (
                  <div className="p-4 rounded-xl bg-slate-50/80 border border-slate-100">
                    <div className="grid grid-cols-4 gap-2">
                      {PIPELINE_STEPS.map((step) => {
                        const isDone = config.stepIndex > step.id;
                        const isCurrent = config.stepIndex === step.id;
                        const isPending = config.stepIndex < step.id;

                        return (
                          <div key={step.id} className="flex flex-col items-center text-center space-y-1.5">
                            <div
                              className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold transition-all ${
                                isDone
                                  ? "bg-emerald-600 text-white"
                                  : isCurrent
                                  ? "bg-blue-600 text-white ring-4 ring-blue-100"
                                  : "bg-slate-200 text-slate-500"
                              }`}
                            >
                              {isDone ? "✓" : step.id}
                            </div>
                            <div className="text-[11px] font-bold text-navy-950">
                              {step.title}
                            </div>
                            <div className="text-[10px] text-slate-400 hidden sm:block">
                              {step.desc}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* Bottom Details Bar & Expansion Toggle */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-2 border-t border-slate-100 text-xs">
                  <div className="flex flex-wrap items-center gap-3 text-slate-600">
                    {/* Screening Score */}
                    {app.screening_score !== undefined && (
                      <span className="inline-flex items-center space-x-1.5 font-medium">
                        <span className="text-slate-400">Match Score:</span>
                        <span
                          className={`font-bold ${
                            app.deal_breaker_passed
                              ? "text-emerald-700"
                              : "text-rose-600"
                          }`}
                        >
                          {app.screening_score}%
                        </span>
                        {!app.deal_breaker_passed && (
                          <span className="text-[10px] text-rose-500 font-bold">
                            (Deal-Breaker Alert)
                          </span>
                        )}
                      </span>
                    )}

                    {/* Resume Attached */}
                    {app.resume_filename && (
                      <span className="inline-flex items-center space-x-1 text-slate-500 font-medium">
                        <FileText className="w-3.5 h-3.5 text-slate-400" />
                        <span className="truncate max-w-[180px]">{app.resume_filename}</span>
                      </span>
                    )}
                  </div>

                  <div className="flex items-center space-x-2 self-end sm:self-auto">
                    {/* Withdraw Action (if active) */}
                    {app.status !== "WITHDRAWN" && app.status !== "REJECTED" && (
                      <button
                        type="button"
                        onClick={() => setWithdrawModalApp(app)}
                        className="px-3 py-1 text-xs font-semibold text-rose-600 hover:text-rose-800 hover:bg-rose-50 rounded-lg transition-colors"
                      >
                        Withdraw
                      </button>
                    )}

                    {/* Toggle details */}
                    <button
                      type="button"
                      onClick={() =>
                        setExpandedAppId(isExpanded ? null : app.id)
                      }
                      className="inline-flex items-center space-x-1 px-3 py-1 rounded-lg border border-slate-200 hover:bg-slate-50 font-semibold text-slate-700"
                    >
                      <span>{isExpanded ? "Hide Details" : "Application Details"}</span>
                      {isExpanded ? (
                        <ChevronUp className="w-3.5 h-3.5" />
                      ) : (
                        <ChevronDown className="w-3.5 h-3.5" />
                      )}
                    </button>
                  </div>
                </div>

                {/* Expanded Details Panel */}
                {isExpanded && (
                  <div className="pt-4 border-t border-slate-100 space-y-4 text-xs bg-slate-50/50 p-4 rounded-xl">
                    {/* Cover Letter */}
                    {app.cover_letter && (
                      <div className="space-y-1">
                        <h4 className="font-bold text-navy-950">Cover Note</h4>
                        <p className="text-slate-600 leading-relaxed whitespace-pre-line bg-white p-3 rounded-lg border border-slate-200">
                          {app.cover_letter}
                        </p>
                      </div>
                    )}

                    {/* Screening Responses */}
                    {app.screening_answers && Object.keys(app.screening_answers).length > 0 && (
                      <div className="space-y-2">
                        <h4 className="font-bold text-navy-950">Submitted Screening Answers</h4>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                          {Object.entries(app.screening_answers).map(([key, val]) => (
                            <div key={key} className="bg-white p-2.5 rounded-lg border border-slate-200">
                              <span className="text-[10px] text-slate-400 font-bold uppercase block">
                                Question #{key}
                              </span>
                              <span className="font-semibold text-navy-900 mt-0.5 block">
                                {String(val)}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Recruiter Review Notes */}
                    {app.review_notes && (
                      <div className="space-y-1 bg-blue-50/60 border border-blue-100 p-3 rounded-lg">
                        <h4 className="font-bold text-blue-950">Recruiter Feedback / Notes</h4>
                        <p className="text-blue-900">{app.review_notes}</p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Withdraw Confirmation Modal (AC-5) */}
      {withdrawModalApp && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-navy-950/60 backdrop-blur-xs">
          <div className="bg-white rounded-2xl border border-slate-200 max-w-md w-full p-6 space-y-4 shadow-xl">
            <div className="w-12 h-12 rounded-xl bg-rose-50 text-rose-600 flex items-center justify-center mx-auto">
              <RotateCcw className="w-6 h-6" />
            </div>
            <div className="text-center space-y-1">
              <h3 className="text-lg font-bold text-navy-950 font-heading">
                Withdraw Application?
              </h3>
              <p className="text-xs text-slate-500 leading-relaxed">
                Are you sure you want to withdraw your application for{" "}
                <strong className="text-navy-900">{withdrawModalApp.job_title}</strong> at{" "}
                <strong className="text-navy-900">{withdrawModalApp.company_name}</strong>?
                This will remove your submission from the recruiter's active pipeline.
              </p>
            </div>

            <div className="flex items-center space-x-3 pt-2">
              <button
                type="button"
                disabled={withdrawLoading}
                onClick={() => setWithdrawModalApp(null)}
                className="w-1/2 py-2.5 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 font-semibold text-xs"
              >
                Keep Application
              </button>
              <button
                type="button"
                disabled={withdrawLoading}
                onClick={handleWithdraw}
                className="w-1/2 py-2.5 rounded-xl bg-rose-600 hover:bg-rose-700 text-white font-semibold text-xs shadow-sm transition-all"
              >
                {withdrawLoading ? "Withdrawing..." : "Confirm Withdrawal"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default LearnerApplications;
