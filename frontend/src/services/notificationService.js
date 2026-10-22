import api from "./api";

/**
 * Service orchestrating REST API for the Notification System (SKL-17).
 */
export const notificationService = {
  /**
   * Fetch paginated notifications with optional read filter and unread count (AC-2, AC-5).
   * @param {Object} params - { page, size, is_read }
   */
  async getNotifications(params = {}) {
    const response = await api.get("/notifications", { params });
    return response.data;
  },

  /**
   * Fetch fast unread count for the navbar badge indicator.
   */
  async getUnreadCount() {
    const response = await api.get("/notifications/unread-count");
    return response.data;
  },

  /**
   * Mark a specific notification as read (AC-3).
   * @param {number} notificationId
   */
  async markAsRead(notificationId) {
    const response = await api.patch(`/notifications/${notificationId}/read`);
    return response.data;
  },

  /**
   * Mark all unread notifications as read (AC-3).
   */
  async markAllAsRead() {
    const response = await api.patch("/notifications/mark-all-read");
    return response.data;
  },
};

export default notificationService;
