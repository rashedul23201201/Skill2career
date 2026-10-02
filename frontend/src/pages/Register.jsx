import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { ROUTES, USER_ROLES } from "../constants";
import { formatErrorMessage } from "../utils";
import {
  Eye,
  EyeOff,
  AlertCircle,
  CheckCircle,
  ArrowRight,
  Building2,
  Lock,
  Phone,
  Globe,
  MapPin,
} from "lucide-react";

export const Register = () => {
  const { register } = useAuth();
  const navigate = useNavigate();

  // Active Role Tab: LEARNER, INSTRUCTOR, or COMPANY
  const [activeRole, setActiveRole] = useState(USER_ROLES.LEARNER);

  // Common Form Fields
  const [formData, setFormData] = useState({
    // Common
    full_name: "",
    email: "",
    password: "",
    confirm_password: "",
    terms_accepted: false,

    // Learner Specific (Learner reg.png)
    institution: "",
    department: "",
    target_role: "",

    // Instructor Specific (Instructor reg.png)
    qualification: "",
    expertise: "",
    years_experience: "",

    // Company Specific (Company reg.png)
    company_name: "",
    industry: "",
    contact_person: "",
    contact_phone: "",
    website_url: "",
    office_address: "",
  });

  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [registeredData, setRegisteredData] = useState(null);

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

    if (!formData.terms_accepted) {
      setError("Please accept the terms and conditions to proceed.");
      return;
    }

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
      // Split full_name into first_name and last_name
      let first_name = formData.full_name.trim();
      let last_name = "";
      if (activeRole === USER_ROLES.COMPANY) {
        first_name = formData.contact_person.trim() || formData.company_name.trim();
      }
      if (first_name.includes(" ")) {
        const parts = first_name.split(" ");
        first_name = parts[0];
        last_name = parts.slice(1).join(" ");
      }

      const payload = {
        email: formData.email,
        password: formData.password,
        first_name: first_name || "User",
        last_name: last_name || "",
        role: activeRole,
        terms_accepted: true,
      };

      if (activeRole === USER_ROLES.LEARNER) {
        payload.institution = formData.institution;
        payload.department = formData.department;
        payload.target_role = formData.target_role;
      } else if (activeRole === USER_ROLES.INSTRUCTOR) {
        payload.qualification = formData.qualification;
        payload.expertise = formData.expertise;
        payload.years_experience = formData.years_experience;
      } else if (activeRole === USER_ROLES.COMPANY) {
        payload.company_name = formData.company_name;
        payload.industry = formData.industry;
        payload.contact_phone = formData.contact_phone;
        payload.website_url = formData.website_url;
        payload.office_address = formData.office_address;
      }

      const response = await register(payload);
      setRegisteredData(response);
    } catch (err) {
      setError(formatErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  // Header texts per active role
  const getHeaders = () => {
    switch (activeRole) {
      case USER_ROLES.INSTRUCTOR:
        return {
          title: "Create Your Account",
          subtitle: "Join SKILL2CAREER to accelerate your professional journey",
        };
      case USER_ROLES.COMPANY:
        return {
          title: "Company Registration",
          subtitle: "Recruit top talent and post internships/jobs in Bangladesh",
        };
      case USER_ROLES.LEARNER:
      default:
        return {
          title: "Create Your Account",
          subtitle: "Join Bangladesh's job preparation and e-learning platform",
        };
    }
  };

  const { title, subtitle } = getHeaders();

  return (
    <div className="min-h-[calc(100vh-10rem)] py-8 sm:py-12 px-4 sm:px-6 lg:px-8 max-w-3xl mx-auto flex items-center justify-center">
      {/* Registration Card */}
      <div className="w-full bg-white rounded-3xl border border-slate-200 shadow-md p-6 sm:p-10 space-y-6">
        {/* Title & Subtitle */}
        <div className="text-center space-y-2">
          <h1 className="text-3xl sm:text-4xl font-extrabold text-navy-950 font-heading">
            {title}
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 max-w-md mx-auto">
            {subtitle}
          </p>
        </div>

        {/* 3 Role Tabs matching Learner/Instructor/Company reg.png */}
        <div className="grid grid-cols-3 p-1 bg-slate-100/80 rounded-2xl border border-slate-200/60 max-w-md mx-auto">
          {[
            { id: USER_ROLES.LEARNER, label: "Learner" },
            { id: USER_ROLES.INSTRUCTOR, label: "Instructor" },
            { id: USER_ROLES.COMPANY, label: "Company" },
          ].map((tab) => (
            <button
              key={tab.id}
              type="button"
              onClick={() => {
                setActiveRole(tab.id);
                setError("");
              }}
              className={`py-2 text-xs sm:text-sm font-semibold rounded-xl transition-all ${
                activeRole === tab.id
                  ? "bg-white text-navy-950 shadow-sm"
                  : "text-slate-500 hover:text-navy-900"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Error Alert */}
        {error && (
          <div className="flex items-start space-x-2.5 p-3 rounded-xl bg-red-50 border border-red-200 text-red-700 text-xs">
            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
            <span className="flex-1 font-medium">{error}</span>
          </div>
        )}

        {/* Form Container */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* ==================== LEARNER FORM FIELDS ==================== */}
          {activeRole === USER_ROLES.LEARNER && (
            <>
              <div>
                <label className="block text-xs font-semibold text-navy-900 mb-1.5">
                  Full Name <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  name="full_name"
                  value={formData.full_name}
                  onChange={handleChange}
                  placeholder="e.g. Saif Mehedi Sami"
                  required
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-300 text-sm text-navy-950 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 transition-colors"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-navy-900 mb-1.5">
                  Email Address <span className="text-red-500">*</span>
                </label>
                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  placeholder="name@gmail.com"
                  required
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-300 text-sm text-navy-950 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 transition-colors"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-navy-900 mb-1.5">
                    Password <span className="text-red-500">*</span>
                  </label>
                  <div className="relative">
                    <input
                      type={showPassword ? "text" : "password"}
                      name="password"
                      value={formData.password}
                      onChange={handleChange}
                      placeholder="••••••••"
                      required
                      className="w-full px-4 py-2.5 pr-11 rounded-xl border border-slate-300 text-sm text-navy-950 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 transition-colors"
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
                    Confirm Password <span className="text-red-500">*</span>
                  </label>
                  <div className="relative">
                    <input
                      type={showConfirmPassword ? "text" : "password"}
                      name="confirm_password"
                      value={formData.confirm_password}
                      onChange={handleChange}
                      placeholder="••••••••"
                      required
                      className="w-full px-4 py-2.5 pr-11 rounded-xl border border-slate-300 text-sm text-navy-950 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 transition-colors"
                    />
                    <button
                      type="button"
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                      className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-slate-400 hover:text-slate-600"
                    >
                      {showConfirmPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-navy-900 mb-1.5">
                    Institution <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    name="institution"
                    value={formData.institution}
                    onChange={handleChange}
                    placeholder="e.g. UAP / DU / BUET"
                    required
                    className="w-full px-4 py-2.5 rounded-xl border border-slate-300 text-sm text-navy-950 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 transition-colors"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-navy-900 mb-1.5">
                    Department <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    name="department"
                    value={formData.department}
                    onChange={handleChange}
                    placeholder="e.g. Computer Science & Engineering"
                    required
                    className="w-full px-4 py-2.5 rounded-xl border border-slate-300 text-sm text-navy-950 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 transition-colors"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-navy-900 mb-1.5">
                  Target Job / Career Goal <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  name="target_role"
                  value={formData.target_role}
                  onChange={handleChange}
                  placeholder="e.g. Software Engineer, Data Scientist"
                  required
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-300 text-sm text-navy-950 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 transition-colors"
                />
              </div>

              <div className="flex items-center pt-1">
                <input
                  id="terms_learner"
                  name="terms_accepted"
                  type="checkbox"
                  checked={formData.terms_accepted}
                  onChange={handleChange}
                  required
                  className="h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500 cursor-pointer"
                />
                <label htmlFor="terms_learner" className="ml-2 block text-xs text-slate-600 cursor-pointer">
                  I agree to the <span className="text-blue-600 font-medium">Terms & Conditions</span> &{" "}
                  <span className="text-blue-600 font-medium">Privacy Policy</span> of SKILL2CAREER.
                </label>
              </div>
            </>
          )}

          {/* ==================== INSTRUCTOR FORM FIELDS ==================== */}
          {activeRole === USER_ROLES.INSTRUCTOR && (
            <>
              <div>
                <label className="block text-xs font-semibold text-navy-900 mb-1.5">
                  Full Name <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  name="full_name"
                  value={formData.full_name}
                  onChange={handleChange}
                  placeholder="e.g. Mahinul Islam"
                  required
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-300 text-sm text-navy-950 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 transition-colors"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-navy-900 mb-1.5">
                  Email Address <span className="text-red-500">*</span>
                </label>
                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  placeholder="name@gmail.com"
                  required
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-300 text-sm text-navy-950 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 transition-colors"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-navy-900 mb-1.5">
                    Password <span className="text-red-500">*</span>
                  </label>
                  <div className="relative">
                    <input
                      type={showPassword ? "text" : "password"}
                      name="password"
                      value={formData.password}
                      onChange={handleChange}
                      placeholder="••••••••••••"
                      required
                      className="w-full px-4 py-2.5 pr-11 rounded-xl border border-slate-300 text-sm text-navy-950 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 transition-colors"
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
                    Confirm Password <span className="text-red-500">*</span>
                  </label>
                  <div className="relative">
                    <input
                      type={showConfirmPassword ? "text" : "password"}
                      name="confirm_password"
                      value={formData.confirm_password}
                      onChange={handleChange}
                      placeholder="••••••••••••"
                      required
                      className="w-full px-4 py-2.5 pr-11 rounded-xl border border-slate-300 text-sm text-navy-950 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 transition-colors"
                    />
                    <button
                      type="button"
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                      className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-slate-400 hover:text-slate-600"
                    >
                      {showConfirmPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-navy-900 mb-1.5">
                  Qualification <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  name="qualification"
                  value={formData.qualification}
                  onChange={handleChange}
                  placeholder="e.g. B.Sc. in CSE, UAP"
                  required
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-300 text-sm text-navy-950 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 transition-colors"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-navy-900 mb-1.5">
                    Expertise <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    name="expertise"
                    value={formData.expertise}
                    onChange={handleChange}
                    placeholder="e.g. Machine Learning"
                    required
                    className="w-full px-4 py-2.5 rounded-xl border border-slate-300 text-sm text-navy-950 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 transition-colors"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-navy-900 mb-1.5">
                    Experience <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    name="years_experience"
                    value={formData.years_experience}
                    onChange={handleChange}
                    placeholder="e.g. 8+ Years Industry/Academics"
                    required
                    className="w-full px-4 py-2.5 rounded-xl border border-slate-300 text-sm text-navy-950 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 transition-colors"
                  />
                </div>
              </div>

              <div className="flex items-center pt-1">
                <input
                  id="terms_instructor"
                  name="terms_accepted"
                  type="checkbox"
                  checked={formData.terms_accepted}
                  onChange={handleChange}
                  required
                  className="h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500 cursor-pointer"
                />
                <label htmlFor="terms_instructor" className="ml-2 block text-xs text-slate-600 cursor-pointer">
                  I agree to the <span className="text-blue-600 font-medium">Terms & Conditions</span> and{" "}
                  <span className="text-blue-600 font-medium">Privacy Policy</span>
                </label>
              </div>
            </>
          )}

          {/* ==================== COMPANY FORM FIELDS ==================== */}
          {activeRole === USER_ROLES.COMPANY && (
            <>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-navy-900 mb-1.5">
                    Company Name <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    name="company_name"
                    value={formData.company_name}
                    onChange={handleChange}
                    placeholder="e.g. Software Shop Ltd."
                    required
                    className="w-full px-4 py-2.5 rounded-xl border border-slate-300 text-sm text-navy-950 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 transition-colors"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-navy-900 mb-1.5">
                    Industry <span className="text-red-500">*</span>
                  </label>
                  <select
                    name="industry"
                    value={formData.industry}
                    onChange={handleChange}
                    required
                    className="w-full px-4 py-2.5 rounded-xl border border-slate-300 text-sm text-navy-950 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 transition-colors bg-white"
                  >
                    <option value="">Select Industry</option>
                    <option value="Information Technology">Information Technology & Software</option>
                    <option value="Financial Services">Financial Services & Fintech</option>
                    <option value="Telecommunications">Telecommunications</option>
                    <option value="E-Commerce">E-Commerce & Retail</option>
                    <option value="Education">Education & EdTech</option>
                    <option value="Healthcare">Healthcare & BioTech</option>
                    <option value="Manufacturing">Manufacturing & Engineering</option>
                    <option value="Other">Other</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-navy-900 mb-1.5">
                    Contact Person Name <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    name="contact_person"
                    value={formData.contact_person}
                    onChange={handleChange}
                    placeholder="Full Name"
                    required
                    className="w-full px-4 py-2.5 rounded-xl border border-slate-300 text-sm text-navy-950 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 transition-colors"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-navy-900 mb-1.5">
                    Business Email <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="email"
                    name="email"
                    value={formData.email}
                    onChange={handleChange}
                    placeholder="hr@company.com"
                    required
                    className="w-full px-4 py-2.5 rounded-xl border border-slate-300 text-sm text-navy-950 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 transition-colors"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-navy-900 mb-1.5">
                    Password <span className="text-red-500">*</span>
                  </label>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                      <Lock className="w-4 h-4" />
                    </div>
                    <input
                      type={showPassword ? "text" : "password"}
                      name="password"
                      value={formData.password}
                      onChange={handleChange}
                      placeholder="••••••••"
                      required
                      className="w-full pl-10 pr-10 py-2.5 rounded-xl border border-slate-300 text-sm text-navy-950 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 transition-colors"
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
                    Confirm Password <span className="text-red-500">*</span>
                  </label>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                      <Lock className="w-4 h-4" />
                    </div>
                    <input
                      type={showConfirmPassword ? "text" : "password"}
                      name="confirm_password"
                      value={formData.confirm_password}
                      onChange={handleChange}
                      placeholder="••••••••"
                      required
                      className="w-full pl-10 pr-10 py-2.5 rounded-xl border border-slate-300 text-sm text-navy-950 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 transition-colors"
                    />
                    <button
                      type="button"
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                      className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-slate-400 hover:text-slate-600"
                    >
                      {showConfirmPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-navy-900 mb-1.5">
                    Contact Information (Phone) <span className="text-red-500">*</span>
                  </label>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                      <Phone className="w-4 h-4" />
                    </div>
                    <input
                      type="tel"
                      name="contact_phone"
                      value={formData.contact_phone}
                      onChange={handleChange}
                      placeholder="+880 1700 000000"
                      required
                      className="w-full pl-10 py-2.5 rounded-xl border border-slate-300 text-sm text-navy-950 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 transition-colors"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-navy-900 mb-1.5">
                    Website URL
                  </label>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                      <Globe className="w-4 h-4" />
                    </div>
                    <input
                      type="url"
                      name="website_url"
                      value={formData.website_url}
                      onChange={handleChange}
                      placeholder="https://company.com"
                      className="w-full pl-10 py-2.5 rounded-xl border border-slate-300 text-sm text-navy-950 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 transition-colors"
                    />
                  </div>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-navy-900 mb-1.5">
                  Office Address <span className="text-red-500">*</span>
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                    <MapPin className="w-4 h-4" />
                  </div>
                  <input
                    type="text"
                    name="office_address"
                    value={formData.office_address}
                    onChange={handleChange}
                    placeholder="House, Road, Area, Gulshan / Banani, Dhaka, Bangladesh"
                    required
                    className="w-full pl-10 py-2.5 rounded-xl border border-slate-300 text-sm text-navy-950 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 transition-colors"
                  />
                </div>
              </div>

              <div className="flex items-center pt-1">
                <input
                  id="terms_company"
                  name="terms_accepted"
                  type="checkbox"
                  checked={formData.terms_accepted}
                  onChange={handleChange}
                  required
                  className="h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500 cursor-pointer"
                />
                <label htmlFor="terms_company" className="ml-2 block text-xs text-slate-600 cursor-pointer">
                  I agree to the <span className="text-blue-600 font-medium">Terms & Conditions</span> and{" "}
                  <span className="text-blue-600 font-medium">Employer Guidelines</span> set forth by SKILL2CAREER for verified hiring partners.
                </label>
              </div>
            </>
          )}

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-black hover:bg-navy-900 text-white font-medium py-3 rounded-xl text-sm shadow-md transition-all disabled:opacity-60 flex items-center justify-center space-x-2 mt-4"
          >
            {loading ? (
              <span>Creating Account...</span>
            ) : (
              <>
                <span>Create Account</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </form>

        {/* Footer switch to login */}
        <div className="text-center text-xs text-slate-500 pt-2 border-t border-slate-100">
          Already have an account?{" "}
          <Link
            to={ROUTES.LOGIN}
            className="font-bold text-blue-600 hover:text-blue-700 transition-colors"
          >
            Login
          </Link>
        </div>
      </div>

      {/* Registration Success & Verification Modal */}
      {registeredData && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-navy-950/60 backdrop-blur-sm animate-fade-in">
          <div className="relative w-full max-w-lg bg-white rounded-3xl shadow-2xl border border-slate-100 p-8 space-y-6 text-center">
            <div className="w-16 h-16 rounded-full bg-emerald-50 text-emerald-600 mx-auto flex items-center justify-center">
              <CheckCircle className="w-9 h-9" />
            </div>

            <div className="space-y-2">
              <h3 className="text-2xl font-extrabold text-navy-950 font-heading">
                Account Created Successfully!
              </h3>
              <p className="text-sm text-slate-600">
                Welcome to SKILL2CAREER, <span className="font-semibold text-navy-900">{registeredData.user?.first_name}</span>. A verification token has been generated to verify your email.
              </p>
            </div>

            {registeredData.verification_token && (
              <div className="bg-blue-50/70 border border-blue-200/80 rounded-2xl p-4 text-left space-y-2.5">
                <div className="flex items-center space-x-2 text-xs font-bold uppercase tracking-wider text-blue-800">
                  <span>Development Verification Token:</span>
                </div>
                <p className="font-mono text-xs text-blue-900 bg-white p-2.5 rounded-xl border border-blue-200 break-all select-all">
                  {registeredData.verification_token}
                </p>
                <p className="text-[11px] text-blue-700">
                  In live production, an email is sent to your inbox. In this environment, click the button below to verify immediately.
                </p>
              </div>
            )}

            <div className="flex flex-col sm:flex-row gap-3">
              {registeredData.verification_token && (
                <button
                  type="button"
                  onClick={() => navigate(`${ROUTES.VERIFY_EMAIL}?token=${registeredData.verification_token}`)}
                  className="flex-1 bg-emerald-600 hover:bg-emerald-700 text-white font-medium py-3 rounded-xl text-sm transition-colors shadow-sm"
                >
                  Verify Email Now
                </button>
              )}
              <button
                type="button"
                onClick={() => navigate(ROUTES.LOGIN)}
                className="flex-1 bg-black hover:bg-navy-900 text-white font-medium py-3 rounded-xl text-sm transition-colors shadow-sm"
              >
                Proceed to Login
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Register;
