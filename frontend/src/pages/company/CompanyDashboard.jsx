import React, { useState, useEffect, useRef } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../../hooks/useAuth";
import companyService from "../../services/companyService";
import Button from "../../components/forms/Button";
import Input from "../../components/forms/Input";
import { ROUTES } from "../../constants";
import {
  Building2,
  CheckCircle2,
  AlertCircle,
  MapPin,
  Globe,
  Users,
  Briefcase,
  FileText,
  Calendar,
  UserCheck,
  Edit3,
  ExternalLink,
  Plus,
  UploadCloud,
  X,
  RefreshCw,
  Sparkles,
  Phone,
  User,
  ShieldCheck,
  Clock,
  Eye,
  Camera,
  Image as ImageIcon,
} from "lucide-react";

// Brand Social Media SVGs
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

export const CompanyDashboard = () => {
  const { user } = useAuth();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);

  // Edit Modal State
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isActionModalOpen, setIsActionModalOpen] = useState(null); // 'job' | 'candidates' | 'interviews'
  const [isSaving, setIsSaving] = useState(false);
  const [modalTab, setModalTab] = useState("general"); // 'general' | 'assets' | 'social'

  // Form Fields
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
    social_links: {
      linkedin: "",
      facebook: "",
      twitter: "",
      github: "",
    },
  });

  // Asset upload states
  const [logoFile, setLogoFile] = useState(null);
  const [logoPreview, setLogoPreview] = useState(null);
  const [bannerFile, setBannerFile] = useState(null);
  const [bannerPreview, setBannerPreview] = useState(null);
  const [uploadingLogo, setUploadingLogo] = useState(false);
  const [uploadingBanner, setUploadingBanner] = useState(false);
  const [assetError, setAssetError] = useState(null);

  const logoInputRef = useRef(null);
  const bannerInputRef = useRef(null);

  const fetchCompanyProfile = async (silent = false) => {
    try {
      if (!silent) setLoading(true);
      else setRefreshing(true);
      setError(null);

      const res = await companyService.getProfile();
      if (res.success && res.data) {
        setProfile(res.data);
        setFormData({
          company_name: res.data.company_name || "",
          tagline: res.data.tagline || "",
          description: res.data.description || "",
          industry: res.data.industry || "",
          company_size: res.data.company_size || "",
          contact_person: res.data.contact_person || "",
          contact_phone: res.data.contact_phone || "",
          website_url: res.data.website_url || "",
          office_address: res.data.office_address || "",
          social_links: {
            linkedin: res.data.social_links?.linkedin || "",
            facebook: res.data.social_links?.facebook || "",
            twitter: res.data.social_links?.twitter || "",
            github: res.data.social_links?.github || "",
          },
        });
      }
    } catch (err) {
      console.error("Failed to load company profile:", err);
      setError(err.response?.data?.message || "Failed to load company profile. Please try again.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchCompanyProfile();
  }, []);

  // Compute initials avatar (e.g. BS for Brain Station 23)
  const getCompanyInitials = (name) => {
    if (!name) return "CO";
    const words = name.trim().split(/\s+/);
    if (words.length >= 2) {
      return (words[0][0] + words[1][0]).toUpperCase();
    }
    return name.slice(0, 2).toUpperCase();
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    if (name.startsWith("social_")) {
      const platform = name.replace("social_", "");
      setFormData((prev) => ({
        ...prev,
        social_links: {
          ...prev.social_links,
          [platform]: value,
        },
      }));
    } else {
      setFormData((prev) => ({
        ...prev,
        [name]: value,
      }));
    }
  };

  const handleSaveProfile = async (e) => {
    e.preventDefault();
    try {
      setIsSaving(true);
      setError(null);

      const payload = {
        company_name: formData.company_name.trim(),
        tagline: formData.tagline.trim() || null,
        description: formData.description.trim() || null,
        industry: formData.industry.trim() || null,
        company_size: formData.company_size || null,
        contact_person: formData.contact_person.trim() || null,
        contact_phone: formData.contact_phone.trim() || null,
        website_url: formData.website_url.trim() || null,
        office_address: formData.office_address.trim() || null,
        social_links: {
          linkedin: formData.social_links.linkedin.trim() || null,
          facebook: formData.social_links.facebook.trim() || null,
          twitter: formData.social_links.twitter.trim() || null,
          github: formData.social_links.github.trim() || null,
        },
      };

      const res = await companyService.updateProfile(payload);
      if (res.success && res.data) {
        setProfile(res.data);
        setSuccessMessage("Company profile updated successfully!");
        setIsEditModalOpen(false);
        setTimeout(() => setSuccessMessage(null), 4000);
      }
    } catch (err) {
      console.error("Update profile error:", err);
      const msg = err.response?.data?.message || "Failed to update profile. Please verify all inputs.";
      setError(msg);
    } finally {
      setIsSaving(false);
    }
  };

  // Asset Upload Handlers
  const handleLogoSelect = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const validTypes = ["image/png", "image/jpeg", "image/webp"];
    if (!validTypes.includes(file.type)) {
      setAssetError("Logo must be in PNG, JPG, or WEBP image format.");
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      setAssetError("Logo file size exceeds maximum allowable limit of 5MB.");
      return;
    }

    setAssetError(null);
    setLogoFile(file);
    setLogoPreview(URL.createObjectURL(file));
  };

  const handleBannerSelect = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const validTypes = ["image/png", "image/jpeg", "image/webp"];
    if (!validTypes.includes(file.type)) {
      setAssetError("Cover banner must be in PNG, JPG, or WEBP image format.");
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      setAssetError("Cover banner file size exceeds maximum allowable limit of 5MB.");
      return;
    }

    setAssetError(null);
    setBannerFile(file);
    setBannerPreview(URL.createObjectURL(file));
  };

  const handleUploadLogo = async () => {
    if (!logoFile) return;
    try {
      setUploadingLogo(true);
      setAssetError(null);
      const res = await companyService.uploadLogo(logoFile);
      if (res.success && res.data) {
        setProfile((prev) => ({ ...prev, logo_url: res.data.asset_url }));
        setSuccessMessage("Company logo uploaded and updated successfully!");
        setLogoFile(null);
        setTimeout(() => setSuccessMessage(null), 4000);
      }
    } catch (err) {
      console.error("Logo upload error:", err);
      setAssetError(err.response?.data?.message || "Failed to upload logo.");
    } finally {
      setUploadingLogo(false);
    }
  };

  const handleUploadBanner = async () => {
    if (!bannerFile) return;
    try {
      setUploadingBanner(true);
      setAssetError(null);
      const res = await companyService.uploadBanner(bannerFile);
      if (res.success && res.data) {
        setProfile((prev) => ({ ...prev, banner_url: res.data.asset_url }));
        setSuccessMessage("Company cover banner uploaded and updated successfully!");
        setBannerFile(null);
        setTimeout(() => setSuccessMessage(null), 4000);
      }
    } catch (err) {
      console.error("Banner upload error:", err);
      setAssetError(err.response?.data?.message || "Failed to upload cover banner.");
    } finally {
      setUploadingBanner(false);
    }
  };

  const isVerified = profile?.is_verified || profile?.verification_status === "APPROVED";

  if (loading) {
    return (
      <div className="min-h-[70vh] flex flex-col items-center justify-center space-y-4">
        <div className="w-12 h-12 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin"></div>
        <p className="text-sm font-semibold text-slate-600">Loading Company Dashboard...</p>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Toast Alert Messages */}
      {successMessage && (
        <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-sm flex items-center justify-between shadow-sm animate-fade-in">
          <div className="flex items-center space-x-2.5">
            <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0" />
            <span className="font-medium">{successMessage}</span>
          </div>
          <button onClick={() => setSuccessMessage(null)} className="text-emerald-700 hover:text-emerald-900">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {error && (
        <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-red-800 text-sm flex items-center justify-between shadow-sm">
          <div className="flex items-center space-x-2.5">
            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0" />
            <span className="font-medium">{error}</span>
          </div>
          <button onClick={() => setError(null)} className="text-red-700 hover:text-red-900">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* 1. Header matching UI Specification */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-6">
        <div className="space-y-1">
          <div className="flex items-center flex-wrap gap-2.5">
            <h1 className="text-2xl sm:text-3xl font-extrabold text-navy-950 font-heading">
              Welcome, {profile?.company_name || user?.first_name || "Company"}
            </h1>
            {isVerified ? (
              <span className="inline-flex items-center space-x-1 px-3 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 border border-emerald-200 shadow-xs">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                <span>Verified Company</span>
              </span>
            ) : (
              <span className="inline-flex items-center space-x-1 px-3 py-1 rounded-full text-xs font-bold bg-amber-100 text-amber-800 border border-amber-200 shadow-xs">
                <Clock className="w-3.5 h-3.5 text-amber-600" />
                <span>Verification Pending</span>
              </span>
            )}
          </div>
          <p className="text-sm text-slate-500">
            Corporate Recruitment, Talent Pipeline & Brand Identity Console
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={() => fetchCompanyProfile(true)}
            disabled={refreshing}
            className="inline-flex items-center space-x-1.5 px-3 py-2 rounded-lg text-xs font-semibold text-slate-600 bg-white border border-slate-200 hover:bg-slate-50 transition-colors shadow-2xs"
            title="Refresh dashboard data"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? "animate-spin text-emerald-600" : ""}`} />
            <span className="hidden sm:inline">Refresh</span>
          </button>

          {profile?.id && (
            <Link
              to={`/companies/${profile.id}`}
              className="inline-flex items-center space-x-1.5 px-3.5 py-2 rounded-lg text-xs font-semibold text-navy-900 bg-slate-100 hover:bg-slate-200 transition-colors border border-slate-200"
            >
              <Eye className="w-3.5 h-3.5 text-navy-700" />
              <span>Public View</span>
            </Link>
          )}

          <Button
            variant="primary"
            size="sm"
            onClick={() => setIsEditModalOpen(true)}
            className="inline-flex items-center space-x-1.5"
          >
            <Edit3 className="w-3.5 h-3.5 mr-1" />
            <span>Edit Profile</span>
          </Button>
        </div>
      </div>

      {/* 2. Verification Alert Banner (Muktadir Gatekeeper Requirement) */}
      {!isVerified && (
        <div className="rounded-2xl bg-gradient-to-r from-amber-500/10 via-amber-50 to-orange-50 border border-amber-300 p-5 sm:p-6 shadow-sm">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div className="flex items-start space-x-3.5">
              <div className="w-10 h-10 rounded-xl bg-amber-500/20 border border-amber-400/40 flex items-center justify-center flex-shrink-0 text-amber-700">
                <ShieldCheck className="w-5 h-5 text-amber-600" />
              </div>
              <div className="space-y-1">
                <h3 className="text-sm font-bold text-amber-950 font-heading">
                  Administrative Account Verification In Progress
                </h3>
                <p className="text-xs sm:text-sm text-amber-900/90 leading-relaxed max-w-3xl">
                  Your company account is currently pending administrative verification. Job and internship publishing is disabled until verified by platform administration.
                </p>
                <div className="flex items-center space-x-3 pt-1 text-xs text-amber-800">
                  <span>Status: <strong className="font-semibold uppercase">{profile?.verification_status || "PENDING"}</strong></span>
                  <span>·</span>
                  <span>Registered: {profile?.created_at ? new Date(profile.created_at).toLocaleDateString() : "Active"}</span>
                </div>
              </div>
            </div>
            <button
              onClick={() => setIsEditModalOpen(true)}
              className="px-4 py-2 rounded-lg text-xs font-bold text-amber-900 bg-amber-200/80 hover:bg-amber-200 border border-amber-300/80 transition-all flex-shrink-0"
            >
              Verify Company Details
            </button>
          </div>
        </div>
      )}

      {/* 3. Quick Profile Card matching `Company Dashboard.png` */}
      <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm hover:shadow-md transition-shadow">
        {/* Banner Strip (if banner_url exists, render it; otherwise modern gradient) */}
        <div className="h-32 sm:h-44 w-full bg-gradient-to-r from-navy-950 via-slate-900 to-blue-950 relative overflow-hidden">
          {profile?.banner_url ? (
            <img
              src={profile.banner_url}
              alt="Company Cover Banner"
              className="w-full h-full object-cover"
            />
          ) : (
            <div className="absolute inset-0 opacity-20 bg-[radial-gradient(#38bdf8_1px,transparent_1px)] [background-size:16px_16px]"></div>
          )}
          <div className="absolute top-3 right-3">
            <button
              onClick={() => {
                setModalTab("assets");
                setIsEditModalOpen(true);
              }}
              className="px-2.5 py-1.5 rounded-lg bg-black/40 hover:bg-black/60 backdrop-blur-xs text-white text-xs font-semibold flex items-center space-x-1.5 transition-colors"
            >
              <Camera className="w-3.5 h-3.5" />
              <span>Change Cover</span>
            </button>
          </div>
        </div>

        {/* Profile Card Body */}
        <div className="p-6 sm:p-8 pt-0 relative">
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 -mt-12 sm:-mt-16 mb-6">
            {/* Logo Initial Avatar / Image */}
            <div className="flex flex-col sm:flex-row sm:items-end space-y-3 sm:space-y-0 sm:space-x-5">
              <div className="relative group">
                <div className="w-24 h-24 sm:w-28 sm:h-28 rounded-2xl bg-white border-4 border-white shadow-md overflow-hidden flex items-center justify-center">
                  {profile?.logo_url ? (
                    <img
                      src={profile.logo_url}
                      alt={profile.company_name}
                      className="w-full h-full object-contain p-2"
                    />
                  ) : (
                    <div className="w-full h-full bg-gradient-to-br from-navy-900 to-blue-900 flex flex-col items-center justify-center text-white">
                      <span className="text-2xl sm:text-3xl font-black font-heading tracking-wider">
                        {getCompanyInitials(profile?.company_name)}
                      </span>
                    </div>
                  )}
                </div>
                <button
                  onClick={() => {
                    setModalTab("assets");
                    setIsEditModalOpen(true);
                  }}
                  className="absolute bottom-1 right-1 w-7 h-7 rounded-full bg-navy-950 text-white flex items-center justify-center shadow hover:bg-blue-600 transition-colors"
                  title="Upload brand logo"
                >
                  <Camera className="w-3.5 h-3.5" />
                </button>
              </div>

              <div className="space-y-1">
                <div className="flex items-center space-x-2">
                  <h2 className="text-xl sm:text-2xl font-black text-navy-950 font-heading">
                    {profile?.company_name}
                  </h2>
                  {isVerified && (
                    <CheckCircle2 className="w-5 h-5 text-emerald-500 flex-shrink-0" title="Verified Organization" />
                  )}
                </div>
                {profile?.tagline && (
                  <p className="text-sm font-medium text-slate-600 italic">
                    "{profile.tagline}"
                  </p>
                )}
                <div className="flex flex-wrap items-center gap-3 pt-1 text-xs text-slate-500">
                  {profile?.industry && (
                    <span className="inline-flex items-center">
                      <Building2 className="w-3.5 h-3.5 mr-1 text-slate-400" />
                      {profile.industry}
                    </span>
                  )}
                  {profile?.office_address && (
                    <span className="inline-flex items-center">
                      <MapPin className="w-3.5 h-3.5 mr-1 text-slate-400" />
                      {profile.office_address}
                    </span>
                  )}
                  {profile?.company_size && (
                    <span className="inline-flex items-center">
                      <Users className="w-3.5 h-3.5 mr-1 text-slate-400" />
                      {profile.company_size} Employees
                    </span>
                  )}
                </div>
              </div>
            </div>

            {/* Quick Action in Profile Card Header */}
            <div className="flex items-center space-x-3 self-start md:self-end">
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setModalTab("general");
                  setIsEditModalOpen(true);
                }}
                className="text-xs font-semibold"
              >
                <Edit3 className="w-3.5 h-3.5 mr-1.5" />
                <span>Edit Profile</span>
              </Button>
            </div>
          </div>

          {/* Social Links & Web Links Bar */}
          <div className="pt-4 border-t border-slate-100 flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center space-x-3">
              {profile?.website_url && (
                <a
                  href={profile.website_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-blue-50 text-blue-700 hover:bg-blue-100 text-xs font-semibold transition-colors"
                >
                  <Globe className="w-3.5 h-3.5 text-blue-600" />
                  <span>{profile.website_url.replace(/^https?:\/\//, "")}</span>
                  <ExternalLink className="w-3 h-3 ml-0.5 opacity-60" />
                </a>
              )}

              {profile?.social_links?.linkedin && (
                <a
                  href={profile.social_links.linkedin}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="p-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 transition-colors text-slate-600"
                  title="LinkedIn Profile"
                >
                  <LinkedinIcon className="w-4 h-4" />
                </a>
              )}
              {profile?.social_links?.github && (
                <a
                  href={profile.social_links.github}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="p-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 transition-colors text-slate-600"
                  title="GitHub Profile"
                >
                  <GithubIcon className="w-4 h-4" />
                </a>
              )}
              {profile?.social_links?.facebook && (
                <a
                  href={profile.social_links.facebook}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="p-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 transition-colors text-slate-600"
                  title="Facebook Page"
                >
                  <FacebookIcon className="w-4 h-4" />
                </a>
              )}
              {profile?.social_links?.twitter && (
                <a
                  href={profile.social_links.twitter}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="p-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 transition-colors text-slate-600"
                  title="Twitter / X Profile"
                >
                  <TwitterIcon className="w-4 h-4" />
                </a>
              )}
            </div>

            <div className="flex items-center space-x-2 text-xs font-semibold text-slate-500">
              <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
              <span>0 Active Job Openings</span>
            </div>
          </div>
        </div>
      </div>

      {/* 4. Stat Counters (Active Jobs, Applications, Shortlisted, Upcoming Interviews) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {/* Stat 1: Active Jobs */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs hover:border-slate-300 transition-colors space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
              Active Jobs
            </span>
            <div className="w-10 h-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center">
              <Briefcase className="w-5 h-5" />
            </div>
          </div>
          <div>
            <div className="text-3xl font-black text-navy-950 font-heading">0</div>
            <p className="text-xs text-slate-500 mt-1">Currently listed vacancies</p>
          </div>
        </div>

        {/* Stat 2: Applications */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs hover:border-slate-300 transition-colors space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
              Applications
            </span>
            <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center">
              <FileText className="w-5 h-5" />
            </div>
          </div>
          <div>
            <div className="text-3xl font-black text-navy-950 font-heading">0</div>
            <p className="text-xs text-slate-500 mt-1">Candidate CVs received</p>
          </div>
        </div>

        {/* Stat 3: Shortlisted */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs hover:border-slate-300 transition-colors space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
              Shortlisted
            </span>
            <div className="w-10 h-10 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center">
              <UserCheck className="w-5 h-5" />
            </div>
          </div>
          <div>
            <div className="text-3xl font-black text-navy-950 font-heading">0</div>
            <p className="text-xs text-slate-500 mt-1">Screened for next rounds</p>
          </div>
        </div>

        {/* Stat 4: Upcoming Interviews */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs hover:border-slate-300 transition-colors space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
              Upcoming Interviews
            </span>
            <div className="w-10 h-10 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center">
              <Calendar className="w-5 h-5" />
            </div>
          </div>
          <div>
            <div className="text-3xl font-black text-navy-950 font-heading">0</div>
            <p className="text-xs text-slate-500 mt-1">Scheduled candidate rounds</p>
          </div>
        </div>
      </div>

      {/* 5. Bottom Quick Action Buttons: [+ Post Job], [View Candidates], [View Interviews] */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 sm:p-8 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <div className="space-y-0.5">
            <h3 className="text-base font-bold text-navy-950 font-heading">
              Recruitment Quick Actions
            </h3>
            <p className="text-xs text-slate-500">
              Fast-track your corporate hiring and candidate review workflow
            </p>
          </div>
          <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-blue-50 text-blue-700">
            Sprint 1 Active
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2">
          {/* Quick Action 1: + Post Job */}
          <button
            onClick={() => setIsActionModalOpen("job")}
            className="flex items-center justify-center space-x-2 px-6 py-4 rounded-xl bg-gradient-to-r from-emerald-600 to-emerald-500 text-white font-bold text-sm shadow hover:from-emerald-700 hover:to-emerald-600 transition-all hover:shadow-md cursor-pointer"
          >
            <Plus className="w-4 h-4" />
            <span>+ Post Job</span>
          </button>

          {/* Quick Action 2: View Candidates */}
          <button
            onClick={() => setIsActionModalOpen("candidates")}
            className="flex items-center justify-center space-x-2 px-6 py-4 rounded-xl bg-slate-900 text-white font-bold text-sm shadow hover:bg-navy-950 transition-all hover:shadow-md cursor-pointer"
          >
            <Users className="w-4 h-4" />
            <span>View Candidates</span>
          </button>

          {/* Quick Action 3: View Interviews */}
          <button
            onClick={() => setIsActionModalOpen("interviews")}
            className="flex items-center justify-center space-x-2 px-6 py-4 rounded-xl bg-white border border-slate-300 text-navy-900 font-bold text-sm shadow-2xs hover:bg-slate-50 transition-all cursor-pointer"
          >
            <Calendar className="w-4 h-4 text-emerald-600" />
            <span>View Interviews</span>
          </button>
        </div>
      </div>

      {/* 6. Edit Profile Modal (Inline Editing of Tagline, Size, Address, Assets) */}
      {isEditModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-navy-950/60 backdrop-blur-xs animate-fade-in">
          <div className="bg-white rounded-3xl border border-slate-200 w-full max-w-3xl shadow-2xl overflow-hidden max-h-[90vh] flex flex-col">
            {/* Modal Header */}
            <div className="p-6 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 rounded-xl bg-emerald-500/10 text-emerald-600 flex items-center justify-center">
                  <Building2 className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-navy-950 font-heading">
                    Edit Company Profile & Branding
                  </h3>
                  <p className="text-xs text-slate-500">
                    Update company credentials, social identities, and visual assets
                  </p>
                </div>
              </div>
              <button
                onClick={() => setIsEditModalOpen(false)}
                className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Tabs */}
            <div className="flex border-b border-slate-100 px-6 bg-white gap-6 text-xs font-semibold">
              <button
                type="button"
                onClick={() => setModalTab("general")}
                className={`py-3 border-b-2 transition-colors ${
                  modalTab === "general"
                    ? "border-emerald-600 text-emerald-700"
                    : "border-transparent text-slate-500 hover:text-navy-900"
                }`}
              >
                General Details
              </button>
              <button
                type="button"
                onClick={() => setModalTab("assets")}
                className={`py-3 border-b-2 transition-colors ${
                  modalTab === "assets"
                    ? "border-emerald-600 text-emerald-700"
                    : "border-transparent text-slate-500 hover:text-navy-900"
                }`}
              >
                Branding Assets (Logo & Banner)
              </button>
              <button
                type="button"
                onClick={() => setModalTab("social")}
                className={`py-3 border-b-2 transition-colors ${
                  modalTab === "social"
                    ? "border-emerald-600 text-emerald-700"
                    : "border-transparent text-slate-500 hover:text-navy-900"
                }`}
              >
                Social Profiles & Contact
              </button>
            </div>

            {/* Modal Body / Scrollable */}
            <div className="p-6 overflow-y-auto space-y-6 flex-1">
              {assetError && (
                <div className="p-3.5 rounded-xl bg-red-50 border border-red-200 text-red-700 text-xs flex items-center space-x-2">
                  <AlertCircle className="w-4 h-4 flex-shrink-0" />
                  <span>{assetError}</span>
                </div>
              )}

              {/* Tab 1: General Details */}
              {modalTab === "general" && (
                <form id="edit-company-form" onSubmit={handleSaveProfile} className="space-y-4">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <Input
                      label="Company Trade Name"
                      name="company_name"
                      value={formData.company_name}
                      onChange={handleInputChange}
                      placeholder="e.g. Brain Station 23 Limited"
                      required
                    />
                    <Input
                      label="Corporate Tagline"
                      name="tagline"
                      value={formData.tagline}
                      onChange={handleInputChange}
                      placeholder="e.g. Empowering Global Enterprises"
                    />
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs font-semibold text-navy-900 mb-1.5">
                        Industry Domain
                      </label>
                      <select
                        name="industry"
                        value={formData.industry}
                        onChange={handleInputChange}
                        className="w-full px-3.5 py-2.5 rounded-lg border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 bg-white"
                      >
                        <option value="">Select Industry</option>
                        <option value="Software & IT Services">Software & IT Services</option>
                        <option value="Fintech & Banking">Fintech & Banking</option>
                        <option value="Telecommunications">Telecommunications</option>
                        <option value="E-Commerce & Retail">E-Commerce & Retail</option>
                        <option value="Healthcare & BioTech">Healthcare & BioTech</option>
                        <option value="Education & EdTech">Education & EdTech</option>
                        <option value="Manufacturing & Engineering">Manufacturing & Engineering</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-xs font-semibold text-navy-900 mb-1.5">
                        Company Size Range
                      </label>
                      <select
                        name="company_size"
                        value={formData.company_size}
                        onChange={handleInputChange}
                        className="w-full px-3.5 py-2.5 rounded-lg border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 bg-white"
                      >
                        <option value="">Select Company Size</option>
                        <option value="1-10">1-10 Employees (Startup)</option>
                        <option value="11-50">11-50 Employees (Early Stage)</option>
                        <option value="51-200">51-200 Employees (Growing SME)</option>
                        <option value="201-500">201-500 Employees (Mid-Market)</option>
                        <option value="500+">500+ Employees (Enterprise)</option>
                      </select>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <Input
                      label="Official Website URL"
                      name="website_url"
                      value={formData.website_url}
                      onChange={handleInputChange}
                      placeholder="https://example.com"
                    />
                    <Input
                      label="Headquarters Office Address"
                      name="office_address"
                      value={formData.office_address}
                      onChange={handleInputChange}
                      placeholder="Plot 2, Mirpur 14, Dhaka 1206"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-navy-900 mb-1.5">
                      Company Overview & Mission
                    </label>
                    <textarea
                      name="description"
                      rows={4}
                      value={formData.description}
                      onChange={handleInputChange}
                      placeholder="Describe your organization, engineering focus, work culture, and key milestones..."
                      className="w-full px-3.5 py-2.5 rounded-lg border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
                    />
                  </div>
                </form>
              )}

              {/* Tab 2: Assets (Logo & Banner) */}
              {modalTab === "assets" && (
                <div className="space-y-6">
                  {/* Logo Upload Section */}
                  <div className="p-5 rounded-2xl border border-slate-200 bg-slate-50/50 space-y-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <h4 className="text-sm font-bold text-navy-950 font-heading">
                          Company Logo Asset
                        </h4>
                        <p className="text-xs text-slate-500">
                          Square brand logo (PNG, JPG, or WEBP, max 5MB)
                        </p>
                      </div>
                      {profile?.logo_url && (
                        <span className="text-[11px] font-semibold text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded-full">
                          Logo Active
                        </span>
                      )}
                    </div>

                    <div className="flex flex-col sm:flex-row items-center gap-5">
                      <div className="w-20 h-20 rounded-2xl bg-white border-2 border-dashed border-slate-300 overflow-hidden flex items-center justify-center flex-shrink-0 shadow-2xs">
                        {logoPreview ? (
                          <img src={logoPreview} alt="New Logo Preview" className="w-full h-full object-contain p-1" />
                        ) : profile?.logo_url ? (
                          <img src={profile.logo_url} alt="Current Logo" className="w-full h-full object-contain p-1" />
                        ) : (
                          <Building2 className="w-8 h-8 text-slate-300" />
                        )}
                      </div>

                      <div className="flex-1 space-y-2 text-center sm:text-left">
                        <input
                          type="file"
                          ref={logoInputRef}
                          onChange={handleLogoSelect}
                          accept="image/png,image/jpeg,image/webp"
                          className="hidden"
                        />
                        <div className="flex flex-wrap items-center gap-2 justify-center sm:justify-start">
                          <button
                            type="button"
                            onClick={() => logoInputRef.current?.click()}
                            className="px-3.5 py-1.5 rounded-lg bg-white border border-slate-300 text-xs font-semibold text-navy-900 hover:bg-slate-50 transition-colors shadow-2xs"
                          >
                            Choose Logo File
                          </button>
                          {logoFile && (
                            <Button
                              variant="primary"
                              size="sm"
                              onClick={handleUploadLogo}
                              loading={uploadingLogo}
                              className="text-xs"
                            >
                              <UploadCloud className="w-3.5 h-3.5 mr-1" />
                              <span>Upload Selected Logo</span>
                            </Button>
                          )}
                        </div>
                        <p className="text-[11px] text-slate-400">
                          {logoFile ? `Selected: ${logoFile.name} (${(logoFile.size / 1024).toFixed(1)} KB)` : "Recommended size 400x400px with transparent background."}
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Banner Upload Section */}
                  <div className="p-5 rounded-2xl border border-slate-200 bg-slate-50/50 space-y-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <h4 className="text-sm font-bold text-navy-950 font-heading">
                          Cover Banner Image
                        </h4>
                        <p className="text-xs text-slate-500">
                          Horizontal corporate banner (PNG, JPG, or WEBP, max 5MB)
                        </p>
                      </div>
                      {profile?.banner_url && (
                        <span className="text-[11px] font-semibold text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded-full">
                          Banner Active
                        </span>
                      )}
                    </div>

                    <div className="space-y-3">
                      <div className="w-full h-32 rounded-xl bg-slate-900 border-2 border-dashed border-slate-300 overflow-hidden flex items-center justify-center relative">
                        {bannerPreview ? (
                          <img src={bannerPreview} alt="New Banner Preview" className="w-full h-full object-cover" />
                        ) : profile?.banner_url ? (
                          <img src={profile.banner_url} alt="Current Banner" className="w-full h-full object-cover" />
                        ) : (
                          <div className="text-center p-4">
                            <ImageIcon className="w-8 h-8 text-slate-500 mx-auto mb-1" />
                            <span className="text-xs text-slate-400 font-medium">No cover banner set</span>
                          </div>
                        )}
                      </div>

                      <div className="flex flex-wrap items-center justify-between gap-3">
                        <input
                          type="file"
                          ref={bannerInputRef}
                          onChange={handleBannerSelect}
                          accept="image/png,image/jpeg,image/webp"
                          className="hidden"
                        />
                        <div className="flex items-center space-x-2">
                          <button
                            type="button"
                            onClick={() => bannerInputRef.current?.click()}
                            className="px-3.5 py-1.5 rounded-lg bg-white border border-slate-300 text-xs font-semibold text-navy-900 hover:bg-slate-50 transition-colors shadow-2xs"
                          >
                            Choose Banner File
                          </button>
                          {bannerFile && (
                            <Button
                              variant="primary"
                              size="sm"
                              onClick={handleUploadBanner}
                              loading={uploadingBanner}
                              className="text-xs"
                            >
                              <UploadCloud className="w-3.5 h-3.5 mr-1" />
                              <span>Upload Selected Banner</span>
                            </Button>
                          )}
                        </div>
                        <span className="text-[11px] text-slate-400">
                          {bannerFile ? bannerFile.name : "Recommended: 1200x400px aspect ratio"}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Tab 3: Social & Contact */}
              {modalTab === "social" && (
                <div className="space-y-4">
                  <div className="p-4 rounded-xl bg-blue-50/60 border border-blue-100 text-xs text-blue-900">
                    Validate that your social profile links follow standard URL syntax (e.g., https://linkedin.com/company/...).
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <Input
                      label="Primary Contact Person"
                      name="contact_person"
                      value={formData.contact_person}
                      onChange={handleInputChange}
                      placeholder="e.g. Asif Mahmud"
                    />
                    <Input
                      label="Contact Phone Number"
                      name="contact_phone"
                      value={formData.contact_phone}
                      onChange={handleInputChange}
                      placeholder="+8801700000000"
                    />
                  </div>

                  <div className="space-y-3 pt-2">
                    <h4 className="text-xs font-bold text-navy-900 uppercase tracking-wider">
                      Verified Social Identifiers
                    </h4>

                    <Input
                      label="LinkedIn Profile"
                      name="social_linkedin"
                      value={formData.social_links.linkedin}
                      onChange={handleInputChange}
                      placeholder="https://linkedin.com/company/yourcompany"
                    />
                    <Input
                      label="GitHub Organization"
                      name="social_github"
                      value={formData.social_links.github}
                      onChange={handleInputChange}
                      placeholder="https://github.com/yourcompany"
                    />
                    <Input
                      label="Facebook Page"
                      name="social_facebook"
                      value={formData.social_links.facebook}
                      onChange={handleInputChange}
                      placeholder="https://facebook.com/yourcompany"
                    />
                    <Input
                      label="Twitter / X Profile"
                      name="social_twitter"
                      value={formData.social_links.twitter}
                      onChange={handleInputChange}
                      placeholder="https://x.com/yourcompany"
                    />
                  </div>
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="p-4 sm:p-6 border-t border-slate-100 flex items-center justify-between bg-slate-50/50">
              <button
                type="button"
                onClick={() => setIsEditModalOpen(false)}
                className="px-4 py-2 rounded-lg text-xs font-semibold text-slate-600 hover:text-navy-950 transition-colors"
              >
                Cancel
              </button>

              <div className="flex items-center space-x-2">
                <Button
                  variant="primary"
                  size="md"
                  type="submit"
                  form="edit-company-form"
                  onClick={modalTab !== "general" ? handleSaveProfile : undefined}
                  loading={isSaving}
                  className="text-xs font-bold"
                >
                  Save Profile Changes
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 7. Action Placeholder Modals for [+ Post Job], [View Candidates], [View Interviews] */}
      {isActionModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-navy-950/60 backdrop-blur-xs animate-fade-in">
          <div className="bg-white rounded-3xl border border-slate-200 w-full max-w-md p-6 sm:p-8 shadow-2xl text-center space-y-5">
            <div className="w-14 h-14 rounded-2xl bg-emerald-50 text-emerald-600 flex items-center justify-center mx-auto shadow-xs">
              {isActionModalOpen === "job" && <Briefcase className="w-7 h-7" />}
              {isActionModalOpen === "candidates" && <Users className="w-7 h-7" />}
              {isActionModalOpen === "interviews" && <Calendar className="w-7 h-7" />}
            </div>

            <div className="space-y-1.5">
              <span className="px-3 py-1 rounded-full text-[11px] font-extrabold uppercase tracking-wider bg-blue-50 text-blue-700">
                Sprint 3 Roadmap Integration
              </span>
              <h3 className="text-xl font-extrabold text-navy-950 font-heading">
                {isActionModalOpen === "job" && "Publish Job Opening"}
                {isActionModalOpen === "candidates" && "Candidate Pipeline"}
                {isActionModalOpen === "interviews" && "Interview Schedules"}
              </h3>
              <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
                {isActionModalOpen === "job" && (
                  !isVerified
                    ? "Job posting is locked until your company account passes administrative verification. Please ensure your company details and trade documents are submitted."
                    : "The full multi-stage job publishing engine with AI skill matching will go live in Sprint 3."
                )}
                {isActionModalOpen === "candidates" &&
                  "Browse and shortlist verified learners with dynamic competency scores, portfolio links, and vetted CVs (Sprint 3 Placement Pipeline)."}
                {isActionModalOpen === "interviews" &&
                  "Schedule and coordinate technical assessment rounds with automated candidate invitations (Sprint 3 Placement Pipeline)."}
              </p>
            </div>

            <div className="pt-2">
              <Button
                variant="secondary"
                size="md"
                onClick={() => setIsActionModalOpen(null)}
                className="w-full text-xs font-bold"
              >
                Close Window
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CompanyDashboard;
