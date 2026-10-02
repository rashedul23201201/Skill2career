import React, { useState } from "react";
import { Link } from "react-router-dom";
import { authService } from "../../services/authService";
import { formatErrorMessage } from "../../utils";
import { ROUTES } from "../../constants";
import { X, Mail, CheckCircle, AlertCircle, ArrowRight } from "lucide-react";

export const ForgotPasswordModal = ({ isOpen, onClose }) => {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [successData, setSuccessData] = useState(null);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const response = await authService.forgotPassword(email);
      setSuccessData(response.data);
    } catch (err) {
      setError(formatErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setEmail("");
    setError("");
    setSuccessData(null);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-navy-950/60 backdrop-blur-sm animate-fade-in">
      <div className="relative w-full max-w-md bg-white rounded-2xl shadow-xl border border-slate-100 p-6 sm:p-8 space-y-6">
        {/* Close Button */}
        <button
          type="button"
          onClick={handleClose}
          className="absolute top-5 right-5 text-slate-400 hover:text-slate-600 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        {!successData ? (
          <>
            <div className="space-y-2">
              <div className="w-12 h-12 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center mb-3">
                <Mail className="w-6 h-6" />
              </div>
              <h3 className="text-xl font-bold text-navy-900 font-heading">
                Reset Your Password
              </h3>
              <p className="text-sm text-slate-500">
                Enter your registered email address and we'll send you instructions to reset your password.
              </p>
            </div>

            {error && (
              <div className="flex items-center space-x-2 p-3 bg-red-50 border border-red-200 text-red-700 text-xs rounded-lg">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-navy-800 uppercase tracking-wider mb-1.5">
                  Email Address
                </label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@gmail.com"
                  required
                  className="w-full px-4 py-2.5 rounded-lg border border-slate-300 text-sm text-navy-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600"
                />
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full bg-black hover:bg-navy-900 text-white font-medium py-3 rounded-lg text-sm shadow transition-all disabled:opacity-50"
              >
                {loading ? "Sending..." : "Send Reset Instructions"}
              </button>
            </form>
          </>
        ) : (
          <div className="space-y-5 text-center py-2">
            <div className="w-14 h-14 rounded-full bg-emerald-50 text-emerald-600 mx-auto flex items-center justify-center">
              <CheckCircle className="w-8 h-8" />
            </div>

            <div className="space-y-2">
              <h3 className="text-xl font-bold text-navy-900 font-heading">
                Reset Instructions Sent
              </h3>
              <p className="text-sm text-slate-600">
                {successData.message}
              </p>
            </div>

            {successData.reset_token && (
              <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 text-left space-y-3">
                <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500">
                  Development / Testing Reset Token:
                </span>
                <p className="font-mono text-xs break-all text-blue-700 bg-white p-2 rounded border border-slate-200">
                  {successData.reset_token}
                </p>
                <Link
                  to={`${ROUTES.RESET_PASSWORD}?token=${successData.reset_token}`}
                  onClick={handleClose}
                  className="inline-flex items-center text-xs font-semibold text-blue-600 hover:text-blue-800"
                >
                  Proceed Directly to Password Reset <ArrowRight className="ml-1 w-3.5 h-3.5" />
                </Link>
              </div>
            )}

            <button
              type="button"
              onClick={handleClose}
              className="w-full bg-slate-100 hover:bg-slate-200 text-slate-700 font-medium py-2.5 rounded-lg text-sm transition-colors"
            >
              Done
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default ForgotPasswordModal;
