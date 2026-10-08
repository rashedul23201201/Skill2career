import React, { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import jobService from "../services/jobService";
import screeningService from "../services/screeningService";
import { ROUTES, USER_ROLES } from "../constants";
import {
  ArrowLeft,
  CheckCircle2,
  XCircle,
  Plus,
  Trash2,
  AlertCircle,
  Users,
  Send,
  X,
  Sparkles,
} from "lucide-react";

export const CandidateScreening = () => {
  const { id } = useParams();
  const { user } = useAuth();

  const [job, setJob] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [applicantsData, setApplicantsData] = useState({
    items: [],
    total: 0,
    passed_count: 0,
    disqualified_count: 0,
    avg_match_score: 0,
  });

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [statusFilter, setStatusFilter] = useState("ALL"); // ALL | PASSED | DISQUALIFIED

  // Modals
  const [selectedCandidate, setSelectedCandidate] = useState(null);
  const [isAddQuestionOpen, setIsAddQuestionOpen] = useState(false);
  const [isTestScreeningOpen, setIsTestScreeningOpen] = useState(false);
  const [savingAction, setSavingAction] = useState(false);

  // New question form state
  const [newQuestion, setNewQuestion] = useState({
    question_text: "",
    question_type: "NUMERIC",
    options: "",
    expected_answer: "",
    is_required: true,
    is_deal_breaker: true,
    deal_breaker_rule: "GTE",
    deal_breaker_value: "2",
    deal_breaker_label: "",
    weight: 20,
  });

  // Candidate screening test state
  const [testSubmission, setTestSubmission] = useState({
    candidate_name: user ? `${user.first_name || ""} ${user.last_name || ""}`.trim() : "Test Applicant",
    candidate_email: user?.email || "applicant@example.com",
    answers: {},
  });

  const isOwner = user && job?.company_id === user.id;
  const canManage = isOwner || user?.role === USER_ROLES.ADMIN;

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [jobRes, questionsRes, applicantsRes] = await Promise.all([
        jobService.getJobById(id),
        screeningService.getScreeningQuestions(id),
        screeningService.getApplicants(id, {
          deal_breaker_passed:
            statusFilter === "PASSED" ? true : statusFilter === "DISQUALIFIED" ? false : undefined,
        }),
      ]);

      if (jobRes?.data) setJob(jobRes.data);
      if (questionsRes?.data) setQuestions(questionsRes.data);
      if (applicantsRes?.data) setApplicantsData(applicantsRes.data);
    } catch (err) {
      console.error("Error loading candidate screening data:", err);
      setError(err.response?.data?.message || "Failed to load candidate screening data.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [id, statusFilter]);

  const handleStatusUpdate = async (candidateId, nextStatus) => {
    try {
      setSavingAction(true);
      await screeningService.updateApplicantStatus(candidateId, nextStatus);
      await loadData();
      if (selectedCandidate?.id === candidateId) {
        setSelectedCandidate((prev) => (prev ? { ...prev, status: nextStatus } : null));
      }
    } catch (err) {
      console.error("Failed to update status:", err);
      alert(err.response?.data?.message || "Unable to update candidate status.");
    } finally {
      setSavingAction(false);
    }
  };

  const handleCreateQuestion = async (e) => {
    e.preventDefault();
    if (!newQuestion.question_text.trim()) return;

    try {
      setSavingAction(true);
      const payload = {
        question_text: newQuestion.question_text.trim(),
        question_type: newQuestion.question_type,
        options:
          newQuestion.question_type === "MULTIPLE_CHOICE"
            ? newQuestion.options.split(",").map((s) => s.trim()).filter(Boolean)
            : null,
        expected_answer: newQuestion.expected_answer?.trim() || undefined,
        is_required: newQuestion.is_required,
        is_deal_breaker: newQuestion.is_deal_breaker,
        deal_breaker_rule: newQuestion.is_deal_breaker ? newQuestion.deal_breaker_rule : null,
        deal_breaker_value: newQuestion.is_deal_breaker ? newQuestion.deal_breaker_value : null,
        deal_breaker_label: newQuestion.deal_breaker_label.trim() || undefined,
        weight: Number(newQuestion.weight) || 10,
        order_index: questions.length + 1,
      };

      await screeningService.addScreeningQuestion(id, payload);
      setIsAddQuestionOpen(false);
      setNewQuestion({
        question_text: "",
        question_type: "NUMERIC",
        options: "",
        expected_answer: "",
        is_required: true,
        is_deal_breaker: true,
        deal_breaker_rule: "GTE",
        deal_breaker_value: "2",
        deal_breaker_label: "",
        weight: 20,
      });
      await loadData();
    } catch (err) {
      console.error("Failed to add question:", err);
      alert(err.response?.data?.message || "Error adding screening question.");
    } finally {
      setSavingAction(false);
    }
  };

  const handleDeleteQuestion = async (questionId) => {
    if (!window.confirm("Remove this screening question from the vacancy?")) return;
    try {
      setSavingAction(true);
      await screeningService.deleteScreeningQuestion(questionId);
      await loadData();
    } catch (err) {
      console.error("Failed to delete question:", err);
      alert(err.response?.data?.message || "Error deleting screening question.");
    } finally {
      setSavingAction(false);
    }
  };

  const handleSimulateScreening = async (e) => {
    e.preventDefault();
    try {
      setSavingAction(true);
      const res = await screeningService.screenCandidate(id, testSubmission);
      setIsTestScreeningOpen(false);
      await loadData();
      if (res?.data) {
        setSelectedCandidate(res.data);
      }
    } catch (err) {
      console.error("Screening evaluation failed:", err);
      alert(err.response?.data?.message || "Failed to evaluate screening answers.");
    } finally {
      setSavingAction(false);
    }
  };

  const getScoreBadgeClass = (score) => {
    if (score >= 80) return "bg-emerald-50 text-emerald-700 font-bold border border-emerald-200";
    if (score >= 60) return "bg-blue-50 text-blue-700 font-bold border border-blue-200";
    return "bg-slate-100 text-slate-700 font-bold border border-slate-200";
  };

  if (loading && !job) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 text-center space-y-4">
        <div className="w-10 h-10 border-4 border-slate-900 border-t-transparent rounded-full animate-spin mx-auto" />
        <p className="text-slate-500 text-sm font-medium">Loading recruitment pipeline...</p>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Top Navigation */}
      <div className="flex items-center justify-between">
        <Link
          to={ROUTES.JOB_DETAILS.replace(":id", id)}
          className="inline-flex items-center space-x-1.5 text-xs font-semibold text-slate-500 hover:text-navy-950 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Vacancy Details</span>
        </Link>

        <div className="flex items-center space-x-2">
          <button
            type="button"
            onClick={() => setIsTestScreeningOpen(true)}
            className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg border border-slate-300 text-slate-700 hover:bg-slate-50 text-xs font-semibold shadow-2xs transition-colors"
          >
            <Sparkles className="w-3.5 h-3.5 text-blue-600" />
            <span>Simulate Screening</span>
          </button>

          {canManage && (
            <button
              type="button"
              onClick={() => setIsAddQuestionOpen(true)}
              className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-navy-950 hover:bg-navy-900 text-white text-xs font-semibold shadow-xs transition-colors"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Add Question</span>
            </button>
          )}
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-red-800 text-sm flex items-center justify-between shadow-2xs">
          <div className="flex items-center space-x-2.5">
            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0" />
            <span>{error}</span>
          </div>
          <button onClick={() => setError(null)} className="text-red-700 hover:text-red-900">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Header Section */}
      <div className="space-y-1">
        <h1 className="text-2xl sm:text-3xl font-extrabold text-navy-950 font-heading tracking-tight">
          Recruitment Pipeline: {job?.title || "Candidate Screening"}
        </h1>
        <div className="flex flex-wrap items-center gap-2.5 pt-0.5 text-sm text-slate-600">
          <span className="font-medium text-slate-700">
            {job?.company_name || "Brain Station 23"}
          </span>
          <span>•</span>
          <span className="font-semibold text-slate-900">
            {applicantsData.total} Total Applicants
          </span>
          <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-blue-50 text-blue-700 border border-blue-100 uppercase tracking-wide">
            {job?.status === "ACTIVE" ? "ACTIVE VACANCY" : job?.status || "VACANCY"}
          </span>
        </div>
      </div>

      {/* Two Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Screening Questions & Deal-Breaker Rules */}
        <div className="lg:col-span-5 bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-6">
          <div className="flex items-center justify-between border-b border-slate-100 pb-4">
            <h2 className="text-base font-bold text-navy-950 font-heading">
              Screening Questions & Deal-Breaker Rules Configuration
            </h2>
          </div>

          {questions.length === 0 ? (
            <div className="text-center py-8 space-y-2">
              <p className="text-xs text-slate-400">No screening questions configured yet.</p>
              {canManage && (
                <button
                  type="button"
                  onClick={() => setIsAddQuestionOpen(true)}
                  className="text-xs font-semibold text-blue-600 hover:underline"
                >
                  Configure first screening question
                </button>
              )}
            </div>
          ) : (
            <div className="divide-y divide-slate-100">
              {questions.map((q, idx) => (
                <div key={q.id} className="py-4 first:pt-0 last:pb-0 space-y-2 group">
                  <div className="flex items-center justify-between text-xs text-slate-400">
                    <span className="font-medium">Question {idx + 1}:</span>
                    {canManage && (
                      <button
                        type="button"
                        onClick={() => handleDeleteQuestion(q.id)}
                        disabled={savingAction}
                        className="opacity-0 group-hover:opacity-100 text-slate-400 hover:text-red-600 transition-opacity p-1"
                        title="Remove question"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </div>

                  <p className="text-sm font-semibold text-slate-900 leading-snug">
                    {q.question_text}
                  </p>

                  {q.is_deal_breaker && (
                    <div>
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-50 text-red-600 border border-red-200/80">
                        {q.deal_breaker_label || "Deal-Breaker Requirement"}
                      </span>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Right Column: Candidate Evaluation Table */}
        <div className="lg:col-span-7 bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-4">
            <h2 className="text-base font-bold text-navy-950 font-heading">
              Candidate Evaluation Table
            </h2>

            {/* Filter Pills */}
            <div className="flex items-center space-x-1.5 bg-slate-50 p-1 rounded-xl border border-slate-200/80 text-xs font-semibold">
              <button
                type="button"
                onClick={() => setStatusFilter("ALL")}
                className={`px-3 py-1 rounded-lg transition-all ${
                  statusFilter === "ALL"
                    ? "bg-white text-navy-950 shadow-2xs font-bold"
                    : "text-slate-500 hover:text-navy-950"
                }`}
              >
                All ({(applicantsData.passed_count || 0) + (applicantsData.disqualified_count || 0) || applicantsData.total || 0})
              </button>
              <button
                type="button"
                onClick={() => setStatusFilter("PASSED")}
                className={`px-3 py-1 rounded-lg transition-all ${
                  statusFilter === "PASSED"
                    ? "bg-emerald-600 text-white shadow-2xs font-bold"
                    : "text-slate-500 hover:text-emerald-700"
                }`}
              >
                Passed ({applicantsData.passed_count})
              </button>
              <button
                type="button"
                onClick={() => setStatusFilter("DISQUALIFIED")}
                className={`px-3 py-1 rounded-lg transition-all ${
                  statusFilter === "DISQUALIFIED"
                    ? "bg-rose-600 text-white shadow-2xs font-bold"
                    : "text-slate-500 hover:text-rose-700"
                }`}
              >
                Disqualified ({applicantsData.disqualified_count})
              </button>
            </div>
          </div>

          {applicantsData.items.length === 0 ? (
            <div className="text-center py-12 space-y-2">
              <Users className="w-8 h-8 text-slate-300 mx-auto" />
              <p className="text-sm font-semibold text-slate-700">No candidate submissions found</p>
              <p className="text-xs text-slate-400">
                Candidates applying or evaluated against deal-breaker rules will populate here.
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-100 text-slate-800 font-semibold text-xs">
                    <th className="py-3 px-3">Candidate Name</th>
                    <th className="py-3 px-3">Match Score</th>
                    <th className="py-3 px-3">Deal-Breaker Status</th>
                    <th className="py-3 px-3">Key Answers Preview</th>
                    <th className="py-3 px-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 font-medium">
                  {applicantsData.items.map((candidate) => (
                    <tr
                      key={candidate.id}
                      className="hover:bg-slate-50/75 transition-colors group cursor-pointer"
                      onClick={() => setSelectedCandidate(candidate)}
                    >
                      {/* Candidate Name + Avatar */}
                      <td className="py-3 px-3">
                        <div className="flex items-center space-x-2.5">
                          <div className="w-8 h-8 rounded-full overflow-hidden bg-gradient-to-tr from-slate-200 to-slate-300 flex items-center justify-center text-slate-700 font-bold text-xs flex-shrink-0 shadow-2xs">
                            {candidate.candidate_name
                              ? candidate.candidate_name
                                  .split(" ")
                                  .map((n) => n[0])
                                  .slice(0, 2)
                                  .join("")
                                  .toUpperCase()
                              : "AP"}
                          </div>
                          <div>
                            <div className="font-semibold text-slate-900 text-xs">
                              {candidate.candidate_name}
                            </div>
                            <div className="text-[10px] text-slate-400">
                              {candidate.candidate_email}
                            </div>
                          </div>
                        </div>
                      </td>

                      {/* Match Score Badge */}
                      <td className="py-3 px-3">
                        <span
                          className={`inline-block px-2.5 py-0.5 rounded-full text-xs font-semibold ${getScoreBadgeClass(
                            candidate.match_score
                          )}`}
                        >
                          {Math.round(candidate.match_score)}%
                        </span>
                      </td>

                      {/* Deal Breaker Status */}
                      <td className="py-3 px-3">
                        {candidate.deal_breaker_passed ? (
                          <div className="inline-flex items-center space-x-1.5 text-emerald-600 font-semibold text-xs">
                            <CheckCircle2 className="w-4 h-4 fill-emerald-600 text-white" />
                            <span>Passed</span>
                          </div>
                        ) : (
                          <div className="inline-flex items-center space-x-1.5 text-rose-600 font-semibold text-xs">
                            <XCircle className="w-4 h-4 fill-rose-600 text-white" />
                            <span>Disqualified</span>
                          </div>
                        )}
                      </td>

                      {/* Key Answers Preview */}
                      <td className="py-3 px-3">
                        <span
                          className="text-slate-600 truncate block max-w-[140px] hover:text-slate-900 hover:underline"
                          title={candidate.key_answers_preview || "View full candidate answers"}
                        >
                          {candidate.key_answers_preview || "Key Answers Previ..."}
                        </span>
                      </td>

                      {/* Actions */}
                      <td
                        className="py-3 px-3 text-right space-x-1.5 whitespace-nowrap"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <button
                          type="button"
                          onClick={() => handleStatusUpdate(candidate.id, "SHORTLISTED")}
                          disabled={savingAction || candidate.status === "SHORTLISTED"}
                          className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${
                            candidate.status === "SHORTLISTED"
                              ? "bg-slate-200 text-slate-500 cursor-default"
                              : "bg-black text-white hover:bg-slate-800 shadow-2xs"
                          }`}
                        >
                          Shortlist
                        </button>
                        <button
                          type="button"
                          onClick={() => handleStatusUpdate(candidate.id, "DISQUALIFIED")}
                          disabled={savingAction || candidate.status === "DISQUALIFIED"}
                          className={`px-3 py-1.5 rounded-md text-xs font-semibold border transition-all ${
                            candidate.status === "DISQUALIFIED"
                              ? "border-slate-200 text-slate-400 bg-slate-50 cursor-default"
                              : "border-slate-300 text-slate-800 hover:bg-slate-100"
                          }`}
                        >
                          Disqualify
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Candidate Response Review Modal (AC-3) */}
      {selectedCandidate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-navy-950/60 backdrop-blur-xs">
          <div className="bg-white rounded-2xl border border-slate-200 max-w-lg w-full p-6 space-y-5 shadow-2xl animate-fade-in">
            <div className="flex items-start justify-between border-b border-slate-100 pb-4">
              <div className="space-y-1">
                <div className="flex items-center space-x-2">
                  <h3 className="text-lg font-bold text-navy-950 font-heading">
                    {selectedCandidate.candidate_name}
                  </h3>
                  <span
                    className={`px-2 py-0.5 rounded-full text-xs font-bold ${getScoreBadgeClass(
                      selectedCandidate.match_score
                    )}`}
                  >
                    {Math.round(selectedCandidate.match_score)}% Match
                  </span>
                </div>
                <p className="text-xs text-slate-500">{selectedCandidate.candidate_email}</p>
              </div>
              <button
                onClick={() => setSelectedCandidate(null)}
                className="text-slate-400 hover:text-slate-700 p-1"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Deal Breaker Summary */}
            <div
              className={`p-3 rounded-xl border text-xs flex items-center space-x-2.5 ${
                selectedCandidate.deal_breaker_passed
                  ? "bg-emerald-50 border-emerald-200 text-emerald-800"
                  : "bg-rose-50 border-rose-200 text-rose-800"
              }`}
            >
              {selectedCandidate.deal_breaker_passed ? (
                <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
              ) : (
                <XCircle className="w-4 h-4 text-rose-600 flex-shrink-0" />
              )}
              <span className="font-medium">
                {selectedCandidate.deal_breaker_passed
                  ? "Candidate passed all mandatory deal-breaker requirements."
                  : selectedCandidate.deal_breaker_failed_reason ||
                    "Candidate failed deal-breaker criteria and was automatically flagged."}
              </span>
            </div>

            {/* Full Questions and Candidate Answers */}
            <div className="space-y-3 max-h-72 overflow-y-auto pr-1">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                Submitted Screening Responses
              </h4>
              {questions.map((q) => {
                const answer =
                  selectedCandidate.answers?.[String(q.id)] ||
                  selectedCandidate.answers?.[q.id] ||
                  "No response recorded";
                return (
                  <div key={q.id} className="p-3 rounded-xl bg-slate-50 border border-slate-100 space-y-1">
                    <div className="flex items-center justify-between text-[11px] text-slate-500 font-medium">
                      <span>{q.question_text}</span>
                      {q.is_deal_breaker && (
                        <span className="text-[10px] font-bold text-rose-600 uppercase">
                          Deal-Breaker
                        </span>
                      )}
                    </div>
                    <div className="text-xs font-semibold text-navy-950">{String(answer)}</div>
                  </div>
                );
              })}
            </div>

            {/* Modal Actions */}
            <div className="pt-2 border-t border-slate-100 flex items-center justify-between">
              <div className="text-xs font-semibold text-slate-500">
                Current Status:{" "}
                <span className="font-bold text-slate-800">{selectedCandidate.status}</span>
              </div>
              <div className="flex items-center space-x-2">
                <button
                  type="button"
                  onClick={() => handleStatusUpdate(selectedCandidate.id, "SHORTLISTED")}
                  disabled={savingAction}
                  className="px-3 py-1.5 rounded-lg bg-black text-white hover:bg-slate-800 text-xs font-semibold"
                >
                  Shortlist
                </button>
                <button
                  type="button"
                  onClick={() => handleStatusUpdate(selectedCandidate.id, "DISQUALIFIED")}
                  disabled={savingAction}
                  className="px-3 py-1.5 rounded-lg border border-slate-300 text-slate-700 hover:bg-slate-100 text-xs font-semibold"
                >
                  Disqualify
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Add Screening Question Modal (AC-1) */}
      {isAddQuestionOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-navy-950/60 backdrop-blur-xs">
          <div className="bg-white rounded-2xl border border-slate-200 max-w-md w-full p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="text-base font-bold text-navy-950 font-heading">
                Configure Screening Question
              </h3>
              <button
                onClick={() => setIsAddQuestionOpen(false)}
                className="text-slate-400 hover:text-slate-700"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreateQuestion} className="space-y-4 text-xs">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Question Prompt</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Years of hands-on React/Node experience?"
                  value={newQuestion.question_text}
                  onChange={(e) => setNewQuestion({ ...newQuestion, question_text: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs focus:ring-1 focus:ring-navy-900 focus:outline-hidden"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Answer Format</label>
                  <select
                    value={newQuestion.question_type}
                    onChange={(e) => setNewQuestion({ ...newQuestion, question_type: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs focus:ring-1 focus:ring-navy-900 focus:outline-hidden"
                  >
                    <option value="NUMERIC">Numeric Input</option>
                    <option value="YES_NO">Yes / No</option>
                    <option value="MULTIPLE_CHOICE">Multiple Choice</option>
                    <option value="TEXT">Short Text</option>
                  </select>
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Points Weight</label>
                  <input
                    type="number"
                    min="1"
                    max="100"
                    value={newQuestion.weight}
                    onChange={(e) => setNewQuestion({ ...newQuestion, weight: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs focus:ring-1 focus:ring-navy-900 focus:outline-hidden"
                  />
                </div>
              </div>

              {newQuestion.question_type === "MULTIPLE_CHOICE" && (
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">
                    Options (comma-separated)
                  </label>
                  <input
                    type="text"
                    placeholder="Option A, Option B, Option C"
                    value={newQuestion.options}
                    onChange={(e) => setNewQuestion({ ...newQuestion, options: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs"
                  />
                </div>
              )}

              {/* Deal Breaker Toggle & Threshold */}
              <div className="p-3 rounded-xl bg-slate-50 border border-slate-200/80 space-y-3">
                <label className="flex items-center space-x-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={newQuestion.is_deal_breaker}
                    onChange={(e) =>
                      setNewQuestion({ ...newQuestion, is_deal_breaker: e.target.checked })
                    }
                    className="rounded border-slate-300 text-navy-950 focus:ring-navy-900"
                  />
                  <span className="font-bold text-slate-800">
                    Deal-Breaker (Auto-Disqualification Rule)
                  </span>
                </label>

                {newQuestion.is_deal_breaker && (
                  <div className="space-y-2 pt-1 border-t border-slate-200/60">
                    <div className="grid grid-cols-2 gap-2">
                      <div>
                        <label className="block text-[11px] font-semibold text-slate-600 mb-0.5">
                          Rule Type
                        </label>
                        <select
                          value={newQuestion.deal_breaker_rule}
                          onChange={(e) =>
                            setNewQuestion({ ...newQuestion, deal_breaker_rule: e.target.value })
                          }
                          className="w-full px-2 py-1.5 border border-slate-300 rounded-md text-xs"
                        >
                          <option value="GTE">Must be ≥ Value</option>
                          <option value="MANDATORY">Mandatory Answer</option>
                          <option value="EQUALS">Must Equal Exactly</option>
                        </select>
                      </div>
                      <div>
                        <label className="block text-[11px] font-semibold text-slate-600 mb-0.5">
                          Threshold Value
                        </label>
                        <input
                          type="text"
                          placeholder="e.g. 2 or Yes"
                          value={newQuestion.deal_breaker_value}
                          onChange={(e) =>
                            setNewQuestion({ ...newQuestion, deal_breaker_value: e.target.value })
                          }
                          className="w-full px-2 py-1.5 border border-slate-300 rounded-md text-xs"
                        />
                      </div>
                    </div>
                    <div>
                      <label className="block text-[11px] font-semibold text-slate-600 mb-0.5">
                        Badge Label
                      </label>
                      <input
                        type="text"
                        placeholder="Deal-Breaker: Auto-Disqualify if < 2 Years"
                        value={newQuestion.deal_breaker_label}
                        onChange={(e) =>
                          setNewQuestion({ ...newQuestion, deal_breaker_label: e.target.value })
                        }
                        className="w-full px-2 py-1.5 border border-slate-300 rounded-md text-xs"
                      />
                    </div>
                  </div>
                )}
              </div>

              <div className="pt-2 flex items-center justify-end space-x-2">
                <button
                  type="button"
                  onClick={() => setIsAddQuestionOpen(false)}
                  className="px-3 py-1.5 rounded-lg border border-slate-300 text-slate-700 hover:bg-slate-50 font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={savingAction}
                  className="px-4 py-1.5 rounded-lg bg-navy-950 text-white hover:bg-navy-900 font-semibold shadow-xs"
                >
                  {savingAction ? "Saving..." : "Save Question"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Interactive Screening Test Simulation Modal (AC-2) */}
      {isTestScreeningOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-navy-950/60 backdrop-blur-xs">
          <div className="bg-white rounded-2xl border border-slate-200 max-w-lg w-full p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="space-y-0.5">
                <h3 className="text-base font-bold text-navy-950 font-heading">
                  Simulate Candidate Screening Application
                </h3>
                <p className="text-[11px] text-slate-500">
                  Submit candidate answers to verify automatic qualification scoring and deal-breaker filtering
                </p>
              </div>
              <button
                onClick={() => setIsTestScreeningOpen(false)}
                className="text-slate-400 hover:text-slate-700"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSimulateScreening} className="space-y-4 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Candidate Name</label>
                  <input
                    type="text"
                    required
                    value={testSubmission.candidate_name}
                    onChange={(e) =>
                      setTestSubmission({ ...testSubmission, candidate_name: e.target.value })
                    }
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Candidate Email</label>
                  <input
                    type="email"
                    required
                    value={testSubmission.candidate_email}
                    onChange={(e) =>
                      setTestSubmission({ ...testSubmission, candidate_email: e.target.value })
                    }
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs"
                  />
                </div>
              </div>

              <div className="space-y-3 pt-2 border-t border-slate-100">
                <h4 className="font-bold text-slate-800 text-xs">Screening Questions</h4>
                {questions.map((q) => (
                  <div key={q.id} className="space-y-1">
                    <label className="block font-semibold text-slate-700">
                      {q.question_text}{" "}
                      {q.is_deal_breaker && (
                        <span className="text-[10px] text-rose-600 font-bold uppercase">
                          (Deal-Breaker)
                        </span>
                      )}
                    </label>

                    {q.question_type === "YES_NO" ? (
                      <select
                        value={testSubmission.answers[q.id] || ""}
                        onChange={(e) =>
                          setTestSubmission({
                            ...testSubmission,
                            answers: { ...testSubmission.answers, [q.id]: e.target.value },
                          })
                        }
                        className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs"
                      >
                        <option value="">Select an option</option>
                        <option value="Yes">Yes</option>
                        <option value="No">No</option>
                      </select>
                    ) : q.question_type === "MULTIPLE_CHOICE" && Array.isArray(q.options) && q.options.length > 0 ? (
                      <select
                        value={testSubmission.answers[q.id] || ""}
                        onChange={(e) =>
                          setTestSubmission({
                            ...testSubmission,
                            answers: { ...testSubmission.answers, [q.id]: e.target.value },
                          })
                        }
                        className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs"
                      >
                        <option value="">Select an option</option>
                        {q.options.map((opt) => (
                          <option key={opt} value={opt}>
                            {opt}
                          </option>
                        ))}
                      </select>
                    ) : (
                      <input
                        type="text"
                        placeholder={
                          q.question_type === "NUMERIC" ? "e.g. 3 years" : "Enter response"
                        }
                        value={testSubmission.answers[q.id] || ""}
                        onChange={(e) =>
                          setTestSubmission({
                            ...testSubmission,
                            answers: { ...testSubmission.answers, [q.id]: e.target.value },
                          })
                        }
                        className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs"
                      />
                    )}
                  </div>
                ))}
              </div>

              <div className="pt-2 flex items-center justify-end space-x-2">
                <button
                  type="button"
                  onClick={() => setIsTestScreeningOpen(false)}
                  className="px-3 py-1.5 rounded-lg border border-slate-300 text-slate-700 hover:bg-slate-50 font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={savingAction}
                  className="inline-flex items-center space-x-1.5 px-4 py-1.5 rounded-lg bg-navy-950 text-white hover:bg-navy-900 font-semibold shadow-xs"
                >
                  <Send className="w-3.5 h-3.5" />
                  <span>{savingAction ? "Evaluating..." : "Submit & Evaluate"}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default CandidateScreening;
