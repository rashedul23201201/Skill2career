import api from "./api";

/**
 * Authentication API service handling registration, login, token refresh, password reset, and email verification (SKL-49).
 */
export const authService = {
  /**
   * Register a new user across Learner, Instructor, or Company roles (AC-1)
   */
  async register(data) {
    const response = await api.post("/auth/register", data);
    return response.data;
  },

  /**
   * Authenticate user with credentials and optional remember_me (AC-2, AC-3)
   */
  async login(credentials) {
    const response = await api.post("/auth/login", credentials);
    return response.data;
  },

  /**
   * Rotate refresh token and fetch new access token
   */
  async refreshToken(refreshToken) {
    const response = await api.post("/auth/refresh", { refresh_token: refreshToken });
    return response.data;
  },

  /**
   * Request password reset token (AC-4)
   */
  async forgotPassword(email) {
    const response = await api.post("/auth/forgot-password", { email });
    return response.data;
  },

  /**
   * Reset password using reset token (AC-4)
   */
  async resetPassword({ token, new_password }) {
    const response = await api.post("/auth/reset-password", { token, new_password });
    return response.data;
  },

  /**
   * Verify email address with verification token (AC-1)
   */
  async verifyEmail(token) {
    const response = await api.post("/auth/verify-email", { token });
    return response.data;
  },

  /**
   * Fetch current authenticated user's profile
   */
  async getMe() {
    const response = await api.get("/auth/me");
    return response.data;
  },

  /**
   * Check backend health status
   */
  async checkHealth() {
    const response = await api.get("/health");
    return response.data;
  },
};

export default authService;
