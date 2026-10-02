import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { ROUTES, USER_ROLES } from "../constants";
import { formatErrorMessage } from "../utils";
import Input from "../components/forms/Input";
import Button from "../components/forms/Button";
import { Mail, Lock, User, AlertCircle, CheckCircle, ArrowRight } from "lucide-react";

export const Register = () => {
  const { register, login } = useAuth();
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    first_name: "",
    last_name: "",
    email: "",
    role: USER_ROLES.LEARNER,
    password: "",
    confirm_password: "",
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    if (error) setError("");
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (formData.password.length < 8) {
      setError("Password must be at least 8 characters long.");
      return;
    }

    if (formData.password !== formData.confirm_password) {
      setError("Passwords do not match. Please verify.");
      return;
    }

    setLoading(true);

    try {
      // 1. Call registration endpoint
      await register({
        first_name: formData.first_name,
        last_name: formData.last_name,
        email: formData.email,
        role: formData.role,
        password: formData.password,
      });

      // 2. Automatically log the user in
      await login(formData.email, formData.password);
      navigate(ROUTES.DASHBOARD, { replace: true });
    } catch (err) {
      setError(formatErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[calc(100vh-16rem)] flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-lg w-full space-y-8 bg-white p-8 rounded-2xl border border-slate-200 shadow-sm">
        <div className="text-center space-y-2">
          <span className="text-xs font-bold uppercase tracking-wider text-emerald-600 bg-emerald-50 px-2.5 py-1 rounded-full">
            Join the Ecosystem
          </span>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-navy-900 font-heading">
            Create Your Account
          </h2>
          <p className="text-sm text-slate-500">
            Start your professional journey with SKILL2CAREER
          </p>
        </div>

        {error && (
          <div className="flex items-start space-x-2.5 p-3.5 rounded-lg bg-crimson-50 border border-red-200 text-crimson text-sm">
            <AlertCircle className="w-5 h-5 shrink-0 mt-0.5 text-crimson" />
            <div className="flex-1 font-medium">{error}</div>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="First Name"
              id="first_name"
              name="first_name"
              value={formData.first_name}
              onChange={handleChange}
              placeholder="e.g. Rahim"
              required
              icon={User}
            />

            <Input
              label="Last Name"
              id="last_name"
              name="last_name"
              value={formData.last_name}
              onChange={handleChange}
              placeholder="e.g. Uddin"
              required
              icon={User}
            />
          </div>

          <Input
            label="Email Address"
            id="email"
            name="email"
            type="email"
            value={formData.email}
            onChange={handleChange}
            placeholder="e.g. rahim.uddin@example.com"
            required
            icon={Mail}
            autoComplete="email"
          />

          {/* Role Selection */}
          <div>
            <label className="block text-sm font-medium text-navy-800 mb-1.5">
              Select Your Role <span className="text-crimson">*</span>
            </label>
            <div className="grid grid-cols-3 gap-2.5">
              {[
                { id: USER_ROLES.LEARNER, label: "Learner / Job Seeker" },
                { id: USER_ROLES.INSTRUCTOR, label: "Instructor / Mentor" },
                { id: USER_ROLES.COMPANY, label: "Hiring Company" },
              ].map((roleOption) => (
                <label
                  key={roleOption.id}
                  className={`flex flex-col items-center justify-center p-3 rounded-xl border text-center cursor-pointer transition-all ${
                    formData.role === roleOption.id
                      ? "border-emerald-500 bg-emerald-50/50 text-navy-900 ring-2 ring-emerald-200"
                      : "border-slate-200 hover:border-slate-300 text-slate-600 bg-white"
                  }`}
                >
                  <input
                    type="radio"
                    name="role"
                    value={roleOption.id}
                    checked={formData.role === roleOption.id}
                    onChange={handleChange}
                    className="sr-only"
                  />
                  <span className="text-xs font-semibold">{roleOption.label}</span>
                </label>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="Password"
              id="password"
              name="password"
              type="password"
              value={formData.password}
              onChange={handleChange}
              placeholder="Min. 8 characters"
              required
              icon={Lock}
              autoComplete="new-password"
            />

            <Input
              label="Confirm Password"
              id="confirm_password"
              name="confirm_password"
              type="password"
              value={formData.confirm_password}
              onChange={handleChange}
              placeholder="Re-enter password"
              required
              icon={Lock}
              autoComplete="new-password"
            />
          </div>

          <Button
            type="submit"
            variant="primary"
            size="md"
            loading={loading}
            className="w-full shadow-sm text-base py-3 mt-2"
          >
            Create Account <ArrowRight className="ml-2 w-4 h-4" />
          </Button>
        </form>

        <div className="text-center text-sm text-slate-600 pt-2 border-t border-slate-100">
          Already registered?{" "}
          <Link
            to={ROUTES.LOGIN}
            className="font-semibold text-emerald-600 hover:text-emerald-700 transition-colors"
          >
            Sign in
          </Link>
        </div>
      </div>
    </div>
  );
};

export default Register;
