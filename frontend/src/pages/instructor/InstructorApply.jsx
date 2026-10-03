import React, { useState, useEffect } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../../hooks/useAuth";
import instructorService from "../../services/instructorService";
import Button from "../../components/forms/Button";
import { ROUTES } from "../../constants";
import {
  GraduationCap,
  Award,
  Video,
  ExternalLink,
  CheckCircle2,
  Clock,
  Sparkles,
  ArrowRight,
  ShieldCheck,
  BookOpen,
} from "lucide-react";

export const InstructorApply = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [form, setForm] = useState({
    designation: "",
    institution: "",
    qualification: "",
    expertise_domain: "Full-Stack Web Engineering",
    years_experience: "",
    certificates: "",
    intro_video_url: "",
    bio: "",
    linkedin_url: "",
  });

  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [existingProfile, setExistingProfile] = useState(null);
  const [checkingExisting, setCheckingExisting] = useState(true);

  useEffect(() => {
    const checkProfile = async () => {
      try {
        const res = await instructorService.getProfile();
        if (res?.data) {
          setExistingProfile(res.data);
        }
      } catch (err) {
        // No existing profile, user is free to apply
      } finally {
        setCheckingExisting(false);
      }
    };

    if (user) {
      checkProfile();
    } else {
      setCheckingExisting(false);
    }
  }, [user]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!user) {
      navigate(ROUTES.LOGIN);
      return;
    }

    try {
      setLoading(true);
      const payload = {
        ...form,
        certificates: form.certificates
          ? form.certificates.split(",").map((c) => c.trim()).filter(Boolean)
          : [],
      };
      await instructorService.applyAsInstructor(payload);
      setSubmitted(true);
    } catch (err) {
      console.error("Instructor application failed:", err);
      alert(err.response?.data?.message || "Failed to submit application. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  if (checkingExisting) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-20 text-center">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600 mb-4" />
        <p className="text-slate-600 text-sm">Checking instructor credentials...</p>
      </div>
    );
  }

  if (submitted || existingProfile) {
    const status = existingProfile?.onboarding_status || "PENDING_REVIEW";
    return (
      <div className="max-w-3xl mx-auto px-4 py-16">
        <div className="bg-white rounded-3xl border border-slate-200 p-8 sm:p-12 shadow-sm text-center space-y-6">
          <div className="w-16 h-16 rounded-2xl bg-emerald-100 text-emerald-600 flex items-center justify-center mx-auto shadow-sm">
            <CheckCircle2 className="w-8 h-8" />
          </div>

          <div className="space-y-2">
            <span className="inline-flex items-center space-x-1 px-3 py-1 rounded-full text-xs font-extrabold uppercase tracking-wider bg-amber-100 text-amber-800">
              <Clock className="w-3.5 h-3.5 text-amber-600" />
              <span>Status: {status}</span>
            </span>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-navy-950 font-heading">
              Instructor Dossier Submitted
            </h1>
            <p className="text-sm text-slate-600 max-w-lg mx-auto leading-relaxed">
              Thank you for applying to educate on Skill2Career. Your credentials, teaching domain, and sample video have been registered for administrative board evaluation.
            </p>
          </div>

          <div className="p-4 bg-slate-50 border border-slate-200 rounded-2xl max-w-md mx-auto text-left text-xs space-y-2 text-slate-700">
            <div className="flex justify-between">
              <span className="font-semibold text-slate-500">Applicant:</span>
              <span className="font-bold text-navy-950">{user?.first_name} {user?.last_name}</span>
            </div>
            <div className="flex justify-between">
              <span className="font-semibold text-slate-500">Target Role:</span>
              <span className="font-bold text-navy-950">Accredited Instructor</span>
            </div>
            <div className="flex justify-between">
              <span className="font-semibold text-slate-500">Estimated Review Time:</span>
              <span className="font-bold text-navy-950">24 – 48 Hours</span>
            </div>
          </div>

          <div className="pt-4 flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              to={ROUTES.INSTRUCTOR_DASHBOARD}
              className="inline-flex items-center space-x-2 px-6 py-3 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs shadow-md transition-all"
            >
              <span>Go to Instructor Dashboard</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
            <Link
              to={ROUTES.HOME}
              className="inline-flex items-center px-6 py-3 rounded-xl border border-slate-300 text-slate-700 hover:bg-slate-50 font-semibold text-xs transition-colors"
            >
              Return Home
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12 space-y-8">
      {/* Title & Introduction */}
      <div className="text-center space-y-3">
        <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 border border-emerald-200">
          <Sparkles className="w-3.5 h-3.5 text-emerald-600" />
          <span>SKL-52 Instructor Accreditation Program</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-extrabold text-navy-950 font-heading">
          Teach on Skill2Career
        </h1>
        <p className="text-sm sm:text-base text-slate-600 max-w-2xl mx-auto">
          Share your industry mastery with university students and career switchers across Bangladesh. Receive verified instructor credentials, course publishing rights, and interview mentoring tools.
        </p>
      </div>

      {/* Main Form Card (Matching Instructor reg.png) */}
      <div className="bg-white rounded-3xl border border-slate-200 p-6 sm:p-10 shadow-sm">
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Section 1: Affiliation */}
          <div className="space-y-4">
            <h3 className="text-sm font-extrabold uppercase tracking-wider text-emerald-700 border-b border-slate-100 pb-2 flex items-center space-x-2">
              <GraduationCap className="w-4 h-4" />
              <span>1. Professional & Academic Affiliation</span>
            </h3>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-bold text-navy-900 mb-1">
                  Current Designation / Title *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Senior Software Architect / Assistant Professor"
                  value={form.designation}
                  onChange={(e) => setForm({ ...form, designation: e.target.value })}
                  className="w-full px-3.5 py-2.5 border border-slate-300 rounded-xl text-xs focus:ring-2 focus:ring-emerald-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-navy-900 mb-1">
                  Institution or Company *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. BUET, Dhaka University, Brain Station 23"
                  value={form.institution}
                  onChange={(e) => setForm({ ...form, institution: e.target.value })}
                  className="w-full px-3.5 py-2.5 border border-slate-300 rounded-xl text-xs focus:ring-2 focus:ring-emerald-500 focus:outline-none"
                />
              </div>
            </div>
          </div>

          {/* Section 2: Qualifications & Domain */}
          <div className="space-y-4">
            <h3 className="text-sm font-extrabold uppercase tracking-wider text-emerald-700 border-b border-slate-100 pb-2 flex items-center space-x-2">
              <Award className="w-4 h-4" />
              <span>2. Domain Expertise & Experience</span>
            </h3>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-bold text-navy-900 mb-1">
                  Highest Degree *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. M.Sc. in Computer Science"
                  value={form.qualification}
                  onChange={(e) => setForm({ ...form, qualification: e.target.value })}
                  className="w-full px-3.5 py-2.5 border border-slate-300 rounded-xl text-xs focus:ring-2 focus:ring-emerald-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-navy-900 mb-1">
                  Primary Teaching Domain *
                </label>
                <select
                  value={form.expertise_domain}
                  onChange={(e) => setForm({ ...form, expertise_domain: e.target.value })}
                  className="w-full px-3.5 py-2.5 border border-slate-300 rounded-xl text-xs focus:ring-2 focus:ring-emerald-500 focus:outline-none bg-white"
                >
                  <option value="Full-Stack Web Engineering">Full-Stack Web Engineering</option>
                  <option value="AI, Machine Learning & Data Science">AI, Machine Learning & Data Science</option>
                  <option value="Cloud Architecture & DevOps">Cloud Architecture & DevOps</option>
                  <option value="Cybersecurity & Network Defense">Cybersecurity & Network Defense</option>
                  <option value="Mobile App Development (Flutter/React Native)">Mobile App Development</option>
                  <option value="Software Quality Assurance & Automation">Software QA & Automation</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-navy-900 mb-1">
                  Years of Experience *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. 5+ Years"
                  value={form.years_experience}
                  onChange={(e) => setForm({ ...form, years_experience: e.target.value })}
                  className="w-full px-3.5 py-2.5 border border-slate-300 rounded-xl text-xs focus:ring-2 focus:ring-emerald-500 focus:outline-none"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold text-navy-900 mb-1">
                Certifications & Accreditations (comma-separated)
              </label>
              <input
                type="text"
                placeholder="e.g. AWS Solutions Architect Professional, CKA, Google Cloud ML Engineer"
                value={form.certificates}
                onChange={(e) => setForm({ ...form, certificates: e.target.value })}
                className="w-full px-3.5 py-2.5 border border-slate-300 rounded-xl text-xs focus:ring-2 focus:ring-emerald-500 focus:outline-none"
              />
            </div>
          </div>

          {/* Section 3: Media & Profiles */}
          <div className="space-y-4">
            <h3 className="text-sm font-extrabold uppercase tracking-wider text-emerald-700 border-b border-slate-100 pb-2 flex items-center space-x-2">
              <Video className="w-4 h-4" />
              <span>3. Introductory Lecture & Online Profile</span>
            </h3>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-bold text-navy-900 mb-1">
                  Introductory Video / Sample Lecture URL
                </label>
                <input
                  type="url"
                  placeholder="https://youtube.com/watch?v=... or Google Drive"
                  value={form.intro_video_url}
                  onChange={(e) => setForm({ ...form, intro_video_url: e.target.value })}
                  className="w-full px-3.5 py-2.5 border border-slate-300 rounded-xl text-xs focus:ring-2 focus:ring-emerald-500 focus:outline-none"
                />
                <p className="text-[11px] text-slate-400 mt-1">
                  A 2-5 min sample lecture explaining a technical concept dramatically increases approval speed.
                </p>
              </div>

              <div>
                <label className="block text-xs font-bold text-navy-900 mb-1">
                  LinkedIn Profile / GitHub / Portfolio URL
                </label>
                <input
                  type="url"
                  placeholder="https://linkedin.com/in/username"
                  value={form.linkedin_url}
                  onChange={(e) => setForm({ ...form, linkedin_url: e.target.value })}
                  className="w-full px-3.5 py-2.5 border border-slate-300 rounded-xl text-xs focus:ring-2 focus:ring-emerald-500 focus:outline-none"
                />
              </div>
            </div>
          </div>

          {/* Section 4: Bio */}
          <div className="space-y-2">
            <label className="block text-xs font-bold text-navy-900">
              Biography & Teaching Philosophy *
            </label>
            <textarea
              required
              rows={4}
              placeholder="Tell us about your background, pedagogical methodology, and what makes your instruction impactful for Bangladeshi tech graduates..."
              value={form.bio}
              onChange={(e) => setForm({ ...form, bio: e.target.value })}
              className="w-full px-3.5 py-2.5 border border-slate-300 rounded-xl text-xs focus:ring-2 focus:ring-emerald-500 focus:outline-none"
            />
          </div>

          {/* Submit */}
          <div className="pt-4 border-t border-slate-100 flex items-center justify-between">
            <div className="flex items-center space-x-2 text-xs text-slate-500">
              <ShieldCheck className="w-4 h-4 text-emerald-600" />
              <span>Credentials audited under strict academic privacy protocols</span>
            </div>

            <Button
              type="submit"
              variant="primary"
              size="md"
              disabled={loading}
              className="bg-emerald-600 hover:bg-emerald-700 text-white font-bold px-8 shadow-md"
            >
              {loading ? "Submitting Application..." : "Submit Application for Review"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default InstructorApply;
