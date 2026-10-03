import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../../hooks/useAuth";
import instructorService from "../../services/instructorService";
import Button from "../../components/forms/Button";
import { ROUTES } from "../../constants";
import {
  GraduationCap,
  BookOpen,
  Users,
  Calendar,
  CheckCircle2,
  Clock,
  AlertCircle,
  ExternalLink,
  Edit3,
  Video,
  Award,
  PlusCircle,
  Briefcase,
  Building,
  RefreshCw,
  X,
  Sparkles,
} from "lucide-react";

export const InstructorDashboard = () => {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [editForm, setEditForm] = useState({
    designation: "",
    institution: "",
    qualification: "",
    expertise_domain: "",
    years_experience: "",
    intro_video_url: "",
    bio: "",
    linkedin_url: "",
  });
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  const fetchDashboard = async (isManual = false) => {
    try {
      if (isManual) setRefreshing(true);
      else setLoading(true);
      setError(null);

      const [statsRes, profileRes] = await Promise.all([
        instructorService.getDashboardStats().catch(() => null),
        instructorService.getProfile().catch(() => null),
      ]);

      if (statsRes?.data) setStats(statsRes.data);
      if (profileRes?.data) {
        setProfile(profileRes.data);
        setEditForm({
          designation: profileRes.data.designation || "",
          institution: profileRes.data.institution || "",
          qualification: profileRes.data.qualification || "",
          expertise_domain: profileRes.data.expertise_domain || "",
          years_experience: profileRes.data.years_experience || "",
          intro_video_url: profileRes.data.intro_video_url || "",
          bio: profileRes.data.bio || "",
          linkedin_url: profileRes.data.linkedin_url || "",
        });
      }
    } catch (err) {
      console.error("Failed to load instructor dashboard:", err);
      setError("Unable to load instructor telemetry. Please check server connectivity.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchDashboard();
  }, []);

  const handleEditSubmit = async (e) => {
    e.preventDefault();
    try {
      setSaving(true);
      const res = await instructorService.updateProfile(editForm);
      if (res?.data) {
        setProfile(res.data);
        setSaveSuccess(true);
        setTimeout(() => {
          setSaveSuccess(false);
          setIsEditModalOpen(false);
        }, 1200);
      }
    } catch (err) {
      console.error("Failed to update instructor profile:", err);
      alert(err.response?.data?.message || "Failed to update profile.");
    } finally {
      setSaving(false);
    }
  };

  const onboardingStatus = profile?.onboarding_status || stats?.onboarding_status || "PENDING_REVIEW";

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-20 text-center">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600 mb-4" />
        <p className="text-slate-600 text-sm font-medium">Loading instructor workspace...</p>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header Banner */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 sm:p-8 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="space-y-2">
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-2xl sm:text-3xl font-extrabold text-navy-950 font-heading">
              Welcome back, {user?.first_name || profile?.first_name || "Instructor"}!
            </h1>
            {onboardingStatus === "APPROVED" ? (
              <span className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 border border-emerald-300">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                <span>Verified Instructor</span>
              </span>
            ) : onboardingStatus === "REJECTED" ? (
              <span className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-bold bg-red-100 text-red-800 border border-red-300">
                <AlertCircle className="w-3.5 h-3.5 text-red-600" />
                <span>Application Needs Revision</span>
              </span>
            ) : (
              <span className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-bold bg-amber-100 text-amber-800 border border-amber-300">
                <Clock className="w-3.5 h-3.5 text-amber-600" />
                <span>Pending Administrative Review</span>
              </span>
            )}
          </div>
          <p className="text-sm text-slate-500">
            {profile?.designation ? `${profile.designation} · ${profile?.institution || "Independent Educator"}` : "Instructor Account Management (SKL-52)"}
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <Button
            variant="outline"
            size="sm"
            onClick={() => fetchDashboard(true)}
            disabled={refreshing}
            className="flex items-center space-x-1.5"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? "animate-spin" : ""}`} />
            <span>Refresh</span>
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={() => setIsEditModalOpen(true)}
            className="flex items-center space-x-1.5 bg-emerald-600 hover:bg-emerald-700 text-white"
          >
            <Edit3 className="w-3.5 h-3.5" />
            <span>Edit Credentials</span>
          </Button>
        </div>
      </div>

      {/* Onboarding Notice Banner */}
      {onboardingStatus === "PENDING_REVIEW" && (
        <div className="bg-amber-50 border border-amber-200 rounded-2xl p-5 text-amber-900 flex items-start space-x-4 shadow-sm">
          <Clock className="w-5 h-5 text-amber-600 mt-0.5 flex-shrink-0" />
          <div className="text-sm space-y-1">
            <h3 className="font-bold text-amber-950">Application Pending Review (SKL-52)</h3>
            <p className="text-amber-800 leading-relaxed">
              Your instructor accreditation dossier has been submitted and is currently being audited by the platform administrative board. Once verified, your status will become <strong>APPROVED</strong> and full course creation and mock test scheduling capabilities will be unlocked.
            </p>
          </div>
        </div>
      )}

      {onboardingStatus === "REJECTED" && (
        <div className="bg-red-50 border border-red-200 rounded-2xl p-5 text-red-900 flex items-start space-x-4 shadow-sm">
          <AlertCircle className="w-5 h-5 text-red-600 mt-0.5 flex-shrink-0" />
          <div className="text-sm space-y-2">
            <h3 className="font-bold text-red-950">Application Requires Revision</h3>
            <p className="text-red-800 leading-relaxed">
              The administrative committee has requested additional credentials or clarifications. Please update your qualifications, experience, and introductory lecture video using the button below.
            </p>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsEditModalOpen(true)}
              className="bg-white border-red-300 text-red-700 hover:bg-red-50 text-xs"
            >
              Update Application Credentials
            </Button>
          </div>
        </div>
      )}

      {/* 4 Metric Cards (Matching Instructors dashboard.png) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between mb-4">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500">Active Courses</span>
            <div className="w-10 h-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center">
              <BookOpen className="w-5 h-5" />
            </div>
          </div>
          <div className="text-3xl font-extrabold text-navy-950 font-heading">
            {stats?.active_courses ?? 0}
          </div>
          <p className="text-xs text-slate-500 mt-2">Published learning tracks</p>
        </div>

        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between mb-4">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500">Total Learners</span>
            <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center">
              <Users className="w-5 h-5" />
            </div>
          </div>
          <div className="text-3xl font-extrabold text-navy-950 font-heading">
            {stats?.total_learners ?? 0}
          </div>
          <p className="text-xs text-slate-500 mt-2">Students enrolled across tracks</p>
        </div>

        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between mb-4">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500">Mock Tests</span>
            <div className="w-10 h-10 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center">
              <Award className="w-5 h-5" />
            </div>
          </div>
          <div className="text-3xl font-extrabold text-navy-950 font-heading">
            {stats?.mock_tests ?? 0}
          </div>
          <p className="text-xs text-slate-500 mt-2">Assessment papers active</p>
        </div>

        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between mb-4">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500">Upcoming Interviews</span>
            <div className="w-10 h-10 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center">
              <Calendar className="w-5 h-5" />
            </div>
          </div>
          <div className="text-3xl font-extrabold text-navy-950 font-heading">
            {stats?.upcoming_interviews ?? 0}
          </div>
          <p className="text-xs text-slate-500 mt-2">Scheduled 1-on-1 mock sessions</p>
        </div>
      </div>

      {/* Main Grid: Credentials & Modules */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Profile & Credentials Card (2 cols) */}
        <div className="lg:col-span-2 bg-white rounded-2xl border border-slate-200 p-6 sm:p-8 shadow-sm space-y-6">
          <div className="flex items-center justify-between border-b border-slate-100 pb-4">
            <div className="flex items-center space-x-2">
              <GraduationCap className="w-5 h-5 text-emerald-600" />
              <h2 className="text-lg font-bold text-navy-950 font-heading">
                Academic & Professional Dossier
              </h2>
            </div>
            <button
              onClick={() => setIsEditModalOpen(true)}
              className="text-xs font-semibold text-emerald-600 hover:text-emerald-700 flex items-center space-x-1"
            >
              <Edit3 className="w-3.5 h-3.5" />
              <span>Edit Details</span>
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-1">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Designation</span>
              <p className="text-sm font-semibold text-navy-900">{profile?.designation || "Not specified"}</p>
            </div>
            <div className="space-y-1">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Institution / Org</span>
              <p className="text-sm font-semibold text-navy-900">{profile?.institution || "Not specified"}</p>
            </div>
            <div className="space-y-1">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Highest Qualification</span>
              <p className="text-sm font-semibold text-navy-900">{profile?.qualification || "Not specified"}</p>
            </div>
            <div className="space-y-1">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Domain Expertise</span>
              <p className="text-sm font-semibold text-navy-900">{profile?.expertise_domain || "Not specified"}</p>
            </div>
            <div className="space-y-1">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Experience</span>
              <p className="text-sm font-semibold text-navy-900">{profile?.years_experience || "Not specified"}</p>
            </div>
            <div className="space-y-1">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-400">LinkedIn / Profile</span>
              {profile?.linkedin_url ? (
                <a
                  href={profile.linkedin_url}
                  target="_blank"
                  rel="noreferrer"
                  className="text-sm font-semibold text-blue-600 hover:underline inline-flex items-center space-x-1 truncate max-w-xs"
                >
                  <span className="truncate">{profile.linkedin_url}</span>
                  <ExternalLink className="w-3 h-3 flex-shrink-0" />
                </a>
              ) : (
                <p className="text-sm text-slate-400 italic">No link attached</p>
              )}
            </div>
          </div>

          {/* Intro Video Preview */}
          {profile?.intro_video_url && (
            <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="w-9 h-9 rounded-lg bg-red-100 text-red-600 flex items-center justify-center">
                  <Video className="w-4 h-4" />
                </div>
                <div>
                  <h4 className="text-xs font-bold text-navy-950">Introductory Lecture / Video Link</h4>
                  <p className="text-xs text-slate-500 truncate max-w-md">{profile.intro_video_url}</p>
                </div>
              </div>
              <a
                href={profile.intro_video_url}
                target="_blank"
                rel="noreferrer"
                className="px-3 py-1.5 text-xs font-semibold bg-white border border-slate-200 rounded-lg text-slate-700 hover:bg-slate-100 flex items-center space-x-1"
              >
                <span>Watch</span>
                <ExternalLink className="w-3 h-3" />
              </a>
            </div>
          )}

          {/* Bio */}
          <div className="space-y-2">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Teaching Philosophy & Bio</span>
            <p className="text-sm text-slate-700 leading-relaxed bg-slate-50/50 p-4 rounded-xl border border-slate-100">
              {profile?.bio || "No professional biography provided yet. Add your teaching methodology and career highlights to enhance learner trust."}
            </p>
          </div>
        </div>

        {/* Quick Actions & Sprint 2/3 Feature Card (1 col) */}
        <div className="space-y-6">
          {/* Quick Create Card */}
          <div className="bg-gradient-to-br from-navy-950 to-blue-950 text-white rounded-2xl p-6 shadow-md space-y-4">
            <div className="flex items-center space-x-2">
              <Sparkles className="w-4 h-4 text-emerald-400" />
              <span className="text-xs font-extrabold uppercase tracking-wider text-emerald-400">Course Management</span>
            </div>
            <h3 className="text-xl font-bold font-heading">Publish New Curriculum</h3>
            <p className="text-xs text-slate-300 leading-relaxed">
              Design comprehensive video lessons, project assignments, and automated quizzes for Bangladeshi students.
            </p>
            <div className="pt-2">
              <Button
                variant="primary"
                size="sm"
                className="w-full bg-emerald-500 hover:bg-emerald-600 text-white font-bold flex items-center justify-center space-x-2"
                onClick={() => alert("Sprint 2 Feature: Course Curriculum Creation will be available in the upcoming release.")}
              >
                <PlusCircle className="w-4 h-4" />
                <span>Create Course (Sprint 2)</span>
              </Button>
            </div>
          </div>

          {/* Mock Test Card */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-4">
            <div className="flex items-center space-x-2 text-purple-600">
              <Award className="w-4 h-4" />
              <h4 className="text-sm font-bold text-navy-950 font-heading">Mock Exam Sandbox</h4>
            </div>
            <p className="text-xs text-slate-500 leading-relaxed">
              Draft technical coding problems and multiple-choice aptitude tests mapped to BD IT industry hiring standards.
            </p>
            <Button
              variant="outline"
              size="sm"
              className="w-full text-xs font-semibold"
              onClick={() => alert("Sprint 3 Feature: Mock Exam Sandbox is scheduled for Sprint 3.")}
            >
              <span>Explore Assessment Tools</span>
            </Button>
          </div>
        </div>
      </div>

      {/* Edit Profile Modal */}
      {isEditModalOpen && (
        <div className="fixed inset-0 z-50 overflow-y-auto bg-navy-950/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-2xl w-full p-6 sm:p-8 shadow-2xl relative border border-slate-200">
            <button
              onClick={() => setIsEditModalOpen(false)}
              className="absolute top-6 right-6 text-slate-400 hover:text-slate-600"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="space-y-1 mb-6">
              <h3 className="text-xl font-bold text-navy-950 font-heading">
                Update Instructor Credentials
              </h3>
              <p className="text-xs text-slate-500">
                Keep your academic affiliations, expertise domains, and introductory video updated.
              </p>
            </div>

            {saveSuccess && (
              <div className="mb-4 p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl text-xs font-semibold flex items-center space-x-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                <span>Credentials successfully saved!</span>
              </div>
            )}

            <form onSubmit={handleEditSubmit} className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-navy-900 mb-1">
                    Professional Designation
                  </label>
                  <input
                    type="text"
                    required
                    value={editForm.designation}
                    onChange={(e) => setEditForm({ ...editForm, designation: e.target.value })}
                    placeholder="e.g. Senior Software Architect / Lecturer"
                    className="w-full px-3 py-2 border border-slate-300 rounded-xl text-xs focus:ring-2 focus:ring-emerald-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-navy-900 mb-1">
                    Institution / Organization
                  </label>
                  <input
                    type="text"
                    required
                    value={editForm.institution}
                    onChange={(e) => setEditForm({ ...editForm, institution: e.target.value })}
                    placeholder="e.g. BUET / Brain Station 23"
                    className="w-full px-3 py-2 border border-slate-300 rounded-xl text-xs focus:ring-2 focus:ring-emerald-500 focus:outline-none"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-navy-900 mb-1">
                    Highest Academic Degree
                  </label>
                  <input
                    type="text"
                    value={editForm.qualification}
                    onChange={(e) => setEditForm({ ...editForm, qualification: e.target.value })}
                    placeholder="e.g. M.Sc. in Computer Science"
                    className="w-full px-3 py-2 border border-slate-300 rounded-xl text-xs focus:ring-2 focus:ring-emerald-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-navy-900 mb-1">
                    Expertise Domain
                  </label>
                  <input
                    type="text"
                    value={editForm.expertise_domain}
                    onChange={(e) => setEditForm({ ...editForm, expertise_domain: e.target.value })}
                    placeholder="e.g. Full-Stack Web, AI/ML, Cloud DevOps"
                    className="w-full px-3 py-2 border border-slate-300 rounded-xl text-xs focus:ring-2 focus:ring-emerald-500 focus:outline-none"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-navy-900 mb-1">
                    Years of Experience
                  </label>
                  <input
                    type="text"
                    value={editForm.years_experience}
                    onChange={(e) => setEditForm({ ...editForm, years_experience: e.target.value })}
                    placeholder="e.g. 6+ years"
                    className="w-full px-3 py-2 border border-slate-300 rounded-xl text-xs focus:ring-2 focus:ring-emerald-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-navy-900 mb-1">
                    LinkedIn / Portfolio URL
                  </label>
                  <input
                    type="url"
                    value={editForm.linkedin_url}
                    onChange={(e) => setEditForm({ ...editForm, linkedin_url: e.target.value })}
                    placeholder="https://linkedin.com/in/username"
                    className="w-full px-3 py-2 border border-slate-300 rounded-xl text-xs focus:ring-2 focus:ring-emerald-500 focus:outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-navy-900 mb-1">
                  Introductory Lecture / Sample Video URL
                </label>
                <input
                  type="url"
                  value={editForm.intro_video_url}
                  onChange={(e) => setEditForm({ ...editForm, intro_video_url: e.target.value })}
                  placeholder="https://youtube.com/watch?v=..."
                  className="w-full px-3 py-2 border border-slate-300 rounded-xl text-xs focus:ring-2 focus:ring-emerald-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-navy-900 mb-1">
                  Teaching Philosophy & Professional Biography
                </label>
                <textarea
                  rows={4}
                  value={editForm.bio}
                  onChange={(e) => setEditForm({ ...editForm, bio: e.target.value })}
                  placeholder="Describe your practical teaching approach and accomplishments..."
                  className="w-full px-3 py-2 border border-slate-300 rounded-xl text-xs focus:ring-2 focus:ring-emerald-500 focus:outline-none"
                />
              </div>

              <div className="flex items-center justify-end space-x-3 pt-3 border-t border-slate-100">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setIsEditModalOpen(false)}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  variant="primary"
                  size="sm"
                  disabled={saving}
                  className="bg-emerald-600 hover:bg-emerald-700 text-white"
                >
                  {saving ? "Saving..." : "Save Credentials"}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default InstructorDashboard;
