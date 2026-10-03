import api from "./api";

/**
 * Service for Learner Profile Management, Dynamic Rubric Calculation, and Resume Management (SKL-51).
 */
export const learnerService = {
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
};

export default learnerService;
