import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import {
  X,
  Bookmark,
  Trash2,
  ExternalLink,
  MapPin,
  Building2,
  Calendar,
  AlertCircle,
  Briefcase,
  CheckCircle2,
  ArrowRight,
  Clock,
} from "lucide-react";
import jobService from "../../services/jobService";
import { ROUTES } from "../../constants";

export const SavedJobsDrawer = ({ isOpen, onClose, onSavedCountChange }) => {
  const [savedJobs, setSavedJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [statusFilter, setStatusFilter] = useState("all");
  const [removingId, setRemovingId] = useState(null);

  const fetchSavedJobs = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await jobService.getSavedJobs();
      if (res?.data) {
        setSavedJobs(res.data);
        if (onSavedCountChange) {
          onSavedCountChange(res.data.length);
        }
      }
    } catch (err) {
      console.error("Failed to load saved jobs:", err);
      setError("Unable to load saved vacancies.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchSavedJobs();
    }
  }, [isOpen]);

  // Handle ESC key to close
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  const handleRemove = async (e, savedJob) => {
    e.preventDefault();
    e.stopPropagation();

    const targetId = savedJob.id;
    setRemovingId(targetId);

    // Optimistic UI update
    const previous = savedJobs;
    const nextList = savedJobs.filter((item) => item.id !== targetId);
    setSavedJobs(nextList);
    if (onSavedCountChange) {
      onSavedCountChange(nextList.length);
    }

    try {
      await jobService.unsaveJob(savedJob.job_id || savedJob.id);
    } catch (err) {
      console.error("Failed to remove saved job:", err);
      // Revert if error
      setSavedJobs(previous);
      if (onSavedCountChange) {
        onSavedCountChange(previous.length);
      }
    } finally {
      setRemovingId(null);
    }
  };

  const filteredJobs = savedJobs.filter((item) => {
    if (statusFilter === "all") return true;
    if (statusFilter === "active") return item.computed_status === "Active";
    if (statusFilter === "closed_expired") {
      return item.computed_status === "Closed" || item.computed_status === "Expired";
    }
    return true;
  });

  const getStatusBadge = (status) => {
    switch (status) {
      case "Active":
        return {
          bg: "bg-emerald-50 text-emerald-700 border-emerald-200",
          icon: <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 mr-1.5" />,
          label: "Active",
        };
      case "Expired":
        return {
          bg: "bg-amber-50 text-amber-700 border-amber-200",
          icon: <span className="w-1.5 h-1.5 rounded-full bg-amber-500 mr-1.5" />,
          label: "Expired",
        };
      case "Closed":
      default:
        return {
          bg: "bg-slate-100 text-slate-600 border-slate-200",
          icon: <span className="w-1.5 h-1.5 rounded-full bg-slate-400 mr-1.5" />,
          label: "Closed",
        };
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-slate-900/50 backdrop-blur-xs transition-opacity duration-300"
        onClick={onClose}
        aria-hidden="true"
      />

      <div className="fixed inset-y-0 right-0 max-w-full flex pl-10">
        <div className="w-screen max-w-md bg-white shadow-2xl flex flex-col h-full border-l border-slate-200 transform transition-transform duration-300 ease-out">
          {/* Drawer Header */}
          <div className="p-5 sm:p-6 border-b border-slate-200 flex items-center justify-between bg-slate-50/70">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center flex-shrink-0 shadow-2xs">
                <Bookmark className="w-5 h-5 fill-blue-600" />
              </div>
              <div>
                <div className="flex items-center space-x-2">
                  <h2 className="text-lg font-extrabold text-navy-950 font-heading">
                    Saved Jobs
                  </h2>
                  <span className="px-2 py-0.5 rounded-full text-xs font-bold bg-blue-100 text-blue-800">
                    {savedJobs.length}
                  </span>
                </div>
                <p className="text-xs text-slate-500 mt-0.5">
                  Bookmarked vacancies for easy reference & direct apply.
                </p>
              </div>
            </div>

            <button
              type="button"
              onClick={onClose}
              className="p-2 rounded-xl text-slate-400 hover:text-slate-700 hover:bg-slate-200/60 transition-colors"
              aria-label="Close saved jobs drawer"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Filter Tabs */}
          <div className="px-5 pt-3 pb-2 border-b border-slate-100 flex items-center space-x-2 bg-white">
            <button
              type="button"
              onClick={() => setStatusFilter("all")}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                statusFilter === "all"
                  ? "bg-navy-950 text-white shadow-xs"
                  : "bg-slate-100 text-slate-600 hover:bg-slate-200"
              }`}
            >
              All ({savedJobs.length})
            </button>
            <button
              type="button"
              onClick={() => setStatusFilter("active")}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                statusFilter === "active"
                  ? "bg-emerald-600 text-white shadow-xs"
                  : "bg-slate-100 text-slate-600 hover:bg-slate-200"
              }`}
            >
              Active ({savedJobs.filter((j) => j.computed_status === "Active").length})
            </button>
            <button
              type="button"
              onClick={() => setStatusFilter("closed_expired")}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                statusFilter === "closed_expired"
                  ? "bg-slate-800 text-white shadow-xs"
                  : "bg-slate-100 text-slate-600 hover:bg-slate-200"
              }`}
            >
              Closed / Expired ({savedJobs.filter((j) => j.computed_status !== "Active").length})
            </button>
          </div>

          {/* Jobs List Body */}
          <div className="flex-1 overflow-y-auto p-5 space-y-4">
            {loading ? (
              <div className="space-y-4">
                {[1, 2, 3].map((n) => (
                  <div
                    key={n}
                    className="p-4 rounded-xl border border-slate-200 animate-pulse space-y-3"
                  >
                    <div className="h-4 w-2/3 bg-slate-100 rounded" />
                    <div className="h-3 w-1/2 bg-slate-100 rounded" />
                    <div className="h-8 w-full bg-slate-100 rounded" />
                  </div>
                ))}
              </div>
            ) : error ? (
              <div className="p-6 text-center space-y-3">
                <AlertCircle className="w-8 h-8 text-amber-500 mx-auto" />
                <p className="text-sm text-slate-600">{error}</p>
                <button
                  type="button"
                  onClick={fetchSavedJobs}
                  className="px-4 py-2 text-xs font-bold rounded-xl bg-navy-950 text-white"
                >
                  Retry
                </button>
              </div>
            ) : filteredJobs.length === 0 ? (
              <div className="py-12 text-center space-y-4">
                <div className="w-14 h-14 rounded-2xl bg-blue-50 text-blue-500 flex items-center justify-center mx-auto shadow-2xs">
                  <Bookmark className="w-7 h-7" />
                </div>
                <div className="max-w-xs mx-auto space-y-1">
                  <h4 className="text-sm font-extrabold text-navy-950 font-heading">
                    {statusFilter === "all"
                      ? "No saved jobs yet"
                      : "No vacancies match this filter"}
                  </h4>
                  <p className="text-xs text-slate-500">
                    Bookmark vacancies you find interesting to track deadlines and apply when ready.
                  </p>
                </div>
                <Link
                  to={ROUTES.JOBS || "/jobs"}
                  onClick={onClose}
                  className="inline-flex items-center space-x-1.5 px-4 py-2 text-xs font-bold rounded-xl bg-navy-950 text-white hover:bg-navy-900 transition-colors shadow-xs"
                >
                  <span>Explore Vacancies</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            ) : (
              filteredJobs.map((item) => {
                const job = item.job || {};
                const statusBadge = getStatusBadge(item.computed_status);
                const isActionable = item.computed_status === "Active";

                return (
                  <div
                    key={item.id}
                    className="p-4 rounded-2xl border border-slate-200 bg-white hover:border-slate-300 transition-all shadow-xs space-y-3 group"
                  >
                    {/* Status Pill & 1-Click Remove */}
                    <div className="flex items-center justify-between">
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-bold border ${statusBadge.bg}`}
                      >
                        {statusBadge.icon}
                        <span>{statusBadge.label}</span>
                      </span>

                      <button
                        type="button"
                        onClick={(e) => handleRemove(e, item)}
                        disabled={removingId === item.id}
                        className="text-slate-400 hover:text-rose-600 p-1.5 rounded-lg hover:bg-rose-50 transition-colors"
                        title="Remove from saved jobs"
                        aria-label="Remove saved job"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>

                    {/* Job Details */}
                    <div>
                      <Link
                        to={`/jobs/${item.job_id}`}
                        onClick={onClose}
                        className="text-sm font-bold text-navy-950 hover:text-blue-600 transition-colors font-heading block line-clamp-1"
                      >
                        {job.title || "Job Vacancy"}
                      </Link>

                      <div className="flex items-center space-x-2 text-xs text-slate-500 font-medium mt-1">
                        <span className="font-semibold text-slate-700 truncate">
                          {job.company_name || "Hiring Company"}
                        </span>
                        <span>•</span>
                        <span>{job.location || "Dhaka"}</span>
                      </div>

                      <div className="flex items-center justify-between text-xs font-bold text-slate-800 mt-2">
                        <span>{job.compensation || "Competitive"}</span>
                        <span className="text-[11px] font-normal text-slate-400">
                          Saved {item.saved_at ? new Date(item.saved_at).toLocaleDateString() : ""}
                        </span>
                      </div>
                    </div>

                    {/* Deadline Warning if active */}
                    {job.deadline && item.computed_status === "Active" && (
                      <div className="flex items-center space-x-1.5 text-[11px] text-amber-600 font-medium bg-amber-50/60 rounded-lg px-2.5 py-1 border border-amber-100">
                        <Clock className="w-3.5 h-3.5 flex-shrink-0" />
                        <span>
                          Deadline: {new Date(job.deadline).toLocaleDateString()}
                        </span>
                      </div>
                    )}

                    {/* Action Button */}
                    <div className="pt-1">
                      {isActionable ? (
                        <Link
                          to={`/jobs/${item.job_id}`}
                          onClick={onClose}
                          className="w-full py-2 px-3 rounded-xl text-xs font-bold bg-navy-950 hover:bg-navy-900 text-white transition-all text-center flex items-center justify-center space-x-1.5 shadow-xs"
                        >
                          <span>Apply Now</span>
                          <ExternalLink className="w-3.5 h-3.5" />
                        </Link>
                      ) : (
                        <div className="w-full py-1.5 text-center text-xs font-semibold text-slate-400 bg-slate-100 rounded-xl">
                          Applications Closed
                        </div>
                      )}
                    </div>
                  </div>
                );
              })
            )}
          </div>

          {/* Drawer Footer */}
          <div className="p-4 border-t border-slate-200 bg-slate-50 flex items-center justify-between text-xs text-slate-500 font-medium">
            <span>Real-time deadline tracking</span>
            <button
              type="button"
              onClick={onClose}
              className="px-3 py-1.5 font-bold rounded-lg bg-white border border-slate-200 text-slate-700 hover:bg-slate-100 transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SavedJobsDrawer;
