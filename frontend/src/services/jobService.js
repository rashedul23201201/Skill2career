import api from "./api";

/**
 * Service handling recruitment vacancies, candidate discovery, and company posting management (SKL-4).
 */
export const jobService = {
  /**
   * Fetch paginated job/internship postings with optional filters (posting_type, work_mode, search, my_jobs, status).
   */
  async getJobs(params = {}) {
    const response = await api.get("/jobs", { params });
    return response.data;
  },

  /**
   * Fetch single job posting details including requirements and hiring company profile.
   */
  async getJobById(jobId) {
    const response = await api.get(`/jobs/${jobId}`);
    return response.data;
  },

  /**
   * Create a new job or internship posting (Company / Admin).
   */
  async createJob(jobData) {
    const response = await api.post("/jobs", jobData);
    return response.data;
  },

  /**
   * Update existing job posting metadata.
   */
  async updateJob(jobId, jobData) {
    const response = await api.put(`/jobs/${jobId}`, jobData);
    return response.data;
  },

  /**
   * Delete a job posting.
   */
  async deleteJob(jobId) {
    const response = await api.delete(`/jobs/${jobId}`);
    return response.data;
  },

  /**
   * Toggle vacancy status (ACTIVE / CLOSED / DRAFT) or apply administrative moderation.
   */
  async updateJobStatus(jobId, { status, reason = "" }) {
    const response = await api.patch(`/jobs/${jobId}/status`, {
      status,
      reason,
    });
    return response.data;
  },
};

export default jobService;
