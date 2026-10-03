import React, { useState, useEffect, useRef } from "react";
import { useAuth } from "../../hooks/useAuth";
import learnerService from "../../services/learnerService";
import Button from "../../components/forms/Button";
import Input from "../../components/forms/Input";
import {
  User,
  Mail,
  Phone,
  MapPin,
  GraduationCap,
  Briefcase,
  Code2,
  FileText,
  UploadCloud,
  Download,
  Trash2,
  ExternalLink,
  CheckCircle2,
  Circle,
  AlertCircle,
  Sparkles,
  Edit3,
  Plus,
  X,
  FileCheck,
  Check,
  Globe,
  RefreshCw,
} from "lucide-react";

// Standard brand SVG icons
const GithubIcon = ({ className = "w-5 h-5 text-slate-700" }) => (
  <svg className={className} fill="currentColor" viewBox="0 0 24 24">
    <path fillRule="evenodd" clipRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" />
  </svg>
);

const LinkedinIcon = ({ className = "w-5 h-5 text-blue-600" }) => (
  <svg className={className} fill="currentColor" viewBox="0 0 24 24">
    <path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z" />
  </svg>
);

export const LearnerProfile = () => {
  const { user } = useAuth();

  // Profile data & loading states
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [uploadingResume, setUploadingResume] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  const [successMsg, setSuccessMsg] = useState("");

  // Modal edit state
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [editFormData, setEditFormData] = useState({
    phone_number: "",
    location: "",
    bio: "",
    target_role: "",
    primary_track: "",
    institution: "",
    department: "",
    github_url: "",
    linkedin_url: "",
    portfolio_url: "",
    degree: "",
  });

  // Interactive inline skill input
  const [newSkillInput, setNewSkillInput] = useState("");
  const fileInputRef = useRef(null);

  // Popular skills suggestion chips
  const suggestedSkills = [
    "Python",
    "FastAPI",
    "JavaScript",
    "React",
    "Docker",
    "PostgreSQL",
    "TailwindCSS",
    "Git",
    "Node.js",
    "AWS",
    "MySQL",
    "REST APIs",
  ];

  // Fetch learner profile on mount
  const fetchProfile = async () => {
    try {
      setLoading(true);
      setErrorMsg("");
      const res = await learnerService.getProfile();
      if (res && res.data) {
        setProfile(res.data);
      }
    } catch (err) {
      console.error("Failed to fetch learner profile:", err);
      setErrorMsg(
        err.response?.data?.message ||
          "Could not load learner profile. Please check your connection."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProfile();
  }, []);

  // Populate edit modal when opened
  const handleOpenEditModal = () => {
    if (!profile) return;
    const portfolio = profile.portfolio_links || {};
    setEditFormData({
      phone_number: profile.phone_number || "",
      location: profile.location || "",
      bio: profile.bio || "",
      target_role: profile.target_role || "",
      primary_track: profile.primary_track || "",
      institution: profile.institution || "",
      department: profile.department || "",
      github_url: portfolio.github_url || "",
      linkedin_url: portfolio.linkedin_url || "",
      portfolio_url: portfolio.portfolio_url || "",
      degree: portfolio.degree || "",
    });
    setErrorMsg("");
    setSuccessMsg("");
    setIsEditModalOpen(true);
  };

  // Submit edit modal changes
  const handleSaveProfile = async (e) => {
    e.preventDefault();
    try {
      setSaving(true);
      setErrorMsg("");

      const payload = {
        phone_number: editFormData.phone_number,
        location: editFormData.location,
        bio: editFormData.bio,
        target_role: editFormData.target_role,
        primary_track: editFormData.primary_track,
        institution: editFormData.institution,
        department: editFormData.department,
        skills: profile.skills || [],
        portfolio_links: {
          github_url: editFormData.github_url,
          linkedin_url: editFormData.linkedin_url,
          portfolio_url: editFormData.portfolio_url,
          degree: editFormData.degree,
        },
      };

      const res = await learnerService.updateProfile(payload);
      if (res && res.data) {
        setProfile(res.data);
        setSuccessMsg("Profile details updated successfully!");
        setIsEditModalOpen(false);
      }
    } catch (err) {
      console.error("Failed to update profile:", err);
      setErrorMsg(
        err.response?.data?.message || "Failed to update profile details."
      );
    } finally {
      setSaving(false);
    }
  };

  // Interactive inline skill additions
  const handleAddSkill = async (skillToAdd) => {
    const skill = (skillToAdd || newSkillInput).trim();
    if (!skill || !profile) return;

    const currentSkills = profile.skills || [];
    if (
      currentSkills.some(
        (s) => s.toLowerCase() === skill.toLowerCase()
      )
    ) {
      setNewSkillInput("");
      return;
    }

    const updatedSkills = [...currentSkills, skill];
    try {
      const res = await learnerService.updateProfile({
        skills: updatedSkills,
      });
      if (res && res.data) {
        setProfile(res.data);
        setNewSkillInput("");
      }
    } catch (err) {
      console.error("Failed to add skill:", err);
      setErrorMsg(err.response?.data?.message || "Failed to add skill tag.");
    }
  };

  // Interactive skill removal
  const handleRemoveSkill = async (skillToRemove) => {
    if (!profile) return;
    const currentSkills = profile.skills || [];
    const updatedSkills = currentSkills.filter(
      (s) => s.toLowerCase() !== skillToRemove.toLowerCase()
    );

    try {
      const res = await learnerService.updateProfile({
        skills: updatedSkills,
      });
      if (res && res.data) {
        setProfile(res.data);
      }
    } catch (err) {
      console.error("Failed to remove skill:", err);
      setErrorMsg(err.response?.data?.message || "Failed to remove skill tag.");
    }
  };

  // Handle Resume Upload
  const handleFileChange = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Reset input value so same file can be re-uploaded if desired
    e.target.value = "";

    // 5MB validation
    if (file.size > 5 * 1024 * 1024) {
      setErrorMsg("Resume file must not exceed 5MB.");
      return;
    }

    const fileExt = file.name.split(".").pop().toLowerCase();
    if (!["pdf", "docx", "doc"].includes(fileExt)) {
      setErrorMsg("Only PDF (.pdf) and Word documents (.docx, .doc) are allowed.");
      return;
    }

    try {
      setUploadingResume(true);
      setErrorMsg("");
      const res = await learnerService.uploadResume(file);
      if (res) {
        setSuccessMsg("Resume document uploaded and verified successfully!");
        await fetchProfile();
      }
    } catch (err) {
      console.error("Failed to upload resume:", err);
      setErrorMsg(
        err.response?.data?.message ||
          "Failed to upload resume. Ensure file is a valid PDF or DOCX under 5MB."
      );
    } finally {
      setUploadingResume(false);
    }
  };

  // Handle Resume Download
  const handleDownloadResume = async () => {
    try {
      const res = await learnerService.downloadResume();
      const blob = new Blob([res.data], {
        type: res.headers["content-type"] || "application/pdf",
      });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", profile.resume_filename || "resume.pdf");
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Resume download failed:", err);
      setErrorMsg("Could not download resume file.");
    }
  };

  // Handle Resume Deletion
  const handleDeleteResume = async () => {
    if (!window.confirm("Are you sure you want to remove your uploaded resume?")) {
      return;
    }

    try {
      setUploadingResume(true);
      const res = await learnerService.deleteResume();
      if (res && res.data) {
        setProfile(res.data);
        setSuccessMsg("Resume removed successfully.");
      }
    } catch (err) {
      console.error("Failed to delete resume:", err);
      setErrorMsg("Could not delete resume.");
    } finally {
      setUploadingResume(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-[70vh] flex flex-col items-center justify-center space-y-4">
        <div className="w-12 h-12 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin"></div>
        <p className="text-slate-600 text-sm font-medium">Loading learner profile...</p>
      </div>
    );
  }

  const completionPct = profile?.completion_pct ?? 0;
  const breakdown = profile?.completion_breakdown;
  const portfolio = profile?.portfolio_links || {};

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Alert Notifications */}
      {errorMsg && (
        <div className="flex items-center justify-between p-4 bg-crimson-50 border border-crimson-200 rounded-xl text-crimson text-sm">
          <div className="flex items-center space-x-2.5">
            <AlertCircle className="w-5 h-5 flex-shrink-0" />
            <span>{errorMsg}</span>
          </div>
          <button
            onClick={() => setErrorMsg("")}
            className="p-1 hover:bg-crimson-100 rounded-md transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {successMsg && (
        <div className="flex items-center justify-between p-4 bg-emerald-50 border border-emerald-200 rounded-xl text-emerald-800 text-sm">
          <div className="flex items-center space-x-2.5">
            <CheckCircle2 className="w-5 h-5 flex-shrink-0 text-emerald-600" />
            <span>{successMsg}</span>
          </div>
          <button
            onClick={() => setSuccessMsg("")}
            className="p-1 hover:bg-emerald-100 rounded-md transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* TOP HEADER CARD: Profile Identity & Dynamic Completion Score */}
      <div className="bg-white rounded-3xl border border-slate-200 shadow-sm p-6 sm:p-8 relative overflow-hidden">
        {/* Subtle decorative background gradient accent */}
        <div className="absolute top-0 right-0 -mt-10 -mr-10 w-80 h-80 bg-gradient-to-br from-blue-100/50 via-emerald-100/30 to-transparent rounded-full blur-2xl pointer-events-none" />

        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-8 relative z-10">
          {/* Left Avatar & Identity details */}
          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-5">
            {/* Avatar Pill */}
            <div className="relative group">
              <div className="w-24 h-24 sm:w-28 sm:h-28 rounded-2xl bg-gradient-to-tr from-navy-950 via-blue-900 to-indigo-700 flex items-center justify-center text-white text-3xl font-extrabold shadow-md border-4 border-white">
                {profile?.first_name?.charAt(0) || user?.first_name?.charAt(0) || "L"}
                {profile?.last_name?.charAt(0) || user?.last_name?.charAt(0) || ""}
              </div>
              <div
                className="absolute -bottom-1.5 -right-1.5 w-7 h-7 rounded-full bg-emerald-500 border-2 border-white flex items-center justify-center shadow-sm"
                title="Verified Account"
              >
                <Check className="w-4 h-4 text-white stroke-[3]" />
              </div>
            </div>

            {/* Name, Role & Badges */}
            <div className="space-y-1.5">
              <div className="flex flex-wrap items-center gap-2.5">
                <h1 className="text-2xl sm:text-3xl font-extrabold text-navy-950 font-heading tracking-tight">
                  {profile?.first_name} {profile?.last_name}
                </h1>
                <span className="inline-flex items-center space-x-1 px-3 py-1 rounded-full text-xs font-bold bg-blue-50 text-blue-700 border border-blue-200">
                  <Sparkles className="w-3 h-3 text-blue-600" />
                  <span>Learner</span>
                </span>
                <span className="inline-flex items-center space-x-1 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                  <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                  <span>Verified Identity</span>
                </span>
              </div>

              <p className="text-base font-medium text-slate-700">
                {profile?.target_role || "Junior Software Engineer / Developer"}
                {profile?.primary_track && (
                  <span className="text-slate-400 font-normal"> · {profile.primary_track}</span>
                )}
              </p>

              <div className="flex flex-wrap items-center gap-x-5 gap-y-2 text-xs text-slate-500 pt-1">
                <div className="flex items-center space-x-1.5">
                  <Mail className="w-3.5 h-3.5 text-slate-400" />
                  <span>{profile?.email}</span>
                </div>
                {profile?.phone_number && (
                  <div className="flex items-center space-x-1.5">
                    <Phone className="w-3.5 h-3.5 text-slate-400" />
                    <span>{profile.phone_number}</span>
                  </div>
                )}
                {profile?.location && (
                  <div className="flex items-center space-x-1.5">
                    <MapPin className="w-3.5 h-3.5 text-slate-400" />
                    <span>{profile.location}</span>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-3">
            <Button
              variant="outline"
              size="sm"
              onClick={handleOpenEditModal}
              className="flex items-center space-x-1.5 bg-white border-slate-300 hover:bg-slate-50 text-navy-900"
            >
              <Edit3 className="w-4 h-4 text-blue-600" />
              <span>Edit Profile</span>
            </Button>
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={uploadingResume}
              className="inline-flex items-center space-x-1.5 px-4 py-2 rounded-lg text-xs font-semibold bg-navy-950 hover:bg-navy-900 text-white shadow-sm transition-all"
            >
              <UploadCloud className="w-4 h-4 text-emerald-400" />
              <span>{uploadingResume ? "Uploading..." : "Upload CV"}</span>
            </button>
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileChange}
              accept=".pdf,.docx,.doc"
              className="hidden"
            />
          </div>
        </div>

        {/* PROGRESS BAR & DYNAMIC COMPLETION RUBRIC (SKL-51) */}
        <div className="mt-8 pt-6 border-t border-slate-100 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div className="flex items-center space-x-2">
              <span className="text-sm font-bold text-navy-950 font-heading">
                Profile Strength & Verification
              </span>
              <span
                className={`px-2.5 py-0.5 rounded-full text-xs font-extrabold ${
                  completionPct === 100
                    ? "bg-emerald-100 text-emerald-800"
                    : completionPct >= 75
                    ? "bg-blue-100 text-blue-800"
                    : "bg-amber-100 text-amber-800"
                }`}
              >
                {completionPct}% Complete
              </span>
            </div>
            <p className="text-xs text-slate-500">
              {completionPct === 100
                ? "Excellent! Your profile is 100% complete and ready for employer shortlisting."
                : "Complete all 4 sections to maximize your ranking in recruiter searches."}
            </p>
          </div>

          {/* Progress bar line */}
          <div className="w-full bg-slate-100 rounded-full h-3 overflow-hidden p-0.5">
            <div
              className={`h-full rounded-full transition-all duration-700 ease-out ${
                completionPct === 100
                  ? "bg-gradient-to-r from-emerald-500 to-teal-400"
                  : completionPct >= 50
                  ? "bg-gradient-to-r from-blue-600 to-emerald-400"
                  : "bg-gradient-to-r from-amber-500 to-orange-400"
              }`}
              style={{ width: `${completionPct}%` }}
            />
          </div>

          {/* 4-Tier Checklist Badges */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 pt-1">
            {/* Tier 1: Basic Info */}
            <div
              className={`p-3 rounded-xl border text-xs flex items-center space-x-2.5 ${
                breakdown?.basic_info?.is_complete
                  ? "bg-emerald-50/70 border-emerald-200 text-emerald-900"
                  : "bg-slate-50 border-slate-200 text-slate-600"
              }`}
            >
              {breakdown?.basic_info?.is_complete ? (
                <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
              ) : (
                <Circle className="w-4 h-4 text-slate-400 flex-shrink-0" />
              )}
              <div className="truncate">
                <span className="font-semibold block">Basic Info (+25%)</span>
                <span className="text-[11px] text-slate-500 truncate">Phone & Location</span>
              </div>
            </div>

            {/* Tier 2: Education */}
            <div
              className={`p-3 rounded-xl border text-xs flex items-center space-x-2.5 ${
                breakdown?.education?.is_complete
                  ? "bg-emerald-50/70 border-emerald-200 text-emerald-900"
                  : "bg-slate-50 border-slate-200 text-slate-600"
              }`}
            >
              {breakdown?.education?.is_complete ? (
                <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
              ) : (
                <Circle className="w-4 h-4 text-slate-400 flex-shrink-0" />
              )}
              <div className="truncate">
                <span className="font-semibold block">Education (+25%)</span>
                <span className="text-[11px] text-slate-500 truncate">Institution & Major</span>
              </div>
            </div>

            {/* Tier 3: Career & Skills */}
            <div
              className={`p-3 rounded-xl border text-xs flex items-center space-x-2.5 ${
                breakdown?.career_skills?.is_complete
                  ? "bg-emerald-50/70 border-emerald-200 text-emerald-900"
                  : "bg-slate-50 border-slate-200 text-slate-600"
              }`}
            >
              {breakdown?.career_skills?.is_complete ? (
                <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
              ) : (
                <Circle className="w-4 h-4 text-slate-400 flex-shrink-0" />
              )}
              <div className="truncate">
                <span className="font-semibold block">Skills & Role (+25%)</span>
                <span className="text-[11px] text-slate-500 truncate">Track & ≥3 Skills</span>
              </div>
            </div>

            {/* Tier 4: Resume */}
            <div
              className={`p-3 rounded-xl border text-xs flex items-center space-x-2.5 ${
                breakdown?.resume?.is_complete
                  ? "bg-emerald-50/70 border-emerald-200 text-emerald-900"
                  : "bg-slate-50 border-slate-200 text-slate-600"
              }`}
            >
              {breakdown?.resume?.is_complete ? (
                <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
              ) : (
                <Circle className="w-4 h-4 text-slate-400 flex-shrink-0" />
              )}
              <div className="truncate">
                <span className="font-semibold block">Resume/CV (+25%)</span>
                <span className="text-[11px] text-slate-500 truncate">PDF/DOCX Upload</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 4-CARD MODULAR GRID (Matching Profile(Learner based).png) */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* CARD 1: PERSONAL INFORMATION */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-5">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div className="flex items-center space-x-2.5">
              <div className="w-9 h-9 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center">
                <User className="w-5 h-5" />
              </div>
              <h2 className="text-base font-bold text-navy-950 font-heading">
                Personal Information
              </h2>
            </div>
            <button
              onClick={handleOpenEditModal}
              className="text-xs font-semibold text-blue-600 hover:text-blue-800 transition-colors"
            >
              Edit
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-xs text-slate-400 font-medium uppercase tracking-wider block">
                Full Name
              </span>
              <span className="font-semibold text-navy-900 mt-0.5 block">
                {profile?.first_name} {profile?.last_name}
              </span>
            </div>
            <div>
              <span className="text-xs text-slate-400 font-medium uppercase tracking-wider block">
                Email Address
              </span>
              <span className="font-semibold text-navy-900 mt-0.5 block truncate">
                {profile?.email}
              </span>
            </div>
            <div>
              <span className="text-xs text-slate-400 font-medium uppercase tracking-wider block">
                Phone Number
              </span>
              <span className="font-semibold text-navy-900 mt-0.5 block">
                {profile?.phone_number || <span className="text-slate-400 font-normal italic">Not provided</span>}
              </span>
            </div>
            <div>
              <span className="text-xs text-slate-400 font-medium uppercase tracking-wider block">
                Location
              </span>
              <span className="font-semibold text-navy-900 mt-0.5 block">
                {profile?.location || <span className="text-slate-400 font-normal italic">Dhaka, Bangladesh</span>}
              </span>
            </div>
          </div>

          <div className="pt-2">
            <span className="text-xs text-slate-400 font-medium uppercase tracking-wider block mb-1.5">
              About / Professional Bio
            </span>
            <p className="text-sm text-slate-600 leading-relaxed bg-slate-50/70 p-3.5 rounded-xl border border-slate-100">
              {profile?.bio ||
                "Add your bio to introduce your engineering skills, learning journey, and career goals to recruiters."}
            </p>
          </div>
        </div>

        {/* CARD 2: CAREER INFORMATION & INTERACTIVE SKILL PILLS */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-5">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div className="flex items-center space-x-2.5">
              <div className="w-9 h-9 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center">
                <Briefcase className="w-5 h-5" />
              </div>
              <h2 className="text-base font-bold text-navy-950 font-heading">
                Career Information & Skills
              </h2>
            </div>
            <button
              onClick={handleOpenEditModal}
              className="text-xs font-semibold text-blue-600 hover:text-blue-800 transition-colors"
            >
              Edit
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-xs text-slate-400 font-medium uppercase tracking-wider block">
                Target Job Role
              </span>
              <span className="font-semibold text-navy-900 mt-0.5 block">
                {profile?.target_role || "Junior Software Developer"}
              </span>
            </div>
            <div>
              <span className="text-xs text-slate-400 font-medium uppercase tracking-wider block">
                Primary Track
              </span>
              <span className="font-semibold text-navy-900 mt-0.5 block">
                {profile?.primary_track || "Full-Stack Development"}
              </span>
            </div>
          </div>

          {/* Interactive Skills Section */}
          <div className="pt-2 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-400 font-medium uppercase tracking-wider block">
                Tagged Competency Skills ({profile?.skills?.length || 0})
              </span>
              <span className="text-[11px] text-slate-400">
                {profile?.skills?.length >= 3 ? (
                  <span className="text-emerald-600 font-semibold">✓ Meets 3+ requirement</span>
                ) : (
                  <span className="text-amber-600">Need at least 3 for +25%</span>
                )}
              </span>
            </div>

            {/* Current Skill Pills */}
            <div className="flex flex-wrap gap-2">
              {profile?.skills?.map((skill) => (
                <span
                  key={skill}
                  className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-blue-50 text-blue-800 border border-blue-200 group hover:border-blue-400 transition-colors"
                >
                  <span>{skill}</span>
                  <button
                    type="button"
                    onClick={() => handleRemoveSkill(skill)}
                    className="w-3.5 h-3.5 rounded-full hover:bg-blue-200 flex items-center justify-center text-blue-500 hover:text-blue-900 transition-colors"
                    title={`Remove ${skill}`}
                  >
                    <X className="w-2.5 h-2.5" />
                  </button>
                </span>
              ))}

              {(!profile?.skills || profile.skills.length === 0) && (
                <p className="text-xs text-slate-400 italic py-1">
                  No skills added yet. Type below or choose from recommended suggestions.
                </p>
              )}
            </div>

            {/* Skill Input field with instant add */}
            <div className="flex items-center space-x-2 pt-1">
              <div className="relative flex-1">
                <input
                  type="text"
                  placeholder="Add a new skill (e.g. Docker, Python)..."
                  value={newSkillInput}
                  onChange={(e) => setNewSkillInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault();
                      handleAddSkill();
                    }
                  }}
                  className="w-full text-xs px-3.5 py-2 rounded-lg border border-slate-200 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                />
              </div>
              <button
                type="button"
                onClick={() => handleAddSkill()}
                className="px-3 py-2 bg-navy-950 hover:bg-navy-900 text-white rounded-lg text-xs font-semibold flex items-center space-x-1 shadow-sm transition-colors"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Add</span>
              </button>
            </div>

            {/* Quick suggestion chips */}
            <div className="pt-1">
              <span className="text-[11px] text-slate-400 block mb-1.5">
                Suggested skills:
              </span>
              <div className="flex flex-wrap gap-1.5">
                {suggestedSkills
                  .filter(
                    (s) =>
                      !profile?.skills?.some(
                        (ps) => ps.toLowerCase() === s.toLowerCase()
                      )
                  )
                  .slice(0, 6)
                  .map((chip) => (
                    <button
                      key={chip}
                      type="button"
                      onClick={() => handleAddSkill(chip)}
                      className="px-2 py-0.5 rounded-md text-[11px] bg-slate-100 text-slate-600 hover:bg-slate-200 hover:text-navy-900 transition-colors"
                    >
                      + {chip}
                    </button>
                  ))}
              </div>
            </div>
          </div>
        </div>

        {/* CARD 3: EDUCATIONAL BACKGROUND */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-5">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div className="flex items-center space-x-2.5">
              <div className="w-9 h-9 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center">
                <GraduationCap className="w-5 h-5" />
              </div>
              <h2 className="text-base font-bold text-navy-950 font-heading">
                Educational Background
              </h2>
            </div>
            <button
              onClick={handleOpenEditModal}
              className="text-xs font-semibold text-blue-600 hover:text-blue-800 transition-colors"
            >
              Edit
            </button>
          </div>

          <div className="space-y-4">
            <div className="p-4 rounded-xl bg-slate-50/70 border border-slate-100 space-y-2">
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="text-sm font-bold text-navy-950">
                    {profile?.institution || "University of Asia Pacific"}
                  </h3>
                  <p className="text-xs text-slate-600 font-medium">
                    {profile?.department || "Computer Science & Engineering"}
                    {portfolio.degree && ` · ${portfolio.degree}`}
                  </p>
                </div>
                <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-purple-100 text-purple-800">
                  Higher Education
                </span>
              </div>
              <p className="text-xs text-slate-500 pt-1">
                Academic records verified on platform for job applications and mock test credentials.
              </p>
            </div>
          </div>
        </div>

        {/* CARD 4: EXPERIENCE & PORTFOLIO LINKS */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-5">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div className="flex items-center space-x-2.5">
              <div className="w-9 h-9 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center">
                <Globe className="w-5 h-5" />
              </div>
              <h2 className="text-base font-bold text-navy-950 font-heading">
                Experience & Online Presence
              </h2>
            </div>
            <button
              onClick={handleOpenEditModal}
              className="text-xs font-semibold text-blue-600 hover:text-blue-800 transition-colors"
            >
              Edit
            </button>
          </div>

          <div className="space-y-3">
            {/* GitHub */}
            <div className="flex items-center justify-between p-3 rounded-xl border border-slate-100 hover:border-slate-300 transition-colors">
              <div className="flex items-center space-x-3">
                <GithubIcon className="w-5 h-5 text-slate-700" />
                <div>
                  <span className="text-xs font-semibold text-navy-900 block">GitHub Profile</span>
                  <span className="text-[11px] text-slate-400 block truncate max-w-[200px]">
                    {portfolio.github_url || "Not added yet"}
                  </span>
                </div>
              </div>
              {portfolio.github_url ? (
                <a
                  href={portfolio.github_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="p-1.5 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                >
                  <ExternalLink className="w-4 h-4" />
                </a>
              ) : (
                <button
                  onClick={handleOpenEditModal}
                  className="text-xs text-blue-600 font-medium hover:underline"
                >
                  Add link
                </button>
              )}
            </div>

            {/* LinkedIn */}
            <div className="flex items-center justify-between p-3 rounded-xl border border-slate-100 hover:border-slate-300 transition-colors">
              <div className="flex items-center space-x-3">
                <LinkedinIcon className="w-5 h-5 text-blue-600" />
                <div>
                  <span className="text-xs font-semibold text-navy-900 block">LinkedIn Profile</span>
                  <span className="text-[11px] text-slate-400 block truncate max-w-[200px]">
                    {portfolio.linkedin_url || "Not added yet"}
                  </span>
                </div>
              </div>
              {portfolio.linkedin_url ? (
                <a
                  href={portfolio.linkedin_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="p-1.5 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                >
                  <ExternalLink className="w-4 h-4" />
                </a>
              ) : (
                <button
                  onClick={handleOpenEditModal}
                  className="text-xs text-blue-600 font-medium hover:underline"
                >
                  Add link
                </button>
              )}
            </div>

            {/* Portfolio Website */}
            <div className="flex items-center justify-between p-3 rounded-xl border border-slate-100 hover:border-slate-300 transition-colors">
              <div className="flex items-center space-x-3">
                <Globe className="w-5 h-5 text-emerald-600" />
                <div>
                  <span className="text-xs font-semibold text-navy-900 block">Portfolio Website</span>
                  <span className="text-[11px] text-slate-400 block truncate max-w-[200px]">
                    {portfolio.portfolio_url || "Not added yet"}
                  </span>
                </div>
              </div>
              {portfolio.portfolio_url ? (
                <a
                  href={portfolio.portfolio_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="p-1.5 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                >
                  <ExternalLink className="w-4 h-4" />
                </a>
              ) : (
                <button
                  onClick={handleOpenEditModal}
                  className="text-xs text-blue-600 font-medium hover:underline"
                >
                  Add link
                </button>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* RESUME / CV DOCUMENT CARD */}
      <div className="bg-white rounded-3xl border border-slate-200 p-6 sm:p-8 shadow-sm space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100">
          <div>
            <div className="flex items-center space-x-2.5">
              <div className="w-9 h-9 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center">
                <FileText className="w-5 h-5" />
              </div>
              <h2 className="text-xl font-bold text-navy-950 font-heading">
                Curriculum Vitae (CV) & Resume Management
              </h2>
            </div>
            <p className="text-xs text-slate-500 mt-1">
              Your resume is shared when applying for jobs and internships across verified partner companies.
            </p>
          </div>
          <span className="px-3 py-1 text-xs font-semibold rounded-full bg-slate-100 text-slate-600 self-start sm:self-auto">
            Max 5MB (PDF or DOCX)
          </span>
        </div>

        {/* Uploaded CV State or Empty Dropzone */}
        {profile?.resume_filename ? (
          <div className="bg-emerald-50/60 border border-emerald-200 rounded-2xl p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-6">
            <div className="flex items-center space-x-4">
              <div className="w-14 h-14 rounded-2xl bg-white border border-emerald-200 flex items-center justify-center text-emerald-600 shadow-sm flex-shrink-0">
                <FileCheck className="w-7 h-7" />
              </div>
              <div>
                <div className="flex items-center space-x-2">
                  <h3 className="text-base font-bold text-navy-950">
                    {profile.resume_filename}
                  </h3>
                  <span className="px-2.5 py-0.5 rounded-full text-[10px] font-extrabold uppercase tracking-wide bg-emerald-200 text-emerald-900">
                    Uploaded & Active
                  </span>
                </div>
                <p className="text-xs text-slate-500 mt-0.5">
                  Verified document · Attached to your learner profile (+25% completion achieved)
                </p>
              </div>
            </div>

            <div className="flex items-center space-x-3">
              <button
                type="button"
                onClick={handleDownloadResume}
                className="inline-flex items-center space-x-1.5 px-4 py-2 rounded-xl text-xs font-semibold bg-white border border-slate-200 text-navy-900 hover:bg-slate-50 shadow-sm transition-colors"
              >
                <Download className="w-3.5 h-3.5 text-blue-600" />
                <span>View / Download CV</span>
              </button>
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                disabled={uploadingResume}
                className="inline-flex items-center space-x-1.5 px-4 py-2 rounded-xl text-xs font-semibold bg-navy-950 hover:bg-navy-900 text-white shadow-sm transition-colors"
              >
                <RefreshCw className={`w-3.5 h-3.5 text-emerald-400 ${uploadingResume ? "animate-spin" : ""}`} />
                <span>Replace CV</span>
              </button>
              <button
                type="button"
                onClick={handleDeleteResume}
                disabled={uploadingResume}
                className="p-2 text-slate-400 hover:text-crimson hover:bg-crimson-50 rounded-xl transition-colors"
                title="Remove Resume"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          </div>
        ) : (
          <div
            onClick={() => fileInputRef.current?.click()}
            className="border-2 border-dashed border-slate-300 hover:border-blue-500 bg-slate-50 hover:bg-blue-50/40 rounded-2xl p-8 text-center cursor-pointer transition-all duration-200 group"
          >
            <div className="w-14 h-14 mx-auto rounded-2xl bg-white border border-slate-200 group-hover:border-blue-300 flex items-center justify-center text-slate-400 group-hover:text-blue-600 shadow-sm transition-colors mb-3">
              <UploadCloud className="w-7 h-7" />
            </div>
            <h4 className="text-sm font-bold text-navy-900">
              {uploadingResume ? "Uploading & validating document..." : "Click to upload or drag & drop your CV"}
            </h4>
            <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
              Supports official PDF (.pdf) and Word documents (.docx) up to 5MB. Adds +25% towards your profile strength.
            </p>
          </div>
        )}
      </div>

      {/* EDIT PROFILE MODAL */}
      {isEditModalOpen && (
        <div className="fixed inset-0 z-50 overflow-y-auto bg-navy-950/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl max-w-2xl w-full p-6 sm:p-8 shadow-2xl border border-slate-100 relative space-y-6">
            <div className="flex items-center justify-between pb-4 border-b border-slate-100">
              <div className="flex items-center space-x-2.5">
                <div className="w-9 h-9 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center">
                  <Edit3 className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-navy-950 font-heading">
                    Edit Learner Profile
                  </h3>
                  <p className="text-xs text-slate-500">
                    Update your personal, educational, and career details.
                  </p>
                </div>
              </div>
              <button
                onClick={() => setIsEditModalOpen(false)}
                className="p-1.5 text-slate-400 hover:text-navy-900 rounded-lg hover:bg-slate-100 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSaveProfile} className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Input
                  label="Contact Phone"
                  name="phone_number"
                  placeholder="01712345678"
                  value={editFormData.phone_number}
                  onChange={(e) =>
                    setEditFormData({ ...editFormData, phone_number: e.target.value })
                  }
                />
                <Input
                  label="Current Location"
                  name="location"
                  placeholder="Dhaka, Bangladesh"
                  value={editFormData.location}
                  onChange={(e) =>
                    setEditFormData({ ...editFormData, location: e.target.value })
                  }
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Input
                  label="Target Job Role"
                  name="target_role"
                  placeholder="Junior Backend Developer"
                  value={editFormData.target_role}
                  onChange={(e) =>
                    setEditFormData({ ...editFormData, target_role: e.target.value })
                  }
                />
                <Input
                  label="Primary Career Track"
                  name="primary_track"
                  placeholder="Python & Cloud Engineering"
                  value={editFormData.primary_track}
                  onChange={(e) =>
                    setEditFormData({ ...editFormData, primary_track: e.target.value })
                  }
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Input
                  label="Institution / University"
                  name="institution"
                  placeholder="University of Asia Pacific"
                  value={editFormData.institution}
                  onChange={(e) =>
                    setEditFormData({ ...editFormData, institution: e.target.value })
                  }
                />
                <Input
                  label="Department / Degree"
                  name="department"
                  placeholder="Computer Science & Engineering"
                  value={editFormData.department}
                  onChange={(e) =>
                    setEditFormData({ ...editFormData, department: e.target.value })
                  }
                />
              </div>

              <div className="space-y-1.5">
                <label className="block text-xs font-semibold text-navy-800 uppercase tracking-wider">
                  Professional Bio & Objectives
                </label>
                <textarea
                  rows={3}
                  value={editFormData.bio}
                  onChange={(e) =>
                    setEditFormData({ ...editFormData, bio: e.target.value })
                  }
                  placeholder="Briefly describe your career background, coding ambitions, and learning goals..."
                  className="w-full text-sm p-3 rounded-xl border border-slate-200 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-1">
                <Input
                  label="GitHub URL"
                  name="github_url"
                  placeholder="https://github.com/..."
                  value={editFormData.github_url}
                  onChange={(e) =>
                    setEditFormData({ ...editFormData, github_url: e.target.value })
                  }
                />
                <Input
                  label="LinkedIn URL"
                  name="linkedin_url"
                  placeholder="https://linkedin.com/in/..."
                  value={editFormData.linkedin_url}
                  onChange={(e) =>
                    setEditFormData({ ...editFormData, linkedin_url: e.target.value })
                  }
                />
                <Input
                  label="Portfolio URL"
                  name="portfolio_url"
                  placeholder="https://mywebsite.com"
                  value={editFormData.portfolio_url}
                  onChange={(e) =>
                    setEditFormData({ ...editFormData, portfolio_url: e.target.value })
                  }
                />
              </div>

              <div className="flex items-center justify-end space-x-3 pt-4 border-t border-slate-100">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setIsEditModalOpen(false)}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  size="sm"
                  loading={saving}
                  className="bg-navy-950 hover:bg-navy-900 text-white"
                >
                  Save Changes
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default LearnerProfile;
