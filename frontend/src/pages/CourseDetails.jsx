import React, { useState, useEffect } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import courseService from "../services/courseService";
import { ROUTES, USER_ROLES } from "../constants";
import {
  ArrowLeft,
  BookOpen,
  Clock,
  User,
  Layers,
  Video,
  FileText,
  ChevronDown,
  ChevronRight,
  Edit3,
  CheckCircle,
  Share2,
  Shield,
  Download,
} from "lucide-react";

export const CourseDetails = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();

  const [course, setCourse] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Active playing lesson
  const [activeLesson, setActiveLesson] = useState(null);
  const [expandedModules, setExpandedModules] = useState({});

  useEffect(() => {
    const fetchCourse = async () => {
      try {
        setLoading(true);
        setError(null);
        const res = await courseService.getCourseById(id);
        if (res?.data) {
          const c = res.data;
          setCourse(c);

          // Default expand all modules
          const exp = {};
          (c.modules || []).forEach((m, idx) => {
            exp[m.id || idx] = true;
          });
          setExpandedModules(exp);

          // Select first lesson with video or first lesson
          if (c.modules?.[0]?.lessons?.[0]) {
            setActiveLesson(c.modules[0].lessons[0]);
          }
        }
      } catch (err) {
        console.error("Error fetching course:", err);
        setError("Unable to load course. It may be unpublished or does not exist.");
      } finally {
        setLoading(false);
      }
    };

    fetchCourse();
  }, [id]);

  const toggleModule = (modId) => {
    setExpandedModules((prev) => ({
      ...prev,
      [modId]: !prev[modId],
    }));
  };

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 text-center space-y-4">
        <div className="w-10 h-10 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto" />
        <p className="text-slate-500 text-sm">Loading course curriculum...</p>
      </div>
    );
  }

  if (error || !course) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-16 text-center space-y-4">
        <h2 className="text-2xl font-bold text-navy-950 font-heading">
          Course Not Found
        </h2>
        <p className="text-sm text-slate-500">{error || "This course does not exist."}</p>
        <Link
          to={ROUTES.COURSES}
          className="inline-flex items-center space-x-2 px-4 py-2 text-xs font-semibold rounded-lg bg-navy-950 text-white"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Courses</span>
        </Link>
      </div>
    );
  }

  const isOwner = user && course.instructor_id === user.id;
  const canManage = isOwner || user?.role === USER_ROLES.ADMIN;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Top Navigation Bar */}
      <div className="flex items-center justify-between">
        <Link
          to={ROUTES.COURSES}
          className="inline-flex items-center space-x-1.5 text-xs font-semibold text-slate-500 hover:text-navy-950 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to All Courses</span>
        </Link>

        {canManage && (
          <Link
            to={`/courses/${course.id}/manage`}
            className="inline-flex items-center space-x-1.5 px-3.5 py-1.5 text-xs font-semibold rounded-lg bg-navy-950 hover:bg-navy-900 text-white shadow-sm transition-all"
          >
            <Edit3 className="w-3.5 h-3.5 text-emerald-400" />
            <span>Curriculum Builder / Manage</span>
          </Link>
        )}
      </div>

      {/* Hero Header */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 sm:p-8 shadow-sm flex flex-col md:flex-row justify-between gap-6">
        <div className="space-y-4 max-w-3xl">
          <div className="flex flex-wrap items-center gap-2">
            <span className="px-3 py-1 text-xs font-semibold rounded-full bg-blue-50 text-blue-700 border border-blue-100">
              {course.category}
            </span>
            <span className="px-3 py-1 text-xs font-semibold rounded-full bg-emerald-50 text-emerald-700 border border-emerald-100">
              {course.level}
            </span>
            {course.status !== "PUBLISHED" && (
              <span className="px-3 py-1 text-xs font-bold rounded-full bg-amber-50 text-amber-700 border border-amber-200">
                {course.status}
              </span>
            )}
          </div>

          <h1 className="text-2xl sm:text-4xl font-extrabold text-navy-950 font-heading">
            {course.title}
          </h1>

          <p className="text-sm sm:text-base text-slate-600 leading-relaxed">
            {course.description}
          </p>

          <div className="flex flex-wrap items-center gap-6 pt-2 text-xs text-slate-500">
            <div className="flex items-center space-x-2">
              <div className="w-7 h-7 rounded-full bg-slate-200 flex items-center justify-center font-bold text-slate-700">
                {course.instructor_name?.charAt(0) || "I"}
              </div>
              <div>
                <span className="font-semibold text-navy-950 block">
                  {course.instructor_name}
                </span>
                <span className="text-[11px] text-slate-400">
                  {course.instructor_designation || "Instructor"}
                </span>
              </div>
            </div>

            <div className="flex items-center space-x-1.5">
              <Clock className="w-4 h-4 text-slate-400" />
              <span>{course.duration_weeks || 8} Weeks Duration</span>
            </div>

            <div className="flex items-center space-x-1.5">
              <BookOpen className="w-4 h-4 text-slate-400" />
              <span>{course.lessons_count || 0} Total Lessons</span>
            </div>
          </div>
        </div>

        {/* Enrollment Card / Pricing */}
        <div className="w-full md:w-72 bg-slate-50 rounded-xl border border-slate-200 p-5 flex flex-col justify-between space-y-4">
          <div className="space-y-1">
            <span className="text-xs uppercase tracking-wider text-slate-400 font-bold">
              Tuition
            </span>
            <div className="text-2xl font-black text-navy-950">
              {course.is_free || course.price === 0 ? "Free Access" : `BDT ${course.price}`}
            </div>
            <p className="text-[11px] text-slate-500">
              Full curriculum access including all study materials
            </p>
          </div>

          <button
            type="button"
            onClick={() => alert("1-Click Enrollment is ready in Sprint 2 LMS Track (SKL-54)!")}
            className="w-full py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs shadow-sm transition-all text-center"
          >
            Enroll in Course
          </button>
        </div>
      </div>

      {/* 2-Column: Video Player (Left/Top) & Syllabus Accordion (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Active Lesson Viewer / Player */}
        <div className="lg:col-span-7 bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h3 className="text-base font-bold text-navy-950 font-heading flex items-center space-x-2">
              <Video className="w-4 h-4 text-blue-600" />
              <span>{activeLesson?.title || "Active Lesson"}</span>
            </h3>
            {activeLesson?.duration_minutes && (
              <span className="text-xs text-slate-500 font-medium">
                {activeLesson.duration_minutes} Mins
              </span>
            )}
          </div>

          {/* Video Player Frame */}
          <div className="aspect-video w-full rounded-xl overflow-hidden bg-navy-950 flex items-center justify-center text-white">
            {activeLesson?.video_url && activeLesson.video_url.includes("embed") ? (
              <iframe
                src={activeLesson.video_url}
                title={activeLesson.title}
                className="w-full h-full"
                allowFullScreen
              />
            ) : (
              <div className="text-center p-6 space-y-2">
                <Video className="w-10 h-10 text-slate-500 mx-auto" />
                <p className="text-xs text-slate-400">
                  Lesson Video Stream
                </p>
                <p className="text-[11px] text-slate-500 font-mono">
                  {activeLesson?.title}
                </p>
              </div>
            )}
          </div>

          {/* Lesson Study Materials */}
          {activeLesson?.attachments && activeLesson.attachments.length > 0 && (
            <div className="pt-2 space-y-2">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500">
                Lesson Study Materials
              </h4>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {activeLesson.attachments.map((att, idx) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between p-2.5 rounded-lg border border-slate-200 bg-slate-50 text-xs"
                  >
                    <div className="flex items-center space-x-2 truncate">
                      <FileText className="w-4 h-4 text-blue-600 flex-shrink-0" />
                      <span className="truncate font-medium text-navy-950">
                        {att.name}
                      </span>
                    </div>
                    <span className="text-[11px] text-slate-400 flex-shrink-0 pl-2">
                      {att.size || "PDF"}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Curriculum Outline Accordion */}
        <div className="lg:col-span-5 bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-4">
          <div className="border-b border-slate-100 pb-3 flex items-center justify-between">
            <h3 className="text-base font-bold text-navy-950 font-heading">
              Curriculum Outline
            </h3>
            <span className="text-xs text-slate-500 font-medium">
              {course.modules?.length || 0} Modules
            </span>
          </div>

          <div className="space-y-3 max-h-[500px] overflow-y-auto pr-1">
            {(course.modules || []).map((mod, mIdx) => {
              const isExpanded = expandedModules[mod.id || mIdx];
              return (
                <div
                  key={mod.id || mIdx}
                  className="rounded-xl border border-slate-200 overflow-hidden"
                >
                  <div
                    onClick={() => toggleModule(mod.id || mIdx)}
                    className="p-3 bg-slate-50 hover:bg-slate-100 cursor-pointer flex items-center justify-between select-none transition-colors"
                  >
                    <span className="text-xs font-bold text-navy-900">
                      {mod.title}
                    </span>
                    {isExpanded ? (
                      <ChevronDown className="w-4 h-4 text-slate-400" />
                    ) : (
                      <ChevronRight className="w-4 h-4 text-slate-400" />
                    )}
                  </div>

                  {isExpanded && (
                    <div className="p-2 space-y-1 bg-white">
                      {(mod.lessons || []).map((les, lIdx) => {
                        const isCurrent = activeLesson?.id === les.id;
                        return (
                          <div
                            key={les.id || lIdx}
                            onClick={() => setActiveLesson(les)}
                            className={`flex items-center justify-between p-2 rounded-lg cursor-pointer transition-colors text-xs ${
                              isCurrent
                                ? "bg-blue-50 text-blue-900 font-semibold"
                                : "hover:bg-slate-50 text-slate-600"
                            }`}
                          >
                            <div className="flex items-center space-x-2 truncate">
                              <FileText className="w-3.5 h-3.5 flex-shrink-0 text-slate-400" />
                              <span className="truncate">{les.title}</span>
                            </div>
                            <span className="text-[11px] text-slate-400 flex-shrink-0">
                              {les.duration_minutes || 30}m
                            </span>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};

export default CourseDetails;
