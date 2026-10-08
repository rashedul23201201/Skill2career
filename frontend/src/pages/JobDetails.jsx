import React, { useState, useEffect } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import jobService from "../services/jobService";
import { ROUTES, USER_ROLES } from "../constants";
import {
  ArrowLeft,
  Building2,
  MapPin,
  Briefcase,
  Clock,
  Calendar,
  CheckCircle2,
  DollarSign,
  Edit3,
  Trash2,
  ShieldAlert,
  Share2,
  ExternalLink,
  Layers,
} from "lucide-react";

export const JobDetails = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();

  const [job, setJob] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [actionLoading, setActionLoading] = useState(false);
  const [applyModalOpen, setApplyModalOpen] = useState(false);

  useEffect(() => {
    const fetchJob = async () => {
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

    fetchJob();
  }, [id]);

  const isOwner = user && job?.company_id === user.id;
  const canManage = isOwner || user?.role === USER_ROLES.ADMIN;

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

        {/* Compensation & Apply Card */}
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

          <button
            type="button"
            onClick={() => setApplyModalOpen(true)}
            className="w-full py-2.5 rounded-xl bg-navy-950 hover:bg-navy-900 text-white font-semibold text-xs shadow-sm transition-all text-center"
          >
            Apply Now
          </button>
        </div>
      </div>

      {/* 2-Column: Left (Description & Requirements) and Right (Company Overview) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-8 bg-white rounded-2xl border border-slate-200 p-6 sm:p-8 shadow-sm space-y-8">
          {/* Skills Required */}
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

          {/* Description */}
          <div className="space-y-3">
            <h3 className="text-base font-bold text-navy-950 font-heading">
              Role Description
            </h3>
            <p className="text-sm text-slate-600 leading-relaxed whitespace-pre-line">
              {job.description}
            </p>
          </div>

          {/* Requirements */}
          <div className="space-y-3 pt-4 border-t border-slate-100">
            <h3 className="text-base font-bold text-navy-950 font-heading">
              Candidate Requirements & Qualifications
            </h3>
            <p className="text-sm text-slate-600 leading-relaxed whitespace-pre-line">
              {job.requirements}
            </p>
          </div>
        </div>

        {/* Right Sidebar: Hiring Company Information */}
        <div className="lg:col-span-4 bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-6 self-start">
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
      </div>

      {/* Application Notice Modal */}
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
