import React from "react";
import { Link } from "react-router-dom";
import { ROUTES } from "../constants";
import Button from "../components/forms/Button";
import { Home } from "lucide-react";

export const NotFound = () => {
  return (
    <div className="min-h-[calc(100vh-16rem)] flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8 text-center">
      <div className="max-w-md w-full space-y-4">
        <h1 className="text-7xl font-extrabold text-navy-900 font-heading">404</h1>
        <h2 className="text-xl font-bold text-navy-800">Page Not Found</h2>
        <p className="text-sm text-slate-500">
          The requested page could not be found or has been moved.
        </p>
        <div className="pt-2">
          <Link to={ROUTES.HOME}>
            <Button variant="primary" size="md">
              <Home className="w-4 h-4 mr-2" /> Back to Home
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
};

export default NotFound;
