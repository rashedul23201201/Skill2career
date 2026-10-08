import React, { useState, useEffect } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import jobService from "../services/jobService";
import companyService from "../services/companyService";
import { ROUTES, USER_ROLES } from "../constants";
import {
  ArrowLeft,
  Briefcase,
  Calendar,
  CheckCircle2,
  AlertCircle,
  ShieldAlert,
  Trash2,
  X,
  Save,
  MapPin,
} from "lucide-react";

export const JobManagement = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const isNew = !id || id === "new";

  const [formData, setFormData] = useState({
    title: "",
    posting_type: "Job",
    work_mode: "On-site",
    location: "Dhaka, Bangladesh",
    description: "",
    requirements: "",
    skills: [],
    compensation: "",
    duration: "",
    experience_level: "Entry Level",
    category: "Software Engineering",
    deadline: "",
    status: "ACTIVE",
  });

  const [skillInput, setSkillInput] = useState("");
  const [loading, setLoading] = useState(!isNew);
  const [submitting, setSubmitting] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  const [verificationStatus, setVerificationStatus] = useState("APPROVED");
  const [checkingVerification, setCheckingVerification] = useState(user?.role === USER_ROLES.COMPANY);

  // Check company verification status if company role
  useEffect(() => {
    const checkVerification = async () => {
      if (user?.role === USER_ROLES.COMPANY) {
        try {
          const res = await companyService.getVerificationStatus();
          if (res?.data?.status) {
            setVerificationStatus(res.data.status);
          }
        } catch {
          // Fallback if verification endpoint is unreachable
        } finally {
          setCheckingVerification(false);
        }
      } else {
        setCheckingVerification(false);
      }
    };
    checkVerification();
  }, [user]);

  // Load existing job details if editing
  useEffect(() => {
    if (!isNew && id) {
      const loadJob = async () => {
        try {
          setLoading(true);
          setError(null);
          const res = await jobService.getJobById(id);
          if (res?.data) {
            const data = res.data;
            setFormData({
              title: data.title || "",
              posting_type: data.posting_type || "JOB",
              work_mode: data.work_mode || "ON_SITE",
              location: data.location || "Dhaka, Bangladesh",
              description: data.description || "",
              requirements: data.requirements || "",
              skills: Array.isArray(data.skills) ? data.skills : [],
              compensation: data.compensation || "",
              duration: data.duration || "",
              experience_level: data.experience_level || "ENTRY_LEVEL",
              category: data.category || "Software Engineering",
              deadline: data.deadline ? data.deadline.substring(0, 10) : "",
              status: data.status || "ACTIVE",
            });
          }
        } catch {
          setError("Failed to load job posting data. Ensure the ID is valid.");
        } finally {
          setLoading(false);
        }
      };
      loadJob();
    }
  }, [id, isNew]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleAddSkill = (e) => {
    if (e) e.preventDefault();
    const trimmed = skillInput.trim();
    if (trimmed && !formData.skills.includes(trimmed)) {
      setFormData((prev) => ({
        ...prev,
        skills: [...prev.skills, trimmed],
      }));
      setSkillInput("");
    }
  };

  const handleRemoveSkill = (skillToRemove) => {
    setFormData((prev) => ({
      ...prev,
      skills: prev.skills.filter((s) => s !== skillToRemove),
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    if (formData.title.trim().length < 3) {
      setError("Job title must be at least 3 characters.");
      return;
    }
    if (formData.description.trim().length < 10) {
      setError("Job description must be at least 10 characters.");
      return;
    }
    if (formData.requirements.trim().length < 5) {
      setError("Requirements must be at least 5 characters.");
      return;
    }
    if (!formData.compensation.trim()) {
      setError("Please specify the salary or stipend compensation.");
      return;
    }

    const payload = {
      title: formData.title.trim(),
      posting_type: formData.posting_type,
      work_mode: formData.work_mode,
      location: formData.location.trim(),
      description: formData.description.trim(),
      requirements: formData.requirements.trim(),
      skills: formData.skills,
      compensation: formData.compensation.trim(),
      duration: formData.posting_type?.toUpperCase() === "INTERNSHIP" ? formData.duration.trim() || "3 Months" : null,
      experience_level: formData.experience_level,
      category: formData.category,
      deadline: formData.deadline ? new Date(formData.deadline).toISOString() : null,
      status: formData.status,
    };

    try {
      setSubmitting(true);
      if (isNew) {
        const res = await jobService.createJob(payload);
        setSuccess("Vacancy published successfully!");
        setTimeout(() => {
          if (res?.data?.id) {
            navigate(`/jobs/${res.data.id}`);
          } else {
            navigate(ROUTES.JOBS);
          }
        }, 800);
      } else {
        await jobService.updateJob(id, payload);
        setSuccess("Job posting updated successfully!");
        setTimeout(() => {
          navigate(`/jobs/${id}`);
        }, 800);
      }
    } catch (err) {
      const detail = err.response?.data?.detail;
      if (detail === "COMPANY_NOT_VERIFIED" || err.response?.status === 403) {
        setError("Your company is not verified. Unverified companies cannot publish vacancies.");
      } else {
        setError(detail || "An error occurred while saving the vacancy. Please try again.");
      }
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async () => {
    if (!window.confirm("Are you sure you want to permanently delete this vacancy listing?")) return;
    try {
      setDeleting(true);
      await jobService.deleteJob(id);
      navigate(ROUTES.JOBS);
    } catch {
      setError("Failed to delete vacancy.");
      setDeleting(false);
    }
  };

  const isVerified = verificationStatus === "APPROVED" || user?.role === USER_ROLES.ADMIN;

  if (loading || checkingVerification) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16 flex flex-col items-center justify-center space-y-4">
        <div className="w-10 h-10 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
        <p className="text-sm font-semibold text-slate-500">Loading vacancy details...</p>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 space-y-8 animate-fade-in">
      {/* Navigation header */}
      <div className="flex items-center justify-between">
        <Link
          to={isNew ? ROUTES.JOBS : `/jobs/${id}`}
          className="inline-flex items-center space-x-2 text-sm font-semibold text-slate-600 hover:text-navy-950 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>{isNew ? "Back to Job Board" : "Cancel & Return to Details"}</span>
        </Link>

        {!isNew && (
          <button
            type="button"
            onClick={handleDelete}
            disabled={deleting}
            className="inline-flex items-center space-x-1.5 px-3 py-1.5 text-xs font-semibold text-red-600 hover:text-red-700 hover:bg-red-50 rounded-lg transition-colors border border-red-200"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span>{deleting ? "Deleting..." : "Delete Vacancy"}</span>
          </button>
        )}
      </div>

      {/* Page Title Card */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 sm:p-8 shadow-xs">
        <div className="flex items-center space-x-3">
          <div className="w-12 h-12 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center">
            <Briefcase className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-2xl font-black text-navy-950 font-heading">
              {isNew ? "Create Recruitment Posting" : "Edit Vacancy Details"}
            </h1>
            <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
              Publish career vacancies and internship opportunities to connect with qualified learners.
            </p>
          </div>
        </div>
      </div>

      {/* Company Verification Banner if not approved */}
      {!isVerified && (
        <div className="p-5 rounded-2xl border border-amber-200 bg-amber-50/80 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex items-start space-x-3">
            <ShieldAlert className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
            <div>
              <h3 className="text-sm font-bold text-amber-900">Company Verification Required</h3>
              <p className="text-xs text-amber-700 mt-0.5 leading-relaxed">
                Your company status is currently <strong>{verificationStatus}</strong>. Under platform policy (SKL-2 & SKL-4), only verified companies can publish active vacancies.
              </p>
            </div>
          </div>
          <Link
            to={ROUTES.COMPANY_VERIFICATION}
            className="shrink-0 px-4 py-2 rounded-xl bg-amber-600 hover:bg-amber-700 text-white text-xs font-bold shadow-sm transition-colors"
          >
            Complete Verification
          </Link>
        </div>
      )}

      {/* Notifications */}
      {error && (
        <div className="p-4 rounded-xl border border-red-200 bg-red-50 text-red-700 text-sm flex items-center space-x-2">
          <AlertCircle className="w-5 h-5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {success && (
        <div className="p-4 rounded-xl border border-emerald-200 bg-emerald-50 text-emerald-700 text-sm flex items-center space-x-2">
          <CheckCircle2 className="w-5 h-5 shrink-0" />
          <span>{success}</span>
        </div>
      )}

      {/* Main Form */}
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Section 1: Basic Information */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6 sm:p-8 shadow-xs space-y-6">
          <h2 className="text-base font-bold text-navy-950 font-heading border-b border-slate-100 pb-3">
            1. Basic Opportunity Details
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-1.5 md:col-span-2">
              <label className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                Vacancy Title <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                name="title"
                value={formData.title}
                onChange={handleChange}
                placeholder="e.g. Senior Frontend Engineer, Junior Machine Learning Intern"
                required
                className="w-full px-4 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm text-slate-800"
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                Opportunity Type
              </label>
              <select
                name="posting_type"
                value={formData.posting_type}
                onChange={handleChange}
                className="w-full px-4 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm text-slate-800 bg-white"
              >
                <option value="Job">Job (Full-time / Part-time)</option>
                <option value="Internship">Internship</option>
              </select>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                Work Mode
              </label>
              <select
                name="work_mode"
                value={formData.work_mode}
                onChange={handleChange}
                className="w-full px-4 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm text-slate-800 bg-white"
              >
                <option value="On-site">On-site</option>
                <option value="Remote">Remote</option>
                <option value="Hybrid">Hybrid</option>
              </select>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                Experience Level
              </label>
              <select
                name="experience_level"
                value={formData.experience_level}
                onChange={handleChange}
                className="w-full px-4 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm text-slate-800 bg-white"
              >
                <option value="Entry Level">Entry Level / Graduate</option>
                <option value="Junior">Junior (1–2 years)</option>
                <option value="Mid Level">Mid Level (2–4 years)</option>
                <option value="Senior">Senior Level (5+ years)</option>
              </select>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                Domain Category
              </label>
              <select
                name="category"
                value={formData.category}
                onChange={handleChange}
                className="w-full px-4 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm text-slate-800 bg-white"
              >
                <option value="Software Engineering">Software Engineering</option>
                <option value="Product & Design">Product & Design</option>
                <option value="Data Science">Data Science & AI</option>
                <option value="Quality Assurance">Quality Assurance (QA)</option>
                <option value="DevOps & Cloud">DevOps & Cloud</option>
                <option value="Mobile Development">Mobile Development</option>
                <option value="Cybersecurity">Cybersecurity</option>
              </select>
            </div>

            <div className="space-y-1.5 md:col-span-2">
              <label className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                Work Location / Headquarter <span className="text-red-500">*</span>
              </label>
              <div className="relative">
                <MapPin className="w-4 h-4 text-slate-400 absolute left-3.5 top-3.5" />
                <input
                  type="text"
                  name="location"
                  value={formData.location}
                  onChange={handleChange}
                  placeholder="e.g. Dhaka, Bangladesh or Remote (Worldwide)"
                  required
                  className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm text-slate-800"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Section 2: Compensation & Deadlines */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6 sm:p-8 shadow-xs space-y-6">
          <h2 className="text-base font-bold text-navy-950 font-heading border-b border-slate-100 pb-3">
            2. Compensation & Timeline
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                {formData.posting_type?.toUpperCase() === "INTERNSHIP" ? "Monthly Stipend" : "Salary Range"}{" "}
                <span className="text-red-500">*</span>
              </label>
              <div className="relative">
                <span className="text-slate-400 text-sm font-semibold absolute left-3.5 top-2.5">৳</span>
                <input
                  type="text"
                  name="compensation"
                  value={formData.compensation}
                  onChange={handleChange}
                  placeholder={formData.posting_type?.toUpperCase() === "INTERNSHIP" ? "e.g. ৳20K / month" : "e.g. ৳35K – ৳50K"}
                  required
                  className="w-full pl-8 pr-4 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm text-slate-800"
                />
              </div>
            </div>

            {formData.posting_type?.toUpperCase() === "INTERNSHIP" && (
              <div className="space-y-1.5">
                <label className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                  Internship Duration
                </label>
                <input
                  type="text"
                  name="duration"
                  value={formData.duration}
                  onChange={handleChange}
                  placeholder="e.g. 3 Months or 6 Months"
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm text-slate-800"
                />
              </div>
            )}

            <div className="space-y-1.5">
              <label className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                Application Deadline
              </label>
              <div className="relative">
                <Calendar className="w-4 h-4 text-slate-400 absolute left-3.5 top-3.5" />
                <input
                  type="date"
                  name="deadline"
                  value={formData.deadline}
                  onChange={handleChange}
                  className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm text-slate-800"
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                Publication Status
              </label>
              <select
                name="status"
                value={formData.status}
                onChange={handleChange}
                className="w-full px-4 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm text-slate-800 bg-white"
              >
                <option value="ACTIVE">Active (Live on Job Board)</option>
                <option value="DRAFT">Draft (Saved privately)</option>
                <option value="CLOSED">Closed (Hiring completed)</option>
              </select>
            </div>
          </div>
        </div>

        {/* Section 3: Detailed Description & Requirements */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6 sm:p-8 shadow-xs space-y-6">
          <h2 className="text-base font-bold text-navy-950 font-heading border-b border-slate-100 pb-3">
            3. Job Description & Competencies
          </h2>

          <div className="space-y-1.5">
            <label className="text-xs font-bold text-slate-700 uppercase tracking-wider">
              Role Description & Scope <span className="text-red-500">*</span>
            </label>
            <textarea
              name="description"
              rows={5}
              value={formData.description}
              onChange={handleChange}
              placeholder="Outline role responsibilities, key projects, and team culture..."
              required
              className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm text-slate-800"
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-bold text-slate-700 uppercase tracking-wider">
              Candidate Requirements & Qualifications <span className="text-red-500">*</span>
            </label>
            <textarea
              name="requirements"
              rows={5}
              value={formData.requirements}
              onChange={handleChange}
              placeholder="List degrees, experience, and must-have qualities (each on a new line or paragraph)..."
              required
              className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm text-slate-800"
            />
          </div>

          {/* Key Skill Tags */}
          <div className="space-y-3">
            <label className="text-xs font-bold text-slate-700 uppercase tracking-wider">
              Required Skills & Technologies
            </label>
            <div className="flex items-center space-x-2">
              <input
                type="text"
                value={skillInput}
                onChange={(e) => setSkillInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    handleAddSkill();
                  }
                }}
                placeholder="Type skill and press Add (e.g. React, Python, PostgreSQL, AWS)"
                className="flex-1 px-4 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm text-slate-800"
              />
              <button
                type="button"
                onClick={handleAddSkill}
                className="px-4 py-2.5 bg-slate-900 hover:bg-navy-950 text-white rounded-xl text-xs font-bold transition-colors cursor-pointer"
              >
                Add Skill
              </button>
            </div>

            {/* Rendered Skill Badges */}
            <div className="flex flex-wrap gap-2 pt-1">
              {formData.skills.map((skill) => (
                <span
                  key={skill}
                  className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-200"
                >
                  <span>{skill}</span>
                  <button
                    type="button"
                    onClick={() => handleRemoveSkill(skill)}
                    className="hover:text-blue-900 transition-colors"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </span>
              ))}
              {formData.skills.length === 0 && (
                <span className="text-xs text-slate-400 italic">No skill tags added yet.</span>
              )}
            </div>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center justify-end space-x-4 pt-4">
          <Link
            to={isNew ? ROUTES.JOBS : `/jobs/${id}`}
            className="px-6 py-3 rounded-xl border border-slate-300 text-slate-700 hover:bg-slate-50 text-xs font-bold transition-colors"
          >
            Cancel
          </Link>
          <button
            type="submit"
            disabled={submitting || (!isVerified && user?.role === USER_ROLES.COMPANY)}
            className="inline-flex items-center space-x-2 px-8 py-3 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white text-xs font-extrabold shadow-md hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
          >
            <Save className="w-4 h-4" />
            <span>
              {submitting
                ? "Saving Vacancy..."
                : isNew
                ? "Publish Vacancy"
                : "Save Changes"}
            </span>
          </button>
        </div>
      </form>
    </div>
  );
};

export default JobManagement;
