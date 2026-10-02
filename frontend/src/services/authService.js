import api from "./api";

/**
 * Authentication API service handling registration, login, and user profile.
 */
export const authService = {
  /**
   * Register a new user
   * @param {Object} data { email, password, first_name, last_name, role }
   */
  async register(data) {
    const response = await api.post("/auth/register", data);
    return response.data;
  },

  /**
   * Authenticate user with credentials
   * @param {Object} credentials { email, password }
   */
  async login(credentials) {
    const response = await api.post("/auth/login", credentials);
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
