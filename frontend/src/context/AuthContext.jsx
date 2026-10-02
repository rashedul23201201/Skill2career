import React, { createContext, useState, useEffect, useCallback } from "react";
import authService from "../services/authService";
import {
  getStoredToken,
  setStoredToken,
  getStoredRefreshToken,
  setStoredRefreshToken,
  clearAllTokens,
} from "../utils";

export const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(() => getStoredToken());
  const [refreshToken, setRefreshToken] = useState(() => getStoredRefreshToken());
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
      clearAllTokens();
      setToken(null);
      setRefreshToken(null);
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadUser();

    // Handle unauthorized event dispatched from Axios interceptor
    const handleUnauthorized = () => {
      clearAllTokens();
      setToken(null);
      setRefreshToken(null);
      setUser(null);
    };

    window.addEventListener("auth:unauthorized", handleUnauthorized);
    return () => {
      window.removeEventListener("auth:unauthorized", handleUnauthorized);
    };
  }, [loadUser]);

  const login = async (email, password, remember_me = false) => {
    setLoading(true);
    try {
      const result = await authService.login({ email, password, remember_me });
      const { access_token, refresh_token, user: loggedUser } = result.data;

      setStoredToken(access_token);
      setToken(access_token);

      if (refresh_token) {
        setStoredRefreshToken(refresh_token);
        setRefreshToken(refresh_token);
      }

      setUser(loggedUser);
      return loggedUser;
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

  const forgotPassword = async (email) => {
    return await authService.forgotPassword(email);
  };

  const resetPassword = async (token, new_password) => {
    return await authService.resetPassword({ token, new_password });
  };

  const verifyEmail = async (token) => {
    const result = await authService.verifyEmail(token);
    if (result.data) {
      setUser(result.data);
    }
    return result;
  };

  const logout = () => {
    clearAllTokens();
    setToken(null);
    setRefreshToken(null);
    setUser(null);
  };

  const value = {
    user,
    token,
    refreshToken,
    loading,
    isAuthenticated: Boolean(token && user),
    login,
    register,
    forgotPassword,
    resetPassword,
    verifyEmail,
    logout,
    refreshUser: loadUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
