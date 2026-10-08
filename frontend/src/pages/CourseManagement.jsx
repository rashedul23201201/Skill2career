import React, { useState, useEffect, useRef } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import courseService from "../services/courseService";
import { ROUTES, USER_ROLES } from "../constants";
import {
  BookOpen,
  ChevronRight,
  ChevronDown,
  Plus,
  Trash2,
  FileText,
  Video,
  Upload,
  X,
  Eye,
  CheckCircle2,
  AlertCircle,
  Save,
  ArrowLeft,
  Settings,
  Sparkles,
  Layers,
  Paperclip,
} from "lucide-react";

export const CourseManagement = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const isNew = !id || id === "new";

  // Course State
  const [course, setCourse] = useState({
    title: "Data Structures & Algorithms in Python",
    description: "Comprehensive curriculum covering fundamental and advanced data structures and algorithms.",
    category: "Programming",
    level: "Intermediate",
    duration_weeks: 10,
    price: 0,
    is_free: true,
    status: "DRAFT",
    modules: [],
  });

  const [loading, setLoading] = useState(!isNew);
  const [saving, setSaving] = useState(false);
  const [statusUpdating, setStatusUpdating] = useState(false);
  const [message, setMessage] = useState(null);
  const [error, setError] = useState(null);

  // Curriculum State
  const [modules, setModules] = useState([
    {
      id: "mod-1",
      title: "Module 1: Foundations of Algorithms",
      order_index: 0,
      expanded: true,
      lessons: [
        {
          id: "les-1",
          title: "Asymptotic Notation & Analysis",
          duration: "30 Mins",
          video_url: "https://www.youtube.com/embed/dQw4w9WgXcQ",
          content_type: "video",
          attachments: [{ name: "Algorithm_Basics.pdf", size: "1.2 MB" }],
        },
      ],
    },
    {
      id: "mod-2",
      title: "Module 2: Linear Data Structures",
      order_index: 1,
      expanded: true,
      lessons: [
        { id: "les-2", title: "Lesson: Linked Lists", duration: "35 Mins", video_url: "", content_type: "video", attachments: [] },
        { id: "les-3", title: "Lesson: Theory Trees", duration: "40 Mins", video_url: "", content_type: "video", attachments: [] },
        { id: "les-4", title: "Lesson: Backend Intras", duration: "25 Mins", video_url: "", content_type: "video", attachments: [] },
        { id: "les-5", title: "Lesson: Retrenchobe Lists", duration: "30 Mins", video_url: "", content_type: "video", attachments: [] },
        {
          id: "les-6",
          title: "Binary Trees and Traversal Strategies",
          duration: "45 Mins",
          video_url: "https://www.youtube.com/embed/dQw4w9WgXcQ",
          content_type: "video",
          attachments: [
            { name: "Lecture_Notes_Trees.pdf", size: "2.4 MB" },
            { name: "Binary_Tree_Code_Examples.pdf", size: "1.8 MB" },
            { name: "Lecture_Notes.pdf", size: "2.16 MB" },
          ],
        },
      ],
    },
    {
      id: "mod-3",
      title: "Module 3: Solved Strategies",
      order_index: 2,
      expanded: true,
      lessons: [
        { id: "les-7", title: "Lesson: Dynamic Programming", duration: "50 Mins", video_url: "", content_type: "video", attachments: [] },
        { id: "les-8", title: "Lesson: Graph Traversals", duration: "45 Mins", video_url: "", content_type: "video", attachments: [] },
      ],
    },
  ]);

  // Active Selected Lesson in the right panel
  const [activeModuleIndex, setActiveModuleIndex] = useState(1);
  const [activeLessonIndex, setActiveLessonIndex] = useState(4); // "Binary Trees and Traversal Strategies"

  // Active Lesson Form
  const [activeLessonData, setActiveLessonData] = useState({
    title: "Binary Trees and Traversal Strategies",
    duration: "45 Mins",
    video_url: "https://www.youtube.com/embed/dQw4w9WgXcQ",
    content_type: "video",
    attachments: [
      { name: "Lecture_Notes_Trees.pdf", size: "2.4 MB" },
      { name: "Binary_Tree_Code_Examples.pdf", size: "1.8 MB" },
      { name: "Lecture_Notes.pdf", size: "2.16 MB" },
    ],
  });

  // Course Settings Modal
  const [showSettingsModal, setShowSettingsModal] = useState(false);

  // File Upload Ref
  const fileInputRef = useRef(null);

  // Load Course Details
  useEffect(() => {
    if (isNew) return;

    const fetchCourse = async () => {
      try {
        setLoading(true);
        setError(null);
        const res = await courseService.getCourseById(id);
        if (res?.data) {
          const c = res.data;
          setCourse(c);

          // Populate modules
          if (c.modules && c.modules.length > 0) {
            const formattedModules = c.modules.map((m) => ({
              id: m.id,
              title: m.title,
              order_index: m.order_index,
              expanded: true,
              lessons: (m.lessons || []).map((l) => ({
                id: l.id,
                title: l.title,
                duration: `${l.duration_minutes || 30} Mins`,
                video_url: l.video_url || "",
                study_material_url: l.study_material_url || "",
                content_type: l.content_type || "video",
                attachments: l.attachments || [],
              })),
            }));
            setModules(formattedModules);

            if (formattedModules[0]?.lessons?.length > 0) {
              setActiveModuleIndex(0);
              setActiveLessonIndex(0);
              setActiveLessonData(formattedModules[0].lessons[0]);
            }
          }
        }
      } catch (err) {
        console.error("Error loading course:", err);
        setError("Failed to load course details. Ensure the ID is valid.");
      } finally {
        setLoading(false);
      }
    };

    fetchCourse();
  }, [id, isNew]);

  // Select a lesson to edit in the right pane
  const handleSelectLesson = (mIdx, lIdx) => {
    setActiveModuleIndex(mIdx);
    setActiveLessonIndex(lIdx);
    const selectedLesson = modules[mIdx]?.lessons[lIdx];
    if (selectedLesson) {
      setActiveLessonData({
        ...selectedLesson,
        attachments: selectedLesson.attachments || [],
      });
    }
  };

  // Toggle Module Expand/Collapse
  const toggleModule = (mIdx) => {
    setModules((prev) =>
      prev.map((mod, i) => (i === mIdx ? { ...mod, expanded: !mod.expanded } : mod))
    );
  };

  // Add Module
  const handleAddModule = () => {
    const newModNumber = modules.length + 1;
    const newModule = {
      id: `temp-mod-${Date.now()}`,
      title: `Module ${newModNumber}: New Topic`,
      order_index: modules.length,
      expanded: true,
      lessons: [
        {
          id: `temp-les-${Date.now()}`,
          title: "Introduction",
          duration: "30 Mins",
          video_url: "",
          content_type: "video",
          attachments: [],
        },
      ],
    };
    const updated = [...modules, newModule];
    setModules(updated);
    setActiveModuleIndex(updated.length - 1);
    setActiveLessonIndex(0);
    setActiveLessonData(newModule.lessons[0]);
  };

  // Add Lesson to a specific module
  const handleAddLesson = (mIdx, e) => {
    e.stopPropagation();
    const targetModule = modules[mIdx];
    const newLessonNumber = (targetModule.lessons || []).length + 1;
    const newLesson = {
      id: `temp-les-${Date.now()}`,
      title: `Lesson: New Concept ${newLessonNumber}`,
      duration: "30 Mins",
      video_url: "",
      content_type: "video",
      attachments: [],
    };

    const updated = modules.map((mod, i) => {
      if (i === mIdx) {
        return {
          ...mod,
          expanded: true,
          lessons: [...(mod.lessons || []), newLesson],
        };
      }
      return mod;
    });

    setModules(updated);
    setActiveModuleIndex(mIdx);
    setActiveLessonIndex(updated[mIdx].lessons.length - 1);
    setActiveLessonData(newLesson);
  };

  // Remove Module
  const handleRemoveModule = (mIdx, e) => {
    e.stopPropagation();
    if (modules.length <= 1) {
      alert("A course must have at least one module.");
      return;
    }
    const updated = modules.filter((_, i) => i !== mIdx);
    setModules(updated);
    setActiveModuleIndex(0);
    setActiveLessonIndex(0);
    if (updated[0]?.lessons[0]) {
      setActiveLessonData(updated[0].lessons[0]);
    }
  };

  // Remove Lesson
  const handleRemoveLesson = (mIdx, lIdx, e) => {
    e.stopPropagation();
    const targetMod = modules[mIdx];
    if (targetMod.lessons.length <= 1) {
      alert("Each module must have at least one lesson.");
      return;
    }
    const updatedLessons = targetMod.lessons.filter((_, i) => i !== lIdx);
    const updated = modules.map((mod, i) =>
      i === mIdx ? { ...mod, lessons: updatedLessons } : mod
    );
    setModules(updated);
    setActiveLessonIndex(0);
    setActiveLessonData(updatedLessons[0]);
  };

  // Update current active lesson field
  const handleLessonFieldChange = (field, value) => {
    setActiveLessonData((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  // Add File Attachment (direct upload or local preview)
  const handleAddAttachment = async (e) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    const file = files[0];
    const sizeInMB = (file.size / (1024 * 1024)).toFixed(2);

    if (activeLessonData.id && typeof activeLessonData.id === "number") {
      try {
        const uploadRes = await courseService.uploadLessonMaterial(activeLessonData.id, file);
        if (uploadRes?.data) {
          const uploaded = uploadRes.data;
          setActiveLessonData((prev) => ({
            ...prev,
            attachments: [
              ...(prev.attachments || []),
              {
                name: uploaded.name,
                size: uploaded.size,
                url: uploaded.file_url,
                filename: uploaded.filename,
              },
            ],
          }));
          if (fileInputRef.current) fileInputRef.current.value = "";
          return;
        }
      } catch (err) {
        console.warn("Backend material upload failed, using local preview:", err);
      }
    }

    const newAttachment = {
      name: file.name,
      size: `${sizeInMB} MB`,
    };

    setActiveLessonData((prev) => ({
      ...prev,
      attachments: [...(prev.attachments || []), newAttachment],
    }));

    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  // Remove Attachment
  const handleRemoveAttachment = (attIdx) => {
    setActiveLessonData((prev) => ({
      ...prev,
      attachments: prev.attachments.filter((_, i) => i !== attIdx),
    }));
  };

  // Apply changes to the active lesson in the modules array
  const handleApplyLessonChanges = () => {
    setModules((prev) =>
      prev.map((mod, mIdx) => {
        if (mIdx === activeModuleIndex) {
          const updatedLessons = mod.lessons.map((les, lIdx) => {
            if (lIdx === activeLessonIndex) {
              return { ...activeLessonData };
            }
            return les;
          });
          return { ...mod, lessons: updatedLessons };
        }
        return mod;
      })
    );
    setMessage("Lesson changes applied. Remember to save & publish!");
    setTimeout(() => setMessage(null), 3000);
  };

  // Save Full Course & Curriculum Outline
  const handleSaveAndSync = async (publish = false) => {
    try {
      setSaving(true);
      setError(null);
      setMessage(null);

      // Make sure active lesson changes are synced first
      const updatedModules = modules.map((mod, mIdx) => {
        if (mIdx === activeModuleIndex) {
          const updatedLessons = mod.lessons.map((les, lIdx) => {
            if (lIdx === activeLessonIndex) {
              return { ...activeLessonData };
            }
            return les;
          });
          return { ...mod, lessons: updatedLessons };
        }
        return mod;
      });

      // Prepare payload
      const statusToSet = publish
        ? "PUBLISHED"
        : course.status || "DRAFT";

      let courseId = id;

      if (isNew) {
        // Create course first
        const createPayload = {
          title: course.title,
          description: course.description,
          category: course.category,
          level: course.level,
          duration_weeks: Number(course.duration_weeks) || 8,
          price: Number(course.price) || 0,
          is_free: course.is_free,
          status: statusToSet,
        };
        const createRes = await courseService.createCourse(createPayload);
        courseId = createRes.data.id;
      } else {
        // Update metadata
        await courseService.updateCourse(courseId, {
          title: course.title,
          description: course.description,
          category: course.category,
          level: course.level,
          duration_weeks: Number(course.duration_weeks) || 8,
          price: Number(course.price) || 0,
          is_free: course.is_free,
          status: statusToSet,
        });
      }

      // Format curriculum tree for sync
      const curriculumPayload = updatedModules.map((m, mIdx) => ({
        title: m.title,
        order_index: mIdx,
        lessons: m.lessons.map((l, lIdx) => {
          // Parse minutes from "45 Mins"
          const parsedMinutes = parseInt(l.duration, 10) || 30;
          return {
            title: l.title,
            duration_minutes: parsedMinutes,
            content_type: l.content_type || "video",
            video_url: l.video_url || null,
            attachments: l.attachments || [],
            order_index: lIdx,
          };
        }),
      }));

      await courseService.syncCurriculum(courseId, curriculumPayload);

      setCourse((prev) => ({ ...prev, status: statusToSet }));
      setMessage(
        publish
          ? "Course successfully published! Learners can now view it."
          : "Course and curriculum outline saved successfully!"
      );

      if (isNew) {
        navigate(`/courses/${courseId}/manage`);
      }
    } catch (err) {
      console.error("Save error:", err);
      setError(
        err.response?.data?.message ||
          "Failed to save curriculum outline. Please check required fields."
      );
    } finally {
      setSaving(false);
      setTimeout(() => setMessage(null), 4000);
    }
  };

  // Toggle publish / unpublish
  const handleTogglePublish = async () => {
    if (isNew) {
      handleSaveAndSync(true);
      return;
    }

    try {
      setStatusUpdating(true);
      setError(null);
      const newStatus =
        course.status === "PUBLISHED" ? "UNPUBLISHED" : "PUBLISHED";
      const res = await courseService.updateCourseStatus(id, {
        status: newStatus,
        reason: "Instructor status toggle",
      });
      setCourse((prev) => ({ ...prev, status: newStatus }));
      setMessage(
        newStatus === "PUBLISHED"
          ? "Course published! It is now live on Explore Courses."
          : "Course unpublished. It is no longer visible to learners."
      );
    } catch (err) {
      console.error("Status update error:", err);
      setError("Failed to update course publication status.");
    } finally {
      setStatusUpdating(false);
      setTimeout(() => setMessage(null), 4000);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Top Banner & Header matching Course Management.png */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-slate-100">
        <div>
          <div className="flex items-center space-x-2 text-xs font-semibold text-slate-400 mb-1">
            <Link
              to={ROUTES.COURSES}
              className="hover:text-blue-600 flex items-center space-x-1"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Back to Courses</span>
            </Link>
            <span>/</span>
            <span>Curriculum Builder</span>
          </div>

          <h1 className="text-2xl sm:text-3xl font-extrabold text-navy-950 font-heading">
            Course Management & Curriculum Builder
          </h1>

          <div className="flex items-center space-x-3 mt-1.5">
            <h2 className="text-lg font-bold text-slate-700">
              {course.title}
            </h2>
            <span
              className={`px-3 py-0.5 text-xs font-bold rounded-full border ${
                course.status === "PUBLISHED"
                  ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                  : "bg-blue-50 text-blue-700 border-blue-200"
              }`}
            >
              {course.status === "PUBLISHED"
                ? "Published - Live"
                : "Draft - Ready to Publish"}
            </span>

            <button
              type="button"
              onClick={() => setShowSettingsModal(true)}
              className="text-xs font-semibold text-blue-600 hover:text-blue-800 flex items-center space-x-1 pl-2 border-l border-slate-200"
            >
              <Settings className="w-3.5 h-3.5" />
              <span>Edit Course Info</span>
            </button>
          </div>
        </div>

        {/* Top Action Buttons matching Course Management.png */}
        <div className="flex items-center space-x-3 self-start md:self-auto">
          {!isNew && (
            <Link
              to={`/courses/${id}/learn`}
              className="inline-flex items-center space-x-1.5 px-4 py-2 text-xs font-semibold rounded-lg border border-slate-300 bg-white hover:bg-slate-50 text-navy-950 shadow-sm transition-all"
            >
              <Eye className="w-3.5 h-3.5 text-slate-600" />
              <span>Preview as Learner</span>
            </Link>
          )}

          <button
            type="button"
            onClick={() => handleSaveAndSync(course.status !== "PUBLISHED")}
            disabled={saving || statusUpdating}
            className="inline-flex items-center space-x-1.5 px-4 py-2 text-xs font-semibold rounded-lg bg-navy-950 hover:bg-navy-900 text-white shadow-sm transition-all hover:shadow disabled:opacity-50"
          >
            <Save className="w-3.5 h-3.5 text-emerald-400" />
            <span>
              {saving
                ? "Saving..."
                : course.status === "PUBLISHED"
                ? "Save & Keep Published"
                : "Save & Publish Course"}
            </span>
          </button>
        </div>
      </div>

      {/* Notifications */}
      {message && (
        <div className="p-3.5 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-medium flex items-center space-x-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
          <span>{message}</span>
        </div>
      )}

      {error && (
        <div className="p-3.5 rounded-xl bg-crimson-50 border border-crimson-200 text-crimson-700 text-xs font-medium flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 text-crimson flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Main 2-Column Grid matching Course Management.png */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Curriculum Outline Card (Course Management.png) */}
        <div className="lg:col-span-6 bg-white rounded-2xl border border-slate-200 p-6 shadow-sm flex flex-col justify-between space-y-6">
          <div className="space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-4">
              <h3 className="text-base font-bold text-navy-950 font-heading">
                Curriculum Outline
              </h3>
              <button
                type="button"
                onClick={handleAddModule}
                className="inline-flex items-center space-x-1 px-3 py-1.5 text-xs font-semibold rounded-lg bg-blue-600 hover:bg-blue-700 text-white transition-colors shadow-sm"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Add Module</span>
              </button>
            </div>

            {/* Modules List Tree */}
            <div className="space-y-4">
              {modules.map((mod, mIdx) => (
                <div
                  key={mod.id || mIdx}
                  className="rounded-xl border border-slate-200 overflow-hidden bg-slate-50/50"
                >
                  {/* Module Header Bar */}
                  <div
                    onClick={() => toggleModule(mIdx)}
                    className="p-3.5 bg-slate-100/70 hover:bg-slate-100 cursor-pointer flex items-center justify-between select-none transition-colors"
                  >
                    <div className="flex items-center space-x-2">
                      {mod.expanded ? (
                        <ChevronDown className="w-4 h-4 text-slate-500" />
                      ) : (
                        <ChevronRight className="w-4 h-4 text-slate-500" />
                      )}
                      <span className="text-xs font-bold text-navy-900">
                        {mod.title}
                      </span>
                    </div>

                    <div className="flex items-center space-x-2">
                      <button
                        type="button"
                        onClick={(e) => handleAddLesson(mIdx, e)}
                        className="px-2.5 py-1 text-[11px] font-semibold rounded-md bg-blue-600 hover:bg-blue-700 text-white shadow-sm flex items-center space-x-1"
                        title="Add lesson to this module"
                      >
                        <Plus className="w-3 h-3" />
                        <span>Add Lesson</span>
                      </button>
                      <button
                        type="button"
                        onClick={(e) => handleRemoveModule(mIdx, e)}
                        className="p-1 text-slate-400 hover:text-crimson transition-colors"
                        title="Delete module"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>

                  {/* Lessons List inside Module */}
                  {mod.expanded && (
                    <div className="p-2 space-y-1 bg-white">
                      {mod.lessons.map((les, lIdx) => {
                        const isActive =
                          mIdx === activeModuleIndex &&
                          lIdx === activeLessonIndex;

                        return (
                          <div
                            key={les.id || lIdx}
                            onClick={() => handleSelectLesson(mIdx, lIdx)}
                            className={`flex items-center justify-between p-2.5 rounded-lg cursor-pointer transition-all ${
                              isActive
                                ? "bg-blue-50/80 border border-blue-200 text-blue-900 font-semibold shadow-xs"
                                : "hover:bg-slate-50 text-slate-700 font-normal"
                            }`}
                          >
                            <div className="flex items-center space-x-2.5 overflow-hidden">
                              <FileText
                                className={`w-3.5 h-3.5 flex-shrink-0 ${
                                  isActive ? "text-blue-600" : "text-slate-400"
                                }`}
                              />
                              <span className="text-xs truncate">
                                {les.title}
                              </span>
                            </div>

                            <div className="flex items-center space-x-2 flex-shrink-0">
                              <span className="text-[11px] text-slate-400">
                                {les.duration}
                              </span>
                              <button
                                type="button"
                                onClick={(e) => handleRemoveLesson(mIdx, lIdx, e)}
                                className="p-1 text-slate-300 hover:text-crimson transition-colors"
                                title="Remove lesson"
                              >
                                <X className="w-3 h-3" />
                              </button>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          <div className="pt-4 border-t border-slate-100 flex items-center justify-between text-xs text-slate-400">
            <span>
              Total {modules.length} Modules ·{" "}
              {modules.reduce((acc, m) => acc + (m.lessons?.length || 0), 0)}{" "}
              Lessons
            </span>
            <button
              type="button"
              onClick={() => handleSaveAndSync(false)}
              className="text-xs font-semibold text-blue-600 hover:text-blue-800"
            >
              Quick Save Outline
            </button>
          </div>
        </div>

        {/* Right Column: Edit Lesson Details Card (Course Management.png) */}
        <div className="lg:col-span-6 bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-6">
          <div className="border-b border-slate-100 pb-4 flex items-center justify-between">
            <h3 className="text-base font-bold text-navy-950 font-heading">
              Edit Lesson Details
            </h3>
            <span className="text-xs text-slate-400 font-medium">
              Editing: {activeLessonData.title}
            </span>
          </div>

          <div className="space-y-4">
            {/* Lesson Title & Duration Inputs */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div className="sm:col-span-2 space-y-1.5">
                <label className="text-xs font-semibold text-slate-700">
                  Lesson Title
                </label>
                <input
                  type="text"
                  value={activeLessonData.title}
                  onChange={(e) =>
                    handleLessonFieldChange("title", e.target.value)
                  }
                  placeholder="e.g. Binary Trees and Traversal Strategies"
                  className="w-full px-3.5 py-2.5 bg-white border border-slate-300 rounded-xl text-xs focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 text-navy-950 font-medium"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-700">
                  Duration
                </label>
                <input
                  type="text"
                  value={activeLessonData.duration}
                  onChange={(e) =>
                    handleLessonFieldChange("duration", e.target.value)
                  }
                  placeholder="45 Mins"
                  className="w-full px-3.5 py-2.5 bg-white border border-slate-300 rounded-xl text-xs focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 text-navy-950 font-medium"
                />
              </div>
            </div>

            {/* Video Embed Link Input */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-700 flex items-center justify-between">
                <span>Video Embed Link</span>
                <span className="text-[11px] font-normal text-slate-400">
                  YouTube embed or direct video URL
                </span>
              </label>
              <input
                type="text"
                value={activeLessonData.video_url || ""}
                onChange={(e) =>
                  handleLessonFieldChange("video_url", e.target.value)
                }
                placeholder="https://www.youtube.com/embed/..."
                className="w-full px-3.5 py-2.5 bg-white border border-slate-300 rounded-xl text-xs focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 text-navy-950 font-mono"
              />
            </div>

            {/* Video Preview Iframe if link is valid */}
            {activeLessonData.video_url &&
              activeLessonData.video_url.includes("embed") && (
                <div className="aspect-video w-full rounded-xl overflow-hidden border border-slate-200 bg-black">
                  <iframe
                    src={activeLessonData.video_url}
                    title="Lesson Preview"
                    className="w-full h-full"
                    allowFullScreen
                  />
                </div>
              )}

            {/* Study Material Attachments matching Course Management.png */}
            <div className="space-y-2 pt-2">
              <div className="flex items-center justify-between">
                <label className="text-xs font-semibold text-slate-700">
                  Study Material Attachments
                </label>
                <span className="text-[11px] text-slate-400">
                  {(activeLessonData.attachments || []).length} attached
                </span>
              </div>

              {/* Dashed Dropzone */}
              <div className="rounded-2xl border-2 border-dashed border-slate-300 bg-slate-50/50 p-4 space-y-3">
                {/* List of Attached Files */}
                {(activeLessonData.attachments || []).map((file, attIdx) => (
                  <div
                    key={attIdx}
                    className="flex items-center justify-between p-2.5 rounded-xl bg-blue-50/70 border border-blue-200/60 text-xs text-navy-950"
                  >
                    <div className="flex items-center space-x-2 truncate">
                      <FileText className="w-4 h-4 text-blue-600 flex-shrink-0" />
                      <span className="font-medium truncate">
                        {file.name} {file.size ? `(${file.size})` : ""}
                      </span>
                    </div>
                    <button
                      type="button"
                      onClick={() => handleRemoveAttachment(attIdx)}
                      className="p-1 text-slate-400 hover:text-crimson transition-colors"
                      title="Remove attachment"
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                  </div>
                ))}

                {/* Upload Trigger Dropzone */}
                <div className="flex flex-col items-center justify-center py-4 text-center">
                  <Upload className="w-6 h-6 text-slate-400 mb-2" />
                  <p className="text-xs text-slate-600 font-medium">
                    Upload or drag files here
                  </p>
                  <p className="text-[11px] text-slate-400 mt-0.5">
                    PDFs, slides, lecture notes up to 25 MB
                  </p>
                  <input
                    type="file"
                    ref={fileInputRef}
                    onChange={handleAddAttachment}
                    className="hidden"
                  />
                  <button
                    type="button"
                    onClick={() => fileInputRef.current?.click()}
                    className="mt-3 px-3 py-1.5 text-xs font-semibold rounded-lg border border-slate-300 bg-white hover:bg-slate-50 text-slate-700 transition-colors shadow-xs"
                  >
                    Choose Document
                  </button>
                </div>
              </div>
            </div>

            {/* Bottom Lesson Action Bar */}
            <div className="pt-4 border-t border-slate-100 flex items-center justify-between">
              <button
                type="button"
                onClick={handleApplyLessonChanges}
                className="inline-flex items-center space-x-1.5 px-4 py-2 text-xs font-semibold rounded-lg bg-blue-600 hover:bg-blue-700 text-white shadow-sm transition-colors"
              >
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Apply Lesson Changes</span>
              </button>

              <button
                type="button"
                onClick={() => handleSaveAndSync(false)}
                disabled={saving}
                className="inline-flex items-center space-x-1.5 px-4 py-2 text-xs font-semibold rounded-lg bg-navy-950 hover:bg-navy-900 text-white shadow-sm transition-colors disabled:opacity-50"
              >
                <Save className="w-3.5 h-3.5 text-emerald-400" />
                <span>Save All Curriculum</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Course Settings / Metadata Modal */}
      {showSettingsModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4">
          <div className="bg-white rounded-2xl border border-slate-200 max-w-lg w-full p-6 space-y-4 shadow-xl">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="text-base font-bold text-navy-950 font-heading">
                Course Information & Settings
              </h3>
              <button
                type="button"
                onClick={() => setShowSettingsModal(false)}
                className="p-1 text-slate-400 hover:text-slate-600"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <label className="font-semibold text-slate-700 block mb-1">
                  Course Title
                </label>
                <input
                  type="text"
                  value={course.title}
                  onChange={(e) =>
                    setCourse({ ...course, title: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-navy-950"
                />
              </div>

              <div>
                <label className="font-semibold text-slate-700 block mb-1">
                  Description
                </label>
                <textarea
                  rows={3}
                  value={course.description}
                  onChange={(e) =>
                    setCourse({ ...course, description: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-navy-950"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="font-semibold text-slate-700 block mb-1">
                    Category
                  </label>
                  <select
                    value={course.category}
                    onChange={(e) =>
                      setCourse({ ...course, category: e.target.value })
                    }
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg text-navy-950"
                  >
                    <option value="Programming">Programming</option>
                    <option value="Web Development">Web Development</option>
                    <option value="Database">Database</option>
                    <option value="Software Engineering">
                      Software Engineering
                    </option>
                  </select>
                </div>

                <div>
                  <label className="font-semibold text-slate-700 block mb-1">
                    Difficulty Level
                  </label>
                  <select
                    value={course.level}
                    onChange={(e) =>
                      setCourse({ ...course, level: e.target.value })
                    }
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg text-navy-950"
                  >
                    <option value="Beginner">Beginner</option>
                    <option value="Intermediate">Intermediate</option>
                    <option value="Advanced">Advanced</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="font-semibold text-slate-700 block mb-1">
                  Duration (Weeks)
                </label>
                <input
                  type="number"
                  min="1"
                  max="52"
                  value={course.duration_weeks || 8}
                  onChange={(e) =>
                    setCourse({
                      ...course,
                      duration_weeks: parseInt(e.target.value, 10) || 8,
                    })
                  }
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-navy-950"
                />
              </div>
            </div>

            <div className="pt-3 border-t border-slate-100 flex justify-end space-x-2">
              <button
                type="button"
                onClick={() => setShowSettingsModal(false)}
                className="px-4 py-2 text-xs font-semibold rounded-lg border border-slate-300 hover:bg-slate-50 text-slate-700"
              >
                Close
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowSettingsModal(false);
                  handleSaveAndSync(false);
                }}
                className="px-4 py-2 text-xs font-semibold rounded-lg bg-navy-950 hover:bg-navy-900 text-white"
              >
                Save Settings
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CourseManagement;
