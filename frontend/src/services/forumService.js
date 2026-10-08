import api from "./api";

export const forumService = {
  async getCategories() {
    const response = await api.get("/forum/categories");
    return response.data;
  },

  async getPosts(params = {}) {
    const response = await api.get("/forum/posts", { params });
    return response.data;
  },

  async getPostById(postId) {
    const response = await api.get(`/forum/posts/${postId}`);
    return response.data;
  },

  async createPost(postData) {
    const response = await api.post("/forum/posts", postData);
    return response.data;
  },

  async updatePost(postId, postData) {
    const response = await api.put(`/forum/posts/${postId}`, postData);
    return response.data;
  },

  async deletePost(postId) {
    const response = await api.delete(`/forum/posts/${postId}`);
    return response.data;
  },

  async togglePostLike(postId) {
    const response = await api.post(`/forum/posts/${postId}/like`);
    return response.data;
  },

  async getComments(postId) {
    const response = await api.get(`/forum/posts/${postId}/comments`);
    return response.data;
  },

  async addComment(postId, commentData) {
    const response = await api.post(`/forum/posts/${postId}/comments`, commentData);
    return response.data;
  },

  async updateComment(commentId, commentData) {
    const response = await api.put(`/forum/comments/${commentId}`, commentData);
    return response.data;
  },

  async deleteComment(commentId) {
    const response = await api.delete(`/forum/comments/${commentId}`);
    return response.data;
  },

  async toggleCommentLike(commentId) {
    const response = await api.post(`/forum/comments/${commentId}/like`);
    return response.data;
  },

  async createReport(reportData) {
    const response = await api.post("/forum/reports", reportData);
    return response.data;
  },

  async getReports(params = {}) {
    const response = await api.get("/forum/reports", { params });
    return response.data;
  },

  async updateReportStatus(reportId, { status }) {
    const response = await api.patch(`/forum/reports/${reportId}`, { status });
    return response.data;
  },
};

export default forumService;
