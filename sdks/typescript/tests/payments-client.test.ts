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

function createPaymentResponse(paymentId: string, overrides?: object) {
  return {
    paymentId,
    clientOrderId: "order_123",
    provider: "STRIPE",
    status: "PENDING",
    amount: 100,
    currency: "EUR",
    description: "Test payment",
    customerEmail: "test@example.com",
    checkoutUrl: "https://checkout.example.com",
    providerPaymentId: "pi_123",
    createdAt: "2026-02-12T10:00:00Z",
    metadata: { orderId: "internal_123" },
    ...overrides
  };
}

describe("PaymentsClient", () => {
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

  describe("create", () => {
    it("should create a payment with all required fields", async () => {
      const responseBody = createPaymentResponse("pay_new_123", {
        status: "PENDING",
        checkoutUrl: "https://checkout.stripe.com/test"
      });
      fetchMock.mockResolvedValue(createMockResponse(responseBody));

      const result = await client.payments.create({
        clientOrderId: "order_123",
        provider: "STRIPE",
        amount: 100,
        currency: "EUR",
        successUrl: "https://shop.test/success",
        cancelUrl: "https://shop.test/cancel",
        description: "Test payment",
        customerEmail: "customer@test.com",
        callbackUrl: "https://shop.test/webhook",
        metadata: { orderId: "internal_123" },
        autoCapture: true
      });

      expect(fetchMock).toHaveBeenCalledTimes(1);
      const [url, options] = fetchMock.mock.calls[0] as [string, RequestInit];
      expect(url).toBe("https://api.test.com/api/payments/create");
      expect(options.method).toBe("POST");
      
      const body = JSON.parse(options.body as string);
      expect(body.clientOrderId).toBe("order_123");
      expect(body.provider).toBe("STRIPE");
      expect(body.amount).toBe(100);
      expect(body.currency).toBe("EUR");
      expect(body.successUrl).toBe("https://shop.test/success");
      expect(body.cancelUrl).toBe("https://shop.test/cancel");
      
      expect(result.paymentId).toBe("pay_new_123");
      expect(result.status).toBe("PENDING");
    });

    it("should create a payment with minimal required fields", async () => {
      const responseBody = createPaymentResponse("pay_minimal");
      fetchMock.mockResolvedValue(createMockResponse(responseBody));

      await client.payments.create({
        clientOrderId: "minimal_order",
        provider: "PAYPAL",
        amount: 50,
        currency: "USD",
        successUrl: "https://test.com/success",
        cancelUrl: "https://test.com/cancel"
      });

      const [, options] = fetchMock.mock.calls[0] as [string, RequestInit];
      const body = JSON.parse(options.body as string);
      expect(body.autoCapture).toBeUndefined();
      expect(body.metadata).toBeUndefined();
    });

    it("should handle validation errors on create", async () => {
      fetchMock.mockResolvedValue(
        createMockResponse(
          { message: "Invalid currency", code: "E_INVALID_CURRENCY" },
          400,
          { "x-request-id": "req_456" }
        )
      );

      await expect(
        client.payments.create({
          clientOrderId: "order_test",
          provider: "STRIPE",
          amount: 100,
          currency: "INVALID",
          successUrl: "https://test.com/success",
          cancelUrl: "https://test.com/cancel"
        })
      ).rejects.toMatchObject({
        status: 400,
        code: "E_INVALID_CURRENCY",
        message: "Invalid currency",
        requestId: "req_456"
      });
    });
  });

  describe("get", () => {
    it("should get a payment by ID", async () => {
      const responseBody = createPaymentResponse("pay_existing", {
        status: "COMPLETED",
        completedAt: "2026-02-12T11:00:00Z",
        amountPaid: 100
      });
      fetchMock.mockResolvedValue(createMockResponse(responseBody));

      const result = await client.payments.get("pay_existing");

      expect(fetchMock).toHaveBeenCalledTimes(1);
      const [url] = fetchMock.mock.calls[0] as [string, RequestInit];
      expect(url).toBe("https://api.test.com/api/payments/pay_existing");
      
      expect(result.paymentId).toBe("pay_existing");
      expect(result.status).toBe("COMPLETED");
      expect(result.completedAt).toBe("2026-02-12T11:00:00Z");
      expect(result.amountPaid).toBe(100);
    });

    it("should handle payment not found", async () => {
      fetchMock.mockResolvedValue(
        createMockResponse(
          { message: "Payment not found", code: "E_NOT_FOUND" },
          404,
          { "x-request-id": "req_789" }
        )
      );

      await expect(client.payments.get("pay_nonexistent")).rejects.toMatchObject({
        status: 404,
        code: "E_NOT_FOUND"
      });
    });

    it("should URL-encode payment IDs with special characters", async () => {
      fetchMock.mockResolvedValue(createMockResponse(createPaymentResponse("pay%20id")));

      await client.payments.get("pay test/id");

      const [url] = fetchMock.mock.calls[0] as [string, RequestInit];
      expect(url).toBe("https://api.test.com/api/payments/pay%20test%2Fid");
    });
  });

  describe("getByOrder", () => {
    it("should get a payment by client order ID", async () => {
      const responseBody = createPaymentResponse("pay_by_order", {
        clientOrderId: "my_custom_order_123"
      });
      fetchMock.mockResolvedValue(createMockResponse(responseBody));

      const result = await client.payments.getByOrder("my_custom_order_123");

      expect(fetchMock).toHaveBeenCalledTimes(1);
      const [url] = fetchMock.mock.calls[0] as [string, RequestInit];
      expect(url).toBe("https://api.test.com/api/payments/by-order/my_custom_order_123");
      
      expect(result.clientOrderId).toBe("my_custom_order_123");
    });

    it("should URL-encode order IDs with special characters", async () => {
      fetchMock.mockResolvedValue(createMockResponse(createPaymentResponse("pay_encoded")));

      await client.payments.getByOrder("order#123/test");

      const [url] = fetchMock.mock.calls[0] as [string, RequestInit];
      expect(url).toBe("https://api.test.com/api/payments/by-order/order%23123%2Ftest");
    });
  });

  describe("update", () => {
    it("should update payment metadata", async () => {
      const responseBody = createPaymentResponse("pay_update", {
        metadata: { updated: "true", orderId: "123" }
      });
      fetchMock.mockResolvedValue(createMockResponse(responseBody));

      const result = await client.payments.update("pay_update", {
        metadata: { updated: "true" },
        description: "Updated description"
      });

      expect(fetchMock).toHaveBeenCalledTimes(1);
      const [url, options] = fetchMock.mock.calls[0] as [string, RequestInit];
      expect(url).toBe("https://api.test.com/api/payments/pay_update");
      expect(options.method).toBe("PUT");
      
      const body = JSON.parse(options.body as string);
      expect(body.metadata).toEqual({ updated: "true" });
      expect(body.description).toBe("Updated description");
      
      expect(result.metadata).toEqual({ updated: "true", orderId: "123" });
    });

    it("should update callback URL", async () => {
      fetchMock.mockResolvedValue(createMockResponse(createPaymentResponse("pay_callback")));

      await client.payments.update("pay_callback", {
        callbackUrl: "https://new.webhook.com/callback"
      });

      const [, options] = fetchMock.mock.calls[0] as [string, RequestInit];
      const body = JSON.parse(options.body as string);
      expect(body.callbackUrl).toBe("https://new.webhook.com/callback");
    });
  });

  describe("capture", () => {
    it("should capture an authorized payment", async () => {
      const responseBody = createPaymentResponse("pay_capture", {
        status: "NEEDS_CAPTURING"
      });
      fetchMock.mockResolvedValue(createMockResponse(responseBody));

      const result = await client.payments.capture("pay_auth");

      expect(fetchMock).toHaveBeenCalledTimes(1);
      const [url, options] = fetchMock.mock.calls[0] as [string, RequestInit];
      expect(url).toBe("https://api.test.com/api/payments/pay_auth/capture");
      expect(options.method).toBe("POST");
      
      expect(result.status).toBe("NEEDS_CAPTURING");
    });

    it("should handle capture of already captured payment", async () => {
      fetchMock.mockResolvedValue(
        createMockResponse(
          { message: "Payment already captured", code: "E_ALREADY_CAPTURED" },
          400
        )
      );

      await expect(client.payments.capture("pay_captured")).rejects.toMatchObject({
        status: 400,
        code: "E_ALREADY_CAPTURED"
      });
    });
  });

  describe("refund", () => {
    it("should process a full refund", async () => {
      const responseBody = {
        refundId: "ref_123",
        paymentId: "pay_refund",
        providerRefundId: "re_123",
        amount: 100,
        originalAmount: 100,
        remainingAmount: 0,
        status: "PENDING",
        reason: "Customer request",
        createdAt: "2026-02-12T12:00:00Z"
      };
      fetchMock.mockResolvedValue(createMockResponse(responseBody));

      const result = await client.payments.refund("pay_refund", {
        amount: 100,
        reason: "Customer request"
      });

      expect(fetchMock).toHaveBeenCalledTimes(1);
      const [url, options] = fetchMock.mock.calls[0] as [string, RequestInit];
      expect(url).toBe("https://api.test.com/api/payments/pay_refund/refund");
      expect(options.method).toBe("POST");
      
      const body = JSON.parse(options.body as string);
      expect(body.amount).toBe(100);
      expect(body.reason).toBe("Customer request");
      
      expect(result.refundId).toBe("ref_123");
      expect(result.status).toBe("PENDING");
      expect(result.remainingAmount).toBe(0);
    });

    it("should process a partial refund", async () => {
      const responseBody = {
        refundId: "ref_partial",
        paymentId: "pay_partial",
        amount: 50,
        originalAmount: 100,
        remainingAmount: 50,
        status: "COMPLETED",
        reason: null,
        createdAt: "2026-02-12T12:00:00Z",
        completedAt: "2026-02-12T12:05:00Z"
      };
      fetchMock.mockResolvedValue(createMockResponse(responseBody));

      const result = await client.payments.refund("pay_partial", {
        amount: 50
      });

      expect(result.amount).toBe(50);
      expect(result.remainingAmount).toBe(50);
      expect(result.completedAt).toBe("2026-02-12T12:05:00Z");
    });

    it("should handle refund exceeding amount", async () => {
      fetchMock.mockResolvedValue(
        createMockResponse(
          { message: "Refund amount exceeds payment", code: "E_REFUND_EXCEEDS" },
          400
        )
      );

      await expect(
        client.payments.refund("pay_small", { amount: 200 })
      ).rejects.toMatchObject({
        status: 400,
        code: "E_REFUND_EXCEEDS"
      });
    });
  });

  describe("resendFailedCallbacks", () => {
    it("should resend failed callbacks", async () => {
      fetchMock.mockResolvedValue(createMockResponse({ resent: 5 }));

      const result = await client.payments.resendFailedCallbacks();

      expect(fetchMock).toHaveBeenCalledTimes(1);
      const [url, options] = fetchMock.mock.calls[0] as [string, RequestInit];
      expect(url).toBe("https://api.test.com/api/payments/resend-failed-callbacks");
      expect(options.method).toBe("POST");
      
      expect(result.resent).toBe(5);
    });

    it("should handle no failed callbacks", async () => {
      fetchMock.mockResolvedValue(createMockResponse({ resent: 0 }));

      const result = await client.payments.resendFailedCallbacks();
      expect(result.resent).toBe(0);
    });
  });
});
