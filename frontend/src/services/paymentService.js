import api from "./api";

/**
 * Service handling local (SSLCommerz) and global payment gateway integrations (SKL-20).
 */
export const paymentService = {
  /**
   * Initiate a payment session for a subscription plan tier.
   * @param {Object} data - { plan_id, plan_code, gateway_type, payment_method, success_url, fail_url, cancel_url }
   */
  initiatePayment: async (data) => {
    const response = await api.post("/payments/initiate", data);
    return response.data;
  },

  /**
   * Inspect current transaction status.
   * @param {string} transactionRef
   */
  getPaymentStatus: async (transactionRef) => {
    const response = await api.get(`/payments/${transactionRef}/status`);
    return response.data;
  },

  /**
   * Complete payment verification on SSLCommerz success (used in simulated/test box flow).
   * @param {Object} data - { tran_id, val_id, amount, card_type, bank_tran_id, status }
   */
  verifySSLCommerzSuccess: async (data) => {
    const response = await api.post("/payments/sslcommerz/success", data);
    return response.data;
  },

  /**
   * Report payment failure callback.
   * @param {Object} data - { tran_id, error }
   */
  reportSSLCommerzFail: async (data) => {
    const response = await api.post("/payments/sslcommerz/fail", data);
    return response.data;
  },

  /**
   * Report payment cancel callback.
   * @param {Object} data - { tran_id }
   */
  reportSSLCommerzCancel: async (data) => {
    const response = await api.post("/payments/sslcommerz/cancel", data);
    return response.data;
  },

  /**
   * Trigger Global Gateway (Stripe) webhook in test/simulation mode.
   * @param {Object} eventData - { type, data }
   */
  triggerGlobalWebhook: async (eventData) => {
    const response = await api.post("/payments/global/webhook", eventData);
    return response.data;
  },
};

export default paymentService;
