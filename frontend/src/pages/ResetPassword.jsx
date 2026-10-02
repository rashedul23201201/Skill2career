import React, { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { authService } from "../services/authService";
import { ROUTES } from "../constants";
import { formatErrorMessage } from "../utils";
import { Lock, Eye, EyeOff, CheckCircle, AlertCircle, ArrowLeft } from "lucide-react";

export const ResetPassword = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const tokenFromUrl = searchParams.get("token") || "";

  const [token, setToken] = useState(tokenFromUrl);
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (!token.trim()) {
      setError("Password reset token is required.");
      return;
    }

    if (newPassword.length < 8) {
      setError("New password must be at least 8 characters long.");
      return;
    }

    if (newPassword !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setLoading(true);

    try {
      await authService.resetPassword({
        token: token.trim(),
        new_password: newPassword,
      });
      setSuccess(true);
    } catch (err) {
      setError(formatErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[calc(100vh-12rem)] flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full bg-white rounded-3xl border border-slate-200 shadow-md p-6 sm:p-10 space-y-6">
        {!success ? (
          <>
            <div className="text-center space-y-2">
              <div className="w-12 h-12 rounded-xl bg-blue-50 text-blue-600 mx-auto flex items-center justify-center mb-2">
                <Lock className="w-6 h-6" />
              </div>
              <h2 className="text-2xl font-extrabold text-navy-950 font-heading">
                Set New Password
              </h2>
              <p className="text-xs sm:text-sm text-slate-500">
                Please enter and confirm your new secure password.
              </p>
            </div>

            {error && (
              <div className="flex items-start space-x-2.5 p-3 rounded-xl bg-red-50 border border-red-200 text-red-700 text-xs">
                <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                <span className="flex-1 font-medium">{error}</span>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              {!tokenFromUrl && (
                <div>
                  <label className="block text-xs font-semibold text-navy-900 mb-1.5">
                    Reset Token <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={token}
                    onChange={(e) => setToken(e.target.value)}
                    placeholder="Paste your reset token"
                    required
                    className="w-full px-4 py-2.5 rounded-xl border border-slate-300 text-sm font-mono text-navy-950 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 transition-colors"
                  />
                </div>
              )}

              <div>
                <label className="block text-xs font-semibold text-navy-900 mb-1.5">
                  New Password <span className="text-red-500">*</span>
                </label>
                <div className="relative">
                  <input
                    type={showPassword ? "text" : "password"}
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    placeholder="Min. 8 characters"
                    required
                    className="w-full px-4 py-2.5 pr-11 rounded-xl border border-slate-300 text-sm text-navy-950 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 transition-colors"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-slate-400 hover:text-slate-600"
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-navy-900 mb-1.5">
                  Confirm New Password <span className="text-red-500">*</span>
                </label>
                <input
                  type={showPassword ? "text" : "password"}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Re-enter new password"
                  required
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-300 text-sm text-navy-950 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 transition-colors"
                />
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full bg-black hover:bg-navy-900 text-white font-medium py-3 rounded-xl text-sm shadow-md transition-all disabled:opacity-60 flex items-center justify-center"
              >
                {loading ? "Updating Password..." : "Update Password"}
              </button>
            </form>

            <div className="text-center pt-2">
              <Link
                to={ROUTES.LOGIN}
                className="inline-flex items-center text-xs font-semibold text-slate-500 hover:text-navy-950 transition-colors"
              >
                <ArrowLeft className="w-3.5 h-3.5 mr-1" /> Back to Login
              </Link>
            </div>
          </>
        ) : (
          <div className="space-y-6 text-center py-4">
            <div className="w-16 h-16 rounded-full bg-emerald-50 text-emerald-600 mx-auto flex items-center justify-center">
              <CheckCircle className="w-10 h-10" />
            </div>

            <div className="space-y-2">
              <h3 className="text-2xl font-extrabold text-navy-950 font-heading">
                Password Reset Complete
              </h3>
              <p className="text-sm text-slate-600">
                Your password has been securely updated. All previous active sessions have been revoked.
              </p>
            </div>

            <button
              type="button"
              onClick={() => navigate(ROUTES.LOGIN)}
              className="w-full bg-black hover:bg-navy-900 text-white font-medium py-3 rounded-xl text-sm shadow-md transition-all"
            >
              Sign In with New Password
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default ResetPassword;
