import React, { useState, useEffect, useRef } from "react";
import { useSearchParams } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { useChat } from "../hooks/useChat";
import chatService from "../services/chatService";
import {
  MessageSquare,
  Search,
  Send,
  GraduationCap,
  Check,
  CheckCheck,
} from "lucide-react";

export const Messages = () => {
  const { user } = useAuth();
  const [searchParams] = useSearchParams();
  const targetUserId = searchParams.get("user");

  const {
    conversations,
    activeConversation,
    messages,
    loading,
    messagesLoading,
    isWsConnected,
    typingCounterpart,
    selectConversation,
    sendMessage,
    emitTyping,
    startConversation,
  } = useChat();

  const [inputText, setInputText] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [showInstructorsModal, setShowInstructorsModal] = useState(false);
  const [instructors, setInstructors] = useState([]);
  const [instructorsLoading, setInstructorsLoading] = useState(false);

  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // If query parameter ?user={id} is present, automatically start/select conversation
  useEffect(() => {
    if (targetUserId) {
      startConversation(Number(targetUserId)).catch(() => {});
    }
  }, [targetUserId, startConversation]);

  // Auto-scroll to bottom of active message stream
  useEffect(() => {
    if (activeConversation && messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, typingCounterpart, activeConversation]);

  // Focus message input when active conversation changes
  useEffect(() => {
    if (activeConversation && inputRef.current) {
      inputRef.current.focus();
    }
  }, [activeConversation]);

  // Load instructors directory
  const loadInstructors = () => {
    setShowInstructorsModal(true);
    if (instructors.length === 0) {
      setInstructorsLoading(true);
      chatService
        .getInstructorsDirectory()
        .then((res) => {
          if (res?.data) setInstructors(res.data);
        })
        .catch((err) => console.warn("Failed to load instructors directory:", err))
        .finally(() => setInstructorsLoading(false));
    }
  };

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
      console.error("Message send failure:", err);
      setInputText(textToSend);
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
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <span className="text-xs font-extrabold uppercase tracking-wider text-blue-600">
            Real-time Communication (SKL-16)
          </span>
          <h1 className="text-3xl font-extrabold text-navy-950 font-heading tracking-tight mt-1 flex items-center gap-3">
            Messages & Academic Guidance
            <span
              className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold ${
                isWsConnected
                  ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                  : "bg-amber-50 text-amber-700 border border-amber-200"
              }`}
            >
              <span
                className={`w-2 h-2 rounded-full ${
                  isWsConnected ? "bg-emerald-500 animate-pulse" : "bg-amber-500"
                }`}
              />
              {isWsConnected ? "WebSocket Connected" : "Connecting..."}
            </span>
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Direct duplex communication connecting learners with verified instructors.
          </p>
        </div>

        <button
          onClick={loadInstructors}
          className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold shadow-sm hover:shadow transition self-start sm:self-auto"
        >
          <GraduationCap className="w-4 h-4" />
          <span>New Conversation</span>
        </button>
      </div>

      {/* Main Dual-Panel Workspace */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-200/80 overflow-hidden flex h-[700px] max-h-[82vh]">
        {/* Left Column: Conversations List */}
        <div className="w-full md:w-80 lg:w-96 border-r border-slate-200 flex flex-col bg-slate-50/50">
          {/* Search Box */}
          <div className="p-3 bg-white border-b border-slate-200">
            <div className="relative">
              <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search conversations..."
                className="w-full pl-9 pr-3 py-2 text-xs bg-slate-100 border border-slate-200 rounded-xl focus:outline-none focus:ring-1 focus:ring-blue-600 focus:bg-white text-slate-900"
              />
            </div>
          </div>

          {/* Conversations Scrollable List */}
          <div className="flex-1 overflow-y-auto divide-y divide-slate-100">
            {loading ? (
              <div className="p-8 text-center text-xs text-slate-400">Loading messages...</div>
            ) : filteredConversations.length === 0 ? (
              <div className="p-8 text-center space-y-3">
                <div className="w-12 h-12 mx-auto rounded-full bg-blue-50 flex items-center justify-center text-blue-600">
                  <MessageSquare className="w-6 h-6" />
                </div>
                <h4 className="text-sm font-bold text-slate-800">No conversations yet</h4>
                <p className="text-xs text-slate-500 max-w-xs mx-auto">
                  Start direct guidance chats with verified course instructors.
                </p>
                <button
                  onClick={loadInstructors}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-600 text-white text-xs font-semibold hover:bg-blue-700 transition"
                >
                  <GraduationCap className="w-3.5 h-3.5" />
                  Connect with Instructors
                </button>
              </div>
            ) : (
              filteredConversations.map((conv) => {
                const isSelected = activeConversation?.id === conv.id;
                const hasUnread = conv.unread_count > 0;
                return (
                  <div
                    key={conv.id}
                    onClick={() => selectConversation(conv)}
                    className={`p-3.5 cursor-pointer transition flex items-start gap-3 border-l-4 ${
                      isSelected
                        ? "bg-white border-blue-600 shadow-sm"
                        : hasUnread
                        ? "bg-blue-50/70 border-blue-400 hover:bg-blue-50"
                        : "border-transparent hover:bg-white"
                    }`}
                  >
                    <div className="relative shrink-0">
                      <div className="w-11 h-11 rounded-full bg-gradient-to-tr from-blue-600 to-indigo-600 text-white font-bold flex items-center justify-center text-sm shadow-sm">
                        {conv.participant.name.charAt(0).toUpperCase()}
                      </div>
                      <span
                        className={`absolute bottom-0 right-0 w-3 h-3 rounded-full border-2 border-white ${
                          conv.participant.is_online ? "bg-emerald-500" : "bg-slate-300"
                        }`}
                      />
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <h4
                          className={`text-xs truncate ${
                            hasUnread || isSelected
                              ? "font-bold text-navy-950"
                              : "font-semibold text-slate-800"
                          }`}
                        >
                          {conv.participant.name}
                        </h4>
                        <span className="text-[10px] text-slate-400 shrink-0">
                          {formatTime(conv.last_message?.created_at || conv.updated_at)}
                        </span>
                      </div>

                      <div className="flex items-center gap-1 mt-0.5">
                        <span className="text-[9px] font-semibold uppercase px-1 rounded bg-slate-200/80 text-slate-700">
                          {conv.participant.role}
                        </span>
                        <p
                          className={`text-[11px] truncate ${
                            hasUnread ? "font-bold text-slate-900" : "text-slate-500"
                          }`}
                        >
                          {conv.last_message
                            ? (conv.last_message.sender_id === user.id ? "You: " : "") +
                              conv.last_message.message_text
                            : "New conversation"}
                        </p>
                      </div>
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
        </div>

        {/* Right Column: Active Thread */}
        <div className="flex-1 flex flex-col bg-white">
          {activeConversation ? (
            <>
              {/* Active Conversation Header */}
              <div className="p-4 border-b border-slate-200 flex items-center justify-between bg-white">
                <div className="flex items-center gap-3">
                  <div className="relative">
                    <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-blue-600 to-indigo-600 text-white font-bold flex items-center justify-center text-sm shadow">
                      {activeConversation.participant.name.charAt(0).toUpperCase()}
                    </div>
                    <span
                      className={`absolute bottom-0 right-0 w-2.5 h-2.5 rounded-full border-2 border-white ${
                        activeConversation.participant.is_online ? "bg-emerald-500" : "bg-slate-300"
                      }`}
                    />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="text-sm font-bold text-navy-950">
                        {activeConversation.participant.name}
                      </h3>
                      <span className="text-[10px] font-bold uppercase px-1.5 py-0.5 rounded bg-blue-100 text-blue-700">
                        {activeConversation.participant.role}
                      </span>
                    </div>
                    <p className="text-xs text-slate-500">
                      {activeConversation.participant.designation ||
                        activeConversation.participant.institution ||
                        activeConversation.participant.email}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <span
                    className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold ${
                      activeConversation.participant.is_online
                        ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                        : "bg-slate-100 text-slate-600"
                    }`}
                  >
                    <span
                      className={`w-1.5 h-1.5 rounded-full ${
                        activeConversation.participant.is_online ? "bg-emerald-500" : "bg-slate-400"
                      }`}
                    />
                    {activeConversation.participant.is_online ? "Active Now" : "Offline"}
                  </span>
                </div>
              </div>

              {/* Message History Feed */}
              <div className="flex-1 p-4 overflow-y-auto space-y-3 bg-slate-50/40">
                {messagesLoading ? (
                  <div className="p-8 text-center text-xs text-slate-400">Loading messages...</div>
                ) : messages.length === 0 ? (
                  <div className="p-8 text-center text-xs text-slate-400 space-y-1">
                    <p className="font-semibold text-slate-600">No messages in this thread yet.</p>
                    <p>Send a message below to start your conversation.</p>
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
                          className={`max-w-[70%] px-4 py-2.5 rounded-2xl text-xs shadow-sm break-words ${
                            isMine
                              ? "bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-br-none"
                              : "bg-white text-slate-800 border border-slate-200/80 rounded-bl-none"
                          }`}
                        >
                          <p className="leading-relaxed whitespace-pre-wrap">{msg.message_text}</p>
                        </div>
                        <div className="flex items-center gap-1.5 mt-1 px-1 text-[10px] text-slate-400">
                          <span>{formatTime(msg.created_at)}</span>
                          {isMine && (
                            <span>
                              {msg.is_read ? (
                                <CheckCheck className="w-3.5 h-3.5 text-blue-500 inline" />
                              ) : (
                                <Check className="w-3.5 h-3.5 text-slate-400 inline" />
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
                  <div className="flex items-center gap-1.5 text-xs text-slate-400 italic px-2 py-1">
                    <span className="w-2 h-2 rounded-full bg-blue-500 animate-ping" />
                    <span>{activeConversation.participant.name} is typing...</span>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>

              {/* Message Input Box */}
              <form
                onSubmit={handleSend}
                className="p-3 bg-white border-t border-slate-200 flex items-center gap-3"
              >
                <input
                  ref={inputRef}
                  type="text"
                  value={inputText}
                  onChange={handleInputChange}
                  onKeyDown={handleKeyDown}
                  placeholder={`Message ${activeConversation.participant.name}... (Press Enter to send)`}
                  className="flex-1 px-4 py-2.5 text-xs bg-slate-100 border border-slate-200 rounded-xl focus:outline-none focus:ring-1 focus:ring-blue-600 focus:bg-white text-slate-900 placeholder:text-slate-400"
                />
                <button
                  type="submit"
                  disabled={!inputText.trim() || isSending}
                  className="px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold disabled:opacity-40 disabled:hover:bg-blue-600 transition flex items-center gap-1.5 shadow-sm"
                >
                  <span>Send</span>
                  <Send className="w-3.5 h-3.5" />
                </button>
              </form>
            </>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center p-8 text-center">
              <div className="w-16 h-16 rounded-full bg-blue-50 flex items-center justify-center text-blue-600 mb-4">
                <MessageSquare className="w-8 h-8" />
              </div>
              <h3 className="text-lg font-bold text-navy-950 font-heading">
                Select a conversation
              </h3>
              <p className="text-xs text-slate-500 max-w-sm mt-1">
                Choose an active discussion from the left panel, or reach out to verified instructors for real-time mentorship.
              </p>
              <button
                onClick={loadInstructors}
                className="mt-4 inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold shadow-sm transition"
              >
                <GraduationCap className="w-4 h-4" />
                Browse Instructors Directory
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Instructors Directory Modal */}
      {showInstructorsModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
          <div className="bg-white rounded-2xl shadow-xl border border-slate-200 w-full max-w-lg max-h-[85vh] flex flex-col overflow-hidden animate-in fade-in duration-200">
            <div className="p-4 border-b border-slate-200 flex items-center justify-between bg-slate-50">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg bg-blue-100 flex items-center justify-center text-blue-600">
                  <GraduationCap className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-navy-950">Instructors Directory</h3>
                  <p className="text-xs text-slate-500">Connect with verified educators for guidance</p>
                </div>
              </div>
              <button
                onClick={() => setShowInstructorsModal(false)}
                className="p-1 hover:bg-slate-200 rounded-lg text-slate-500 transition"
              >
                ✕
              </button>
            </div>

            <div className="p-3 border-b border-slate-200 bg-white">
              <div className="relative">
                <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Filter by name or domain..."
                  className="w-full pl-8 pr-3 py-1.5 text-xs bg-slate-100 border border-slate-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-blue-600 text-slate-900"
                />
              </div>
            </div>

            <div className="flex-1 overflow-y-auto divide-y divide-slate-100 p-2">
              {instructorsLoading ? (
                <div className="p-8 text-center text-xs text-slate-400">Loading directory...</div>
              ) : filteredInstructors.length === 0 ? (
                <div className="p-8 text-center text-xs text-slate-500">No instructors found.</div>
              ) : (
                filteredInstructors.map((inst) => (
                  <div
                    key={inst.id}
                    className="p-3 hover:bg-slate-50 rounded-xl flex items-center justify-between gap-3 transition"
                  >
                    <div className="flex items-center gap-3 min-w-0">
                      <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-indigo-600 to-purple-600 text-white font-bold flex items-center justify-center text-sm shadow-sm shrink-0">
                        {inst.name.charAt(0).toUpperCase()}
                      </div>
                      <div className="truncate">
                        <h4 className="text-xs font-bold text-slate-900 truncate">{inst.name}</h4>
                        <p className="text-[11px] text-slate-600 truncate">
                          {inst.designation || inst.institution || "Instructor"}
                        </p>
                        {inst.expertise_domain && (
                          <span className="inline-block mt-0.5 text-[10px] font-medium text-blue-600 bg-blue-50 px-1.5 py-0.2 rounded">
                            {inst.expertise_domain}
                          </span>
                        )}
                      </div>
                    </div>

                    <button
                      onClick={async () => {
                        setShowInstructorsModal(false);
                        await startConversation(inst.id);
                      }}
                      className="px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold shrink-0 transition"
                    >
                      {inst.has_existing_conversation ? "Open Thread" : "Message"}
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Messages;
