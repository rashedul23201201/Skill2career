import React from "react";
import { Link } from "react-router-dom";
import { ROUTES } from "../constants";
import Button from "../components/forms/Button";
import {
  GraduationCap,
  Briefcase,
  Building2,
  ShieldCheck,
  ArrowRight,
  TrendingUp,
} from "lucide-react";

export const Home = () => {
  return (
    <div className="space-y-16 py-12 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
      {/* Hero Section */}
      <section className="text-center space-y-6 pt-8 pb-12">
        <div className="inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-semibold tracking-wide uppercase">
          <TrendingUp className="w-3.5 h-3.5 text-emerald-600" />
          <span>Bangladesh Job Preparation Ecosystem</span>
        </div>

        <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold text-navy-900 tracking-tight font-heading max-w-4xl mx-auto leading-tight">
          Learn Today, <span className="text-emerald-500">Get Hired</span> Tomorrow
        </h1>

        <p className="text-lg text-slate-600 max-w-2xl mx-auto leading-relaxed">
          The unified career advancement platform bridging the gap between university graduates, technical skill-builders, and top hiring employers across Bangladesh.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
          <Link to={ROUTES.REGISTER}>
            <Button variant="primary" size="lg" className="w-full sm:w-auto shadow-md">
              Create Free Account <ArrowRight className="ml-2 w-4 h-4" />
            </Button>
          </Link>
          <Link to={ROUTES.LOGIN}>
            <Button variant="outline" size="lg" className="w-full sm:w-auto">
              Sign In to Portal
            </Button>
          </Link>
        </div>
      </section>

      {/* Ecosystem Roles Architecture Grid */}
      <section className="space-y-8">
        <div className="text-center space-y-2">
          <h2 className="text-2xl sm:text-3xl font-bold text-navy-900 font-heading">
            Tailored For Every Career Stakeholder
          </h2>
          <p className="text-slate-500 text-sm max-w-xl mx-auto">
            Engineered with dedicated role-based access for each participant in Bangladesh's employment ecosystem.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {/* Learner Card */}
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition-shadow">
            <div className="w-12 h-12 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center mb-4">
              <GraduationCap className="w-6 h-6" />
            </div>
            <span className="text-[11px] font-bold uppercase tracking-wider text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded">
              Role: LEARNER
            </span>
            <h3 className="text-lg font-bold text-navy-900 mt-2 mb-2 font-heading">
              Graduates & Job Seekers
            </h3>
            <p className="text-sm text-slate-600 leading-normal">
              Acquire verified skills, complete curated assessments, track career milestones, and match with verified companies.
            </p>
          </div>

          {/* Instructor Card */}
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition-shadow">
            <div className="w-12 h-12 rounded-xl bg-navy-50 text-navy-900 flex items-center justify-center mb-4">
              <Briefcase className="w-6 h-6" />
            </div>
            <span className="text-[11px] font-bold uppercase tracking-wider text-navy-700 bg-navy-100 px-2 py-0.5 rounded">
              Role: INSTRUCTOR
            </span>
            <h3 className="text-lg font-bold text-navy-900 mt-2 mb-2 font-heading">
              Domain Experts & Mentors
            </h3>
            <p className="text-sm text-slate-600 leading-normal">
              Publish job-oriented courses, design mock interview rubrics, and guide the next generation of engineers and analysts.
            </p>
          </div>

          {/* Company Card */}
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition-shadow">
            <div className="w-12 h-12 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center mb-4">
              <Building2 className="w-6 h-6" />
            </div>
            <span className="text-[11px] font-bold uppercase tracking-wider text-amber-700 bg-amber-100 px-2 py-0.5 rounded">
              Role: COMPANY
            </span>
            <h3 className="text-lg font-bold text-navy-900 mt-2 mb-2 font-heading">
              Recruiters & Enterprises
            </h3>
            <p className="text-sm text-slate-600 leading-normal">
              Post verified openings, filter candidates by pre-tested technical proficiencies, and streamline university recruitment.
            </p>
          </div>

          {/* Admin Card */}
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition-shadow">
            <div className="w-12 h-12 rounded-xl bg-slate-100 text-slate-700 flex items-center justify-center mb-4">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <span className="text-[11px] font-bold uppercase tracking-wider text-slate-700 bg-slate-200 px-2 py-0.5 rounded">
              Role: ADMIN
            </span>
            <h3 className="text-lg font-bold text-navy-900 mt-2 mb-2 font-heading">
              System Administrators
            </h3>
            <p className="text-sm text-slate-600 leading-normal">
              Monitor ecosystem integrity, audit company verifications, enforce standards, and maintain platform security.
            </p>
          </div>
        </div>
      </section>

    </div>
  );
};

export default Home;
