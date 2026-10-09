import api from "./api";

export const interviewService = {
  createInterviewRequest: async (applicationId, data) => {
    const res = await api.post(`/applications/${applicationId}/interview-request`, data);
    return res.data;
  },

  getMyInterviews: async (params = {}) => {
    const res = await api.get("/interviews/me", { params });
    return res.data;
  },

  getInterviewById: async (id) => {
    const res = await api.get(`/interviews/${id}`);
    return res.data;
  },

  getInterviewForApplication: async (applicationId) => {
    const res = await api.get(`/applications/${applicationId}/interview`);
    return res.data;
  },

  selectSlot: async (interviewId, slotId) => {
    const res = await api.post(`/interviews/${interviewId}/select-slot`, { slot_id: slotId });
    return res.data;
  },

  rescheduleInterview: async (interviewId, data) => {
    const res = await api.post(`/interviews/${interviewId}/reschedule`, data);
    return res.data;
  },

  updateStatus: async (interviewId, data) => {
    const res = await api.patch(`/interviews/${interviewId}/status`, data);
    return res.data;
  },

  downloadIcsCalendar: async (interviewId) => {
    const res = await api.get(`/interviews/${interviewId}/ics`, {
      responseType: "blob",
    });
    const blob = new Blob([res.data], { type: "text/calendar;charset=utf-8" });
    const downloadUrl = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = downloadUrl;
    link.setAttribute("download", `interview-${interviewId}.ics`);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(downloadUrl);
  },

  submitFeedback: async (interviewId, data) => {
    const res = await api.post(`/interviews/${interviewId}/feedback`, data);
    return res.data;
  },

  getInterviewFeedback: async (interviewId) => {
    const res = await api.get(`/interviews/${interviewId}/feedback`);
    return res.data;
  },

  getApplicationFeedback: async (applicationId) => {
    const res = await api.get(`/applications/${applicationId}/interview-feedback`);
    return res.data;
  },

  updateFeedback: async (feedbackId, data) => {
    const res = await api.put(`/interviews/feedback/${feedbackId}`, data);
    return res.data;
  },

  shareFeedback: async (interviewId, isShared = true) => {
    const res = await api.post(`/interviews/${interviewId}/feedback/share`, {
      is_shared_with_candidate: isShared,
    });
    return res.data;
  },

  getFeedbackAuditLogs: async (params = {}) => {
    const res = await api.get("/interviews/feedback/audit-logs", { params });
    return res.data;
  },
};

export default interviewService;
