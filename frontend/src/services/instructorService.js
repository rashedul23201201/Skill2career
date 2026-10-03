import api from "./api";

/**
 * Service for Instructor Account Management and Admin Review (SKL-52).
 */
const instructorService = {
  /**
   * Submit an initial instructor onboarding application.
   */
  applyAsInstructor: async (payload) => {
    const response = await api.post("/instructors/apply", payload);
    return response.data;
  },

  /**
   * Retrieve the current instructor's profile and credentials.
   */
  getProfile: async () => {
    const response = await api.get("/instructors/profile");
    return response.data;
  },

  /**
   * Update the current instructor's profile details.
   */
  updateProfile: async (payload) => {
    const response = await api.put("/instructors/profile", payload);
    return response.data;
  },

  /**
   * Get instructor workspace counters (active courses, total learners, mock tests).
   */
  getDashboardStats: async () => {
    const response = await api.get("/instructors/dashboard-stats");
    return response.data;
  },

  /**
   * Admin: Fetch pending instructor applications awaiting review.
   */
  getPendingInstructors: async (skip = 0, limit = 50) => {
    const response = await api.get("/admin/instructors/pending", {
      params: { skip, limit },
    });
    return response.data;
  },

  /**
   * Admin: Approve, reject, or suspend an instructor onboarding request.
   */
  updateInstructorStatus: async (profileId, status, reason = null) => {
    const response = await api.patch(`/admin/instructors/${profileId}/status`, {
      status,
      reason,
    });
    return response.data;
  },
};

export default instructorService;
