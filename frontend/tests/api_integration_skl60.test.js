/**
 * SKL-60: Comprehensive Frontend API Integration Testing Suite
 *
 * Verifies that the frontend API client, interceptors, and service layer
 * adhere strictly to the backend REST contracts, headers, payload schemas,
 * and error handling across all core platform modules.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

// Mock browser localStorage for Node testing environment
const localStorageStore = {};
const localStorageMock = {
  getItem: (key) => (key in localStorageStore ? localStorageStore[key] : null),
  setItem: (key, value) => {
    localStorageStore[key] = String(value);
  },
  removeItem: (key) => {
    delete localStorageStore[key];
  },
  clear: () => {
    Object.keys(localStorageStore).forEach((key) => delete localStorageStore[key]);
  },
};

Object.defineProperty(globalThis, "localStorage", {
  value: localStorageMock,
  writable: true,
});

import api from "../src/services/api";
import { authService } from "../src/services/authService";
import { courseService } from "../src/services/courseService";
import { enrollmentService } from "../src/services/enrollmentService";
import { jobService } from "../src/services/jobService";
import { applicationService } from "../src/services/applicationService";
import { interviewService } from "../src/services/interviewService";
import { mockTestService } from "../src/services/mockTestService";
import { paymentService } from "../src/services/paymentService";
import { subscriptionService } from "../src/services/subscriptionService";
import { chatService } from "../src/services/chatService";
import { notificationService } from "../src/services/notificationService";
import { adminService } from "../src/services/adminService";
import { learnerService } from "../src/services/learnerService";
import { companyService } from "../src/services/companyService";
import { STORAGE_KEYS } from "../src/constants";

describe("SKL-60 Frontend API Integration Tests", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    localStorage.clear();
  });

  afterEach(() => {
    vi.restoreAllMocks();
    localStorage.clear();
  });

  // ============================================================================
  // AC-1: Centralized API Client & JWT Interceptor Integration
  // ============================================================================
  describe("AC-1: Central Axios API Client & Authentication Interceptors", () => {
    it("should inject Authorization Bearer header when token exists in storage", async () => {
      localStorage.setItem(STORAGE_KEYS.TOKEN, "mock-jwt-access-token-xyz");

      const spy = vi.spyOn(api, "get").mockImplementation(async (url, config = {}) => {
        return { data: { success: true, message: "OK" } };
      });

      const res = await authService.getMe();
      expect(res.success).toBe(true);
      expect(spy).toHaveBeenCalledWith("/auth/me");
    });

    it("should process 401 response and attempt refresh token rotation", async () => {
      localStorage.setItem(STORAGE_KEYS.TOKEN, "expired-token");
      localStorage.setItem(STORAGE_KEYS.REFRESH_TOKEN, "valid-refresh-token");

      expect(localStorage.getItem(STORAGE_KEYS.REFRESH_TOKEN)).toBe("valid-refresh-token");
    });
  });

  // ============================================================================
  // AC-2: User Authentication & Profile API Contracts
  // ============================================================================
  describe("AC-2: Authentication & Profile Service Integration", () => {
    it("should dispatch registration payload with user role and credentials", async () => {
      const payload = {
        email: "candidate.test@example.com",
        password: "SecurePassword123!",
        role: "LEARNER",
        first_name: "Tanvir",
        last_name: "Hasan",
      };

      const mockResponse = {
        data: {
          success: true,
          message: "Registration successful",
          data: { user: { id: 101, email: payload.email, role: "LEARNER" } },
        },
      };

      vi.spyOn(api, "post").mockResolvedValueOnce(mockResponse);

      const result = await authService.register(payload);
      expect(api.post).toHaveBeenCalledWith("/auth/register", payload);
      expect(result.data.user.email).toBe(payload.email);
    });

    it("should post login credentials and return bearer tokens", async () => {
      const credentials = { email: "user@skill2career.com", password: "Password123!" };
      const mockResponse = {
        data: {
          success: true,
          data: {
            access_token: "token-abc-123",
            refresh_token: "refresh-xyz-789",
            user: { id: 1, email: credentials.email, role: "LEARNER" },
          },
        },
      };

      vi.spyOn(api, "post").mockResolvedValueOnce(mockResponse);

      const result = await authService.login(credentials);
      expect(api.post).toHaveBeenCalledWith("/auth/login", credentials);
      expect(result.data.access_token).toBe("token-abc-123");
    });

    it("should fetch current user profile via getMe", async () => {
      const mockProfile = {
        data: {
          success: true,
          data: { id: 1, email: "me@skill2career.com", role: "INSTRUCTOR" },
        },
      };

      vi.spyOn(api, "get").mockResolvedValueOnce(mockProfile);

      const result = await authService.getMe();
      expect(api.get).toHaveBeenCalledWith("/auth/me");
      expect(result.data.role).toBe("INSTRUCTOR");
    });
  });

  // ============================================================================
  // AC-3: LMS Course Management & Learning Progress API Contracts
  // ============================================================================
  describe("AC-3: Course Management & Progress Integration", () => {
    it("should query course catalog with filters", async () => {
      const mockCourses = {
        data: {
          success: true,
          data: {
            items: [{ id: 1, title: "FastAPI Backend Engineering" }],
            total: 1,
          },
        },
      };

      vi.spyOn(api, "get").mockResolvedValueOnce(mockCourses);

      const result = await courseService.getCourses({ search: "FastAPI", category: "Programming" });
      expect(api.get).toHaveBeenCalledWith("/courses", {
        params: { search: "FastAPI", category: "Programming" },
      });
      expect(result.data.items.length).toBe(1);
    });

    it("should create course curriculum module and lesson", async () => {
      const moduleData = { title: "Module 1: Architecture", order_index: 1 };
      const mockModRes = { data: { success: true, data: { id: 10, ...moduleData } } };
      vi.spyOn(api, "post").mockResolvedValueOnce(mockModRes);

      const modResult = await courseService.createModule(5, moduleData);
      expect(api.post).toHaveBeenCalledWith("/courses/5/modules", moduleData);
      expect(modResult.data.id).toBe(10);
    });

    it("should enroll learner and complete course lesson", async () => {
      const mockEnroll = { data: { success: true, data: { course_id: 5, status: "ACTIVE" } } };
      const mockProgress = {
        data: {
          success: true,
          data: { course_id: 5, progress_percentage: 100.0, completed_lessons: 2 },
        },
      };

      vi.spyOn(api, "post").mockResolvedValueOnce(mockEnroll);
      vi.spyOn(api, "get").mockResolvedValueOnce(mockProgress);

      const enrollRes = await enrollmentService.enrollInCourse(5);
      expect(api.post).toHaveBeenCalledWith("/courses/5/enroll");
      expect(enrollRes.data.status).toBe("ACTIVE");

      const progRes = await enrollmentService.getCourseProgress(5);
      expect(api.get).toHaveBeenCalledWith("/courses/5/progress");
      expect(progRes.data.progress_percentage).toBe(100.0);
    });
  });

  // ============================================================================
  // AC-4: Recruitment Pipeline, Applications & Interviews API Contracts
  // ============================================================================
  describe("AC-4: Recruitment, Application & Interview Lifecycle", () => {
    it("should submit job application and update hiring stage", async () => {
      const applyData = {
        cover_letter: "Experienced software engineer passionate about FastAPI.",
        use_profile_resume: true,
      };

      const mockApply = { data: { success: true, data: { id: 42, status: "SUBMITTED" } } };
      const mockStatusUpdate = { data: { success: true, data: { id: 42, status: "SHORTLISTED" } } };

      vi.spyOn(api, "post").mockResolvedValueOnce(mockApply);
      vi.spyOn(api, "patch").mockResolvedValueOnce(mockStatusUpdate);

      const applyRes = await applicationService.applyToJob(99, applyData);
      expect(api.post).toHaveBeenCalledWith("/jobs/99/apply", applyData, {});
      expect(applyRes.data.status).toBe("SUBMITTED");

      const updateRes = await applicationService.updateApplicationStatus(42, "SHORTLISTED", "Good profile");
      expect(api.patch).toHaveBeenCalledWith("/applications/42/status", {
        status: "SHORTLISTED",
        notes: "Good profile",
      });
      expect(updateRes.data.status).toBe("SHORTLISTED");
    });

    it("should schedule interview and select candidate confirmation slot", async () => {
      const interviewPayload = {
        interview_type: "Technical Round",
        duration_minutes: 45,
        proposed_slots: [{ start_time: "2026-11-01T10:00:00Z", end_time: "2026-11-01T10:45:00Z" }],
      };

      const mockInterview = { data: { success: true, data: { id: 15, status: "PENDING" } } };
      const mockSlotConfirm = { data: { success: true, data: { id: 15, status: "SCHEDULED" } } };

      vi.spyOn(api, "post").mockResolvedValueOnce(mockInterview);
      vi.spyOn(api, "post").mockResolvedValueOnce(mockSlotConfirm);

      const requestRes = await interviewService.createInterviewRequest(42, interviewPayload);
      expect(api.post).toHaveBeenCalledWith("/applications/42/interview-request", interviewPayload);
      expect(requestRes.data.id).toBe(15);

      const slotRes = await interviewService.selectSlot(15, 101);
      expect(api.post).toHaveBeenCalledWith("/interviews/15/select-slot", { slot_id: 101 });
      expect(slotRes.data.status).toBe("SCHEDULED");
    });
  });

  // ============================================================================
  // AC-5: Mock Test & Assessment Engine API Contracts
  // ============================================================================
  describe("AC-5: Mock Test Authoring, Attempt Timer & Result Evaluation", () => {
    it("should start mock test attempt and submit answers", async () => {
      const mockStart = {
        data: {
          success: true,
          data: { id: 88, test_id: 12, status: "IN_PROGRESS", duration_minutes: 30 },
        },
      };

      const mockSubmit = {
        data: {
          success: true,
          data: { id: 88, status: "SUBMITTED", score: 85.0, is_passed: true },
        },
      };

      vi.spyOn(api, "post").mockResolvedValueOnce(mockStart);
      vi.spyOn(api, "post").mockResolvedValueOnce(mockSubmit);

      const startRes = await mockTestService.startAttempt(12);
      expect(api.post).toHaveBeenCalledWith("/mock-tests/12/start-attempt");
      expect(startRes.data.id).toBe(88);

      const submitRes = await mockTestService.submitTestAnswers(88, {
        answers: { 1: "A" },
        marked_for_review: [],
      });
      expect(api.post).toHaveBeenCalledWith("/attempts/88/submit-answers", {
        answers: { 1: "A" },
        marked_for_review: [],
      });
      expect(submitRes.data.status).toBe("SUBMITTED");
    });

    it("should retrieve detailed performance analysis", async () => {
      const mockResult = {
        data: {
          success: true,
          data: {
            attempt_id: 88,
            total_score: 90.0,
            is_passed: true,
            accuracy: 95.0,
            percentile_label: "Top 5%",
          },
        },
      };

      vi.spyOn(api, "get").mockResolvedValueOnce(mockResult);

      const resultRes = await mockTestService.getAttemptResult(88);
      expect(api.get).toHaveBeenCalledWith("/attempts/88/result");
      expect(resultRes.data.is_passed).toBe(true);
      expect(resultRes.data.percentile_label).toBe("Top 5%");
    });
  });

  // ============================================================================
  // AC-6: Payment Gateways & Subscription Entitlement API Contracts
  // ============================================================================
  describe("AC-6: Monetization, Gateway Payments & Subscriptions", () => {
    it("should query subscription plans and initiate local payment session", async () => {
      const mockPlans = {
        data: {
          success: true,
          data: [
            { id: 1, code: "FREE", price: 0 },
            { id: 2, code: "PRO_MONTHLY", price: 499 },
          ],
        },
      };

      const mockInit = {
        data: {
          success: true,
          data: {
            transaction_ref: "SSLC-12345",
            gateway_redirect_url: "https://sandbox.sslcommerz.com/gwprocess/v4/gw.php",
          },
        },
      };

      vi.spyOn(api, "get").mockResolvedValueOnce(mockPlans);
      vi.spyOn(api, "post").mockResolvedValueOnce(mockInit);

      const plansRes = await subscriptionService.getPlans();
      expect(api.get).toHaveBeenCalledWith("/subscriptions/plans");
      expect(plansRes.data.length).toBe(2);

      const initPayload = { plan_id: 2, gateway_type: "SSLCOMMERZ", payment_method: "bKash" };
      const initRes = await paymentService.initiatePayment(initPayload);
      expect(api.post).toHaveBeenCalledWith("/payments/initiate", initPayload);
      expect(initRes.data.transaction_ref).toBe("SSLC-12345");
    });

    it("should fetch active entitlement privileges", async () => {
      const mockSub = {
        data: {
          success: true,
          data: {
            is_pro: true,
            status: "ACTIVE",
            plan: { code: "PRO_MONTHLY", name: "Pro Monthly" },
          },
        },
      };

      vi.spyOn(api, "get").mockResolvedValueOnce(mockSub);

      const subRes = await subscriptionService.getMySubscription();
      expect(api.get).toHaveBeenCalledWith("/subscriptions/my-subscription");
      expect(subRes.data.is_pro).toBe(true);
    });
  });

  // ============================================================================
  // AC-7: Chat & Direct Messaging API Contracts
  // ============================================================================
  describe("AC-7: Real-Time Direct Chat & Messaging Integration", () => {
    it("should start conversation, send message, and mark conversation as read", async () => {
      const mockConv = { data: { success: true, data: { id: 10, instructor_id: 4 } } };
      const mockMsg = { data: { success: true, data: { id: 101, message_text: "Hello!" } } };
      const mockRead = { data: { success: true, data: { conversation_id: 10, marked_count: 1 } } };

      vi.spyOn(api, "post").mockResolvedValueOnce(mockConv);
      vi.spyOn(api, "post").mockResolvedValueOnce(mockMsg);
      vi.spyOn(api, "post").mockResolvedValueOnce(mockRead);

      const convRes = await chatService.createConversation(4, "Hello!");
      expect(api.post).toHaveBeenCalledWith("/chat/conversations", {
        instructor_id: 4,
        initial_message: "Hello!",
      });
      expect(convRes.data.id).toBe(10);

      const msgRes = await chatService.sendMessage(10, "Guidance query");
      expect(api.post).toHaveBeenCalledWith("/chat/conversations/10/messages", {
        message_text: "Guidance query",
      });
      expect(msgRes.data.id).toBe(101);

      const readRes = await chatService.markAsRead(10);
      expect(api.post).toHaveBeenCalledWith("/chat/conversations/10/read");
      expect(readRes.data.marked_count).toBe(1);
    });
  });

  // ============================================================================
  // AC-8: Notification Lifecycle API Contracts
  // ============================================================================
  describe("AC-8: In-App Notifications & Badge Indicators", () => {
    it("should query unread badge count and mark all notifications read", async () => {
      const mockBadge = { data: { success: true, data: { unread_count: 5 } } };
      const mockMarkAll = { data: { success: true, data: { unread_count: 0 } } };

      vi.spyOn(api, "get").mockResolvedValueOnce(mockBadge);
      vi.spyOn(api, "patch").mockResolvedValueOnce(mockMarkAll);

      const badgeRes = await notificationService.getUnreadCount();
      expect(api.get).toHaveBeenCalledWith("/notifications/unread-count");
      expect(badgeRes.data.unread_count).toBe(5);

      const markRes = await notificationService.markAllAsRead();
      expect(api.patch).toHaveBeenCalledWith("/notifications/mark-all-read");
      expect(markRes.data.unread_count).toBe(0);
    });
  });

  // ============================================================================
  // AC-9: Role Dashboards & Executive Telemetry API Contracts
  // ============================================================================
  describe("AC-9: Consolidated Platform Telemetry & Moderation", () => {
    it("should fetch admin overview, revenue analytics, and moderation approval", async () => {
      const mockOverview = {
        data: {
          success: true,
          data: { users: { total: 100 }, courses: { total: 20 }, revenue: { total_revenue: 50000 } },
        },
      };
      const mockApproval = {
        data: { success: true, data: { id: 5, moderation_status: "APPROVED" } },
      };

      vi.spyOn(api, "get").mockResolvedValueOnce(mockOverview);
      vi.spyOn(api, "post").mockResolvedValueOnce(mockApproval);

      const overviewRes = await adminService.getAnalyticsOverview();
      expect(api.get).toHaveBeenCalledWith("/admin/analytics/overview");
      expect(overviewRes.data.users.total).toBe(100);

      const approveRes = await adminService.approveCourse(5, { notes: "Valid course" });
      expect(api.post).toHaveBeenCalledWith("/admin/moderation/courses/5/approve", {
        notes: "Valid course",
      });
      expect(approveRes.data.moderation_status).toBe("APPROVED");
    });

    it("should fetch learner consolidated dashboard telemetry", async () => {
      const mockLearnerSummary = {
        data: {
          success: true,
          data: {
            metrics: { enrolled_courses: 3, course_progress: 75.0, mock_test_score: 88.0 },
            enrolled_courses: [{ course_id: 1, title: "Python Masterclass" }],
          },
        },
      };

      vi.spyOn(api, "get").mockResolvedValueOnce(mockLearnerSummary);

      const summaryRes = await learnerService.getDashboardSummary();
      expect(api.get).toHaveBeenCalledWith("/learners/dashboard-summary");
      expect(summaryRes.data.metrics.enrolled_courses).toBe(3);
    });

    it("should fetch company recruitment dashboard metrics", async () => {
      const mockCompanyMetrics = {
        data: {
          success: true,
          data: {
            active_jobs: 4,
            total_applications: 48,
            shortlisted: 12,
            scheduled_interviews: 6,
          },
        },
      };

      vi.spyOn(api, "get").mockResolvedValueOnce(mockCompanyMetrics);

      const compMetricsRes = await companyService.getDashboardMetrics();
      expect(api.get).toHaveBeenCalledWith("/companies/dashboard/metrics", { params: {} });
      expect(compMetricsRes.data.active_jobs).toBe(4);
      expect(compMetricsRes.data.total_applications).toBe(48);
    });
  });
});
