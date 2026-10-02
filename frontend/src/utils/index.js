/**
 * Utility functions for storage, formatting, and validation.
 */
import { STORAGE_KEYS } from "../constants";

export const getStoredToken = () => {
  try {
    return localStorage.getItem(STORAGE_KEYS.TOKEN);
  } catch {
    return null;
  }
};

export const setStoredToken = (token) => {
  try {
    if (token) {
      localStorage.setItem(STORAGE_KEYS.TOKEN, token);
    } else {
      localStorage.removeItem(STORAGE_KEYS.TOKEN);
    }
  } catch (e) {
    console.error("Failed to persist access token to storage", e);
  }
};

export const removeStoredToken = () => {
  try {
    localStorage.removeItem(STORAGE_KEYS.TOKEN);
  } catch (e) {
    console.error("Failed to remove access token from storage", e);
  }
};

export const getStoredRefreshToken = () => {
  try {
    return localStorage.getItem(STORAGE_KEYS.REFRESH_TOKEN);
  } catch {
    return null;
  }
};

export const setStoredRefreshToken = (refreshToken) => {
  try {
    if (refreshToken) {
      localStorage.setItem(STORAGE_KEYS.REFRESH_TOKEN, refreshToken);
    } else {
      localStorage.removeItem(STORAGE_KEYS.REFRESH_TOKEN);
    }
  } catch (e) {
    console.error("Failed to persist refresh token to storage", e);
  }
};

export const removeStoredRefreshToken = () => {
  try {
    localStorage.removeItem(STORAGE_KEYS.REFRESH_TOKEN);
  } catch (e) {
    console.error("Failed to remove refresh token from storage", e);
  }
};

export const clearAllTokens = () => {
  removeStoredToken();
  removeStoredRefreshToken();
};

export const formatErrorMessage = (error) => {
  if (error.response?.data?.message) {
    return error.response.data.message;
  }
  if (error.response?.data?.detail) {
    if (typeof error.response.data.detail === "string") {
      return error.response.data.detail;
    }
    if (Array.isArray(error.response.data.detail)) {
      return error.response.data.detail.map((d) => d.msg || d).join(", ");
    }
  }
  if (error.message) {
    return error.message;
  }
  return "An unexpected error occurred. Please try again.";
};
