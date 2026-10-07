import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import adminService from "../../services/adminService";
import { ROUTES } from "../../constants";
import Button from "../../components/forms/Button";
import {
  Building2,
  ShieldCheck,
  ShieldAlert,
  Clock,
  ExternalLink,
  CheckCircle2,
  XCircle,
  FileText,
  Search,
  RefreshCw,
  ArrowLeft,
  Mail,
  Phone,
  MapPin,
  Globe,
  AlertTriangle,
  Info,
} from "lucide-react";

export const CompanyVerifications = () => {
  const [verifications, setVerifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [actionModal, setActionModal] = useState(null); // { type: 'APPROVE' | 'REJECT', company: item }
  const [adminNotes, setAdminNotes] = useState("");
  const [processing, setProcessing] = useState(false);
  const [notification, setNotification] = useState(null); // { type: 'success' | 'error', text }

  const fetchVerifications = async (isManual = false) => {
    try {
      if (isManual) setRefreshing(true);
      else setLoading(true);

      const res = await adminService.getPendingCompanyVerifications();
      if (res?.data) {
        setVerifications(res.data);
      }
    } catch (err) {
      console.error("Failed to load company verifications:", err);
      setNotification({
        type: "error",
        text: "Could not load verification dossiers. Please ensure backend is running.",
      });
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchVerifications();
  }, []);

  const handleOpenAction = (type, company) => {
    setActionModal({ type, company });
    setAdminNotes(
      type === "APPROVE"
        ? "Official documentation, trade license, and registration verified."
        : ""
    );
  };

  const handleConfirmDecision = async () => {
    if (!actionModal) return;

    if (actionModal.type === "REJECT" && !adminNotes.trim()) {
      setNotification({
        type: "error",
        text: "Please provide a reason or constructive feedback when rejecting a company verification.",
      });
      return;
    }

    try {
      setProcessing(true);
      await adminService.verifyCompany(actionModal.company.company_id, {
        action: actionModal.type,
        notes: adminNotes.trim(),
      });

      setNotification({
        type: "success",
        text: `Company '${actionModal.company.company_name}' was successfully ${
          actionModal.type === "APPROVE" ? "APPROVED and verified" : "REJECTED"
        }.`,
      });

      setActionModal(null);
      setAdminNotes("");
      await fetchVerifications();
    } catch (err) {
      console.error("Failed to process verification:", err);
      setNotification({
        type: "error",
        text: err?.response?.data?.message || "Failed to process verification action.",
      });
    } finally {
      setProcessing(false);
    }
  };

  const filtered = verifications.filter((item) => {
    const matchesSearch =
      item.company_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.email?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.registration_number?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.contact_person?.toLowerCase().includes(searchTerm.toLowerCase());

    if (!matchesSearch) return false;
    if (statusFilter === "ALL") return true;
    return item.verification_status === statusFilter;
  });

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header Banner */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 sm:p-8 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="space-y-2">
          <div className="flex items-center space-x-3">
            <Link
              to={ROUTES.ADMIN_DASHBOARD}
              className="p-2 rounded-xl border border-slate-200 hover:bg-slate-50 text-slate-600 transition-colors"
              title="Return to Admin Console"
            >
              <ArrowLeft className="w-5 h-5" />
            </Link>
            <div className="w-10 h-10 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center shadow-sm">
              <Building2 className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h1 className="text-2xl sm:text-3xl font-extrabold text-navy-950 font-heading">
                  Company Verifications
                </h1>
                <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-100 text-amber-800">
                  SKL-2 Module
                </span>
              </div>
              <p className="text-xs text-slate-500">
                Audit employer credentials, inspect trade licenses, approve corporate registrations, and unlock job-posting access.
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          <Button
            variant="outline"
            size="sm"
            onClick={() => fetchVerifications(true)}
            disabled={refreshing}
            className="flex items-center space-x-2"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? "animate-spin" : ""}`} />
            <span>Refresh</span>
          </Button>
          <Link
            to={ROUTES.ADMIN_USERS}
            className="px-4 py-2 rounded-xl text-xs font-semibold bg-navy-950 text-white hover:bg-navy-900 transition-colors shadow-sm"
          >
            All Users Directory
          </Link>
        </div>
      </div>

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

      {/* Control Bar */}
      <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        {/* Search */}
        <div className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search by company name, registration #, contact..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-4 py-2 rounded-xl text-xs border border-slate-200 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
          />
        </div>

        {/* Counter Badge */}
        <div className="flex items-center space-x-2 text-xs text-slate-600 font-medium">
          <span className="w-2.5 h-2.5 rounded-full bg-amber-500 animate-pulse" />
          <span>
            <strong>{verifications.length}</strong> Dossier{verifications.length !== 1 ? "s" : ""} Awaiting Review
          </span>
        </div>
      </div>

      {/* Dossiers Grid */}
      {loading ? (
        <div className="p-12 text-center bg-white rounded-2xl border border-slate-200">
          <RefreshCw className="w-8 h-8 animate-spin text-purple-600 mx-auto mb-3" />
          <p className="text-sm font-medium text-slate-600">Loading pending verification dossiers...</p>
        </div>
      ) : filtered.length === 0 ? (
        <div className="p-12 text-center bg-white rounded-2xl border border-slate-200 space-y-3">
          <div className="w-12 h-12 rounded-2xl bg-emerald-50 text-emerald-600 flex items-center justify-center mx-auto">
            <CheckCircle2 className="w-6 h-6" />
          </div>
          <h3 className="text-base font-bold text-navy-950 font-heading">
            All Company Submissions Processed
          </h3>
          <p className="text-xs text-slate-500 max-w-md mx-auto">
            There are currently no company verification dossiers awaiting administrative review. Newly registered employers submitting trade licenses will automatically appear here.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {filtered.map((item) => (
            <div
              key={item.company_id}
              className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm hover:border-purple-300 transition-all flex flex-col justify-between space-y-5"
            >
              {/* Card Header */}
              <div className="space-y-2">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-center space-x-3">
                    <div className="w-12 h-12 rounded-xl bg-purple-100 text-purple-700 flex items-center justify-center font-bold text-lg">
                      {item.company_name?.charAt(0) || "C"}
                    </div>
                    <div>
                      <h2 className="text-base font-bold text-navy-950 font-heading">
                        {item.company_name}
                      </h2>
                      <div className="flex items-center space-x-2 text-xs text-slate-500 mt-0.5">
                        <span className="font-mono">ID: #{item.company_id}</span>
                        <span>·</span>
                        <span>{item.industry || "General Tech"}</span>
                        {item.company_size && (
                          <>
                            <span>·</span>
                            <span>{item.company_size} employees</span>
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                  <span className="inline-flex items-center px-2.5 py-1 rounded-full text-[11px] font-bold bg-amber-100 text-amber-800 border border-amber-200">
                    <Clock className="w-3 h-3 mr-1" />
                    PENDING REVIEW
                  </span>
                </div>
              </div>

              {/* Dossier Details Block */}
              <div className="bg-slate-50 rounded-xl p-4 border border-slate-100 space-y-2.5 text-xs">
                {/* Registration Number */}
                <div className="flex justify-between items-center py-1 border-b border-slate-200/60">
                  <span className="text-slate-500 font-medium">Govt / TIN / BIN Reg #:</span>
                  <span className="font-mono font-bold text-navy-900">
                    {item.registration_number || "Not specified"}
                  </span>
                </div>

                {/* Email & Contact Person */}
                <div className="flex justify-between items-center py-1 border-b border-slate-200/60">
                  <span className="text-slate-500 font-medium">Contact Person:</span>
                  <span className="font-semibold text-navy-900">
                    {item.contact_person || "Corporate Representative"}
                  </span>
                </div>

                <div className="flex justify-between items-center py-1 border-b border-slate-200/60">
                  <span className="text-slate-500 font-medium">Corporate Email:</span>
                  <span className="font-mono text-slate-800">{item.email}</span>
                </div>

                {item.contact_phone && (
                  <div className="flex justify-between items-center py-1 border-b border-slate-200/60">
                    <span className="text-slate-500 font-medium">Phone Number:</span>
                    <span className="text-slate-800">{item.contact_phone}</span>
                  </div>
                )}

                {item.office_address && (
                  <div className="flex justify-between items-center py-1 border-b border-slate-200/60">
                    <span className="text-slate-500 font-medium">Office Address:</span>
                    <span className="text-slate-800 text-right max-w-xs truncate">
                      {item.office_address}
                    </span>
                  </div>
                )}

                {item.location && (
                  <div className="flex justify-between items-center py-1 border-b border-slate-200/60">
                    <span className="text-slate-500 font-medium">Location:</span>
                    <span className="text-slate-800">{item.location}</span>
                  </div>
                )}

                {/* Document Links */}
                <div className="pt-2 flex flex-wrap items-center gap-3">
                  {item.trade_license_url ? (
                    <a
                      href={item.trade_license_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-white border border-purple-200 text-purple-700 hover:bg-purple-50 font-semibold transition-colors shadow-2xs"
                    >
                      <FileText className="w-3.5 h-3.5" />
                      <span>Inspect Trade License</span>
                      <ExternalLink className="w-3 h-3 ml-0.5" />
                    </a>
                  ) : (
                    <span className="text-slate-400 italic">No trade license document link</span>
                  )}

                  {item.website_url && (
                    <a
                      href={item.website_url.startsWith("http") ? item.website_url : `https://${item.website_url}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center space-x-1 px-2.5 py-1.5 rounded-lg bg-white border border-slate-200 text-slate-700 hover:bg-slate-100 transition-colors"
                    >
                      <Globe className="w-3 h-3 text-slate-500" />
                      <span>Visit Website</span>
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  )}
                </div>
              </div>

              {/* Action Buttons */}
              <div className="pt-2 flex items-center justify-end space-x-3">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleOpenAction("REJECT", item)}
                  className="text-red-700 border-red-200 hover:bg-red-50 hover:border-red-300"
                >
                  <XCircle className="w-4 h-4 mr-1.5 text-red-600" />
                  <span>Reject with Reason</span>
                </Button>
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => handleOpenAction("APPROVE", item)}
                  className="bg-emerald-600 hover:bg-emerald-700 text-white border-transparent"
                >
                  <CheckCircle2 className="w-4 h-4 mr-1.5" />
                  <span>Approve Verification</span>
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Confirmation & Feedback Modal */}
      {actionModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-navy-950/60 backdrop-blur-xs">
          <div className="bg-white rounded-2xl border border-slate-200 shadow-2xl max-w-lg w-full p-6 sm:p-7 space-y-5 animate-in fade-in zoom-in-95 duration-150">
            <div className="flex items-start justify-between">
              <div className="flex items-center space-x-3">
                <div
                  className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                    actionModal.type === "APPROVE"
                      ? "bg-emerald-100 text-emerald-700"
                      : "bg-red-100 text-red-700"
                  }`}
                >
                  {actionModal.type === "APPROVE" ? (
                    <ShieldCheck className="w-5 h-5" />
                  ) : (
                    <ShieldAlert className="w-5 h-5" />
                  )}
                </div>
                <div>
                  <h3 className="text-lg font-bold text-navy-950 font-heading">
                    {actionModal.type === "APPROVE"
                      ? "Approve Company Verification"
                      : "Reject Company Verification"}
                  </h3>
                  <p className="text-xs text-slate-500">
                    Organization: <strong>{actionModal.company.company_name}</strong>
                  </p>
                </div>
              </div>
              <button
                onClick={() => setActionModal(null)}
                className="text-slate-400 hover:text-slate-600 text-sm font-bold"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3">
              <p className="text-xs text-slate-600 leading-relaxed">
                {actionModal.type === "APPROVE"
                  ? "Approving this dossier will mark the company account as verified, update verification_status to 'APPROVED', and immediately unlock full job & internship publishing privileges across the ecosystem."
                  : "Rejecting will flag the company verification_status as 'REJECTED' and maintain job-posting lockout until a revised dossier is submitted. Please provide feedback below."}
              </p>

              <div>
                <label className="block text-xs font-bold text-navy-900 mb-1">
                  {actionModal.type === "APPROVE"
                    ? "Administrative Verification Notes (Optional)"
                    : "Reason for Rejection / Corrective Instructions (Required)"}
                </label>
                <textarea
                  rows={4}
                  value={adminNotes}
                  onChange={(e) => setAdminNotes(e.target.value)}
                  placeholder={
                    actionModal.type === "APPROVE"
                      ? "e.g., Trade license verified with DNCC registry..."
                      : "e.g., The submitted trade license is expired. Please upload your renewed FY2026 certification."
                  }
                  className="w-full p-3 rounded-xl text-xs border border-slate-200 focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
              </div>
            </div>

            <div className="flex items-center justify-end space-x-3 pt-3 border-t border-slate-100">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setActionModal(null)}
                disabled={processing}
              >
                Cancel
              </Button>
              <Button
                variant="primary"
                size="sm"
                onClick={handleConfirmDecision}
                disabled={processing}
                className={
                  actionModal.type === "APPROVE"
                    ? "bg-emerald-600 hover:bg-emerald-700 text-white"
                    : "bg-red-600 hover:bg-red-700 text-white"
                }
              >
                {processing
                  ? "Submitting..."
                  : actionModal.type === "APPROVE"
                  ? "Confirm Approval"
                  : "Confirm Rejection"}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CompanyVerifications;
