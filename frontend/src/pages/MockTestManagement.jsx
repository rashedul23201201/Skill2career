import React, { useState, useEffect } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import mockTestService from "../services/mockTestService";
import { ROUTES } from "../constants";
import {
  ArrowLeft,
  Plus,
  Save,
  Trash2,
  Edit3,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  X,
} from "lucide-react";

export const MockTestManagement = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const isNew = !id || id === "new";

  const [formData, setFormData] = useState({
    title: "",
    category: "Programming",
    description: "",
    duration_minutes: 60,
    passing_score: 50,
    status: "DRAFT",
  });

  const [questions, setQuestions] = useState([]);
  const [loading, setLoading] = useState(!isNew);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  const [isQuestionModalOpen, setIsQuestionModalOpen] = useState(false);
  const [editingQuestionIndex, setEditingQuestionIndex] = useState(null);
  const [questionForm, setQuestionForm] = useState({
    question_text: "",
    options: ["", "", "", ""],
    correct_option: "A",
    marks: 1,
    explanation: "",
  });

  const categories = ["Programming", "Database", "Web Development", "Other"];

  useEffect(() => {
    if (!isNew) {
      const fetchTest = async () => {
        try {
          setLoading(true);
          setError(null);
          const res = await mockTestService.getMockTestById(id);
          if (res?.data) {
            setFormData({
              title: res.data.title || "",
              category: res.data.category || "Programming",
              description: res.data.description || "",
              duration_minutes: res.data.duration_minutes || 60,
              passing_score: res.data.passing_score || 50,
              status: res.data.status || "DRAFT",
            });
            if (res.data.questions) {
              setQuestions(res.data.questions);
            }
          }
        } catch (err) {
          console.error("Failed to fetch mock test:", err);
          setError("Failed to load mock test details.");
        } finally {
          setLoading(false);
        }
      };
      fetchTest();
    }
  }, [id, isNew]);

  const handleInputChange = (e) => {
    const { name, value, type } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === "number" ? Number(value) : value,
    }));
  };

  const handleSaveTest = async (e) => {
    if (e) e.preventDefault();
    if (!formData.title.trim()) {
      setError("Please provide a test title.");
      return;
    }

    try {
      setSaving(true);
      setError(null);

      if (isNew) {
        const res = await mockTestService.createMockTest({
          ...formData,
          duration_minutes: Number(formData.duration_minutes),
          passing_score: Number(formData.passing_score),
        });
        if (res?.data?.id) {
          const newId = res.data.id;
          if (questions.length > 0) {
            await mockTestService.syncQuestions(newId, questions);
          }
          setSuccess("Mock test created successfully!");
          setTimeout(() => {
            navigate(ROUTES.MOCK_TEST_MANAGE.replace(":id", newId));
          }, 800);
        }
      } else {
        await mockTestService.updateMockTest(id, {
          ...formData,
          duration_minutes: Number(formData.duration_minutes),
          passing_score: Number(formData.passing_score),
        });
        await mockTestService.syncQuestions(id, questions);
        setSuccess("Mock test and questions updated successfully!");
        setTimeout(() => setSuccess(null), 3000);
      }
    } catch (err) {
      console.error("Failed to save mock test:", err);
      setError(err.response?.data?.message || "Failed to save mock test.");
    } finally {
      setSaving(false);
    }
  };

  const handleOpenAddQuestion = () => {
    setEditingQuestionIndex(null);
    setQuestionForm({
      question_text: "",
      options: ["", "", "", ""],
      correct_option: "A",
      marks: 1,
      explanation: "",
    });
    setIsQuestionModalOpen(true);
  };

  const handleOpenEditQuestion = (index) => {
    setEditingQuestionIndex(index);
    const target = questions[index];
    setQuestionForm({
      question_text: target.question_text,
      options: [...(target.options || ["", "", "", ""])],
      correct_option: target.correct_option || "A",
      marks: target.marks || 1,
      explanation: target.explanation || "",
    });
    setIsQuestionModalOpen(true);
  };

  const handleOptionChange = (idx, value) => {
    setQuestionForm((prev) => {
      const nextOpts = [...prev.options];
      nextOpts[idx] = value;
      return { ...prev, options: nextOpts };
    });
  };

  const handleSaveQuestionModal = () => {
    if (!questionForm.question_text.trim()) {
      alert("Question prompt cannot be empty.");
      return;
    }
    const filledOptions = questionForm.options.filter((opt) => opt.trim() !== "");
    if (filledOptions.length < 2) {
      alert("A question must have at least 2 non-empty options.");
      return;
    }

    const newQuestion = {
      question_text: questionForm.question_text.trim(),
      options: filledOptions,
      correct_option: questionForm.correct_option,
      marks: Number(questionForm.marks) || 1,
      explanation: questionForm.explanation.trim() || null,
      order_index: editingQuestionIndex !== null ? editingQuestionIndex : questions.length,
    };

    if (editingQuestionIndex !== null) {
      setQuestions((prev) => {
        const next = [...prev];
        next[editingQuestionIndex] = newQuestion;
        return next;
      });
    } else {
      setQuestions((prev) => [...prev, newQuestion]);
    }

    setIsQuestionModalOpen(false);
  };

  const handleDeleteQuestion = (index) => {
    setQuestions((prev) => prev.filter((_, idx) => idx !== index));
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-brandBg py-16 flex items-center justify-center">
        <div className="text-center space-y-3">
          <div className="w-8 h-8 border-4 border-navy-950 border-t-transparent rounded-full animate-spin mx-auto"></div>
          <p className="text-xs text-slate-500 font-medium">Loading test editor...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-brandBg py-10 px-4 sm:px-6 lg:px-8">
      <div className="max-w-5xl mx-auto space-y-8">
        {/* Navigation & Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            <Link
              to={ROUTES.MOCK_TESTS}
              className="p-2 bg-white border border-slate-200 rounded-xl text-slate-600 hover:text-navy-950 hover:bg-slate-50 transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
            </Link>
            <div>
              <div className="flex items-center space-x-2">
                <h1 className="text-2xl sm:text-3xl font-extrabold text-navy-950 font-heading">
                  {isNew ? "Create Mock Test" : "Manage Mock Test"}
                </h1>
                <span
                  className={`text-xs px-2.5 py-0.5 rounded-full font-bold ${
                    formData.status === "PUBLISHED"
                      ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                      : "bg-slate-100 text-slate-700 border border-slate-200"
                  }`}
                >
                  {formData.status}
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-1">
                Configure exam parameters and author multiple-choice question items.
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-3 self-end sm:self-auto">
            <button
              onClick={() => {
                const nextStatus = formData.status === "PUBLISHED" ? "DRAFT" : "PUBLISHED";
                setFormData((prev) => ({ ...prev, status: nextStatus }));
              }}
              type="button"
              className={`px-4 py-2 rounded-xl text-xs font-semibold border transition-all ${
                formData.status === "PUBLISHED"
                  ? "bg-amber-50 text-amber-700 border-amber-200 hover:bg-amber-100"
                  : "bg-emerald-50 text-emerald-700 border-emerald-200 hover:bg-emerald-100"
              }`}
            >
              {formData.status === "PUBLISHED" ? "Unpublish Test" : "Publish Test"}
            </button>

            <button
              onClick={handleSaveTest}
              disabled={saving}
              className="inline-flex items-center space-x-2 px-5 py-2 bg-navy-950 hover:bg-navy-900 text-white rounded-xl text-xs sm:text-sm font-semibold shadow-sm transition-all disabled:opacity-50"
            >
              <Save className="w-4 h-4" />
              <span>{saving ? "Saving..." : "Save Changes"}</span>
            </button>
          </div>
        </div>

        {/* Alerts */}
        {error && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-red-700 text-xs sm:text-sm flex items-center space-x-3">
            <AlertCircle className="w-5 h-5 flex-shrink-0 text-red-500" />
            <span>{error}</span>
          </div>
        )}
        {success && (
          <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl text-emerald-800 text-xs sm:text-sm flex items-center space-x-3">
            <CheckCircle2 className="w-5 h-5 flex-shrink-0 text-emerald-500" />
            <span>{success}</span>
          </div>
        )}

        {/* Section 1: Test Metadata Form */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6 sm:p-8 shadow-sm space-y-6">
          <div className="border-b border-slate-100 pb-4">
            <h2 className="text-lg font-bold text-navy-950 font-heading">
              Assessment Details
            </h2>
            <p className="text-xs text-slate-500">
              Basic properties and passing criteria for this test.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="md:col-span-2 space-y-1.5">
              <label className="text-xs font-bold text-slate-700">Test Title *</label>
              <input
                type="text"
                name="title"
                value={formData.title}
                onChange={handleInputChange}
                placeholder="e.g. Data Structures & Algorithms Practice Exam"
                className="w-full px-3.5 py-2.5 text-sm bg-white border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-navy-900 text-navy-950"
                required
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-bold text-slate-700">Category *</label>
              <select
                name="category"
                value={formData.category}
                onChange={handleInputChange}
                className="w-full px-3.5 py-2.5 text-sm bg-white border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-navy-900 text-navy-950"
              >
                {categories.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <label className="text-xs font-bold text-slate-700">
                  Duration (Minutes) *
                </label>
                <input
                  type="number"
                  name="duration_minutes"
                  value={formData.duration_minutes}
                  onChange={handleInputChange}
                  min="5"
                  max="360"
                  className="w-full px-3.5 py-2.5 text-sm bg-white border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-navy-900 text-navy-950"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-bold text-slate-700">
                  Passing Score (%) *
                </label>
                <input
                  type="number"
                  name="passing_score"
                  value={formData.passing_score}
                  onChange={handleInputChange}
                  min="1"
                  max="100"
                  className="w-full px-3.5 py-2.5 text-sm bg-white border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-navy-900 text-navy-950"
                />
              </div>
            </div>

            <div className="md:col-span-2 space-y-1.5">
              <label className="text-xs font-bold text-slate-700">Description</label>
              <textarea
                name="description"
                rows="3"
                value={formData.description}
                onChange={handleInputChange}
                placeholder="Overview of the topics evaluated and target audience..."
                className="w-full px-3.5 py-2.5 text-sm bg-white border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-navy-900 text-navy-950"
              ></textarea>
            </div>
          </div>
        </div>

        {/* Section 2: Question Bank Builder */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6 sm:p-8 shadow-sm space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-4">
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="text-lg font-bold text-navy-950 font-heading">
                  Question Bank
                </h2>
                <span className="text-xs px-2 py-0.5 rounded-full font-bold bg-blue-50 text-blue-700 border border-blue-200">
                  {questions.length} Items
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                Build multiple-choice questions with options, answer key, and explanations.
              </p>
            </div>

            <button
              onClick={handleOpenAddQuestion}
              type="button"
              className="inline-flex items-center space-x-1.5 px-3.5 py-2 bg-blue-50 hover:bg-blue-100 text-blue-700 rounded-xl text-xs font-semibold border border-blue-200 transition-colors self-start sm:self-auto"
            >
              <Plus className="w-4 h-4" />
              <span>Add Question</span>
            </button>
          </div>

          {questions.length === 0 ? (
            <div className="text-center py-12 border-2 border-dashed border-slate-200 rounded-2xl space-y-3">
              <HelpCircle className="w-8 h-8 text-slate-300 mx-auto" />
              <p className="text-sm font-semibold text-slate-600">No questions added yet</p>
              <p className="text-xs text-slate-400 max-w-sm mx-auto">
                Click "+ Add Question" above to start populating this mock test question bank.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {questions.map((q, idx) => (
                <div
                  key={idx}
                  className="bg-slate-50 border border-slate-200 rounded-xl p-5 space-y-3 hover:border-slate-300 transition-colors"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="space-y-1">
                      <div className="flex items-center space-x-2">
                        <span className="w-6 h-6 rounded-full bg-navy-950 text-white text-xs font-bold flex items-center justify-center">
                          {idx + 1}
                        </span>
                        <h4 className="text-sm font-bold text-navy-950">
                          {q.question_text}
                        </h4>
                      </div>
                    </div>

                    <div className="flex items-center space-x-1 flex-shrink-0">
                      <span className="text-xs px-2 py-0.5 rounded-md bg-white border border-slate-200 text-slate-600 font-medium mr-2">
                        {q.marks || 1} pt{q.marks > 1 ? "s" : ""}
                      </span>
                      <button
                        onClick={() => handleOpenEditQuestion(idx)}
                        className="p-1.5 text-slate-400 hover:text-blue-600 rounded-lg hover:bg-white"
                        title="Edit question"
                      >
                        <Edit3 className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleDeleteQuestion(idx)}
                        className="p-1.5 text-slate-400 hover:text-red-600 rounded-lg hover:bg-white"
                        title="Delete question"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>

                  {/* Options List */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pl-8">
                    {(q.options || []).map((opt, oIdx) => {
                      const letter = String.fromCharCode(65 + oIdx);
                      const isCorrect =
                        q.correct_option === letter ||
                        q.correct_option === opt ||
                        (q.correct_option && q.correct_option.trim() === opt.trim());
                      return (
                        <div
                          key={oIdx}
                          className={`text-xs px-3 py-2 rounded-lg border flex items-center space-x-2 ${
                            isCorrect
                              ? "bg-emerald-50 border-emerald-300 text-emerald-900 font-semibold"
                              : "bg-white border-slate-200 text-slate-700"
                          }`}
                        >
                          <span
                            className={`w-4 h-4 rounded-full text-center text-xs font-bold leading-4 ${
                              isCorrect ? "bg-emerald-600 text-white" : "bg-slate-100 text-slate-500"
                            }`}
                          >
                            {letter}
                          </span>
                          <span>{opt}</span>
                          {isCorrect && (
                            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 ml-auto" />
                          )}
                        </div>
                      );
                    })}
                  </div>

                  {q.explanation && (
                    <div className="pl-8 text-xs text-slate-500 italic bg-white/60 p-2.5 rounded-lg border border-slate-100">
                      <span className="font-semibold text-slate-600">Explanation: </span>
                      {q.explanation}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Add / Edit Question Modal */}
      {isQuestionModalOpen && (
        <div className="fixed inset-0 z-50 overflow-y-auto bg-navy-950/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-xl w-full p-6 sm:p-8 shadow-2xl relative border border-slate-200 space-y-5">
            <button
              onClick={() => setIsQuestionModalOpen(false)}
              className="absolute top-5 right-5 text-slate-400 hover:text-slate-600"
            >
              <X className="w-5 h-5" />
            </button>

            <div>
              <h3 className="text-xl font-bold text-navy-950 font-heading">
                {editingQuestionIndex !== null ? "Edit Question" : "Add New Question"}
              </h3>
              <p className="text-xs text-slate-500 mt-1">
                Define the question prompt, multiple choice answers, and select the correct option.
              </p>
            </div>

            <div className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-xs font-bold text-slate-700">Question Prompt *</label>
                <textarea
                  rows="2"
                  value={questionForm.question_text}
                  onChange={(e) =>
                    setQuestionForm((p) => ({ ...p, question_text: e.target.value }))
                  }
                  placeholder="e.g. What is the time complexity of binary search?"
                  className="w-full px-3.5 py-2 text-sm bg-white border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-navy-900 text-navy-950"
                ></textarea>
              </div>

              {/* Options Inputs */}
              <div className="space-y-2">
                <label className="text-xs font-bold text-slate-700">
                  Options (Select radio for correct answer) *
                </label>
                {["A", "B", "C", "D"].map((letter, idx) => (
                  <div key={letter} className="flex items-center space-x-2">
                    <input
                      type="radio"
                      name="correct_option"
                      checked={questionForm.correct_option === letter}
                      onChange={() =>
                        setQuestionForm((p) => ({ ...p, correct_option: letter }))
                      }
                      className="w-4 h-4 text-emerald-600 focus:ring-emerald-500 cursor-pointer"
                      title="Mark as correct answer"
                    />
                    <span className="w-5 text-xs font-bold text-slate-500">{letter}.</span>
                    <input
                      type="text"
                      value={questionForm.options[idx] || ""}
                      onChange={(e) => handleOptionChange(idx, e.target.value)}
                      placeholder={`Option ${letter}`}
                      className={`w-full px-3 py-1.5 text-xs bg-white border rounded-xl focus:outline-none focus:ring-2 ${
                        questionForm.correct_option === letter
                          ? "border-emerald-300 ring-1 ring-emerald-300"
                          : "border-slate-200 focus:ring-navy-900"
                      }`}
                    />
                  </div>
                ))}
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <label className="text-xs font-bold text-slate-700">Marks / Points</label>
                  <input
                    type="number"
                    min="1"
                    max="10"
                    value={questionForm.marks}
                    onChange={(e) =>
                      setQuestionForm((p) => ({ ...p, marks: Number(e.target.value) }))
                    }
                    className="w-full px-3 py-2 text-xs bg-white border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-navy-900"
                  />
                </div>
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-bold text-slate-700">
                  Explanation (Shown in review)
                </label>
                <textarea
                  rows="2"
                  value={questionForm.explanation}
                  onChange={(e) =>
                    setQuestionForm((p) => ({ ...p, explanation: e.target.value }))
                  }
                  placeholder="Why this answer is correct..."
                  className="w-full px-3 py-2 text-xs bg-white border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-navy-900"
                ></textarea>
              </div>
            </div>

            <div className="flex items-center justify-end space-x-3 pt-3 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setIsQuestionModalOpen(false)}
                className="px-4 py-2 border border-slate-200 rounded-xl text-xs font-semibold text-slate-600 hover:bg-slate-50"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleSaveQuestionModal}
                className="px-5 py-2 bg-navy-950 hover:bg-navy-900 text-white rounded-xl text-xs font-semibold"
              >
                Save Question
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MockTestManagement;
