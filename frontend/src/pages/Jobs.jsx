import React, { useState, useEffect, useCallback } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import jobService from "../services/jobService";
import { ROUTES, USER_ROLES } from "../constants";
import {
  Search,
  Briefcase,
  Heart,
  Plus,
  MapPin,
  Clock,
  ShieldCheck,
  Edit3,
  Building2,
  AlertCircle,
  ExternalLink,
} from "lucide-react";

export const Jobs = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Search input state (un-debounced issue avoided by searching on submit or filter click)
  const [searchInput, setSearchInput] = useState(searchParams.get("search") || "");
  const [appliedSearch, setAppliedSearch] = useState(searchParams.get("search") || "");

  // Posting type filter: "All", "Job", "Internship"
  const [typeFilter, setTypeFilter] = useState(searchParams.get("type") || "All");

  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalJobs, setTotalJobs] = useState(0);

  // Bookmarked IDs saved in localStorage
  const [bookmarkedIds, setBookmarkedIds] = useState(() => {
    try {
      const saved = localStorage.getItem("s2c_bookmarked_jobs");
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });

  const toggleBookmark = (jobId) => {
    setBookmarkedIds((prev) => {
      const next = prev.includes(jobId)
        ? prev.filter((id) => id !== jobId)
        : [...prev, jobId];
      try {
        localStorage.setItem("s2c_bookmarked_jobs", JSON.stringify(next));
      } catch {
        // ignore storage errors
      }
      return next;
    });
  };

  // Tab: "all" or "my_jobs" (for companies / admins)
  const isCompanyOrAdmin =
    user?.role === USER_ROLES.COMPANY || user?.role === USER_ROLES.ADMIN;
  const [activeTab, setActiveTab] = useState(
    searchParams.get("tab") === "my_jobs" && isCompanyOrAdmin
      ? "my_jobs"
      : "all"
  );

  const fetchJobs = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const params = {
        page,
        size: 8,
      };

      if (appliedSearch.trim()) {
        params.search = appliedSearch.trim();
      }

      if (typeFilter === "Jobs") {
        params.posting_type = "Job";
      } else if (typeFilter === "Internships") {
        params.posting_type = "Internship";
      }

      if (activeTab === "my_jobs") {
        params.my_jobs = true;
      }

      const res = await jobService.getJobs(params);
      if (res?.data) {
        setJobs(res.data.items || []);
        setTotalPages(res.data.total_pages || 1);
        setTotalJobs(res.data.total || 0);
      }
    } catch (err) {
      console.error("Failed to load vacancies:", err);
      setError("Unable to load job postings. Please verify backend connection.");
    } finally {
      setLoading(false);
    }
  }, [page, appliedSearch, typeFilter, activeTab]);

  useEffect(() => {
    fetchJobs();
  }, [fetchJobs]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setAppliedSearch(searchInput.trim());
    setPage(1);
  };

  const handleTypeFilterClick = (type) => {
    setTypeFilter(type);
    setPage(1);
  };

  const handleTabChange = (tab) => {
    setActiveTab(tab);
    setPage(1);
    setSearchParams(tab === "my_jobs" ? { tab: "my_jobs" } : {});
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">
      {/* 1. Header matching Jobs and internships.png */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl sm:text-4xl font-extrabold text-navy-950 font-heading tracking-tight">
            Jobs & Internships
          </h1>
          <p className="mt-2 text-base text-slate-500">
            Find job and internship opportunities from companies in Bangladesh.
          </p>
        </div>

        {isCompanyOrAdmin && (
          <div className="flex items-center space-x-3">
            <Link
              to={ROUTES.JOB_NEW}
              className="inline-flex items-center space-x-2 bg-navy-950 hover:bg-navy-900 text-white font-semibold text-sm px-4 py-2.5 rounded-xl shadow-sm transition-all hover:shadow"
            >
              <Plus className="w-4 h-4 text-emerald-400" />
              <span>Post Vacancy</span>
            </Link>
          </div>
        )}
      </div>

      {/* 2. Recruiter Tab Switcher (if Company/Admin) */}
      {isCompanyOrAdmin && (
        <div className="flex items-center space-x-2 border-b border-slate-200 pb-2">
          <button
            type="button"
            onClick={() => handleTabChange("all")}
            className={`px-4 py-2 text-sm font-semibold rounded-lg transition-colors ${
              activeTab === "all"
                ? "bg-navy-950 text-white"
                : "text-slate-600 hover:text-navy-950 hover:bg-slate-100"
            }`}
          >
            All Open Opportunities
          </button>
          <button
            type="button"
            onClick={() => handleTabChange("my_jobs")}
            className={`px-4 py-2 text-sm font-semibold rounded-lg transition-colors ${
              activeTab === "my_jobs"
                ? "bg-navy-950 text-white"
                : "text-slate-600 hover:text-navy-950 hover:bg-slate-100"
            }`}
          >
            My Company Listings
          </button>
        </div>
      )}

      {/* 3. Search Bar matching Jobs and internships.png */}
      <form onSubmit={handleSearchSubmit} className="flex gap-3 max-w-2xl">
        <div className="relative flex-1">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder="Search jobs, skills or companies"
            className="w-full pl-11 pr-4 py-3 bg-white border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all text-navy-950 placeholder:text-slate-400"
          />
        </div>
        <button
          type="submit"
          className="bg-navy-950 hover:bg-navy-900 text-white text-sm font-semibold px-6 py-3 rounded-xl shadow-sm transition-colors flex items-center space-x-2"
        >
          <span>Search</span>
        </button>
      </form>

      {/* 4. Filter Pills matching Jobs and internships.png (All, Jobs, Internships) */}
      <div className="flex items-center space-x-2">
        {["All", "Jobs", "Internships"].map((filter) => {
          const isSelected = typeFilter === filter;
          return (
            <button
              key={filter}
              type="button"
              onClick={() => handleTypeFilterClick(filter)}
              className={`px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
                isSelected
                  ? "bg-navy-950 text-white shadow-sm"
                  : "bg-white text-slate-600 border border-slate-200 hover:border-slate-300 hover:bg-slate-50"
              }`}
            >
              {filter}
            </button>
          );
        })}
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* 5. Loading Skeleton */}
      {loading && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {[1, 2, 3, 4].map((i) => (
            <div
              key={i}
              className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm animate-pulse space-y-4"
            >
              <div className="flex justify-between items-start">
                <div className="space-y-2 w-3/4">
                  <div className="w-48 h-5 bg-slate-200 rounded" />
                  <div className="w-32 h-4 bg-slate-100 rounded" />
                </div>
                <div className="w-6 h-6 bg-slate-200 rounded-full" />
              </div>
              <div className="flex gap-2">
                <div className="w-16 h-6 bg-slate-200 rounded" />
                <div className="w-16 h-6 bg-slate-200 rounded" />
                <div className="w-16 h-6 bg-slate-200 rounded" />
              </div>
              <div className="flex justify-between items-end pt-4 border-t border-slate-100">
                <div className="w-24 h-6 bg-slate-200 rounded" />
                <div className="w-24 h-8 bg-slate-200 rounded" />
              </div>
            </div>
          ))}
        </div>
      )}

      {/* 6. Empty State */}
      {!loading && jobs.length === 0 && (
        <div className="text-center py-16 bg-white rounded-2xl border border-slate-200 p-8 space-y-4">
          <div className="w-12 h-12 mx-auto rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center">
            <Briefcase className="w-6 h-6" />
          </div>
          <h3 className="text-lg font-bold text-navy-950 font-heading">
            No vacancies found
          </h3>
          <p className="text-slate-500 text-sm max-w-sm mx-auto">
            {appliedSearch || typeFilter !== "All"
              ? "Try adjusting your search query or filter criteria."
              : "No vacancies are currently published in this section."}
          </p>
          {isCompanyOrAdmin && (
            <Link
              to={ROUTES.JOB_NEW}
              className="inline-flex items-center space-x-2 bg-navy-950 text-white text-xs font-semibold px-4 py-2 rounded-xl mt-2"
            >
              <Plus className="w-4 h-4" />
              <span>Create First Job Post</span>
            </Link>
          )}
        </div>
      )}

      {/* 7. 2x2 Grid of Job / Internship Cards matching Jobs and internships.png */}
      {!loading && jobs.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {jobs.map((job) => {
            const isOwner = user && job.company_id === user.id;
            const canManage = isOwner || user?.role === USER_ROLES.ADMIN;
            const isBookmarked = bookmarkedIds.includes(job.id);
            const isInternship =
              (job.posting_type || "").toLowerCase() === "internship";

            return (
              <div
                key={job.id}
                className="bg-white rounded-2xl border border-slate-200 p-6 sm:p-7 shadow-xs hover:border-slate-300 hover:shadow-md transition-all flex flex-col justify-between group"
              >
                <div className="space-y-4">
                  {/* Top Row: Title, Subtitle & Heart Bookmark */}
                  <div className="flex items-start justify-between gap-4">
                    <div className="space-y-1">
                      <h3 className="text-xl font-bold text-navy-950 font-heading group-hover:text-blue-600 transition-colors">
                        {job.title}
                      </h3>
                      <p className="text-xs sm:text-sm text-slate-500 font-medium">
                        {job.company_name} · {job.location} ·{" "}
                        {job.posting_type === "Internship"
                          ? "Internship"
                          : job.work_mode || "Full-time"}
                      </p>
                    </div>

                    <button
                      type="button"
                      onClick={() => toggleBookmark(job.id)}
                      className="p-1.5 rounded-lg text-slate-400 hover:text-red-500 transition-colors"
                      title={
                        isBookmarked ? "Remove bookmark" : "Save this job"
                      }
                    >
                      <Heart
                        className={`w-5 h-5 ${
                          isBookmarked
                            ? "fill-red-500 text-red-500"
                            : "text-slate-400 hover:text-red-500"
                        }`}
                      />
                    </button>
                  </div>

                  {/* Skills / Tags Pills matching Jobs and internships.png */}
                  <div className="flex flex-wrap gap-2 pt-1">
                    {(job.skills || []).map((skill, sIdx) => (
                      <span
                        key={sIdx}
                        className="px-2.5 py-1 text-xs font-semibold rounded-md bg-slate-100 text-slate-700"
                      >
                        {skill}
                      </span>
                    ))}
                    {(!job.skills || job.skills.length === 0) && (
                      <span className="px-2.5 py-1 text-xs font-semibold rounded-md bg-slate-100 text-slate-700">
                        {job.category || "Software"}
                      </span>
                    )}
                  </div>
                </div>

                {/* Bottom Row: Salary / Stipend and Actions matching Jobs and internships.png */}
                <div className="mt-6 pt-5 border-t border-slate-100 flex items-end justify-between gap-4">
                  <div>
                    <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block mb-0.5">
                      {isInternship ? "DURATION & STIPEND" : "SALARY"}
                    </span>
                    <div className="text-base sm:text-lg font-extrabold text-navy-950">
                      {isInternship && job.duration
                        ? `${job.duration} · ${job.compensation}`
                        : job.compensation}
                    </div>
                  </div>

                  <div className="flex items-center space-x-2">
                    {canManage && (
                      <Link
                        to={`/jobs/${job.id}/manage`}
                        className="inline-flex items-center space-x-1.5 px-3 py-2 text-xs font-semibold rounded-lg border border-slate-200 hover:bg-slate-50 text-slate-700 transition-colors"
                        title="Edit vacancy details"
                      >
                        <Edit3 className="w-3.5 h-3.5" />
                        <span>Manage</span>
                      </Link>
                    )}
                    <Link
                      to={`/jobs/${job.id}`}
                      className="bg-navy-950 hover:bg-navy-900 text-white text-xs font-semibold px-5 py-2.5 rounded-lg shadow-sm transition-all text-center"
                    >
                      View Details
                    </Link>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* 8. Pagination matching Jobs and internships.png (Previous, 1, 2, 3, Next) */}
      {!loading && totalPages > 1 && (
        <div className="flex items-center justify-center space-x-2 pt-6">
          <button
            type="button"
            disabled={page <= 1}
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            className="px-3.5 py-1.5 text-xs font-medium rounded-lg text-slate-600 hover:bg-slate-100 disabled:opacity-40 disabled:hover:bg-transparent transition-colors"
          >
            Previous
          </button>

          {Array.from({ length: totalPages }, (_, idx) => idx + 1).map(
            (pNum) => (
              <button
                key={pNum}
                type="button"
                onClick={() => setPage(pNum)}
                className={`w-8 h-8 rounded-lg text-xs font-semibold transition-colors ${
                  page === pNum
                    ? "bg-navy-950 text-white"
                    : "text-slate-600 hover:bg-slate-100"
                }`}
              >
                {pNum}
              </button>
            )
          )}

          <button
            type="button"
            disabled={page >= totalPages}
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            className="px-3.5 py-1.5 text-xs font-medium rounded-lg text-slate-600 hover:bg-slate-100 disabled:opacity-40 disabled:hover:bg-transparent transition-colors"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
};

export default Jobs;
