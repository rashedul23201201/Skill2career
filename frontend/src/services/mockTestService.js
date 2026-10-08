import api from "./api";

export const mockTestService = {
  async getMockTests(params = {}) {
    const response = await api.get("/mock-tests", { params });
    return response.data;
  },

  async getMockTestById(testId) {
    const response = await api.get(`/mock-tests/${testId}`);
    return response.data;
  },

  async createMockTest(testData) {
    const response = await api.post("/mock-tests", testData);
    return response.data;
  },

  async updateMockTest(testId, testData) {
    const response = await api.put(`/mock-tests/${testId}`, testData);
    return response.data;
  },

  async deleteMockTest(testId) {
    const response = await api.delete(`/mock-tests/${testId}`);
    return response.data;
  },

  async updateTestStatus(testId, { status }) {
    const response = await api.patch(`/mock-tests/${testId}/status`, { status });
    return response.data;
  },

  async addQuestion(testId, questionData) {
    const response = await api.post(`/mock-tests/${testId}/questions`, questionData);
    return response.data;
  },

  async getQuestions(testId) {
    const response = await api.get(`/mock-tests/${testId}/questions`);
    return response.data;
  },

  async updateQuestion(testId, questionId, questionData) {
    const response = await api.put(`/mock-tests/${testId}/questions/${questionId}`, questionData);
    return response.data;
  },

  async deleteQuestion(testId, questionId) {
    const response = await api.delete(`/mock-tests/${testId}/questions/${questionId}`);
    return response.data;
  },

  async syncQuestions(testId, questions) {
    const response = await api.post(`/mock-tests/${testId}/questions/sync`, { questions });
    return response.data;
  },
};

export default mockTestService;
