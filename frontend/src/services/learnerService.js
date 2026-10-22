import api from "./api";

/**
 * Service for Learner Profile Management, Dynamic Rubric Calculation, and Resume Management (SKL-51).
 */
export const learnerService = {
  /**
   * Fetch consolidated candidate dashboard telemetry (SKL-59).
   */
  async getDashboardSummary() {
    const response = await api.get("/learners/dashboard-summary");
    return response.data;
  },

  /**
   * Fetch authenticated learner's complete profile with completion breakdown.
   */
  async getProfile() {
    const response = await api.get("/learners/profile");
    return response.data;
  },

  /**
   * Update profile fields and receive recalculation of completion score.
   * @param {Object} data - Form fields to update
   */
  async updateProfile(data) {
    const response = await api.put("/learners/profile", data);
    return response.data;
  },

  /**
   * Upload resume document (PDF or DOCX, max 5MB).
   * @param {File} file - Browser File object
   */
  async uploadResume(file) {
    const formData = new FormData();
    formData.append("file", file);

    const response = await api.post("/learners/resume", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
    return response.data;
  },

  /**
   * Download the authenticated learner's uploaded resume.
   */
  async downloadResume() {
    const response = await api.get("/learners/resume/download", {
      responseType: "blob",
    });
    return response;
  },

  /**
   * Delete uploaded resume and decrement profile completion.
   */
  async deleteResume() {
    const response = await api.delete("/learners/resume");
    return response.data;
  },

  /**
   * Fetch saved vacancies collection with real-time status reflection (SKL-6).
   */
  async getSavedJobs(params = {}) {
    const response = await api.get("/learners/saved-jobs", { params });
    return response.data;
  },

  /**
   * Remove a saved vacancy by saved_job_id or job_id (SKL-6).
   */
  async deleteSavedJob(id) {
    const response = await api.delete(`/learners/saved-jobs/${id}`);
    return response.data;
  },

  /**
   * Fetch profile-based smart job recommendations with match percentages (SKL-6).
   */
  async getRecommendedJobs(params = {}) {
    const response = await api.get("/learners/recommended-jobs", { params });
    return response.data;
  },
};

export default learnerService;
