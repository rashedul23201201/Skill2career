import React, { useState, useEffect, useCallback, useRef } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import mockTestService from "../services/mockTestService";
import { ROUTES } from "../constants";
import {
  Clock,
  CheckCircle,
  AlertCircle,
  HelpCircle,
  ArrowLeft,
  ChevronLeft,
  ChevronRight,
  Flag,
  RotateCcw,
  Award,
  X,
  Send,
} from "lucide-react";

export const MockTestAttempt = () => {
  const { id: testId } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();

  const [attempt, setAttempt] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState({});
  const [markedForReview, setMarkedForReview] = useState([]);
  const [remainingSeconds, setRemainingSeconds] = useState(0);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [resultData, setResultData] = useState(null);

  const autoSubmitTriggered = useRef(false);
  const saveTimeoutRef = useRef(null);

  const formatTimer = (totalSeconds) => {
    const s = Math.max(0, totalSeconds);
    const mins = Math.floor(s / 60);
    const secs = s % 60;
    return `${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
  };

  const syncAnswersToBackend = useCallback(
    async (updatedAnswers, updatedReview) => {
      if (!attempt || attempt.status !== "ACTIVE" || resultData) return;
      try {
        await mockTestService.saveIntermediateAnswers(attempt.id, {
          answers: updatedAnswers,
          marked_for_review: updatedReview,
        });
      } catch (err) {
        console.warn("Failed to persist intermediate answers:", err);
      }
    },
    [attempt, resultData]
  );

  const initializeAttempt = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await mockTestService.startAttempt(testId);
      const data = res.data;

      setAttempt(data);
      setQuestions(data.questions || []);
      setAnswers(data.answers || {});
      setMarkedForReview(data.marked_for_review || []);
      setRemainingSeconds(data.remaining_seconds || 0);

      if (data.status === "SUBMITTED" || data.status === "EXPIRED") {
        setResultData({
          score: data.score,
          total_marks: data.total_marks,
          percentage: data.percentage,
          is_passed: data.is_passed,
          time_taken_seconds: data.time_taken_seconds,
          test_title: data.test_title,
          passing_score: data.passing_score,
          status: data.status,
        });
      }
    } catch (err) {
      console.error("Failed to start attempt:", err);
      setError(
        err.response?.data?.message ||
          "Unable to start the test attempt. The test might be unpublished or unavailable."
      );
    } finally {
      setLoading(false);
    }
  }, [testId]);

  useEffect(() => {
    initializeAttempt();
  }, [initializeAttempt]);

  const handleSubmitAttempt = useCallback(
    async (isAutoExpired = false) => {
      if (!attempt || isSubmitting || resultData) return;
      try {
        setIsSubmitting(true);
        setShowConfirmModal(false);

        const res = await mockTestService.submitTestAnswers(attempt.id, {
          answers,
          marked_for_review: markedForReview,
        });

        setResultData(res.data);
      } catch (err) {
        console.error("Failed to submit test:", err);
        setError("Failed to submit assessment answers. Please try again.");
      } finally {
        setIsSubmitting(false);
      }
    },
    [attempt, answers, markedForReview, isSubmitting, resultData]
  );

  useEffect(() => {
    if (loading || !attempt || attempt.status !== "ACTIVE" || resultData) return;

    const timer = setInterval(() => {
      setRemainingSeconds((prev) => {
        if (prev <= 1) {
          clearInterval(timer);
          if (!autoSubmitTriggered.current) {
            autoSubmitTriggered.current = true;
            handleSubmitAttempt(true);
          }
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [loading, attempt, resultData, handleSubmitAttempt]);

  const handleSelectOption = (optionLetter) => {
    if (resultData || !currentQuestion) return;
    const qIdStr = String(currentQuestion.id);

    const updated = {
      ...answers,
      [qIdStr]: optionLetter,
    };
    setAnswers(updated);

    if (saveTimeoutRef.current) clearTimeout(saveTimeoutRef.current);
    saveTimeoutRef.current = setTimeout(() => {
      syncAnswersToBackend(updated, markedForReview);
    }, 500);
  };

  const handleToggleMarkForReview = () => {
    if (!currentQuestion || resultData) return;
    const qId = currentQuestion.id;
    let updated;
    if (markedForReview.includes(qId)) {
      updated = markedForReview.filter((id) => id !== qId);
    } else {
      updated = [...markedForReview, qId];
    }
    setMarkedForReview(updated);
    syncAnswersToBackend(answers, updated);
  };

  const handleNext = () => {
    if (currentIndex < questions.length - 1) {
      setCurrentIndex((prev) => prev + 1);
    } else {
      setShowConfirmModal(true);
    }
  };

  const handlePrevious = () => {
    if (currentIndex > 0) {
      setCurrentIndex((prev) => prev - 1);
    }
  };

  const currentQuestion = questions[currentIndex] || null;

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center p-4">
        <div className="w-12 h-12 border-4 border-navy-900 border-t-transparent rounded-full animate-spin mb-4" />
        <h3 className="text-base font-bold text-navy-950 font-heading">
          Initializing Assessment Session...
        </h3>
        <p className="text-xs text-slate-500 mt-1">Preparing question bank and timer</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl p-8 max-w-md w-full shadow-sm border border-slate-200 text-center space-y-4">
          <div className="w-12 h-12 rounded-full bg-red-50 text-red-600 flex items-center justify-center mx-auto">
            <AlertCircle className="w-6 h-6" />
          </div>
          <h2 className="text-xl font-bold text-navy-950 font-heading">Unable to Start Test</h2>
          <p className="text-sm text-slate-600">{error}</p>
          <div className="pt-2">
            <button
              onClick={() => navigate(ROUTES.MOCK_TESTS)}
              className="w-full px-4 py-2.5 bg-navy-950 hover:bg-navy-900 text-white rounded-xl text-sm font-semibold transition-all"
            >
              Back to Mock Tests
            </button>
          </div>
        </div>
      </div>
    );
  }

  const answeredCount = Object.keys(answers).filter(
    (k) => answers[k] !== undefined && answers[k] !== null && answers[k] !== ""
  ).length;
  const markedCount = markedForReview.length;
  const unansweredCount = Math.max(0, questions.length - answeredCount);

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
      {/* Top Header / Sticky Navigation matching UI design */}
      <header className="sticky top-0 z-30 bg-white border-b border-slate-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          {/* Breadcrumb Title */}
          <div className="flex items-center space-x-2 text-sm">
            <Link
              to={ROUTES.MOCK_TESTS}
              className="text-slate-500 hover:text-navy-950 font-medium transition-colors"
            >
              Mock Tests
            </Link>
            <span className="text-slate-400">/</span>
            <span className="text-navy-950 font-bold font-heading truncate max-w-xs sm:max-w-md">
              {attempt?.test_title || "Technical Assessment"}
            </span>
          </div>

          {/* Timer & Submit Trigger */}
          <div className="flex items-center space-x-3 sm:space-x-4">
            <div
              className={`flex items-center space-x-2 px-3 sm:px-4 py-1.5 rounded-full border text-xs sm:text-sm font-semibold transition-all ${
                remainingSeconds < 300
                  ? "bg-red-50 border-red-200 text-red-600 animate-pulse"
                  : remainingSeconds < 600
                  ? "bg-amber-50 border-amber-200 text-amber-700"
                  : "bg-slate-100 border-slate-200 text-navy-950"
              }`}
            >
              <Clock className="w-4 h-4 text-slate-500" />
              <span>Time Remaining:</span>
              <span className="font-mono font-bold">{formatTimer(remainingSeconds)}</span>
            </div>

            {!resultData && (
              <button
                onClick={() => setShowConfirmModal(true)}
                disabled={isSubmitting}
                className="px-4 sm:px-5 py-2 bg-navy-950 hover:bg-navy-900 text-white rounded-xl text-xs sm:text-sm font-semibold transition-all shadow-sm"
              >
                Submit Test
              </button>
            )}
          </div>
        </div>
      </header>

      {/* Main Runner Body */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
        {questions.length === 0 ? (
          <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center max-w-lg mx-auto">
            <HelpCircle className="w-12 h-12 text-slate-300 mx-auto mb-3" />
            <h3 className="text-lg font-bold text-navy-950 font-heading">
              No questions found
            </h3>
            <p className="text-sm text-slate-500 mt-1">
              This mock test currently has no multiple-choice questions added.
            </p>
            <button
              onClick={() => navigate(ROUTES.MOCK_TESTS)}
              className="mt-6 px-4 py-2 bg-navy-950 text-white text-xs font-semibold rounded-xl"
            >
              Return to Catalog
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 sm:gap-8 items-start">
            {/* Left / Center: Question & Options Panel */}
            <div className="lg:col-span-8 bg-white rounded-2xl border border-slate-200 p-6 sm:p-8 shadow-sm flex flex-col justify-between min-h-[500px]">
              <div>
                {/* Question Progress Header */}
                <div className="text-xs sm:text-sm font-medium text-slate-400 mb-2">
                  Question {currentIndex + 1} of {questions.length}:
                </div>

                {/* Question Prompt */}
                <h2 className="text-base sm:text-xl font-bold text-navy-950 font-heading leading-relaxed mb-6">
                  {currentQuestion?.question_text}
                </h2>

                {/* Options List */}
                <div className="space-y-3 sm:space-y-4">
                  {currentQuestion?.options?.map((optionText, optIdx) => {
                    const optionLetter = String.fromCharCode(65 + optIdx);
                    const currentSelected = answers[String(currentQuestion.id)];
                    const isSelected = currentSelected === optionLetter;

                    return (
                      <div
                        key={optIdx}
                        onClick={() => handleSelectOption(optionLetter)}
                        className={`rounded-xl p-4 flex items-center space-x-3 cursor-pointer transition-all border ${
                          isSelected
                            ? "border-blue-600 bg-blue-50/70 shadow-sm"
                            : "border-slate-200 bg-white hover:bg-slate-50 hover:border-slate-300"
                        }`}
                      >
                        <div
                          className={`w-5 h-5 rounded-full border flex items-center justify-center flex-shrink-0 transition-colors ${
                            isSelected
                              ? "border-blue-600 bg-blue-600"
                              : "border-slate-300 bg-white"
                          }`}
                        >
                          {isSelected && (
                            <div className="w-2 h-2 rounded-full bg-white" />
                          )}
                        </div>
                        <span className="text-sm sm:text-base text-slate-800 font-medium">
                          <strong className="text-navy-950 font-semibold mr-1.5">
                            {optionLetter}:
                          </strong>
                          {optionText}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Action Footer matching UI design */}
              <div className="flex items-center justify-between pt-8 mt-8 border-t border-slate-100">
                <button
                  onClick={handlePrevious}
                  disabled={currentIndex === 0}
                  className="px-5 py-2.5 border border-slate-200 rounded-xl text-xs sm:text-sm font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-40 disabled:hover:bg-white transition-all"
                >
                  Previous
                </button>

                <div className="flex items-center space-x-3">
                  <button
                    onClick={handleToggleMarkForReview}
                    className={`px-4 sm:px-5 py-2.5 rounded-xl text-xs sm:text-sm font-semibold transition-all flex items-center space-x-2 ${
                      markedForReview.includes(currentQuestion?.id)
                        ? "bg-purple-700 text-white"
                        : "bg-purple-600 hover:bg-purple-700 text-white shadow-sm"
                    }`}
                  >
                    <Flag className="w-3.5 h-3.5" />
                    <span>
                      {markedForReview.includes(currentQuestion?.id)
                        ? "Marked"
                        : "Mark for Review"}
                    </span>
                  </button>

                  <button
                    onClick={handleNext}
                    className="px-5 sm:px-6 py-2.5 bg-navy-950 hover:bg-navy-900 text-white rounded-xl text-xs sm:text-sm font-semibold shadow-sm transition-all"
                  >
                    {currentIndex === questions.length - 1 ? "Review & Finish" : "Save & Next"}
                  </button>
                </div>
              </div>
            </div>

            {/* Right Sidebar: Question Palette */}
            <div className="lg:col-span-4 bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
              <h3 className="text-base font-bold text-navy-950 font-heading mb-4">
                Question Palette
              </h3>

              {/* Palette Grid */}
              <div className="grid grid-cols-5 gap-2.5">
                {questions.map((q, idx) => {
                  const isActive = idx === currentIndex;
                  const isAnswered =
                    answers[String(q.id)] !== undefined &&
                    answers[String(q.id)] !== null &&
                    answers[String(q.id)] !== "";
                  const isMarked = markedForReview.includes(q.id);

                  return (
                    <button
                      key={q.id}
                      onClick={() => setCurrentIndex(idx)}
                      className={`h-11 rounded-xl flex flex-col items-center justify-center font-semibold text-sm transition-all border ${
                        isActive
                          ? "border-2 border-blue-600 bg-blue-50 text-blue-700 shadow-sm"
                          : "border-slate-200 bg-white hover:bg-slate-50 text-slate-700"
                      }`}
                    >
                      <span className="leading-none">{idx + 1}</span>
                      <div className="h-2 flex items-center justify-center mt-1">
                        {isMarked ? (
                          <span className="w-1.5 h-1.5 rounded-full bg-purple-600" />
                        ) : isAnswered ? (
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                        ) : (
                          <span className="w-1.5 h-1.5 rounded-full bg-slate-300" />
                        )}
                      </div>
                    </button>
                  );
                })}
              </div>

              {/* Palette Legend */}
              <div className="mt-6 pt-5 border-t border-slate-100 space-y-2 text-xs text-slate-600">
                <div className="flex items-center justify-between">
                  <span className="flex items-center space-x-2">
                    <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
                    <span>Answered</span>
                  </span>
                  <span className="font-bold text-navy-950">{answeredCount}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="flex items-center space-x-2">
                    <span className="w-2.5 h-2.5 rounded-full bg-purple-600" />
                    <span>Marked for Review</span>
                  </span>
                  <span className="font-bold text-navy-950">{markedCount}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="flex items-center space-x-2">
                    <span className="w-2.5 h-2.5 rounded-full bg-slate-300" />
                    <span>Unanswered</span>
                  </span>
                  <span className="font-bold text-navy-950">{unansweredCount}</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Submit Confirmation Modal */}
      {showConfirmModal && (
        <div className="fixed inset-0 z-50 bg-navy-950/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 sm:p-8 shadow-2xl border border-slate-200 space-y-5">
            <h3 className="text-xl font-bold text-navy-950 font-heading">
              Submit Assessment?
            </h3>
            <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
              Are you sure you want to finalize your attempt? You cannot change your answers after submission.
            </p>

            <div className="grid grid-cols-3 gap-2 bg-slate-50 rounded-xl p-3 border border-slate-100 text-center text-xs">
              <div>
                <p className="text-slate-400 font-medium">Answered</p>
                <p className="text-base font-bold text-emerald-600 mt-0.5">{answeredCount}</p>
              </div>
              <div>
                <p className="text-slate-400 font-medium">Marked</p>
                <p className="text-base font-bold text-purple-600 mt-0.5">{markedCount}</p>
              </div>
              <div>
                <p className="text-slate-400 font-medium">Unanswered</p>
                <p className="text-base font-bold text-slate-500 mt-0.5">{unansweredCount}</p>
              </div>
            </div>

            <div className="flex items-center justify-end space-x-3 pt-2">
              <button
                onClick={() => setShowConfirmModal(false)}
                className="px-4 py-2 border border-slate-200 rounded-xl text-xs font-semibold text-slate-600 hover:bg-slate-50"
              >
                Continue Test
              </button>
              <button
                onClick={() => handleSubmitAttempt(false)}
                disabled={isSubmitting}
                className="px-5 py-2 bg-navy-950 hover:bg-navy-900 text-white rounded-xl text-xs font-semibold shadow-sm flex items-center space-x-1.5"
              >
                {isSubmitting ? (
                  <span>Submitting...</span>
                ) : (
                  <>
                    <span>Confirm & Submit</span>
                    <Send className="w-3.5 h-3.5" />
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Completion & Scorecard Modal */}
      {resultData && (
        <div className="fixed inset-0 z-50 bg-navy-950/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 sm:p-8 shadow-2xl border border-slate-200 text-center space-y-6">
            <div
              className={`w-16 h-16 rounded-full flex items-center justify-center mx-auto ${
                resultData.is_passed
                  ? "bg-emerald-50 text-emerald-600"
                  : "bg-amber-50 text-amber-600"
              }`}
            >
              {resultData.is_passed ? (
                <Award className="w-8 h-8" />
              ) : (
                <RotateCcw className="w-8 h-8" />
              )}
            </div>

            <div>
              <span
                className={`inline-block px-3 py-1 rounded-full text-xs font-bold uppercase ${
                  resultData.is_passed
                    ? "bg-emerald-100 text-emerald-800"
                    : "bg-amber-100 text-amber-800"
                }`}
              >
                {resultData.is_passed ? "Passed" : "Needs Improvement"}
              </span>
              <h2 className="text-2xl font-extrabold text-navy-950 font-heading mt-2">
                Assessment Completed
              </h2>
              <p className="text-xs text-slate-500 mt-1">
                {attempt?.test_title || "Mock Test Assessment"}
              </p>
            </div>

            {/* Score Grid */}
            <div className="grid grid-cols-3 gap-3 bg-slate-50 rounded-xl p-4 border border-slate-100 text-center">
              <div>
                <p className="text-xs text-slate-400 font-medium">Your Score</p>
                <p className="text-lg font-bold text-navy-950 mt-0.5">
                  {resultData.score} / {resultData.total_marks}
                </p>
              </div>
              <div>
                <p className="text-xs text-slate-400 font-medium">Accuracy</p>
                <p className="text-lg font-bold text-navy-950 mt-0.5">
                  {resultData.percentage}%
                </p>
              </div>
              <div>
                <p className="text-xs text-slate-400 font-medium">Time Taken</p>
                <p className="text-lg font-bold text-navy-950 mt-0.5">
                  {Math.floor(resultData.time_taken_seconds / 60)}m {resultData.time_taken_seconds % 60}s
                </p>
              </div>
            </div>

            <p className="text-xs text-slate-500">
              Passing threshold for this assessment is {resultData.passing_score}%.
            </p>

            <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-2">
              <button
                onClick={() => navigate(ROUTES.MOCK_TESTS)}
                className="w-full sm:w-auto px-5 py-2.5 border border-slate-200 hover:bg-slate-50 text-slate-700 rounded-xl text-xs sm:text-sm font-semibold transition-all"
              >
                Return to Catalog
              </button>
              <button
                onClick={() =>
                  navigate(
                    ROUTES.MOCK_TEST_RESULT.replace(":id", attempt?.id || resultData?.attempt_id)
                  )
                }
                className="w-full sm:w-auto px-5 py-2.5 bg-navy-950 hover:bg-navy-900 text-white rounded-xl text-xs sm:text-sm font-semibold transition-all shadow-sm flex items-center justify-center space-x-1.5"
              >
                <span>View Performance Analysis</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MockTestAttempt;
