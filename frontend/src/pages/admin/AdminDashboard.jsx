import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import adminService from "../../services/adminService";
import { ROUTES } from "../../constants";
import {
  Users,
  Building2,
  GraduationCap,
  AlertCircle,
  Shield,
  Briefcase,
  BookOpen,
  MessageSquare,
  CreditCard,
  Clock,
  ArrowRight,
  ShieldAlert,
  UserCheck,
  UserX,
  RefreshCw,
} from "lucide-react";

export const AdminDashboard = () => {
  const [stats, setStats] = useState(null);
  const [auditLogs, setAuditLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);

  const fetchDashboardData = async (isManualRefresh = false) => {
    try {
      if (isManualRefresh) setRefreshing(true);
      else setLoading(true);
      setError(null);

      const [statsRes, logsRes] = await Promise.all([
        adminService.getOverviewStats(),
        adminService.getAuditLogs(10),
      ]);

      if (statsRes?.data) setStats(statsRes.data);
      if (logsRes?.data) setAuditLogs(logsRes.data);
    } catch (err) {
      console.error("Failed to load admin dashboard data:", err);
      setError("Unable to load administration telemetry. Please ensure the backend is running.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const formatTimestamp = (dateString) => {
    if (!dateString) return "Recently";
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const getActionBadge = (action) => {
    if (action.includes("STATUS")) {
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-amber-100 text-amber-800">
          Status Override
        </span>
      );
    }
    if (action.includes("ROLE")) {
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-blue-100 text-blue-800">
          Role Reassigned
        </span>
      );
    }
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-slate-100 text-slate-800">
        {action}
      </span>
    );
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header Banner */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 sm:p-8 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="space-y-2">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-navy-950 flex items-center justify-center text-blue-400 shadow-sm">
              <Shield className="w-5 h-5 text-emerald-400" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h1 className="text-2xl sm:text-3xl font-extrabold text-navy-950 font-heading">
                  Admin Dashboard
                </h1>
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider bg-emerald-100 text-emerald-800">
                  Super Admin
                </span>
              </div>
              <p className="text-sm text-slate-500">
                Ecosystem Governance, Role-Based Access Control & Platform Moderation
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          <button
            type="button"
            onClick={() => fetchDashboardData(true)}
            disabled={refreshing}
            className="inline-flex items-center space-x-2 px-3.5 py-2 text-xs font-semibold rounded-lg border border-slate-300 bg-white hover:bg-slate-50 text-slate-700 transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? "animate-spin" : ""}`} />
            <span>{refreshing ? "Refreshing..." : "Refresh Telemetry"}</span>
          </button>
          <Link
            to={ROUTES.ADMIN_USERS}
            className="inline-flex items-center space-x-2 bg-navy-950 hover:bg-navy-900 text-white text-xs font-semibold px-4 py-2 rounded-lg shadow-sm transition-all hover:shadow"
          >
            <Users className="w-3.5 h-3.5 text-emerald-400" />
            <span>Manage Users</span>
          </Link>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-crimson-50 border border-crimson-200 text-crimson-700 text-sm flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* 4 Metric Counters (Admin Dashboard.png) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {/* Metric 1: Total Users */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm hover:border-slate-300 transition-all">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
              Total Users
            </span>
            <div className="w-9 h-9 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center">
              <Users className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-4">
            <h3 className="text-3xl font-extrabold text-navy-950 font-heading">
              {loading ? "--" : stats?.total_users ?? 0}
            </h3>
            <p className="mt-1 text-xs text-slate-500 flex items-center space-x-1">
              <span className="text-emerald-600 font-semibold">
                {stats?.active_users ?? 0} active
              </span>
              <span>·</span>
              <span className="text-slate-500">
                {stats?.inactive_users ?? 0} inactive
              </span>
            </p>
          </div>
        </div>

        {/* Metric 2: Companies */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm hover:border-slate-300 transition-all">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
              Companies
            </span>
            <div className="w-9 h-9 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center">
              <Building2 className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-4">
            <h3 className="text-3xl font-extrabold text-navy-950 font-heading">
              {loading ? "--" : stats?.total_companies ?? 0}
            </h3>
            <p className="mt-1 text-xs text-slate-500">
              Hiring partners & enterprise recruiters
            </p>
          </div>
        </div>

        {/* Metric 3: Active Courses */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm hover:border-slate-300 transition-all">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
              Active Courses
            </span>
            <div className="w-9 h-9 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center">
              <GraduationCap className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-4">
            <h3 className="text-3xl font-extrabold text-navy-950 font-heading">
              {loading ? "--" : stats?.active_courses ?? 0}
            </h3>
            <p className="mt-1 text-xs text-slate-500">
              Verified curriculum modules
            </p>
          </div>
        </div>

        {/* Metric 4: Pending Approvals */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm hover:border-slate-300 transition-all">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
              Pending Approvals
            </span>
            <div className="w-9 h-9 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center">
              <AlertCircle className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-4">
            <h3 className="text-3xl font-extrabold text-navy-950 font-heading">
              {loading ? "--" : stats?.pending_approvals ?? 0}
            </h3>
            <p className="mt-1 text-xs text-amber-700 font-medium">
              {stats?.pending_approvals > 0 ? "Action required by admin" : "All approvals processed"}
            </p>
          </div>
        </div>
      </div>

      {/* Role Breakdown Bar */}
      {stats?.role_breakdown && (
        <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm">
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">
            Ecosystem Role Distribution
          </h4>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-center">
            <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
              <span className="text-xs text-slate-500 font-medium">Learners</span>
              <p className="text-xl font-bold text-navy-950 mt-1">
                {stats.role_breakdown.LEARNER ?? 0}
              </p>
            </div>
            <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
              <span className="text-xs text-slate-500 font-medium">Instructors</span>
              <p className="text-xl font-bold text-navy-950 mt-1">
                {stats.role_breakdown.INSTRUCTOR ?? 0}
              </p>
            </div>
            <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
              <span className="text-xs text-slate-500 font-medium">Companies</span>
              <p className="text-xl font-bold text-navy-950 mt-1">
                {stats.role_breakdown.COMPANY ?? 0}
              </p>
            </div>
            <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
              <span className="text-xs text-slate-500 font-medium">Administrators</span>
              <p className="text-xl font-bold text-navy-950 mt-1">
                {stats.role_breakdown.ADMIN ?? 0}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Platform Management Grid (Admin Dashboard.png) */}
      <div className="space-y-4">
        <div>
          <h2 className="text-lg font-bold text-navy-950 font-heading">
            Platform Management Modules
          </h2>
          <p className="text-xs text-slate-500">
            Administrative controls and operations across all 6 core functional sectors
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Card 1: Users */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm flex flex-col justify-between hover:border-blue-400 hover:shadow-md transition-all">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="w-10 h-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center">
                  <Users className="w-5 h-5" />
                </div>
                <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-50 text-emerald-700">
                  Active
                </span>
              </div>
              <h3 className="text-base font-bold text-navy-900 font-heading">
                Users & Access Control
              </h3>
              <p className="text-xs text-slate-500 leading-relaxed">
                Filter platform users, inspect profile state, toggle active/inactive lockout, and reassign system RBAC permissions.
              </p>
            </div>
            <div className="mt-6 pt-4 border-t border-slate-100">
              <Link
                to={ROUTES.ADMIN_USERS}
                className="inline-flex items-center space-x-1.5 text-xs font-bold text-blue-600 hover:text-blue-800 transition-colors"
              >
                <span>Manage Users</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>

          {/* Card 2: Companies */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm flex flex-col justify-between hover:border-purple-400 hover:shadow-md transition-all">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="w-10 h-10 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center">
                  <Building2 className="w-5 h-5" />
                </div>
                {stats?.pending_approvals > 0 ? (
                  <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-100 text-amber-800">
                    {stats.pending_approvals} Pending
                  </span>
                ) : (
                  <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-slate-100 text-slate-600">
                    Verified
                  </span>
                )}
              </div>
              <h3 className="text-base font-bold text-navy-900 font-heading">
                Companies & Verification
              </h3>
              <p className="text-xs text-slate-500 leading-relaxed">
                Audit employer credentials, inspect trade licenses, approve corporate registrations, and unlock job-posting access.
              </p>
            </div>
            <div className="mt-6 pt-4 border-t border-slate-100">
              <Link
                to={`${ROUTES.ADMIN_USERS}?role=COMPANY`}
                className="inline-flex items-center space-x-1.5 text-xs font-bold text-purple-600 hover:text-purple-800 transition-colors"
              >
                <span>Review Companies</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>

          {/* Card 3: Courses & Materials */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm flex flex-col justify-between hover:border-emerald-400 hover:shadow-md transition-all">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center">
                  <BookOpen className="w-5 h-5" />
                </div>
                <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-blue-50 text-blue-700">
                  Sprint 2
                </span>
              </div>
              <h3 className="text-base font-bold text-navy-900 font-heading">
                Courses & Materials
              </h3>
              <p className="text-xs text-slate-500 leading-relaxed">
                Audit curriculum syllabi, manage course modules, verify instructor materials, and maintain educational quality.
              </p>
            </div>
            <div className="mt-6 pt-4 border-t border-slate-100">
              <Link
                to={ROUTES.COURSES}
                className="inline-flex items-center space-x-1.5 text-xs font-bold text-emerald-600 hover:text-emerald-800 transition-colors"
              >
                <span>Curate Courses</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>

          {/* Card 4: Jobs & Internships */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm flex flex-col justify-between hover:border-slate-300 transition-all">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="w-10 h-10 rounded-xl bg-slate-100 text-slate-700 flex items-center justify-center">
                  <Briefcase className="w-5 h-5" />
                </div>
                <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-slate-100 text-slate-600">
                  Sprint 3
                </span>
              </div>
              <h3 className="text-base font-bold text-navy-900 font-heading">
                Jobs & Internships
              </h3>
              <p className="text-xs text-slate-500 leading-relaxed">
                Oversee verified recruitment listings, ensure wage fairness, prevent fraudulent hiring posts, and audit internship standards.
              </p>
            </div>
            <div className="mt-6 pt-4 border-t border-slate-100">
              <Link
                to={ROUTES.JOBS}
                className="inline-flex items-center space-x-1.5 text-xs font-bold text-slate-700 hover:text-navy-950 transition-colors"
              >
                <span>Audit Postings</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>

          {/* Card 5: Community Forum */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm flex flex-col justify-between hover:border-slate-300 transition-all">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="w-10 h-10 rounded-xl bg-slate-100 text-slate-700 flex items-center justify-center">
                  <MessageSquare className="w-5 h-5" />
                </div>
                <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-slate-100 text-slate-600">
                  Sprint 4
                </span>
              </div>
              <h3 className="text-base font-bold text-navy-900 font-heading">
                Community Forum
              </h3>
              <p className="text-xs text-slate-500 leading-relaxed">
                Moderate public learner discussions, resolve spam complaints, enforce code of conduct, and uphold community guidelines.
              </p>
            </div>
            <div className="mt-6 pt-4 border-t border-slate-100">
              <Link
                to={ROUTES.FORUM}
                className="inline-flex items-center space-x-1.5 text-xs font-bold text-slate-700 hover:text-navy-950 transition-colors"
              >
                <span>Moderate Forum</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>

          {/* Card 6: Payments & Finances */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm flex flex-col justify-between hover:border-slate-300 transition-all">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="w-10 h-10 rounded-xl bg-slate-100 text-slate-700 flex items-center justify-center">
                  <CreditCard className="w-5 h-5" />
                </div>
                <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-slate-100 text-slate-600">
                  Sprint 4
                </span>
              </div>
              <h3 className="text-base font-bold text-navy-900 font-heading">
                Payments & Accounting
              </h3>
              <p className="text-xs text-slate-500 leading-relaxed">
                Monitor bKash / Nagad payment gateway settlements, instructor revenue cuts, and enterprise job-posting subscriptions.
              </p>
            </div>
            <div className="mt-6 pt-4 border-t border-slate-100">
              <span className="text-xs font-medium text-slate-400">
                Integration Scheduled in Sprint 4
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Activity Feed */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 sm:p-8 shadow-sm space-y-5">
        <div className="flex items-center justify-between border-b border-slate-100 pb-4">
          <div className="flex items-center space-x-2.5">
            <Clock className="w-5 h-5 text-slate-600" />
            <h2 className="text-lg font-bold text-navy-950 font-heading">
              Recent Administrative Activity
            </h2>
          </div>
          <span className="text-xs text-slate-400">
            Last {auditLogs.length} logged overrides
          </span>
        </div>

        {auditLogs.length === 0 ? (
          <div className="py-8 text-center text-slate-400 text-xs">
            No administrative status overrides recorded yet.
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {auditLogs.map((log) => (
              <div
                key={log.id}
                className="py-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs"
              >
                <div className="flex items-start sm:items-center space-x-3">
                  <div className="w-8 h-8 rounded-lg bg-slate-100 flex items-center justify-center flex-shrink-0 text-slate-700">
                    {log.action.includes("STATUS") ? (
                      log.details?.new_is_active ? (
                        <UserCheck className="w-4 h-4 text-emerald-600" />
                      ) : (
                        <UserX className="w-4 h-4 text-crimson" />
                      )
                    ) : (
                      <ShieldAlert className="w-4 h-4 text-blue-600" />
                    )}
                  </div>
                  <div>
                    <div className="flex items-center space-x-2">
                      <span className="font-semibold text-navy-950">
                        {log.admin_name || "Admin"}
                      </span>
                      <span className="text-slate-500">
                        {log.action === "STATUS_UPDATE"
                          ? `changed active status for user #${log.target_user_id}`
                          : `updated role for user #${log.target_user_id}`}
                      </span>
                      {getActionBadge(log.action)}
                    </div>
                    {log.details?.reason && (
                      <p className="text-slate-500 mt-0.5">
                        Reason: &ldquo;{log.details.reason}&rdquo;
                      </p>
                    )}
                  </div>
                </div>

                <div className="text-right sm:self-center flex-shrink-0">
                  <span className="text-slate-400 font-medium">
                    {formatTimestamp(log.created_at)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default AdminDashboard;
