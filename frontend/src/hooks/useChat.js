import { useState, useEffect, useRef, useCallback } from "react";
import chatService from "../services/chatService";
import { useAuth } from "./useAuth";

/**
 * Custom React Hook managing duplex WebSocket connection, active thread state,
 * optimistic message updates, and unread counters for SKL-16.
 */
export const useChat = (initialActiveId = null) => {
  const { user, isAuthenticated } = useAuth();

  const [conversations, setConversations] = useState([]);
  const [activeConversation, setActiveConversation] = useState(null);
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [messagesLoading, setMessagesLoading] = useState(false);
  const [isWsConnected, setIsWsConnected] = useState(false);
  const [typingCounterpart, setTypingCounterpart] = useState(false);

  const socketRef = useRef(null);
  const typingTimeoutRef = useRef(null);
  const activeConvRef = useRef(null);

  // Keep ref synchronized with state to prevent stale closures inside WebSocket callbacks
  useEffect(() => {
    activeConvRef.current = activeConversation;
  }, [activeConversation]);

  // Total unread count across all conversations
  const totalUnreadCount = conversations.reduce(
    (sum, c) => sum + (c.unread_count || 0),
    0
  );

  // 1. Fetch conversations list
  const fetchConversations = useCallback(async () => {
    if (!isAuthenticated || !user) return;
    try {
      setLoading(true);
      const res = await chatService.getConversations();
      if (res?.data) {
        setConversations(res.data);
      }
    } catch (err) {
      console.warn("Error loading conversations:", err);
    } finally {
      setLoading(false);
    }
  }, [isAuthenticated, user]);

  useEffect(() => {
    fetchConversations();
  }, [fetchConversations]);

  // 2. Load messages when active conversation changes
  const loadMessages = useCallback(async (convId) => {
    if (!convId) {
      setMessages([]);
      return;
    }
    try {
      setMessagesLoading(true);
      const res = await chatService.getMessages(convId);
      if (res?.data) {
        setMessages(res.data);
      }
      // Mark as read immediately on open
      chatService.markAsRead(convId).catch(() => {});
      setConversations((prev) =>
        prev.map((c) => (c.id === convId ? { ...c, unread_count: 0 } : c))
      );
    } catch (err) {
      console.error("Failed to load historical messages:", err);
    } finally {
      setMessagesLoading(false);
    }
  }, []);

  const selectConversation = useCallback(
    (conv) => {
      setActiveConversation(conv);
      if (conv) {
        loadMessages(conv.id);
      } else {
        setMessages([]);
      }
    },
    [loadMessages]
  );

  // If initial ID provided or changed externally
  useEffect(() => {
    if (initialActiveId && conversations.length > 0) {
      const match = conversations.find((c) => c.id === Number(initialActiveId));
      if (match && (!activeConversation || activeConversation.id !== match.id)) {
        selectConversation(match);
      }
    }
  }, [initialActiveId, conversations, activeConversation, selectConversation]);

  // 3. Duplex WebSocket Lifecycle
  useEffect(() => {
    if (!isAuthenticated || !user) {
      if (socketRef.current) {
        socketRef.current.close();
        socketRef.current = null;
      }
      setIsWsConnected(false);
      return;
    }

    const wsUrl = chatService.getWebSocketUrl();
    if (!wsUrl) return;

    let socket;
    let reconnectTimer;
    let isUnmounted = false;

    const connectWebSocket = () => {
      try {
        socket = new WebSocket(wsUrl);
        socketRef.current = socket;

        socket.onopen = () => {
          if (!isUnmounted) setIsWsConnected(true);
        };

        socket.onmessage = (event) => {
          if (isUnmounted) return;
          try {
            const data = JSON.parse(event.data);

            if (data.type === "new_message") {
              const incomingMsg = data.message;
              const currentActive = activeConvRef.current;

              // Append to active message thread if currently viewing this conversation
              if (currentActive && currentActive.id === data.conversation_id) {
                setMessages((prev) => {
                  if (prev.some((m) => m.id === incomingMsg.id)) return prev;
                  return [...prev, incomingMsg];
                });
                setTypingCounterpart(false);
                // Mark as read in real-time
                if (incomingMsg.sender_id !== user.id) {
                  chatService.markAsRead(data.conversation_id).catch(() => {});
                }
              }

              // Update conversation snippet and order in list
              setConversations((prev) => {
                const existingIndex = prev.findIndex((c) => c.id === data.conversation_id);
                if (existingIndex >= 0) {
                  const existing = prev[existingIndex];
                  const isCurrent = currentActive && currentActive.id === data.conversation_id;
                  const updated = {
                    ...existing,
                    last_message: incomingMsg,
                    updated_at: incomingMsg.created_at,
                    unread_count:
                      isCurrent || incomingMsg.sender_id === user.id
                        ? 0
                        : (existing.unread_count || 0) + 1,
                  };
                  const filtered = prev.filter((c) => c.id !== data.conversation_id);
                  return [updated, ...filtered];
                } else {
                  // New conversation created externally: reload list
                  fetchConversations();
                  return prev;
                }
              });
            } else if (data.type === "typing_status") {
              const currentActive = activeConvRef.current;
              if (currentActive && currentActive.id === data.conversation_id) {
                if (data.user_id !== user.id) {
                  setTypingCounterpart(data.is_typing);
                  if (typingTimeoutRef.current) clearTimeout(typingTimeoutRef.current);
                  if (data.is_typing) {
                    typingTimeoutRef.current = setTimeout(() => {
                      setTypingCounterpart(false);
                    }, 4000);
                  }
                }
              }
            } else if (data.type === "messages_read") {
              const currentActive = activeConvRef.current;
              if (currentActive && currentActive.id === data.conversation_id) {
                setMessages((prev) =>
                  prev.map((m) =>
                    m.sender_id === user.id ? { ...m, is_read: true } : m
                  )
                );
              }
            }
          } catch (err) {
            console.debug("Non-JSON or unknown WebSocket packet:", err);
          }
        };

        socket.onclose = () => {
          if (!isUnmounted) {
            setIsWsConnected(false);
            // Reconnect after 3 seconds with backoff
            reconnectTimer = setTimeout(connectWebSocket, 3000);
          }
        };

        socket.onerror = () => {
          socket.close();
        };
      } catch (err) {
        console.warn("WebSocket setup error:", err);
      }
    };

    connectWebSocket();

    return () => {
      isUnmounted = true;
      if (reconnectTimer) clearTimeout(reconnectTimer);
      if (typingTimeoutRef.current) clearTimeout(typingTimeoutRef.current);
      if (socket) {
        socket.close();
      }
      setIsWsConnected(false);
    };
  }, [isAuthenticated, user, fetchConversations]);

  // 4. Send Message (Duplex WebSocket with REST fallback)
  const sendMessage = useCallback(
    async (text) => {
      const clean = text?.trim();
      if (!clean || !activeConversation) return;

      const convId = activeConversation.id;

      // Prefer live duplex WebSocket
      if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
        socketRef.current.send(
          JSON.stringify({
            action: "send_message",
            conversation_id: convId,
            message_text: clean,
          })
        );
      } else {
        // Fallback to REST API
        try {
          const res = await chatService.sendMessage(convId, clean);
          if (res?.data) {
            setMessages((prev) => [...prev, res.data]);
            setConversations((prev) =>
              prev.map((c) =>
                c.id === convId
                  ? { ...c, last_message: res.data, updated_at: res.data.created_at }
                  : c
              )
            );
          }
        } catch (err) {
          console.error("Failed to send message via REST fallback:", err);
          throw err;
        }
      }
    },
    [activeConversation]
  );

  // 5. Emit typing status
  const emitTyping = useCallback(
    (isTyping) => {
      if (
        socketRef.current &&
        socketRef.current.readyState === WebSocket.OPEN &&
        activeConversation
      ) {
        socketRef.current.send(
          JSON.stringify({
            action: "typing",
            conversation_id: activeConversation.id,
            is_typing: isTyping,
          })
        );
      }
    },
    [activeConversation]
  );

  // 6. Start new conversation with instructor
  const startConversation = useCallback(
    async (instructorId, initialMsg = null) => {
      try {
        const res = await chatService.createConversation(instructorId, initialMsg);
        if (res?.data) {
          await fetchConversations();
          selectConversation(res.data);
          return res.data;
        }
      } catch (err) {
        console.error("Failed to start conversation:", err);
        throw err;
      }
    },
    [fetchConversations, selectConversation]
  );

  return {
    conversations,
    activeConversation,
    messages,
    loading,
    messagesLoading,
    isWsConnected,
    typingCounterpart,
    totalUnreadCount,
    selectConversation,
    sendMessage,
    emitTyping,
    startConversation,
    refreshConversations: fetchConversations,
  };
};

export default useChat;
