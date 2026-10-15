import api from "./api";

/**
 * Service handling subscription tiers, entitlements, plan activations, and transaction invoices.
 * Matches Sprint 3 SKL-19 and SKL-21 specifications.
 */
export const subscriptionService = {
  /**
   * Fetch all active subscription tiers (Free, Pro Monthly, Pro Yearly).
   */
  getPlans: async () => {
    const response = await api.get("/subscriptions/plans");
    return response.data;
  },

  /**
   * Get the current authenticated user's active subscription.
   */
  getMySubscription: async () => {
    const response = await api.get("/subscriptions/my-subscription");
    return response.data;
  },

  /**
   * Select, subscribe, or switch subscription plan.
   * @param {Object} data - { plan_code, plan_id, payment_gateway, payment_method }
   */
  selectPlan: async (data) => {
    const response = await api.post("/subscriptions/select-plan", data);
    return response.data;
  },

  /**
   * Fetch current user's entitlement permissions (is_pro, can_access_premium_mock_tests, etc.).
   */
  getEntitlements: async () => {
    const response = await api.get("/subscriptions/entitlements");
    return response.data;
  },

  /**
   * Cancel paid subscription and revert to Free tier.
   * @param {Object} [data] - { reason }
   */
  cancelSubscription: async (data = {}) => {
    const response = await api.post("/subscriptions/cancel", data);
    return response.data;
  },

  /**
   * Fetch deep advanced analytics (Pro-only feature).
   */
  getAdvancedAnalytics: async () => {
    const response = await api.get("/subscriptions/analytics/advanced");
    return response.data;
  },

  /**
   * Get authenticated user's personal transaction ledger.
   */
  getMyTransactions: async () => {
    const response = await api.get("/transactions/my-history");
    return response.data;
  },

  /**
   * Idempotent verification for a transaction reference.
   * @param {Object} data - { transaction_ref, status }
   */
  verifyTransaction: async (data) => {
    const response = await api.post("/transactions/verify", data);
    return response.data;
  },

  /**
   * Download or view tax invoice for a given transaction.
   * @param {number|string} transactionId
   */
  getInvoice: async (transactionId) => {
    const response = await api.get(`/transactions/${transactionId}/invoice`);
    return response.data;
  },

  /**
   * Platform-wide transactions audit (Admin-only).
   */
  getAdminTransactions: async (params = {}) => {
    const response = await api.get("/admin/transactions", { params });
    return response.data;
  },
};

export default subscriptionService;
