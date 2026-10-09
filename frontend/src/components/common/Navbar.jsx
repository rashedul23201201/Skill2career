import React, { useState, useRef, useEffect } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../../hooks/useAuth";
import { ROUTES, USER_ROLES } from "../../constants";
import {
  LogOut,
  LayoutDashboard,
  User as UserIcon,
  Shield,
  Building2,
  GraduationCap,
  ChevronDown,
  Menu,
  X,
  BookOpen,
  Briefcase,
  MessageSquare,
  Award,
  FileText,
  Sparkles,
  PlusCircle,
  Users,
} from "lucide-react";

export const Navbar = () => {
  const { user, isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [isProfileOpen, setIsProfileOpen] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const profileDropdownRef = useRef(null);

  // Close profile dropdown on click outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (
        profileDropdownRef.current &&
        !profileDropdownRef.current.contains(event.target)
      ) {
        setIsProfileOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  // Close menus on navigation
  useEffect(() => {
    setIsProfileOpen(false);
    setIsMobileMenuOpen(false);
  }, [location.pathname]);

  const handleLogout = () => {
    logout();
    setIsProfileOpen(false);
    setIsMobileMenuOpen(false);
    navigate(ROUTES.LOGIN);
  };

  // Get Primary Navigation Links (Clean, core discovery destinations)
  const getNavLinks = () => {
    if (!isAuthenticated || !user) {
      return [
        { name: "Courses", path: ROUTES.COURSES, icon: BookOpen },
        { name: "Mock Tests", path: ROUTES.MOCK_TESTS, icon: Award },
        { name: "Jobs & Internships", path: ROUTES.JOBS, icon: Briefcase },
        { name: "Forum", path: ROUTES.FORUM, icon: MessageSquare },
      ];
    }

    switch (user.role) {
      case USER_ROLES.ADMIN:
        return [
          { name: "Courses", path: ROUTES.COURSES, icon: BookOpen },
          { name: "Jobs", path: ROUTES.JOBS, icon: Briefcase },
          { name: "Forum", path: ROUTES.FORUM, icon: MessageSquare },
          { name: "Verifications", path: ROUTES.ADMIN_VERIFICATIONS, icon: Shield },
          { name: "User Management", path: ROUTES.ADMIN_USERS, icon: Users },
        ];
      case USER_ROLES.INSTRUCTOR:
        return [
          { name: "Courses", path: ROUTES.COURSES, icon: BookOpen },
          { name: "Assessments", path: ROUTES.MOCK_TESTS, icon: Award },
          { name: "Forum", path: ROUTES.FORUM, icon: MessageSquare },
        ];
      case USER_ROLES.COMPANY:
        return [
          { name: "Jobs & Internships", path: ROUTES.JOBS, icon: Briefcase },
          { name: "Forum", path: ROUTES.FORUM, icon: MessageSquare },
        ];
      case USER_ROLES.LEARNER:
      default:
        return [
          { name: "Courses", path: ROUTES.COURSES, icon: BookOpen },
          { name: "Mock Tests", path: ROUTES.MOCK_TESTS, icon: Award },
          { name: "Jobs & Internships", path: ROUTES.JOBS, icon: Briefcase },
          { name: "Forum", path: ROUTES.FORUM, icon: MessageSquare },
        ];
    }
  };

  const navLinks = getNavLinks();

  // Role badge configuration
  const getRoleBadgeConfig = (role) => {
    switch (role) {
      case USER_ROLES.ADMIN:
        return {
          label: "Admin",
          bg: "bg-purple-50 text-purple-700 border-purple-200/80",
          dot: "bg-purple-500",
        };
      case USER_ROLES.INSTRUCTOR:
        return {
          label: "Instructor",
          bg: "bg-blue-50 text-blue-700 border-blue-200/80",
          dot: "bg-blue-500",
        };
      case USER_ROLES.COMPANY:
        return {
          label: "Recruiter",
          bg: "bg-amber-50 text-amber-700 border-amber-200/80",
          dot: "bg-amber-500",
        };
      case USER_ROLES.LEARNER:
      default:
        return {
          label: "Learner",
          bg: "bg-emerald-50 text-emerald-700 border-emerald-200/80",
          dot: "bg-emerald-500",
        };
    }
  };

  // Quick Action Button next to profile
  const renderQuickActionBtn = () => {
    if (!isAuthenticated || !user) return null;

    if (user.role === USER_ROLES.ADMIN) {
      return (
        <Link
          to={ROUTES.ADMIN_DASHBOARD}
          className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-purple-50 hover:bg-purple-100 text-purple-700 border border-purple-200 transition-colors shadow-2xs"
        >
          <Shield className="w-3.5 h-3.5" />
          <span>Admin Console</span>
        </Link>
      );
    }

    if (user.role === USER_ROLES.COMPANY) {
      return (
        <Link
          to={ROUTES.COMPANY_DASHBOARD}
          className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-900 hover:bg-slate-800 text-white transition-all shadow-sm"
        >
          <Building2 className="w-3.5 h-3.5 text-blue-400" />
          <span>Company Portal</span>
        </Link>
      );
    }

    if (user.role === USER_ROLES.INSTRUCTOR) {
      return (
        <Link
          to={ROUTES.INSTRUCTOR_DASHBOARD}
          className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-blue-600 hover:bg-blue-700 text-white transition-all shadow-sm"
        >
          <GraduationCap className="w-3.5 h-3.5" />
          <span>Instructor Hub</span>
        </Link>
      );
    }

    // Default Learner Quick Action
    return (
      <Link
        to={ROUTES.DASHBOARD}
        className="hidden sm:inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-blue-50/90 hover:bg-blue-100 text-blue-700 border border-blue-200/70 transition-colors shadow-2xs"
      >
        <LayoutDashboard className="w-3.5 h-3.5 text-blue-600" />
        <span>Dashboard</span>
      </Link>
    );
  };

  // Profile avatar initial & initials background
  const userInitial =
    user?.first_name?.charAt(0)?.toUpperCase() ||
    user?.email?.charAt(0)?.toUpperCase() ||
    "U";
  const userFullName =
    [user?.first_name, user?.last_name].filter(Boolean).join(" ") ||
    user?.email?.split("@")[0] ||
    "Account";

  const roleBadge = getRoleBadgeConfig(user?.role);

  return (
    <header className="sticky top-0 z-40 bg-white/90 backdrop-blur-md border-b border-slate-200/80 shadow-[0_1px_3px_0_rgba(15,23,42,0.03)] transition-all">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16 md:h-18">
          {/* Left: Brand Logo */}
          <div className="flex items-center shrink-0 mr-4 lg:mr-8">
            <Link
              to={ROUTES.HOME}
              className="flex items-center space-x-2.5 group focus:outline-none focus:ring-2 focus:ring-blue-500/20 rounded-lg p-0.5"
            >
              <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-navy-900 to-navy-950 flex items-center justify-center text-blue-400 font-black text-sm shadow-sm group-hover:scale-105 group-hover:from-blue-600 group-hover:to-indigo-600 group-hover:text-white transition-all duration-200">
                <span className="font-heading tracking-tight">A*</span>
              </div>
              <span className="text-xl font-extrabold tracking-tight text-navy-950 font-heading">
                SKILL<span className="text-blue-600">2</span>CAREER
              </span>
            </Link>
          </div>

          {/* Center: Desktop Navigation Links */}
          <nav className="hidden lg:flex items-center space-x-1 xl:space-x-2">
            {navLinks.map((link) => {
              const isActive =
                location.pathname === link.path ||
                (link.path !== "/" && location.pathname.startsWith(link.path));
              return (
                <Link
                  key={link.name}
                  to={link.path}
                  className={`px-3 py-2 rounded-lg text-sm font-medium transition-all duration-150 inline-flex items-center gap-1.5 ${
                    isActive
                      ? "bg-blue-50/80 text-blue-700 font-semibold shadow-xs"
                      : "text-slate-600 hover:text-navy-950 hover:bg-slate-100/70"
                  }`}
                >
                  <span>{link.name}</span>
                </Link>
              );
            })}
          </nav>

          {/* Right: Actions & User Controls */}
          <div className="flex items-center space-x-3 sm:space-x-4">
            {isAuthenticated ? (
              <div className="flex items-center space-x-2.5 sm:space-x-3">
                {/* Role-Specific Quick CTA */}
                {renderQuickActionBtn()}

                {/* Profile Dropdown Menu Trigger */}
                <div className="relative" ref={profileDropdownRef}>
                  <button
                    type="button"
                    onClick={() => setIsProfileOpen((prev) => !prev)}
                    className={`flex items-center gap-2 p-1 sm:px-2 sm:py-1.5 rounded-xl border transition-all text-left focus:outline-none focus:ring-2 focus:ring-blue-500/20 ${
                      isProfileOpen
                        ? "border-blue-300 bg-blue-50/50 shadow-xs"
                        : "border-slate-200/90 hover:border-slate-300 bg-white hover:bg-slate-50"
                    }`}
                    aria-expanded={isProfileOpen}
                    aria-haspopup="true"
                  >
                    {/* User Avatar */}
                    <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-blue-600 to-indigo-600 text-white flex items-center justify-center text-xs font-bold shadow-xs shrink-0">
                      {userInitial}
                    </div>

                    {/* Name & Role preview (hidden on tiny screens) */}
                    <div className="hidden md:flex flex-col text-left pr-1 max-w-[130px]">
                      <span className="text-xs font-semibold text-navy-900 truncate leading-tight">
                        {userFullName}
                      </span>
                      <span className="text-[10px] font-medium text-slate-500 capitalize">
                        {roleBadge.label}
                      </span>
                    </div>

                    <ChevronDown
                      className={`w-3.5 h-3.5 text-slate-400 transition-transform duration-200 ${
                        isProfileOpen ? "rotate-180 text-blue-600" : ""
                      }`}
                    />
                  </button>

                  {/* Profile Dropdown Card */}
                  {isProfileOpen && (
                    <div className="absolute right-0 mt-2 w-64 bg-white rounded-2xl shadow-xl border border-slate-100 py-1.5 z-50 animate-in fade-in slide-in-from-top-2 duration-150 divide-y divide-slate-100">
                      {/* User Header */}
                      <div className="px-4 py-3">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 text-white flex items-center justify-center text-sm font-bold shadow-xs">
                            {userInitial}
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-semibold text-navy-950 truncate">
                              {userFullName}
                            </p>
                            <p className="text-xs text-slate-500 truncate mb-1">
                              {user?.email}
                            </p>
                            <span
                              className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold border ${roleBadge.bg}`}
                            >
                              <span
                                className={`w-1.5 h-1.5 rounded-full ${roleBadge.dot}`}
                              />
                              {user?.role}
                            </span>
                          </div>
                        </div>
                      </div>

                      {/* Dropdown Navigation Links */}
                      <div className="py-1 px-1">
                        <Link
                          to={ROUTES.DASHBOARD}
                          className="flex items-center gap-2.5 px-3 py-2 text-xs font-medium text-slate-700 hover:text-blue-600 hover:bg-slate-50 rounded-lg transition-colors"
                        >
                          <LayoutDashboard className="w-4 h-4 text-slate-400 group-hover:text-blue-600" />
                          <span>My Dashboard</span>
                        </Link>

                        {user?.role === USER_ROLES.LEARNER && (
                          <>
                            <Link
                              to={ROUTES.LEARNER_PROFILE}
                              className="flex items-center gap-2.5 px-3 py-2 text-xs font-medium text-slate-700 hover:text-blue-600 hover:bg-slate-50 rounded-lg transition-colors"
                            >
                              <UserIcon className="w-4 h-4 text-slate-400" />
                              <span>Learner Profile</span>
                            </Link>
                            <Link
                              to={ROUTES.LEARNER_APPLICATIONS}
                              className="flex items-center gap-2.5 px-3 py-2 text-xs font-medium text-slate-700 hover:text-blue-600 hover:bg-slate-50 rounded-lg transition-colors"
                            >
                              <FileText className="w-4 h-4 text-slate-400" />
                              <span>My Applications</span>
                            </Link>
                            <Link
                              to={ROUTES.INSTRUCTOR_APPLY}
                              className="flex items-center gap-2.5 px-3 py-2 text-xs font-medium text-emerald-700 hover:bg-emerald-50 rounded-lg transition-colors"
                            >
                              <Sparkles className="w-4 h-4 text-emerald-600" />
                              <span>Teach on Skill2Career</span>
                            </Link>
                          </>
                        )}

                        {user?.role === USER_ROLES.INSTRUCTOR && (
                          <>
                            <Link
                              to={ROUTES.INSTRUCTOR_DASHBOARD}
                              className="flex items-center gap-2.5 px-3 py-2 text-xs font-medium text-slate-700 hover:text-blue-600 hover:bg-slate-50 rounded-lg transition-colors"
                            >
                              <GraduationCap className="w-4 h-4 text-slate-400" />
                              <span>Instructor Dashboard</span>
                            </Link>
                            <Link
                              to={ROUTES.COURSE_NEW}
                              className="flex items-center gap-2.5 px-3 py-2 text-xs font-medium text-slate-700 hover:text-blue-600 hover:bg-slate-50 rounded-lg transition-colors"
                            >
                              <PlusCircle className="w-4 h-4 text-slate-400" />
                              <span>Create New Course</span>
                            </Link>
                          </>
                        )}

                        {user?.role === USER_ROLES.COMPANY && (
                          <>
                            <Link
                              to={ROUTES.COMPANY_DASHBOARD}
                              className="flex items-center gap-2.5 px-3 py-2 text-xs font-medium text-slate-700 hover:text-blue-600 hover:bg-slate-50 rounded-lg transition-colors"
                            >
                              <Building2 className="w-4 h-4 text-slate-400" />
                              <span>Company Workspace</span>
                            </Link>
                            <Link
                              to={ROUTES.JOB_NEW}
                              className="flex items-center gap-2.5 px-3 py-2 text-xs font-medium text-slate-700 hover:text-blue-600 hover:bg-slate-50 rounded-lg transition-colors"
                            >
                              <PlusCircle className="w-4 h-4 text-slate-400" />
                              <span>Post a Job Opening</span>
                            </Link>
                            <Link
                              to={ROUTES.COMPANY_VERIFICATION}
                              className="flex items-center gap-2.5 px-3 py-2 text-xs font-medium text-slate-700 hover:text-blue-600 hover:bg-slate-50 rounded-lg transition-colors"
                            >
                              <Shield className="w-4 h-4 text-slate-400" />
                              <span>Verification Dossier</span>
                            </Link>
                          </>
                        )}

                        {user?.role === USER_ROLES.ADMIN && (
                          <>
                            <Link
                              to={ROUTES.ADMIN_DASHBOARD}
                              className="flex items-center gap-2.5 px-3 py-2 text-xs font-medium text-slate-700 hover:text-purple-600 hover:bg-purple-50 rounded-lg transition-colors"
                            >
                              <Shield className="w-4 h-4 text-purple-500" />
                              <span>Admin Console</span>
                            </Link>
                            <Link
                              to={ROUTES.ADMIN_VERIFICATIONS}
                              className="flex items-center gap-2.5 px-3 py-2 text-xs font-medium text-slate-700 hover:text-purple-600 hover:bg-purple-50 rounded-lg transition-colors"
                            >
                              <Building2 className="w-4 h-4 text-purple-500" />
                              <span>Review Verifications</span>
                            </Link>
                            <Link
                              to={ROUTES.ADMIN_USERS}
                              className="flex items-center gap-2.5 px-3 py-2 text-xs font-medium text-slate-700 hover:text-purple-600 hover:bg-purple-50 rounded-lg transition-colors"
                            >
                              <Users className="w-4 h-4 text-purple-500" />
                              <span>Manage Users</span>
                            </Link>
                          </>
                        )}
                      </div>

                      {/* Logout Action */}
                      <div className="py-1 px-1">
                        <button
                          type="button"
                          onClick={handleLogout}
                          className="w-full flex items-center gap-2.5 px-3 py-2 text-xs font-medium text-rose-600 hover:bg-rose-50 rounded-lg transition-colors text-left"
                        >
                          <LogOut className="w-4 h-4 text-rose-500" />
                          <span>Sign Out</span>
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              /* Unauthenticated Auth Buttons */
              <div className="flex items-center space-x-2.5">
                <Link
                  to={ROUTES.LOGIN}
                  className="text-sm font-semibold text-slate-700 hover:text-blue-600 px-3.5 py-2 rounded-lg hover:bg-slate-100/70 transition-colors"
                >
                  Sign In
                </Link>
                <Link
                  to={ROUTES.REGISTER}
                  className="inline-flex items-center justify-center bg-slate-900 hover:bg-blue-600 text-white text-sm font-semibold px-4 py-2 rounded-xl shadow-xs hover:shadow-md transition-all active:scale-[0.98]"
                >
                  Create Account
                </Link>
              </div>
            )}

            {/* Mobile Hamburger Button */}
            <div className="lg:hidden flex items-center">
              <button
                type="button"
                onClick={() => setIsMobileMenuOpen((prev) => !prev)}
                className="p-2 rounded-xl text-slate-600 hover:text-navy-950 hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                aria-label="Toggle navigation menu"
              >
                {isMobileMenuOpen ? (
                  <X className="w-6 h-6" />
                ) : (
                  <Menu className="w-6 h-6" />
                )}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Mobile Navigation Drawer */}
      {isMobileMenuOpen && (
        <div className="lg:hidden border-t border-slate-200/80 bg-white/95 backdrop-blur-lg px-4 pt-3 pb-6 space-y-3 shadow-xl">
          {/* Mobile Nav Links */}
          <div className="space-y-1">
            <Link
              to={ROUTES.HOME}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium ${
                location.pathname === ROUTES.HOME
                  ? "bg-blue-50 text-blue-700 font-semibold"
                  : "text-slate-700 hover:bg-slate-50"
              }`}
            >
              <Sparkles className="w-4 h-4 text-blue-500" />
              <span>Home</span>
            </Link>

            {navLinks.map((link) => {
              const Icon = link.icon;
              const isActive =
                location.pathname === link.path ||
                (link.path !== "/" && location.pathname.startsWith(link.path));
              return (
                <Link
                  key={link.name}
                  to={link.path}
                  className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium ${
                    isActive
                      ? "bg-blue-50 text-blue-700 font-semibold"
                      : "text-slate-700 hover:bg-slate-50"
                  }`}
                >
                  {Icon && <Icon className="w-4 h-4 text-slate-500" />}
                  <span>{link.name}</span>
                </Link>
              );
            })}
          </div>

          {/* Mobile User Section */}
          {isAuthenticated ? (
            <div className="pt-3 border-t border-slate-100 space-y-2">
              <div className="px-3 py-2 bg-slate-50 rounded-xl flex items-center justify-between">
                <div>
                  <p className="text-sm font-semibold text-navy-950">
                    {userFullName}
                  </p>
                  <p className="text-xs text-slate-500">{user?.email}</p>
                </div>
                <span
                  className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${roleBadge.bg}`}
                >
                  {user?.role}
                </span>
              </div>

              <div className="grid grid-cols-2 gap-2 pt-1">
                <Link
                  to={ROUTES.DASHBOARD}
                  className="flex items-center justify-center gap-1.5 py-2 px-3 rounded-lg text-xs font-semibold bg-blue-50 text-blue-700"
                >
                  <LayoutDashboard className="w-3.5 h-3.5" />
                  <span>Dashboard</span>
                </Link>

                {user?.role === USER_ROLES.LEARNER && (
                  <Link
                    to={ROUTES.LEARNER_PROFILE}
                    className="flex items-center justify-center gap-1.5 py-2 px-3 rounded-lg text-xs font-semibold bg-emerald-50 text-emerald-800"
                  >
                    <UserIcon className="w-3.5 h-3.5" />
                    <span>My Profile</span>
                  </Link>
                )}

                {user?.role === USER_ROLES.COMPANY && (
                  <Link
                    to={ROUTES.COMPANY_DASHBOARD}
                    className="flex items-center justify-center gap-1.5 py-2 px-3 rounded-lg text-xs font-semibold bg-amber-50 text-amber-800"
                  >
                    <Building2 className="w-3.5 h-3.5" />
                    <span>Company Hub</span>
                  </Link>
                )}

                {user?.role === USER_ROLES.INSTRUCTOR && (
                  <Link
                    to={ROUTES.INSTRUCTOR_DASHBOARD}
                    className="flex items-center justify-center gap-1.5 py-2 px-3 rounded-lg text-xs font-semibold bg-blue-50 text-blue-800"
                  >
                    <GraduationCap className="w-3.5 h-3.5" />
                    <span>Instructor Hub</span>
                  </Link>
                )}

                {user?.role === USER_ROLES.ADMIN && (
                  <Link
                    to={ROUTES.ADMIN_DASHBOARD}
                    className="flex items-center justify-center gap-1.5 py-2 px-3 rounded-lg text-xs font-semibold bg-purple-50 text-purple-800"
                  >
                    <Shield className="w-3.5 h-3.5" />
                    <span>Admin Panel</span>
                  </Link>
                )}

                <button
                  type="button"
                  onClick={handleLogout}
                  className="flex items-center justify-center gap-1.5 py-2 px-3 rounded-lg text-xs font-semibold bg-rose-50 text-rose-700"
                >
                  <LogOut className="w-3.5 h-3.5" />
                  <span>Sign Out</span>
                </button>
              </div>
            </div>
          ) : (
            <div className="pt-3 border-t border-slate-100 grid grid-cols-2 gap-2">
              <Link
                to={ROUTES.LOGIN}
                className="py-2.5 text-center text-sm font-semibold text-slate-700 bg-slate-100 rounded-xl"
              >
                Sign In
              </Link>
              <Link
                to={ROUTES.REGISTER}
                className="py-2.5 text-center text-sm font-semibold text-white bg-slate-900 rounded-xl"
              >
                Create Account
              </Link>
            </div>
          )}
        </div>
      )}
    </header>
  );
};

export default Navbar;
