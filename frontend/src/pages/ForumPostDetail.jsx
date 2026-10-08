import React, { useState, useEffect, useCallback } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import forumService from "../services/forumService";
import { ROUTES, USER_ROLES } from "../constants";
import {
  ArrowLeft,
  MessageSquare,
  ThumbsUp,
  CheckCircle2,
  Trash2,
  Edit3,
  Flag,
  Share2,
  AlertCircle,
  Eye,
  X,
  Send,
  GraduationCap,
  Shield,
} from "lucide-react";

export const ForumPostDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user, isAuthenticated } = useAuth();

  const [post, setPost] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Comment submission state
  const [commentText, setCommentText] = useState("");
  const [commentSubmitting, setCommentSubmitting] = useState(false);
  const [commentError, setCommentError] = useState(null);

  // Edit post state
  const [isEditingPost, setIsEditingPost] = useState(false);
  const [editTitle, setEditTitle] = useState("");
  const [editContent, setEditContent] = useState("");
  const [editPostSubmitting, setEditPostSubmitting] = useState(false);

  // Edit comment state
  const [editingCommentId, setEditingCommentId] = useState(null);
  const [editCommentText, setEditCommentText] = useState("");

  // Report modal state
  const [reportTarget, setReportTarget] = useState(null); // { post_id or comment_id }
  const [reportReason, setReportReason] = useState("Spam");
  const [reportDetails, setReportDetails] = useState("");
  const [reportSubmitting, setReportSubmitting] = useState(false);
  const [reportSuccess, setReportSuccess] = useState(false);

  const fetchPostDetail = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await forumService.getPostById(id);
      if (res?.data) {
        setPost(res.data);
        setEditTitle(res.data.title);
        setEditContent(res.data.content);
      }
    } catch (err) {
      console.error("Failed to load post detail:", err);
      setError("Discussion post not found or has been removed.");
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchPostDetail();
  }, [fetchPostDetail]);

  const handlePostLike = async () => {
    if (!isAuthenticated) {
      navigate(ROUTES.LOGIN);
      return;
    }
    try {
      const res = await forumService.togglePostLike(post.id);
      if (res?.data) {
        setPost((prev) => ({
          ...prev,
          is_liked_by_me: res.data.is_liked,
          likes_count: res.data.likes_count,
        }));
      }
    } catch (err) {
      console.error("Failed to toggle like:", err);
    }
  };

  const handleCommentLike = async (commentId) => {
    if (!isAuthenticated) {
      navigate(ROUTES.LOGIN);
      return;
    }
    try {
      const res = await forumService.toggleCommentLike(commentId);
      if (res?.data) {
        setPost((prev) => ({
          ...prev,
          comments: prev.comments.map((c) =>
            c.id === commentId
              ? {
                  ...c,
                  is_liked_by_me: res.data.is_liked,
                  likes_count: res.data.likes_count,
                }
              : c
          ),
        }));
      }
    } catch (err) {
      console.error("Failed to toggle comment like:", err);
    }
  };

  const handleAddComment = async (e) => {
    e.preventDefault();
    if (!isAuthenticated) {
      navigate(ROUTES.LOGIN);
      return;
    }
    if (!commentText.trim()) return;

    try {
      setCommentSubmitting(true);
      setCommentError(null);
      const res = await forumService.addComment(post.id, {
        content: commentText.trim(),
      });
      if (res?.data) {
        setPost((prev) => ({
          ...prev,
          replies_count: prev.replies_count + 1,
          has_instructor_reply: prev.has_instructor_reply || res.data.is_instructor_reply,
          instructor_reply_name:
            res.data.is_instructor_reply && !prev.instructor_reply_name
              ? res.data.author.name
              : prev.instructor_reply_name,
          comments: [...prev.comments, res.data],
        }));
        setCommentText("");
      }
    } catch (err) {
      setCommentError(err.response?.data?.message || "Failed to submit comment.");
    } finally {
      setCommentSubmitting(false);
    }
  };

  const handleUpdatePost = async (e) => {
    e.preventDefault();
    if (!editTitle.trim() || !editContent.trim()) return;

    try {
      setEditPostSubmitting(true);
      const res = await forumService.updatePost(post.id, {
        title: editTitle.trim(),
        content: editContent.trim(),
      });
      if (res?.data) {
        setPost((prev) => ({
          ...prev,
          title: res.data.title,
          content: res.data.content,
        }));
        setIsEditingPost(false);
      }
    } catch (err) {
      alert(err.response?.data?.message || "Failed to update discussion.");
    } finally {
      setEditPostSubmitting(false);
    }
  };

  const handleDeletePost = async () => {
    if (!window.confirm("Are you sure you want to delete this discussion post?")) return;
    try {
      await forumService.deletePost(post.id);
      navigate(ROUTES.FORUM);
    } catch (err) {
      alert(err.response?.data?.message || "Failed to delete post.");
    }
  };

  const handleUpdateComment = async (commentId) => {
    if (!editCommentText.trim()) return;
    try {
      const res = await forumService.updateComment(commentId, {
        content: editCommentText.trim(),
      });
      if (res?.data) {
        setPost((prev) => ({
          ...prev,
          comments: prev.comments.map((c) =>
            c.id === commentId ? { ...c, content: res.data.content } : c
          ),
        }));
        setEditingCommentId(null);
      }
    } catch (err) {
      alert(err.response?.data?.message || "Failed to update comment.");
    }
  };

  const handleDeleteComment = async (commentId) => {
    if (!window.confirm("Delete this comment?")) return;
    try {
      await forumService.deleteComment(commentId);
      fetchPostDetail();
    } catch (err) {
      alert(err.response?.data?.message || "Failed to delete comment.");
    }
  };

  const handleReportSubmit = async (e) => {
    e.preventDefault();
    if (!isAuthenticated) {
      navigate(ROUTES.LOGIN);
      return;
    }
    try {
      setReportSubmitting(true);
      await forumService.createReport({
        post_id: reportTarget.post_id,
        comment_id: reportTarget.comment_id,
        reason: reportReason,
        details: reportDetails.trim() || undefined,
      });
      setReportSuccess(true);
      setTimeout(() => {
        setReportSuccess(false);
        setReportTarget(null);
        setReportDetails("");
      }, 1500);
    } catch (err) {
      alert(err.response?.data?.message || "Failed to submit report.");
    } finally {
      setReportSubmitting(false);
    }
  };

  const formatRelativeTime = (dateStr) => {
    if (!dateStr) return "";
    const date = new Date(dateStr);
    const now = new Date();
    const diffSeconds = Math.floor((now - date) / 1000);

    if (diffSeconds < 60) return "just now";
    const diffMinutes = Math.floor(diffSeconds / 60);
    if (diffMinutes < 60) return `${diffMinutes}m ago`;
    const diffHours = Math.floor(diffMinutes / 60);
    if (diffHours < 24) return `${diffHours} hours ago`;
    const diffDays = Math.floor(diffHours / 24);
    if (diffDays === 1) return "Yesterday";
    if (diffDays < 7) return `${diffDays} days ago`;
    return date.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 py-12">
        <div className="max-w-4xl mx-auto px-4 space-y-4 animate-pulse">
          <div className="h-6 bg-slate-200 rounded w-28" />
          <div className="h-10 bg-slate-200 rounded w-3/4" />
          <div className="h-40 bg-white rounded-xl border border-slate-200" />
        </div>
      </div>
    );
  }

  if (error || !post) {
    return (
      <div className="min-h-screen bg-slate-50 py-16">
        <div className="max-w-md mx-auto px-4 text-center space-y-4">
          <AlertCircle className="w-12 h-12 text-slate-400 mx-auto" />
          <h2 className="text-xl font-bold text-slate-900 font-heading">Discussion Not Found</h2>
          <p className="text-slate-500 text-sm">{error || "This post may have been removed."}</p>
          <Link
            to={ROUTES.FORUM}
            className="inline-flex items-center gap-1.5 px-4 py-2 bg-slate-900 text-white rounded-lg text-xs font-semibold"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back to Forum</span>
          </Link>
        </div>
      </div>
    );
  }

  const isAuthor = user && user.id === post.author.id;
  const isAdmin = user && user.role === USER_ROLES.ADMIN;
  const isInstructor = user && user.role === USER_ROLES.INSTRUCTOR;
  const canManagePost = isAuthor || isAdmin;

  return (
    <div className="min-w-0 bg-slate-50 min-h-screen py-8 text-slate-800">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 space-y-6">
        {/* Navigation Breadcrumb */}
        <div>
          <Link
            to={ROUTES.FORUM}
            className="inline-flex items-center gap-1.5 text-xs font-medium text-slate-500 hover:text-slate-900 transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back to Forum Activities</span>
          </Link>
        </div>

        {/* Main Post Card */}
        <div className="bg-white rounded-xl border border-slate-200/80 p-6 shadow-xs space-y-4">
          {/* Header row */}
          <div className="flex items-start justify-between gap-4">
            <span className="px-2.5 py-1 bg-slate-100 text-slate-700 text-xs font-medium rounded-md">
              {post.category_name}
            </span>
            <div className="flex items-center gap-2 text-xs text-slate-400">
              <span className="flex items-center gap-1">
                <Eye className="w-3.5 h-3.5" />
                <span>{post.views_count} views</span>
              </span>
            </div>
          </div>

          {/* Title & Edit mode */}
          {isEditingPost ? (
            <form onSubmit={handleUpdatePost} className="space-y-3">
              <input
                type="text"
                required
                value={editTitle}
                onChange={(e) => setEditTitle(e.target.value)}
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-base font-semibold text-slate-900"
              />
              <textarea
                rows={6}
                required
                value={editContent}
                onChange={(e) => setEditContent(e.target.value)}
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-800"
              />
              <div className="flex items-center gap-2">
                <button
                  type="submit"
                  disabled={editPostSubmitting}
                  className="px-4 py-1.5 bg-slate-900 text-white rounded-lg text-xs font-semibold"
                >
                  {editPostSubmitting ? "Saving..." : "Save"}
                </button>
                <button
                  type="button"
                  onClick={() => setIsEditingPost(false)}
                  className="px-3 py-1.5 border border-slate-200 text-slate-600 rounded-lg text-xs font-medium"
                >
                  Cancel
                </button>
              </div>
            </form>
          ) : (
            <h1 className="text-xl sm:text-2xl font-bold text-slate-900 leading-snug font-heading">
              {post.title}
            </h1>
          )}

          {/* Instructor Reply Banner if exists */}
          {post.has_instructor_reply && (
            <div className="flex items-center justify-between px-3.5 py-2.5 bg-emerald-50 border border-emerald-100 rounded-lg text-emerald-800 text-xs font-medium">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                <span>
                  {post.instructor_reply_name
                    ? `${post.instructor_reply_name} answered this discussion`
                    : "Verified instructor answered"}
                </span>
              </div>
              <span className="font-semibold text-[11px] text-emerald-700 uppercase tracking-wider bg-emerald-100/60 px-2 py-0.5 rounded-full">
                Instructor Reply
              </span>
            </div>
          )}

          {/* Author info row */}
          <div className="flex items-center justify-between py-2 border-y border-slate-100 text-xs">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-full bg-slate-800 text-white flex items-center justify-center font-bold text-sm uppercase overflow-hidden">
                {post.author.avatar_url ? (
                  <img
                    src={post.author.avatar_url}
                    alt={post.author.name}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  post.author.name.charAt(0)
                )}
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-slate-900">{post.author.name}</span>
                  {post.author.role === USER_ROLES.INSTRUCTOR && (
                    <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded">
                      <GraduationCap className="w-3 h-3" />
                      Instructor
                    </span>
                  )}
                  {post.author.role === USER_ROLES.ADMIN && (
                    <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-purple-700 bg-purple-50 px-2 py-0.5 rounded">
                      <Shield className="w-3 h-3" />
                      Admin
                    </span>
                  )}
                </div>
                <span className="text-slate-400">{formatRelativeTime(post.created_at)}</span>
              </div>
            </div>

            {/* Author / Admin Edit / Delete Actions */}
            {canManagePost && !isEditingPost && (
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setIsEditingPost(true)}
                  className="p-1.5 text-slate-400 hover:text-slate-800 transition-colors"
                  title="Edit post"
                >
                  <Edit3 className="w-4 h-4" />
                </button>
                <button
                  type="button"
                  onClick={handleDeletePost}
                  className="p-1.5 text-slate-400 hover:text-red-600 transition-colors"
                  title="Delete post"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            )}
          </div>

          {/* Post Content */}
          {!isEditingPost && (
            <div className="prose prose-slate max-w-none text-slate-800 text-sm leading-relaxed whitespace-pre-line py-2">
              {post.content}
            </div>
          )}

          {/* Footer Actions Row */}
          <div className="flex items-center justify-between pt-3 border-t border-slate-100 text-xs">
            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={handlePostLike}
                className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border transition-all ${
                  post.is_liked_by_me
                    ? "border-blue-200 bg-blue-50 text-blue-600 font-semibold"
                    : "border-slate-200 text-slate-600 hover:bg-slate-50"
                }`}
              >
                <ThumbsUp
                  className={`w-3.5 h-3.5 ${
                    post.is_liked_by_me ? "fill-blue-600 text-blue-600" : "text-slate-400"
                  }`}
                />
                <span>{post.likes_count} Likes</span>
              </button>

              <span className="inline-flex items-center gap-1.5 text-slate-500">
                <MessageSquare className="w-3.5 h-3.5" />
                <span>{post.replies_count} Replies</span>
              </span>
            </div>

            {/* Report post */}
            {isAuthenticated && !isAuthor && (
              <button
                type="button"
                onClick={() => {
                  setReportTarget({ post_id: post.id });
                  setReportReason("Spam");
                  setReportDetails("");
                }}
                className="text-slate-400 hover:text-amber-600 text-xs flex items-center gap-1 transition-colors"
              >
                <Flag className="w-3.5 h-3.5" />
                <span>Report</span>
              </button>
            )}
          </div>
        </div>

        {/* Discussion Replies Section */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-slate-900 font-heading">
              Discussion Replies ({post.comments?.length || 0})
            </h2>
          </div>

          {/* Add Reply Box */}
          <div className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-xs space-y-3">
            {isInstructor && (
              <div className="flex items-center gap-2 text-xs font-semibold text-emerald-800 bg-emerald-50 px-3 py-1.5 rounded-lg border border-emerald-100">
                <GraduationCap className="w-4 h-4 text-emerald-600" />
                <span>
                  Posting as verified Instructor. Your response will display the Instructor Reply badge.
                </span>
              </div>
            )}

            {commentError && (
              <div className="p-3 bg-red-50 border border-red-200 text-red-700 text-xs rounded-lg flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{commentError}</span>
              </div>
            )}

            {isAuthenticated ? (
              <form onSubmit={handleAddComment} className="space-y-3">
                <textarea
                  rows={4}
                  required
                  placeholder="Join the discussion or share helpful guidance..."
                  value={commentText}
                  onChange={(e) => setCommentText(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-slate-900 resize-y"
                />
                <div className="flex items-center justify-end">
                  <button
                    type="submit"
                    disabled={commentSubmitting || !commentText.trim()}
                    className="inline-flex items-center gap-1.5 px-4 py-2 bg-emerald-950 hover:bg-emerald-900 text-white rounded-lg text-xs font-semibold transition-all disabled:opacity-40"
                  >
                    <Send className="w-3.5 h-3.5" />
                    <span>{commentSubmitting ? "Posting..." : "Post Reply"}</span>
                  </button>
                </div>
              </form>
            ) : (
              <div className="py-4 text-center space-y-2">
                <p className="text-sm text-slate-500">You must be logged in to reply.</p>
                <Link
                  to={ROUTES.LOGIN}
                  className="inline-block px-4 py-2 bg-slate-900 text-white text-xs font-semibold rounded-lg"
                >
                  Log In to Reply
                </Link>
              </div>
            )}
          </div>

          {/* Comments List */}
          <div className="space-y-3">
            {post.comments?.length === 0 ? (
              <div className="bg-white rounded-xl border border-slate-200/80 p-8 text-center text-slate-500 text-sm">
                No replies yet. Be the first to provide insight!
              </div>
            ) : (
              post.comments?.map((comment) => {
                const isCommentAuthor = user && user.id === comment.author.id;
                const canManageComment = isCommentAuthor || isAdmin;

                return (
                  <div
                    key={comment.id}
                    className={`bg-white rounded-xl border p-5 shadow-xs space-y-3 transition-colors ${
                      comment.is_instructor_reply
                        ? "border-emerald-200/90 bg-emerald-50/20"
                        : "border-slate-200/80"
                    }`}
                  >
                    {/* Instructor Badge header on comment */}
                    {comment.is_instructor_reply && (
                      <div className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-emerald-100/70 text-emerald-800 rounded-md text-[11px] font-semibold">
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                        <span>Verified Instructor Answer</span>
                      </div>
                    )}

                    {/* Author row */}
                    <div className="flex items-center justify-between text-xs">
                      <div className="flex items-center gap-2.5">
                        <div className="w-7 h-7 rounded-full bg-slate-800 text-white flex items-center justify-center font-bold text-xs uppercase overflow-hidden">
                          {comment.author.avatar_url ? (
                            <img
                              src={comment.author.avatar_url}
                              alt={comment.author.name}
                              className="w-full h-full object-cover"
                            />
                          ) : (
                            comment.author.name.charAt(0)
                          )}
                        </div>
                        <span className="font-semibold text-slate-900">{comment.author.name}</span>
                        {comment.author.role === USER_ROLES.INSTRUCTOR && (
                          <span className="text-[10px] font-semibold text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded">
                            Instructor
                          </span>
                        )}
                        <span>·</span>
                        <span className="text-slate-400">{formatRelativeTime(comment.created_at)}</span>
                      </div>

                      {canManageComment && editingCommentId !== comment.id && (
                        <div className="flex items-center gap-1.5">
                          <button
                            type="button"
                            onClick={() => {
                              setEditingCommentId(comment.id);
                              setEditCommentText(comment.content);
                            }}
                            className="p-1 text-slate-400 hover:text-slate-700"
                            title="Edit comment"
                          >
                            <Edit3 className="w-3.5 h-3.5" />
                          </button>
                          <button
                            type="button"
                            onClick={() => handleDeleteComment(comment.id)}
                            className="p-1 text-slate-400 hover:text-red-600"
                            title="Delete comment"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      )}
                    </div>

                    {/* Comment content */}
                    {editingCommentId === comment.id ? (
                      <div className="space-y-2">
                        <textarea
                          rows={3}
                          value={editCommentText}
                          onChange={(e) => setEditCommentText(e.target.value)}
                          className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-800"
                        />
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => handleUpdateComment(comment.id)}
                            className="px-3 py-1 bg-slate-900 text-white rounded text-xs font-semibold"
                          >
                            Save
                          </button>
                          <button
                            onClick={() => setEditingCommentId(null)}
                            className="px-3 py-1 border border-slate-200 text-slate-600 rounded text-xs font-medium"
                          >
                            Cancel
                          </button>
                        </div>
                      </div>
                    ) : (
                      <p className="text-slate-800 text-sm whitespace-pre-line leading-relaxed">
                        {comment.content}
                      </p>
                    )}

                    {/* Actions row */}
                    <div className="flex items-center justify-between pt-1 text-xs text-slate-500">
                      <button
                        type="button"
                        onClick={() => handleCommentLike(comment.id)}
                        className={`inline-flex items-center gap-1 hover:text-blue-600 transition-colors ${
                          comment.is_liked_by_me ? "text-blue-600 font-semibold" : ""
                        }`}
                      >
                        <ThumbsUp
                          className={`w-3.5 h-3.5 ${
                            comment.is_liked_by_me ? "fill-blue-600 text-blue-600" : "text-slate-400"
                          }`}
                        />
                        <span>{comment.likes_count} Likes</span>
                      </button>

                      {isAuthenticated && !isCommentAuthor && (
                        <button
                          type="button"
                          onClick={() => {
                            setReportTarget({ comment_id: comment.id });
                            setReportReason("Spam");
                            setReportDetails("");
                          }}
                          className="text-slate-400 hover:text-amber-600 flex items-center gap-1"
                        >
                          <Flag className="w-3 h-3" />
                          <span>Report</span>
                        </button>
                      )}
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>

      {/* Report Modal */}
      {reportTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4 backdrop-blur-xs">
          <div className="bg-white rounded-xl max-w-md w-full p-6 shadow-xl border border-slate-200 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <h2 className="text-base font-bold text-slate-900 font-heading">
                Report Inappropriate Content
              </h2>
              <button
                onClick={() => setReportTarget(null)}
                className="text-slate-400 hover:text-slate-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {reportSuccess ? (
              <div className="py-6 text-center space-y-2">
                <CheckCircle2 className="w-10 h-10 text-emerald-600 mx-auto" />
                <p className="font-semibold text-slate-800 text-sm">
                  Report submitted successfully
                </p>
                <p className="text-xs text-slate-500">
                  Our moderators will review this content.
                </p>
              </div>
            ) : (
              <form onSubmit={handleReportSubmit} className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Reason for report *
                  </label>
                  <select
                    value={reportReason}
                    onChange={(e) => setReportReason(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-slate-900"
                  >
                    <option value="Spam">Spam or unwanted advertising</option>
                    <option value="Harassment / Inappropriate behavior">
                      Harassment or inappropriate behavior
                    </option>
                    <option value="Misinformation">Misinformation or false guidance</option>
                    <option value="Academic Dishonesty">
                      Academic dishonesty / Cheating / Plagiarism
                    </option>
                    <option value="Off-topic / Other">Off-topic or other concern</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Additional details (optional)
                  </label>
                  <textarea
                    rows={3}
                    placeholder="Describe why this content violates community guidelines..."
                    value={reportDetails}
                    onChange={(e) => setReportDetails(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-slate-900 resize-none"
                  />
                </div>

                <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-100">
                  <button
                    type="button"
                    onClick={() => setReportTarget(null)}
                    className="px-4 py-2 border border-slate-200 text-slate-700 rounded-lg text-xs font-medium hover:bg-slate-50"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={reportSubmitting}
                    className="px-5 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-xs font-semibold transition-all disabled:opacity-50"
                  >
                    {reportSubmitting ? "Submitting..." : "Submit Report"}
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default ForumPostDetail;
