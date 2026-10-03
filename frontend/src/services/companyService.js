import api from "./api";

/**
 * Service for employer company registration, verification dossier pipelines, and job publishing (SKL-2).
 */
export const companyService = {
  /**
   * Fetch current verification status and dossier details for authenticated company.
   */
  async getVerificationStatus() {
    const response = await api.get("/companies/verification-status");
    return response.data;
  },

  /**
   * Submit official trade license and credentials dossier for verification review.
   */
  async submitVerificationRequest(payload) {
    const response = await api.post("/companies/verification-request", payload);
    return response.data;
  },

  /**
   * Simulated job creation endpoint (enforces require_verified_company gatekeeper).
   */
  async createJob(payload) {
    const response = await api.post("/companies/jobs", payload);
    return response.data;
  },
};

export default companyService;
