import React, { useState } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { ROUTES } from "../constants";
import { formatErrorMessage } from "../utils";
import ForgotPasswordModal from "../components/forms/ForgotPasswordModal";
import {
  GraduationCap,
  FileCheck2,
  Briefcase,
  Eye,
  EyeOff,
  AlertCircle,
  ArrowLeft,
  ShieldCheck,
} from "lucide-react";

export const Login = () => {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [formData, setFormData] = useState({
    email: "",
    password: "",
    remember_me: false,
  });
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [showForgotModal, setShowForgotModal] = useState(false);

  const from = location.state?.from?.pathname || ROUTES.DASHBOARD;

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === "checkbox" ? checked : value,
    }));
    if (error) setError("");
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      await login(formData.email, formData.password, formData.remember_me);
      navigate(from, { replace: true });
    } catch (err) {
      setError(formatErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[calc(100vh-10rem)] py-8 sm:py-12 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto flex items-center">
      <div className="w-full grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-12 items-center">
        {/* Left Column: Hero & Value Proposition (matching Login.png) */}
        <div className="lg:col-span-7 space-y-8 pr-0 lg:pr-6">
          <div className="inline-flex items-center space-x-2 px-3 py-1.5 rounded-full bg-blue-50 border border-blue-100 text-blue-700 text-xs font-bold tracking-wide uppercase">
            <ShieldCheck className="w-4 h-4 text-blue-600" />
            <span>Bangladesh Job Preparation Ecosystem</span>
          </div>

          <div className="space-y-3">
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold text-navy-950 tracking-tight font-heading leading-tight">
              Your Career Journey <br />
              <span className="text-blue-600">Starts Here.</span>
            </h1>
            <p className="text-base sm:text-lg text-slate-600 max-w-xl leading-relaxed">
              Create your account, build your skills, prepare for assessments, and connect with career opportunities in Bangladesh.
            </p>
          </div>

          {/* 3 Value Cards matching Login.png */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2">
            {/* Card 1: Learn & Practice */}
            <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm hover:shadow-md transition-shadow">
              <div className="w-10 h-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center mb-3">
                <GraduationCap className="w-5 h-5" />
              </div>
              <h3 className="font-bold text-navy-900 text-sm mb-1 font-heading">
                Learn & Practice
              </h3>
              <p className="text-xs text-slate-500 leading-normal">
                Industry-aligned courses & guided paths.
              </p>
            </div>

            {/* Card 2: Mock Tests */}
            <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm hover:shadow-md transition-shadow">
              <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center mb-3">
                <FileCheck2 className="w-5 h-5" />
              </div>
              <h3 className="font-bold text-navy-900 text-sm mb-1 font-heading">
                Mock Tests
              </h3>
              <p className="text-xs text-slate-500 leading-normal">
                Real exam simulations & instant feedback.
              </p>
            </div>

            {/* Card 3: Jobs & Internships */}
            <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm hover:shadow-md transition-shadow">
              <div className="w-10 h-10 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center mb-3">
                <Briefcase className="w-5 h-5" />
              </div>
              <h3 className="font-bold text-navy-900 text-sm mb-1 font-heading">
                Jobs & Internships
              </h3>
              <p className="text-xs text-slate-500 leading-normal">
                Direct placement with top employers.
              </p>
            </div>
          </div>

          {/* Social Proof */}
          <div className="pt-2">
            <p className="text-sm font-bold text-navy-900">
              Join 25,00+ ambitious talents
            </p>
            <p className="text-xs text-slate-500">
              Building careers across Bangladesh.
            </p>
          </div>
        </div>

        {/* Right Column: Login Card matching Login.png */}
        <div className="lg:col-span-5">
          <div className="bg-white rounded-3xl border border-slate-200 shadow-lg p-6 sm:p-10 space-y-6">
            {/* Card Top Header */}
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <div className="w-7 h-7 rounded-md bg-navy-950 flex items-center justify-center text-blue-400 font-bold text-xs">
                  A*
                </div>
                <span className="font-extrabold text-sm tracking-tight text-navy-950 font-heading">
                  SKILL<span className="text-blue-600">2</span>CAREER
                </span>
              </div>
              <Link
                to={ROUTES.HOME}
                className="inline-flex items-center text-xs font-semibold text-slate-500 hover:text-navy-950 transition-colors"
              >
                <ArrowLeft className="w-3.5 h-3.5 mr-1" /> Back to Home
              </Link>
            </div>

            {/* Toggle Tab Pills: Login | Register */}
            <div className="grid grid-cols-2 p-1 bg-slate-100 rounded-xl">
              <button
                type="button"
                className="py-2 text-xs font-bold rounded-lg bg-white text-navy-950 shadow-sm transition-all"
              >
                Login
              </button>
              <button
                type="button"
                onClick={() => navigate(ROUTES.REGISTER)}
                className="py-2 text-xs font-semibold rounded-lg text-slate-500 hover:text-navy-900 transition-colors"
              >
                Register
              </button>
            </div>

            {/* Form Titles */}
            <div className="space-y-1">
              <h2 className="text-2xl sm:text-3xl font-extrabold text-navy-950 font-heading">
                Welcome Back
              </h2>
              <p className="text-xs sm:text-sm text-slate-500">
                Enter your credentials to access your career portal.
              </p>
            </div>

            {/* Error Banner */}
            {error && (
              <div className="flex items-start space-x-2.5 p-3 rounded-xl bg-red-50 border border-red-200 text-red-700 text-xs">
                <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                <span className="flex-1 font-medium">{error}</span>
              </div>
            )}

            {/* Login Form */}
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-navy-900 mb-1.5">
                  Email Address
                </label>
                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  placeholder="name@gmail.com"
                  required
                  autoComplete="email"
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-300 text-sm text-navy-950 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 transition-colors"
                />
              </div>

              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label className="block text-xs font-semibold text-navy-900">
                    Password
                  </label>
                  <button
                    type="button"
                    onClick={() => setShowForgotModal(true)}
                    className="text-xs font-semibold text-blue-600 hover:text-blue-800 transition-colors"
                  >
                    Forgot Password?
                  </button>
                </div>
                <div className="relative">
                  <input
                    type={showPassword ? "text" : "password"}
                    name="password"
                    value={formData.password}
                    onChange={handleChange}
                    placeholder="••••••••"
                    required
                    autoComplete="current-password"
                    className="w-full px-4 py-2.5 pr-11 rounded-xl border border-slate-300 text-sm text-navy-950 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 transition-colors"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-slate-400 hover:text-slate-600"
                    title={showPassword ? "Hide password" : "Show password"}
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              {/* Remember me checkbox */}
              <div className="flex items-center">
                <input
                  id="remember_me"
                  name="remember_me"
                  type="checkbox"
                  checked={formData.remember_me}
                  onChange={handleChange}
                  className="h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500 cursor-pointer"
                />
                <label
                  htmlFor="remember_me"
                  className="ml-2 block text-xs font-medium text-slate-600 cursor-pointer"
                >
                  Remember me
                </label>
              </div>

              {/* Submit Button */}
              <button
                type="submit"
                disabled={loading}
                className="w-full bg-black hover:bg-navy-900 text-white font-medium py-3 rounded-xl text-sm shadow-md transition-all disabled:opacity-60 flex items-center justify-center"
              >
                {loading ? (
                  <span className="flex items-center space-x-2">
                    <svg className="animate-spin h-4 w-4 text-white" viewBox="0 0 24 24" fill="none">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    <span>Authenticating...</span>
                  </span>
                ) : (
                  "Login"
                )}
              </button>
            </form>

            {/* Footer switch to register */}
            <div className="text-center text-xs text-slate-500 pt-2 border-t border-slate-100">
              Don't have an account?{" "}
              <Link
                to={ROUTES.REGISTER}
                className="font-bold text-blue-600 hover:text-blue-700 transition-colors"
              >
                Register
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Forgot Password Modal */}
      <ForgotPasswordModal
        isOpen={showForgotModal}
        onClose={() => setShowForgotModal(false)}
      />
    </div>
  );
};

export default Login;
