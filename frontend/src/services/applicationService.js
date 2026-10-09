import api from "./api";

export const applicationService = {
  async applyToJob(jobId, data, isMultipart = false) {
    const config = isMultipart
      ? { headers: { "Content-Type": "multipart/form-data" } }
      : {};
    const response = await api.post(`/jobs/${jobId}/apply`, data, config);
    return response.data;
  },

  async getMyApplications(params = {}) {
    const response = await api.get("/learners/applications", { params });
    return response.data;
  },

  async checkApplicationStatus(jobId) {
    const response = await api.get(`/applications/check/${jobId}`);
    return response.data;
  },

  async getApplicationById(applicationId) {
    const response = await api.get(`/applications/${applicationId}`);
    return response.data;
  },

  async withdrawApplication(applicationId) {
    const response = await api.delete(`/applications/${applicationId}/withdraw`);
    return response.data;
  },

  async updateApplicationStatus(applicationId, status, notes = "") {
    const response = await api.patch(`/applications/${applicationId}/status`, {
      status,
      notes,
    });
    return response.data;
  },

  async getJobApplications(jobId, params = {}) {
    const response = await api.get(`/jobs/${jobId}/applications`, { params });
    return response.data;
  },
};

export default applicationService;
