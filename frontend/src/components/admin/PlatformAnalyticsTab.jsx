import React, { useState, useEffect } from "react";
import adminService from "../../services/adminService";
import {
  TrendingUp,
  DollarSign,
  Briefcase,
  Users,
  Calendar,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Building2,
  CreditCard,
  ShieldCheck,
  Clock,
  ArrowUpRight,
  Filter,
} from "lucide-react";

export const PlatformAnalyticsTab = () => {
  const [revenue, setRevenue] = useState(null);
  const [recruitment, setRecruitment] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);

  const fetchAnalytics = async (isManual = false) => {
    try {
      if (isManual) setRefreshing(true);
      else setLoading(true);
      setError(null);

      const [revRes, recRes] = await Promise.all([
        adminService.getRevenueAnalytics(),
        adminService.getRecruitmentSummary(),
      ]);

      if (revRes?.data) setRevenue(revRes.data);
      if (recRes?.data) setRecruitment(recRes.data);
    } catch (err) {
      console.error("Failed to load platform analytics:", err);
      setError("Unable to load platform analytics telemetry. Please verify backend connection.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat("en-BD", {
      style: "currency",
      currency: "BDT",
      minimumFractionDigits: 0,
      maximumFractionDigits: 2,
    }).format(amount || 0);
  };

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

  if (loading && !refreshing) {
    return (
      <div className="py-16 text-center space-y-4">
        <RefreshCw className="w-8 h-8 mx-auto text-blue-600 animate-spin" />
        <p className="text-sm text-slate-500 font-medium">Aggregating platform analytics and financial telemetry...</p>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Tab Header with Refresh Control */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center space-x-2">
            <h2 className="text-xl font-extrabold text-navy-950 font-heading">
              Platform Analytics & Financial Telemetry
            </h2>
            <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-bold bg-blue-100 text-blue-800">
              SKL-23
            </span>
          </div>
          <p className="text-xs text-slate-500">
            Real-time monetization revenue, payment gateway distributions, and hiring partner pipelines
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            type="button"
            onClick={() => fetchAnalytics(true)}
            disabled={refreshing}
            className="inline-flex items-center space-x-2 px-3.5 py-2 text-xs font-semibold rounded-lg border border-slate-300 bg-white hover:bg-slate-50 text-slate-700 transition-colors shadow-sm"
          >
            <RefreshCw className={`w-3.5 h-3.5 text-blue-600 ${refreshing ? "animate-spin" : ""}`} />
            <span>{refreshing ? "Refreshing..." : "Refresh Analytics"}</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-crimson-50 border border-crimson-200 text-crimson-700 text-sm flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Top 5 KPI Metrics Strip */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        {/* Metric 1: Total Revenue */}
        <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm hover:border-emerald-300 transition-all">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
              Platform Revenue
            </span>
            <div className="w-8 h-8 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center">
              <DollarSign className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            <h3 className="text-2xl font-black text-navy-950 font-heading">
              {formatCurrency(revenue?.total_revenue)}
            </h3>
            <div className="mt-1 flex items-center space-x-1.5 text-[11px]">
              <span className="text-emerald-700 font-semibold bg-emerald-50 px-1.5 py-0.5 rounded">
                {revenue?.success_rate || 0}% Success
              </span>
              <span className="text-slate-400">·</span>
              <span className="text-slate-500 font-medium">
                {revenue?.successful_transactions || 0} paid
              </span>
            </div>
          </div>
        </div>

        {/* Metric 2: Active Subscriptions */}
        <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm hover:border-blue-300 transition-all">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
              Active Subscribers
            </span>
            <div className="w-8 h-8 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center">
              <Users className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            <h3 className="text-2xl font-black text-navy-950 font-heading">
              {revenue?.active_subscriptions || 0}
            </h3>
            <p className="mt-1 text-[11px] text-slate-500">
              {revenue?.subscriptions_by_status?.CANCELLED || 0} cancelled · {revenue?.subscriptions_by_status?.EXPIRED || 0} expired
            </p>
          </div>
        </div>

        {/* Metric 3: Total Job Postings */}
        <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm hover:border-purple-300 transition-all">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
              Job Vacancies
            </span>
            <div className="w-8 h-8 rounded-lg bg-purple-50 text-purple-600 flex items-center justify-center">
              <Briefcase className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            <h3 className="text-2xl font-black text-navy-950 font-heading">
              {recruitment?.total_jobs || 0}
            </h3>
            <p className="mt-1 text-[11px] text-purple-700 font-medium">
              {recruitment?.active_jobs || 0} active openings
            </p>
          </div>
        </div>

        {/* Metric 4: Total Candidates */}
        <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm hover:border-amber-300 transition-all">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
              Job Applications
            </span>
            <div className="w-8 h-8 rounded-lg bg-amber-50 text-amber-600 flex items-center justify-center">
              <TrendingUp className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            <h3 className="text-2xl font-black text-navy-950 font-heading">
              {recruitment?.total_applications || 0}
            </h3>
            <p className="mt-1 text-[11px] text-amber-700 font-medium">
              {recruitment?.applications_by_status?.SHORTLISTED || 0} shortlisted
            </p>
          </div>
        </div>

        {/* Metric 5: Interviews Pipeline */}
        <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm hover:border-teal-300 transition-all">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
              Interviews Scheduled
            </span>
            <div className="w-8 h-8 rounded-lg bg-teal-50 text-teal-600 flex items-center justify-center">
              <Calendar className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            <h3 className="text-2xl font-black text-navy-950 font-heading">
              {recruitment?.total_interviews || 0}
            </h3>
            <p className="mt-1 text-[11px] text-teal-700 font-medium">
              {recruitment?.interviews_by_status?.COMPLETED || 0} completed
            </p>
          </div>
        </div>
      </div>

      {/* Two Column Section: Financial Telemetry & Recruitment Pipeline */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Column 1: Financial & Gateway Telemetry (SKL-20 / SKL-23) */}
        <div className="space-y-6">
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-6">
            <div className="border-b border-slate-100 pb-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2.5">
                  <div className="w-8 h-8 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center">
                    <CreditCard className="w-4 h-4" />
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-navy-950 font-heading">
                      Payment Gateway Distributions
                    </h3>
                    <p className="text-xs text-slate-500">
                      Settlement breakdown across SSLCommerz, Global Gateway, and Sandbox
                    </p>
                  </div>
                </div>
                <span className="px-2.5 py-1 rounded-full text-[11px] font-bold bg-emerald-100 text-emerald-800">
                  {revenue?.total_transactions || 0} Total Txns
                </span>
              </div>
            </div>

            {/* Gateways Breakdown */}
            <div className="space-y-4">
              {revenue?.revenue_by_gateway?.length === 0 ? (
                <p className="text-xs text-slate-400 py-4 text-center">No transactions recorded yet.</p>
              ) : (
                revenue?.revenue_by_gateway?.map((gw) => {
                  const pct =
                    revenue.total_revenue > 0
                      ? Math.round((gw.total_amount / revenue.total_revenue) * 100)
                      : 0;
                  return (
                    <div key={gw.gateway} className="space-y-1.5">
                      <div className="flex items-center justify-between text-xs">
                        <span className="font-bold text-navy-900">{gw.gateway}</span>
                        <div className="space-x-2 font-medium">
                          <span className="text-slate-500">{gw.count} txns</span>
                          <span className="text-navy-950 font-bold">
                            {formatCurrency(gw.total_amount)}
                          </span>
                          <span className="text-slate-400">({pct}%)</span>
                        </div>
                      </div>
                      <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                        <div
                          className="bg-emerald-500 h-2 rounded-full transition-all duration-500"
                          style={{ width: `${Math.min(100, Math.max(5, pct))}%` }}
                        />
                      </div>
                    </div>
                  );
                })
              )}
            </div>

            {/* Subscription Plans Breakdown */}
            <div className="pt-4 border-t border-slate-100">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">
                Subscription Plan Adoption
              </h4>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                {revenue?.revenue_by_plan?.map((plan) => (
                  <div key={plan.plan_code} className="p-3.5 rounded-xl bg-slate-50 border border-slate-100">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-navy-900">{plan.plan_name}</span>
                      <span className="text-[10px] font-semibold text-slate-500">{plan.plan_code}</span>
                    </div>
                    <div className="mt-2">
                      <span className="text-lg font-extrabold text-navy-950">
                        {plan.subscriber_count}
                      </span>
                      <span className="text-[11px] text-slate-500 ml-1">subscribers</span>
                    </div>
                    <div className="text-[11px] font-semibold text-emerald-700 mt-1">
                      {formatCurrency(plan.total_revenue)}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Recent Monetized Transactions */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="text-sm font-bold text-navy-950 font-heading">
                Recent Monetized Transactions
              </h3>
              <span className="text-[11px] text-slate-400">Last 10 ledger entries</span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-700">
                <thead className="bg-slate-50 text-slate-500 font-bold uppercase tracking-wider text-[10px] border-b border-slate-200">
                  <tr>
                    <th className="py-2.5 px-3">Reference & User</th>
                    <th className="py-2.5 px-3">Gateway</th>
                    <th className="py-2.5 px-3 text-right">Amount</th>
                    <th className="py-2.5 px-3 text-right">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {revenue?.recent_transactions?.length === 0 ? (
                    <tr>
                      <td colSpan={4} className="py-6 text-center text-slate-400">
                        No recent transactions found.
                      </td>
                    </tr>
                  ) : (
                    revenue?.recent_transactions?.map((tx) => (
                      <tr key={tx.id} className="hover:bg-slate-50/50 transition-colors">
                        <td className="py-2.5 px-3">
                          <div className="font-bold text-navy-950">{tx.transaction_ref}</div>
                          <div className="text-[11px] text-slate-400 truncate max-w-[150px]">
                            {tx.user_name} ({tx.user_email})
                          </div>
                        </td>
                        <td className="py-2.5 px-3 text-[11px] font-medium text-slate-600">
                          {tx.gateway}
                        </td>
                        <td className="py-2.5 px-3 text-right font-bold text-navy-950">
                          {formatCurrency(tx.amount)}
                        </td>
                        <td className="py-2.5 px-3 text-right">
                          <span
                            className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold ${
                              tx.status === "SUCCESS"
                                ? "bg-emerald-100 text-emerald-800"
                                : tx.status === "PENDING"
                                ? "bg-amber-100 text-amber-800"
                                : "bg-red-100 text-red-800"
                            }`}
                          >
                            {tx.status}
                          </span>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Column 2: Recruitment Pipeline & Talent Flow (SKL-4 / SKL-7 / SKL-9) */}
        <div className="space-y-6">
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-6">
            <div className="border-b border-slate-100 pb-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2.5">
                  <div className="w-8 h-8 rounded-lg bg-purple-50 text-purple-600 flex items-center justify-center">
                    <TrendingUp className="w-4 h-4" />
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-navy-950 font-heading">
                      Candidate Pipeline Funnel
                    </h3>
                    <p className="text-xs text-slate-500">
                      End-to-end applicant progression across recruitment stages
                    </p>
                  </div>
                </div>
                <span className="px-2.5 py-1 rounded-full text-[11px] font-bold bg-purple-100 text-purple-800">
                  {recruitment?.total_applications || 0} Total Candidates
                </span>
              </div>
            </div>

            {/* Visual Funnel */}
            <div className="space-y-3">
              {[
                { stage: "Submitted", count: recruitment?.applications_by_status?.SUBMITTED || 0, color: "bg-blue-500" },
                { stage: "Under Review", count: recruitment?.applications_by_status?.UNDER_REVIEW || 0, color: "bg-indigo-500" },
                { stage: "Shortlisted", count: recruitment?.applications_by_status?.SHORTLISTED || 0, color: "bg-purple-500" },
                { stage: "Interview Scheduled", count: recruitment?.applications_by_status?.INTERVIEW_SCHEDULED || 0, color: "bg-amber-500" },
                { stage: "Offered", count: recruitment?.applications_by_status?.OFFERED || 0, color: "bg-emerald-500" },
                { stage: "Rejected / Withdrawn", count: (recruitment?.applications_by_status?.REJECTED || 0) + (recruitment?.applications_by_status?.WITHDRAWN || 0), color: "bg-slate-400" },
              ].map((item) => {
                const total = recruitment?.total_applications || 0;
                const pct = total > 0 ? Math.round((item.count / total) * 100) : 0;
                return (
                  <div key={item.stage} className="space-y-1">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-semibold text-slate-700">{item.stage}</span>
                      <span className="font-bold text-navy-950">
                        {item.count} <span className="text-slate-400 font-normal">({pct}%)</span>
                      </span>
                    </div>
                    <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                      <div
                        className={`${item.color} h-2 rounded-full transition-all duration-500`}
                        style={{ width: `${Math.min(100, Math.max(item.count > 0 ? 6 : 0, pct))}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Top Hiring Partner Organizations */}
            <div className="pt-4 border-t border-slate-100">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">
                Top Hiring Partner Organizations
              </h4>
              <div className="space-y-2">
                {recruitment?.top_hiring_companies?.length === 0 ? (
                  <p className="text-xs text-slate-400 py-3 text-center">No hiring organizations active.</p>
                ) : (
                  recruitment?.top_hiring_companies?.map((comp) => (
                    <div
                      key={comp.company_id}
                      className="p-3 rounded-xl bg-slate-50 border border-slate-100 flex items-center justify-between text-xs"
                    >
                      <div className="flex items-center space-x-2.5">
                        <div className="w-7 h-7 rounded-lg bg-white border border-slate-200 flex items-center justify-center text-slate-700">
                          <Building2 className="w-3.5 h-3.5" />
                        </div>
                        <div>
                          <div className="font-bold text-navy-950">{comp.company_name}</div>
                          <div className="text-[11px] text-slate-400">Employer #{comp.company_id}</div>
                        </div>
                      </div>
                      <div className="text-right space-x-2 font-medium">
                        <span className="text-purple-700 font-bold bg-purple-50 px-2 py-0.5 rounded">
                          {comp.active_jobs} open jobs
                        </span>
                        <span className="text-slate-600">
                          {comp.total_applications} applicants
                        </span>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>

          {/* Recent Vacancy Postings */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="text-sm font-bold text-navy-950 font-heading">
                Recent Job & Internship Openings
              </h3>
              <span className="text-[11px] text-slate-400">Latest 10 vacancies</span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-700">
                <thead className="bg-slate-50 text-slate-500 font-bold uppercase tracking-wider text-[10px] border-b border-slate-200">
                  <tr>
                    <th className="py-2.5 px-3">Title & Company</th>
                    <th className="py-2.5 px-3">Category</th>
                    <th className="py-2.5 px-3">Mode</th>
                    <th className="py-2.5 px-3 text-right">Applicants</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {recruitment?.recent_job_postings?.length === 0 ? (
                    <tr>
                      <td colSpan={4} className="py-6 text-center text-slate-400">
                        No vacancies posted yet.
                      </td>
                    </tr>
                  ) : (
                    recruitment?.recent_job_postings?.map((j) => (
                      <tr key={j.id} className="hover:bg-slate-50/50 transition-colors">
                        <td className="py-2.5 px-3">
                          <div className="font-bold text-navy-950">{j.title}</div>
                          <div className="text-[11px] text-slate-400">{j.company_name}</div>
                        </td>
                        <td className="py-2.5 px-3 text-[11px] text-slate-600">
                          {j.category}
                        </td>
                        <td className="py-2.5 px-3">
                          <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-100 text-slate-700">
                            {j.work_mode}
                          </span>
                        </td>
                        <td className="py-2.5 px-3 text-right font-bold text-navy-950">
                          {j.applications_count}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PlatformAnalyticsTab;
