import React, { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import {
  Bell,
  CheckCheck,
  X,
  Briefcase,
  Calendar,
  MessageSquare,
  CreditCard,
  GraduationCap,
  CheckCircle2,
  Clock,
  ExternalLink,
  Check,
  AlertCircle,
  RefreshCw,
} from "lucide-react";
import notificationService from "../../services/notificationService";

/**
 * Format relative time string from ISO date string.
 */
const formatTimeAgo = (isoString) => {
  if (!isoString) return "";
  const date = new Date(isoString);
  const now = new Date();
  const seconds = Math.floor((now - date) / 1000);

  if (seconds < 60) return "Just now";
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 30) return `${days}d ago`;
  return date.toLocaleDateString();
};

/**
 * Get iconography and color scheme tailored to notification event type.
 */
const getEventVisuals = (eventType) => {
  const type = (eventType || "").toUpperCase();
  switch (type) {
    case "APPLICATION_UPDATE":
    case "APPLICATION_RECEIVED":
      return {
        icon: Briefcase,
        bg: "bg-blue-50 text-blue-600 border-blue-200",
        badge: "Application",
      };
    case "INTERVIEW_INVITE":
    case "INTERVIEW_CONFIRMED":
      return {
        icon: Calendar,
        bg: "bg-emerald-50 text-emerald-600 border-emerald-200",
        badge: "Interview",
      };
    case "CHAT_MESSAGE":
      return {
        icon: MessageSquare,
        bg: "bg-indigo-50 text-indigo-600 border-indigo-200",
        badge: "Message",
      };
    case "PAYMENT_SUCCESS":
      return {
        icon: CreditCard,
        bg: "bg-amber-50 text-amber-600 border-amber-200",
        badge: "Payment",
      };
    case "COURSE_ENROLLMENT":
      return {
        icon: GraduationCap,
        bg: "bg-sky-50 text-sky-600 border-sky-200",
        badge: "Course",
      };
    case "FORUM_VERIFIED_ANSWER":
      return {
        icon: CheckCircle2,
        bg: "bg-purple-50 text-purple-600 border-purple-200",
        badge: "Verified Answer",
      };
    default:
      return {
        icon: Bell,
        bg: "bg-slate-50 text-slate-600 border-slate-200",
        badge: "Alert",
      };
  }
};

export const NotificationDrawer = ({
  isOpen,
  onClose,
  unreadCount = 0,
  onUnreadCountChange,
}) => {
  const navigate = useNavigate();
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(false);
  const [filter, setFilter] = useState("ALL"); // "ALL" | "UNREAD"
  const [error, setError] = useState(null);
  const [markingAll, setMarkingAll] = useState(false);

  const fetchNotifications = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = {
        page: 1,
        size: 50,
      };
      if (filter === "UNREAD") {
        params.is_read = false;
      }
      const res = await notificationService.getNotifications(params);
      if (res && res.data) {
        setNotifications(res.data.items || []);
        if (typeof onUnreadCountChange === "function") {
          onUnreadCountChange(res.data.unread_count || 0);
        }
      }
    } catch (err) {
      console.error("Failed to load notifications:", err);
      setError("Unable to load notifications. Please try again.");
    } finally {
      setLoading(false);
    }
  }, [filter, onUnreadCountChange]);

  useEffect(() => {
    if (isOpen) {
      fetchNotifications();
    }
  }, [isOpen, fetchNotifications]);

  const handleMarkAsRead = async (e, item) => {
    e.stopPropagation();
    if (item.is_read) return;

    try {
      await notificationService.markAsRead(item.id);
      setNotifications((prev) =>
        prev.map((n) => (n.id === item.id ? { ...n, is_read: true } : n))
      );
      if (typeof onUnreadCountChange === "function") {
        onUnreadCountChange(Math.max(0, unreadCount - 1));
      }
    } catch (err) {
      console.error("Failed to mark notification as read:", err);
    }
  };

  const handleMarkAllAsRead = async () => {
    setMarkingAll(true);
    try {
      await notificationService.markAllAsRead();
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
      if (typeof onUnreadCountChange === "function") {
        onUnreadCountChange(0);
      }
    } catch (err) {
      console.error("Failed to mark all as read:", err);
    } finally {
      setMarkingAll(false);
    }
  };

  const handleItemClick = async (item) => {
    if (!item.is_read) {
      try {
        await notificationService.markAsRead(item.id);
        setNotifications((prev) =>
          prev.map((n) => (n.id === item.id ? { ...n, is_read: true } : n))
        );
        if (typeof onUnreadCountChange === "function") {
          onUnreadCountChange(Math.max(0, unreadCount - 1));
        }
      } catch (err) {
        console.error("Failed to mark notification as read on click:", err);
      }
    }

    if (item.link_url) {
      onClose();
      navigate(item.link_url);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden" role="dialog" aria-modal="true">
      {/* Backdrop overlay */}
      <div
        className="fixed inset-0 bg-navy-950/40 backdrop-blur-xs transition-opacity duration-200"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Drawer Container */}
      <div className="fixed inset-y-0 right-0 max-w-full flex pl-10">
        <div className="w-screen max-w-md bg-white shadow-2xl flex flex-col border-l border-slate-200/80 animate-in slide-in-from-right duration-200">
          
          {/* Header */}
          <div className="p-4 sm:p-5 border-b border-slate-100 bg-slate-50/70">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2.5">
                <div className="w-9 h-9 rounded-xl bg-blue-50 border border-blue-200/60 flex items-center justify-center text-blue-600 shadow-2xs">
                  <Bell className="w-5 h-5" />
                </div>
                <div>
                  <h2 className="text-base font-bold text-navy-950 font-heading leading-tight">
                    Notifications
                  </h2>
                  <p className="text-xs text-slate-500">
                    {unreadCount > 0
                      ? `${unreadCount} unread alert${unreadCount > 1 ? "s" : ""}`
                      : "All caught up"}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-1.5">
                <button
                  type="button"
                  onClick={fetchNotifications}
                  disabled={loading}
                  className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-200/60 transition"
                  title="Refresh notifications"
                >
                  <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
                </button>
                <button
                  type="button"
                  onClick={onClose}
                  className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-200/60 transition"
                  aria-label="Close notifications drawer"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Filter Tabs & Quick Action */}
            <div className="flex items-center justify-between pt-1">
              <div className="flex items-center bg-slate-200/60 p-0.5 rounded-lg text-xs font-semibold">
                <button
                  type="button"
                  onClick={() => setFilter("ALL")}
                  className={`px-3 py-1 rounded-md transition ${
                    filter === "ALL"
                      ? "bg-white text-navy-950 shadow-2xs"
                      : "text-slate-600 hover:text-navy-950"
                  }`}
                >
                  All
                </button>
                <button
                  type="button"
                  onClick={() => setFilter("UNREAD")}
                  className={`px-3 py-1 rounded-md transition flex items-center gap-1.5 ${
                    filter === "UNREAD"
                      ? "bg-white text-blue-600 shadow-2xs"
                      : "text-slate-600 hover:text-navy-950"
                  }`}
                >
                  <span>Unread</span>
                  {unreadCount > 0 && (
                    <span className="w-4 h-4 rounded-full bg-blue-600 text-white text-[10px] flex items-center justify-center font-bold">
                      {unreadCount}
                    </span>
                  )}
                </button>
              </div>

              {unreadCount > 0 && (
                <button
                  type="button"
                  onClick={handleMarkAllAsRead}
                  disabled={markingAll}
                  className="inline-flex items-center gap-1 text-xs font-medium text-blue-600 hover:text-blue-700 hover:underline disabled:opacity-50 transition"
                >
                  <CheckCheck className="w-3.5 h-3.5" />
                  <span>Mark all as read</span>
                </button>
              )}
            </div>
          </div>

          {/* Body: Notifications List */}
          <div className="flex-1 overflow-y-auto divide-y divide-slate-100">
            {loading && notifications.length === 0 ? (
              <div className="p-8 text-center space-y-3">
                <div className="w-8 h-8 mx-auto border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
                <p className="text-xs text-slate-500">Loading your notifications...</p>
              </div>
            ) : error ? (
              <div className="p-8 text-center space-y-3">
                <AlertCircle className="w-8 h-8 mx-auto text-rose-500" />
                <p className="text-xs text-slate-600">{error}</p>
                <button
                  type="button"
                  onClick={fetchNotifications}
                  className="px-3 py-1.5 text-xs font-semibold bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  Try Again
                </button>
              </div>
            ) : notifications.length === 0 ? (
              <div className="p-12 text-center space-y-3">
                <div className="w-14 h-14 mx-auto rounded-2xl bg-slate-50 border border-slate-200 flex items-center justify-center text-slate-400">
                  <Bell className="w-6 h-6" />
                </div>
                <h3 className="text-sm font-bold text-navy-900 font-heading">
                  {filter === "UNREAD" ? "No unread alerts" : "No notifications yet"}
                </h3>
                <p className="text-xs text-slate-500 max-w-xs mx-auto">
                  {filter === "UNREAD"
                    ? "You are all caught up with your latest platform updates."
                    : "When you receive application updates, interview requests, or messages, they will appear right here."}
                </p>
              </div>
            ) : (
              notifications.map((item) => {
                const visuals = getEventVisuals(item.event_type);
                const IconComponent = visuals.icon;
                return (
                  <div
                    key={item.id}
                    onClick={() => handleItemClick(item)}
                    className={`p-4 transition-colors cursor-pointer relative group flex items-start gap-3.5 ${
                      item.is_read
                        ? "bg-white hover:bg-slate-50/70"
                        : "bg-blue-50/40 hover:bg-blue-50/70 border-l-4 border-l-blue-600"
                    }`}
                  >
                    {/* Event Icon */}
                    <div
                      className={`w-9 h-9 rounded-xl border flex items-center justify-center shrink-0 mt-0.5 ${visuals.bg}`}
                    >
                      <IconComponent className="w-4 h-4" />
                    </div>

                    {/* Content */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between gap-2 mb-1">
                        <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                          {visuals.badge}
                        </span>
                        <div className="flex items-center gap-1 text-[11px] text-slate-400">
                          <Clock className="w-3 h-3" />
                          <span>{formatTimeAgo(item.created_at)}</span>
                        </div>
                      </div>

                      <h4
                        className={`text-xs font-semibold leading-snug mb-1 line-clamp-1 ${
                          item.is_read ? "text-navy-900" : "text-navy-950 font-bold"
                        }`}
                      >
                        {item.title}
                      </h4>

                      <p className="text-xs text-slate-600 leading-relaxed line-clamp-2 mb-2">
                        {item.message}
                      </p>

                      <div className="flex items-center justify-between">
                        {item.link_url ? (
                          <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-blue-600 group-hover:text-blue-700">
                            <span>Open details</span>
                            <ExternalLink className="w-3 h-3" />
                          </span>
                        ) : (
                          <span />
                        )}

                        {!item.is_read && (
                          <button
                            type="button"
                            onClick={(e) => handleMarkAsRead(e, item)}
                            className="p-1 rounded-md text-slate-400 hover:text-blue-600 hover:bg-blue-100/60 transition text-[11px] inline-flex items-center gap-1"
                            title="Mark as read"
                          >
                            <Check className="w-3.5 h-3.5" />
                            <span>Mark read</span>
                          </button>
                        )}
                      </div>
                    </div>

                    {/* Unread dot */}
                    {!item.is_read && (
                      <span className="w-2 h-2 rounded-full bg-blue-600 shrink-0 mt-2" />
                    )}
                  </div>
                );
              })
            )}
          </div>

          {/* Footer Info */}
          <div className="p-3 bg-slate-50 border-t border-slate-200/80 text-center">
            <p className="text-[11px] text-slate-400">
              Skill2Career Real-time Event Notification Hub &bull; SKL-17
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default NotificationDrawer;
