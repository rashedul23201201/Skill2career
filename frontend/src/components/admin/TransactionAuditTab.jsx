import React, { useState, useEffect } from "react";
import subscriptionService from "../../services/subscriptionService";
import {
  CreditCard,
  Search,
  Filter,
  RefreshCw,
  CheckCircle2,
  AlertCircle,
  Clock,
  Download,
  ShieldCheck,
  FileText,
  DollarSign,
  TrendingUp,
  X,
  Loader2,
  ArrowUpDown,
  ExternalLink,
} from "lucide-react";

export const TransactionAuditTab = () => {
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);

  // Search & Filters
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [gatewayFilter, setGatewayFilter] = useState("ALL");

  // Selected Transaction for Tax Invoice Modal
  const [selectedInvoice, setSelectedInvoice] = useState(null);
  const [loadingInvoice, setLoadingInvoice] = useState(false);

  // Verifying Transaction ID state
  const [verifyingRef, setVerifyingRef] = useState(null);

  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 8;

  const fetchTransactions = async (isManual = false) => {
    try {
      if (isManual) setRefreshing(true);
      else setLoading(true);
      setError(null);

      const res = await subscriptionService.getAdminTransactions({ limit: 100, offset: 0 });
      if (res?.success) {
        setTransactions(res.data || []);
      }
    } catch (err) {
      console.error("Failed to load admin transactions:", err);
      setError(err?.response?.data?.message || "Failed to load platform transactions.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchTransactions();
  }, []);

  const handleVerify = async (transactionRef) => {
    try {
      setVerifyingRef(transactionRef);
      setError(null);
      const res = await subscriptionService.verifyTransaction({
        transaction_ref: transactionRef,
        status: "SUCCESS",
      });

      if (res?.success) {
        setSuccessMsg(`Transaction ${transactionRef} idempotently verified successfully!`);
        await fetchTransactions(true);
        setTimeout(() => setSuccessMsg(null), 5000);
      }
    } catch (err) {
      setError(err?.response?.data?.message || "Failed to verify transaction.");
    } finally {
      setVerifyingRef(null);
    }
  };

  const handleViewInvoice = async (transactionId) => {
    try {
      setLoadingInvoice(true);
      const res = await subscriptionService.getInvoice(transactionId);
      if (res?.success) {
        setSelectedInvoice(res.data);
      }
    } catch (err) {
      setError(err?.response?.data?.message || "Failed to load tax invoice.");
    } finally {
      setLoadingInvoice(false);
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return "N/A";
    const d = new Date(dateStr);
    return d.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  // Metrics Calculations
  const totalVolume = transactions.length;
  const successfulTxns = transactions.filter((t) => t.status === "SUCCESS");
  const totalRevenueBDT = successfulTxns.reduce((sum, t) => sum + (Number(t.amount) || 0), 0);
  const successRate = totalVolume > 0 ? Math.round((successfulTxns.length / totalVolume) * 100) : 100;
  const pendingCount = transactions.filter((t) => t.status === "PENDING").length;

  // Filtering
  const filteredTransactions = transactions.filter((txn) => {
    const matchesSearch =
      !searchQuery ||
      txn.transaction_ref?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      txn.user_email?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      txn.user_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      txn.plan_name?.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesStatus = statusFilter === "ALL" || txn.status === statusFilter;
    const matchesGateway = gatewayFilter === "ALL" || txn.gateway === gatewayFilter;

    return matchesSearch && matchesStatus && matchesGateway;
  });

  // Pagination calculation
  const totalPages = Math.ceil(filteredTransactions.length / pageSize) || 1;
  const paginatedTransactions = filteredTransactions.slice(
    (currentPage - 1) * pageSize,
    currentPage * pageSize
  );

  return (
    <div className="space-y-6 animate-in fade-in duration-200">
      {/* Alert Banners */}
      {error && (
        <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-xs sm:text-sm flex items-center justify-between">
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
        <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs sm:text-sm flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-600" />
            <span>{successMsg}</span>
          </div>
          <button onClick={() => setSuccessMsg(null)} className="text-emerald-500 hover:text-emerald-700">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* 4 Financial Telemetry Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-5">
        <div className="bg-white rounded-2xl border border-slate-200/90 p-5 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
              Total Volume
            </span>
            <div className="w-8 h-8 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center">
              <FileText className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-2xl font-black text-navy-950 font-heading">
              {totalVolume}
            </span>
            <span className="text-xs text-slate-500 font-medium">transactions</span>
          </div>
        </div>

        <div className="bg-white rounded-2xl border border-slate-200/90 p-5 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
              Total Revenue
            </span>
            <div className="w-8 h-8 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center">
              <DollarSign className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-2xl font-black text-emerald-600 font-heading">
              ৳{totalRevenueBDT.toLocaleString()}
            </span>
            <span className="text-xs text-slate-500 font-medium">BDT</span>
          </div>
        </div>

        <div className="bg-white rounded-2xl border border-slate-200/90 p-5 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
              Success Rate
            </span>
            <div className="w-8 h-8 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center">
              <TrendingUp className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-2xl font-black text-navy-950 font-heading">
              {successRate}%
            </span>
            <span className="text-xs text-slate-500 font-medium">settled</span>
          </div>
        </div>

        <div className="bg-white rounded-2xl border border-slate-200/90 p-5 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
              Pending Verification
            </span>
            <div className="w-8 h-8 rounded-lg bg-amber-50 text-amber-600 flex items-center justify-center">
              <Clock className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-2xl font-black text-amber-600 font-heading">
              {pendingCount}
            </span>
            <span className="text-xs text-slate-500 font-medium">in queue</span>
          </div>
        </div>
      </div>

      {/* Main Ledger Card */}
      <div className="bg-white rounded-2xl border border-slate-200/90 shadow-2xs overflow-hidden">
        {/* Ledger Header & Search Filters */}
        <div className="p-5 sm:p-6 border-b border-slate-100 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h2 className="text-base font-bold text-navy-950 font-heading flex items-center gap-2">
                <CreditCard className="w-4 h-4 text-emerald-600" />
                <span>Financial Transaction Ledger (SKL-21)</span>
              </h2>
              <p className="text-xs text-slate-500 mt-0.5">
                Real-time platform payment records, tax invoices, and idempotent verification hooks.
              </p>
            </div>

            <button
              type="button"
              onClick={() => fetchTransactions(true)}
              disabled={refreshing}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-slate-200 hover:bg-slate-50 text-xs font-semibold text-slate-700 transition-colors self-start sm:self-auto disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? "animate-spin text-emerald-600" : ""}`} />
              <span>Refresh Ledger</span>
            </button>
          </div>

          {/* Search Bar & Dropdowns */}
          <div className="flex flex-col sm:flex-row gap-3 pt-1">
            <div className="relative flex-1">
              <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                placeholder="Search by transaction ref, customer name, email, or plan..."
                value={searchQuery}
                onChange={(e) => {
                  setSearchQuery(e.target.value);
                  setCurrentPage(1);
                }}
                className="w-full pl-9 pr-4 py-2 rounded-xl border border-slate-200 bg-slate-50/50 text-xs text-navy-950 placeholder-slate-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all"
              />
            </div>

            <div className="flex items-center gap-2">
              <select
                value={statusFilter}
                onChange={(e) => {
                  setStatusFilter(e.target.value);
                  setCurrentPage(1);
                }}
                className="px-3 py-2 rounded-xl border border-slate-200 bg-white text-xs font-semibold text-slate-700 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all"
              >
                <option value="ALL">All Statuses</option>
                <option value="SUCCESS">Success / Paid</option>
                <option value="PENDING">Pending</option>
                <option value="FAILED">Failed</option>
              </select>

              <select
                value={gatewayFilter}
                onChange={(e) => {
                  setGatewayFilter(e.target.value);
                  setCurrentPage(1);
                }}
                className="px-3 py-2 rounded-xl border border-slate-200 bg-white text-xs font-semibold text-slate-700 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all"
              >
                <option value="ALL">All Gateways</option>
                <option value="SIMULATED">Simulated</option>
                <option value="BKASH">bKash</option>
                <option value="NAGAD">Nagad</option>
              </select>
            </div>
          </div>
        </div>

        {/* Ledger Table */}
        {loading ? (
          <div className="py-20 flex flex-col items-center justify-center">
            <Loader2 className="w-8 h-8 text-emerald-600 animate-spin mb-3" />
            <p className="text-xs font-semibold text-slate-600">Loading platform transactions...</p>
          </div>
        ) : filteredTransactions.length === 0 ? (
          <div className="py-14 text-center px-4">
            <div className="w-10 h-10 rounded-full bg-slate-100 text-slate-400 flex items-center justify-center mx-auto mb-2">
              <FileText className="w-5 h-5" />
            </div>
            <p className="text-sm font-semibold text-slate-700">No transactions match your query</p>
            <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
              Try adjusting your search terms or filter selection.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="bg-slate-50/70 border-b border-slate-100 text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                  <th className="py-3 px-5">Date</th>
                  <th className="py-3 px-5">Reference ID</th>
                  <th className="py-3 px-5">Customer</th>
                  <th className="py-3 px-5">Plan</th>
                  <th className="py-3 px-5">Amount</th>
                  <th className="py-3 px-5">Gateway</th>
                  <th className="py-3 px-5">Status</th>
                  <th className="py-3 px-5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {paginatedTransactions.map((txn) => {
                  const isSuccess = txn.status === "SUCCESS";
                  const isPending = txn.status === "PENDING";

                  return (
                    <tr key={txn.id} className="hover:bg-slate-50/60 transition-colors">
                      <td className="py-3.5 px-5 text-slate-600 font-medium whitespace-nowrap">
                        {formatDate(txn.created_at)}
                      </td>

                      <td className="py-3.5 px-5 font-mono text-slate-800 font-semibold whitespace-nowrap">
                        {txn.transaction_ref}
                      </td>

                      <td className="py-3.5 px-5">
                        <div className="font-semibold text-navy-950">
                          {txn.user_name || `User #${txn.user_id}`}
                        </div>
                        <div className="text-[11px] text-slate-400 font-mono">
                          {txn.user_email || `ID: ${txn.user_id}`}
                        </div>
                      </td>

                      <td className="py-3.5 px-5 font-medium text-slate-800">
                        {txn.plan_name || "Pro Subscription"}
                      </td>

                      <td className="py-3.5 px-5 font-bold text-navy-950 whitespace-nowrap">
                        ৳{Number(txn.amount).toLocaleString()}
                      </td>

                      <td className="py-3.5 px-5">
                        <span className="inline-block px-2 py-0.5 rounded-md text-[10px] font-bold bg-slate-100 text-slate-600 uppercase">
                          {txn.gateway}
                        </span>
                      </td>

                      <td className="py-3.5 px-5">
                        <span
                          className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold ${
                            isSuccess
                              ? "bg-emerald-50 text-emerald-700 border border-emerald-200/60"
                              : isPending
                              ? "bg-amber-50 text-amber-700 border border-amber-200/60"
                              : "bg-rose-50 text-rose-700 border border-rose-200/60"
                          }`}
                        >
                          <span
                            className={`w-1.5 h-1.5 rounded-full ${
                              isSuccess ? "bg-emerald-500" : isPending ? "bg-amber-500" : "bg-rose-500"
                            }`}
                          />
                          {isSuccess ? "Paid" : txn.status}
                        </span>
                      </td>

                      <td className="py-3.5 px-5 text-right whitespace-nowrap">
                        <div className="flex items-center justify-end gap-1.5">
                          {/* Invoice Trigger */}
                          <button
                            type="button"
                            onClick={() => handleViewInvoice(txn.id)}
                            title="View Official Tax Invoice"
                            className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg border border-slate-200 hover:bg-slate-100 text-slate-700 font-semibold transition-colors"
                          >
                            <Download className="w-3 h-3 text-slate-500" />
                            <span>Invoice</span>
                          </button>

                          {/* Idempotent Verify Hook Trigger */}
                          <button
                            type="button"
                            disabled={verifyingRef === txn.transaction_ref}
                            onClick={() => handleVerify(txn.transaction_ref)}
                            title="Execute Idempotent Verification Hook"
                            className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-emerald-50 hover:bg-emerald-100 text-emerald-700 border border-emerald-200 font-semibold transition-colors disabled:opacity-50"
                          >
                            {verifyingRef === txn.transaction_ref ? (
                              <Loader2 className="w-3 h-3 animate-spin" />
                            ) : (
                              <ShieldCheck className="w-3 h-3 text-emerald-600" />
                            )}
                            <span>Verify</span>
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>

            {/* Pagination Controls */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between px-5 py-3 border-t border-slate-100 bg-slate-50/50 text-xs text-slate-500">
                <span>
                  Showing {(currentPage - 1) * pageSize + 1} to{" "}
                  {Math.min(currentPage * pageSize, filteredTransactions.length)} of{" "}
                  {filteredTransactions.length} records
                </span>

                <div className="flex items-center gap-1.5">
                  <button
                    disabled={currentPage === 1}
                    onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                    className="px-2.5 py-1 rounded-lg border border-slate-200 hover:bg-white disabled:opacity-40 disabled:cursor-not-allowed font-medium"
                  >
                    &lt; Previous
                  </button>
                  {Array.from({ length: totalPages }, (_, i) => i + 1).map((num) => (
                    <button
                      key={num}
                      onClick={() => setCurrentPage(num)}
                      className={`w-7 h-7 rounded-lg font-bold text-xs ${
                        currentPage === num
                          ? "bg-emerald-600 text-white"
                          : "hover:bg-slate-100 text-slate-700"
                      }`}
                    >
                      {num}
                    </button>
                  ))}
                  <button
                    disabled={currentPage === totalPages}
                    onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                    className="px-2.5 py-1 rounded-lg border border-slate-200 hover:bg-white disabled:opacity-40 disabled:cursor-not-allowed font-medium"
                  >
                    Next &gt;
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Tax Invoice Modal */}
      {selectedInvoice && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 animate-in fade-in duration-150">
          <div className="bg-white rounded-2xl shadow-xl max-w-lg w-full p-6 sm:p-8 space-y-6 border border-slate-100">
            <div className="flex items-center justify-between border-b border-slate-100 pb-4">
              <div>
                <h4 className="text-base font-black text-navy-950 tracking-tight font-heading">
                  SKILL2CAREER
                </h4>
                <p className="text-[10px] text-slate-400 uppercase tracking-widest font-bold">
                  Official Platform Tax Receipt
                </p>
              </div>
              <button
                onClick={() => setSelectedInvoice(null)}
                className="text-slate-400 hover:text-slate-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Invoice Metadata */}
            <div className="grid grid-cols-2 gap-4 text-xs">
              <div>
                <p className="text-slate-400 font-medium">Invoice Number</p>
                <p className="font-bold text-navy-950 text-sm mt-0.5">{selectedInvoice.invoice_number}</p>
              </div>
              <div>
                <p className="text-slate-400 font-medium">Transaction Ref</p>
                <p className="font-semibold text-slate-700 font-mono mt-0.5">{selectedInvoice.transaction_ref}</p>
              </div>
              <div>
                <p className="text-slate-400 font-medium">Customer</p>
                <p className="font-bold text-navy-950 mt-0.5">{selectedInvoice.user_name}</p>
                <p className="text-slate-500 text-[11px]">{selectedInvoice.user_email}</p>
              </div>
              <div>
                <p className="text-slate-400 font-medium">Date &amp; Gateway</p>
                <p className="font-semibold text-slate-700 mt-0.5">{formatDate(selectedInvoice.date)}</p>
                <p className="text-slate-500 text-[11px]">{selectedInvoice.payment_method}</p>
              </div>
            </div>

            {/* Line Item Table */}
            <div className="bg-slate-50 rounded-xl p-4 border border-slate-200/80">
              <div className="flex justify-between text-xs font-bold text-slate-500 uppercase tracking-wider pb-2 border-b border-slate-200">
                <span>Description</span>
                <span>Amount</span>
              </div>
              <div className="flex justify-between text-sm font-semibold text-navy-950 pt-2.5">
                <span>{selectedInvoice.plan_name}</span>
                <span>৳{Number(selectedInvoice.amount).toLocaleString()}</span>
              </div>
              <div className="flex justify-between text-base font-bold text-navy-950 pt-3 mt-3 border-t border-slate-200">
                <span>Total Paid (BDT)</span>
                <span className="text-emerald-600 font-black">
                  ৳{Number(selectedInvoice.amount).toLocaleString()}
                </span>
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
                onClick={() => setSelectedInvoice(null)}
                className="py-2.5 px-5 rounded-xl border border-slate-200 hover:bg-slate-50 text-slate-700 text-xs sm:text-sm font-semibold transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TransactionAuditTab;
