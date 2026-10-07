import React, { useState, useEffect, useCallback } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import courseService from "../services/courseService";
import { ROUTES, USER_ROLES } from "../constants";
import {
  Search,
  BookOpen,
  Code2,
  Globe,
  Database,
  Layers,
  Sparkles,
  Plus,
  Clock,
  BookMarked,
  Filter,
  SlidersHorizontal,
  ChevronLeft,
  ChevronRight,
  Edit3,
  ShieldAlert,
} from "lucide-react";

const CATEGORIES = [
  "All",
  "Programming",
  "Web Development",
  "Database",
  "Software Engineering",
];

export const Courses = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  const [courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("All");
  const [selectedLevel, setSelectedLevel] = useState("");
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCourses, setTotalCourses] = useState(0);

  // Tab: "all" or "my_courses" (for instructors/admins)
  const isInstructorOrAdmin =
    user?.role === USER_ROLES.INSTRUCTOR || user?.role === USER_ROLES.ADMIN;
  const [activeTab, setActiveTab] = useState(
    searchParams.get("tab") === "my_courses" && isInstructorOrAdmin
      ? "my_courses"
      : "all"
  );

  const fetchCourses = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const params = {
        page,
        size: 8,
      };

      if (searchTerm.trim()) {
        params.search = searchTerm.trim();
      }

      if (selectedCategory && selectedCategory !== "All") {
        params.category = selectedCategory;
      }

      if (selectedLevel) {
        params.level = selectedLevel;
      }

      if (activeTab === "my_courses") {
        params.my_courses = true;
      }

      const res = await courseService.getCourses(params);
      if (res?.data) {
        setCourses(res.data.items || []);
        setTotalPages(res.data.total_pages || 1);
        setTotalCourses(res.data.total || 0);
      }
    } catch (err) {
      console.error("Failed to fetch courses:", err);
      setError("Unable to load courses. Please verify backend connection.");
    } finally {
      setLoading(false);
    }
  }, [page, searchTerm, selectedCategory, selectedLevel, activeTab]);

  useEffect(() => {
    fetchCourses();
  }, [fetchCourses]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setPage(1);
    fetchCourses();
  };

  const handleCategoryClick = (category) => {
    setSelectedCategory(category);
    setPage(1);
  };

  const handleTabChange = (tab) => {
    setActiveTab(tab);
    setPage(1);
    setSearchParams(tab === "my_courses" ? { tab: "my_courses" } : {});
  };

  const getCategoryIcon = (category) => {
    const cat = (category || "").toLowerCase();
    if (cat.includes("web")) {
      return (
        <div className="w-10 h-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center">
          <Globe className="w-5 h-5" />
        </div>
      );
    }
    if (cat.includes("data") && !cat.includes("structure")) {
      return (
        <div className="w-10 h-10 rounded-xl bg-cyan-50 text-cyan-600 flex items-center justify-center">
          <Database className="w-5 h-5" />
        </div>
      );
    }
    if (cat.includes("program") || cat.includes("algorithm")) {
      return (
        <div className="w-10 h-10 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center">
          <Code2 className="w-5 h-5" />
        </div>
      );
    }
    return (
      <div className="w-10 h-10 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center">
        <Layers className="w-5 h-5" />
      </div>
    );
  };

  const getLevelBadge = (level) => {
    const lvl = (level || "").toLowerCase();
    if (lvl.includes("beginner")) {
      return (
        <span className="px-3 py-1 text-xs font-semibold rounded-full bg-emerald-50 text-emerald-700 border border-emerald-100">
          Beginner
        </span>
      );
    }
    if (lvl.includes("intermed")) {
      return (
        <span className="px-3 py-1 text-xs font-semibold rounded-full bg-blue-50 text-blue-700 border border-blue-100">
          Intermediate
        </span>
      );
    }
    return (
      <span className="px-3 py-1 text-xs font-semibold rounded-full bg-purple-50 text-purple-700 border border-purple-100">
        Advanced
      </span>
    );
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">
      {/* Header and Title matching Courses.png */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl sm:text-4xl font-extrabold text-navy-950 font-heading tracking-tight">
            Explore Courses
          </h1>
          <p className="mt-2 text-base text-slate-500">
            Build practical skills and prepare for your career.
          </p>
        </div>

        {isInstructorOrAdmin && (
          <div className="flex items-center space-x-3">
            <Link
              to={ROUTES.COURSE_NEW}
              className="inline-flex items-center space-x-2 bg-navy-950 hover:bg-navy-900 text-white font-semibold text-sm px-4 py-2.5 rounded-xl shadow-sm transition-all hover:shadow"
            >
              <Plus className="w-4 h-4 text-emerald-400" />
              <span>Create Course</span>
            </Link>
          </div>
        )}
      </div>

      {/* Instructor / Admin Tab Switcher */}
      {isInstructorOrAdmin && (
        <div className="flex items-center space-x-2 border-b border-slate-200 pb-2">
          <button
            type="button"
            onClick={() => handleTabChange("all")}
            className={`px-4 py-2 text-sm font-semibold rounded-lg transition-colors ${
              activeTab === "all"
                ? "bg-navy-950 text-white"
                : "text-slate-600 hover:text-navy-950 hover:bg-slate-100"
            }`}
          >
            All Published Courses
          </button>
          <button
            type="button"
            onClick={() => handleTabChange("my_courses")}
            className={`px-4 py-2 text-sm font-semibold rounded-lg transition-colors ${
              activeTab === "my_courses"
                ? "bg-navy-950 text-white"
                : "text-slate-600 hover:text-navy-950 hover:bg-slate-100"
            }`}
          >
            My Authored Courses
          </button>
        </div>
      )}

      {/* Search Bar matching Courses.png */}
      <form onSubmit={handleSearchSubmit} className="flex gap-3 max-w-2xl">
        <div className="relative flex-1">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search courses..."
            className="w-full pl-11 pr-4 py-3 bg-white border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all text-navy-950"
          />
        </div>
        <button
          type="submit"
          className="bg-navy-950 hover:bg-navy-900 text-white text-sm font-semibold px-6 py-3 rounded-xl shadow-sm transition-colors flex items-center space-x-2"
        >
          <span>Search</span>
        </button>
      </form>

      {/* Category Pills matching Courses.png */}
      <div className="flex flex-wrap gap-2 pt-1">
        {CATEGORIES.map((cat) => {
          const isSelected = selectedCategory === cat;
          return (
            <button
              key={cat}
              type="button"
              onClick={() => handleCategoryClick(cat)}
              className={`px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
                isSelected
                  ? "bg-navy-950 text-white shadow-sm"
                  : "bg-white text-slate-600 border border-slate-200 hover:border-slate-300 hover:bg-slate-50"
              }`}
            >
              {cat}
            </button>
          );
        })}
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-crimson-50 border border-crimson-200 text-crimson-700 text-sm flex items-center space-x-2">
          <ShieldAlert className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Loading Skeleton */}
      {loading && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {[1, 2, 3, 4].map((i) => (
            <div
              key={i}
              className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm animate-pulse space-y-4"
            >
              <div className="flex justify-between items-center">
                <div className="w-10 h-10 bg-slate-200 rounded-xl" />
                <div className="w-20 h-6 bg-slate-200 rounded-full" />
              </div>
              <div className="w-3/4 h-5 bg-slate-200 rounded" />
              <div className="w-full h-12 bg-slate-100 rounded" />
              <div className="w-1/2 h-4 bg-slate-200 rounded" />
            </div>
          ))}
        </div>
      )}

      {/* Empty State */}
      {!loading && courses.length === 0 && (
        <div className="text-center py-16 bg-white rounded-2xl border border-slate-200 p-8 space-y-4">
          <div className="w-12 h-12 mx-auto rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center">
            <BookOpen className="w-6 h-6" />
          </div>
          <h3 className="text-lg font-bold text-navy-950 font-heading">
            No courses found
          </h3>
          <p className="text-slate-500 text-sm max-w-sm mx-auto">
            {searchTerm || selectedCategory !== "All"
              ? "Try adjusting your search criteria or category filter."
              : "No courses are currently available in this section."}
          </p>
          {isInstructorOrAdmin && (
            <Link
              to={ROUTES.COURSE_NEW}
              className="inline-flex items-center space-x-2 bg-navy-950 text-white text-xs font-semibold px-4 py-2 rounded-xl mt-2"
            >
              <Plus className="w-4 h-4" />
              <span>Create First Course</span>
            </Link>
          )}
        </div>
      )}

      {/* 2x2 Course Cards Grid matching Courses.png */}
      {!loading && courses.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {courses.map((course) => {
            const isOwner = user && course.instructor_id === user.id;
            const canManage = isOwner || user?.role === USER_ROLES.ADMIN;

            return (
              <div
                key={course.id}
                className="bg-white rounded-2xl border border-slate-200 p-6 sm:p-7 shadow-sm hover:border-slate-300 hover:shadow-md transition-all flex flex-col justify-between group"
              >
                <div className="space-y-4">
                  {/* Top Bar: Icon & Level Badge */}
                  <div className="flex items-center justify-between">
                    {getCategoryIcon(course.category)}
                    <div className="flex items-center space-x-2">
                      {course.status !== "PUBLISHED" && (
                        <span className="px-2.5 py-0.5 text-xs font-bold rounded-full bg-amber-50 text-amber-700 border border-amber-200">
                          {course.status}
                        </span>
                      )}
                      {getLevelBadge(course.level)}
                    </div>
                  </div>

                  {/* Course Title */}
                  <h3 className="text-xl font-bold text-navy-950 font-heading group-hover:text-blue-600 transition-colors">
                    {course.title}
                  </h3>

                  {/* Description */}
                  <p className="text-xs sm:text-sm text-slate-500 line-clamp-2 leading-relaxed">
                    {course.description}
                  </p>
                </div>

                {/* Bottom Row: Instructor, Meta, and Action Button matching Courses.png */}
                <div className="mt-6 pt-5 border-t border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div className="space-y-1">
                    <p className="text-xs text-slate-600">
                      Instructor:{" "}
                      <span className="font-semibold text-navy-950">
                        {course.instructor_name}
                      </span>
                    </p>
                    <p className="text-xs text-slate-500 font-medium">
                      {course.lessons_count || 0} Lessons ·{" "}
                      {course.duration_weeks || 8} Weeks
                    </p>
                  </div>

                  <div className="flex items-center space-x-2">
                    {canManage && (
                      <Link
                        to={`/courses/${course.id}/manage`}
                        className="inline-flex items-center space-x-1.5 px-3 py-2 text-xs font-semibold rounded-lg border border-slate-200 hover:bg-slate-50 text-slate-700 transition-colors"
                        title="Edit curriculum & course settings"
                      >
                        <Edit3 className="w-3.5 h-3.5" />
                        <span>Manage</span>
                      </Link>
                    )}
                    <Link
                      to={`/courses/${course.id}`}
                      className="bg-navy-950 hover:bg-navy-900 text-white text-xs font-semibold px-4 py-2 rounded-lg shadow-sm transition-all text-center"
                    >
                      View Course
                    </Link>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Pagination matching Courses.png (Previous, 1, 2, 3, Next) */}
      {!loading && totalPages > 1 && (
        <div className="flex items-center justify-center space-x-2 pt-6">
          <button
            type="button"
            disabled={page <= 1}
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            className="px-3.5 py-1.5 text-xs font-medium rounded-lg text-slate-600 hover:bg-slate-100 disabled:opacity-40 disabled:hover:bg-transparent transition-colors"
          >
            Previous
          </button>

          {Array.from({ length: totalPages }, (_, idx) => idx + 1).map(
            (pNum) => (
              <button
                key={pNum}
                type="button"
                onClick={() => setPage(pNum)}
                className={`w-8 h-8 rounded-lg text-xs font-semibold transition-colors ${
                  page === pNum
                    ? "bg-navy-950 text-white"
                    : "text-slate-600 hover:bg-slate-100"
                }`}
              >
                {pNum}
              </button>
            )
          )}

          <button
            type="button"
            disabled={page >= totalPages}
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            className="px-3.5 py-1.5 text-xs font-medium rounded-lg text-slate-600 hover:bg-slate-100 disabled:opacity-40 disabled:hover:bg-transparent transition-colors"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
};

export default Courses;
