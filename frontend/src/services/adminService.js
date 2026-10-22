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

  /**
   * Fetch all companies awaiting administrative verification review (SKL-2).
   */
  async getPendingCompanyVerifications() {
    const response = await api.get("/admin/companies/pending-verifications");
    return response.data;
  },

  /**
   * Approve or reject a company's verification dossier (SKL-2).
   */
  async verifyCompany(companyId, { action, notes = "" }) {
    const response = await api.post(`/admin/companies/${companyId}/verify`, {
      action,
      notes,
    });
    return response.data;
  },

  /**
   * Fetch courses and mock tests awaiting administrative moderation review (SKL-25).
   */
  async getPendingModeration() {
    const response = await api.get("/admin/moderation/pending");
    return response.data;
  },

  /**
   * Fetch moderation items with optional status and content_type filter (SKL-25).
   */
  async getModerationItems(params = {}) {
    const response = await api.get("/admin/moderation/items", { params });
    return response.data;
  },

  /**
   * Fetch overview count metrics across moderation stages (SKL-25).
   */
  async getModerationStats() {
    const response = await api.get("/admin/moderation/stats");
    return response.data;
  },

  /**
   * Fetch complete course curriculum details for inspection drawer (SKL-25).
   */
  async getCourseModerationPreview(courseId) {
    const response = await api.get(`/admin/moderation/courses/${courseId}/preview`);
    return response.data;
  },

  /**
   * Fetch complete mock test questions & solutions for inspection drawer (SKL-25).
   */
  async getMockTestModerationPreview(testId) {
    const response = await api.get(`/admin/moderation/mock-tests/${testId}/preview`);
    return response.data;
  },

  /**
   * Administratively approve a course for catalog distribution (SKL-25).
   */
  async approveCourse(courseId, { notes = "" } = {}) {
    const response = await api.post(`/admin/moderation/courses/${courseId}/approve`, {
      notes,
    });
    return response.data;
  },

  /**
   * Administratively restrict a policy-violating course (SKL-25).
   */
  async restrictCourse(courseId, { reason = "" }) {
    const response = await api.post(`/admin/moderation/courses/${courseId}/restrict`, {
      reason,
    });
    return response.data;
  },

  /**
   * Administratively approve a mock test for assessment catalog (SKL-25).
   */
  async approveMockTest(testId, { notes = "" } = {}) {
    const response = await api.post(`/admin/moderation/mock-tests/${testId}/approve`, {
      notes,
    });
    return response.data;
  },

  /**
   * Administratively restrict a policy-violating mock test (SKL-25).
   */
  async restrictMockTest(testId, { reason = "" }) {
    const response = await api.post(`/admin/moderation/mock-tests/${testId}/restrict`, {
      reason,
    });
    return response.data;
  },

  /**
   * Fetch chronological audit log of administrative moderation actions (SKL-25).
   */
  async getModerationLogs(params = {}) {
    const response = await api.get("/admin/moderation/logs", { params });
    return response.data;
  },

  /**
   * Fetch executive overview analytics with user, company, course, job, and revenue metrics (SKL-23).
   */
  async getAnalyticsOverview() {
    const response = await api.get("/admin/analytics/overview");
    return response.data;
  },

  /**
   * Fetch platform revenue analytics, gateway volume, and subscription distribution (SKL-23).
   */
  async getRevenueAnalytics() {
    const response = await api.get("/admin/analytics/revenue");
    return response.data;
  },

  /**
   * Fetch platform recruitment pipeline summary, application funnels, and hiring metrics (SKL-23).
   */
  async getRecruitmentSummary() {
    const response = await api.get("/admin/analytics/recruitment-summary");
    return response.data;
  },
};

export default adminService;

