import React, { useState, useEffect, useCallback } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useAuth } from "../../hooks/useAuth";
import adminService from "../../services/adminService";
import { ROUTES, USER_ROLES } from "../../constants";
import {
  Search,
  CheckCircle2,
  XCircle,
  ArrowLeft,
  RefreshCw,
  AlertTriangle,
  ChevronLeft,
  ChevronRight,
  ShieldAlert,
  X,
} from "lucide-react";

export const UserManagement = () => {
  const { user: currentUser } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();

  // State
  const [users, setUsers] = useState([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(15);
  const [loading, setLoading] = useState(true);

  // Filters initialized from URL parameters if present
  const [searchTerm, setSearchTerm] = useState(() => searchParams.get("search") || "");
  const [roleFilter, setRoleFilter] = useState(() => searchParams.get("role") || "");
  const [statusFilter, setStatusFilter] = useState(() => searchParams.get("status") || "");
  const [verifiedFilter, setVerifiedFilter] = useState(() => searchParams.get("verified") || "");

  // Sync state if URL query parameters change (e.g. clicking Review Companies from Admin Dashboard)
  useEffect(() => {
    const roleParam = searchParams.get("role") || "";
    const statusParam = searchParams.get("status") || "";
    const searchParam = searchParams.get("search") || "";
    setRoleFilter(roleParam);
    setStatusFilter(statusParam);
    if (searchParam) setSearchTerm(searchParam);
    setPage(1);
  }, [searchParams]);

  // Feedback notifications
  const [alert, setAlert] = useState(null);

  const showAlert = useCallback((type, message) => {
    setAlert({ type, message });
    setTimeout(() => {
      setAlert(null);
    }, 4500);
  }, []);

  // Role Change Modal state
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [targetRole, setTargetRole] = useState("");
  const [roleReason, setRoleReason] = useState("");
  const [modalSubmitting, setModalSubmitting] = useState(false);

  // Status toggle loading state
  const [actionLoadingId, setActionLoadingId] = useState(null);

  const fetchUsers = useCallback(async () => {
    try {
      setLoading(true);
      const params = {
        page,
        size: pageSize,
      };

      if (searchTerm.trim()) params.search = searchTerm.trim();
      if (roleFilter) params.role = roleFilter;
      if (statusFilter !== "") params.is_active = statusFilter === "active";
      if (verifiedFilter !== "") params.is_verified = verifiedFilter === "verified";

      const response = await adminService.getUsers(params);
      if (response?.data) {
        setUsers(response.data.items || []);
        setTotal(response.data.total || 0);
        setTotalPages(response.data.total_pages || 1);
      }
    } catch (err) {
      console.error("Failed to load users:", err);
      showAlert("error", "Failed to retrieve user accounts. Please verify your connection.");
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, searchTerm, roleFilter, statusFilter, verifiedFilter, showAlert]);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);


  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setPage(1);
    fetchUsers();
  };

  const handleResetFilters = () => {
    setSearchTerm("");
    setRoleFilter("");
    setStatusFilter("");
    setVerifiedFilter("");
    setSearchParams({});
    setPage(1);
  };

  const handleToggleStatus = async (targetUser) => {
    if (targetUser.id === currentUser?.id && targetUser.is_active) {
      showAlert("error", "Safety constraint: Administrators cannot deactivate their own administrative account.");
      return;
    }

    try {
      setActionLoadingId(targetUser.id);
      const newStatus = !targetUser.is_active;
      await adminService.updateUserStatus(targetUser.id, {
        is_active: newStatus,
        reason: newStatus ? "Administrative re-activation" : "Account suspended by administrator",
      });

      showAlert(
        "success",
        `User ${targetUser.email} has been successfully ${newStatus ? "activated" : "deactivated"}.`
      );

      // Update in local state
      setUsers((prev) =>
        prev.map((u) => (u.id === targetUser.id ? { ...u, is_active: newStatus } : u))
      );
    } catch (err) {
      console.error("Status update error:", err);
      showAlert("error", err.response?.data?.message || "Failed to update user account status.");
    } finally {
      setActionLoadingId(null);
    }
  };

  const openRoleModal = (targetUser) => {
    setSelectedUser(targetUser);
    setTargetRole(targetUser.role);
    setRoleReason("");
    setModalOpen(true);
  };

  const handleConfirmRoleChange = async () => {
    if (!selectedUser || !targetRole) return;

    if (selectedUser.id === currentUser?.id && targetRole !== USER_ROLES.ADMIN) {
      showAlert("error", "You cannot demote your own administrator privileges.");
      return;
    }

    try {
      setModalSubmitting(true);
      await adminService.updateUserRole(selectedUser.id, {
        role: targetRole,
        reason: roleReason.trim() || "Administrative role override",
      });

      showAlert(
        "success",
        `Role for ${selectedUser.email} changed to ${targetRole}. Active sessions revoked.`
      );

      setUsers((prev) =>
        prev.map((u) => (u.id === selectedUser.id ? { ...u, role: targetRole } : u))
      );
      setModalOpen(false);
    } catch (err) {
      console.error("Role update error:", err);
      showAlert("error", err.response?.data?.message || "Failed to update user role.");
    } finally {
      setModalSubmitting(false);
    }
  };

  const getRoleBadge = (role) => {
    switch (role) {
      case USER_ROLES.ADMIN:
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-bold bg-purple-100 text-purple-800">
            ADMIN
          </span>
        );
      case USER_ROLES.COMPANY:
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-bold bg-blue-100 text-blue-800">
            COMPANY
          </span>
        );
      case USER_ROLES.INSTRUCTOR:
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-bold bg-indigo-100 text-indigo-800">
            INSTRUCTOR
          </span>
        );
      case USER_ROLES.LEARNER:
      default:
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800">
            LEARNER
          </span>
        );
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Breadcrumb & Navigation Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2 text-xs font-medium text-slate-500 mb-1">
            <Link to={ROUTES.ADMIN_DASHBOARD} className="hover:text-blue-600 transition-colors">
              Admin Console
            </Link>
            <span>/</span>
            <span className="text-navy-900 font-semibold">User Management</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-navy-950 font-heading">
            User Directory & Access Governance
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Audit user accounts, enforce active security locks, and override RBAC authority (SKL-50/SKL-24)
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <Link
            to={ROUTES.ADMIN_DASHBOARD}
            className="inline-flex items-center space-x-1.5 px-3 py-2 text-xs font-semibold rounded-lg border border-slate-300 bg-white hover:bg-slate-50 text-slate-700 transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Dashboard</span>
          </Link>
          <button
            type="button"
            onClick={fetchUsers}
            disabled={loading}
            className="inline-flex items-center space-x-1.5 px-3 py-2 text-xs font-semibold rounded-lg bg-navy-950 text-white hover:bg-navy-900 transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Alert Banner */}
      {alert && (
        <div
          className={`p-4 rounded-xl text-xs font-medium flex items-center justify-between transition-all ${
            alert.type === "success"
              ? "bg-emerald-50 border border-emerald-200 text-emerald-800"
              : "bg-red-50 border border-red-200 text-red-800"
          }`}
        >
          <div className="flex items-center space-x-2">
            {alert.type === "success" ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
            ) : (
              <AlertTriangle className="w-4 h-4 text-red-600 flex-shrink-0" />
            )}
            <span>{alert.message}</span>
          </div>
          <button
            type="button"
            onClick={() => setAlert(null)}
            className="text-slate-400 hover:text-slate-600"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* Filter and Search Bar */}
      <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm space-y-4">
        <form onSubmit={handleSearchSubmit} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
          {/* Search Input */}
          <div className="relative sm:col-span-2">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 transform -translate-y-1/2" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search by name or email address..."
              className="w-full pl-9 pr-3 py-2 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          {/* Role Filter */}
          <div>
            <select
              value={roleFilter}
              onChange={(e) => {
                setRoleFilter(e.target.value);
                setPage(1);
              }}
              className="w-full px-3 py-2 text-xs rounded-lg border border-slate-200 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Roles</option>
              <option value={USER_ROLES.LEARNER}>Learner</option>
              <option value={USER_ROLES.INSTRUCTOR}>Instructor</option>
              <option value={USER_ROLES.COMPANY}>Company</option>
              <option value={USER_ROLES.ADMIN}>Administrator</option>
            </select>
          </div>

          {/* Status Filter */}
          <div>
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setPage(1);
              }}
              className="w-full px-3 py-2 text-xs rounded-lg border border-slate-200 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Statuses</option>
              <option value="active">Active Only</option>
              <option value="inactive">Inactive Only</option>
            </select>
          </div>

          {/* Verification Filter */}
          <div>
            <select
              value={verifiedFilter}
              onChange={(e) => {
                setVerifiedFilter(e.target.value);
                setPage(1);
              }}
              className="w-full px-3 py-2 text-xs rounded-lg border border-slate-200 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Verification</option>
              <option value="verified">Verified</option>
              <option value="unverified">Unverified</option>
            </select>
          </div>
        </form>

        {(searchTerm || roleFilter || statusFilter || verifiedFilter) && (
          <div className="flex items-center justify-between pt-2 border-t border-slate-100 text-xs text-slate-500">
            <span>
              Filters active. Showing {total} matching user(s).
            </span>
            <button
              type="button"
              onClick={handleResetFilters}
              className="text-blue-600 hover:text-blue-800 font-medium"
            >
              Clear all filters
            </button>
          </div>
        )}
      </div>

      {/* Users Data Table */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 text-xs font-bold uppercase tracking-wider">
                <th className="py-3.5 px-4 sm:px-6">User / Identity</th>
                <th className="py-3.5 px-4">Role</th>
                <th className="py-3.5 px-4">Account Status</th>
                <th className="py-3.5 px-4">Email Verification</th>
                <th className="py-3.5 px-4">Joined Date</th>
                <th className="py-3.5 px-4 sm:px-6 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-xs">
              {loading ? (
                <tr>
                  <td colSpan="6" className="py-12 text-center text-slate-400">
                    <div className="flex flex-col items-center space-y-2">
                      <RefreshCw className="w-5 h-5 animate-spin text-blue-600" />
                      <span>Loading user accounts...</span>
                    </div>
                  </td>
                </tr>
              ) : users.length === 0 ? (
                <tr>
                  <td colSpan="6" className="py-12 text-center text-slate-400">
                    No users matching the selected filters were found.
                  </td>
                </tr>
              ) : (
                users.map((targetUser) => {
                  const isCurrent = targetUser.id === currentUser?.id;
                  const isActionLoading = actionLoadingId === targetUser.id;

                  return (
                    <tr
                      key={targetUser.id}
                      className="hover:bg-slate-50/70 transition-colors"
                    >
                      {/* Name & Email */}
                      <td className="py-3.5 px-4 sm:px-6">
                        <div className="flex items-center space-x-3">
                          <div className="w-8 h-8 rounded-full bg-slate-200 flex items-center justify-center font-bold text-slate-700 flex-shrink-0">
                            {targetUser.first_name?.charAt(0) || "U"}
                          </div>
                          <div>
                            <div className="font-semibold text-navy-950 flex items-center space-x-1.5">
                              <span>
                                {targetUser.first_name} {targetUser.last_name}
                              </span>
                              {isCurrent && (
                                <span className="px-1.5 py-0.2 rounded text-[10px] font-bold bg-slate-200 text-slate-700">
                                  You
                                </span>
                              )}
                            </div>
                            <span className="text-slate-500 font-mono text-[11px]">
                              {targetUser.email}
                            </span>
                          </div>
                        </div>
                      </td>

                      {/* Role Badge */}
                      <td className="py-3.5 px-4">
                        {getRoleBadge(targetUser.role)}
                      </td>

                      {/* Status */}
                      <td className="py-3.5 px-4">
                        {targetUser.is_active ? (
                          <span className="inline-flex items-center space-x-1 text-emerald-700 font-medium">
                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                            <span>Active</span>
                          </span>
                        ) : (
                          <span className="inline-flex items-center space-x-1 text-crimson font-medium">
                            <span className="w-1.5 h-1.5 rounded-full bg-crimson"></span>
                            <span>Suspended</span>
                          </span>
                        )}
                      </td>

                      {/* Email Verification */}
                      <td className="py-3.5 px-4">
                        {targetUser.is_verified ? (
                          <span className="inline-flex items-center space-x-1 text-emerald-700 font-medium">
                            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                            <span>Verified</span>
                          </span>
                        ) : (
                          <span className="inline-flex items-center space-x-1 text-amber-700 font-medium">
                            <XCircle className="w-3.5 h-3.5 text-amber-500" />
                            <span>Unverified</span>
                          </span>
                        )}
                      </td>

                      {/* Joined Date */}
                      <td className="py-3.5 px-4 text-slate-500">
                        {targetUser.created_at
                          ? new Date(targetUser.created_at).toLocaleDateString()
                          : "N/A"}
                      </td>

                      {/* Actions */}
                      <td className="py-3.5 px-4 sm:px-6 text-right">
                        <div className="flex items-center justify-end space-x-2">
                          {/* Role Override Trigger */}
                          <button
                            type="button"
                            onClick={() => openRoleModal(targetUser)}
                            className="px-2.5 py-1 text-xs font-semibold rounded border border-slate-300 bg-white hover:bg-slate-50 text-slate-700 transition-colors"
                          >
                            Change Role
                          </button>

                          {/* Status Toggle Button */}
                          <button
                            type="button"
                            disabled={isActionLoading || (isCurrent && targetUser.is_active)}
                            onClick={() => handleToggleStatus(targetUser)}
                            className={`px-2.5 py-1 text-xs font-semibold rounded transition-colors ${
                              targetUser.is_active
                                ? "bg-red-50 text-red-700 border border-red-200 hover:bg-red-100 disabled:opacity-40"
                                : "bg-emerald-50 text-emerald-700 border border-emerald-200 hover:bg-emerald-100"
                            }`}
                            title={
                              isCurrent && targetUser.is_active
                                ? "Cannot deactivate yourself"
                                : targetUser.is_active
                                ? "Deactivate account"
                                : "Activate account"
                            }
                          >
                            {isActionLoading
                              ? "Updating..."
                              : targetUser.is_active
                              ? "Deactivate"
                              : "Activate"}
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Footer */}
        <div className="p-4 border-t border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs text-slate-500">
          <div>
            Showing {users.length > 0 ? (page - 1) * pageSize + 1 : 0} to{" "}
            {Math.min(page * pageSize, total)} of {total} registered users
          </div>

          <div className="flex items-center space-x-2">
            <button
              type="button"
              disabled={page <= 1 || loading}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              className="p-1.5 rounded border border-slate-200 bg-white hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              title="Previous Page"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="font-semibold text-navy-950 px-2">
              Page {page} of {totalPages || 1}
            </span>
            <button
              type="button"
              disabled={page >= totalPages || loading}
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              className="p-1.5 rounded border border-slate-200 bg-white hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              title="Next Page"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Role Change Modal */}
      {modalOpen && selectedUser && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-navy-950/60 backdrop-blur-sm animate-fade-in">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-5 border border-slate-200">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="flex items-center space-x-2">
                <ShieldAlert className="w-5 h-5 text-blue-600" />
                <h3 className="text-base font-bold text-navy-950 font-heading">
                  Reassign User Role
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setModalOpen(false)}
                className="text-slate-400 hover:text-slate-600"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-4 text-xs">
              <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
                <div className="text-slate-500 font-medium">Selected User:</div>
                <div className="font-bold text-navy-950 text-sm">
                  {selectedUser.first_name} {selectedUser.last_name}
                </div>
                <div className="text-slate-500 font-mono">{selectedUser.email}</div>
                <div className="pt-1 flex items-center space-x-2">
                  <span className="text-slate-500">Current Role:</span>
                  {getRoleBadge(selectedUser.role)}
                </div>
              </div>

              <div>
                <label className="block text-slate-700 font-semibold mb-1">
                  Select New Ecosystem Role:
                </label>
                <select
                  value={targetRole}
                  onChange={(e) => setTargetRole(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 text-xs font-medium focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value={USER_ROLES.LEARNER}>LEARNER (Student / Job Seeker)</option>
                  <option value={USER_ROLES.INSTRUCTOR}>INSTRUCTOR (Course Creator / Mentor)</option>
                  <option value={USER_ROLES.COMPANY}>COMPANY (Corporate Hiring Partner)</option>
                  <option value={USER_ROLES.ADMIN}>ADMIN (System Administrator)</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-700 font-semibold mb-1">
                  Reason for Override (Optional):
                </label>
                <input
                  type="text"
                  value={roleReason}
                  onChange={(e) => setRoleReason(e.target.value)}
                  placeholder="e.g. Instructor credential approved, KYC verified"
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div className="p-3 rounded-xl bg-amber-50 border border-amber-200 text-amber-800 flex items-start space-x-2 leading-relaxed">
                <AlertTriangle className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
                <span>
                  <strong>Security Enforcement:</strong> Changing this user&apos;s role will immediately invalidate all active JWT refresh sessions, forcing them to re-authenticate with their new permission scope.
                </span>
              </div>
            </div>

            <div className="flex items-center justify-end space-x-3 pt-2">
              <button
                type="button"
                onClick={() => setModalOpen(false)}
                className="px-4 py-2 text-xs font-semibold rounded-lg border border-slate-300 text-slate-700 hover:bg-slate-50 transition-colors"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={modalSubmitting || targetRole === selectedUser.role}
                onClick={handleConfirmRoleChange}
                className="px-4 py-2 text-xs font-semibold rounded-lg bg-blue-600 hover:bg-blue-700 text-white disabled:opacity-50 transition-colors"
              >
                {modalSubmitting ? "Updating..." : "Confirm Role Update"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default UserManagement;
