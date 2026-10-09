import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../../hooks/useAuth";
import applicationService from "../../services/applicationService";
import interviewService from "../../services/interviewService";
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
  ExternalLink,
  RotateCcw,
  Video,
  Target,
  Flag,
  CalendarCheck,
  Check,
  Send,
  CalendarDays,
  X,
  Sparkles,
} from "lucide-react";

export const LearnerApplications = () => {
  const { user } = useAuth();
  const [applications, setApplications] = useState([]);
  const [totalApplications, setTotalApplications] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [selectedAppId, setSelectedAppId] = useState(null);
  const [activeInterview, setActiveInterview] = useState(null);
  const [interviewLoading, setInterviewLoading] = useState(false);

  const [page, setPage] = useState(1);
  const pageSize = 5;

  const [isInterviewModalOpen, setIsInterviewModalOpen] = useState(false);
  const [isFeedbackModalOpen, setIsFeedbackModalOpen] = useState(false);
  const [isWithdrawModalOpen, setIsWithdrawModalOpen] = useState(false);

  const [selectedSlotId, setSelectedSlotId] = useState(null);
  const [submittingSlot, setSubmittingSlot] = useState(false);

  const [showRescheduleForm, setShowRescheduleForm] = useState(false);
  const [rescheduleReason, setRescheduleReason] = useState("");
  const [preferredTime, setPreferredTime] = useState("");
  const [submittingReschedule, setSubmittingReschedule] = useState(false);

  const [notification, setNotification] = useState(null);
  const [withdrawLoading, setWithdrawLoading] = useState(false);

  const fetchApplications = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await applicationService.getMyApplications({ page: 1, size: 50 });
      if (res?.data) {
        const items = res.data.items || [];
        setApplications(items);
        setTotalApplications(res.data.total || items.length);

        if (items.length > 0) {
          if (!selectedAppId || !items.some((a) => a.id === selectedAppId)) {
            setSelectedAppId(items[0].id);
          }
        }
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
  }, []);

  const selectedApp = applications.find((a) => a.id === selectedAppId) || applications[0] || null;

  useEffect(() => {
    if (!selectedApp) {
      setActiveInterview(null);
      return;
    }

    const fetchInterview = async () => {
      try {
        setInterviewLoading(true);
        const res = await interviewService.getInterviewForApplication(selectedApp.id);
        if (res?.data) {
          setActiveInterview(res.data);
          if (res.data.selected_slot_id) {
            setSelectedSlotId(res.data.selected_slot_id);
          } else if (res.data.slots && res.data.slots.length > 0) {
            setSelectedSlotId(res.data.slots[0].id);
          }
        } else {
          setActiveInterview(null);
        }
      } catch (err) {
        console.warn("No interview session found for application:", err);
        setActiveInterview(null);
      } finally {
        setInterviewLoading(false);
      }
    };

    fetchInterview();
    setShowRescheduleForm(false);
  }, [selectedAppId]);

  const handleSelectSlot = async () => {
    if (!activeInterview || !selectedSlotId) return;
    try {
      setSubmittingSlot(true);
      const res = await interviewService.selectSlot(activeInterview.id, selectedSlotId);
      if (res?.data) {
        setActiveInterview(res.data);
        setNotification({
          type: "success",
          message: "Interview time slot confirmed! Calendar invitation has been generated.",
        });
        await fetchApplications();
      }
    } catch (err) {
      console.error("Failed to confirm slot:", err);
      setNotification({
        type: "error",
        message: err.response?.data?.message || "Failed to confirm time slot.",
      });
    } finally {
      setSubmittingSlot(false);
    }
  };

  const handleRescheduleSubmit = async (e) => {
    e.preventDefault();
    if (!activeInterview || !rescheduleReason.trim()) return;
    try {
      setSubmittingReschedule(true);
      const res = await interviewService.rescheduleInterview(activeInterview.id, {
        reason: rescheduleReason.trim(),
        preferred_time: preferredTime.trim() || undefined,
      });
      if (res?.data) {
        setActiveInterview(res.data);
        setShowRescheduleForm(false);
        setRescheduleReason("");
        setPreferredTime("");
        setNotification({
          type: "success",
          message: "Reschedule request submitted to recruiter.",
        });
      }
    } catch (err) {
      console.error("Failed to request reschedule:", err);
      setNotification({
        type: "error",
        message: err.response?.data?.message || "Failed to request reschedule.",
      });
    } finally {
      setSubmittingReschedule(false);
    }
  };

  const handleDownloadIcs = async () => {
    if (!activeInterview) return;
    try {
      await interviewService.downloadIcsCalendar(activeInterview.id);
    } catch (err) {
      console.error("Failed to download ICS:", err);
      setNotification({
        type: "error",
        message: "Unable to download calendar invitation file.",
      });
    }
  };

  const handleWithdraw = async () => {
    if (!selectedApp) return;
    try {
      setWithdrawLoading(true);
      await applicationService.withdrawApplication(selectedApp.id);
      setIsWithdrawModalOpen(false);
      setNotification({
        type: "success",
        message: `Application for "${selectedApp.job_title}" has been withdrawn.`,
      });
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

  const totalPages = Math.ceil(applications.length / pageSize) || 1;
  const paginatedApplications = applications.slice((page - 1) * pageSize, page * pageSize);

  const getStatusBadge = (status) => {
    switch (status) {
      case "SHORTLISTED":
        return (
          <span className="inline-flex items-center space-x-1.5 px-3 py-0.5 rounded-full text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-600"></span>
            <span>Shortlisted</span>
          </span>
        );
      case "INTERVIEW_SCHEDULED":
      case "INTERVIEW":
        return (
          <span className="inline-flex items-center space-x-1.5 px-3 py-0.5 rounded-full text-xs font-medium bg-blue-50 text-blue-700 border border-blue-200">
            <span className="w-1.5 h-1.5 rounded-full bg-blue-600"></span>
            <span>Interview</span>
          </span>
        );
      case "SUBMITTED":
      case "APPLIED":
        return (
          <span className="inline-flex items-center space-x-1.5 px-3 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-700 border border-slate-200">
            <span className="w-1.5 h-1.5 rounded-full bg-slate-500"></span>
            <span>Applied</span>
          </span>
        );
      case "UNDER_REVIEW":
        return (
          <span className="inline-flex items-center space-x-1.5 px-3 py-0.5 rounded-full text-xs font-medium bg-amber-50 text-amber-700 border border-amber-200">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-500"></span>
            <span>In Review</span>
          </span>
        );
      case "OFFERED":
        return (
          <span className="inline-flex items-center space-x-1.5 px-3 py-0.5 rounded-full text-xs font-medium bg-green-50 text-green-700 border border-green-200">
            <span className="w-1.5 h-1.5 rounded-full bg-green-600"></span>
            <span>Offered</span>
          </span>
        );
      case "REJECTED":
        return (
          <span className="inline-flex items-center space-x-1.5 px-3 py-0.5 rounded-full text-xs font-medium bg-rose-50 text-rose-700 border border-rose-200">
            <span className="w-1.5 h-1.5 rounded-full bg-rose-600"></span>
            <span>Rejected</span>
          </span>
        );
      case "WITHDRAWN":
        return (
          <span className="inline-flex items-center space-x-1.5 px-3 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-500 border border-slate-200">
            <span className="w-1.5 h-1.5 rounded-full bg-slate-400"></span>
            <span>Withdrawn</span>
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center space-x-1.5 px-3 py-0.5 rounded-full text-xs font-medium bg-blue-50 text-blue-700 border border-blue-200">
            <span className="w-1.5 h-1.5 rounded-full bg-blue-600"></span>
            <span>{status}</span>
          </span>
        );
    }
  };

  const getStepState = () => {
    if (!selectedApp) return { stepNumber: 1, stepText: "Step 1 of 4" };
    switch (selectedApp.status) {
      case "SUBMITTED":
        return { stepNumber: 1, stepText: "Step 1 of 4" };
      case "UNDER_REVIEW":
      case "SHORTLISTED":
        return { stepNumber: 2, stepText: "Step 2 of 4" };
      case "INTERVIEW_SCHEDULED":
        return { stepNumber: 3, stepText: "Step 3 of 4" };
      case "OFFERED":
      case "REJECTED":
        return { stepNumber: 4, stepText: "Step 4 of 4" };
      default:
        return { stepNumber: 2, stepText: "Step 2 of 4" };
    }
  };

  const stepState = getStepState();

  const formattedAppliedDate = selectedApp?.applied_at
    ? new Date(selectedApp.applied_at).toLocaleDateString("en-US", {
        month: "long",
        day: "numeric",
        year: "numeric",
      })
    : "September 18, 2026";

  const interviewDateStr = activeInterview?.scheduled_at
    ? new Date(activeInterview.scheduled_at).toLocaleDateString("en-US", {
        month: "long",
        day: "numeric",
        year: "numeric",
      })
    : "September 25, 2026";

  const interviewTimeStr = activeInterview?.scheduled_at
    ? new Date(activeInterview.scheduled_at).toLocaleTimeString("en-US", {
        hour: "numeric",
        minute: "2-digit",
        hour12: true,
      }) + " (BST)"
    : "3:00 PM (BST)";

  return (
    <div className="min-h-screen bg-slate-50/50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header Breadcrumb & Title */}
        <div className="space-y-1">
          <div className="text-[11px] font-bold uppercase tracking-wider text-blue-700">
            CANDIDATE DASHBOARD / INTERVIEW & RECRUITMENT TRACKER
          </div>
          <h1 className="text-3xl font-extrabold text-navy-950 font-heading tracking-tight">
            Interview & Recruitment
          </h1>
          <p className="text-sm text-slate-500">
            Track, inspect, and prepare for every stage of your active recruitment pipelines.
          </p>
        </div>

        {/* Notification Toast */}
        {notification && (
          <div
            className={`p-4 rounded-xl border flex items-center justify-between text-xs font-semibold ${
              notification.type === "success"
                ? "bg-emerald-50 border-emerald-200 text-emerald-800"
                : "bg-rose-50 border-rose-200 text-rose-800"
            }`}
          >
            <div className="flex items-center space-x-2">
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
              className="font-bold hover:opacity-75"
            >
              ✕
            </button>
          </div>
        )}

        {/* Top Table: My Applications */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
          <div className="p-5 sm:p-6 border-b border-slate-100 flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center">
                <CheckCircle2 className="w-4 h-4" />
              </div>
              <div>
                <h2 className="text-base font-bold text-navy-950 font-heading">
                  My Applications
                </h2>
                <p className="text-xs text-slate-500">
                  Real-time status updates across hiring partners
                </p>
              </div>
            </div>

            <span className="px-3 py-1 rounded-full text-xs font-bold bg-blue-50 text-blue-700">
              {totalApplications} Total Applications
            </span>
          </div>

          {loading ? (
            <div className="p-12 text-center text-xs text-slate-500">
              Loading applications...
            </div>
          ) : error ? (
            <div className="p-8 text-center text-xs text-rose-600">
              {error}
            </div>
          ) : applications.length === 0 ? (
            <div className="p-12 text-center space-y-3">
              <p className="text-xs text-slate-500">
                You haven't submitted any job applications yet.
              </p>
              <Link
                to={ROUTES.JOBS || "/jobs"}
                className="inline-flex items-center space-x-1.5 px-4 py-2 rounded-xl bg-navy-950 text-white font-semibold text-xs"
              >
                <span>Browse Vacancies</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-100 text-[11px] font-bold text-slate-400 uppercase tracking-wider bg-slate-50/50">
                    <th className="py-3 px-6">Position</th>
                    <th className="py-3 px-6">Company</th>
                    <th className="py-3 px-6">Applied Date</th>
                    <th className="py-3 px-6">Status</th>
                    <th className="py-3 px-6 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {paginatedApplications.map((app) => {
                    const isSelected = selectedApp?.id === app.id;
                    const dateFormatted = app.applied_at
                      ? new Date(app.applied_at).toLocaleDateString("en-US", {
                          month: "short",
                          day: "numeric",
                          year: "numeric",
                        })
                      : "Sep 18, 2026";

                    return (
                      <tr
                        key={app.id}
                        onClick={() => setSelectedAppId(app.id)}
                        className={`cursor-pointer transition-colors ${
                          isSelected
                            ? "bg-blue-50/30"
                            : "hover:bg-slate-50/80"
                        }`}
                      >
                        <td className="py-4 px-6 font-semibold text-navy-950">
                          <div className="flex items-center space-x-2">
                            {isSelected && (
                              <span className="w-1 h-5 rounded-full bg-blue-600 -ml-4 mr-2" />
                            )}
                            <span>{app.job_title}</span>
                          </div>
                        </td>
                        <td className="py-4 px-6 text-slate-600 font-medium">
                          {app.company_name}
                        </td>
                        <td className="py-4 px-6 text-slate-500 font-medium">
                          {dateFormatted}
                        </td>
                        <td className="py-4 px-6">
                          {getStatusBadge(app.status)}
                        </td>
                        <td className="py-4 px-6 text-right">
                          {isSelected ? (
                            <button
                              type="button"
                              onClick={(e) => {
                                e.stopPropagation();
                                setSelectedAppId(app.id);
                              }}
                              className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-navy-950 text-white font-semibold text-xs shadow-xs"
                            >
                              <span>View Details</span>
                              <ArrowRight className="w-3.5 h-3.5" />
                            </button>
                          ) : (
                            <button
                              type="button"
                              onClick={(e) => {
                                e.stopPropagation();
                                setSelectedAppId(app.id);
                              }}
                              className="inline-flex items-center px-3 py-1.5 rounded-lg border border-slate-200 text-slate-700 hover:bg-slate-50 font-semibold text-xs"
                            >
                              View Details
                            </button>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>

              {/* Pagination Row */}
              <div className="p-4 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
                <span>
                  Showing {Math.min((page - 1) * pageSize + 1, applications.length)}-
                  {Math.min(page * pageSize, applications.length)} of {applications.length} applications
                </span>

                <div className="flex items-center space-x-1">
                  <button
                    type="button"
                    disabled={page <= 1}
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    className="px-2.5 py-1 rounded-md border border-slate-200 text-slate-600 disabled:opacity-40 disabled:cursor-not-allowed text-xs hover:bg-slate-50"
                  >
                    Previous
                  </button>
                  {Array.from({ length: totalPages }, (_, i) => i + 1).map((p) => (
                    <button
                      key={p}
                      type="button"
                      onClick={() => setPage(p)}
                      className={`w-7 h-7 rounded-md text-xs font-semibold ${
                        page === p
                          ? "bg-navy-950 text-white"
                          : "border border-slate-200 text-slate-600 hover:bg-slate-50"
                      }`}
                    >
                      {p}
                    </button>
                  ))}
                  <button
                    type="button"
                    disabled={page >= totalPages}
                    onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                    className="px-2.5 py-1 rounded-md border border-slate-200 text-slate-600 disabled:opacity-40 disabled:cursor-not-allowed text-xs hover:bg-slate-50"
                  >
                    Next
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Selected Application Details */}
        {selectedApp && (
          <div className="bg-white rounded-2xl border border-slate-200 p-6 sm:p-7 shadow-xs space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <h3 className="text-xl font-extrabold text-navy-950 font-heading">
                  Selected Application Details — {selectedApp.job_title}
                </h3>
                <p className="text-xs font-medium text-slate-500 mt-0.5">
                  {selectedApp.job_title} ·{" "}
                  <span className="text-blue-700 font-semibold">
                    {selectedApp.company_name}
                  </span>
                </p>
              </div>

              <div className="flex items-center space-x-2">
                <Link
                  to={`/jobs/${selectedApp.job_id}`}
                  className="inline-flex items-center space-x-1.5 px-4 py-2 rounded-xl bg-navy-950 hover:bg-navy-900 text-white font-semibold text-xs shadow-xs transition-colors"
                >
                  <span>View Job Details</span>
                  <ExternalLink className="w-3.5 h-3.5" />
                </Link>

                {selectedApp.status !== "WITHDRAWN" && selectedApp.status !== "REJECTED" && (
                  <button
                    type="button"
                    onClick={() => setIsWithdrawModalOpen(true)}
                    className="p-2 rounded-xl border border-slate-200 hover:bg-rose-50 hover:border-rose-200 text-slate-500 hover:text-rose-600 transition-colors"
                    title="Withdraw Application"
                  >
                    <RotateCcw className="w-4 h-4" />
                  </button>
                )}
              </div>
            </div>

            {/* 5 Meta Cards Row */}
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 p-4 rounded-xl bg-slate-50/70 border border-slate-100 text-xs">
              <div>
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">
                  Job Type
                </span>
                <span className="font-bold text-navy-950 mt-1 block">
                  {selectedApp.posting_type || "Full-time"}
                </span>
              </div>

              <div>
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">
                  Location
                </span>
                <span className="font-bold text-navy-950 mt-1 block">
                  {selectedApp.location || "Dhaka"}
                </span>
              </div>

              <div>
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">
                  Applied Date
                </span>
                <span className="font-bold text-navy-950 mt-1 block">
                  {formattedAppliedDate}
                </span>
              </div>

              <div>
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">
                  CV Submitted
                </span>
                <div className="flex items-center space-x-1 text-blue-700 font-semibold mt-1 truncate">
                  <FileText className="w-3.5 h-3.5 flex-shrink-0" />
                  <span className="truncate">
                    {selectedApp.resume_filename || "AB_CV.pdf"}
                  </span>
                </div>
              </div>

              <div>
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">
                  Current Status
                </span>
                <div className="mt-1">
                  {getStatusBadge(selectedApp.status)}
                </div>
              </div>
            </div>

            {/* Recruitment Progress Stepper */}
            <div className="space-y-3 pt-2">
              <div className="flex items-center justify-between text-xs">
                <span className="font-bold uppercase tracking-wider text-slate-600">
                  Recruitment Progress
                </span>
                <span className="font-semibold text-slate-500">
                  {stepState.stepText}
                </span>
              </div>

              <div className="grid grid-cols-4 gap-2 pt-2">
                {/* Step 1: Applied */}
                <div className="flex flex-col items-center text-center space-y-1.5">
                  <div
                    className={`w-9 h-9 rounded-full flex items-center justify-center text-xs font-bold ${
                      stepState.stepNumber >= 1
                        ? "bg-emerald-600 text-white"
                        : "bg-slate-200 text-slate-500"
                    }`}
                  >
                    <Check className="w-4 h-4" />
                  </div>
                  <span className="text-xs font-bold text-navy-950">Applied</span>
                  <span className="text-[10px] text-slate-400">
                    {formattedAppliedDate}
                  </span>
                </div>

                {/* Step 2: Shortlisted */}
                <div className="flex flex-col items-center text-center space-y-1.5">
                  <div
                    className={`w-9 h-9 rounded-full flex items-center justify-center text-xs font-bold ${
                      stepState.stepNumber >= 2
                        ? "bg-emerald-600 text-white"
                        : "bg-slate-200 text-slate-500"
                    }`}
                  >
                    <Target className="w-4 h-4" />
                  </div>
                  <span className="text-xs font-bold text-navy-950">Shortlisted</span>
                  <span className="text-[10px] text-slate-400">In Review</span>
                </div>

                {/* Step 3: Interview */}
                <div className="flex flex-col items-center text-center space-y-1.5">
                  <div
                    className={`w-9 h-9 rounded-full flex items-center justify-center text-xs font-bold ${
                      stepState.stepNumber >= 3
                        ? "bg-blue-600 text-white ring-4 ring-blue-100"
                        : "bg-slate-200 text-slate-500"
                    }`}
                  >
                    <Calendar className="w-4 h-4" />
                  </div>
                  <span className="text-xs font-bold text-navy-950">Interview</span>
                  <span className="text-[10px] text-slate-400">
                    {activeInterview?.scheduled_at ? interviewDateStr : "Pending Schedule"}
                  </span>
                </div>

                {/* Step 4: Final Decision */}
                <div className="flex flex-col items-center text-center space-y-1.5">
                  <div
                    className={`w-9 h-9 rounded-full flex items-center justify-center text-xs font-bold ${
                      stepState.stepNumber >= 4
                        ? "bg-emerald-600 text-white"
                        : "bg-slate-200 text-slate-500"
                    }`}
                  >
                    <Flag className="w-4 h-4" />
                  </div>
                  <span className="text-xs font-bold text-navy-950">Final Decision</span>
                  <span className="text-[10px] text-slate-400">
                    {selectedApp.status === "OFFERED"
                      ? "Offer Extended"
                      : selectedApp.status === "REJECTED"
                      ? "Decision Complete"
                      : "Pending Outcome"}
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Bottom Split Cards: SKL-9 (Interview Details) & SKL-10 (Interview Feedback) */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Left Card: Upcoming Session / Interview Details (SKL-9) */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs flex flex-col justify-between space-y-6">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-1.5 text-xs font-extrabold uppercase tracking-wider text-blue-700">
                  <CalendarDays className="w-4 h-4" />
                  <span>Upcoming Session</span>
                </div>

                <span
                  className={`px-3 py-1 rounded-full text-xs font-semibold ${
                    activeInterview?.status === "SCHEDULED"
                      ? "bg-blue-50 text-blue-700 border border-blue-200"
                      : activeInterview?.status === "RESCHEDULE_REQUESTED"
                      ? "bg-amber-50 text-amber-700 border border-amber-200"
                      : activeInterview?.status === "COMPLETED"
                      ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                      : "bg-purple-50 text-purple-700 border border-purple-200"
                  }`}
                >
                  {activeInterview
                    ? activeInterview.status === "PENDING"
                      ? "Pending Slot Selection"
                      : activeInterview.status.replace("_", " ")
                    : "Scheduled"}
                </span>
              </div>

              <div>
                <h4 className="text-xl font-extrabold text-navy-950 font-heading">
                  Interview Details
                </h4>
                <p className="text-xs font-semibold text-slate-500 mt-1 leading-snug">
                  {selectedApp?.job_title || "Junior Software Developer"}
                  <br />
                  <span className="text-slate-700">{selectedApp?.company_name || "Brain Station 23"}</span>
                </p>
              </div>

              {/* Specs Rows */}
              <div className="space-y-2.5 text-xs pt-1 divide-y divide-slate-100">
                <div className="flex items-center justify-between pt-1">
                  <span className="text-slate-500">Interview Type</span>
                  <span className="font-bold text-navy-950">
                    {activeInterview?.interview_type || "Company Interview"}
                  </span>
                </div>

                <div className="flex items-center justify-between pt-2">
                  <span className="text-slate-500">Date</span>
                  <span className="font-bold text-navy-950">
                    {interviewDateStr}
                  </span>
                </div>

                <div className="flex items-center justify-between pt-2">
                  <span className="text-slate-500">Time</span>
                  <span className="font-bold text-navy-950">
                    {interviewTimeStr}
                  </span>
                </div>

                <div className="flex items-center justify-between pt-2">
                  <span className="text-slate-500">Mode</span>
                  <span className="font-bold text-blue-700 flex items-center space-x-1">
                    <Video className="w-3.5 h-3.5" />
                    <span>
                      {activeInterview?.location || activeInterview?.meeting_platform
                        ? `Online (${activeInterview.meeting_platform || "Google Meet"})`
                        : "Online (Google Meet)"}
                    </span>
                  </span>
                </div>

                <div className="flex items-center justify-between pt-2">
                  <span className="text-slate-500">Duration</span>
                  <span className="font-bold text-navy-950">
                    {activeInterview?.duration_minutes || 45} Minutes
                  </span>
                </div>
              </div>
            </div>

            {/* Bottom Trigger Action */}
            <button
              type="button"
              onClick={() => setIsInterviewModalOpen(true)}
              className="w-full py-2.5 rounded-xl border border-slate-300 hover:bg-slate-50 text-slate-800 font-semibold text-xs flex items-center justify-center space-x-2 transition-colors shadow-2xs"
            >
              <span>View Interview Details</span>
              <Calendar className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Right Card: Evaluation Record / Interview Feedback (SKL-10 Preview) */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs flex flex-col justify-between space-y-6">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-1.5 text-xs font-extrabold uppercase tracking-wider text-emerald-700">
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Evaluation Record</span>
                </div>

                <div className="flex items-center space-x-2">
                  <span className="text-[10px] font-bold text-slate-400 uppercase">
                    Status: Completed
                  </span>
                  <span className="px-2.5 py-0.5 rounded-full text-xs font-extrabold bg-emerald-50 text-emerald-700 border border-emerald-200">
                    82 / 100
                  </span>
                </div>
              </div>

              <div>
                <h4 className="text-xl font-extrabold text-navy-950 font-heading">
                  Interview Feedback
                </h4>
                <p className="text-xs font-medium text-slate-500 mt-1">
                  Backend Development Mock Interview
                </p>
              </div>

              {/* Strengths Tags */}
              <div className="space-y-1.5 pt-1">
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">
                  Strengths
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {["Problem Solving", "Communication", "Data Structures"].map((tag) => (
                    <span
                      key={tag}
                      className="px-2.5 py-1 rounded-md text-[11px] font-semibold bg-slate-100 text-slate-700"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </div>

              {/* Improvement Area Tags */}
              <div className="space-y-1.5 pt-1">
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">
                  Improvement Area
                </span>
                <div className="flex flex-wrap gap-1.5">
                  <span className="px-2.5 py-1 rounded-md text-[11px] font-semibold bg-blue-50 text-blue-700">
                    System Design
                  </span>
                  <span className="text-xs text-slate-500 self-center">
                    Microservices, Caching layers
                  </span>
                </div>
              </div>

              {/* Quote box */}
              <div className="p-3 rounded-xl bg-slate-50 border border-slate-100 text-xs text-slate-600 italic leading-relaxed">
                "Strong analytical intuition with clean algorithmic complexity. Continue practicing distributed system design and database indexing problems to boost seniority index."
              </div>
            </div>

            {/* Bottom View Full Feedback Button */}
            <button
              type="button"
              onClick={() => setIsFeedbackModalOpen(true)}
              className="w-full py-2.5 rounded-xl bg-navy-950 hover:bg-navy-900 text-white font-semibold text-xs flex items-center justify-center space-x-2 transition-colors shadow-xs"
            >
              <span>View Full Feedback</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>

      {/* SKL-9 Comprehensive Interview Details Modal */}
      {isInterviewModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-navy-950/60 backdrop-blur-xs">
          <div className="bg-white rounded-2xl border border-slate-200 max-w-lg w-full p-6 space-y-6 shadow-2xl animate-fade-in max-h-[90vh] overflow-y-auto">
            {/* Modal Header */}
            <div className="flex items-start justify-between border-b border-slate-100 pb-4">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center">
                  <Calendar className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-navy-950 font-heading">
                    Interview Session & Scheduling
                  </h3>
                  <p className="text-xs text-slate-500">
                    {selectedApp?.job_title} · {selectedApp?.company_name}
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setIsInterviewModalOpen(false)}
                className="text-slate-400 hover:text-slate-600 p-1 rounded-lg"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Details Summary */}
            <div className="space-y-4 text-xs">
              <div className="grid grid-cols-2 gap-3 p-3.5 rounded-xl bg-slate-50 border border-slate-100">
                <div>
                  <span className="text-slate-400 font-medium">Interview Type:</span>
                  <p className="font-bold text-navy-950 mt-0.5">
                    {activeInterview?.interview_type || "Technical Interview"}
                  </p>
                </div>
                <div>
                  <span className="text-slate-400 font-medium">Session Status:</span>
                  <div className="mt-0.5">
                    <span
                      className={`inline-block px-2.5 py-0.5 rounded-full text-[11px] font-bold ${
                        activeInterview?.status === "SCHEDULED"
                          ? "bg-blue-50 text-blue-700"
                          : activeInterview?.status === "RESCHEDULE_REQUESTED"
                          ? "bg-amber-50 text-amber-700"
                          : "bg-purple-50 text-purple-700"
                      }`}
                    >
                      {activeInterview ? activeInterview.status.replace("_", " ") : "Scheduled"}
                    </span>
                  </div>
                </div>
                <div>
                  <span className="text-slate-400 font-medium">Date & Time:</span>
                  <p className="font-bold text-navy-950 mt-0.5">
                    {interviewDateStr} · {interviewTimeStr}
                  </p>
                </div>
                <div>
                  <span className="text-slate-400 font-medium">Duration:</span>
                  <p className="font-bold text-navy-950 mt-0.5">
                    {activeInterview?.duration_minutes || 45} Minutes
                  </p>
                </div>
              </div>

              {/* Meeting Link Banner */}
              <div className="p-4 rounded-xl bg-blue-50/70 border border-blue-100 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-blue-950 flex items-center space-x-1.5">
                    <Video className="w-4 h-4 text-blue-600" />
                    <span>Virtual Meeting Platform: {activeInterview?.meeting_platform || "Google Meet"}</span>
                  </span>
                  <span className="text-[10px] text-blue-700 font-semibold bg-white px-2 py-0.5 rounded-md border border-blue-200">
                    Live Video
                  </span>
                </div>
                <div className="flex items-center justify-between pt-1">
                  <span className="text-slate-600 truncate max-w-[280px]">
                    {activeInterview?.meeting_link || "https://meet.google.com/s2c-tech-eval"}
                  </span>
                  <a
                    href={activeInterview?.meeting_link || "https://meet.google.com"}
                    target="_blank"
                    rel="noreferrer"
                    className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs rounded-lg transition-colors flex items-center space-x-1 shadow-xs"
                  >
                    <span>Join Room</span>
                    <ExternalLink className="w-3 h-3" />
                  </a>
                </div>
              </div>

              {/* Proposed Slots Booking Section (If Recruiter Proposed Multiple Slots) */}
              {activeInterview?.slots && activeInterview.slots.length > 0 && (
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-navy-950">
                      Proposed Interview Slots
                    </span>
                    <span className="text-[10px] text-slate-400">
                      {activeInterview.status === "PENDING"
                        ? "Select your preferred slot"
                        : "Confirmed Time"}
                    </span>
                  </div>

                  <div className="space-y-2">
                    {activeInterview.slots.map((slot) => {
                      const sDate = new Date(slot.start_time).toLocaleDateString("en-US", {
                        weekday: "short",
                        month: "short",
                        day: "numeric",
                      });
                      const sTime = new Date(slot.start_time).toLocaleTimeString("en-US", {
                        hour: "numeric",
                        minute: "2-digit",
                        hour12: true,
                      });
                      const isChosen = selectedSlotId === slot.id || slot.is_selected;

                      return (
                        <label
                          key={slot.id}
                          className={`flex items-center justify-between p-3 rounded-xl border cursor-pointer transition-all ${
                            isChosen
                              ? "bg-blue-50/60 border-blue-300 ring-2 ring-blue-100"
                              : "bg-white border-slate-200 hover:bg-slate-50"
                          }`}
                        >
                          <div className="flex items-center space-x-3">
                            <input
                              type="radio"
                              name="interview_slot"
                              checked={isChosen}
                              onChange={() => setSelectedSlotId(slot.id)}
                              disabled={activeInterview.status === "COMPLETED"}
                              className="text-blue-600 focus:ring-blue-500"
                            />
                            <div>
                              <p className="font-bold text-navy-950">
                                {sDate} at {sTime} BST
                              </p>
                              <span className="text-[10px] text-slate-400">
                                Duration: {activeInterview.duration_minutes || 45} mins
                              </span>
                            </div>
                          </div>

                          {slot.is_selected && (
                            <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                              ✓ Confirmed Slot
                            </span>
                          )}
                        </label>
                      );
                    })}
                  </div>

                  {activeInterview.status === "PENDING" && (
                    <button
                      type="button"
                      disabled={submittingSlot || !selectedSlotId}
                      onClick={handleSelectSlot}
                      className="w-full mt-2 py-2.5 rounded-xl bg-navy-950 hover:bg-navy-900 text-white font-semibold text-xs shadow-xs transition-colors flex items-center justify-center space-x-1.5"
                    >
                      <CalendarCheck className="w-4 h-4" />
                      <span>{submittingSlot ? "Confirming..." : "Confirm Selected Slot"}</span>
                    </button>
                  )}
                </div>
              )}

              {/* Reschedule Request Form / Drawer */}
              {showRescheduleForm ? (
                <form
                  onSubmit={handleRescheduleSubmit}
                  className="p-4 rounded-xl border border-amber-200 bg-amber-50/40 space-y-3"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-amber-950">
                      Request Date / Time Reschedule
                    </span>
                    <button
                      type="button"
                      onClick={() => setShowRescheduleForm(false)}
                      className="text-xs text-amber-800 font-bold hover:underline"
                    >
                      Cancel
                    </button>
                  </div>

                  <div className="space-y-1">
                    <label className="text-[11px] font-semibold text-slate-700">
                      Reason for Reschedule *
                    </label>
                    <textarea
                      rows={2}
                      required
                      placeholder="e.g., University final exam clash, urgent medical appointment..."
                      value={rescheduleReason}
                      onChange={(e) => setRescheduleReason(e.target.value)}
                      className="w-full p-2.5 rounded-lg border border-slate-200 bg-white text-xs focus:outline-hidden focus:border-amber-500"
                    />
                  </div>

                  <div className="space-y-1">
                    <label className="text-[11px] font-semibold text-slate-700">
                      Preferred Alternative Time (optional)
                    </label>
                    <input
                      type="text"
                      placeholder="e.g., Next Monday after 4:00 PM BST"
                      value={preferredTime}
                      onChange={(e) => setPreferredTime(e.target.value)}
                      className="w-full p-2.5 rounded-lg border border-slate-200 bg-white text-xs focus:outline-hidden focus:border-amber-500"
                    />
                  </div>

                  <button
                    type="submit"
                    disabled={submittingReschedule || !rescheduleReason.trim()}
                    className="w-full py-2 bg-amber-600 hover:bg-amber-700 text-white font-semibold text-xs rounded-lg shadow-xs transition-colors flex items-center justify-center space-x-1"
                  >
                    <Send className="w-3.5 h-3.5" />
                    <span>{submittingReschedule ? "Sending..." : "Send Reschedule Request"}</span>
                  </button>
                </form>
              ) : (
                <div className="flex items-center justify-between p-3 rounded-xl bg-slate-50 border border-slate-100">
                  <div className="space-y-0.5">
                    <span className="font-semibold text-slate-800">
                      Need a different time?
                    </span>
                    <p className="text-[11px] text-slate-500">
                      Notify the recruiter if none of the proposed slots work for you.
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => setShowRescheduleForm(true)}
                    className="px-3 py-1.5 rounded-lg border border-slate-200 hover:bg-white text-slate-700 font-semibold text-xs"
                  >
                    Request Reschedule
                  </button>
                </div>
              )}

              {/* Automated Calendar (.ics) Download & Simulation */}
              <div className="p-3.5 rounded-xl border border-slate-200 flex items-center justify-between bg-white">
                <div className="flex items-center space-x-2.5">
                  <div className="w-8 h-8 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center">
                    <CalendarCheck className="w-4 h-4" />
                  </div>
                  <div>
                    <span className="font-bold text-navy-950 block">
                      Calendar Sync (.ics file)
                    </span>
                    <span className="text-[10px] text-slate-400 block">
                      Compatible with Google Calendar, Outlook, and Apple Calendar
                    </span>
                  </div>
                </div>

                <button
                  type="button"
                  onClick={handleDownloadIcs}
                  className="px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-xs flex items-center space-x-1 transition-colors"
                >
                  <Calendar className="w-3.5 h-3.5" />
                  <span>Download .ics</span>
                </button>
              </div>
            </div>

            <div className="pt-2 border-t border-slate-100 flex items-center justify-between">
              {activeInterview?.status !== "CANCELLED" && activeInterview?.status !== "COMPLETED" ? (
                <button
                  type="button"
                  onClick={async () => {
                    const reason = window.prompt("Reason for declining/cancelling this interview session:");
                    if (reason === null) return;
                    try {
                      await interviewService.updateStatus(activeInterview.id, {
                        status: "CANCELLED",
                        notes: reason || "Declined by candidate",
                      });
                      setIsInterviewModalOpen(false);
                      setNotification({
                        type: "success",
                        message: "Interview invitation declined.",
                      });
                      await fetchApplications();
                    } catch (err) {
                      alert(err.response?.data?.message || "Failed to decline interview.");
                    }
                  }}
                  className="text-xs font-semibold text-rose-600 hover:text-rose-800 hover:underline"
                >
                  Decline / Cancel Session
                </button>
              ) : (
                <div />
              )}

              <button
                type="button"
                onClick={() => setIsInterviewModalOpen(false)}
                className="px-4 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-xs"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* SKL-10 Full Feedback Modal */}
      {isFeedbackModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-navy-950/60 backdrop-blur-xs">
          <div className="bg-white rounded-2xl border border-slate-200 max-w-lg w-full p-6 space-y-5 shadow-2xl animate-fade-in">
            <div className="flex items-start justify-between border-b border-slate-100 pb-4">
              <div>
                <h3 className="text-lg font-bold text-navy-950 font-heading">
                  Full Interview Evaluation & Scorecard
                </h3>
                <p className="text-xs text-slate-500">
                  Candidate: {user?.first_name} {user?.last_name} · Position: {selectedApp?.job_title}
                </p>
              </div>
              <button
                type="button"
                onClick={() => setIsFeedbackModalOpen(false)}
                className="text-slate-400 hover:text-slate-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-4 text-xs">
              <div className="flex items-center justify-between p-3.5 rounded-xl bg-emerald-50/70 border border-emerald-200 text-emerald-950">
                <span className="font-bold">Overall Technical Rating</span>
                <span className="px-3 py-1 rounded-full text-xs font-extrabold bg-emerald-600 text-white">
                  82 / 100 · High Recommendation
                </span>
              </div>

              <div className="space-y-2">
                <span className="font-bold text-navy-950">Competency Breakdown</span>
                <div className="space-y-2">
                  {[
                    { label: "Data Structures & Algorithms", score: "88%", level: "Advanced" },
                    { label: "REST APIs & Backend Architecture", score: "84%", level: "Proficient" },
                    { label: "Database Design & SQL Indexing", score: "76%", level: "Intermediate" },
                    { label: "Technical Communication & Reasoning", score: "85%", level: "Advanced" },
                  ].map((item) => (
                    <div
                      key={item.label}
                      className="flex items-center justify-between p-2.5 rounded-lg border border-slate-100 bg-slate-50"
                    >
                      <span className="font-medium text-slate-700">{item.label}</span>
                      <div className="flex items-center space-x-2">
                        <span className="font-bold text-navy-950">{item.score}</span>
                        <span className="text-[10px] text-slate-500">({item.level})</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="space-y-1 bg-slate-50 p-3.5 rounded-xl border border-slate-200">
                <span className="font-bold text-slate-900 block">
                  Lead Interviewer Notes
                </span>
                <p className="text-slate-600 leading-relaxed">
                  "Candidate demonstrated strong problem-solving instinct when optimizing array operations and BST traversal. Explored edge cases methodically. Recommended for progression to final executive round."
                </p>
              </div>
            </div>

            <div className="pt-2 border-t border-slate-100 flex justify-end">
              <button
                type="button"
                onClick={() => setIsFeedbackModalOpen(false)}
                className="px-4 py-2 rounded-xl bg-navy-950 text-white font-semibold text-xs"
              >
                Close Scorecard
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Withdraw Modal */}
      {isWithdrawModalOpen && (
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
                <strong className="text-navy-900">{selectedApp?.job_title}</strong> at{" "}
                <strong className="text-navy-900">{selectedApp?.company_name}</strong>?
              </p>
            </div>

            <div className="flex items-center space-x-3 pt-2">
              <button
                type="button"
                disabled={withdrawLoading}
                onClick={() => setIsWithdrawModalOpen(false)}
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
