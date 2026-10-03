import React, { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import companyService from "../../services/companyService";
import { ROUTES } from "../../constants";
import {
  Building2,
  CheckCircle2,
  MapPin,
  Globe,
  Users,
  Briefcase,
  ExternalLink,
  ArrowLeft,
  Calendar,
  AlertCircle,
  Bell,
  Sparkles,
} from "lucide-react";

// Social Media SVGs
const LinkedinIcon = ({ className = "w-4 h-4 text-blue-600" }) => (
  <svg className={className} fill="currentColor" viewBox="0 0 24 24">
    <path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z" />
  </svg>
);

const GithubIcon = ({ className = "w-4 h-4 text-slate-800" }) => (
  <svg className={className} fill="currentColor" viewBox="0 0 24 24">
    <path fillRule="evenodd" clipRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" />
  </svg>
);

const FacebookIcon = ({ className = "w-4 h-4 text-blue-700" }) => (
  <svg className={className} fill="currentColor" viewBox="0 0 24 24">
    <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z" />
  </svg>
);

const TwitterIcon = ({ className = "w-4 h-4 text-sky-500" }) => (
  <svg className={className} fill="currentColor" viewBox="0 0 24 24">
    <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
  </svg>
);

export const CompanyPublicProfile = () => {
  const { id } = useParams();
  const [company, setCompany] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [subscribed, setSubscribed] = useState(false);

  useEffect(() => {
    const fetchPublicData = async () => {
      try {
        setLoading(true);
        setError(null);
        const res = await companyService.getPublicProfile(id);
        if (res.success && res.data) {
          setCompany(res.data);
        }
      } catch (err) {
        console.error("Public profile load error:", err);
        setError(err.response?.data?.message || "Company profile not found or unavailable.");
      } finally {
        setLoading(false);
      }
    };

    if (id) {
      fetchPublicData();
    }
  }, [id]);

  const getCompanyInitials = (name) => {
    if (!name) return "CO";
    const words = name.trim().split(/\s+/);
    if (words.length >= 2) {
      return (words[0][0] + words[1][0]).toUpperCase();
    }
    return name.slice(0, 2).toUpperCase();
  };

  if (loading) {
    return (
      <div className="min-h-[70vh] flex flex-col items-center justify-center space-y-4">
        <div className="w-12 h-12 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin"></div>
        <p className="text-sm font-semibold text-slate-600">Loading Company Details...</p>
      </div>
    );
  }

  if (error || !company) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-16 text-center space-y-5">
        <div className="w-16 h-16 rounded-2xl bg-red-50 text-red-600 flex items-center justify-center mx-auto shadow-xs">
          <AlertCircle className="w-8 h-8" />
        </div>
        <h2 className="text-2xl font-black text-navy-950 font-heading">
          Company Profile Unavailable
        </h2>
        <p className="text-sm text-slate-600 max-w-md mx-auto">
          {error || "The requested company profile does not exist or has been removed."}
        </p>
        <div className="pt-2">
          <Link
            to={ROUTES.HOME}
            className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-navy-950 text-white font-bold text-xs shadow hover:bg-navy-900 transition-colors"
          >
            <ArrowLeft className="w-4 h-4 mr-1" />
            <span>Return to Home</span>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50/50 pb-16">
      {/* Top Breadcrumb Navigation */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-6">
        <Link
          to={ROUTES.JOBS}
          className="inline-flex items-center space-x-1.5 text-xs font-semibold text-slate-500 hover:text-navy-950 transition-colors mb-4"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Jobs & Companies</span>
        </Link>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8">
        {/* Company Header & Branding Card */}
        <div className="bg-white rounded-3xl border border-slate-200 overflow-hidden shadow-sm">
          {/* Cover Banner */}
          <div className="h-44 sm:h-64 w-full bg-gradient-to-r from-navy-950 via-slate-900 to-blue-950 relative overflow-hidden">
            {company.banner_url ? (
              <img
                src={company.banner_url}
                alt="Company Cover Banner"
                className="w-full h-full object-cover"
              />
            ) : (
              <div className="absolute inset-0 opacity-25 bg-[radial-gradient(#38bdf8_1px,transparent_1px)] [background-size:20px_20px]"></div>
            )}
          </div>

          {/* Profile Header Details */}
          <div className="p-6 sm:p-10 pt-0 relative">
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 -mt-16 sm:-mt-20 mb-6">
              {/* Logo & Company Identification */}
              <div className="flex flex-col sm:flex-row sm:items-end space-y-4 sm:space-y-0 sm:space-x-6">
                <div className="w-28 h-28 sm:w-32 sm:h-32 rounded-3xl bg-white border-4 border-white shadow-xl overflow-hidden flex items-center justify-center flex-shrink-0">
                  {company.logo_url ? (
                    <img
                      src={company.logo_url}
                      alt={company.company_name}
                      className="w-full h-full object-contain p-2"
                    />
                  ) : (
                    <div className="w-full h-full bg-gradient-to-br from-navy-900 to-blue-900 flex flex-col items-center justify-center text-white">
                      <span className="text-3xl font-black font-heading tracking-wider">
                        {getCompanyInitials(company.company_name)}
                      </span>
                    </div>
                  )}
                </div>

                <div className="space-y-1.5">
                  <div className="flex items-center flex-wrap gap-2.5">
                    <h1 className="text-2xl sm:text-3xl font-black text-navy-950 font-heading">
                      {company.company_name}
                    </h1>
                    {company.is_verified ? (
                      <span className="inline-flex items-center space-x-1 px-3 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 border border-emerald-200 shadow-2xs">
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                        <span>Verified Company</span>
                      </span>
                    ) : (
                      <span className="inline-flex items-center space-x-1 px-3 py-1 rounded-full text-xs font-bold bg-amber-100 text-amber-800 border border-amber-200">
                        <span>Under Review</span>
                      </span>
                    )}
                  </div>

                  {company.tagline && (
                    <p className="text-sm sm:text-base font-medium text-slate-600">
                      {company.tagline}
                    </p>
                  )}

                  {/* Metadata Tags */}
                  <div className="flex flex-wrap items-center gap-3 pt-2 text-xs font-medium text-slate-500">
                    {company.industry && (
                      <span className="inline-flex items-center bg-slate-100 text-slate-700 px-2.5 py-1 rounded-lg">
                        <Building2 className="w-3.5 h-3.5 mr-1.5 text-slate-400" />
                        {company.industry}
                      </span>
                    )}
                    {company.location && (
                      <span className="inline-flex items-center bg-slate-100 text-slate-700 px-2.5 py-1 rounded-lg">
                        <MapPin className="w-3.5 h-3.5 mr-1.5 text-slate-400" />
                        {company.location}
                      </span>
                    )}
                    {company.company_size && (
                      <span className="inline-flex items-center bg-slate-100 text-slate-700 px-2.5 py-1 rounded-lg">
                        <Users className="w-3.5 h-3.5 mr-1.5 text-slate-400" />
                        {company.company_size} Employees
                      </span>
                    )}
                  </div>
                </div>
              </div>

              {/* Follow / Subscribe Action */}
              <div className="flex items-center space-x-3 self-start md:self-end">
                <button
                  onClick={() => setSubscribed(!subscribed)}
                  className={`inline-flex items-center space-x-1.5 px-4 py-2.5 rounded-xl text-xs font-bold transition-all shadow-xs ${
                    subscribed
                      ? "bg-emerald-50 text-emerald-700 border border-emerald-300"
                      : "bg-navy-950 text-white hover:bg-navy-900"
                  }`}
                >
                  <Bell className="w-3.5 h-3.5" />
                  <span>{subscribed ? "Following Updates" : "Follow Company"}</span>
                </button>
              </div>
            </div>

            {/* Social Links & Web Links */}
            <div className="pt-4 border-t border-slate-100 flex flex-wrap items-center justify-between gap-4">
              <div className="flex items-center space-x-3">
                {company.website_url && (
                  <a
                    href={company.website_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-blue-50 text-blue-700 hover:bg-blue-100 text-xs font-semibold transition-colors"
                  >
                    <Globe className="w-3.5 h-3.5 text-blue-600" />
                    <span>Visit Official Website</span>
                    <ExternalLink className="w-3 h-3 ml-0.5 opacity-60" />
                  </a>
                )}

                {company.social_links?.linkedin && (
                  <a
                    href={company.social_links.linkedin}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="p-2 rounded-lg bg-slate-100 hover:bg-slate-200 transition-colors text-slate-700"
                    title="LinkedIn"
                  >
                    <LinkedinIcon className="w-4 h-4" />
                  </a>
                )}
                {company.social_links?.github && (
                  <a
                    href={company.social_links.github}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="p-2 rounded-lg bg-slate-100 hover:bg-slate-200 transition-colors text-slate-700"
                    title="GitHub"
                  >
                    <GithubIcon className="w-4 h-4" />
                  </a>
                )}
                {company.social_links?.facebook && (
                  <a
                    href={company.social_links.facebook}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="p-2 rounded-lg bg-slate-100 hover:bg-slate-200 transition-colors text-slate-700"
                    title="Facebook"
                  >
                    <FacebookIcon className="w-4 h-4" />
                  </a>
                )}
                {company.social_links?.twitter && (
                  <a
                    href={company.social_links.twitter}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="p-2 rounded-lg bg-slate-100 hover:bg-slate-200 transition-colors text-slate-700"
                    title="Twitter / X"
                  >
                    <TwitterIcon className="w-4 h-4" />
                  </a>
                )}
              </div>

              <div className="flex items-center space-x-2 text-xs font-semibold text-slate-400">
                <Calendar className="w-3.5 h-3.5" />
                <span>On Platform Since {new Date(company.created_at).toLocaleDateString()}</span>
              </div>
            </div>
          </div>
        </div>

        {/* 2-Column Content: About & Vacancies */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Column: About & Mission */}
          <div className="lg:col-span-2 space-y-6">
            <div className="bg-white rounded-3xl border border-slate-200 p-6 sm:p-8 shadow-sm space-y-4">
              <h3 className="text-lg font-bold text-navy-950 font-heading flex items-center space-x-2">
                <Building2 className="w-5 h-5 text-emerald-600" />
                <span>About {company.company_name}</span>
              </h3>

              {company.description ? (
                <div className="text-sm text-slate-700 leading-relaxed whitespace-pre-line">
                  {company.description}
                </div>
              ) : (
                <p className="text-sm text-slate-400 italic">
                  No company overview has been added yet.
                </p>
              )}
            </div>
          </div>

          {/* Sidebar: Active Vacancies & Quick Info */}
          <div className="space-y-6">
            <div className="bg-white rounded-3xl border border-slate-200 p-6 sm:p-7 shadow-sm space-y-4">
              <div className="flex items-center justify-between">
                <h4 className="text-base font-bold text-navy-950 font-heading flex items-center space-x-2">
                  <Briefcase className="w-4 h-4 text-emerald-600" />
                  <span>Active Vacancies</span>
                </h4>
                <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-slate-100 text-slate-600">
                  {company.active_jobs?.length || 0} Open
                </span>
              </div>

              {/* Sprint 1 Placeholder: Empty State ready for Sprint 3 */}
              <div className="p-6 rounded-2xl bg-slate-50 border border-slate-200 text-center space-y-3">
                <div className="w-10 h-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center mx-auto">
                  <Sparkles className="w-5 h-5" />
                </div>
                <div className="space-y-1">
                  <h5 className="text-xs font-bold text-navy-950 uppercase tracking-wider">
                    Sprint 3 Placement Active
                  </h5>
                  <p className="text-xs text-slate-500 leading-relaxed">
                    No active job vacancies open right now. Follow this company to receive instant notifications when new technical roles are posted.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CompanyPublicProfile;
