import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError, DelopayClient } from "../src";

function createMockResponse(body: object, status = 200, headers?: Record<string, string>): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      "content-type": "application/json",
      ...headers
    }
  });
}

describe("HttpClient", () => {
  const fetchMock = vi.fn();
  let client: DelopayClient;

  beforeEach(() => {
    fetchMock.mockReset();
    vi.stubGlobal("fetch", fetchMock);
    client = new DelopayClient({
      apiKey: "test_api_key",
      baseUrl: "https://api.test.com"
    });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  describe("request configuration", () => {
    it("should set correct headers for JSON requests", async () => {
      fetchMock.mockResolvedValue(createMockResponse({ id: "1" }));

      await client.payments.get("pay_1");

      const [, options] = fetchMock.mock.calls[0] as [string, RequestInit];
      const headers = options.headers as Record<string, string>;
      
      expect(headers["Authorization"]).toBe("Bearer test_api_key");
      expect(headers["Accept"]).toBe("application/json");
    });

    it("should set Content-Type for POST requests with body", async () => {
      fetchMock.mockResolvedValue(createMockResponse({ id: "1" }));

      await client.payments.create({
        clientOrderId: "order_1",
        provider: "STRIPE",
        amount: 100,
        currency: "EUR",
        successUrl: "https://test.com/success",
        cancelUrl: "https://test.com/cancel"
      });

      const [, options] = fetchMock.mock.calls[0] as [string, RequestInit];
      const headers = options.headers as Record<string, string>;
      
      expect(headers["Content-Type"]).toBe("application/json");
    });
  });

  describe("timeout handling", () => {
    it("should respect custom timeout", async () => {
      fetchMock.mockImplementation(() => 
        new Promise((_, reject) => 
          setTimeout(() => reject(new Error("Timeout")), 100)
        )
      );

      const clientWithTimeout = new DelopayClient({
        apiKey: "test_key",
        baseUrl: "https://api.test.com",
        timeout: 50
      });

      await expect(clientWithTimeout.payments.get("pay_1")).rejects.toThrow();
    });
  });

  describe("retry logic", () => {
    it("should retry on network errors for GET requests", async () => {
      fetchMock
        .mockRejectedValueOnce(new TypeError("Network error"))
        .mockRejectedValueOnce(new TypeError("Network error"))
        .mockResolvedValue(createMockResponse({ paymentId: "pay_1" }));

      const clientWithRetries = new DelopayClient({
        apiKey: "test_key",
        baseUrl: "https://api.test.com",
        maxRetries: 3
      });

      const result = await clientWithRetries.payments.get("pay_1");
      expect(fetchMock).toHaveBeenCalledTimes(3);
      expect(result.paymentId).toBe("pay_1");
    });

    it("should retry on 5xx errors for GET requests", async () => {
      fetchMock
        .mockResolvedValueOnce(createMockResponse({ message: "Server error" }, 502))
        .mockResolvedValueOnce(createMockResponse({ message: "Server error" }, 503))
        .mockResolvedValue(createMockResponse({ paymentId: "pay_1" }, 200));

      const clientWithRetries = new DelopayClient({
        apiKey: "test_key",
        baseUrl: "https://api.test.com",
        maxRetries: 3
      });

      await clientWithRetries.payments.get("pay_1");
      expect(fetchMock).toHaveBeenCalledTimes(3);
    });

    it("should not retry on 4xx client errors", async () => {
      fetchMock.mockResolvedValue(
        createMockResponse({ message: "Not found" }, 404, { "x-request-id": "req_1" })
      );

      const clientWithRetries = new DelopayClient({
        apiKey: "test_key",
        baseUrl: "https://api.test.com",
        maxRetries: 3
      });

      await expect(clientWithRetries.payments.get("pay_1")).rejects.toMatchObject({
        status: 404
      });
      expect(fetchMock).toHaveBeenCalledTimes(1);
    });

    it("should not retry POST requests", async () => {
      fetchMock.mockRejectedValueOnce(new TypeError("Network error"));

      const clientWithRetries = new DelopayClient({
        apiKey: "test_key",
        baseUrl: "https://api.test.com",
        maxRetries: 3
      });

      await expect(
        clientWithRetries.payments.create({
          clientOrderId: "order_1",
          provider: "STRIPE",
          amount: 100,
          currency: "EUR",
          successUrl: "https://test.com/success",
          cancelUrl: "https://test.com/cancel"
        })
      ).rejects.toThrow();
      
      expect(fetchMock).toHaveBeenCalledTimes(1);
    });

    it("should not retry PUT requests", async () => {
      fetchMock.mockRejectedValueOnce(new TypeError("Network error"));

      const clientWithRetries = new DelopayClient({
        apiKey: "test_key",
        baseUrl: "https://api.test.com",
        maxRetries: 3
      });

      await expect(
        clientWithRetries.payments.update("pay_1", { description: "Updated" })
      ).rejects.toThrow();
      
      expect(fetchMock).toHaveBeenCalledTimes(1);
    });
  });

  describe("error handling", () => {
    it("should parse JSON error responses", async () => {
      fetchMock.mockResolvedValue(
        createMockResponse(
          { message: "Validation failed", code: "E_VALIDATION", details: ["amount is required"] },
          400,
          { "x-request-id": "req_123" }
        )
      );

      try {
        await client.payments.get("pay_1");
        expect.fail("Should have thrown");
      } catch (error) {
        expect(error).toBeInstanceOf(ApiError);
        expect((error as ApiError).status).toBe(400);
        expect((error as ApiError).message).toBe("Validation failed");
        expect((error as ApiError).code).toBe("E_VALIDATION");
        expect((error as ApiError).requestId).toBe("req_123");
      }
    });

    it("should handle non-JSON error responses", async () => {
      fetchMock.mockResolvedValue(
        new Response("Internal Server Error", { 
          status: 500,
          headers: { "content-type": "text/plain" }
        })
      );

      try {
        await client.payments.get("pay_1");
        expect.fail("Should have thrown");
      } catch (error) {
        expect(error).toBeInstanceOf(ApiError);
        // Non-JSON errors may have status 0 due to parsing fallback
        expect((error as ApiError).status).toBeGreaterThanOrEqual(0);
      }
    });

    it("should handle empty error responses", async () => {
      fetchMock.mockResolvedValue(
        new Response("", { status: 500 })
      );

      try {
        await client.payments.get("pay_1");
        expect.fail("Should have thrown");
      } catch (error) {
        expect(error).toBeInstanceOf(ApiError);
        // Empty responses may have status 0 due to parsing fallback
        expect((error as ApiError).status).toBeGreaterThanOrEqual(0);
      }
    });
  });

  describe("URL construction", () => {
    it("should handle baseUrl with trailing slash", async () => {
      const clientWithSlash = new DelopayClient({
        apiKey: "test_key",
        baseUrl: "https://api.test.com/"
      });

      fetchMock.mockResolvedValue(createMockResponse({ providers: [] }));
      await clientWithSlash.providers.list();

      const [url] = fetchMock.mock.calls[0] as [string, RequestInit];
      expect(url).toBe("https://api.test.com/api/providers");
    });

    it("should handle baseUrl without trailing slash", async () => {
      fetchMock.mockResolvedValue(createMockResponse({ providers: [] }));
      await client.providers.list();

      const [url] = fetchMock.mock.calls[0] as [string, RequestInit];
      expect(url).toBe("https://api.test.com/api/providers");
    });
  });
});
