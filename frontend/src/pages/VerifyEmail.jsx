import React, { useState, useEffect, useCallback } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { authService } from "../services/authService";
import { ROUTES } from "../constants";
import { formatErrorMessage } from "../utils";
import { CheckCircle2, AlertCircle, Mail, ArrowRight } from "lucide-react";

export const VerifyEmail = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const tokenFromUrl = searchParams.get("token") || "";

  const [token, setToken] = useState(tokenFromUrl);
  const [loading, setLoading] = useState(false);
  const [verified, setVerified] = useState(false);
  const [error, setError] = useState("");

  const handleVerify = useCallback(async (tokenToVerify) => {
    if (!tokenToVerify) return;
    setLoading(true);
    setError("");

    try {
      await authService.verifyEmail(tokenToVerify);
      setVerified(true);
    } catch (err) {
      setError(formatErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (tokenFromUrl) {
      handleVerify(tokenFromUrl);
    }
  }, [tokenFromUrl, handleVerify]);

  return (
    <div className="min-h-[calc(100vh-12rem)] flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full bg-white rounded-3xl border border-slate-200 shadow-md p-6 sm:p-10 space-y-6 text-center">
        {!verified ? (
          <>
            <div className="w-14 h-14 rounded-2xl bg-blue-50 text-blue-600 mx-auto flex items-center justify-center mb-3">
              <Mail className="w-7 h-7" />
            </div>

            <div className="space-y-1.5">
              <h2 className="text-2xl font-extrabold text-navy-950 font-heading">
                Email Verification
              </h2>
              <p className="text-xs sm:text-sm text-slate-500">
                Confirming your email address unlocks full platform capabilities.
              </p>
            </div>

            {error && (
              <div className="flex items-start space-x-2.5 p-3 rounded-xl bg-red-50 border border-red-200 text-red-700 text-xs text-left">
                <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                <span className="flex-1 font-medium">{error}</span>
              </div>
            )}

            {!tokenFromUrl && (
              <div className="space-y-4 text-left">
                <div>
                  <label className="block text-xs font-semibold text-navy-900 mb-1.5">
                    Verification Token
                  </label>
                  <input
                    type="text"
                    value={token}
                    onChange={(e) => setToken(e.target.value)}
                    placeholder="Paste your email verification token"
                    className="w-full px-4 py-2.5 rounded-xl border border-slate-300 text-sm font-mono text-navy-950 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 transition-colors"
                  />
                </div>
                <button
                  type="button"
                  onClick={() => handleVerify(token)}
                  disabled={loading || !token.trim()}
                  className="w-full bg-black hover:bg-navy-900 text-white font-medium py-3 rounded-xl text-sm shadow-md transition-all disabled:opacity-50"
                >
                  {loading ? "Verifying..." : "Verify Token"}
                </button>
              </div>
            )}

            {tokenFromUrl && loading && (
              <div className="py-6 flex flex-col items-center space-y-3">
                <div className="w-8 h-8 border-3 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
                <p className="text-xs font-medium text-slate-500">Validating your verification token...</p>
              </div>
            )}

            <div className="pt-2">
              <Link to={ROUTES.LOGIN} className="text-xs font-semibold text-slate-500 hover:text-navy-950">
                Back to Sign In
              </Link>
            </div>
          </>
        ) : (
          <div className="space-y-6 py-2">
            <div className="w-16 h-16 rounded-full bg-emerald-50 text-emerald-600 mx-auto flex items-center justify-center">
              <CheckCircle2 className="w-10 h-10" />
            </div>

            <div className="space-y-2">
              <h3 className="text-2xl font-extrabold text-navy-950 font-heading">
                Email Verified!
              </h3>
              <p className="text-sm text-slate-600">
                Your email address has been successfully verified. You now have full access to your personalized portal.
              </p>
            </div>

            <div className="space-y-2">
              <button
                type="button"
                onClick={() => navigate(ROUTES.DASHBOARD)}
                className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-medium py-3 rounded-xl text-sm shadow-sm transition-colors flex items-center justify-center space-x-1.5"
              >
                <span>Go to Dashboard</span>
                <ArrowRight className="w-4 h-4" />
              </button>
              <button
                type="button"
                onClick={() => navigate(ROUTES.LOGIN)}
                className="w-full bg-slate-100 hover:bg-slate-200 text-slate-700 font-medium py-2.5 rounded-xl text-sm transition-colors"
              >
                Sign In
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default VerifyEmail;
