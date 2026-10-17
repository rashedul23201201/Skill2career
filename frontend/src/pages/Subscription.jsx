import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import subscriptionService from "../services/subscriptionService";
import { ROUTES } from "../constants";
import {
  ShieldCheck,
  Check,
  Settings,
  Calendar,
  CreditCard,
  Download,
  AlertCircle,
  CheckCircle2,
  X,
  FileText,
  Loader2,
  Sparkles,
  ArrowRight,
  ChevronLeft,
  ChevronRight,
  Info,
} from "lucide-react";

export const Subscription = () => {
  const { user } = useAuth();

  const [loading, setLoading] = useState(true);
  const [plans, setPlans] = useState([]);
  const [currentSub, setCurrentSub] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [entitlements, setEntitlements] = useState(null);
  const [error, setError] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);

  // Modal states
  const [selectedPlanForCheckout, setSelectedPlanForCheckout] = useState(null);
  const [paymentMethod, setPaymentMethod] = useState("bKash Auto-Debit");
  const [isProcessingCheckout, setIsProcessingCheckout] = useState(false);

  const [isManageModalOpen, setIsManageModalOpen] = useState(false);
  const [isCancelling, setIsCancelling] = useState(false);

  const [activeInvoice, setActiveInvoice] = useState(null);
  const [isLoadingInvoice, setIsLoadingInvoice] = useState(false);

  // Pagination for Payment History
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 5;

  const loadSubscriptionData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [plansRes, mySubRes, txnsRes, entRes] = await Promise.all([
        subscriptionService.getPlans(),
        subscriptionService.getMySubscription(),
        subscriptionService.getMyTransactions(),
        subscriptionService.getEntitlements(),
      ]);

      if (plansRes?.success) setPlans(plansRes.data || []);
      if (mySubRes?.success) setCurrentSub(mySubRes.data || null);
      if (txnsRes?.success) setTransactions(txnsRes.data || []);
      if (entRes?.success) setEntitlements(entRes.data || null);
    } catch (err) {
      console.error("Failed to load subscription data:", err);
      setError(err?.response?.data?.message || "Failed to load subscription information.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSubscriptionData();
  }, []);

  const handleSelectPlan = async () => {
    if (!selectedPlanForCheckout) return;

    try {
      setIsProcessingCheckout(true);
      setError(null);
      const res = await subscriptionService.selectPlan({
        plan_id: selectedPlanForCheckout.id,
        plan_code: selectedPlanForCheckout.code,
        payment_gateway: "SIMULATED",
        payment_method: paymentMethod,
      });

      if (res?.success) {
        setSuccessMsg(`Successfully activated ${selectedPlanForCheckout.name} plan!`);
        setSelectedPlanForCheckout(null);
        await loadSubscriptionData();
        setTimeout(() => setSuccessMsg(null), 5000);
      }
    } catch (err) {
      setError(err?.response?.data?.message || "Failed to update subscription.");
    } finally {
      setIsProcessingCheckout(false);
    }
  };

  const handleCancelSubscription = async () => {
    try {
      setIsCancelling(true);
      setError(null);
      const res = await subscriptionService.cancelSubscription({
        reason: "User requested downgrade from billing portal",
      });

      if (res?.success) {
        setSuccessMsg("Subscription cancelled. Your account has reverted to the Free tier.");
        setIsManageModalOpen(false);
        await loadSubscriptionData();
        setTimeout(() => setSuccessMsg(null), 5000);
      }
    } catch (err) {
      setError(err?.response?.data?.message || "Failed to cancel subscription.");
    } finally {
      setIsCancelling(false);
    }
  };

  const handleViewInvoice = async (txnId) => {
    try {
      setIsLoadingInvoice(true);
      const res = await subscriptionService.getInvoice(txnId);
      if (res?.success) {
        setActiveInvoice(res.data);
      }
    } catch (err) {
      setError(err?.response?.data?.message || "Failed to retrieve tax invoice.");
    } finally {
      setIsLoadingInvoice(false);
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return "N/A";
    const d = new Date(dateStr);
    return d.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  // Pagination calculation
  const totalPages = Math.ceil(transactions.length / pageSize) || 1;
  const paginatedTransactions = transactions.slice(
    (currentPage - 1) * pageSize,
    currentPage * pageSize
  );

  const activePlanCode = currentSub?.plan?.code || "FREE";
  const activePlanName = currentSub?.plan?.name || "Free";
  const activePrice = currentSub?.plan?.price || 0;
  const activeCycle = currentSub?.plan?.billing_cycle || "forever";

  return (
    <div className="min-h-screen bg-[#F8FAFC] py-8 sm:py-12">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8">
        {/* Breadcrumb Navigation */}
        <div className="flex items-center gap-2 text-xs font-semibold text-slate-500">
          <div className="w-5 h-5 rounded-md bg-blue-50 text-blue-600 flex items-center justify-center">
            <CreditCard className="w-3.5 h-3.5" />
          </div>
          <span>Account &amp; Billing</span>
          <span className="text-slate-300">/</span>
          <span className="text-slate-900 font-bold">Subscription</span>
        </div>

        {/* Page Header */}
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-navy-950 font-heading tracking-tight">
            Subscription &amp; Payment
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Manage your subscription tier, billing cycles, and access payment receipts.
          </p>
        </div>

        {/* Feedback Alerts */}
        {error && (
          <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0 text-red-500" />
              <span>{error}</span>
            </div>
            <button onClick={() => setError(null)} className="text-red-400 hover:text-red-600">
              <X className="w-4 h-4" />
            </button>
          </div>
        )}

        {successMsg && (
          <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-sm flex items-center justify-between">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-600" />
              <span>{successMsg}</span>
            </div>
            <button onClick={() => setSuccessMsg(null)} className="text-emerald-500 hover:text-emerald-700">
              <X className="w-4 h-4" />
            </button>
          </div>
        )}

        {loading ? (
          <div className="flex flex-col items-center justify-center py-20 bg-white rounded-2xl border border-slate-200">
            <Loader2 className="w-8 h-8 text-blue-600 animate-spin mb-3" />
            <p className="text-sm font-semibold text-navy-950">Loading subscription details...</p>
          </div>
        ) : (
          <>
            {/* Top Card: Current Plan Banner */}
            <div className="bg-white rounded-2xl p-6 sm:p-7 border border-slate-200/90 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-5">
              <div className="flex items-start sm:items-center gap-4">
                <div className="w-12 h-12 rounded-xl bg-emerald-50 border border-emerald-200/60 flex items-center justify-center text-emerald-600 shrink-0">
                  <Check className="w-6 h-6 stroke-[3]" />
                </div>
                <div className="space-y-1">
                  <div className="flex items-center gap-2.5 flex-wrap">
                    <h2 className="text-base sm:text-lg font-bold text-navy-950 font-heading">
                      Current Plan: {activePlanName}
                    </h2>
                    <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-50 text-emerald-700 border border-emerald-200/80">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                      Active
                    </span>
                  </div>
                  <div className="flex items-baseline gap-1.5">
                    <span className="text-2xl font-black text-navy-950 font-heading">
                      ৳{activePrice}
                    </span>
                    <span className="text-xs text-slate-500 font-medium">
                      / {activeCycle.toLowerCase()}
                    </span>
                  </div>
                  <div className="flex items-center gap-1.5 text-xs text-slate-500 pt-0.5">
                    <Calendar className="w-3.5 h-3.5 text-slate-400" />
                    <span>
                      {currentSub?.expires_at
                        ? `Next billing date: ${formatDate(currentSub.expires_at)} · Via bKash Auto-Debit`
                        : "Free Tier · Lifetime standard access"}
                    </span>
                  </div>
                </div>
              </div>

              {/* Manage Plan Button */}
              <div className="shrink-0 self-start sm:self-center">
                <button
                  type="button"
                  onClick={() => setIsManageModalOpen(true)}
                  className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-white text-xs sm:text-sm font-semibold transition-all shadow-xs active:scale-98"
                >
                  <Settings className="w-4 h-4 text-slate-300" />
                  <span>Manage Plan</span>
                </button>
              </div>
            </div>

            {/* Section: Available Plans */}
            <div className="space-y-4">
              <div>
                <h2 className="text-lg font-bold text-navy-950 font-heading">
                  Available Plans
                </h2>
                <p className="text-xs sm:text-sm text-slate-500">
                  Switch tier at any time. Changes take effect at the start of your next billing cycle.
                </p>
              </div>

              {/* Plan Cards 3-Column Grid */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-stretch">
                {plans.map((plan) => {
                  const isCurrent = activePlanCode === plan.code;
                  const isMonthly = plan.code === "PRO_MONTHLY";

                  return (
                    <div
                      key={plan.id}
                      className={`relative flex flex-col justify-between rounded-2xl p-6 sm:p-7 transition-all ${
                        isMonthly
                          ? "bg-white border-2 border-emerald-500 shadow-md ring-4 ring-emerald-500/10"
                          : "bg-white border border-slate-200/90 shadow-2xs hover:border-slate-300"
                      }`}
                    >

                      <div className="space-y-4">
                        <div>
                          <h3 className="text-base font-bold text-navy-950 font-heading">
                            {plan.name}
                          </h3>
                          <div className="flex items-baseline gap-1.5 mt-2">
                            <span className="text-3xl font-black text-navy-950 font-heading">
                              ৳{plan.price.toLocaleString()}
                            </span>
                            <span className="text-xs text-slate-500 font-medium">
                              / {plan.billing_cycle === "FREE" ? "forever" : plan.billing_cycle.toLowerCase()}
                            </span>
                          </div>
                          <p className="text-xs text-slate-500 leading-relaxed mt-2 min-h-[36px]">
                            {plan.description}
                          </p>
                        </div>

                        <div className="pt-2 border-t border-slate-100">
                          <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-3">
                            Included:
                          </p>
                          <ul className="space-y-2.5">
                            {(plan.features || []).map((feat, idx) => (
                              <li key={idx} className="flex items-start gap-2.5 text-xs text-slate-700">
                                <div className="w-4 h-4 rounded-full bg-emerald-50 text-emerald-600 flex items-center justify-center shrink-0 mt-0.5">
                                  <Check className="w-2.5 h-2.5 stroke-[3]" />
                                </div>
                                <span className="leading-snug">{feat}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      </div>

                      {/* Card Action Button */}
                      <div className="pt-6 mt-6 border-t border-slate-100">
                        {isCurrent ? (
                          <button
                            type="button"
                            disabled
                            className="w-full py-2.5 px-4 rounded-xl text-xs sm:text-sm font-semibold bg-emerald-600 text-white flex items-center justify-center gap-1.5 cursor-default shadow-xs"
                          >
                            <Check className="w-4 h-4 stroke-[2.5]" />
                            <span>Current Plan</span>
                          </button>
                        ) : (
                          <button
                            type="button"
                            onClick={() => setSelectedPlanForCheckout(plan)}
                            className={`w-full py-2.5 px-4 rounded-xl text-xs sm:text-sm font-semibold transition-all ${
                              isMonthly
                                ? "bg-slate-900 hover:bg-slate-800 text-white shadow-xs"
                                : "border border-slate-200 hover:bg-slate-50 text-slate-800"
                            }`}
                          >
                            Choose Plan
                          </button>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Section: Payment History */}
            <div className="bg-white rounded-2xl border border-slate-200/90 shadow-2xs overflow-hidden">
              <div className="p-6 border-b border-slate-100">
                <h2 className="text-base font-bold text-navy-950 font-heading">
                  Payment History
                </h2>
                <p className="text-xs text-slate-500 mt-0.5">
                  Download official tax invoices and review your previous subscription debits.
                </p>
              </div>

              {transactions.length === 0 ? (
                <div className="py-12 px-4 text-center space-y-2">
                  <div className="w-10 h-10 rounded-full bg-slate-50 text-slate-400 flex items-center justify-center mx-auto">
                    <FileText className="w-5 h-5" />
                  </div>
                  <p className="text-sm font-semibold text-slate-700">No payment history found</p>
                  <p className="text-xs text-slate-400 max-w-sm mx-auto">
                    When you subscribe to a Pro plan, official tax invoices and receipts will be recorded here.
                  </p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead>
                      <tr className="bg-slate-50/70 border-b border-slate-100 text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                        <th className="py-3 px-6">Date</th>
                        <th className="py-3 px-6">Plan</th>
                        <th className="py-3 px-6">Amount</th>
                        <th className="py-3 px-6">Status</th>
                        <th className="py-3 px-6 text-right">Invoice</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {paginatedTransactions.map((txn) => (
                        <tr
                          key={txn.id}
                          onClick={() => handleViewInvoice(txn.id)}
                          title="Click to view tax invoice"
                          className="hover:bg-slate-50/70 transition-colors cursor-pointer"
                        >
                          <td className="py-4 px-6 text-slate-600 font-medium">
                            {formatDate(txn.created_at)}
                          </td>
                          <td className="py-4 px-6 font-semibold text-navy-950">
                            {txn.plan_name || "Monthly Plan"}
                          </td>
                          <td className="py-4 px-6 font-bold text-navy-950">
                            ৳{Number(txn.amount).toLocaleString()}
                          </td>
                          <td className="py-4 px-6">
                            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-bold bg-[#E8F8F0] text-[#059669]">
                              <span className="w-1.5 h-1.5 rounded-full bg-[#059669]" />
                              {txn.status === "SUCCESS" ? "Paid" : txn.status}
                            </span>
                          </td>
                          <td className="py-4 px-6 text-right">
                            <button
                              type="button"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleViewInvoice(txn.id);
                              }}
                              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-100 text-slate-700 font-semibold transition-all shadow-2xs"
                            >
                              <Download className="w-3.5 h-3.5 text-slate-500" />
                              <span>Invoice</span>
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>

                  {/* Pagination Footer */}
                  <div className="flex items-center justify-between px-6 py-4 border-t border-slate-100 bg-white text-xs text-slate-500">
                    <span className="text-slate-400">
                      Showing {(currentPage - 1) * pageSize + 1} to{" "}
                      {Math.min(currentPage * pageSize, transactions.length)} of {transactions.length} debits
                    </span>
                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        disabled={currentPage === 1}
                        onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                        className="text-xs font-medium text-slate-400 hover:text-slate-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                      >
                        &lt;Previous
                      </button>
                      {Array.from({ length: Math.max(totalPages, 1) }, (_, i) => i + 1).map((num) => (
                        <button
                          key={num}
                          type="button"
                          onClick={() => setCurrentPage(num)}
                          className={`w-6 h-6 rounded flex items-center justify-center text-xs font-bold transition-all ${
                            currentPage === num
                              ? "bg-emerald-600 text-white shadow-2xs"
                              : "text-slate-600 hover:text-navy-950 hover:bg-slate-100"
                          }`}
                        >
                          {num}
                        </button>
                      ))}
                      <button
                        type="button"
                        disabled={currentPage === totalPages}
                        onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                        className="text-xs font-medium text-slate-700 hover:text-navy-950 disabled:opacity-40 disabled:cursor-not-allowed transition-colors font-semibold"
                      >
                        Next&gt;
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </>
        )}

        {/* Modal: Checkout / Select Plan Confirmation */}
        {selectedPlanForCheckout && (
          <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 animate-in fade-in duration-150">
            <div className="bg-white rounded-2xl shadow-xl max-w-md w-full p-6 sm:p-7 space-y-5 border border-slate-100">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <div className="w-9 h-9 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center">
                    <Sparkles className="w-5 h-5" />
                  </div>
                  <h3 className="text-lg font-bold text-navy-950 font-heading">
                    Confirm Tier Selection
                  </h3>
                </div>
                <button
                  onClick={() => setSelectedPlanForCheckout(null)}
                  className="text-slate-400 hover:text-slate-600"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Summary Card */}
              <div className="bg-slate-50 rounded-xl p-4 border border-slate-200/80 space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-slate-500 font-medium">Selected Tier:</span>
                  <span className="font-bold text-navy-950">{selectedPlanForCheckout.name} Plan</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-slate-500 font-medium">Billing Cycle:</span>
                  <span className="font-semibold text-slate-800 capitalize">
                    {selectedPlanForCheckout.billing_cycle}
                  </span>
                </div>
                <div className="pt-2 border-t border-slate-200 flex items-center justify-between text-base">
                  <span className="font-bold text-navy-950">Total Amount:</span>
                  <span className="font-black text-emerald-600 text-lg">
                    ৳{selectedPlanForCheckout.price.toLocaleString()}
                  </span>
                </div>
              </div>

              {/* Payment Method Selector if Paid */}
              {selectedPlanForCheckout.price > 0 && (
                <div className="space-y-2">
                  <label className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                    Select Payment Method
                  </label>
                  <div className="grid grid-cols-2 gap-2.5">
                    {[
                      { id: "bKash Auto-Debit", label: "bKash Auto-Debit", color: "text-pink-600" },
                      { id: "Nagad Gateway", label: "Nagad", color: "text-orange-600" },
                    ].map((m) => (
                      <button
                        key={m.id}
                        type="button"
                        onClick={() => setPaymentMethod(m.id)}
                        className={`p-3 rounded-xl border text-left text-xs font-semibold transition-all ${
                          paymentMethod === m.id
                            ? "border-emerald-500 bg-emerald-50/40 text-navy-950 ring-2 ring-emerald-500/20"
                            : "border-slate-200 bg-white hover:bg-slate-50 text-slate-700"
                        }`}
                      >
                        <span className={`block text-[10px] uppercase font-extrabold ${m.color}`}>
                          Mobile Banking
                        </span>
                        <span>{m.label}</span>
                      </button>
                    ))}
                  </div>
                </div>
              )}

              <p className="text-[11px] text-slate-400 leading-relaxed">
                By confirming, your account will be activated immediately with all Pro entitlements including full test access and deep performance analytics.
              </p>

              <div className="flex items-center gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setSelectedPlanForCheckout(null)}
                  className="flex-1 py-2.5 px-4 rounded-xl border border-slate-200 hover:bg-slate-50 text-slate-700 text-xs sm:text-sm font-semibold transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  disabled={isProcessingCheckout}
                  onClick={handleSelectPlan}
                  className="flex-1 py-2.5 px-4 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs sm:text-sm font-semibold transition-colors flex items-center justify-center gap-2 shadow-xs disabled:opacity-50"
                >
                  {isProcessingCheckout ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span>Activating...</span>
                    </>
                  ) : (
                    <span>Confirm &amp; Activate</span>
                  )}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Modal: Manage Plan / Downgrade */}
        {isManageModalOpen && (
          <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 animate-in fade-in duration-150">
            <div className="bg-white rounded-2xl shadow-xl max-w-md w-full p-6 sm:p-7 space-y-5 border border-slate-100">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-bold text-navy-950 font-heading">
                  Manage Subscription
                </h3>
                <button
                  onClick={() => setIsManageModalOpen(false)}
                  className="text-slate-400 hover:text-slate-600"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80 text-xs space-y-2">
                <div className="flex justify-between">
                  <span className="text-slate-500">Tier:</span>
                  <span className="font-bold text-navy-950">{activePlanName}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Auto-Renewal:</span>
                  <span className="font-semibold text-emerald-600">
                    {currentSub?.auto_renew ? "Enabled" : "Disabled"}
                  </span>
                </div>
                {currentSub?.expires_at && (
                  <div className="flex justify-between">
                    <span className="text-slate-500">Billing Date:</span>
                    <span className="font-semibold text-slate-800">
                      {formatDate(currentSub.expires_at)}
                    </span>
                  </div>
                )}
              </div>

              {activePlanCode !== "FREE" ? (
                <div className="space-y-3">
                  <p className="text-xs text-slate-600 leading-relaxed">
                    Cancelling your subscription will turn off automatic renewal. You will be reverted to the Free plan.
                  </p>
                  <button
                    type="button"
                    disabled={isCancelling}
                    onClick={handleCancelSubscription}
                    className="w-full py-2.5 px-4 rounded-xl bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 text-xs sm:text-sm font-semibold transition-colors flex items-center justify-center gap-2"
                  >
                    {isCancelling ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        <span>Processing Cancellation...</span>
                      </>
                    ) : (
                      <span>Cancel Subscription &amp; Downgrade to Free</span>
                    )}
                  </button>
                </div>
              ) : (
                <p className="text-xs text-slate-500">
                  You are currently on the Free tier. Choose a Pro plan from the catalog above to unlock premium mock tests and deep performance analytics.
                </p>
              )}

              <div className="pt-2">
                <button
                  type="button"
                  onClick={() => setIsManageModalOpen(false)}
                  className="w-full py-2.5 px-4 rounded-xl border border-slate-200 hover:bg-slate-50 text-slate-700 text-xs sm:text-sm font-semibold transition-colors"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Modal: Official Tax Invoice */}
        {activeInvoice && (
          <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 animate-in fade-in duration-150">
            <div className="bg-white rounded-2xl shadow-xl max-w-lg w-full p-6 sm:p-8 space-y-6 border border-slate-100">
              <div className="flex items-center justify-between border-b border-slate-100 pb-4">
                <div>
                  <h4 className="text-base font-black text-navy-950 tracking-tight font-heading">
                    SKILL2CAREER
                  </h4>
                  <p className="text-[10px] text-slate-400 uppercase tracking-widest font-bold">
                    Official Tax Receipt
                  </p>
                </div>
                <button
                  onClick={() => setActiveInvoice(null)}
                  className="text-slate-400 hover:text-slate-600"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Invoice Meta */}
              <div className="grid grid-cols-2 gap-4 text-xs">
                <div>
                  <p className="text-slate-400 font-medium">Invoice Number</p>
                  <p className="font-bold text-navy-950 text-sm mt-0.5">{activeInvoice.invoice_number}</p>
                </div>
                <div>
                  <p className="text-slate-400 font-medium">Transaction Ref</p>
                  <p className="font-semibold text-slate-700 font-mono mt-0.5">{activeInvoice.transaction_ref}</p>
                </div>
                <div>
                  <p className="text-slate-400 font-medium">Billed To</p>
                  <p className="font-bold text-navy-950 mt-0.5">{activeInvoice.user_name}</p>
                  <p className="text-slate-500 text-[11px]">{activeInvoice.user_email}</p>
                </div>
                <div>
                  <p className="text-slate-400 font-medium">Date &amp; Gateway</p>
                  <p className="font-semibold text-slate-700 mt-0.5">{formatDate(activeInvoice.date)}</p>
                  <p className="text-slate-500 text-[11px]">{activeInvoice.payment_method}</p>
                </div>
              </div>

              {/* Line Item Table */}
              <div className="bg-slate-50 rounded-xl p-4 border border-slate-200/80">
                <div className="flex justify-between text-xs font-bold text-slate-500 uppercase tracking-wider pb-2 border-b border-slate-200">
                  <span>Description</span>
                  <span>Amount</span>
                </div>
                <div className="flex justify-between text-sm font-semibold text-navy-950 pt-2.5">
                  <span>{activeInvoice.plan_name}</span>
                  <span>৳{activeInvoice.amount.toLocaleString()}</span>
                </div>
                <div className="flex justify-between text-base font-bold text-navy-950 pt-3 mt-3 border-t border-slate-200">
                  <span>Total Paid (BDT)</span>
                  <span className="text-emerald-600 font-black">৳{activeInvoice.amount.toLocaleString()}</span>
                </div>
              </div>

              <div className="flex items-center gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => window.print()}
                  className="flex-1 py-2.5 px-4 rounded-xl bg-slate-900 hover:bg-slate-800 text-white text-xs sm:text-sm font-semibold transition-all flex items-center justify-center gap-2 shadow-xs"
                >
                  <Download className="w-4 h-4" />
                  <span>Print / Save PDF</span>
                </button>
                <button
                  type="button"
                  onClick={() => setActiveInvoice(null)}
                  className="py-2.5 px-5 rounded-xl border border-slate-200 hover:bg-slate-50 text-slate-700 text-xs sm:text-sm font-semibold transition-colors"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Subscription;
