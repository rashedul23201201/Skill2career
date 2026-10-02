import React, { createContext, useState, useEffect, useCallback } from "react";
import authService from "../services/authService";
import { getStoredToken, setStoredToken, removeStoredToken } from "../utils";

export const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(() => getStoredToken());
  const [loading, setLoading] = useState(true);

  // Initialize and verify authentication state on app load
  const loadUser = useCallback(async () => {
    const storedToken = getStoredToken();
    if (!storedToken) {
      setUser(null);
      setLoading(false);
      return;
    }

    try {
      const response = await authService.getMe();
      if (response?.data) {
        setUser(response.data);
      }
    } catch (error) {
      console.error("Session verification failed:", error);
      removeStoredToken();
      setToken(null);
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadUser();

    // Handle unauthorized event dispatched from Axios interceptor
    const handleUnauthorized = () => {
      removeStoredToken();
      setToken(null);
      setUser(null);
    };

    window.addEventListener("auth:unauthorized", handleUnauthorized);
    return () => {
      window.removeEventListener("auth:unauthorized", handleUnauthorized);
    };
  }, [loadUser]);

  const login = async (email, password) => {
    setLoading(true);
    try {
      const result = await authService.login({ email, password });
      const accessToken = result.data.access_token;
      
      setStoredToken(accessToken);
      setToken(accessToken);

      // Fetch user profile immediately after login
      const profile = await authService.getMe();
      setUser(profile.data);
      return profile.data;
    } finally {
      setLoading(false);
    }
  };

  const register = async (userData) => {
    setLoading(true);
    try {
      const result = await authService.register(userData);
      return result.data;
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    removeStoredToken();
    setToken(null);
    setUser(null);
  };

  const value = {
    user,
    token,
    loading,
    isAuthenticated: Boolean(token && user),
    login,
    register,
    logout,
    refreshUser: loadUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
