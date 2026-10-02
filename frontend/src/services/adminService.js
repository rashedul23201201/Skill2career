import api from "./api";

/**
 * Service for administrative operations, user governance, and security audit tracking (SKL-50/SKL-24).
 */
export const adminService = {
  /**
   * Retrieve platform high-level metric counters.
   */
  async getOverviewStats() {
    const response = await api.get("/admin/overview-stats");
    return response.data;
  },

  /**
   * Retrieve paginated and filterable user directory.
   */
  async getUsers(params = {}) {
    const response = await api.get("/admin/users", { params });
    return response.data;
  },

  /**
   * Fetch single user details by ID.
   */
  async getUserById(userId) {
    const response = await api.get(`/admin/users/${userId}`);
    return response.data;
  },

  /**
   * Toggle user account active status.
   */
  async updateUserStatus(userId, { is_active, reason = "" }) {
    const response = await api.patch(`/admin/users/${userId}/status`, {
      is_active,
      reason,
    });
    return response.data;
  },

  /**
   * Modify user system role.
   */
  async updateUserRole(userId, { role, reason = "" }) {
    const response = await api.patch(`/admin/users/${userId}/role`, {
      role,
      reason,
    });
    return response.data;
  },

  /**
   * Retrieve recent security and administrative audit trail.
   */
  async getAuditLogs(limit = 15) {
    const response = await api.get("/admin/audit-logs", {
      params: { limit },
    });
    return response.data;
  },
};

export default adminService;
