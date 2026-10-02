import React from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../../hooks/useAuth";
import { ROUTES } from "../../constants";
import Button from "../forms/Button";
import { Briefcase, User as UserIcon, LogOut, LayoutDashboard } from "lucide-react";

export const Navbar = () => {
  const { user, isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate(ROUTES.LOGIN);
  };

  return (
    <header className="sticky top-0 z-40 bg-white border-b border-slate-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo & Brand */}
          <div className="flex items-center space-x-3">
            <Link to={ROUTES.HOME} className="flex items-center space-x-2.5 group">
              <div className="w-10 h-10 rounded-xl bg-navy-900 flex items-center justify-center text-emerald-400 group-hover:bg-emerald-600 group-hover:text-white transition-colors duration-200 shadow-sm">
                <Briefcase className="w-5 h-5" />
              </div>
              <div>
                <span className="text-xl font-extrabold tracking-tight text-navy-900 font-heading">
                  SKILL<span className="text-emerald-500">2</span>CAREER
                </span>
                <span className="hidden sm:block text-[10px] tracking-wider font-semibold text-slate-500 uppercase">
                  Bangladesh Job Ecosystem
                </span>
              </div>
            </Link>
          </div>

          {/* Navigation Links */}
          <nav className="flex items-center space-x-2 sm:space-x-4">
            <Link
              to={ROUTES.HOME}
              className="px-3 py-2 text-sm font-medium text-navy-700 hover:text-emerald-600 transition-colors"
            >
              Home
            </Link>

            {isAuthenticated ? (
              <>
                <Link
                  to={ROUTES.DASHBOARD}
                  className="inline-flex items-center space-x-1.5 px-3 py-2 text-sm font-medium text-navy-700 hover:text-emerald-600 transition-colors"
                >
                  <LayoutDashboard className="w-4 h-4 text-emerald-500" />
                  <span>Dashboard</span>
                </Link>

                <div className="hidden md:flex items-center space-x-2 px-3 py-1 bg-slate-100 rounded-full border border-slate-200 text-xs text-navy-800">
                  <UserIcon className="w-3.5 h-3.5 text-slate-500" />
                  <span className="font-semibold">{user?.first_name}</span>
                  <span className="px-1.5 py-0.5 rounded text-[10px] font-bold uppercase bg-emerald-100 text-emerald-800">
                    {user?.role}
                  </span>
                </div>

                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleLogout}
                  className="flex items-center space-x-1 text-slate-600 hover:text-crimson"
                >
                  <LogOut className="w-4 h-4" />
                  <span className="hidden sm:inline">Logout</span>
                </Button>
              </>
            ) : (
              <div className="flex items-center space-x-2">
                <Link to={ROUTES.LOGIN}>
                  <Button variant="outline" size="sm">
                    Log In
                  </Button>
                </Link>
                <Link to={ROUTES.REGISTER}>
                  <Button variant="primary" size="sm">
                    Get Started
                  </Button>
                </Link>
              </div>
            )}
          </nav>
        </div>
      </div>
    </header>
  );
};

export default Navbar;
