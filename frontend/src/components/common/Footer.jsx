import React from "react";
import { Link } from "react-router-dom";
import { ROUTES } from "../../constants";

export const Footer = () => {
  return (
    <footer className="bg-navy-900 text-slate-400 border-t border-navy-800 mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          <div className="md:col-span-2 space-y-3">
            <span className="text-xl font-extrabold tracking-tight text-white font-heading">
              SKILL<span className="text-emerald-400">2</span>CAREER
            </span>
            <p className="text-sm text-slate-300 max-w-sm">
              Bangladesh Job Preparation Ecosystem. Empowering learners, instructors, and companies with state-of-the-art career preparation and hiring tools.
            </p>
            <p className="text-xs text-emerald-400 font-medium">
              Learn Today, Get Hired Tomorrow.
            </p>
          </div>

          <div>
            <h4 className="text-xs font-bold text-white uppercase tracking-wider mb-3">
              Platform
            </h4>
            <ul className="space-y-2 text-sm">
              <li>
                <Link to={ROUTES.HOME} className="hover:text-emerald-400 transition-colors">
                  Overview
                </Link>
              </li>
              <li>
                <Link to={ROUTES.LOGIN} className="hover:text-emerald-400 transition-colors">
                  Sign In
                </Link>
              </li>
              <li>
                <Link to={ROUTES.REGISTER} className="hover:text-emerald-400 transition-colors">
                  Create Account
                </Link>
              </li>
            </ul>
          </div>

          <div>
            <h4 className="text-xs font-bold text-white uppercase tracking-wider mb-3">
              Ecosystem Roles
            </h4>
            <ul className="space-y-2 text-sm text-slate-400">
              <li>Learners & Job Seekers</li>
              <li>Industry Instructors</li>
              <li>Hiring Companies</li>
              <li>University Admins</li>
            </ul>
          </div>
        </div>

        <div className="border-t border-navy-800 mt-8 pt-8 flex flex-col sm:flex-row justify-between items-center text-xs text-slate-500">
          <p>© {new Date().getFullYear()} SKILL2CAREER. All rights reserved.</p>
          <p className="mt-2 sm:mt-0">University Software Engineering Project · 4 Sprints · 5 Developers</p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
