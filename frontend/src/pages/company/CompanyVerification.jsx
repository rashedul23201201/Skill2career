import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import companyService from "../../services/companyService";
import { useAuth } from "../../hooks/useAuth";
import { ROUTES } from "../../constants";
import Button from "../../components/forms/Button";
import Input from "../../components/forms/Input";
import {
  Building2,
  ShieldCheck,
  ShieldAlert,
  Clock,
  ExternalLink,
  CheckCircle2,
  XCircle,
  FileText,
  AlertTriangle,
  Briefcase,
  Globe,
  MapPin,
  Phone,
  RefreshCw,
  Send,
  PlusCircle,
} from "lucide-react";

export const CompanyVerification = () => {
  const { user } = useAuth();
  const [statusData, setStatusData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [testingJobPost, setTestingJobPost] = useState(false);
  const [jobTestResult, setJobTestResult] = useState(null);
  const [notification, setNotification] = useState(null);

  const [formData, setFormData] = useState({
    company_name: "",
    trade_license_url: "",
    registration_number: "",
    industry: "",
    location: "Dhaka, Bangladesh",
    company_size: "11-50",
    website_url: "",
    office_address: "",
    contact_person: "",
    contact_phone: "",
    description: "",
  });

  const fetchStatus = async () => {
    try {
      setLoading(true);
      const res = await companyService.getVerificationStatus();
      if (res?.data) {
        setStatusData(res.data);
        setFormData({
          company_name: res.data.company_name || "",
          trade_license_url: res.data.trade_license_url || "",
          registration_number: res.data.registration_number || "",
          industry: res.data.industry || "",
          location: res.data.location || "Dhaka, Bangladesh",
          company_size: res.data.company_size || "11-50",
          website_url: res.data.website_url || "",
          office_address: res.data.office_address || "",
          contact_person: res.data.contact_person || `${user?.first_name || ""} ${user?.last_name || ""}`.trim(),
          contact_phone: res.data.contact_phone || "",
          description: res.data.description || "",
        });
      }
    } catch (err) {
      console.error("Failed to load verification status:", err);
      setNotification({
        type: "error",
        text: "Could not load verification records from the backend.",
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmitDossier = async (e) => {
    e.preventDefault();
    if (!formData.trade_license_url.trim()) {
      setNotification({
        type: "error",
        text: "Please provide a valid trade license URL or document reference.",
      });
      return;
    }

    try {
      setSubmitting(true);
      setNotification(null);
      const res = await companyService.submitVerificationRequest(formData);
      if (res?.data) {
        setStatusData(res.data);
        setNotification({
          type: "success",
          text: "Verification dossier submitted successfully! An administrator has been notified to review your documents.",
        });
      }
    } catch (err) {
      console.error("Dossier submission error:", err);
      setNotification({
        type: "error",
        text: err?.response?.data?.message || "Failed to submit verification dossier.",
      });
    } finally {
      setSubmitting(false);
    }
  };

  const handleTestJobPosting = async () => {
    try {
      setTestingJobPost(true);
      setJobTestResult(null);
      const res = await companyService.createJob({
        title: "Software Engineer (Verification Test Post)",
        description: "Testing gatekeeper authorization for verified employers.",
        job_type: "Full-time",
        location: formData.location || "Dhaka, Bangladesh",
      });
      setJobTestResult({
        success: true,
        data: res?.data,
        message: "Job posting gatekeeper PASSED! Your account has active publishing rights.",
      });
    } catch (err) {
      setJobTestResult({
        success: false,
        code: err?.response?.data?.error_code || "FORBIDDEN",
        message:
          err?.response?.data?.message ||
          "Access denied: Company account is unverified. Job publishing is disabled.",
      });
    } finally {
      setTestingJobPost(false);
    }
  };

  const isVerified = statusData?.is_verified && statusData?.verification_status === "APPROVED";
  const isRejected = statusData?.verification_status === "REJECTED";
  const isPending = !isVerified && !isRejected;

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header Banner */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 sm:p-8 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="space-y-2">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center shadow-sm">
              <Building2 className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h1 className="text-2xl sm:text-3xl font-extrabold text-navy-950 font-heading">
                  Company Verification
                </h1>
                <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-purple-100 text-purple-800">
                  SKL-2 Pipeline
                </span>
              </div>
              <p className="text-xs text-slate-500">
                Official employer verification, trade license compliance, and job publishing authorization.
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          <Link
            to={ROUTES.DASHBOARD}
            className="px-4 py-2 rounded-xl text-xs font-semibold border border-slate-200 hover:bg-slate-50 text-slate-700 transition-colors"
          >
            Dashboard
          </Link>
          <Button
            variant="outline"
            size="sm"
            onClick={fetchStatus}
            disabled={loading}
            className="flex items-center space-x-2"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
            <span>Refresh</span>
          </Button>
        </div>
      </div>

      {/* Mandatory Specification Warning Banners */}
      {isVerified ? (
        <div className="bg-emerald-50 border border-emerald-200 rounded-2xl p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-start space-x-3.5">
            <div className="w-10 h-10 rounded-xl bg-emerald-100 text-emerald-700 flex items-center justify-center flex-shrink-0 mt-0.5">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-base font-bold text-emerald-950 font-heading">
                Verified Enterprise Employer
              </h2>
              <p className="text-xs text-emerald-800 mt-1 leading-relaxed">
                Your company credentials and trade license have been audited and approved by the platform administration. Job and internship publishing is fully enabled.
              </p>
              {statusData?.verified_at && (
                <p className="text-[11px] text-emerald-700 font-mono mt-2">
                  Verified On: {new Date(statusData.verified_at).toLocaleDateString()}
                </p>
              )}
            </div>
          </div>
          <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold bg-emerald-200 text-emerald-900 flex-shrink-0">
            <CheckCircle2 className="w-4 h-4 mr-1 text-emerald-700" />
            APPROVED
          </span>
        </div>
      ) : isRejected ? (
        <div className="bg-red-50 border border-red-200 rounded-2xl p-6 space-y-3">
          <div className="flex items-start justify-between gap-4">
            <div className="flex items-start space-x-3.5">
              <div className="w-10 h-10 rounded-xl bg-red-100 text-red-700 flex items-center justify-center flex-shrink-0 mt-0.5">
                <ShieldAlert className="w-6 h-6" />
              </div>
              <div>
                <h2 className="text-base font-bold text-red-950 font-heading">
                  Verification Dossier Rejected
                </h2>
                <p className="text-xs text-red-800 mt-1 leading-relaxed">
                  Your verification submission was reviewed and rejected by the administration. Job publishing remains disabled until corrected documents are submitted.
                </p>
              </div>
            </div>
            <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold bg-red-200 text-red-900 flex-shrink-0">
              <XCircle className="w-4 h-4 mr-1 text-red-700" />
              REJECTED
            </span>
          </div>

          {statusData?.verification_notes && (
            <div className="bg-white/80 rounded-xl p-3.5 border border-red-200/80 text-xs space-y-1">
              <span className="font-bold text-red-950">Administrative Feedback / Reason:</span>
              <p className="text-red-900">{statusData.verification_notes}</p>
            </div>
          )}
        </div>
      ) : (
        /* Specification Amber Banner */
        <div className="bg-amber-50 border border-amber-200 rounded-2xl p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-2xs">
          <div className="flex items-start space-x-3.5">
            <div className="w-10 h-10 rounded-xl bg-amber-100 text-amber-700 flex items-center justify-center flex-shrink-0 mt-0.5">
              <Clock className="w-6 h-6 animate-pulse" />
            </div>
            <div>
              <h2 className="text-base font-bold text-amber-950 font-heading">
                Verification In Progress
              </h2>
              <p className="text-xs text-amber-800 mt-1 leading-relaxed">
                Your company account is currently pending administrative verification. Job and internship publishing is disabled until verified.
              </p>
            </div>
          </div>
          <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold bg-amber-200 text-amber-900 flex-shrink-0">
            <Clock className="w-4 h-4 mr-1 text-amber-800" />
            PENDING
          </span>
        </div>
      )}

      {/* Notification Toast */}
      {notification && (
        <div
          className={`p-4 rounded-xl border flex items-center justify-between ${
            notification.type === "success"
              ? "bg-emerald-50 border-emerald-200 text-emerald-800"
              : "bg-red-50 border-red-200 text-red-800"
          }`}
        >
          <div className="flex items-center space-x-2">
            {notification.type === "success" ? (
              <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0" />
            ) : (
              <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0" />
            )}
            <span className="text-sm font-medium">{notification.text}</span>
          </div>
          <button
            onClick={() => setNotification(null)}
            className="text-xs font-bold text-slate-500 hover:text-slate-800 ml-4"
          >
            Dismiss
          </button>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Verification Dossier Submission Form (2 Columns) */}
        <div className="lg:col-span-2 bg-white rounded-2xl border border-slate-200 p-6 sm:p-8 shadow-sm space-y-6">
          <div className="border-b border-slate-100 pb-4">
            <h2 className="text-lg font-bold text-navy-950 font-heading">
              {statusData?.trade_license_url ? "Update Verification Dossier" : "Submit Verification Dossier"}
            </h2>
            <p className="text-xs text-slate-500">
              Provide your official trade license document, registration certificate, and contact information for compliance approval.
            </p>
          </div>

          <form onSubmit={handleSubmitDossier} className="space-y-5">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Input
                label="Company Name"
                name="company_name"
                value={formData.company_name}
                onChange={handleChange}
                placeholder="e.g. Brain Station 23 / Optimizely"
                required
              />

              <Input
                label="Government / TIN / BIN Reg #"
                name="registration_number"
                value={formData.registration_number}
                onChange={handleChange}
                placeholder="e.g. TRAD/DNCC/123456/2026"
              />
            </div>

            {/* Official Trade License URL */}
            <div className="space-y-1">
              <label className="block text-xs font-bold text-navy-900">
                Official Trade License URL / Document Link <span className="text-red-500">*</span>
              </label>
              <div className="relative">
                <FileText className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type="url"
                  name="trade_license_url"
                  value={formData.trade_license_url}
                  onChange={handleChange}
                  placeholder="https://drive.google.com/... or https://storage.skill2career.com/license.pdf"
                  required
                  className="w-full pl-10 pr-4 py-2.5 rounded-xl text-xs border border-slate-200 focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
              </div>
              <p className="text-[11px] text-slate-400">
                Provide a publicly accessible or verifiable link to your valid trade license or incorporation certificate.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Input
                label="Industry Sector"
                name="industry"
                value={formData.industry}
                onChange={handleChange}
                placeholder="e.g. Software & FinTech"
              />

              <Input
                label="Location / City"
                name="location"
                value={formData.location}
                onChange={handleChange}
                placeholder="e.g. Gulshan, Dhaka, Bangladesh"
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Input
                label="Official Website URL"
                name="website_url"
                value={formData.website_url}
                onChange={handleChange}
                placeholder="https://company.com"
              />

              <div className="space-y-1">
                <label className="block text-xs font-bold text-navy-900">
                  Company Team Size
                </label>
                <select
                  name="company_size"
                  value={formData.company_size}
                  onChange={handleChange}
                  className="w-full px-3 py-2.5 rounded-xl text-xs border border-slate-200 focus:outline-none focus:ring-2 focus:ring-purple-500 bg-white"
                >
                  <option value="1-10">1-10 employees (Early Startup)</option>
                  <option value="11-50">11-50 employees (Growth Stage)</option>
                  <option value="51-200">51-200 employees (Mid-sized Tech)</option>
                  <option value="201-500">201-500 employees (Enterprise)</option>
                  <option value="500+">500+ employees (Multinational)</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Input
                label="Designated Contact Person"
                name="contact_person"
                value={formData.contact_person}
                onChange={handleChange}
                placeholder="e.g. Senior HR Manager"
              />

              <Input
                label="Contact Phone Number"
                name="contact_phone"
                value={formData.contact_phone}
                onChange={handleChange}
                placeholder="e.g. +8801700000000"
              />
            </div>

            <div className="space-y-1">
              <label className="block text-xs font-bold text-navy-900">
                Registered Office Address
              </label>
              <input
                type="text"
                name="office_address"
                value={formData.office_address}
                onChange={handleChange}
                placeholder="e.g. Plot # 4, Road # 10, Banani, Dhaka"
                className="w-full px-4 py-2.5 rounded-xl text-xs border border-slate-200 focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
            </div>

            <div className="space-y-1">
              <label className="block text-xs font-bold text-navy-900">
                Company Description & Overview
              </label>
              <textarea
                name="description"
                rows={3}
                value={formData.description}
                onChange={handleChange}
                placeholder="Describe your organization's mission, technology stack, and hiring focus..."
                className="w-full p-3 rounded-xl text-xs border border-slate-200 focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
            </div>

            <div className="pt-2 flex items-center justify-end">
              <Button
                type="submit"
                variant="primary"
                disabled={submitting}
                className="flex items-center space-x-2 bg-purple-600 hover:bg-purple-700 text-white"
              >
                <Send className="w-4 h-4" />
                <span>{submitting ? "Submitting Dossier..." : "Submit Verification Dossier"}</span>
              </Button>
            </div>
          </form>
        </div>

        {/* Right Sidebar: Gatekeeper Test & Live Status */}
        <div className="space-y-6">
          {/* Gatekeeper Authorization Sandbox */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-4">
            <div className="flex items-center space-x-3">
              <div className="w-9 h-9 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center">
                <Briefcase className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-navy-950 font-heading">
                  Job-Posting Gatekeeper
                </h3>
                <p className="text-[11px] text-slate-500">
                  Enforces <code className="bg-slate-100 px-1 py-0.5 rounded text-navy-800">require_verified_company</code>
                </p>
              </div>
            </div>

            <p className="text-xs text-slate-600 leading-relaxed">
              Job and internship publication is strictly guarded by backend authorization. Unverified companies receive HTTP 403 Forbidden with <code className="text-red-700">COMPANY_NOT_VERIFIED</code>.
            </p>

            <Button
              variant="outline"
              size="sm"
              onClick={handleTestJobPosting}
              disabled={testingJobPost}
              className="w-full flex items-center justify-center space-x-2"
            >
              <PlusCircle className="w-4 h-4 text-purple-600" />
              <span>{testingJobPost ? "Testing Gatekeeper..." : "Test Job Posting Gatekeeper"}</span>
            </Button>

            {jobTestResult && (
              <div
                className={`p-3.5 rounded-xl border text-xs space-y-1.5 ${
                  jobTestResult.success
                    ? "bg-emerald-50 border-emerald-200 text-emerald-800"
                    : "bg-red-50 border-red-200 text-red-800"
                }`}
              >
                <div className="flex items-center space-x-2 font-bold">
                  {jobTestResult.success ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                  ) : (
                    <XCircle className="w-4 h-4 text-red-600 flex-shrink-0" />
                  )}
                  <span>
                    {jobTestResult.success ? "HTTP 201 Created" : `HTTP 403 (${jobTestResult.code})`}
                  </span>
                </div>
                <p className="leading-relaxed">{jobTestResult.message}</p>
              </div>
            )}
          </div>

          {/* Current Submitted Dossier Info */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500">
              Submitted Dossier Overview
            </h3>

            <div className="space-y-3 text-xs">
              <div className="flex justify-between py-1.5 border-b border-slate-100">
                <span className="text-slate-500">Verification Status:</span>
                <span className="font-bold">
                  {statusData?.verification_status || "PENDING"}
                </span>
              </div>

              <div className="flex justify-between py-1.5 border-b border-slate-100">
                <span className="text-slate-500">Account Verified:</span>
                <span className={`font-semibold ${statusData?.is_verified ? "text-emerald-600" : "text-amber-600"}`}>
                  {statusData?.is_verified ? "Yes (Verified)" : "No (Pending)"}
                </span>
              </div>

              <div className="py-1.5 border-b border-slate-100 space-y-1">
                <span className="text-slate-500">Trade License:</span>
                {statusData?.trade_license_url ? (
                  <a
                    href={statusData.trade_license_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center space-x-1 text-purple-600 hover:text-purple-800 font-medium truncate"
                  >
                    <span className="truncate">{statusData.trade_license_url}</span>
                    <ExternalLink className="w-3 h-3 flex-shrink-0" />
                  </a>
                ) : (
                  <p className="text-slate-400 italic">Not submitted yet</p>
                )}
              </div>

              <div className="flex justify-between py-1.5">
                <span className="text-slate-500">Corporate Email:</span>
                <span className="font-mono text-slate-700">{user?.email}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CompanyVerification;
