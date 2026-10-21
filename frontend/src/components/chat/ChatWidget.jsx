import React, { useState, useRef, useEffect } from "react";
import { useAuth } from "../../hooks/useAuth";
import { useChat } from "../../hooks/useChat";
import chatService from "../../services/chatService";
import {
  MessageSquare,
  X,
  Send,
  Search,
  ArrowLeft,
  GraduationCap,
  Check,
  CheckCheck,
} from "lucide-react";

export const ChatWidget = () => {
  const { user, isAuthenticated } = useAuth();
  const {
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
  } = useChat();

  const [isOpen, setIsOpen] = useState(false);
  const [activeTab, setActiveTab] = useState("chats"); // "chats" | "instructors"
  const [inputText, setInputText] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [instructors, setInstructors] = useState([]);
  const [instructorsLoading, setInstructorsLoading] = useState(false);
  const [isSending, setIsSending] = useState(false);

  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Auto-scroll to latest message
  useEffect(() => {
    if (activeConversation && messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, typingCounterpart, activeConversation]);

  // Focus input when conversation is selected
  useEffect(() => {
    if (activeConversation && inputRef.current) {
      inputRef.current.focus();
    }
  }, [activeConversation]);

  // Load instructors directory when tab switched
  useEffect(() => {
    if (activeTab === "instructors" && instructors.length === 0) {
      setInstructorsLoading(true);
      chatService
        .getInstructorsDirectory()
        .then((res) => {
          if (res?.data) setInstructors(res.data);
        })
        .catch((err) => console.warn("Failed to load instructors directory:", err))
        .finally(() => setInstructorsLoading(false));
    }
  }, [activeTab, instructors.length]);

  if (!isAuthenticated || !user) return null;

  const handleSend = async (e) => {
    e?.preventDefault();
    if (!inputText.trim() || isSending) return;

    const textToSend = inputText;
    setInputText("");
    emitTyping(false);

    try {
      setIsSending(true);
      await sendMessage(textToSend);
    } catch (err) {
      console.error("Message send error:", err);
      setInputText(textToSend); // Restore on error
    } finally {
      setIsSending(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleInputChange = (e) => {
    setInputText(e.target.value);
    emitTyping(e.target.value.length > 0);
  };

  // Filtered lists
  const filteredConversations = conversations.filter((c) => {
    const name = c.participant?.name?.toLowerCase() || "";
    const email = c.participant?.email?.toLowerCase() || "";
    return name.includes(searchQuery.toLowerCase()) || email.includes(searchQuery.toLowerCase());
  });

  const filteredInstructors = instructors.filter((inst) => {
    const name = inst.name?.toLowerCase() || "";
    const domain = inst.expertise_domain?.toLowerCase() || "";
    return name.includes(searchQuery.toLowerCase()) || domain.includes(searchQuery.toLowerCase());
  });

  const formatTime = (isoString) => {
    if (!isoString) return "";
    const date = new Date(isoString);
    const now = new Date();
    const diffHours = (now - date) / (1000 * 60 * 60);
    if (diffHours < 24 && date.getDate() === now.getDate()) {
      return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    }
    return date.toLocaleDateString([], { month: "short", day: "numeric" });
  };

  return (
    <div className="fixed bottom-5 right-5 z-50 font-sans">
      {/* Floating Toggle Button */}
      {!isOpen && (
        <button
          id="chat-widget-toggle-btn"
          onClick={() => setIsOpen(true)}
          className="relative flex items-center justify-center w-14 h-14 rounded-full bg-gradient-to-r from-blue-600 to-indigo-700 text-white shadow-xl hover:shadow-2xl hover:scale-105 active:scale-95 transition-all duration-200 border-2 border-white/20"
          title="Open Real-time Chat (SKL-16)"
        >
          <MessageSquare className="w-6 h-6" />
          {totalUnreadCount > 0 && (
            <span className="absolute -top-1 -right-1 flex items-center justify-center min-w-5 h-5 px-1.5 text-xs font-black text-white bg-red-600 rounded-full border-2 border-white animate-pulse">
              {totalUnreadCount > 9 ? "9+" : totalUnreadCount}
            </span>
          )}
          {/* Real-time WebSocket connection pulse badge */}
          <span
            className={`absolute bottom-0 right-0 w-3.5 h-3.5 rounded-full border-2 border-white ${
              isWsConnected ? "bg-emerald-500" : "bg-amber-400"
            }`}
            title={isWsConnected ? "Live WebSocket Connected" : "Connecting..."}
          />
        </button>
      )}

      {/* Expanded Chat Drawer Container */}
      {isOpen && (
        <div
          id="chat-widget-drawer"
          className="w-[360px] sm:w-[410px] h-[550px] max-h-[85vh] bg-white rounded-2xl shadow-2xl border border-slate-200/80 flex flex-col overflow-hidden animate-in fade-in slide-in-from-bottom-6 duration-200"
        >
          {/* Drawer Header */}
          <div className="bg-gradient-to-r from-navy-950 via-slate-900 to-navy-900 text-white px-4 py-3.5 flex items-center justify-between border-b border-white/10">
            {activeConversation ? (
              <div className="flex items-center gap-2.5 overflow-hidden">
                <button
                  onClick={() => selectConversation(null)}
                  className="p-1 hover:bg-white/10 rounded-lg text-slate-300 hover:text-white transition"
                  title="Back to conversations"
                >
                  <ArrowLeft className="w-5 h-5" />
                </button>
                <div className="w-9 h-9 rounded-full bg-gradient-to-tr from-blue-500 to-indigo-600 text-white font-bold flex items-center justify-center text-sm shrink-0 shadow-inner">
                  {activeConversation.participant.name.charAt(0).toUpperCase()}
                </div>
                <div className="truncate">
                  <div className="flex items-center gap-1.5">
                    <h3 className="text-sm font-bold truncate">
                      {activeConversation.participant.name}
                    </h3>
                    <span className="text-[10px] font-semibold uppercase px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-300">
                      {activeConversation.participant.role}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-300 truncate">
                    {activeConversation.participant.designation ||
                      activeConversation.participant.institution ||
                      (activeConversation.participant.is_online ? "Active Now" : "Offline")}
                  </p>
                </div>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg bg-blue-600/30 flex items-center justify-center text-blue-400">
                  <MessageSquare className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-white flex items-center gap-1.5">
                    Real-time Messages
                    <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-300 uppercase">
                      SKL-16
                    </span>
                  </h3>
                  <div className="flex items-center gap-1 text-[11px] text-slate-400">
                    <span
                      className={`inline-block w-1.5 h-1.5 rounded-full ${
                        isWsConnected ? "bg-emerald-400 animate-pulse" : "bg-amber-400"
                      }`}
                    />
                    <span>{isWsConnected ? "Duplex Live" : "Connecting..."}</span>
                  </div>
                </div>
              </div>
            )}

            <div className="flex items-center gap-1">
              <button
                onClick={() => setIsOpen(false)}
                className="p-1.5 hover:bg-white/10 rounded-lg text-slate-400 hover:text-white transition"
                title="Close chat"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* View A: Conversation List & Directory */}
          {!activeConversation && (
            <div className="flex-1 flex flex-col overflow-hidden bg-slate-50">
              {/* Tab Selector */}
              <div className="flex border-b border-slate-200 bg-white px-2">
                <button
                  onClick={() => setActiveTab("chats")}
                  className={`flex-1 py-2.5 text-xs font-bold transition-all border-b-2 flex items-center justify-center gap-1.5 ${
                    activeTab === "chats"
                      ? "border-blue-600 text-blue-600"
                      : "border-transparent text-slate-500 hover:text-slate-800"
                  }`}
                >
                  <MessageSquare className="w-3.5 h-3.5" />
                  <span>Chats ({conversations.length})</span>
                  {totalUnreadCount > 0 && (
                    <span className="ml-1 px-1.5 py-0.2 bg-red-600 text-white rounded-full text-[10px] font-black">
                      {totalUnreadCount}
                    </span>
                  )}
                </button>
                <button
                  onClick={() => setActiveTab("instructors")}
                  className={`flex-1 py-2.5 text-xs font-bold transition-all border-b-2 flex items-center justify-center gap-1.5 ${
                    activeTab === "instructors"
                      ? "border-blue-600 text-blue-600"
                      : "border-transparent text-slate-500 hover:text-slate-800"
                  }`}
                >
                  <GraduationCap className="w-4 h-4" />
                  <span>Instructors</span>
                </button>
              </div>

              {/* Search Bar */}
              <div className="p-2.5 bg-white border-b border-slate-100">
                <div className="relative">
                  <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder={
                      activeTab === "chats" ? "Search conversations..." : "Search instructors..."
                    }
                    className="w-full pl-8 pr-3 py-1.5 text-xs bg-slate-100 border border-slate-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-blue-600 focus:bg-white text-slate-800"
                  />
                </div>
              </div>

              {/* Tab Content: Active Conversations */}
              {activeTab === "chats" && (
                <div className="flex-1 overflow-y-auto divide-y divide-slate-100">
                  {loading ? (
                    <div className="p-8 text-center text-xs text-slate-400">Loading chats...</div>
                  ) : filteredConversations.length === 0 ? (
                    <div className="p-8 text-center space-y-3">
                      <div className="w-12 h-12 mx-auto rounded-full bg-blue-50 flex items-center justify-center text-blue-600">
                        <MessageSquare className="w-6 h-6" />
                      </div>
                      <h4 className="text-sm font-bold text-slate-800">No conversations yet</h4>
                      <p className="text-xs text-slate-500 max-w-xs mx-auto">
                        Connect directly with verified instructors for real-time mentorship and guidance.
                      </p>
                      <button
                        onClick={() => setActiveTab("instructors")}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-600 text-white text-xs font-semibold hover:bg-blue-700 transition"
                      >
                        <GraduationCap className="w-3.5 h-3.5" />
                        Find Instructors
                      </button>
                    </div>
                  ) : (
                    filteredConversations.map((conv) => {
                      const hasUnread = conv.unread_count > 0;
                      return (
                        <div
                          key={conv.id}
                          onClick={() => selectConversation(conv)}
                          className={`p-3 hover:bg-white cursor-pointer transition flex items-start gap-3 ${
                            hasUnread ? "bg-blue-50/60" : ""
                          }`}
                        >
                          <div className="relative shrink-0">
                            <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-blue-600 to-indigo-600 text-white font-bold flex items-center justify-center text-sm shadow-sm">
                              {conv.participant.name.charAt(0).toUpperCase()}
                            </div>
                            <span
                              className={`absolute bottom-0 right-0 w-2.5 h-2.5 rounded-full border-2 border-white ${
                                conv.participant.is_online ? "bg-emerald-500" : "bg-slate-300"
                              }`}
                            />
                          </div>

                          <div className="flex-1 min-w-0">
                            <div className="flex items-center justify-between">
                              <h4
                                className={`text-xs truncate ${
                                  hasUnread ? "font-bold text-navy-950" : "font-semibold text-slate-800"
                                }`}
                              >
                                {conv.participant.name}
                              </h4>
                              <span className="text-[10px] text-slate-400 shrink-0">
                                {formatTime(conv.last_message?.created_at || conv.updated_at)}
                              </span>
                            </div>

                            <p
                              className={`text-[11px] truncate mt-0.5 ${
                                hasUnread ? "font-medium text-slate-800" : "text-slate-500"
                              }`}
                            >
                              {conv.last_message
                                ? (conv.last_message.sender_id === user.id ? "You: " : "") +
                                  conv.last_message.message_text
                                : "Conversation started"}
                            </p>
                          </div>

                          {hasUnread && (
                            <span className="w-5 h-5 rounded-full bg-blue-600 text-white text-[10px] font-black flex items-center justify-center shrink-0">
                              {conv.unread_count}
                            </span>
                          )}
                        </div>
                      );
                    })
                  )}
                </div>
              )}

              {/* Tab Content: Instructors Directory */}
              {activeTab === "instructors" && (
                <div className="flex-1 overflow-y-auto divide-y divide-slate-100">
                  {instructorsLoading ? (
                    <div className="p-8 text-center text-xs text-slate-400">
                      Loading available instructors...
                    </div>
                  ) : filteredInstructors.length === 0 ? (
                    <div className="p-8 text-center text-xs text-slate-500">
                      No instructors match your search.
                    </div>
                  ) : (
                    filteredInstructors.map((inst) => (
                      <div
                        key={inst.id}
                        className="p-3 hover:bg-white flex items-center justify-between gap-3 transition"
                      >
                        <div className="flex items-center gap-3 min-w-0">
                          <div className="w-9 h-9 rounded-full bg-gradient-to-tr from-indigo-600 to-purple-600 text-white font-bold flex items-center justify-center text-xs shrink-0 shadow-sm">
                            {inst.name.charAt(0).toUpperCase()}
                          </div>
                          <div className="truncate">
                            <h4 className="text-xs font-bold text-slate-900 truncate">
                              {inst.name}
                            </h4>
                            <p className="text-[11px] text-slate-500 truncate">
                              {inst.designation || inst.expertise_domain || inst.institution || "Instructor"}
                            </p>
                          </div>
                        </div>

                        <button
                          onClick={() => {
                            startConversation(inst.id);
                          }}
                          className={`px-2.5 py-1 rounded-lg text-xs font-semibold shrink-0 transition ${
                            inst.has_existing_conversation
                              ? "bg-slate-100 text-slate-700 hover:bg-slate-200"
                              : "bg-blue-600 text-white hover:bg-blue-700"
                          }`}
                        >
                          {inst.has_existing_conversation ? "Open Chat" : "Chat"}
                        </button>
                      </div>
                    ))
                  )}
                </div>
              )}
            </div>
          )}

          {/* View B: Active Chat Message Thread */}
          {activeConversation && (
            <div className="flex-1 flex flex-col overflow-hidden bg-slate-50/50">
              {/* Message Feed */}
              <div className="flex-1 p-3 overflow-y-auto space-y-2.5">
                {messagesLoading ? (
                  <div className="p-6 text-center text-xs text-slate-400">
                    Loading conversation history...
                  </div>
                ) : messages.length === 0 ? (
                  <div className="p-6 text-center text-xs text-slate-400 space-y-1">
                    <p className="font-semibold text-slate-600">No messages in this thread yet.</p>
                    <p>Send a message below to start your real-time guidance session.</p>
                  </div>
                ) : (
                  messages.map((msg) => {
                    const isMine = msg.sender_id === user.id;
                    return (
                      <div
                        key={msg.id}
                        className={`flex flex-col ${isMine ? "items-end" : "items-start"}`}
                      >
                        <div
                          className={`max-w-[82%] px-3 py-2 rounded-2xl text-xs shadow-sm break-words ${
                            isMine
                              ? "bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-br-none"
                              : "bg-white text-slate-800 border border-slate-200/80 rounded-bl-none"
                          }`}
                        >
                          <p className="leading-relaxed whitespace-pre-wrap">{msg.message_text}</p>
                        </div>
                        <div className="flex items-center gap-1 mt-0.5 px-1 text-[10px] text-slate-400">
                          <span>{formatTime(msg.created_at)}</span>
                          {isMine && (
                            <span>
                              {msg.is_read ? (
                                <CheckCheck className="w-3 h-3 text-blue-500 inline" />
                              ) : (
                                <Check className="w-3 h-3 text-slate-400 inline" />
                              )}
                            </span>
                          )}
                        </div>
                      </div>
                    );
                  })
                )}

                {/* Real-time Typing Status Indicator */}
                {typingCounterpart && (
                  <div className="flex items-center gap-1 text-[11px] text-slate-400 italic px-2 py-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-ping" />
                    <span>{activeConversation.participant.name} is typing...</span>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>

              {/* Message Input Box */}
              <form
                onSubmit={handleSend}
                className="p-2.5 bg-white border-t border-slate-200 flex items-center gap-2"
              >
                <input
                  ref={inputRef}
                  type="text"
                  value={inputText}
                  onChange={handleInputChange}
                  onKeyDown={handleKeyDown}
                  placeholder={`Message ${activeConversation.participant.name}...`}
                  className="flex-1 px-3 py-2 text-xs bg-slate-100 border border-slate-200 rounded-xl focus:outline-none focus:ring-1 focus:ring-blue-600 focus:bg-white text-slate-900 placeholder:text-slate-400"
                />
                <button
                  type="submit"
                  disabled={!inputText.trim() || isSending}
                  className="p-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white disabled:opacity-40 disabled:hover:bg-blue-600 transition flex items-center justify-center shrink-0"
                  title="Send message (Enter)"
                >
                  <Send className="w-4 h-4" />
                </button>
              </form>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ChatWidget;
