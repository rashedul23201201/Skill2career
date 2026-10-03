import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import authService from "../services/authService";
import Button from "../components/forms/Button";
import { ROUTES } from "../constants";
import {
  User,
  Shield,
  Activity,
  CheckCircle2,
  Calendar,
  Layers,
  Building2,
} from "lucide-react";

export const Dashboard = () => {
  const { user, logout } = useAuth();
  const [healthStatus, setHealthStatus] = useState(null);
  const [healthLoading, setHealthLoading] = useState(false);

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        setHealthLoading(true);
        const data = await authService.checkHealth();
        setHealthStatus(data);
      } catch (err) {
        console.error("Health check error:", err);
        setHealthStatus({ status: "unavailable" });
      } finally {
        setHealthLoading(false);
      }
    };

    fetchHealth();
  }, []);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">
      {/* Welcome Banner */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 sm:p-8 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="space-y-2">
          <div className="flex items-center space-x-3">
            <h1 className="text-2xl sm:text-3xl font-extrabold text-navy-900 font-heading">
              Welcome back, {user?.first_name} {user?.last_name}!
            </h1>
            <span className="px-3 py-1 text-xs font-bold uppercase tracking-wider bg-emerald-100 text-emerald-800 rounded-full">
              {user?.role}
            </span>
          </div>
          <p className="text-sm text-slate-500">
            Account Email: <span className="font-medium text-navy-800">{user?.email}</span> · Account ID: #{user?.id}
          </p>
        </div>

        <div className="flex items-center space-x-3">
          {user?.role === "ADMIN" && (
            <Link
              to={ROUTES.ADMIN_DASHBOARD}
              className="inline-flex items-center space-x-1.5 px-4 py-2 rounded-lg text-xs font-semibold bg-navy-950 text-white hover:bg-navy-900 transition-colors shadow-sm"
            >
              <Shield className="w-3.5 h-3.5 text-emerald-400" />
              <span>Admin Console</span>
            </Link>
          )}
          <Button variant="outline" size="sm" onClick={logout}>
            Sign Out
          </Button>
        </div>
      </div>

      {/* Learner Profile Quick Action Banner (SKL-51) */}
      {user?.role === "LEARNER" && (
        <div className="bg-gradient-to-r from-navy-950 via-blue-950 to-navy-900 rounded-2xl p-6 sm:p-7 text-white shadow-md flex flex-col sm:flex-row sm:items-center justify-between gap-6 relative overflow-hidden">
          <div className="space-y-1.5 z-10">
            <div className="flex items-center space-x-2">
              <span className="px-2.5 py-0.5 rounded-full text-[11px] font-extrabold uppercase tracking-wider bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                SKL-51 Module Active
              </span>
              <span className="text-xs text-blue-200">Personal & Career Management</span>
            </div>
            <h2 className="text-xl sm:text-2xl font-bold font-heading">
              Your Learner Profile & Verified CV
            </h2>
            <p className="text-xs sm:text-sm text-slate-300 max-w-xl">
              Track your dynamic 4-tier profile completion (Basic Info, Education, Skills, and Resume upload) to get noticed by verified hiring partners.
            </p>
          </div>
          <div className="flex items-center space-x-3 z-10 flex-shrink-0">
            <Link
              to={ROUTES.LEARNER_PROFILE}
              className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl text-xs font-bold bg-emerald-500 hover:bg-emerald-600 text-white shadow transition-all hover:shadow-lg"
            >
              <User className="w-4 h-4" />
              <span>Open Learner Profile</span>
            </Link>
          </div>
        </div>
      )}

      {/* Company Profile Quick Action Banner (SKL-3) */}
      {user?.role === "COMPANY" && (
        <div className="bg-gradient-to-r from-navy-950 via-slate-900 to-blue-950 rounded-2xl p-6 sm:p-7 text-white shadow-md flex flex-col sm:flex-row sm:items-center justify-between gap-6 relative overflow-hidden">
          <div className="space-y-1.5 z-10">
            <div className="flex items-center space-x-2">
              <span className="px-2.5 py-0.5 rounded-full text-[11px] font-extrabold uppercase tracking-wider bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                SKL-3 Module Active
              </span>
              <span className="text-xs text-blue-200">Company Profile & Branding Console</span>
            </div>
            <h2 className="text-xl sm:text-2xl font-bold font-heading">
              Company Dashboard & Recruitment Hub
            </h2>
            <p className="text-xs sm:text-sm text-slate-300 max-w-xl">
              Manage your company branding assets (logo & cover banner), verified badges, candidate pipeline, and public profile view for job seekers.
            </p>
          </div>
          <div className="flex items-center space-x-3 z-10 flex-shrink-0">
            <Link
              to={ROUTES.COMPANY_DASHBOARD}
              className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl text-xs font-bold bg-emerald-500 hover:bg-emerald-600 text-white shadow transition-all hover:shadow-lg"
            >
              <Building2 className="w-4 h-4" />
              <span>Open Company Dashboard</span>
            </Link>
          </div>
        </div>
      )}

      {/* Grid of Foundation Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* User Identity Card */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-bold text-navy-900 font-heading">
              Authentication Profile
            </h3>
            <User className="w-5 h-5 text-emerald-600" />
          </div>

          <div className="space-y-2 text-sm">
            <div className="flex justify-between py-1.5 border-b border-slate-100">
              <span className="text-slate-500">Assigned Role:</span>
              <span className="font-semibold text-navy-800">{user?.role}</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-slate-100">
              <span className="text-slate-500">Account Status:</span>
              <span className="inline-flex items-center text-emerald-600 font-medium text-xs">
                <CheckCircle2 className="w-3.5 h-3.5 mr-1" /> Active
              </span>
            </div>
            <div className="flex justify-between py-1.5">
              <span className="text-slate-500">Joined:</span>
              <span className="text-xs text-slate-700">
                {user?.created_at ? new Date(user.created_at).toLocaleDateString() : "Just now"}
              </span>
            </div>
          </div>
        </div>

        {/* API & Backend Health Card */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-bold text-navy-900 font-heading">
              Backend Connectivity
            </h3>
            <Activity className="w-5 h-5 text-emerald-500" />
          </div>

          <div className="space-y-2 text-sm">
            <div className="flex justify-between py-1.5 border-b border-slate-100">
              <span className="text-slate-500">API Endpoint:</span>
              <span className="font-mono text-xs text-navy-700">/api/v1/health</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-slate-100">
              <span className="text-slate-500">Status:</span>
              <span
                className={`font-semibold text-xs px-2 py-0.5 rounded ${
                  healthStatus?.status === "healthy"
                    ? "bg-emerald-100 text-emerald-800"
                    : "bg-amber-100 text-amber-800"
                }`}
              >
                {healthLoading ? "Checking..." : healthStatus?.status || "Connecting..."}
              </span>
            </div>
            <div className="flex justify-between py-1.5">
              <span className="text-slate-500">Environment:</span>
              <span className="text-xs font-mono text-slate-600">
                {healthStatus?.environment || "development"}
              </span>
            </div>
          </div>
        </div>

        {/* Sprint Roadmap Status Card */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-bold text-navy-900 font-heading">
              Sprint Roadmap
            </h3>
            <Calendar className="w-5 h-5 text-navy-900" />
          </div>

          <div className="space-y-2 text-sm">
            <div className="flex justify-between py-1.5 border-b border-slate-100">
              <span className="text-slate-500">Current Phase:</span>
              <span className="font-bold text-emerald-600">Sprint 1 (Active)</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-slate-100">
              <span className="text-slate-500">Planned Sprints:</span>
              <span className="text-navy-800 font-medium">4 Agile Sprints</span>
            </div>
            <div className="flex justify-between py-1.5">
              <span className="text-slate-500">Backlog:</span>
              <span className="text-xs font-medium text-slate-700">36 Jira Tickets</span>
            </div>
          </div>
        </div>
      </div>

      {/* Feature Development Notice */}
      <div className="bg-slate-50 border border-slate-200 rounded-2xl p-6 sm:p-8 space-y-3">
        <div className="flex items-center space-x-2 text-navy-900 font-bold font-heading text-lg">
          <Layers className="w-5 h-5 text-emerald-600" />
          <span>Sprint 1–4 Feature Placeholder</span>
        </div>
        <p className="text-sm text-slate-600 max-w-3xl leading-relaxed">
          The foundation, architecture, authentication, role authorization, and centralized API services are fully operational. Domain modules (Course Management, Assessments, Job Postings, Candidate Tracking, Interview Prep) will be incrementally delivered across upcoming Agile sprints by the 5-developer team.
        </p>
      </div>
    </div>
  );
};

export default Dashboard;
