import React, { useState, useEffect, useMemo, useCallback } from "react";
import adminService from "../../services/adminService";
import {
  CheckCircle2,
  AlertTriangle,
  Clock,
  Eye,
  BookOpen,
  FileQuestion,
  Search,
  RefreshCw,
  X,
  User,
  Ban,
  Check,
  FileText,
  AlertCircle,
  Video,
} from "lucide-react";

export const ContentModerationTab = () => {
  const [items, setItems] = useState([]);
  const [stats, setStats] = useState(null);
  const [auditLogs, setAuditLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);

  // Filter states
  const [statusFilter, setStatusFilter] = useState("PENDING_REVIEW"); // Default to pending queue
  const [typeFilter, setTypeFilter] = useState("ALL");
  const [searchQuery, setSearchQuery] = useState("");

  // Drawer & Modal states
  const [selectedItem, setSelectedItem] = useState(null);
  const [previewData, setPreviewData] = useState(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);

  // Approve Modal state
  const [approveModalItem, setApproveModalItem] = useState(null);
  const [approveNotes, setApproveNotes] = useState("");
  const [approveSubmitting, setApproveSubmitting] = useState(false);

  // Restrict Modal state
  const [restrictModalItem, setRestrictModalItem] = useState(null);
  const [restrictReason, setRestrictReason] = useState("");
  const [restrictSubmitting, setRestrictSubmitting] = useState(false);
  const [restrictError, setRestrictError] = useState("");

  // Quick reasons for restriction
  const commonReasons = [
    "Inaccurate or misleading question answers",
    "Incomplete course curriculum or missing video lessons",
    "Copyright violation or unverified third-party content",
    "Low audio/video quality not meeting platform standards",
    "Contains prohibited promotional content or external links",
  ];

  const fetchModerationData = useCallback(async (isManual = false) => {
    try {
      if (isManual) setRefreshing(true);
      else setLoading(true);
      setError(null);

      const [statsRes, itemsRes, logsRes] = await Promise.all([
        adminService.getModerationStats().catch(() => ({ data: null })),
        adminService.getModerationItems({
          status: statusFilter === "ALL" ? undefined : statusFilter,
          content_type: typeFilter === "ALL" ? undefined : typeFilter,
        }).catch(() => ({ data: [] })),
        adminService.getModerationLogs({ limit: 15 }).catch(() => ({ data: [] })),
      ]);

      if (statsRes?.data) setStats(statsRes.data);
      if (itemsRes?.data) setItems(itemsRes.data);
      if (logsRes?.data) setAuditLogs(logsRes.data);
    } catch (err) {
      console.error("Failed to load content moderation data:", err);
      setError("Unable to load moderation records. Please check backend connection.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [statusFilter, typeFilter]);

  useEffect(() => {
    fetchModerationData();
  }, [fetchModerationData]);

  // Handle opening preview drawer
  const handleOpenPreview = async (item) => {
    setSelectedItem(item);
    setDrawerOpen(true);
    setPreviewLoading(true);
    setPreviewData(null);

    try {
      if (item.content_type === "COURSE") {
        const res = await adminService.getCourseModerationPreview(item.id);
        if (res?.data) setPreviewData(res.data);
      } else {
        const res = await adminService.getMockTestModerationPreview(item.id);
        if (res?.data) setPreviewData(res.data);
      }
    } catch (err) {
      console.error("Failed to fetch inspection preview:", err);
    } finally {
      setPreviewLoading(false);
    }
  };

  // Handle Approve action
  const handleConfirmApprove = async () => {
    if (!approveModalItem) return;
    try {
      setApproveSubmitting(true);
      if (approveModalItem.content_type === "COURSE") {
        await adminService.approveCourse(approveModalItem.id, { notes: approveNotes });
      } else {
        await adminService.approveMockTest(approveModalItem.id, { notes: approveNotes });
      }
      setApproveModalItem(null);
      setApproveNotes("");
      if (drawerOpen && selectedItem?.id === approveModalItem.id) {
        setDrawerOpen(false);
      }
      await fetchModerationData(true);
    } catch (err) {
      console.error("Failed to approve item:", err);
      alert(err.response?.data?.message || "Failed to approve content item.");
    } finally {
      setApproveSubmitting(false);
    }
  };

  // Handle Restrict action
  const handleConfirmRestrict = async () => {
    if (!restrictModalItem) return;
    if (!restrictReason.trim()) {
      setRestrictError("A clear justification reason is required to restrict content.");
      return;
    }
    try {
      setRestrictSubmitting(true);
      setRestrictError("");
      if (restrictModalItem.content_type === "COURSE") {
        await adminService.restrictCourse(restrictModalItem.id, { reason: restrictReason.trim() });
      } else {
        await adminService.restrictMockTest(restrictModalItem.id, { reason: restrictReason.trim() });
      }
      setRestrictModalItem(null);
      setRestrictReason("");
      if (drawerOpen && selectedItem?.id === restrictModalItem.id) {
        setDrawerOpen(false);
      }
      await fetchModerationData(true);
    } catch (err) {
      console.error("Failed to restrict item:", err);
      setRestrictError(err.response?.data?.message || "Failed to restrict content item.");
    } finally {
      setRestrictSubmitting(false);
    }
  };

  // Search filtering in client
  const filteredItems = useMemo(() => {
    if (!searchQuery.trim()) return items;
    const query = searchQuery.toLowerCase().trim();
    return items.filter(
      (item) =>
        item.title?.toLowerCase().includes(query) ||
        item.instructor_name?.toLowerCase().includes(query) ||
        item.category?.toLowerCase().includes(query)
    );
  }, [items, searchQuery]);

  const formatTimestamp = (dateString) => {
    if (!dateString) return "Recently";
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <div className="space-y-6">
      {error && (
        <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-xs flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Top Moderation Metrics Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {/* Metric 1: Pending Review */}
        <div
          onClick={() => setStatusFilter("PENDING_REVIEW")}
          className={`cursor-pointer rounded-2xl border p-5 shadow-sm transition-all ${
            statusFilter === "PENDING_REVIEW"
              ? "bg-amber-50/70 border-amber-400 ring-2 ring-amber-400/20"
              : "bg-white border-slate-200 hover:border-amber-300"
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
              Pending Review
            </span>
            <div className="w-9 h-9 rounded-xl bg-amber-100 text-amber-700 flex items-center justify-center">
              <Clock className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3">
            <h3 className="text-3xl font-extrabold text-navy-950 font-heading">
              {stats?.total_pending ?? 0}
            </h3>
            <p className="mt-1 text-xs text-amber-700 font-semibold flex items-center space-x-1.5">
              <span>{stats?.pending_courses ?? 0} courses</span>
              <span>·</span>
              <span>{stats?.pending_tests ?? 0} tests</span>
            </p>
          </div>
        </div>

        {/* Metric 2: Approved Catalog */}
        <div
          onClick={() => setStatusFilter("APPROVED")}
          className={`cursor-pointer rounded-2xl border p-5 shadow-sm transition-all ${
            statusFilter === "APPROVED"
              ? "bg-emerald-50/70 border-emerald-400 ring-2 ring-emerald-400/20"
              : "bg-white border-slate-200 hover:border-emerald-300"
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
              Approved Live
            </span>
            <div className="w-9 h-9 rounded-xl bg-emerald-100 text-emerald-700 flex items-center justify-center">
              <CheckCircle2 className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3">
            <h3 className="text-3xl font-extrabold text-navy-950 font-heading">
              {stats?.total_approved ?? 0}
            </h3>
            <p className="mt-1 text-xs text-emerald-700 font-semibold flex items-center space-x-1.5">
              <span>{stats?.approved_courses ?? 0} courses</span>
              <span>·</span>
              <span>{stats?.approved_tests ?? 0} tests</span>
            </p>
          </div>
        </div>

        {/* Metric 3: Restricted / Delisted */}
        <div
          onClick={() => setStatusFilter("RESTRICTED")}
          className={`cursor-pointer rounded-2xl border p-5 shadow-sm transition-all ${
            statusFilter === "RESTRICTED"
              ? "bg-red-50/70 border-red-400 ring-2 ring-red-400/20"
              : "bg-white border-slate-200 hover:border-red-300"
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
              Restricted / Flagged
            </span>
            <div className="w-9 h-9 rounded-xl bg-red-100 text-red-700 flex items-center justify-center">
              <AlertTriangle className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3">
            <h3 className="text-3xl font-extrabold text-navy-950 font-heading">
              {stats?.total_restricted ?? 0}
            </h3>
            <p className="mt-1 text-xs text-red-700 font-semibold flex items-center space-x-1.5">
              <span>{stats?.restricted_courses ?? 0} courses</span>
              <span>·</span>
              <span>{stats?.restricted_tests ?? 0} tests</span>
            </p>
          </div>
        </div>

        {/* Metric 4: All Moderated Items */}
        <div
          onClick={() => setStatusFilter("ALL")}
          className={`cursor-pointer rounded-2xl border p-5 shadow-sm transition-all ${
            statusFilter === "ALL"
              ? "bg-blue-50/70 border-blue-400 ring-2 ring-blue-400/20"
              : "bg-white border-slate-200 hover:border-blue-300"
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
              Total Catalog Items
            </span>
            <div className="w-9 h-9 rounded-xl bg-blue-100 text-blue-700 flex items-center justify-center">
              <BookOpen className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3">
            <h3 className="text-3xl font-extrabold text-navy-950 font-heading">
              {(stats?.total_approved ?? 0) + (stats?.total_pending ?? 0) + (stats?.total_restricted ?? 0)}
            </h3>
            <p className="mt-1 text-xs text-slate-500">
              Click to view entire moderation database
            </p>
          </div>
        </div>
      </div>

      {/* Main Review Card */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        {/* Filters and Search Header */}
        <div className="p-5 border-b border-slate-200 space-y-4">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <h2 className="text-lg font-bold text-navy-950 font-heading">
                Content Moderation Queue & Governance
              </h2>
              <p className="text-xs text-slate-500">
                Review syllabus quality, inspect question sets, and approve or restrict submissions (SKL-25)
              </p>
            </div>

            <div className="flex items-center space-x-2">
              <button
                type="button"
                onClick={() => fetchModerationData(true)}
                disabled={refreshing}
                className="inline-flex items-center space-x-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg border border-slate-300 bg-white hover:bg-slate-50 text-slate-700 transition-colors"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? "animate-spin text-blue-600" : ""}`} />
                <span>{refreshing ? "Refreshing..." : "Refresh Queue"}</span>
              </button>
            </div>
          </div>

          {/* Filter Chips & Type Controls */}
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 pt-2">
            {/* Status Tabs */}
            <div className="flex items-center space-x-1 bg-slate-100 p-1 rounded-xl">
              <button
                type="button"
                onClick={() => setStatusFilter("PENDING_REVIEW")}
                className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                  statusFilter === "PENDING_REVIEW"
                    ? "bg-white text-amber-900 shadow-sm"
                    : "text-slate-600 hover:text-navy-900"
                }`}
              >
                Pending Review {stats?.total_pending > 0 && `(${stats.total_pending})`}
              </button>
              <button
                type="button"
                onClick={() => setStatusFilter("APPROVED")}
                className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                  statusFilter === "APPROVED"
                    ? "bg-white text-emerald-900 shadow-sm"
                    : "text-slate-600 hover:text-navy-900"
                }`}
              >
                Approved
              </button>
              <button
                type="button"
                onClick={() => setStatusFilter("RESTRICTED")}
                className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                  statusFilter === "RESTRICTED"
                    ? "bg-white text-red-900 shadow-sm"
                    : "text-slate-600 hover:text-navy-900"
                }`}
              >
                Restricted
              </button>
              <button
                type="button"
                onClick={() => setStatusFilter("ALL")}
                className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                  statusFilter === "ALL"
                    ? "bg-white text-navy-950 shadow-sm"
                    : "text-slate-600 hover:text-navy-900"
                }`}
              >
                All States
              </button>
            </div>

            {/* Type selector & Search */}
            <div className="flex items-center space-x-2">
              <select
                value={typeFilter}
                onChange={(e) => setTypeFilter(e.target.value)}
                className="text-xs bg-slate-50 border border-slate-300 rounded-lg px-2.5 py-1.5 font-medium text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="ALL">All Content Types</option>
                <option value="COURSE">Courses Only</option>
                <option value="MOCK_TEST">Mock Tests Only</option>
              </select>

              <div className="relative">
                <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  placeholder="Filter title or instructor..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-8 pr-3 py-1.5 text-xs bg-slate-50 border border-slate-300 rounded-lg text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 w-48 sm:w-56"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Table Content */}
        {loading ? (
          <div className="py-16 text-center text-slate-400 text-xs flex flex-col items-center justify-center space-y-2">
            <RefreshCw className="w-6 h-6 animate-spin text-blue-600" />
            <p>Loading moderation records...</p>
          </div>
        ) : filteredItems.length === 0 ? (
          <div className="py-16 text-center text-slate-400 text-xs flex flex-col items-center justify-center space-y-3">
            <div className="w-12 h-12 rounded-2xl bg-slate-100 flex items-center justify-center text-slate-400">
              <CheckCircle2 className="w-6 h-6 text-emerald-500" />
            </div>
            <div>
              <p className="font-bold text-navy-900 text-sm">No items found in this view</p>
              <p className="text-slate-500 mt-1">
                {statusFilter === "PENDING_REVIEW"
                  ? "Great job! All pending content submissions have been reviewed."
                  : "No content items match your current filter selections."}
              </p>
            </div>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-700">
              <thead className="bg-slate-50 text-slate-500 font-bold uppercase tracking-wider text-[11px] border-b border-slate-200">
                <tr>
                  <th className="py-3.5 px-4">Content Item</th>
                  <th className="py-3.5 px-4">Author / Instructor</th>
                  <th className="py-3.5 px-4">Category & Scope</th>
                  <th className="py-3.5 px-4">Moderation Status</th>
                  <th className="py-3.5 px-4">Last Updated</th>
                  <th className="py-3.5 px-4 text-right">Administrative Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredItems.map((item) => {
                  const isCourse = item.content_type === "COURSE";
                  const isPending = item.moderation_status === "PENDING_REVIEW";
                  const isApproved = item.moderation_status === "APPROVED";
                  const isRestricted = item.moderation_status === "RESTRICTED";

                  return (
                    <tr key={`${item.content_type}-${item.id}`} className="hover:bg-slate-50/70 transition-colors">
                      {/* Content Title & Type */}
                      <td className="py-3.5 px-4 max-w-xs">
                        <div className="flex items-start space-x-3">
                          <div
                            className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5 ${
                              isCourse ? "bg-blue-50 text-blue-600" : "bg-purple-50 text-purple-600"
                            }`}
                          >
                            {isCourse ? <BookOpen className="w-4 h-4" /> : <FileQuestion className="w-4 h-4" />}
                          </div>
                          <div className="min-w-0">
                            <div className="font-bold text-navy-950 truncate hover:text-clip" title={item.title}>
                              {item.title}
                            </div>
                            <div className="flex items-center space-x-2 mt-0.5">
                              <span
                                className={`inline-flex items-center px-1.5 py-0.2 rounded text-[10px] font-bold ${
                                  isCourse
                                    ? "bg-blue-100 text-blue-800"
                                    : "bg-purple-100 text-purple-800"
                                }`}
                              >
                                {isCourse ? "Course" : "Mock Test"}
                              </span>
                              <span className="text-[11px] text-slate-400">ID #{item.id}</span>
                            </div>
                          </div>
                        </div>
                      </td>

                      {/* Author */}
                      <td className="py-3.5 px-4">
                        <div className="font-semibold text-navy-900">{item.instructor_name}</div>
                        <div className="text-[11px] text-slate-400">{item.instructor_email || "Instructor"}</div>
                      </td>

                      {/* Category & Scope */}
                      <td className="py-3.5 px-4">
                        <div className="font-medium text-slate-800 bg-slate-100 px-2 py-0.5 rounded text-[11px] inline-block">
                          {item.category}
                        </div>
                        <div className="text-[11px] text-slate-500 mt-1">
                          {isCourse
                            ? `${item.details?.modules_count || 0} modules · ${item.details?.lessons_count || 0} lessons`
                            : `${item.details?.questions_count || 0} questions · ${item.details?.duration_minutes || 0}m`}
                        </div>
                      </td>

                      {/* Moderation Status */}
                      <td className="py-3.5 px-4">
                        {isPending && (
                          <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-xs font-bold bg-amber-100 text-amber-800 border border-amber-200">
                            <Clock className="w-3 h-3 text-amber-600" />
                            <span>Pending Review</span>
                          </span>
                        )}
                        {isApproved && (
                          <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 border border-emerald-200">
                            <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                            <span>Approved Live</span>
                          </span>
                        )}
                        {isRestricted && (
                          <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-xs font-bold bg-red-100 text-red-800 border border-red-200">
                            <Ban className="w-3 h-3 text-red-600" />
                            <span>Restricted</span>
                          </span>
                        )}
                        {!isPending && !isApproved && !isRestricted && (
                          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-slate-100 text-slate-700">
                            {item.moderation_status}
                          </span>
                        )}
                        {item.moderation_notes && (
                          <p className="text-[10px] text-slate-500 mt-1 italic truncate max-w-xs" title={item.moderation_notes}>
                            Note: &ldquo;{item.moderation_notes}&rdquo;
                          </p>
                        )}
                      </td>

                      {/* Updated Date */}
                      <td className="py-3.5 px-4 text-slate-500 text-[11px]">
                        {formatTimestamp(item.updated_at || item.created_at)}
                      </td>

                      {/* Actions */}
                      <td className="py-3.5 px-4 text-right">
                        <div className="flex items-center justify-end space-x-1.5">
                          {/* Inspect / Preview Drawer Button */}
                          <button
                            type="button"
                            onClick={() => handleOpenPreview(item)}
                            className="inline-flex items-center space-x-1 px-2.5 py-1.5 rounded-lg text-xs font-semibold bg-slate-100 hover:bg-slate-200 text-slate-700 transition-colors"
                            title="Inspect syllabus and details in slide-over drawer"
                          >
                            <Eye className="w-3.5 h-3.5" />
                            <span>Inspect</span>
                          </button>

                          {/* Quick Approve Button */}
                          {!isApproved && (
                            <button
                              type="button"
                              onClick={() => setApproveModalItem(item)}
                              className="inline-flex items-center space-x-1 px-2.5 py-1.5 rounded-lg text-xs font-bold bg-emerald-600 hover:bg-emerald-700 text-white shadow-sm transition-all"
                              title="Approve for public catalog"
                            >
                              <Check className="w-3.5 h-3.5" />
                              <span>Approve</span>
                            </button>
                          )}

                          {/* Restrict Button */}
                          {!isRestricted && (
                            <button
                              type="button"
                              onClick={() => {
                                setRestrictModalItem(item);
                                setRestrictReason("");
                                setRestrictError("");
                              }}
                              className="inline-flex items-center space-x-1 px-2.5 py-1.5 rounded-lg text-xs font-semibold bg-red-50 hover:bg-red-100 text-red-700 border border-red-200 transition-colors"
                              title="Restrict from catalog"
                            >
                              <Ban className="w-3.5 h-3.5" />
                              <span>Restrict</span>
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Slide-over Inspection Drawer (Admin Dashboard.png) */}
      {drawerOpen && selectedItem && (
        <div className="fixed inset-0 z-50 overflow-hidden">
          {/* Backdrop */}
          <div
            className="absolute inset-0 bg-navy-950/40 backdrop-blur-sm transition-opacity"
            onClick={() => setDrawerOpen(false)}
          />

          <div className="fixed inset-y-0 right-0 pl-10 max-w-full flex">
            <div className="w-screen max-w-2xl bg-white shadow-2xl border-l border-slate-200 flex flex-col">
              {/* Drawer Header */}
              <div className="p-6 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div
                    className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                      selectedItem.content_type === "COURSE"
                        ? "bg-blue-100 text-blue-700"
                        : "bg-purple-100 text-purple-700"
                    }`}
                  >
                    {selectedItem.content_type === "COURSE" ? (
                      <BookOpen className="w-5 h-5" />
                    ) : (
                      <FileQuestion className="w-5 h-5" />
                    )}
                  </div>
                  <div>
                    <div className="flex items-center space-x-2">
                      <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                        {selectedItem.content_type === "COURSE" ? "Course Inspection" : "Mock Test Inspection"}
                      </span>
                      <span
                        className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                          selectedItem.moderation_status === "APPROVED"
                            ? "bg-emerald-100 text-emerald-800"
                            : selectedItem.moderation_status === "RESTRICTED"
                            ? "bg-red-100 text-red-800"
                            : "bg-amber-100 text-amber-800"
                        }`}
                      >
                        {selectedItem.moderation_status}
                      </span>
                    </div>
                    <h3 className="text-lg font-bold text-navy-950 font-heading truncate max-w-md">
                      {selectedItem.title}
                    </h3>
                  </div>
                </div>

                <button
                  type="button"
                  onClick={() => setDrawerOpen(false)}
                  className="p-2 rounded-xl text-slate-400 hover:text-slate-600 hover:bg-slate-200/60 transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Drawer Content */}
              <div className="flex-1 overflow-y-auto p-6 space-y-6">
                {previewLoading ? (
                  <div className="py-24 text-center text-slate-400 flex flex-col items-center justify-center space-y-3">
                    <RefreshCw className="w-8 h-8 animate-spin text-blue-600" />
                    <p className="text-sm font-medium">Loading comprehensive curriculum telemetry...</p>
                  </div>
                ) : previewData ? (
                  <>
                    {/* Metadata Overview Card */}
                    <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                          Curriculum Dossier
                        </span>
                        <span className="text-xs font-semibold text-slate-600">
                          Category: <span className="text-navy-950 font-bold">{previewData.category}</span>
                        </span>
                      </div>

                      {previewData.description && (
                        <p className="text-xs text-slate-600 leading-relaxed bg-white p-3 rounded-lg border border-slate-200">
                          {previewData.description}
                        </p>
                      )}

                      {/* Instructor Details */}
                      <div className="pt-2 border-t border-slate-200 flex items-center justify-between text-xs">
                        <div className="flex items-center space-x-2">
                          <div className="w-7 h-7 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center font-bold text-xs">
                            <User className="w-3.5 h-3.5" />
                          </div>
                          <div>
                            <span className="font-bold text-navy-950">
                              {previewData.instructor?.name || selectedItem.instructor_name}
                            </span>
                            <span className="text-slate-400 ml-1">
                              ({previewData.instructor?.email || selectedItem.instructor_email || "Instructor"})
                            </span>
                          </div>
                        </div>

                        {selectedItem.content_type === "COURSE" ? (
                          <div className="text-right text-slate-600 font-medium">
                            {previewData.is_free ? (
                              <span className="text-emerald-700 font-bold">Free Course</span>
                            ) : (
                              <span>৳{previewData.price}</span>
                            )}
                            <span className="mx-1">·</span>
                            <span>{previewData.level || "All Levels"}</span>
                          </div>
                        ) : (
                          <div className="text-right text-slate-600 font-medium">
                            <span>Passing: {previewData.passing_score}%</span>
                            <span className="mx-1">·</span>
                            <span>{previewData.duration_minutes} mins</span>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Content Section: Course Modules & Lessons */}
                    {selectedItem.content_type === "COURSE" && (
                      <div className="space-y-3">
                        <div className="flex items-center justify-between">
                          <h4 className="text-sm font-bold text-navy-950 flex items-center space-x-2">
                            <BookOpen className="w-4 h-4 text-blue-600" />
                            <span>Curriculum Modules & Lessons ({previewData.modules?.length || 0})</span>
                          </h4>
                        </div>

                        {previewData.modules?.length === 0 ? (
                          <p className="text-xs text-slate-400 italic p-4 bg-slate-50 rounded-xl">
                            No modules authored for this course yet.
                          </p>
                        ) : (
                          <div className="space-y-3">
                            {previewData.modules?.map((mod, idx) => (
                              <div
                                key={mod.id || idx}
                                className="rounded-xl border border-slate-200 bg-white overflow-hidden shadow-sm"
                              >
                                <div className="bg-slate-50 px-4 py-2.5 border-b border-slate-200 flex items-center justify-between">
                                  <span className="text-xs font-bold text-navy-900">
                                    {mod.title || `Module ${idx + 1}`}
                                  </span>
                                  <span className="text-[11px] text-slate-500 font-medium">
                                    {mod.lessons?.length || 0} lessons
                                  </span>
                                </div>

                                <div className="divide-y divide-slate-100">
                                  {mod.lessons?.map((les, lIdx) => (
                                    <div
                                      key={les.id || lIdx}
                                      className="px-4 py-2.5 flex items-center justify-between text-xs hover:bg-slate-50/50"
                                    >
                                      <div className="flex items-center space-x-2">
                                        {les.content_type === "video" ? (
                                          <Video className="w-3.5 h-3.5 text-blue-500" />
                                        ) : (
                                          <FileText className="w-3.5 h-3.5 text-slate-400" />
                                        )}
                                        <span className="font-medium text-slate-800">{les.title}</span>
                                        {les.is_preview && (
                                          <span className="px-1.5 py-0.2 rounded text-[10px] bg-emerald-50 text-emerald-700 font-semibold">
                                            Preview
                                          </span>
                                        )}
                                      </div>
                                      <span className="text-slate-400 text-[11px]">
                                        {les.duration_minutes ? `${les.duration_minutes} mins` : "Reading"}
                                      </span>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}

                    {/* Content Section: Mock Test Questions */}
                    {selectedItem.content_type === "MOCK_TEST" && (
                      <div className="space-y-3">
                        <div className="flex items-center justify-between">
                          <h4 className="text-sm font-bold text-navy-950 flex items-center space-x-2">
                            <FileQuestion className="w-4 h-4 text-purple-600" />
                            <span>Question Bank & Answer Keys ({previewData.questions?.length || 0})</span>
                          </h4>
                        </div>

                        {previewData.questions?.length === 0 ? (
                          <p className="text-xs text-slate-400 italic p-4 bg-slate-50 rounded-xl">
                            No questions registered for this test yet.
                          </p>
                        ) : (
                          <div className="space-y-4">
                            {previewData.questions?.map((q, idx) => (
                              <div
                                key={q.id || idx}
                                className="rounded-xl border border-slate-200 bg-white p-4 space-y-3 shadow-sm"
                              >
                                <div className="flex items-start justify-between gap-2">
                                  <div className="font-bold text-navy-950 text-xs">
                                    Q{idx + 1}. {q.question_text}
                                  </div>
                                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-700">
                                    {q.marks || 1} mark
                                  </span>
                                </div>

                                {/* Options grid */}
                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                                  {q.options?.map((opt, oIdx) => {
                                    const optionKey = String.fromCharCode(65 + oIdx);
                                    const isCorrect =
                                      q.correct_option === optionKey ||
                                      q.correct_option === opt ||
                                      q.correct_option === String(oIdx);

                                    return (
                                      <div
                                        key={oIdx}
                                        className={`p-2.5 rounded-lg border flex items-center space-x-2 ${
                                          isCorrect
                                            ? "bg-emerald-50 border-emerald-300 text-emerald-900 font-bold"
                                            : "bg-slate-50 border-slate-200 text-slate-700"
                                        }`}
                                      >
                                        <span
                                          className={`w-5 h-5 rounded flex items-center justify-center text-[10px] font-bold ${
                                            isCorrect
                                              ? "bg-emerald-600 text-white"
                                              : "bg-slate-200 text-slate-700"
                                          }`}
                                        >
                                          {optionKey}
                                        </span>
                                        <span className="truncate">{opt}</span>
                                        {isCorrect && (
                                          <Check className="w-3.5 h-3.5 text-emerald-600 ml-auto flex-shrink-0" />
                                        )}
                                      </div>
                                    );
                                  })}
                                </div>

                                {q.explanation && (
                                  <div className="p-2.5 rounded-lg bg-blue-50 border border-blue-200 text-[11px] text-blue-900">
                                    <span className="font-bold">Explanation: </span>
                                    <span>{q.explanation}</span>
                                  </div>
                                )}
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </>
                ) : (
                  <p className="text-xs text-red-600">Failed to load preview details.</p>
                )}
              </div>

              {/* Drawer Footer Actions */}
              <div className="p-4 border-t border-slate-200 bg-slate-50 flex items-center justify-between">
                <button
                  type="button"
                  onClick={() => setDrawerOpen(false)}
                  className="px-4 py-2 text-xs font-semibold text-slate-600 hover:text-slate-800"
                >
                  Close Inspection
                </button>

                <div className="flex items-center space-x-2">
                  <button
                    type="button"
                    onClick={() => {
                      setRestrictModalItem(selectedItem);
                      setRestrictReason("");
                      setRestrictError("");
                    }}
                    className="inline-flex items-center space-x-1.5 px-4 py-2 rounded-xl text-xs font-bold bg-red-50 hover:bg-red-100 text-red-700 border border-red-200 transition-colors"
                  >
                    <Ban className="w-3.5 h-3.5" />
                    <span>Restrict Content</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => setApproveModalItem(selectedItem)}
                    className="inline-flex items-center space-x-1.5 px-4 py-2 rounded-xl text-xs font-bold bg-emerald-600 hover:bg-emerald-700 text-white shadow-sm transition-all"
                  >
                    <Check className="w-3.5 h-3.5" />
                    <span>Approve Content</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Approve Confirmation Modal */}
      {approveModalItem && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div
            className="fixed inset-0 bg-navy-950/40 backdrop-blur-sm"
            onClick={() => setApproveModalItem(null)}
          />

          <div className="relative bg-white rounded-2xl border border-slate-200 shadow-2xl max-w-md w-full p-6 space-y-4">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 rounded-xl bg-emerald-100 text-emerald-700 flex items-center justify-center">
                <CheckCircle2 className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-bold text-navy-950 font-heading">
                  Approve for Public Catalog
                </h3>
                <p className="text-xs text-slate-500">
                  Author: {approveModalItem.instructor_name}
                </p>
              </div>
            </div>

            <div className="p-3 bg-slate-50 rounded-xl text-xs space-y-1">
              <p className="font-bold text-navy-900 truncate">{approveModalItem.title}</p>
              <p className="text-slate-500">
                This item will immediately become discoverable and accessible to all registered learners.
              </p>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-bold text-slate-700">
                Approval Feedback or Quality Remarks (Optional)
              </label>
              <textarea
                rows={3}
                placeholder="e.g. Well-structured curriculum, approved for public distribution."
                value={approveNotes}
                onChange={(e) => setApproveNotes(e.target.value)}
                className="w-full text-xs p-3 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-emerald-500 text-slate-800"
              />
            </div>

            <div className="flex items-center justify-end space-x-2 pt-2">
              <button
                type="button"
                onClick={() => setApproveModalItem(null)}
                disabled={approveSubmitting}
                className="px-4 py-2 text-xs font-semibold text-slate-600 hover:text-slate-800"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleConfirmApprove}
                disabled={approveSubmitting}
                className="px-4 py-2 rounded-xl text-xs font-bold bg-emerald-600 hover:bg-emerald-700 text-white shadow-sm transition-all disabled:opacity-50"
              >
                {approveSubmitting ? "Approving..." : "Confirm & Approve"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Restrict Confirmation Modal */}
      {restrictModalItem && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div
            className="fixed inset-0 bg-navy-950/40 backdrop-blur-sm"
            onClick={() => setRestrictModalItem(null)}
          />

          <div className="relative bg-white rounded-2xl border border-slate-200 shadow-2xl max-w-lg w-full p-6 space-y-4">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 rounded-xl bg-red-100 text-red-700 flex items-center justify-center">
                <AlertTriangle className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-bold text-navy-950 font-heading">
                  Restrict / Delist Content Item
                </h3>
                <p className="text-xs text-slate-500">
                  Target: {restrictModalItem.title}
                </p>
              </div>
            </div>

            <div className="p-3 bg-red-50 border border-red-200 rounded-xl text-xs text-red-800 flex items-start space-x-2">
              <AlertCircle className="w-4 h-4 text-red-600 flex-shrink-0 mt-0.5" />
              <span>
                Restricting this content will remove it from the public catalog immediately. A clear justification is recorded in the platform audit log.
              </span>
            </div>

            {/* Quick Reason Chips */}
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-slate-700">
                Common Violation Reasons (Click to apply)
              </label>
              <div className="flex flex-wrap gap-1.5">
                {commonReasons.map((r, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => setRestrictReason(r)}
                    className="text-[11px] px-2.5 py-1 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 transition-colors"
                  >
                    {r}
                  </button>
                ))}
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-bold text-slate-700">
                Detailed Justification Reason <span className="text-red-500">*</span>
              </label>
              <textarea
                rows={3}
                placeholder="Specify the policy violation or quality requirement..."
                value={restrictReason}
                onChange={(e) => {
                  setRestrictReason(e.target.value);
                  setRestrictError("");
                }}
                className="w-full text-xs p-3 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-red-500 text-slate-800"
              />
              {restrictError && <p className="text-xs text-red-600 font-medium">{restrictError}</p>}
            </div>

            <div className="flex items-center justify-end space-x-2 pt-2">
              <button
                type="button"
                onClick={() => setRestrictModalItem(null)}
                disabled={restrictSubmitting}
                className="px-4 py-2 text-xs font-semibold text-slate-600 hover:text-slate-800"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleConfirmRestrict}
                disabled={restrictSubmitting}
                className="px-4 py-2 rounded-xl text-xs font-bold bg-red-600 hover:bg-red-700 text-white shadow-sm transition-all disabled:opacity-50"
              >
                {restrictSubmitting ? "Restricting..." : "Confirm Restriction"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Recent Moderation Activity Feed */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div className="flex items-center space-x-2">
            <Clock className="w-4 h-4 text-slate-500" />
            <h3 className="text-sm font-bold text-navy-950 font-heading">
              Content Moderation Audit History
            </h3>
          </div>
          <span className="text-xs text-slate-400">
            Last {auditLogs.length} moderation operations
          </span>
        </div>

        {auditLogs.length === 0 ? (
          <p className="text-xs text-slate-400 italic py-4 text-center">
            No moderation actions recorded in the platform audit trail yet.
          </p>
        ) : (
          <div className="divide-y divide-slate-100">
            {auditLogs.map((log) => {
              const isApprove = log.action === "APPROVE";
              const isRestrict = log.action === "RESTRICT";
              const isSubmit = log.action === "SUBMIT_REVIEW";

              return (
                <div key={log.id} className="py-3 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs">
                  <div className="flex items-start sm:items-center space-x-3">
                    <div
                      className={`w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0 ${
                        isApprove
                          ? "bg-emerald-100 text-emerald-700"
                          : isRestrict
                          ? "bg-red-100 text-red-700"
                          : "bg-blue-100 text-blue-700"
                      }`}
                    >
                      {isApprove ? (
                        <Check className="w-3.5 h-3.5" />
                      ) : isRestrict ? (
                        <Ban className="w-3.5 h-3.5" />
                      ) : (
                        <Clock className="w-3.5 h-3.5" />
                      )}
                    </div>
                    <div>
                      <div className="flex items-center space-x-2">
                        <span className="font-bold text-navy-950">{log.admin_name || "Admin"}</span>
                        <span className="text-slate-500">
                          {isApprove && "approved"}
                          {isRestrict && "restricted"}
                          {isSubmit && "submitted"}
                          {" "}
                          <span className="font-semibold text-slate-700">
                            {log.content_type?.toLowerCase().replace(/_/g, " ")} #{log.content_id}
                          </span>
                        </span>
                        <span
                          className={`px-1.5 py-0.2 rounded text-[10px] font-bold ${
                            isApprove
                              ? "bg-emerald-100 text-emerald-800"
                              : isRestrict
                              ? "bg-red-100 text-red-800"
                              : "bg-blue-100 text-blue-800"
                          }`}
                        >
                          {log.action}
                        </span>
                      </div>
                      {log.reason && (
                        <p className="text-slate-500 mt-0.5 text-[11px]">
                          Note: &ldquo;{log.reason}&rdquo;
                        </p>
                      )}
                    </div>
                  </div>

                  <span className="text-slate-400 text-[11px] font-medium flex-shrink-0">
                    {formatTimestamp(log.created_at)}
                  </span>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

export default ContentModerationTab;
