import React from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../../hooks/useAuth";
import { ROUTES, USER_ROLES } from "../../constants";
import { LogOut, LayoutDashboard, User as UserIcon, Shield } from "lucide-react";

export const Navbar = () => {
  const { user, isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    logout();
    navigate(ROUTES.LOGIN);
  };

  // Dynamic role-specific navigation menu items (SKL-50)
  const getNavLinks = () => {
    if (!isAuthenticated || !user) {
      return [
        { name: "Home", path: ROUTES.HOME },
        { name: "Courses", path: ROUTES.COURSES },
        { name: "Jobs & Internships", path: ROUTES.JOBS },
        { name: "Forum", path: ROUTES.FORUM },
        { name: "Mock Tests", path: ROUTES.MOCK_TESTS },
      ];
    }

    switch (user.role) {
      case USER_ROLES.ADMIN:
        return [
          { name: "Admin Dashboard", path: ROUTES.ADMIN_DASHBOARD },
          { name: "User Management", path: ROUTES.ADMIN_USERS },
          { name: "Courses", path: ROUTES.COURSES },
          { name: "Jobs", path: ROUTES.JOBS },
          { name: "Forum", path: ROUTES.FORUM },
        ];
      case USER_ROLES.INSTRUCTOR:
        return [
          { name: "Home", path: ROUTES.HOME },
          { name: "Courses", path: ROUTES.COURSES },
          { name: "Assessments", path: ROUTES.MOCK_TESTS },
          { name: "Forum", path: ROUTES.FORUM },
        ];
      case USER_ROLES.COMPANY:
        return [
          { name: "Home", path: ROUTES.HOME },
          { name: "Jobs & Internships", path: ROUTES.JOBS },
          { name: "Forum", path: ROUTES.FORUM },
        ];
      case USER_ROLES.LEARNER:
      default:
        return [
          { name: "Home", path: ROUTES.HOME },
          { name: "Courses", path: ROUTES.COURSES },
          { name: "Mock Tests", path: ROUTES.MOCK_TESTS },
          { name: "Jobs & Internships", path: ROUTES.JOBS },
          { name: "Forum", path: ROUTES.FORUM },
        ];
    }
  };

  const navLinks = getNavLinks();

  return (
    <header className="sticky top-0 z-40 bg-white border-b border-slate-100 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16 sm:h-20">
          {/* Logo & Brand matching UI design */}
          <Link to={ROUTES.HOME} className="flex items-center space-x-2.5 group">
            <div className="w-8 h-8 rounded-lg bg-navy-950 flex items-center justify-center text-blue-400 font-bold text-sm shadow-sm group-hover:bg-blue-600 group-hover:text-white transition-colors">
              <span className="font-heading">A*</span>
            </div>
            <span className="text-xl font-extrabold tracking-tight text-navy-950 font-heading">
              SKILL<span className="text-blue-600">2</span>CAREER
            </span>
          </Link>

          {/* Navigation Links */}
          <nav className="hidden md:flex items-center space-x-6 lg:space-x-8">
            {navLinks.map((link) => {
              const isActive = location.pathname === link.path;
              return (
                <Link
                  key={link.name}
                  to={link.path}
                  className={`text-sm font-medium transition-colors ${
                    isActive
                      ? "text-blue-600 font-semibold"
                      : "text-slate-600 hover:text-navy-950"
                  }`}
                >
                  {link.name}
                </Link>
              );
            })}
          </nav>

          {/* Auth Controls */}
          <div className="flex items-center space-x-4">
            {isAuthenticated ? (
              <div className="flex items-center space-x-3">
                {/* Role-Specific Portal Button */}
                {user?.role === USER_ROLES.ADMIN ? (
                  <Link
                    to={ROUTES.ADMIN_DASHBOARD}
                    className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-full text-xs font-semibold bg-purple-50 text-purple-700 hover:bg-purple-100 transition-colors border border-purple-200"
                  >
                    <Shield className="w-3.5 h-3.5 text-purple-600" />
                    <span>Admin Console</span>
                  </Link>
                ) : (
                  <Link
                    to={ROUTES.DASHBOARD}
                    className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-full text-xs font-semibold bg-blue-50 text-blue-700 hover:bg-blue-100 transition-colors"
                  >
                    <LayoutDashboard className="w-3.5 h-3.5" />
                    <span>Dashboard</span>
                  </Link>
                )}

                {/* User info & Role Badge */}
                <div className="flex items-center space-x-2 pl-2 border-l border-slate-200">
                  <div className="w-8 h-8 rounded-full bg-slate-200 flex items-center justify-center text-slate-700 text-xs font-bold">
                    {user?.first_name?.charAt(0) || <UserIcon className="w-4 h-4" />}
                  </div>
                  <div className="hidden sm:flex flex-col text-left">
                    <span className="text-xs font-semibold text-navy-900 leading-tight">
                      {user?.first_name} {user?.last_name}
                    </span>
                    <span className="text-[10px] uppercase font-bold text-slate-400">
                      {user?.role}
                    </span>
                  </div>
                </div>

                <button
                  type="button"
                  onClick={handleLogout}
                  className="p-1.5 text-slate-500 hover:text-crimson transition-colors"
                  title="Sign Out"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <div className="flex items-center space-x-3">
                <Link
                  to={ROUTES.LOGIN}
                  className="text-sm font-semibold text-navy-900 hover:text-blue-600 px-3 py-2 transition-colors"
                >
                  Login
                </Link>
                <Link
                  to={ROUTES.REGISTER}
                  className="bg-black hover:bg-navy-900 text-white text-sm font-medium px-5 py-2 rounded-lg shadow-sm transition-all hover:shadow"
                >
                  Register
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};

export default Navbar;
