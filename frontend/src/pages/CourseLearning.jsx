import React, { useState, useEffect, useRef } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import courseService from "../services/courseService";
import { ROUTES } from "../constants";
import {
  ArrowLeft,
  Clock,
  Layers,
  FileText,
  Download,
  Eye,
  CheckCircle2,
  Lock,
  Play,
  Pause,
  Volume2,
  VolumeX,
  Maximize,
  Settings,
  Subtitles,
  ChevronLeft,
  ChevronRight,
  Folder,
  Calendar,
  Check,
  X,
  ExternalLink,
} from "lucide-react";

export const CourseLearning = () => {
  const { id, lessonId } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();

  const [course, setCourse] = useState(null);
  const [lessons, setLessons] = useState([]);
  const [activeLessonIndex, setActiveLessonIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isEnrolled, setIsEnrolled] = useState(true);
  const [enrolling, setEnrolling] = useState(false);

  // Completed lessons tracking
  const [completedLessonIds, setCompletedLessonIds] = useState(() => {
    try {
      const saved = localStorage.getItem(`course_${id}_completed_lessons`);
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });

  // Video Player state
  const [isPlaying, setIsPlaying] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [volume, setVolume] = useState(80);
  const [playbackSpeed, setPlaybackSpeed] = useState("1.0x");
  const [currentTimeSec, setCurrentTimeSec] = useState(728); // 12:08
  const videoPlayerRef = useRef(null);

  // Document preview modal
  const [previewMaterial, setPreviewMaterial] = useState(null);

  useEffect(() => {
    const fetchCourseAndLessons = async () => {
      try {
        setLoading(true);
        setError(null);

        // Fetch course details
        const courseRes = await courseService.getCourseById(id);
        if (!courseRes?.data) {
          throw new Error("Course not found");
        }
        const courseData = courseRes.data;
        setCourse(courseData);

        // Flatten all lessons from modules or course.lessons
        let allLessons = [];
        if (courseData.modules && courseData.modules.length > 0) {
          courseData.modules.forEach((mod) => {
            if (mod.lessons && mod.lessons.length > 0) {
              mod.lessons.forEach((l) => {
                allLessons.push({ ...l, moduleTitle: mod.title });
              });
            }
          });
        }

        if (allLessons.length === 0 && courseData.lessons && courseData.lessons.length > 0) {
          allLessons = courseData.lessons;
        }

        // If no lessons yet, provide standard curriculum demo data
        if (allLessons.length === 0) {
          allLessons = [
            {
              id: 1,
              title: "1. Introduction to Data Structures",
              duration_minutes: 24,
              content_type: "video",
              video_url: "https://www.youtube.com/embed/dQw4w9WgXcQ",
              attachments: [{ name: "Course_Overview.pdf", size: "1.1 MB · High Yield" }],
            },
            {
              id: 2,
              title: "2. Arrays and Strings",
              duration_minutes: 38,
              content_type: "video",
              video_url: "https://www.youtube.com/embed/dQw4w9WgXcQ",
              attachments: [{ name: "Array_Problems.pdf", size: "2.0 MB · Practice Set" }],
            },
            {
              id: 3,
              title: "3. Linked Lists",
              duration_minutes: 45,
              content_type: "video",
              video_url: "https://www.youtube.com/embed/dQw4w9WgXcQ",
              attachments: [{ name: "Linked_List_CheatSheet.pdf", size: "1.5 MB · Reference" }],
            },
            {
              id: 4,
              title: "4. Stacks and Queues",
              duration_minutes: 30,
              content_type: "video",
              video_url: "https://www.youtube.com/embed/dQw4w9WgXcQ",
              attachments: [{ name: "Stack_Queue_Notes.pdf", size: "1.9 MB · Core Theory" }],
            },
            {
              id: 5,
              title: "5. Trees and Tree Traversal",
              duration_minutes: 32,
              content_type: "video",
              video_url: "https://www.youtube.com/embed/dQw4w9WgXcQ",
              attachments: [
                { name: "Lecture Notes.pdf", size: "2.4 MB · High Yield" },
                { name: "Previous Questions.pdf", size: "1.8 MB · Bank & Govt Sets" },
              ],
            },
            {
              id: 6,
              title: "6. Graphs",
              duration_minutes: 50,
              content_type: "video",
              attachments: [{ name: "Graph_Traversals.pdf", size: "2.8 MB" }],
            },
            {
              id: 7,
              title: "7. Sorting Algorithms",
              duration_minutes: 40,
              content_type: "video",
              attachments: [{ name: "Sorting_Visuals.pdf", size: "1.4 MB" }],
            },
            {
              id: 8,
              title: "8. Searching Algorithms",
              duration_minutes: 28,
              content_type: "video",
              attachments: [{ name: "Binary_Search_Tricks.pdf", size: "1.2 MB" }],
            },
          ];
        }

        setLessons(allLessons);

        // Synchronize real enrollment progress from backend if authenticated
        if (user) {
          try {
            const progRes = await courseService.getCourseProgress(id);
            if (progRes?.data) {
              const serverCompleted = progRes.data.completed_lesson_ids || [];
              setCompletedLessonIds(serverCompleted);
              setIsEnrolled(progRes.data.is_enrolled);
              localStorage.setItem(
                `course_${id}_completed_lessons`,
                JSON.stringify(serverCompleted)
              );

              if (progRes.data.last_accessed_lesson_id && !lessonId) {
                const lastIdx = allLessons.findIndex(
                  (l) => l.id === progRes.data.last_accessed_lesson_id
                );
                if (lastIdx !== -1) {
                  setActiveLessonIndex(lastIdx);
                }
              }
            }
          } catch {
            // Guest or non-enrolled
          }
        }

        // Select initial lesson
        if (lessonId) {
          const targetIndex = allLessons.findIndex((l) => String(l.id) === String(lessonId));
          if (targetIndex !== -1) {
            setActiveLessonIndex(targetIndex);
          }
        } else if (!user) {
          const defaultIndex = allLessons.length > 4 ? 4 : 0;
          setActiveLessonIndex(defaultIndex);
        }
      } catch (err) {
        console.error("Failed to load course learning context:", err);
        setError("Unable to load course learning experience. Please try again later.");
      } finally {
        setLoading(false);
      }
    };

    fetchCourseAndLessons();
  }, [id, lessonId, user]);

  const activeLesson = lessons[activeLessonIndex] || null;

  // Toggle lesson completed status (SKL-54 AC-4)
  const toggleLessonCompleted = async (lesId, e) => {
    if (e) e.stopPropagation();
    const isCompleted = completedLessonIds.includes(lesId);
    const nextState = !isCompleted;

    setCompletedLessonIds((prev) => {
      const next = isCompleted
        ? prev.filter((idVal) => idVal !== lesId)
        : [...prev, lesId];
      try {
        localStorage.setItem(`course_${id}_completed_lessons`, JSON.stringify(next));
      } catch (err) {
        console.error(err);
      }
      return next;
    });

    if (user) {
      try {
        await courseService.completeLesson(lesId, nextState);
      } catch (err) {
        console.error("Failed to sync lesson progress:", err);
      }
    }
  };

  const handleEnroll = async () => {
    if (!user) {
      navigate(ROUTES.LOGIN);
      return;
    }
    try {
      setEnrolling(true);
      await courseService.enrollInCourse(id);
      setIsEnrolled(true);
    } catch (err) {
      if (err.response?.data?.error_code === "ALREADY_ENROLLED") {
        setIsEnrolled(true);
      }
    } finally {
      setEnrolling(false);
    }
  };

  // Navigations
  const handleSelectLesson = (idx) => {
    setActiveLessonIndex(idx);
    setIsPlaying(false);
  };

  const handlePrevLesson = () => {
    if (activeLessonIndex > 0) {
      handleSelectLesson(activeLessonIndex - 1);
    }
  };

  const handleNextLesson = () => {
    if (activeLessonIndex < lessons.length - 1) {
      handleSelectLesson(activeLessonIndex + 1);
    }
  };

  // Cycle playback speed
  const cyclePlaybackSpeed = () => {
    const speeds = ["1.0x", "1.25x", "1.5x", "2.0x"];
    const currIdx = speeds.indexOf(playbackSpeed);
    const nextSpeed = speeds[(currIdx + 1) % speeds.length];
    setPlaybackSpeed(nextSpeed);
  };

  // Format time mm:ss
  const formatTime = (seconds) => {
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m}:${s < 10 ? "0" : ""}${s}`;
  };

  const totalDurationSec = (activeLesson?.duration_minutes || 32) * 60;

  // Progress metrics calculation
  const totalLessonsCount = lessons.length || 1;
  const completedCount = completedLessonIds.length;
  const remainingCount = Math.max(0, totalLessonsCount - completedCount);
  const overallProgressPct = Math.round((completedCount / totalLessonsCount) * 100);

  if (loading) {
    return (
      <div className="min-h-[70vh] flex flex-col items-center justify-center space-y-4">
        <div className="w-10 h-10 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
        <p className="text-sm font-medium text-slate-500">Loading course learning environment...</p>
      </div>
    );
  }

  if (error || !course) {
    return (
      <div className="max-w-xl mx-auto my-16 p-8 bg-white rounded-2xl border border-slate-200 text-center space-y-4 shadow-sm">
        <h2 className="text-xl font-bold text-navy-950 font-heading">Course Unavailable</h2>
        <p className="text-sm text-slate-500">{error || "Course could not be loaded."}</p>
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

  return (
    <div className="min-h-screen bg-slate-50 pb-20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Header Title & Subtitle */}
        <div className="space-y-1">
          <div className="flex items-center space-x-2 text-xs font-semibold text-slate-500 mb-2">
            <Link to={ROUTES.COURSES} className="hover:text-navy-950 flex items-center space-x-1">
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Courses</span>
            </Link>
            <span>/</span>
            <Link to={`/courses/${course.id}`} className="hover:text-navy-950 truncate max-w-xs">
              {course.title}
            </Link>
            <span>/</span>
            <span className="text-navy-950 font-bold">Course Learning</span>
          </div>

          <h1 className="text-2xl sm:text-3xl font-extrabold text-navy-950 font-heading tracking-tight">
            Course Learning
          </h1>
          <p className="text-xs sm:text-sm text-slate-500">
            Continue your lessons, access course materials, and track your learning progress.
          </p>
        </div>

        {/* Enrollment Banner if previewing */}
        {!isEnrolled && (
          <div className="bg-gradient-to-r from-navy-900 to-blue-950 rounded-2xl p-4 sm:p-5 text-white shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h3 className="text-sm font-bold">You are currently previewing this course</h3>
              <p className="text-xs text-slate-300 mt-0.5">
                Enroll now to record your lesson progress and update your candidate curriculum.
              </p>
            </div>
            <button
              type="button"
              onClick={handleEnroll}
              disabled={enrolling}
              className="px-4 py-2 text-xs font-bold rounded-xl bg-emerald-500 hover:bg-emerald-600 text-white shadow-xs transition-colors flex-shrink-0"
            >
              {enrolling ? "Enrolling..." : "Enroll in Course"}
            </button>
          </div>
        )}

        {/* Top Course Card & Progress Banner */}
        <div className="bg-white rounded-2xl border border-slate-200 p-5 sm:p-6 shadow-sm space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-center space-x-3.5">
              <div className="w-12 h-12 rounded-xl bg-blue-50 border border-blue-100 flex items-center justify-center text-blue-600 flex-shrink-0">
                <Layers className="w-6 h-6" />
              </div>
              <div>
                <h2 className="text-base sm:text-lg font-bold text-navy-950 font-heading">
                  {course.title}
                </h2>
                <p className="text-xs text-slate-500">
                  Instructor:{" "}
                  <span className="font-semibold text-navy-900">
                    {course.instructor_name || "Jubair Bin Hasan"}
                  </span>
                  {" | "}
                  <span className="text-slate-500">
                    {course.instructor_designation || "Engineering Job Core"}
                  </span>
                </p>
              </div>
            </div>

            <div className="text-left sm:text-right flex-shrink-0">
              <div className="text-xs text-slate-500 font-medium">
                <span className="font-bold text-navy-950">{completedCount}</span> of{" "}
                <span className="font-bold text-navy-950">{totalLessonsCount}</span> lessons completed
              </div>
              <div className="text-sm font-black text-emerald-600">
                {overallProgressPct}% Complete
              </div>
            </div>
          </div>

          {/* Green Progress Bar */}
          <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
            <div
              className="bg-emerald-500 h-2 rounded-full transition-all duration-500 ease-out"
              style={{ width: `${Math.min(100, Math.max(3, overallProgressPct))}%` }}
            />
          </div>
        </div>

        {/* 2-Column Layout: Course Content (Left) & Active Lesson / Materials (Right) */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          {/* Left Column: Course Content List */}
          <div className="lg:col-span-4 bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden flex flex-col">
            <div className="p-4 border-b border-slate-100 flex items-center justify-between">
              <div className="flex items-center space-x-2 text-navy-950 font-bold text-sm font-heading">
                <div className="w-4 h-4 flex flex-col justify-between py-0.5">
                  <span className="block h-0.5 w-full bg-navy-950 rounded-full" />
                  <span className="block h-0.5 w-full bg-navy-950 rounded-full" />
                  <span className="block h-0.5 w-full bg-navy-950 rounded-full" />
                </div>
                <span>Course Content</span>
              </div>
              <span className="text-[11px] font-semibold text-slate-400">
                {lessons.length} Lessons
              </span>
            </div>

            {/* Scrollable Lesson Items */}
            <div className="divide-y divide-slate-100 max-h-[560px] overflow-y-auto">
              {lessons.map((les, idx) => {
                const isCurrent = idx === activeLessonIndex;
                const isCompleted = completedLessonIds.includes(les.id);

                return (
                  <div
                    key={les.id || idx}
                    onClick={() => handleSelectLesson(idx)}
                    className={`p-3.5 sm:p-4 flex items-center justify-between cursor-pointer transition-all select-none ${
                      isCurrent
                        ? "bg-blue-50/70 border-l-4 border-blue-600"
                        : "hover:bg-slate-50"
                    }`}
                  >
                    <div className="flex items-start space-x-3 truncate pr-2">
                      {/* Status Indicator Icon */}
                      <div className="pt-0.5 flex-shrink-0">
                        {isCompleted ? (
                          <button
                            type="button"
                            onClick={(e) => toggleLessonCompleted(les.id, e)}
                            title="Mark as incomplete"
                            className="w-5 h-5 rounded-full bg-emerald-100 hover:bg-emerald-200 text-emerald-600 flex items-center justify-center cursor-pointer transition-colors"
                          >
                            <Check className="w-3.5 h-3.5 stroke-[3]" />
                          </button>
                        ) : isCurrent ? (
                          <button
                            type="button"
                            onClick={(e) => toggleLessonCompleted(les.id, e)}
                            title="Mark as completed"
                            className="w-5 h-5 rounded-full bg-blue-600 hover:bg-blue-700 text-white flex items-center justify-center cursor-pointer transition-colors"
                          >
                            <Play className="w-2.5 h-2.5 fill-current ml-0.5" />
                          </button>
                        ) : (
                          <button
                            type="button"
                            onClick={(e) => toggleLessonCompleted(les.id, e)}
                            title="Mark as completed"
                            className="w-5 h-5 rounded-full bg-slate-100 hover:bg-slate-200 text-slate-400 hover:text-slate-600 flex items-center justify-center cursor-pointer transition-colors"
                          >
                            <Lock className="w-3 h-3" />
                          </button>
                        )}
                      </div>

                      <div className="truncate">
                        <p
                          className={`text-xs truncate ${
                            isCurrent
                              ? "font-bold text-navy-950"
                              : isCompleted
                              ? "font-medium text-slate-800"
                              : "text-slate-600"
                          }`}
                        >
                          {les.title}
                        </p>
                        <p className="text-[11px] text-slate-400">
                          {les.duration_minutes || 30} mins
                        </p>
                      </div>
                    </div>

                    {/* Status Pill Badge */}
                    <div className="flex-shrink-0">
                      {isCompleted ? (
                        <span className="inline-flex px-2 py-0.5 text-[10px] font-bold rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                          Completed
                        </span>
                      ) : isCurrent ? (
                        <span className="inline-flex px-2 py-0.5 text-[10px] font-bold rounded-full bg-blue-600 text-white shadow-xs">
                          Current
                        </span>
                      ) : (
                        <span className="inline-flex px-2 py-0.5 text-[10px] font-medium rounded-full bg-slate-100 text-slate-500">
                          Locked
                        </span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Bottom Nav Controls in Content Sidebar */}
            <div className="p-3 bg-slate-50 border-t border-slate-100 flex items-center justify-between gap-2">
              <button
                type="button"
                onClick={handlePrevLesson}
                disabled={activeLessonIndex === 0}
                className="inline-flex items-center space-x-1 px-3 py-1.5 text-xs font-semibold rounded-lg text-slate-700 hover:bg-slate-200 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
              >
                <ChevronLeft className="w-3.5 h-3.5" />
                <span>Previous Lesson</span>
              </button>

              <button
                type="button"
                onClick={handleNextLesson}
                disabled={activeLessonIndex >= lessons.length - 1}
                className="inline-flex items-center space-x-1 px-3 py-1.5 text-xs font-semibold rounded-lg bg-navy-950 text-white hover:bg-navy-900 disabled:opacity-40 disabled:cursor-not-allowed transition-all shadow-xs"
              >
                <span>Next Lesson</span>
                <ChevronRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          {/* Right Column: Active Lesson Video Player & Study Materials */}
          <div className="lg:col-span-8 space-y-6">
            <div className="bg-white rounded-2xl border border-slate-200 p-5 sm:p-6 shadow-sm space-y-5">
              {/* Active Lesson Header & Mark Completed Toggle */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-4">
                <div>
                  <h2 className="text-xl sm:text-2xl font-black text-navy-950 font-heading">
                    {activeLesson?.title || "Lesson Stream"}
                  </h2>
                  <div className="flex items-center space-x-1.5 text-xs text-slate-500 mt-1">
                    <Clock className="w-3.5 h-3.5 text-slate-400" />
                    <span>{activeLesson?.duration_minutes || 32} minutes</span>
                  </div>
                </div>

                {activeLesson && (
                  <button
                    type="button"
                    onClick={() => toggleLessonCompleted(activeLesson.id)}
                    className={`inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-xl text-xs font-bold transition-all shadow-xs ${
                      completedLessonIds.includes(activeLesson.id)
                        ? "bg-emerald-50 text-emerald-700 border border-emerald-200 hover:bg-emerald-100"
                        : "bg-slate-100 text-slate-700 hover:bg-slate-200 border border-slate-200"
                    }`}
                  >
                    <CheckCircle2
                      className={`w-4 h-4 ${
                        completedLessonIds.includes(activeLesson.id)
                          ? "text-emerald-600"
                          : "text-slate-400"
                      }`}
                    />
                    <span>
                      {completedLessonIds.includes(activeLesson.id)
                        ? "Completed"
                        : "Mark as Complete"}
                    </span>
                  </button>
                )}
              </div>

              {/* Video Player Frame with Custom Styled Controls */}
              <div
                ref={videoPlayerRef}
                className="relative aspect-video w-full rounded-2xl overflow-hidden bg-navy-950 flex flex-col justify-between text-white shadow-md border border-navy-900 group"
              >
                {/* Top Video Overlay Banner */}
                <div className="relative z-10 p-4 bg-gradient-to-b from-black/80 via-black/40 to-transparent flex items-center justify-between">
                  <span className="text-xs sm:text-sm font-semibold text-slate-200 truncate pr-4">
                    {activeLesson?.title || "Binary Trees, Binary Search Trees, and Depth-First/Breadth-First Traversals"}
                  </span>
                </div>

                {/* Embedded Iframe or Video Canvas */}
                {activeLesson?.video_url && activeLesson.video_url.includes("embed") ? (
                  <div className="absolute inset-0 w-full h-full">
                    <iframe
                      src={activeLesson.video_url}
                      title={activeLesson.title}
                      className="w-full h-full border-0"
                      allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                      allowFullScreen
                    />
                  </div>
                ) : (
                  /* Custom Video Player Placeholder / Native Controls */
                  <div className="absolute inset-0 flex items-center justify-center">
                    <button
                      type="button"
                      onClick={() => setIsPlaying(!isPlaying)}
                      className="w-16 h-16 sm:w-20 sm:h-20 rounded-full bg-white/20 backdrop-blur-md hover:bg-white/30 border border-white/30 text-white flex items-center justify-center transition-all transform hover:scale-105 shadow-xl"
                    >
                      {isPlaying ? (
                        <Pause className="w-8 h-8 fill-current" />
                      ) : (
                        <Play className="w-8 h-8 fill-current ml-1" />
                      )}
                    </button>
                  </div>
                )}

                {/* Custom Bottom Media Controller Bar */}
                <div className="relative z-10 p-3 sm:p-4 bg-gradient-to-t from-black/90 via-black/60 to-transparent space-y-2">
                  {/* Seek Bar */}
                  <div className="w-full bg-white/20 rounded-full h-1.5 cursor-pointer relative overflow-hidden group/bar">
                    <div
                      className="bg-emerald-500 h-full rounded-full relative"
                      style={{
                        width: `${(currentTimeSec / totalDurationSec) * 100}%`,
                      }}
                    />
                  </div>

                  <div className="flex items-center justify-between text-xs">
                    <div className="flex items-center space-x-3 sm:space-x-4">
                      {/* Play/Pause */}
                      <button
                        type="button"
                        onClick={() => setIsPlaying(!isPlaying)}
                        className="hover:text-blue-400 transition-colors"
                      >
                        {isPlaying ? (
                          <Pause className="w-4 h-4" />
                        ) : (
                          <Play className="w-4 h-4 fill-current" />
                        )}
                      </button>

                      {/* Volume */}
                      <div className="flex items-center space-x-1.5">
                        <button
                          type="button"
                          onClick={() => setIsMuted(!isMuted)}
                          className="hover:text-blue-400 transition-colors"
                        >
                          {isMuted ? (
                            <VolumeX className="w-4 h-4 text-red-400" />
                          ) : (
                            <Volume2 className="w-4 h-4" />
                          )}
                        </button>
                      </div>

                      {/* Time readout */}
                      <span className="text-[11px] font-mono text-slate-300">
                        {formatTime(currentTimeSec)} / {formatTime(totalDurationSec)}
                      </span>
                    </div>

                    <div className="flex items-center space-x-2 sm:space-x-3">
                      {/* Speed pill */}
                      <button
                        type="button"
                        onClick={cyclePlaybackSpeed}
                        className="px-2 py-0.5 rounded text-[11px] font-bold bg-white/10 hover:bg-white/20 transition-all font-mono"
                      >
                        {playbackSpeed}
                      </button>

                      {/* Captions */}
                      <button type="button" className="hover:text-blue-400 transition-colors">
                        <Subtitles className="w-4 h-4" />
                      </button>

                      {/* Settings */}
                      <button type="button" className="hover:text-blue-400 transition-colors">
                        <Settings className="w-4 h-4" />
                      </button>

                      {/* Fullscreen */}
                      <button
                        type="button"
                        onClick={() => {
                          if (videoPlayerRef.current) {
                            if (document.fullscreenElement) {
                              document.exitFullscreen();
                            } else {
                              videoPlayerRef.current.requestFullscreen?.();
                            }
                          }
                        }}
                        className="hover:text-blue-400 transition-colors"
                      >
                        <Maximize className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>
              </div>

              {/* Lesson Materials Section */}
              <div className="pt-2 space-y-3">
                <div className="flex items-center space-x-2 text-navy-950 font-bold text-sm font-heading">
                  <Folder className="w-4 h-4 text-blue-600" />
                  <span>Lesson Materials</span>
                </div>

                {activeLesson?.attachments && activeLesson.attachments.length > 0 ? (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {activeLesson.attachments.map((att, attIdx) => {
                      const downloadUrl =
                        att.url ||
                        `/api/v1/lessons/${activeLesson.id}/materials/${att.filename || att.name}/download`;

                      return (
                        <div
                          key={attIdx}
                          className="bg-slate-50 border border-slate-200 rounded-xl p-3 sm:p-4 flex items-center justify-between gap-3 hover:border-slate-300 transition-all"
                        >
                          <div className="flex items-center space-x-3 truncate">
                            <div className="w-9 h-9 rounded-lg bg-red-50 border border-red-100 flex items-center justify-center text-red-600 flex-shrink-0">
                              <FileText className="w-5 h-5" />
                            </div>
                            <div className="truncate">
                              <h4 className="text-xs font-bold text-navy-950 truncate">
                                {att.name || "Lecture Notes.pdf"}
                              </h4>
                              <p className="text-[10px] text-slate-500 truncate">
                                {att.size || "2.4 MB · High Yield"}
                              </p>
                            </div>
                          </div>

                          <div className="flex items-center space-x-1.5 flex-shrink-0">
                            <button
                              type="button"
                              onClick={() => setPreviewMaterial(att)}
                              className="px-2.5 py-1 text-xs font-semibold text-slate-700 hover:text-navy-950 hover:bg-slate-200/80 rounded-lg transition-all"
                            >
                              View
                            </button>

                            <a
                              href={downloadUrl}
                              download={att.name || "material.pdf"}
                              target="_blank"
                              rel="noreferrer"
                              className="px-3 py-1 text-xs font-semibold rounded-lg bg-navy-950 hover:bg-navy-900 text-white shadow-xs transition-all flex items-center space-x-1"
                            >
                              <Download className="w-3 h-3" />
                              <span>Download</span>
                            </a>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <div className="p-4 rounded-xl border border-dashed border-slate-200 text-center text-xs text-slate-400">
                    No downloadable lecture materials uploaded for this lesson yet.
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Section: Course Progress Cards & Navigation Footer */}
        <div className="space-y-4 pt-4 border-t border-slate-200">
          <div className="flex items-center space-x-2 text-navy-950 font-bold text-sm font-heading">
            <CheckCircle2 className="w-4 h-4 text-blue-600" />
            <span>Course Progress</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {/* 1. Completed Lessons Card */}
            <div className="bg-white rounded-2xl border border-slate-200 p-4 sm:p-5 shadow-xs flex items-center space-x-4">
              <div className="w-12 h-12 rounded-xl bg-emerald-50 border border-emerald-100 flex items-center justify-center text-emerald-600 flex-shrink-0">
                <Check className="w-6 h-6 stroke-[3]" />
              </div>
              <div>
                <div className="text-xl sm:text-2xl font-black text-navy-950">
                  {completedCount} Completed
                </div>
                <div className="text-xs text-slate-400 font-medium">Lessons Finished</div>
              </div>
            </div>

            {/* 2. Remaining Lessons Card */}
            <div className="bg-white rounded-2xl border border-slate-200 p-4 sm:p-5 shadow-xs flex items-center space-x-4">
              <div className="w-12 h-12 rounded-xl bg-blue-50 border border-blue-100 flex items-center justify-center text-blue-600 flex-shrink-0">
                <Calendar className="w-6 h-6" />
              </div>
              <div>
                <div className="text-xl sm:text-2xl font-black text-navy-950">
                  {remainingCount} Remaining
                </div>
                <div className="text-xs text-slate-400 font-medium">Lessons Left</div>
              </div>
            </div>

            {/* 3. Overall Progress Card */}
            <div className="bg-white rounded-2xl border border-slate-200 p-4 sm:p-5 shadow-xs flex items-center space-x-4">
              <div className="w-12 h-12 rounded-xl bg-cyan-50 border border-cyan-100 flex items-center justify-center text-cyan-600 flex-shrink-0">
                <div className="w-6 h-6 rounded-full border-2 border-cyan-500 border-t-transparent animate-spin" />
              </div>
              <div>
                <div className="text-xl sm:text-2xl font-black text-navy-950">
                  {overallProgressPct}% Overall Progress
                </div>
                <div className="text-xs text-slate-400 font-medium">Total Completion</div>
              </div>
            </div>
          </div>

          {/* Quick Pagination bar */}
          <div className="bg-white rounded-xl border border-slate-200 p-3 flex flex-wrap items-center justify-between gap-3 text-xs">
            <button
              type="button"
              onClick={handlePrevLesson}
              disabled={activeLessonIndex === 0}
              className="inline-flex items-center space-x-1 px-3 py-1.5 font-semibold text-slate-600 hover:text-navy-950 disabled:opacity-30 disabled:cursor-not-allowed"
            >
              <ChevronLeft className="w-3.5 h-3.5" />
              <span>Previous Lesson</span>
            </button>

            <div className="flex items-center space-x-1 overflow-x-auto">
              {lessons.map((l, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => handleSelectLesson(idx)}
                  className={`w-7 h-7 rounded-lg text-xs font-bold transition-all ${
                    idx === activeLessonIndex
                      ? "bg-emerald-600 text-white shadow-xs"
                      : "text-slate-600 hover:bg-slate-100"
                  }`}
                >
                  {idx + 1}
                </button>
              ))}
            </div>

            <button
              type="button"
              onClick={handleNextLesson}
              disabled={activeLessonIndex >= lessons.length - 1}
              className="inline-flex items-center space-x-1 px-3 py-1.5 font-semibold text-slate-600 hover:text-navy-950 disabled:opacity-30 disabled:cursor-not-allowed"
            >
              <span>Next Lesson</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>

      {/* Material Document Preview Modal */}
      {previewMaterial && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4">
          <div className="bg-white rounded-2xl max-w-2xl w-full p-6 shadow-2xl space-y-4 border border-slate-200 animate-in fade-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="flex items-center space-x-2 truncate">
                <FileText className="w-5 h-5 text-red-600" />
                <h3 className="text-base font-bold text-navy-950 truncate">
                  {previewMaterial.name}
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setPreviewMaterial(null)}
                className="w-8 h-8 rounded-lg hover:bg-slate-100 flex items-center justify-center text-slate-400 hover:text-slate-700"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="bg-slate-50 rounded-xl p-8 text-center space-y-3 border border-slate-100">
              <FileText className="w-12 h-12 text-slate-400 mx-auto" />
              <p className="text-sm font-semibold text-navy-950">{previewMaterial.name}</p>
              <p className="text-xs text-slate-500">
                {previewMaterial.size || "PDF Document"} · Ready for review
              </p>
              <div className="pt-2 flex justify-center space-x-3">
                <a
                  href={previewMaterial.url || "#"}
                  download={previewMaterial.name}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center space-x-1.5 px-4 py-2 text-xs font-semibold rounded-lg bg-navy-950 text-white hover:bg-navy-900 transition-all shadow-xs"
                >
                  <Download className="w-3.5 h-3.5" />
                  <span>Download File</span>
                </a>
                <button
                  type="button"
                  onClick={() => setPreviewMaterial(null)}
                  className="px-4 py-2 text-xs font-semibold rounded-lg border border-slate-200 text-slate-700 hover:bg-slate-100"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CourseLearning;
