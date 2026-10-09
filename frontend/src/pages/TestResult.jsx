import React, { useState, useEffect, useCallback } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import mockTestService from "../services/mockTestService";
import { ROUTES } from "../constants";
import {
  CheckCircle2,
  XCircle,
  AlertCircle,
  Clock,
  Award,
  ArrowRight,
  ChevronDown,
  ChevronUp,
  RotateCcw,
  BookOpen,
  ArrowLeft,
  Check,
  Flag,
  BarChart3,
  Sparkles,
} from "lucide-react";

export const TestResult = () => {
  const { id: attemptId } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();

  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showReview, setShowReview] = useState(false);
  const [reviewFilter, setReviewFilter] = useState("all");

  const fetchResult = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await mockTestService.getAttemptResult(attemptId);
      setResult(res.data);
    } catch (err) {
      console.error("Failed to load assessment result:", err);
      setError(
        err.response?.data?.message ||
          "Unable to load assessment result. The test may still be in progress or unauthorized."
      );
    } finally {
      setLoading(false);
    }
  }, [attemptId]);

  useEffect(() => {
    fetchResult();
  }, [fetchResult]);

  const formatCompletedDate = (isoString) => {
    if (!isoString) return "Recently";
    try {
      const d = new Date(isoString);
      return d.toLocaleDateString("en-US", {
        month: "long",
        year: "numeric",
      });
    } catch {
      return "Recently";
    }
  };

  const formatDuration = (seconds) => {
    if (seconds === undefined || seconds === null) return "0m 0s";
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs}s`;
  };

  const getDifficultyColor = (difficulty) => {
    const diff = (difficulty || "").toLowerCase();
    if (diff === "easy") return "bg-emerald-500";
    if (diff === "medium") return "bg-blue-600";
    if (diff === "hard") return "bg-purple-600";
    return "bg-slate-400";
  };

  const filteredQuestions = result?.question_reviews?.filter((q) => {
    if (reviewFilter === "correct") return q.is_correct;
    if (reviewFilter === "incorrect") return !q.is_correct && q.user_answer;
    if (reviewFilter === "unanswered") return !q.user_answer;
    if (reviewFilter === "marked") return q.is_marked_for_review;
    return true;
  }) || [];

  if (loading) {
    return (
      <div className="min-h-screen bg-[#F8FAFC] flex flex-col items-center justify-center p-4">
        <div className="w-12 h-12 border-4 border-navy-950 border-t-transparent rounded-full animate-spin mb-4" />
        <h3 className="text-base font-bold text-navy-950 font-heading">
          Calculating Performance Analytics...
        </h3>
        <p className="text-xs text-slate-500 mt-1">
          Evaluating accuracy, topic mastery, and percentile ranking
        </p>
      </div>
    );
  }

  if (error || !result) {
    return (
      <div className="min-h-screen bg-[#F8FAFC] flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl p-8 max-w-md w-full shadow-sm border border-slate-200 text-center space-y-4">
          <div className="w-12 h-12 rounded-full bg-red-50 text-red-600 flex items-center justify-center mx-auto">
            <AlertCircle className="w-6 h-6" />
          </div>
          <h2 className="text-xl font-bold text-navy-950 font-heading">Result Unavailable</h2>
          <p className="text-sm text-slate-600 leading-relaxed">
            {error || "Could not retrieve the specified assessment result."}
          </p>
          <div className="pt-2 flex flex-col gap-2">
            <button
              onClick={() => navigate(ROUTES.MOCK_TESTS)}
              className="w-full px-4 py-2.5 bg-navy-950 hover:bg-navy-900 text-white rounded-xl text-sm font-semibold transition-all"
            >
              Back to Mock Tests
            </button>
            <button
              onClick={fetchResult}
              className="w-full px-4 py-2.5 border border-slate-200 hover:bg-slate-50 text-slate-700 rounded-xl text-sm font-semibold transition-all"
            >
              Try Again
            </button>
          </div>
        </div>
      </div>
    );
  }

  const {
    test_title,
    score,
    total_marks,
    percentage,
    accuracy,
    is_passed,
    time_taken_seconds,
    total_duration_minutes,
    percentile_rank,
    correct_answers_count,
    total_questions,
    completed_at,
    topic_breakdowns = [],
    difficulty_analysis = [],
    question_reviews = [],
    mock_test_id,
  } = result;

  return (
    <div className="min-h-screen bg-[#F8FAFC] py-8 sm:py-12 px-4 sm:px-6 lg:px-8 font-sans">
      <div className="max-w-6xl mx-auto space-y-8">
        {/* Navigation Breadcrumb */}
        <div className="flex items-center space-x-2 text-xs sm:text-sm text-slate-500">
          <Link
            to={ROUTES.MOCK_TESTS}
            className="hover:text-navy-950 flex items-center space-x-1 font-medium transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Mock Tests</span>
          </Link>
          <span className="text-slate-300">/</span>
          <span className="text-slate-800 font-semibold truncate max-w-xs sm:max-w-md">
            {test_title}
          </span>
          <span className="text-slate-300">/</span>
          <span className="text-navy-950 font-bold">Result</span>
        </div>

        {/* Header Block matching UI design */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2">
          <div>
            <h1 className="text-2xl sm:text-3xl lg:text-4xl font-extrabold text-[#0B1527] font-heading tracking-tight">
              Assessment Result: {test_title}
            </h1>
            <p className="text-slate-500 mt-1 text-sm sm:text-base font-medium">
              Completed {formatCompletedDate(completed_at)}
            </p>
          </div>

          <div className="flex items-center space-x-3 self-start md:self-auto">
            {is_passed ? (
              <div className="inline-flex items-center space-x-2 px-4 py-2 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-700 text-sm sm:text-base font-bold shadow-sm">
                <Check className="w-5 h-5 text-emerald-600 stroke-[3]" />
                <span>
                  {score}/{total_marks} PASSED
                </span>
              </div>
            ) : (
              <div className="inline-flex items-center space-x-2 px-4 py-2 rounded-full bg-amber-50 border border-amber-200 text-amber-700 text-sm sm:text-base font-bold shadow-sm">
                <AlertCircle className="w-5 h-5 text-amber-600" />
                <span>
                  {score}/{total_marks} NEEDS IMPROVEMENT
                </span>
              </div>
            )}
          </div>
        </div>

        {/* 4 Top Metric Cards matching UI design */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          {/* Overall Score */}
          <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-sm flex flex-col justify-between">
            <span className="text-xs sm:text-sm font-semibold text-slate-500 uppercase tracking-wider">
              Overall Score
            </span>
            <div className="my-4">
              <div className="text-3xl sm:text-4xl font-black text-[#0B1527] font-heading">
                {Math.round(percentage)}%
              </div>
              <div className="w-full bg-slate-100 rounded-full h-2 mt-4 overflow-hidden">
                <div
                  className="bg-blue-600 h-2 rounded-full transition-all duration-700 ease-out"
                  style={{ width: `${Math.min(100, Math.max(0, percentage))}%` }}
                />
              </div>
            </div>
            <span className="text-xs text-slate-400 font-medium">
              Score: {score} / {total_marks} pts
            </span>
          </div>

          {/* Accuracy */}
          <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-sm flex flex-col justify-between">
            <span className="text-xs sm:text-sm font-semibold text-slate-500 uppercase tracking-wider">
              Accuracy
            </span>
            <div className="my-4">
              <div className="text-3xl sm:text-4xl font-black text-[#0B1527] font-heading">
                {accuracy}%
              </div>
              <div className="text-xs sm:text-sm font-semibold text-slate-600 mt-2">
                {correct_answers_count} / {total_questions} Correct
              </div>
            </div>
            <span className="text-xs text-slate-400 font-medium">
              Across all evaluated questions
            </span>
          </div>

          {/* Time Taken */}
          <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-sm flex flex-col justify-between">
            <span className="text-xs sm:text-sm font-semibold text-slate-500 uppercase tracking-wider">
              Time Taken
            </span>
            <div className="my-4">
              <div className="text-3xl sm:text-4xl font-black text-[#0B1527] font-heading">
                {formatDuration(time_taken_seconds)}
              </div>
              <div className="text-xs sm:text-sm font-semibold text-slate-600 mt-2">
                / {total_duration_minutes || 60}m Total
              </div>
            </div>
            <span className="text-xs text-slate-400 font-medium">
              Pacing: {total_questions ? (time_taken_seconds / total_questions).toFixed(1) : 0}s per question
            </span>
          </div>

          {/* Percentile */}
          <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-sm flex flex-col justify-between">
            <span className="text-xs sm:text-sm font-semibold text-slate-500 uppercase tracking-wider">
              Percentile
            </span>
            <div className="my-4">
              <div className="text-3xl sm:text-4xl font-black text-[#0B1527] font-heading">
                Top {percentile_rank || 15}%
              </div>
              <div className="inline-flex items-center space-x-1.5 mt-2 px-2.5 py-0.5 rounded-full text-xs font-bold bg-blue-50 text-blue-700 border border-blue-100">
                <Sparkles className="w-3.5 h-3.5 text-blue-600" />
                <span>Candidate</span>
              </div>
            </div>
            <span className="text-xs text-slate-400 font-medium">
              Compared to peer test takers
            </span>
          </div>
        </div>

        {/* 2 Breakdown Cards matching UI design */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Topic Breakdown Card */}
          <div className="bg-white rounded-2xl border border-slate-200/80 p-6 sm:p-7 shadow-sm space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-lg sm:text-xl font-bold text-[#0B1527] font-heading">
                Topic Breakdown
              </h2>
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Mastery %
              </span>
            </div>

            <div className="space-y-5">
              {topic_breakdowns.length === 0 ? (
                <p className="text-xs text-slate-400 py-4 text-center">
                  No topic breakdown data available.
                </p>
              ) : (
                topic_breakdowns.map((item, idx) => (
                  <div key={idx} className="space-y-2">
                    <div className="flex items-center justify-between text-xs sm:text-sm font-medium">
                      <span className="text-slate-800 font-semibold">{item.topic}</span>
                      <span className="text-slate-900 font-bold">{Math.round(item.accuracy_percentage)}%</span>
                    </div>
                    <div className="w-full bg-slate-100 rounded-full h-2.5 overflow-hidden">
                      <div
                        className="bg-blue-600 h-2.5 rounded-full transition-all duration-700 ease-out"
                        style={{
                          width: `${Math.min(100, Math.max(0, item.accuracy_percentage))}%`,
                        }}
                      />
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Difficulty Analysis Card */}
          <div className="bg-white rounded-2xl border border-slate-200/80 p-6 sm:p-7 shadow-sm space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-lg sm:text-xl font-bold text-[#0B1527] font-heading">
                Difficulty Analysis
              </h2>
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Correct / Total
              </span>
            </div>

            <div className="space-y-5">
              {difficulty_analysis.length === 0 ? (
                <p className="text-xs text-slate-400 py-4 text-center">
                  No difficulty analysis data available.
                </p>
              ) : (
                difficulty_analysis.map((item, idx) => {
                  const percent = item.total > 0 ? (item.correct / item.total) * 100 : 0;
                  return (
                    <div key={idx} className="space-y-2">
                      <div className="flex items-center justify-between text-xs sm:text-sm font-medium">
                        <span className="text-slate-800 font-semibold capitalize">
                          {item.difficulty}
                        </span>
                        <span className="text-slate-900 font-bold">
                          {item.correct}/{item.total}
                        </span>
                      </div>
                      <div className="w-full bg-slate-100 rounded-full h-2.5 overflow-hidden">
                        <div
                          className={`h-2.5 rounded-full transition-all duration-700 ease-out ${getDifficultyColor(
                            item.difficulty
                          )}`}
                          style={{
                            width: `${Math.min(100, Math.max(0, percent))}%`,
                          }}
                        />
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        </div>

        {/* Primary Action Buttons matching UI design */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-2">
          <div className="flex items-center space-x-3 w-full sm:w-auto">
            <button
              onClick={() => setShowReview((prev) => !prev)}
              className="w-full sm:w-auto px-6 py-3 rounded-xl border border-slate-300 bg-white hover:bg-slate-50 text-slate-800 text-sm font-bold shadow-sm transition-all flex items-center justify-center space-x-2"
            >
              <BookOpen className="w-4 h-4 text-slate-600" />
              <span>{showReview ? "Hide Answer Review" : "Review Answers"}</span>
              {showReview ? (
                <ChevronUp className="w-4 h-4 text-slate-500" />
              ) : (
                <ChevronDown className="w-4 h-4 text-slate-500" />
              )}
            </button>

            {mock_test_id && (
              <button
                onClick={() => navigate(`/mock-tests/${mock_test_id}/take`)}
                className="hidden sm:inline-flex px-4 py-3 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 text-sm font-semibold transition-all items-center space-x-2"
              >
                <RotateCcw className="w-4 h-4 text-slate-500" />
                <span>Retake</span>
              </button>
            )}
          </div>

          <Link
            to={ROUTES.COURSES}
            className="w-full sm:w-auto inline-flex items-center justify-center space-x-2 px-6 py-3 rounded-full bg-[#0B1527] hover:bg-[#132238] text-white text-sm font-bold shadow-sm transition-all"
          >
            <span>Explore Recommended Courses</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>

        {/* Interactive Answer Review Section */}
        {showReview && (
          <div className="bg-white rounded-2xl border border-slate-200 p-6 sm:p-8 shadow-sm space-y-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-100">
              <div>
                <h3 className="text-xl font-bold text-[#0B1527] font-heading">
                  Question-by-Question Review
                </h3>
                <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
                  Review your answers, correct options, and comprehensive explanations.
                </p>
              </div>

              {/* Filter Tabs */}
              <div className="flex items-center gap-1.5 overflow-x-auto pb-1 sm:pb-0">
                {[
                  { key: "all", label: `All (${question_reviews.length})` },
                  { key: "correct", label: `Correct (${correct_answers_count})` },
                  {
                    key: "incorrect",
                    label: `Incorrect (${
                      question_reviews.filter((q) => !q.is_correct && q.user_answer).length
                    })`,
                  },
                  {
                    key: "unanswered",
                    label: `Skipped (${
                      question_reviews.filter((q) => !q.user_answer).length
                    })`,
                  },
                ].map((tab) => (
                  <button
                    key={tab.key}
                    onClick={() => setReviewFilter(tab.key)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                      reviewFilter === tab.key
                        ? "bg-navy-950 text-white"
                        : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                    }`}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Questions List */}
            <div className="space-y-6">
              {filteredQuestions.length === 0 ? (
                <div className="text-center py-12 text-slate-400">
                  <BookOpen className="w-10 h-10 mx-auto text-slate-300 mb-2" />
                  <p className="text-sm font-medium">No questions match the current filter.</p>
                </div>
              ) : (
                filteredQuestions.map((q, idx) => {
                  return (
                    <div
                      key={q.question_id || idx}
                      className="border border-slate-200 rounded-xl p-5 sm:p-6 space-y-4 hover:border-slate-300 transition-all bg-white"
                    >
                      {/* Question Header Meta */}
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <div className="flex items-center space-x-2">
                          <span className="font-bold text-sm text-[#0B1527]">
                            Question {q.question_number || idx + 1}
                          </span>
                          {q.topic && (
                            <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-blue-50 text-blue-700">
                              {q.topic}
                            </span>
                          )}
                          {q.difficulty && (
                            <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-slate-100 text-slate-600 capitalize">
                              {q.difficulty}
                            </span>
                          )}
                          {q.is_marked_for_review && (
                            <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-purple-50 text-purple-700 flex items-center space-x-1">
                              <Flag className="w-3 h-3" />
                              <span>Marked</span>
                            </span>
                          )}
                        </div>

                        <div>
                          {q.is_correct ? (
                            <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-xs font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                              <span>Correct (+{q.marks_awarded} pts)</span>
                            </span>
                          ) : q.user_answer ? (
                            <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-xs font-bold bg-red-50 text-red-700 border border-red-200">
                              <XCircle className="w-3.5 h-3.5 text-red-600" />
                              <span>Incorrect (0 pts)</span>
                            </span>
                          ) : (
                            <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-xs font-bold bg-slate-100 text-slate-600">
                              <span>Unanswered (0 pts)</span>
                            </span>
                          )}
                        </div>
                      </div>

                      {/* Question Text */}
                      <p className="text-base font-semibold text-slate-900 leading-relaxed">
                        {q.question_text}
                      </p>

                      {/* Options Review */}
                      <div className="space-y-2.5 pt-1">
                        {q.options?.map((optText, optIdx) => {
                          const optLetter = String.fromCharCode(65 + optIdx);
                          const isCorrectOpt = optLetter === q.correct_option;
                          const isUserSelected = optLetter === q.user_answer;

                          let containerStyle =
                            "border-slate-200 bg-white text-slate-700";
                          if (isCorrectOpt) {
                            containerStyle =
                              "border-emerald-500 bg-emerald-50/60 text-emerald-950 font-medium";
                          } else if (isUserSelected && !q.is_correct) {
                            containerStyle =
                              "border-red-300 bg-red-50/70 text-red-950";
                          }

                          return (
                            <div
                              key={optIdx}
                              className={`p-3.5 rounded-xl border flex items-center justify-between text-xs sm:text-sm transition-all ${containerStyle}`}
                            >
                              <div className="flex items-center space-x-3">
                                <span
                                  className={`w-6 h-6 rounded-full flex items-center justify-center font-bold text-xs ${
                                    isCorrectOpt
                                      ? "bg-emerald-600 text-white"
                                      : isUserSelected
                                      ? "bg-red-600 text-white"
                                      : "bg-slate-100 text-slate-600"
                                  }`}
                                >
                                  {optLetter}
                                </span>
                                <span>{optText}</span>
                              </div>

                              <div className="flex items-center space-x-2">
                                {isUserSelected && (
                                  <span
                                    className={`text-[11px] font-bold px-2 py-0.5 rounded-full ${
                                      isCorrectOpt
                                        ? "bg-emerald-200 text-emerald-800"
                                        : "bg-red-200 text-red-800"
                                    }`}
                                  >
                                    Your Choice
                                  </span>
                                )}
                                {isCorrectOpt && (
                                  <span className="text-[11px] font-bold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 flex items-center space-x-1">
                                    <Check className="w-3 h-3 stroke-[3]" />
                                    <span>Correct</span>
                                  </span>
                                )}
                              </div>
                            </div>
                          );
                        })}
                      </div>

                      {/* Explanation Callout */}
                      {q.explanation && (
                        <div className="mt-3 p-4 rounded-xl bg-blue-50/70 border border-blue-100 text-xs sm:text-sm text-slate-700 leading-relaxed space-y-1">
                          <p className="font-bold text-blue-900 flex items-center space-x-1.5">
                            <Sparkles className="w-3.5 h-3.5 text-blue-600" />
                            <span>Explanation:</span>
                          </p>
                          <p className="text-slate-700 pl-5">{q.explanation}</p>
                        </div>
                      )}
                    </div>
                  );
                })
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default TestResult;
