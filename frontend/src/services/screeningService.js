import api from "./api";

export const screeningService = {
  async getScreeningQuestions(jobId) {
    const response = await api.get(`/jobs/${jobId}/screening-questions`);
    return response.data;
  },

  async addScreeningQuestion(jobId, questionData) {
    const response = await api.post(`/jobs/${jobId}/screening-questions`, questionData);
    return response.data;
  },

  async updateScreeningQuestion(questionId, questionData) {
    const response = await api.put(`/screening-questions/${questionId}`, questionData);
    return response.data;
  },

  async deleteScreeningQuestion(questionId) {
    const response = await api.delete(`/screening-questions/${questionId}`);
    return response.data;
  },

  async screenCandidate(jobId, submissionData) {
    const response = await api.post(`/jobs/${jobId}/screen-candidate`, submissionData);
    return response.data;
  },

  async getApplicants(jobId, params = {}) {
    const response = await api.get(`/jobs/${jobId}/applicants`, { params });
    return response.data;
  },

  async updateApplicantStatus(applicantId, status) {
    const response = await api.patch(`/applicants/${applicantId}/status`, { status });
    return response.data;
  },
};

export default screeningService;
