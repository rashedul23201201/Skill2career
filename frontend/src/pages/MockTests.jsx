import React, { useState, useEffect, useCallback } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import mockTestService from "../services/mockTestService";
import { ROUTES, USER_ROLES } from "../constants";
import {
  Search,
  HelpCircle,
  CheckSquare,
  ArrowRight,
  Plus,
  Clock,
  Award,
  Edit3,
  Trash2,
  AlertCircle,
  X,
  BookOpen,
} from "lucide-react";

export const MockTests = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  const [tests, setTests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [searchInput, setSearchInput] = useState(searchParams.get("search") || "");
  const [appliedSearch, setAppliedSearch] = useState(searchParams.get("search") || "");
  const [categoryFilter, setCategoryFilter] = useState(searchParams.get("category") || "All");

  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  const [activeModalTest, setActiveModalTest] = useState(null);
  const [deletingId, setDeletingId] = useState(null);

  const categories = ["All", "Programming", "Database", "Web Development", "Other"];

  const canManage =
    user?.role === USER_ROLES.INSTRUCTOR || user?.role === USER_ROLES.ADMIN;

  const fetchMockTests = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const params = {
        page,
        size: 10,
      };
      if (categoryFilter && categoryFilter !== "All") {
        params.category = categoryFilter;
      }
      if (appliedSearch.trim()) {
        params.search = appliedSearch.trim();
      }

      const res = await mockTestService.getMockTests(params);
      if (res?.data?.items) {
        setTests(res.data.items);
        setTotalPages(res.data.total_pages || 1);
      }
    } catch (err) {
      console.error("Failed to load mock tests:", err);
      setError("Unable to load mock tests. Please check your network connection.");
    } finally {
      setLoading(false);
    }
  }, [page, categoryFilter, appliedSearch]);

  useEffect(() => {
    fetchMockTests();
  }, [fetchMockTests]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setPage(1);
    setAppliedSearch(searchInput);
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      if (searchInput.trim()) next.set("search", searchInput.trim());
      else next.delete("search");
      return next;
    });
  };

  const handleCategorySelect = (cat) => {
    setCategoryFilter(cat);
    setPage(1);
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      if (cat !== "All") next.set("category", cat);
      else next.delete("category");
      return next;
    });
  };

  const handleDeleteTest = async (testId, e) => {
    e.stopPropagation();
    if (!window.confirm("Are you sure you want to delete this mock test? This action cannot be undone.")) {
      return;
    }
    try {
      setDeletingId(testId);
      await mockTestService.deleteMockTest(testId);
      setTests((prev) => prev.filter((t) => t.id !== testId));
    } catch (err) {
      console.error("Failed to delete mock test:", err);
      alert("Failed to delete mock test. Please try again.");
    } finally {
      setDeletingId(null);
    }
  };

  const getCategoryBadgeClass = (category) => {
    const cat = (category || "").toLowerCase();
    if (cat.includes("prog")) {
      return "bg-blue-50 text-blue-600";
    }
    if (cat.includes("data")) {
      return "bg-emerald-50 text-emerald-600";
    }
    if (cat.includes("web")) {
      return "bg-purple-50 text-purple-600";
    }
    return "bg-slate-100 text-slate-700";
  };

  return (
    <div className="min-h-screen bg-brandBg py-10 px-4 sm:px-6 lg:px-8">
      <div className="max-w-6xl mx-auto space-y-8">
        {/* Page Header */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
          <div>
            <h1 className="text-3xl sm:text-4xl font-extrabold text-navy-950 font-heading tracking-tight">
              Mock Tests
            </h1>
            <p className="text-slate-500 mt-2 text-sm sm:text-base">
              Test your skills and prepare for real job assessments.
            </p>
          </div>

          {canManage && (
            <Link
              to={ROUTES.MOCK_TEST_NEW}
              className="inline-flex items-center space-x-2 px-4 py-2.5 bg-navy-950 hover:bg-navy-900 text-white rounded-xl text-sm font-semibold shadow-sm transition-all self-start md:self-auto"
            >
              <Plus className="w-4 h-4" />
              <span>Create Mock Test</span>
            </Link>
          )}
        </div>

        {/* Search and Category Filters */}
        <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4">
          {/* Search bar */}
          <form onSubmit={handleSearchSubmit} className="relative w-full md:w-80">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder="Search tests..."
              className="w-full pl-10 pr-4 py-2 text-sm bg-white border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-navy-900 focus:border-transparent text-navy-950 placeholder-slate-400 shadow-sm"
            />
          </form>

          {/* Filter Pills */}
          <div className="flex items-center gap-2 overflow-x-auto pb-1 sm:pb-0 scrollbar-none">
            {categories.map((cat) => {
              const isActive = categoryFilter === cat;
              return (
                <button
                  key={cat}
                  onClick={() => handleCategorySelect(cat)}
                  className={`px-4 py-1.5 rounded-full text-xs font-semibold whitespace-nowrap transition-all ${
                    isActive
                      ? "bg-navy-950 text-white shadow-sm"
                      : "bg-white text-slate-600 hover:text-navy-950 hover:bg-slate-50 border border-slate-200"
                  }`}
                >
                  {cat}
                </button>
              );
            })}
          </div>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm flex items-center space-x-3">
            <AlertCircle className="w-5 h-5 flex-shrink-0 text-red-500" />
            <span>{error}</span>
          </div>
        )}

        {/* Loading State */}
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {[1, 2, 3, 4].map((i) => (
              <div
                key={i}
                className="bg-white rounded-2xl border border-slate-100 p-6 shadow-sm animate-pulse space-y-4"
              >
                <div className="w-24 h-6 bg-slate-100 rounded-md"></div>
                <div className="w-3/4 h-6 bg-slate-100 rounded-md"></div>
                <div className="w-full h-12 bg-slate-100 rounded-md"></div>
                <div className="flex justify-between items-center pt-2">
                  <div className="w-40 h-4 bg-slate-100 rounded-md"></div>
                  <div className="w-24 h-8 bg-slate-100 rounded-md"></div>
                </div>
              </div>
            ))}
          </div>
        ) : tests.length === 0 ? (
          <div className="bg-white rounded-2xl border border-slate-100 p-12 text-center max-w-md mx-auto space-y-4">
            <div className="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center mx-auto text-slate-400">
              <BookOpen className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-navy-950 font-heading">
              No mock tests found
            </h3>
            <p className="text-xs text-slate-500 leading-relaxed">
              We couldn't find any assessments matching your current filter criteria.
            </p>
            {categoryFilter !== "All" && (
              <button
                onClick={() => handleCategorySelect("All")}
                className="text-xs font-semibold text-blue-600 hover:underline"
              >
                Reset filters
              </button>
            )}
          </div>
        ) : (
          /* Mock Tests Grid (2 Columns) */
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {tests.map((test) => {
              const isOwner = user && (test.instructor_id === user.id || user.role === USER_ROLES.ADMIN);
              return (
                <div
                  key={test.id}
                  className="bg-white rounded-2xl border border-slate-100 p-6 shadow-sm hover:shadow-md transition-shadow flex flex-col justify-between space-y-6"
                >
                  <div className="space-y-3">
                    {/* Top Row: Category Badge & Author Actions */}
                    <div className="flex items-center justify-between">
                      <span
                        className={`inline-block px-2.5 py-1 rounded-md text-xs font-semibold ${getCategoryBadgeClass(
                          test.category
                        )}`}
                      >
                        {test.category}
                      </span>

                      {isOwner && (
                        <div className="flex items-center space-x-1">
                          <button
                            onClick={() => navigate(ROUTES.MOCK_TEST_MANAGE.replace(":id", test.id))}
                            className="p-1.5 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                            title="Edit Test"
                          >
                            <Edit3 className="w-4 h-4" />
                          </button>
                          <button
                            onClick={(e) => handleDeleteTest(test.id, e)}
                            disabled={deletingId === test.id}
                            className="p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                            title="Delete Test"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      )}
                    </div>

                    {/* Test Title */}
                    <h3 className="text-xl font-bold text-navy-950 font-heading leading-snug">
                      {test.title}
                    </h3>

                    {/* Test Description */}
                    <p className="text-xs sm:text-sm text-slate-500 leading-relaxed line-clamp-2">
                      {test.description || "Practice standard questions for technical assessments."}
                    </p>
                  </div>

                  {/* Bottom Meta & Action */}
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pt-2 border-t border-slate-50">
                    <div className="space-y-1.5 text-xs text-slate-500">
                      <div className="flex items-center space-x-1.5">
                        <HelpCircle className="w-3.5 h-3.5 text-slate-400 flex-shrink-0" />
                        <span>
                          {test.total_questions} Questions · {test.duration_minutes} Minutes
                        </span>
                      </div>
                      <div className="flex items-center space-x-1.5">
                        <CheckSquare className="w-3.5 h-3.5 text-slate-400 flex-shrink-0" />
                        <span>Passing Score: {test.passing_score}%</span>
                      </div>
                    </div>

                    <button
                      onClick={() => setActiveModalTest(test)}
                      className="inline-flex items-center justify-center space-x-1.5 px-4 py-2 bg-navy-950 hover:bg-navy-900 text-white rounded-xl text-xs sm:text-sm font-semibold transition-all self-end sm:self-auto"
                    >
                      <span>Start Test</span>
                      <ArrowRight className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-end space-x-2 pt-4">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="px-3 py-1.5 text-xs font-semibold text-slate-600 hover:text-navy-950 disabled:opacity-40 disabled:hover:text-slate-600 rounded-lg hover:bg-slate-100"
            >
              Previous
            </button>
            {Array.from({ length: totalPages }, (_, idx) => idx + 1).map((pNum) => (
              <button
                key={pNum}
                onClick={() => setPage(pNum)}
                className={`w-7 h-7 rounded-lg text-xs font-semibold transition-all ${
                  page === pNum
                    ? "bg-navy-950 text-white"
                    : "text-slate-600 hover:bg-slate-100"
                }`}
              >
                {pNum}
              </button>
            ))}
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="px-3 py-1.5 text-xs font-semibold text-slate-600 hover:text-navy-950 disabled:opacity-40 disabled:hover:text-slate-600 rounded-lg hover:bg-slate-100"
            >
              Next
            </button>
          </div>
        )}
      </div>

      {/* Test Overview Modal */}
      {activeModalTest && (
        <div className="fixed inset-0 z-50 overflow-y-auto bg-navy-950/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 sm:p-8 shadow-2xl relative border border-slate-200 space-y-6">
            <button
              onClick={() => setActiveModalTest(null)}
              className="absolute top-5 right-5 text-slate-400 hover:text-slate-600 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>

            <div>
              <span
                className={`inline-block px-2.5 py-1 rounded-md text-xs font-semibold ${getCategoryBadgeClass(
                  activeModalTest.category
                )}`}
              >
                {activeModalTest.category}
              </span>
              <h3 className="text-xl font-bold text-navy-950 font-heading mt-2">
                {activeModalTest.title}
              </h3>
              <p className="text-xs text-slate-500 mt-1">
                Authored by {activeModalTest.instructor_name}
              </p>
            </div>

            <p className="text-sm text-slate-600 leading-relaxed">
              {activeModalTest.description ||
                "This assessment evaluates core conceptual and problem-solving abilities required for engineering roles."}
            </p>

            {/* Test Stats Grid */}
            <div className="grid grid-cols-3 gap-3 bg-slate-50 rounded-xl p-4 border border-slate-100 text-center">
              <div>
                <p className="text-xs text-slate-400 font-medium">Questions</p>
                <p className="text-base font-bold text-navy-950 mt-0.5">
                  {activeModalTest.total_questions}
                </p>
              </div>
              <div>
                <p className="text-xs text-slate-400 font-medium">Duration</p>
                <p className="text-base font-bold text-navy-950 mt-0.5">
                  {activeModalTest.duration_minutes}m
                </p>
              </div>
              <div>
                <p className="text-xs text-slate-400 font-medium">Passing</p>
                <p className="text-base font-bold text-emerald-600 mt-0.5">
                  {activeModalTest.passing_score}%
                </p>
              </div>
            </div>

            {/* Rules list */}
            <div className="space-y-2 text-xs text-slate-500 bg-blue-50/50 p-4 rounded-xl border border-blue-100">
              <p className="font-semibold text-blue-900 flex items-center space-x-1.5">
                <Clock className="w-4 h-4 text-blue-600" />
                <span>Test Instructions:</span>
              </p>
              <ul className="list-disc list-inside space-y-1 text-slate-600 pl-1">
                <li>The timer runs continuously once started.</li>
                <li>All multiple-choice questions must be answered before submission.</li>
                <li>Results and scorecard are computed automatically upon completion.</li>
              </ul>
            </div>

            <div className="flex items-center justify-end space-x-3 pt-2">
              <button
                onClick={() => setActiveModalTest(null)}
                className="px-4 py-2 border border-slate-200 rounded-xl text-xs font-semibold text-slate-600 hover:bg-slate-50"
              >
                Close
              </button>
              {(user?.role === USER_ROLES.INSTRUCTOR || user?.role === USER_ROLES.ADMIN) && (
                <button
                  onClick={() => {
                    navigate(ROUTES.MOCK_TEST_MANAGE.replace(":id", activeModalTest.id));
                  }}
                  className="px-4 py-2 border border-blue-200 text-blue-700 bg-blue-50 hover:bg-blue-100 rounded-xl text-xs font-semibold"
                >
                  Edit Questions
                </button>
              )}
              <button
                onClick={() => {
                  alert(
                    "Test session timer & answering interface will launch in Phase 2 (SKL-57: Test Attempt & Timer)!"
                  );
                  setActiveModalTest(null);
                }}
                className="px-5 py-2 bg-navy-950 hover:bg-navy-900 text-white rounded-xl text-xs font-semibold shadow-sm"
              >
                Start Assessment
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MockTests;
