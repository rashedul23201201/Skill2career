import React, { useState, useEffect, useCallback } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import forumService from "../services/forumService";
import { ROUTES, USER_ROLES } from "../constants";
import {
  Search,
  Plus,
  MessageSquare,
  ThumbsUp,
  ShieldCheck,
  CheckCircle2,
  Trash2,
  Edit3,
  Flag,
  X,
  AlertCircle,
  HelpCircle,
  Check,
} from "lucide-react";

export const Forum = () => {
  const { user, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  const [categories, setCategories] = useState([]);
  const [posts, setPosts] = useState([]);
  const [categoryCounts, setCategoryCounts] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [activeCategory, setActiveCategory] = useState(
    searchParams.get("category_id") ? Number(searchParams.get("category_id")) : null
  );
  const [searchInput, setSearchInput] = useState(searchParams.get("search") || "");
  const [appliedSearch, setAppliedSearch] = useState(searchParams.get("search") || "");

  const [page, setPage] = useState(Number(searchParams.get("page")) || 1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalPosts, setTotalPosts] = useState(0);

  // Modals state
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [createSubmitting, setCreateSubmitting] = useState(false);
  const [createForm, setCreateForm] = useState({
    title: "",
    category_id: "",
    content: "",
  });
  const [createError, setCreateError] = useState(null);

  // Report modal state
  const [reportingTarget, setReportingTarget] = useState(null); // { post_id: ... }
  const [reportReason, setReportReason] = useState("Spam");
  const [reportDetails, setReportDetails] = useState("");
  const [reportSubmitting, setReportSubmitting] = useState(false);
  const [reportSuccess, setReportSuccess] = useState(false);

  // Edit post modal state
  const [editingPost, setEditingPost] = useState(null);
  const [editForm, setEditForm] = useState({ title: "", category_id: "", content: "" });
  const [editSubmitting, setEditSubmitting] = useState(false);

  const fetchCategories = useCallback(async () => {
    try {
      const res = await forumService.getCategories();
      if (res?.data) {
        setCategories(res.data);
      }
    } catch (err) {
      console.error("Failed to fetch categories:", err);
    }
  }, []);

  const fetchPosts = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const params = {
        page,
        size: 10,
      };
      if (activeCategory) {
        params.category_id = activeCategory;
      }
      if (appliedSearch.trim()) {
        params.search = appliedSearch.trim();
      }

      const res = await forumService.getPosts(params);
      if (res?.data) {
        setPosts(res.data.items || []);
        setTotalPages(res.data.total_pages || 1);
        setTotalPosts(res.data.total || 0);
        if (res.data.category_counts) {
          setCategoryCounts(res.data.category_counts);
        }
      }
    } catch (err) {
      console.error("Failed to load forum discussions:", err);
      setError("Unable to load discussions. Please try again.");
    } finally {
      setLoading(false);
    }
  }, [page, activeCategory, appliedSearch]);

  useEffect(() => {
    fetchCategories();
  }, [fetchCategories]);

  useEffect(() => {
    fetchPosts();
  }, [fetchPosts]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setPage(1);
    setAppliedSearch(searchInput);
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      if (searchInput.trim()) {
        next.set("search", searchInput.trim());
      } else {
        next.delete("search");
      }
      next.set("page", "1");
      return next;
    });
  };

  const handleCategorySelect = (catId) => {
    setActiveCategory(catId);
    setPage(1);
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      if (catId) {
        next.set("category_id", catId);
      } else {
        next.delete("category_id");
      }
      next.set("page", "1");
      return next;
    });
  };

  const handlePageChange = (newPage) => {
    if (newPage < 1 || newPage > totalPages) return;
    setPage(newPage);
    window.scrollTo({ top: 0, behavior: "smooth" });
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      next.set("page", String(newPage));
      return next;
    });
  };

  const handleLikeToggle = async (e, postId) => {
    e.stopPropagation();
    if (!isAuthenticated) {
      navigate(ROUTES.LOGIN);
      return;
    }
    try {
      const res = await forumService.togglePostLike(postId);
      if (res?.data) {
        setPosts((prev) =>
          prev.map((p) =>
            p.id === postId
              ? {
                  ...p,
                  is_liked_by_me: res.data.is_liked,
                  likes_count: res.data.likes_count,
                }
              : p
          )
        );
      }
    } catch (err) {
      console.error("Failed to toggle like:", err);
    }
  };

  const handleCreateSubmit = async (e) => {
    e.preventDefault();
    if (!isAuthenticated) {
      navigate(ROUTES.LOGIN);
      return;
    }
    if (!createForm.title.trim() || !createForm.category_id || !createForm.content.trim()) {
      setCreateError("Please complete all required fields.");
      return;
    }

    try {
      setCreateSubmitting(true);
      setCreateError(null);
      await forumService.createPost({
        title: createForm.title.trim(),
        category_id: Number(createForm.category_id),
        content: createForm.content.trim(),
      });
      setShowCreateModal(false);
      setCreateForm({ title: "", category_id: "", content: "" });
      fetchPosts();
      fetchCategories();
    } catch (err) {
      setCreateError(err.response?.data?.message || "Failed to create discussion post.");
    } finally {
      setCreateSubmitting(false);
    }
  };

  const handleDeletePost = async (e, postId) => {
    e.stopPropagation();
    if (!window.confirm("Are you sure you want to delete this discussion post?")) return;
    try {
      await forumService.deletePost(postId);
      fetchPosts();
      fetchCategories();
    } catch (err) {
      alert(err.response?.data?.message || "Failed to delete post.");
    }
  };

  const handleOpenEdit = (e, post) => {
    e.stopPropagation();
    setEditingPost(post);
    setEditForm({
      title: post.title,
      category_id: String(post.category_id),
      content: post.content,
    });
  };

  const handleEditSubmit = async (e) => {
    e.preventDefault();
    if (!editForm.title.trim() || !editForm.content.trim()) return;

    try {
      setEditSubmitting(true);
      await forumService.updatePost(editingPost.id, {
        title: editForm.title.trim(),
        category_id: Number(editForm.category_id),
        content: editForm.content.trim(),
      });
      setEditingPost(null);
      fetchPosts();
    } catch (err) {
      alert(err.response?.data?.message || "Failed to update post.");
    } finally {
      setEditSubmitting(false);
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
        post_id: reportingTarget.id,
        reason: reportReason,
        details: reportDetails.trim() || undefined,
      });
      setReportSuccess(true);
      setTimeout(() => {
        setReportSuccess(false);
        setReportingTarget(null);
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
    return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
  };

  const totalTopicsCount =
    categoryCounts["All"] ||
    categories.reduce((acc, c) => acc + (c.posts_count || 0), 0) ||
    totalPosts;

  return (
    <div className="min-w-0 bg-slate-50 min-h-screen py-8 text-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-6">
        {/* Header Section matching Forum.png */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900 font-heading">
              Forum Activities
            </h1>
            <p className="text-slate-500 text-sm mt-1">
              Ask questions, share knowledge, and learn from the SKILL2CAREER community.
            </p>
          </div>
          <button
            onClick={() => {
              if (!isAuthenticated) {
                navigate(ROUTES.LOGIN);
              } else {
                setCreateError(null);
                setCreateForm({
                  title: "",
                  category_id: categories[0]?.id ? String(categories[0].id) : "",
                  content: "",
                });
                setShowCreateModal(true);
              }
            }}
            className="inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-lg bg-emerald-950 hover:bg-emerald-900 text-white font-medium text-sm transition-all shadow-sm active:scale-95"
          >
            <Plus className="w-4 h-4" />
            <span>Create Post</span>
          </button>
        </div>

        {/* Search Bar matching Forum.png */}
        <form onSubmit={handleSearchSubmit} className="flex gap-2">
          <div className="relative flex-1">
            <Search className="w-5 h-5 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder="Search discussions by topic, keyword, or author..."
              className="w-full pl-11 pr-4 py-2.5 bg-white border border-slate-200 rounded-lg text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-900 focus:border-transparent transition-all shadow-xs"
            />
          </div>
          <button
            type="submit"
            className="px-6 py-2.5 bg-slate-900 hover:bg-slate-800 text-white text-sm font-medium rounded-lg transition-all shadow-xs"
          >
            Search
          </button>
        </form>

        {/* Main Content Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 items-start">
          {/* Left Sidebar */}
          <div className="space-y-6 lg:col-span-1">
            {/* Categories Card */}
            <div className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-xs">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                <h2 className="font-bold text-slate-900 text-sm">Categories</h2>
                <span className="text-[11px] font-semibold tracking-wider text-slate-400 uppercase">
                  {totalTopicsCount} TOPICS
                </span>
              </div>

              <div className="mt-3 space-y-1">
                {/* All Discussions Option */}
                <button
                  onClick={() => handleCategorySelect(null)}
                  className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm transition-colors ${
                    activeCategory === null
                      ? "bg-slate-100 font-semibold text-slate-900"
                      : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                  }`}
                >
                  <div className="flex items-center gap-2.5">
                    <span className="w-2 h-2 rounded-full bg-emerald-500" />
                    <span>All Discussions</span>
                  </div>
                  <span className="text-xs text-slate-500 font-medium">
                    {categoryCounts["All"] || totalTopicsCount}
                  </span>
                </button>

                {/* Individual Categories */}
                {categories.map((cat) => {
                  const isActive = activeCategory === cat.id;
                  const count = categoryCounts[String(cat.id)] ?? cat.posts_count ?? 0;
                  return (
                    <button
                      key={cat.id}
                      onClick={() => handleCategorySelect(cat.id)}
                      className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm transition-colors ${
                        isActive
                          ? "bg-slate-100 font-semibold text-slate-900"
                          : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                      }`}
                    >
                      <span className="truncate pr-2">{cat.name}</span>
                      <span className="text-xs text-slate-500 font-medium">{count}</span>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Academic Guidelines Card matching Forum.png */}
            <div className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-xs">
              <div className="flex items-center gap-2 text-emerald-600 font-bold text-sm mb-1.5">
                <ShieldCheck className="w-4 h-4 text-emerald-600" />
                <span>Academic Guidelines</span>
              </div>
              <p className="text-xs text-slate-500 leading-relaxed">
                Keep posts structured and focused on engineering curricula and career tracks.
              </p>
            </div>
          </div>

          {/* Right Post Feed */}
          <div className="lg:col-span-3 space-y-4">
            {loading ? (
              <div className="space-y-4">
                {[1, 2, 3].map((n) => (
                  <div
                    key={n}
                    className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-xs animate-pulse space-y-3"
                  >
                    <div className="h-5 bg-slate-200 rounded w-3/4" />
                    <div className="h-4 bg-slate-100 rounded w-1/2" />
                    <div className="h-4 bg-slate-100 rounded w-1/4" />
                  </div>
                ))}
              </div>
            ) : error ? (
              <div className="bg-white rounded-xl border border-red-200 p-8 text-center text-red-600 space-y-2">
                <AlertCircle className="w-8 h-8 mx-auto text-red-500" />
                <p className="font-semibold">{error}</p>
                <button
                  onClick={fetchPosts}
                  className="px-4 py-2 bg-slate-900 text-white text-xs font-medium rounded-lg"
                >
                  Retry
                </button>
              </div>
            ) : posts.length === 0 ? (
              <div className="bg-white rounded-xl border border-slate-200/80 p-12 text-center space-y-3">
                <MessageSquare className="w-10 h-10 mx-auto text-slate-300" />
                <h3 className="text-base font-semibold text-slate-800">No discussions found</h3>
                <p className="text-sm text-slate-500 max-w-sm mx-auto">
                  {appliedSearch
                    ? `No discussions match "${appliedSearch}". Try searching for another topic.`
                    : "Be the first to start a conversation in this category!"}
                </p>
                <button
                  onClick={() => setShowCreateModal(true)}
                  className="inline-flex items-center gap-1.5 px-4 py-2 bg-emerald-950 text-white text-xs font-semibold rounded-lg hover:bg-emerald-900 transition-colors"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>Start Discussion</span>
                </button>
              </div>
            ) : (
              posts.map((post) => {
                const isAuthor = user && user.id === post.author.id;
                const isAdmin = user && user.role === USER_ROLES.ADMIN;
                const canManagePost = isAuthor || isAdmin;

                return (
                  <div
                    key={post.id}
                    onClick={() => navigate(`/forum/posts/${post.id}`)}
                    className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-xs hover:border-slate-300 transition-all cursor-pointer group space-y-3"
                  >
                    {/* Top Row: Title + Category Badge */}
                    <div className="flex items-start justify-between gap-4">
                      <h2 className="text-base sm:text-lg font-semibold text-slate-900 group-hover:text-blue-600 transition-colors leading-snug">
                        {post.title}
                      </h2>
                      <span className="shrink-0 px-2.5 py-1 bg-slate-100 text-slate-700 text-xs font-medium rounded-md">
                        {post.category_name}
                      </span>
                    </div>

                    {/* Instructor Reply Banner matching Forum.png */}
                    {post.has_instructor_reply && (
                      <div className="flex items-center justify-between px-3.5 py-2 bg-emerald-50/90 border border-emerald-100 rounded-lg text-emerald-800 text-xs font-medium">
                        <div className="flex items-center gap-1.5">
                          <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                          <span>
                            {post.instructor_reply_name
                              ? `${post.instructor_reply_name} answered`
                              : "Instructor answered"}
                          </span>
                        </div>
                        <span className="font-semibold text-[11px] text-emerald-700 uppercase tracking-wider">
                          Instructor Reply
                        </span>
                      </div>
                    )}

                    {/* Bottom Row: Author details + Replies / Likes Counters */}
                    <div className="flex flex-wrap items-center justify-between gap-3 pt-1 text-xs text-slate-500">
                      <div className="flex items-center gap-2">
                        {/* Author Avatar circle */}
                        <div className="w-7 h-7 rounded-full bg-slate-800 text-white flex items-center justify-center font-bold text-xs uppercase overflow-hidden">
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
                        <span className="font-medium text-slate-800">{post.author.name}</span>
                        <span>·</span>
                        <span>{formatRelativeTime(post.created_at)}</span>
                      </div>

                      <div className="flex items-center gap-4">
                        {/* Reply count */}
                        <div className="flex items-center gap-1.5">
                          <MessageSquare className="w-4 h-4 text-slate-400" />
                          <span>{post.replies_count} Replies</span>
                        </div>

                        {/* Interactive Likes count button */}
                        <button
                          type="button"
                          onClick={(e) => handleLikeToggle(e, post.id)}
                          className={`flex items-center gap-1.5 hover:text-blue-600 transition-colors ${
                            post.is_liked_by_me ? "text-blue-600 font-semibold" : ""
                          }`}
                        >
                          <ThumbsUp
                            className={`w-4 h-4 ${
                              post.is_liked_by_me ? "fill-blue-600 text-blue-600" : "text-slate-400"
                            }`}
                          />
                          <span>{post.likes_count} Likes</span>
                        </button>

                        {/* Report post button */}
                        {isAuthenticated && !isAuthor && (
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              setReportingTarget(post);
                              setReportReason("Spam");
                              setReportDetails("");
                            }}
                            title="Report post"
                            className="text-slate-400 hover:text-amber-600 transition-colors"
                          >
                            <Flag className="w-3.5 h-3.5" />
                          </button>
                        )}

                        {/* Owner / Admin actions */}
                        {canManagePost && (
                          <div className="flex items-center gap-2 pl-2 border-l border-slate-200">
                            <button
                              type="button"
                              onClick={(e) => handleOpenEdit(e, post)}
                              title="Edit post"
                              className="text-slate-400 hover:text-slate-700 transition-colors"
                            >
                              <Edit3 className="w-3.5 h-3.5" />
                            </button>
                            <button
                              type="button"
                              onClick={(e) => handleDeletePost(e, post.id)}
                              title="Delete post"
                              className="text-slate-400 hover:text-red-600 transition-colors"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })
            )}

            {/* Pagination Controls matching Forum.png */}
            {totalPages > 1 && (
              <div className="flex items-center justify-end gap-1.5 pt-4">
                <button
                  onClick={() => handlePageChange(page - 1)}
                  disabled={page <= 1}
                  className="px-3 py-1.5 text-xs font-medium rounded-md border border-slate-200 bg-white text-slate-700 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  Previous
                </button>
                {Array.from({ length: totalPages }, (_, i) => i + 1).map((p) => (
                  <button
                    key={p}
                    onClick={() => handlePageChange(p)}
                    className={`w-8 h-8 flex items-center justify-center text-xs font-medium rounded-md transition-colors ${
                      page === p
                        ? "bg-slate-900 text-white font-bold"
                        : "bg-white border border-slate-200 text-slate-700 hover:bg-slate-50"
                    }`}
                  >
                    {p}
                  </button>
                ))}
                <button
                  onClick={() => handlePageChange(page + 1)}
                  disabled={page >= totalPages}
                  className="px-3 py-1.5 text-xs font-medium rounded-md border border-slate-200 bg-white text-slate-700 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  Next
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Create Discussion Post Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4 backdrop-blur-xs">
          <div className="bg-white rounded-xl max-w-lg w-full p-6 shadow-xl border border-slate-200 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <h2 className="text-lg font-bold text-slate-900 font-heading">
                Create Discussion Post
              </h2>
              <button
                onClick={() => setShowCreateModal(false)}
                className="text-slate-400 hover:text-slate-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {createError && (
              <div className="p-3 bg-red-50 border border-red-200 text-red-700 text-xs rounded-lg flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{createError}</span>
              </div>
            )}

            <form onSubmit={handleCreateSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Topic Title *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. How should I prepare for a backend developer interview?"
                  value={createForm.title}
                  onChange={(e) => setCreateForm({ ...createForm, title: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-slate-900"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Category *
                </label>
                <select
                  required
                  value={createForm.category_id}
                  onChange={(e) => setCreateForm({ ...createForm, category_id: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-slate-900"
                >
                  <option value="">Select a category</option>
                  {categories.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Discussion Content *
                </label>
                <textarea
                  rows={6}
                  required
                  placeholder="Provide context, code snippets, or specific questions..."
                  value={createForm.content}
                  onChange={(e) => setCreateForm({ ...createForm, content: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-slate-900 resize-y"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 border border-slate-200 text-slate-700 rounded-lg text-xs font-medium hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createSubmitting}
                  className="px-5 py-2 bg-emerald-950 hover:bg-emerald-900 text-white rounded-lg text-xs font-semibold transition-all disabled:opacity-50"
                >
                  {createSubmitting ? "Publishing..." : "Publish Post"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Discussion Post Modal */}
      {editingPost && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4 backdrop-blur-xs">
          <div className="bg-white rounded-xl max-w-lg w-full p-6 shadow-xl border border-slate-200 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <h2 className="text-lg font-bold text-slate-900 font-heading">
                Edit Discussion Post
              </h2>
              <button
                onClick={() => setEditingPost(null)}
                className="text-slate-400 hover:text-slate-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleEditSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Topic Title *
                </label>
                <input
                  type="text"
                  required
                  value={editForm.title}
                  onChange={(e) => setEditForm({ ...editForm, title: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-slate-900"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Category *
                </label>
                <select
                  required
                  value={editForm.category_id}
                  onChange={(e) => setEditForm({ ...editForm, category_id: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-slate-900"
                >
                  {categories.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Content *
                </label>
                <textarea
                  rows={6}
                  required
                  value={editForm.content}
                  onChange={(e) => setEditForm({ ...editForm, content: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-slate-900 resize-y"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setEditingPost(null)}
                  className="px-4 py-2 border border-slate-200 text-slate-700 rounded-lg text-xs font-medium hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={editSubmitting}
                  className="px-5 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-xs font-semibold transition-all disabled:opacity-50"
                >
                  {editSubmitting ? "Saving..." : "Save Changes"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Report Content Modal */}
      {reportingTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4 backdrop-blur-xs">
          <div className="bg-white rounded-xl max-w-md w-full p-6 shadow-xl border border-slate-200 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <h2 className="text-base font-bold text-slate-900 font-heading">
                Report Inappropriate Content
              </h2>
              <button
                onClick={() => setReportingTarget(null)}
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
                  Our moderators will review this discussion topic.
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
                    onClick={() => setReportingTarget(null)}
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

export default Forum;
