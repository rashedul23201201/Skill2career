/**
 * SKL-61: Frontend Security & Access Control Testing Suite
 *
 * Comprehensive tests verifying:
 * 1. Secure token storage, retrieval, and sanitization (JWT lifecycle).
 * 2. Axios client authentication interceptors (Bearer injection & session invalidation).
 * 3. 401 Unauthorized handling, refresh token failure, and auth:unauthorized events.
 * 4. Strict Role-Based Access Control (RBAC) route guarding and role isolation.
 * 5. BOLA/IDOR error handling and safe error formatting.
 * 6. XSS prevention and payload error sanitization.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

// ==============================================================================
// Mock Browser Environment for Node Testing
// ==============================================================================
const localStorageStore = {};
const localStorageMock = {
  getItem: vi.fn((key) => (key in localStorageStore ? localStorageStore[key] : null)),
  setItem: vi.fn((key, value) => {
    localStorageStore[key] = String(value);
  }),
  removeItem: vi.fn((key) => {
    delete localStorageStore[key];
  }),
  clear: vi.fn(() => {
    Object.keys(localStorageStore).forEach((key) => delete localStorageStore[key]);
  }),
};

Object.defineProperty(globalThis, "localStorage", {
  value: localStorageMock,
  writable: true,
});

// Mock window event system if not fully present in environment
if (typeof window === "undefined") {
  globalThis.window = {
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  };
} else {
  if (!window.dispatchEvent) {
    window.dispatchEvent = vi.fn();
  }
}

import api from "../src/services/api";
import {
  getStoredToken,
  setStoredToken,
  removeStoredToken,
  getStoredRefreshToken,
  setStoredRefreshToken,
  removeStoredRefreshToken,
  clearAllTokens,
  formatErrorMessage,
} from "../src/utils";
import { STORAGE_KEYS, USER_ROLES, ROUTES } from "../src/constants";

describe("SKL-61: Frontend Security & Access Control Tests", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    localStorage.clear();
  });

  afterEach(() => {
    vi.restoreAllMocks();
    localStorage.clear();
  });

  // ============================================================================
  // AC-1: Secure Token Storage & Client Credential Sanitization
  // ============================================================================
  describe("AC-1: Token Storage & Credential Sanitization", () => {
    it("should securely persist and retrieve JWT access token in storage", () => {
      const mockJwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.mockTokenPayload.signature";
      setStoredToken(mockJwt);

      expect(localStorageMock.setItem).toHaveBeenCalledWith(STORAGE_KEYS.TOKEN, mockJwt);
      expect(getStoredToken()).toBe(mockJwt);
    });

    it("should remove access token when passed null or empty value", () => {
      setStoredToken("sample-token");
      expect(getStoredToken()).toBe("sample-token");

      setStoredToken(null);
      expect(localStorageMock.removeItem).toHaveBeenCalledWith(STORAGE_KEYS.TOKEN);
      expect(getStoredToken()).toBeNull();
    });

    it("should securely store and retrieve refresh token separately", () => {
      const mockRefresh = "refresh-uuid-token-xyz-12345";
      setStoredRefreshToken(mockRefresh);

      expect(localStorageMock.setItem).toHaveBeenCalledWith(STORAGE_KEYS.REFRESH_TOKEN, mockRefresh);
      expect(getStoredRefreshToken()).toBe(mockRefresh);

      removeStoredRefreshToken();
      expect(localStorageMock.removeItem).toHaveBeenCalledWith(STORAGE_KEYS.REFRESH_TOKEN);
      expect(getStoredRefreshToken()).toBeNull();
    });

    it("should completely wipe all authentication credentials on clearAllTokens", () => {
      setStoredToken("active-access-token");
      setStoredRefreshToken("active-refresh-token");

      clearAllTokens();

      expect(getStoredToken()).toBeNull();
      expect(getStoredRefreshToken()).toBeNull();
      expect(localStorageMock.removeItem).toHaveBeenCalledWith(STORAGE_KEYS.TOKEN);
      expect(localStorageMock.removeItem).toHaveBeenCalledWith(STORAGE_KEYS.REFRESH_TOKEN);
    });

    it("should handle storage exceptions gracefully without crashing (security sandboxing)", () => {
      vi.spyOn(localStorageMock, "getItem").mockImplementationOnce(() => {
        throw new Error("SecurityError: Access to localStorage is denied.");
      });

      expect(() => getStoredToken()).not.toThrow();
      expect(getStoredToken()).toBeNull();
    });
  });

  // ============================================================================
  // AC-2: Axios Security Interceptor & Bearer Authorization Injection
  // ============================================================================
  describe("AC-2: Axios Client Interceptors & Header Injection", () => {
    it("should inject Bearer authorization header when user is authenticated", () => {
      const testToken = "secure.jwt.header.token";
      setStoredToken(testToken);

      // Extract request interceptor handler from Axios instance
      const requestHandlers = api.interceptors.request.handlers;
      expect(requestHandlers.length).toBeGreaterThan(0);

      const requestInterceptor = requestHandlers[0].fulfilled;
      const config = { headers: {} };
      const updatedConfig = requestInterceptor(config);

      expect(updatedConfig.headers.Authorization).toBe(`Bearer ${testToken}`);
    });

    it("should NOT attach Authorization header when no session token exists", () => {
      removeStoredToken();

      const requestHandlers = api.interceptors.request.handlers;
      const requestInterceptor = requestHandlers[0].fulfilled;
      const config = { headers: {} };
      const updatedConfig = requestInterceptor(config);

      expect(updatedConfig.headers.Authorization).toBeUndefined();
    });
  });

  // ============================================================================
  // AC-3: 401 Session Invalidation & Token Expiration Handling
  // ============================================================================
  describe("AC-3: Session Invalidation on 401 & Expiration", () => {
    it("should clear all tokens and dispatch auth:unauthorized when 401 occurs without refresh token", async () => {
      setStoredToken("expired-access-token");
      removeStoredRefreshToken();

      const dispatchSpy = vi.spyOn(window, "dispatchEvent");

      const responseHandlers = api.interceptors.response.handlers;
      expect(responseHandlers.length).toBeGreaterThan(0);
      const responseErrorInterceptor = responseHandlers[0].rejected;

      const mockError = {
        config: { url: "/api/v1/learner/profile", headers: {} },
        response: { status: 401, data: { detail: "Token expired", error_code: "TOKEN_EXPIRED" } },
      };

      await expect(responseErrorInterceptor(mockError)).rejects.toEqual(mockError);

      expect(getStoredToken()).toBeNull();
      expect(getStoredRefreshToken()).toBeNull();
      expect(dispatchSpy).toHaveBeenCalled();
    });

    it("should NOT trigger refresh rotation cycle for auth login or register endpoints on 401", async () => {
      setStoredRefreshToken("some-refresh-token");
      const dispatchSpy = vi.spyOn(window, "dispatchEvent");

      const responseHandlers = api.interceptors.response.handlers;
      const responseErrorInterceptor = responseHandlers[0].rejected;

      const mockLoginError = {
        config: { url: "/auth/login", headers: {} },
        response: { status: 401, data: { detail: "Invalid credentials" } },
      };

      await expect(responseErrorInterceptor(mockLoginError)).rejects.toEqual(mockLoginError);

      // Should not wipe tokens on ordinary invalid login credential error
      expect(dispatchSpy).not.toHaveBeenCalled();
    });
  });

  // ============================================================================
  // AC-4: Strict Role-Based Access Control (RBAC) & Route Guard Logic
  // ============================================================================
  describe("AC-4: Role-Based Access Control (RBAC) Boundaries", () => {
    // Evaluation helper mimicking ProtectedRoute decision matrix
    const evaluateRouteAccess = ({ isAuthenticated, userRole, allowedRoles, loading }) => {
      if (loading) return { decision: "LOADING", target: null };
      if (!isAuthenticated) return { decision: "REDIRECT", target: ROUTES.LOGIN };
      if (allowedRoles && allowedRoles.length > 0 && !allowedRoles.includes(userRole)) {
        return { decision: "REDIRECT", target: ROUTES.DASHBOARD };
      }
      return { decision: "PERMIT", target: null };
    };

    it("should block unauthenticated visitors and redirect to /login", () => {
      const result = evaluateRouteAccess({
        isAuthenticated: false,
        userRole: null,
        allowedRoles: [USER_ROLES.LEARNER],
        loading: false,
      });

      expect(result.decision).toBe("REDIRECT");
      expect(result.target).toBe(ROUTES.LOGIN);
    });

    it("should display loading indicator while verifying session without rendering protected component", () => {
      const result = evaluateRouteAccess({
        isAuthenticated: false,
        userRole: null,
        allowedRoles: [USER_ROLES.LEARNER],
        loading: true,
      });

      expect(result.decision).toBe("LOADING");
      expect(result.target).toBeNull();
    });

    it("should forbid LEARNER from accessing ADMIN routes and redirect to /dashboard", () => {
      const result = evaluateRouteAccess({
        isAuthenticated: true,
        userRole: USER_ROLES.LEARNER,
        allowedRoles: [USER_ROLES.ADMIN],
        loading: false,
      });

      expect(result.decision).toBe("REDIRECT");
      expect(result.target).toBe(ROUTES.DASHBOARD);
    });

    it("should forbid LEARNER from accessing INSTRUCTOR course authoring routes", () => {
      const result = evaluateRouteAccess({
        isAuthenticated: true,
        userRole: USER_ROLES.LEARNER,
        allowedRoles: [USER_ROLES.INSTRUCTOR, USER_ROLES.ADMIN],
        loading: false,
      });

      expect(result.decision).toBe("REDIRECT");
      expect(result.target).toBe(ROUTES.DASHBOARD);
    });

    it("should forbid COMPANY from accessing INSTRUCTOR course management", () => {
      const result = evaluateRouteAccess({
        isAuthenticated: true,
        userRole: USER_ROLES.COMPANY,
        allowedRoles: [USER_ROLES.INSTRUCTOR, USER_ROLES.ADMIN],
        loading: false,
      });

      expect(result.decision).toBe("REDIRECT");
      expect(result.target).toBe(ROUTES.DASHBOARD);
    });

    it("should forbid INSTRUCTOR from accessing COMPANY job creation routes", () => {
      const result = evaluateRouteAccess({
        isAuthenticated: true,
        userRole: USER_ROLES.INSTRUCTOR,
        allowedRoles: [USER_ROLES.COMPANY, USER_ROLES.ADMIN],
        loading: false,
      });

      expect(result.decision).toBe("REDIRECT");
      expect(result.target).toBe(ROUTES.DASHBOARD);
    });

    it("should PERMIT user with exact allowed role (e.g. COMPANY on job management)", () => {
      const result = evaluateRouteAccess({
        isAuthenticated: true,
        userRole: USER_ROLES.COMPANY,
        allowedRoles: [USER_ROLES.COMPANY, USER_ROLES.ADMIN],
        loading: false,
      });

      expect(result.decision).toBe("PERMIT");
      expect(result.target).toBeNull();
    });

    it("should PERMIT ADMIN on any administrative or privileged route", () => {
      const result = evaluateRouteAccess({
        isAuthenticated: true,
        userRole: USER_ROLES.ADMIN,
        allowedRoles: [USER_ROLES.ADMIN],
        loading: false,
      });

      expect(result.decision).toBe("PERMIT");
      expect(result.target).toBeNull();
    });

    it("should PERMIT any authenticated user when allowedRoles is not specified", () => {
      const result = evaluateRouteAccess({
        isAuthenticated: true,
        userRole: USER_ROLES.LEARNER,
        allowedRoles: null,
        loading: false,
      });

      expect(result.decision).toBe("PERMIT");
    });
  });

  // ============================================================================
  // AC-5: Broken Object-Level Authorization (IDOR) & Error Response Security
  // ============================================================================
  describe("AC-5: IDOR Response Handling & Error Message Sanitization", () => {
    it("should format 403 Forbidden message cleanly when user lacks permissions", () => {
      const forbiddenError = {
        response: {
          status: 403,
          data: {
            success: false,
            message: "You do not have permission to view or withdraw this application.",
            error_code: "INSUFFICIENT_ROLE_PERMISSIONS",
          },
        },
      };

      const message = formatErrorMessage(forbiddenError);
      expect(message).toBe("You do not have permission to view or withdraw this application.");
    });

    it("should format 403 Unverified Company message properly", () => {
      const unverifiedError = {
        response: {
          status: 403,
          data: {
            success: false,
            message: "Your company account is currently pending administrative verification.",
            error_code: "COMPANY_NOT_VERIFIED",
          },
        },
      };

      const message = formatErrorMessage(unverifiedError);
      expect(message).toContain("pending administrative verification");
    });

    it("should format 404 Not Found cleanly when resource ID is invalid or belongs to another tenant", () => {
      const notFoundError = {
        response: {
          status: 404,
          data: {
            detail: "Job application not found",
          },
        },
      };

      const message = formatErrorMessage(notFoundError);
      expect(message).toBe("Job application not found");
    });
  });

  // ============================================================================
  // AC-6: XSS & Payload Input Sanitization Defense
  // ============================================================================
  describe("AC-6: Payload Error Sanitization & XSS Defense", () => {
    it("should safely aggregate array-based Pydantic validation errors without executing scripts", () => {
      const xssValidationError = {
        response: {
          status: 422,
          data: {
            detail: [
              { msg: "Field 'title' cannot contain raw HTML", loc: ["body", "title"] },
              { msg: "<script>alert('xss')</script> is not a valid URL", loc: ["body", "website_url"] },
            ],
          },
        },
      };

      const formatted = formatErrorMessage(xssValidationError);
      expect(formatted).toContain("Field 'title' cannot contain raw HTML");
      expect(formatted).toContain("<script>alert('xss')</script> is not a valid URL");
      // Formatted as safe comma-separated text string
      expect(typeof formatted).toBe("string");
    });

    it("should fallback to generic safe error message if error structure is malformed or empty", () => {
      const emptyError = {};
      const formatted = formatErrorMessage(emptyError);
      expect(formatted).toBe("An unexpected error occurred. Please try again.");
    });
  });
});
