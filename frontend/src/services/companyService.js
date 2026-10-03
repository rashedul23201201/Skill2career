import api from "./api";

/**
 * Service for Company Profile Management, Branding Assets, Public Views, Verification, and Jobs (SKL-2 & SKL-3).
 */
export const companyService = {
  /**
   * Fetch authenticated company's complete profile (SKL-3).
   */
  async getProfile() {
    const response = await api.get("/companies/profile/me");
    return response.data;
  },

  /**
   * Update company profile details (tagline, size, address, social links, website) (SKL-3).
   * @param {Object} data - Profile fields to update
   */
  async updateProfile(data) {
    const response = await api.put("/companies/profile/me", data);
    return response.data;
  },

  /**
   * Upload company logo image (PNG, JPG, WEBP, max 5MB) (SKL-3).
   * @param {File} file - Image file object from file input
   */
  async uploadLogo(file) {
    const formData = new FormData();
    formData.append("file", file);

    const response = await api.post("/companies/profile/logo", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
    return response.data;
  },

  /**
   * Upload company cover banner image (PNG, JPG, WEBP, max 5MB) (SKL-3).
   * @param {File} file - Image file object from file input
   */
  async uploadBanner(file) {
    const formData = new FormData();
    formData.append("file", file);

    const response = await api.post("/companies/profile/banner", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
    return response.data;
  },

  /**
   * Fetch public company profile details accessible by Learners and Guests (SKL-3).
   * @param {number|string} companyId - ID of company profile
   */
  async getPublicProfile(companyId) {
    const response = await api.get(`/companies/${companyId}/public`);
    return response.data;
  },

  /**
   * Admin content moderation for company accounts (SKL-3).
   * @param {number|string} companyId - ID of company profile
   * @param {Object} data - Moderation action and notes
   */
  async moderateCompany(companyId, data) {
    const response = await api.patch(`/admin/companies/${companyId}/moderate`, data);
    return response.data;
  },

  /**
   * Fetch current verification status and dossier details for authenticated company (SKL-2).
   */
  async getVerificationStatus() {
    const response = await api.get("/companies/verification-status");
    return response.data;
  },

  /**
   * Submit official trade license and credentials dossier for verification review (SKL-2).
   */
  async submitVerificationRequest(payload) {
    const response = await api.post("/companies/verification-request", payload);
    return response.data;
  },

  /**
   * Simulated job creation endpoint (enforces require_verified_company gatekeeper) (SKL-2).
   */
  async createJob(payload) {
    const response = await api.post("/companies/jobs", payload);
    return response.data;
  },
};

export default companyService;
