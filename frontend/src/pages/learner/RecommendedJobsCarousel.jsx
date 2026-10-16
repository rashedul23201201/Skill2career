import React, { useState, useEffect, useRef } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  Sparkles,
  ChevronLeft,
  ChevronRight,
  Bookmark,
  MapPin,
  Building2,
  ShieldCheck,
  CheckCircle2,
  ArrowRight,
  ExternalLink,
  Briefcase,
  AlertCircle,
  SlidersHorizontal,
} from "lucide-react";
import jobService from "../../services/jobService";
import { ROUTES } from "../../constants";

export const RecommendedJobsCarousel = ({ onSavedJobsChanged, onOpenSavedDrawer }) => {
  const navigate = useNavigate();
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [savingJobId, setSavingJobId] = useState(null);

  const carouselRef = useRef(null);

  const fetchRecommendations = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await jobService.getRecommendedJobs({ limit: 12 });
      if (res?.data) {
        setRecommendations(res.data);
      }
    } catch (err) {
      console.error("Failed to fetch smart recommendations:", err);
      setError("Unable to load recommendations at this time.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRecommendations();
  }, []);

  const handleToggleSave = async (e, job) => {
    e.preventDefault();
    e.stopPropagation();

    const jobId = job.id;
    const prevSaved = job.is_saved;

    // Optimistic UI update
    setRecommendations((prev) =>
      prev.map((item) => (item.id === jobId ? { ...item, is_saved: !prevSaved } : item))
    );
    setSavingJobId(jobId);

    try {
      const res = await jobService.saveJob(jobId);
      if (res?.data) {
        setRecommendations((prev) =>
          prev.map((item) =>
            item.id === jobId ? { ...item, is_saved: res.data.is_saved } : item
          )
        );
      }
      if (onSavedJobsChanged) {
        onSavedJobsChanged();
      }
    } catch (err) {
      console.error("Failed to bookmark vacancy:", err);
      // Revert optimistic update
      setRecommendations((prev) =>
        prev.map((item) => (item.id === jobId ? { ...item, is_saved: prevSaved } : item))
      );
    } finally {
      setSavingJobId(null);
    }
  };

  const visibleCardsCount = 3;
  const maxIndex = Math.max(0, recommendations.length - visibleCardsCount);

  const nextSlide = () => {
    setCurrentIndex((prev) => Math.min(prev + 1, maxIndex));
  };

  const prevSlide = () => {
    setCurrentIndex((prev) => Math.max(prev - 1, 0));
  };

  const getMatchScoreBadge = (score) => {
    if (score >= 85) {
      return {
        bg: "bg-emerald-50 text-emerald-700 border-emerald-200",
        ring: "bg-emerald-500",
        label: `${score}% Match`,
      };
    }
    if (score >= 65) {
      return {
        bg: "bg-blue-50 text-blue-700 border-blue-200",
        ring: "bg-blue-600",
        label: `${score}% Match`,
      };
    }
    return {
      bg: "bg-amber-50 text-amber-700 border-amber-200",
      ring: "bg-amber-500",
      label: `${score}% Match`,
    };
  };

  return (
    <div className="space-y-4">
      {/* Header with Title and Carousel Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="space-y-1">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-blue-600 to-indigo-600 text-white flex items-center justify-center shadow-xs">
              <Sparkles className="w-4 h-4" />
            </div>
            <h2 className="text-xl sm:text-2xl font-extrabold text-navy-950 font-heading">
              Recommended for You
            </h2>
            <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-blue-50 text-blue-700 border border-blue-200 hidden sm:inline-flex items-center space-x-1">
              <span>Smart AI Match</span>
            </span>
          </div>
          <p className="text-xs text-slate-500 font-medium">
            Curated vacancies ranked by matching your profile skills and target career role.
          </p>
        </div>

        <div className="flex items-center space-x-2 self-end sm:self-auto">
          {recommendations.length > visibleCardsCount && (
            <div className="flex items-center space-x-1.5 mr-2">
              <button
                type="button"
                onClick={prevSlide}
                disabled={currentIndex === 0}
                className="w-8 h-8 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 disabled:opacity-30 disabled:cursor-not-allowed flex items-center justify-center text-slate-700 transition-colors shadow-xs"
                aria-label="Previous recommendations"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <span className="text-[11px] font-bold text-slate-500 px-1">
                {currentIndex + 1} / {maxIndex + 1}
              </span>
              <button
                type="button"
                onClick={nextSlide}
                disabled={currentIndex >= maxIndex}
                className="w-8 h-8 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 disabled:opacity-30 disabled:cursor-not-allowed flex items-center justify-center text-slate-700 transition-colors shadow-xs"
                aria-label="Next recommendations"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          )}

          <Link
            to={ROUTES.JOBS || "/jobs"}
            className="inline-flex items-center space-x-1 text-xs font-bold text-blue-600 hover:text-blue-800 transition-colors px-2 py-1"
          >
            <span>Explore All Jobs</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </div>

      {/* Content Area */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {[1, 2, 3].map((n) => (
            <div
              key={n}
              className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs animate-pulse space-y-4"
            >
              <div className="flex justify-between items-center">
                <div className="h-6 w-24 bg-slate-100 rounded-full" />
                <div className="h-7 w-7 bg-slate-100 rounded-lg" />
              </div>
              <div className="space-y-2">
                <div className="h-5 w-3/4 bg-slate-100 rounded" />
                <div className="h-4 w-1/2 bg-slate-100 rounded" />
              </div>
              <div className="h-8 w-full bg-slate-100 rounded-xl" />
            </div>
          ))}
        </div>
      ) : error ? (
        <div className="bg-white rounded-2xl border border-slate-200 p-8 text-center space-y-3">
          <AlertCircle className="w-8 h-8 text-amber-500 mx-auto" />
          <p className="text-sm font-semibold text-slate-700">{error}</p>
          <button
            type="button"
            onClick={fetchRecommendations}
            className="px-4 py-2 text-xs font-bold rounded-xl bg-navy-950 text-white hover:bg-navy-900 transition-colors"
          >
            Retry
          </button>
        </div>
      ) : recommendations.length === 0 ? (
        <div className="bg-gradient-to-br from-slate-50 to-blue-50/40 rounded-2xl border border-slate-200/80 p-8 text-center space-y-4">
          <div className="w-12 h-12 rounded-2xl bg-blue-100/80 text-blue-600 flex items-center justify-center mx-auto shadow-xs">
            <Sparkles className="w-6 h-6" />
          </div>
          <div className="max-w-md mx-auto space-y-1">
            <h3 className="text-base font-extrabold text-navy-950 font-heading">
              No matching vacancies found right now
            </h3>
            <p className="text-xs text-slate-500">
              Enhance your candidate profile with additional skills and target roles to unlock highly personalized job recommendations.
            </p>
          </div>
          <div className="flex items-center justify-center space-x-3 pt-1">
            <Link
              to={ROUTES.LEARNER_PROFILE || "/learner/profile"}
              className="inline-flex items-center space-x-1.5 px-4 py-2 text-xs font-bold rounded-xl bg-navy-950 text-white hover:bg-navy-900 transition-colors shadow-xs"
            >
              <SlidersHorizontal className="w-3.5 h-3.5" />
              <span>Update Profile Skills</span>
            </Link>
            <Link
              to={ROUTES.JOBS || "/jobs"}
              className="inline-flex items-center space-x-1 px-4 py-2 text-xs font-semibold rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 transition-colors shadow-xs"
            >
              <span>Browse All Openings</span>
            </Link>
          </div>
        </div>
      ) : (
        <div className="overflow-hidden relative" ref={carouselRef}>
          <div
            className="flex transition-transform duration-500 ease-out gap-5"
            style={{
              transform: `translateX(-${currentIndex * (100 / visibleCardsCount + 1.2)}%)`,
            }}
          >
            {recommendations.map((job) => {
              const badge = getMatchScoreBadge(job.match_score);
              const matchedSkillsList = job.matched_skills || [];
              const isSaved = Boolean(job.is_saved);

              return (
                <div
                  key={job.id}
                  className="w-full md:w-[calc(50%-10px)] lg:w-[calc(33.333%-14px)] flex-shrink-0 bg-white rounded-2xl border border-slate-200 hover:border-blue-300 hover:shadow-md transition-all duration-300 p-5 sm:p-6 flex flex-col justify-between space-y-4 group"
                >
                  {/* Top Row: Match Badge & Bookmark Trigger */}
                  <div className="flex items-center justify-between">
                    <span
                      className={`inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-bold border shadow-2xs ${badge.bg}`}
                    >
                      <span className={`w-1.5 h-1.5 rounded-full ${badge.ring} animate-pulse`} />
                      <span>{badge.label}</span>
                    </span>

                    <button
                      type="button"
                      onClick={(e) => handleToggleSave(e, job)}
                      disabled={savingJobId === job.id}
                      className={`p-2 rounded-xl border transition-all ${
                        isSaved
                          ? "bg-blue-50 border-blue-200 text-blue-600 shadow-xs"
                          : "bg-white border-slate-200 text-slate-400 hover:text-blue-600 hover:border-slate-300"
                      }`}
                      title={isSaved ? "Remove from Saved Jobs" : "Save Job (1-Click Bookmark)"}
                      aria-label={isSaved ? "Unsave job" : "Save job"}
                    >
                      <Bookmark
                        className={`w-4 h-4 transition-transform group-hover:scale-105 ${
                          isSaved ? "fill-blue-600 text-blue-600" : ""
                        }`}
                      />
                    </button>
                  </div>

                  {/* Company Branding & Title */}
                  <div className="space-y-2">
                    <div className="flex items-center space-x-3">
                      <div className="w-10 h-10 rounded-xl bg-slate-50 border border-slate-100 flex items-center justify-center flex-shrink-0 overflow-hidden text-navy-950 font-bold text-xs shadow-2xs">
                        {job.company_logo_url ? (
                          <img
                            src={job.company_logo_url}
                            alt={job.company_name}
                            className="w-full h-full object-cover"
                          />
                        ) : (
                          <Building2 className="w-5 h-5 text-slate-400" />
                        )}
                      </div>
                      <div className="min-w-0">
                        <div className="flex items-center space-x-1.5">
                          <p className="text-xs font-bold text-slate-700 truncate">
                            {job.company_name}
                          </p>
                          <ShieldCheck className="w-3.5 h-3.5 text-blue-600 flex-shrink-0" title="Verified Company" />
                        </div>
                        <div className="flex items-center space-x-2 text-[11px] text-slate-500 font-medium mt-0.5">
                          <span className="truncate">{job.location}</span>
                          <span>•</span>
                          <span className="capitalize">{job.work_mode}</span>
                        </div>
                      </div>
                    </div>

                    <Link
                      to={`/jobs/${job.id}`}
                      className="block text-base font-extrabold text-navy-950 hover:text-blue-600 transition-colors font-heading line-clamp-1 mt-1"
                    >
                      {job.title}
                    </Link>

                    {/* Compensation Tag */}
                    <p className="text-xs font-bold text-slate-800">
                      {job.compensation}
                    </p>
                  </div>

                  {/* Skills Match Highlights */}
                  <div className="space-y-2 pt-2 border-t border-slate-100">
                    <div className="flex items-center justify-between text-[11px] font-semibold text-slate-500">
                      <span>Matching Competencies</span>
                      <span className="text-emerald-600 font-bold">
                        {matchedSkillsList.length} skills matched
                      </span>
                    </div>

                    <div className="flex flex-wrap gap-1.5 min-h-[30px]">
                      {matchedSkillsList.length > 0 ? (
                        matchedSkillsList.slice(0, 3).map((skill, idx) => (
                          <span
                            key={idx}
                            className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-lg text-[11px] font-bold bg-emerald-50 text-emerald-800 border border-emerald-100"
                          >
                            <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                            <span>{skill}</span>
                          </span>
                        ))
                      ) : (
                        <span className="text-[11px] text-slate-400 italic">
                          Aligned with {job.category}
                        </span>
                      )}
                      {matchedSkillsList.length > 3 && (
                        <span className="px-2 py-0.5 rounded-lg text-[10px] font-bold bg-slate-100 text-slate-600">
                          +{matchedSkillsList.length - 3} more
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Recommendation Reason note */}
                  {job.recommendation_reason && (
                    <p className="text-[11px] text-slate-500 italic bg-slate-50/80 rounded-lg p-2 border border-slate-100 line-clamp-2">
                      💡 {job.recommendation_reason}
                    </p>
                  )}

                  {/* Bottom Action */}
                  <div className="pt-2 flex items-center justify-between gap-3">
                    <Link
                      to={`/jobs/${job.id}`}
                      className="w-full py-2.5 px-4 rounded-xl text-xs font-bold bg-navy-950 hover:bg-navy-900 text-white shadow-xs transition-all text-center flex items-center justify-center space-x-2"
                    >
                      <span>View & Apply</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </Link>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

export default RecommendedJobsCarousel;
