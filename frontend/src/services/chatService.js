import api from "./api";
import { API_BASE_URL } from "../constants";
import { getStoredToken } from "../utils";

/**
 * Service orchestrating REST API & duplex WebSocket channel for Real-time Chat (SKL-16).
 */
export const chatService = {
  /**
   * Fetch authenticated user's conversations list (SKL-16 AC-1).
   */
  async getConversations() {
    const response = await api.get("/chat/conversations");
    return response.data;
  },

  /**
   * Fetch single conversation details with counterpart profile (SKL-16 AC-4).
   */
  async getConversationDetails(conversationId) {
    const response = await api.get(`/chat/conversations/${conversationId}`);
    return response.data;
  },

  /**
   * Fetch paginated historical messages for a conversation (SKL-16 AC-4).
   */
  async getMessages(conversationId, params = {}) {
    const response = await api.get(`/chat/conversations/${conversationId}/messages`, {
      params,
    });
    return response.data;
  },

  /**
   * Start a new conversation or open existing with an instructor (SKL-16 AC-1).
   */
  async createConversation(instructorId, initialMessage = null) {
    const payload = { instructor_id: instructorId };
    if (initialMessage && initialMessage.trim()) {
      payload.initial_message = initialMessage.trim();
    }
    const response = await api.post("/chat/conversations", payload);
    return response.data;
  },

  /**
   * Send a message to an active conversation via REST (SKL-16 AC-2).
   */
  async sendMessage(conversationId, messageText) {
    const response = await api.post(`/chat/conversations/${conversationId}/messages`, {
      message_text: messageText,
    });
    return response.data;
  },

  /**
   * Mark incoming messages in a conversation as read.
   */
  async markAsRead(conversationId) {
    const response = await api.post(`/chat/conversations/${conversationId}/read`);
    return response.data;
  },

  /**
   * Discover active instructors available for direct chat guidance.
   */
  async getInstructorsDirectory() {
    const response = await api.get("/chat/instructors");
    return response.data;
  },

  /**
   * Generate WebSocket URL matching current API base address with JWT authentication.
   */
  getWebSocketUrl() {
    const token = getStoredToken();
    if (!token) return null;

    let wsBase = API_BASE_URL;
    if (wsBase.startsWith("http://")) {
      wsBase = wsBase.replace("http://", "ws://");
    } else if (wsBase.startsWith("https://")) {
      wsBase = wsBase.replace("https://", "wss://");
    } else if (!wsBase.startsWith("ws://") && !wsBase.startsWith("wss://")) {
      const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      wsBase = `${protocol}//${window.location.host}${wsBase}`;
    }

    return `${wsBase}/ws/chat?token=${encodeURIComponent(token)}`;
  },
};

export default chatService;
