import { existsSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError, DelopayClient } from "../src";

const __dirname = fileURLToPath(new URL(".", import.meta.url));

function paymentResponse(): Response {
  return new Response(
    JSON.stringify({
      paymentId: "pay_123",
      clientOrderId: "order_1",
      provider: "STRIPE",
      status: "PENDING",
      amount: 10,
      currency: "EUR"
    }),
    {
      status: 200,
      headers: {
        "content-type": "application/json"
      }
    }
  );
}

describe("DelopayClient", () => {
  const fetchMock = vi.fn();

  beforeEach(() => {
    fetchMock.mockReset();
    vi.stubGlobal("fetch", fetchMock);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("sends authorization header", async () => {
    fetchMock.mockResolvedValue(paymentResponse());

    const client = new DelopayClient({
      apiKey: "test_key",
      baseUrl: "https://api.example.com"
    });

    await client.payments.get("pay_123");

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, options] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toContain("/api/payments/pay_123");

    const headers = options.headers as Record<string, string>;
    expect(headers.Authorization).toBe("Bearer test_key");
  });

  it("retries idempotent GET on network error", async () => {
    fetchMock.mockRejectedValueOnce(new TypeError("offline")).mockResolvedValueOnce(paymentResponse());

    const client = new DelopayClient({
      apiKey: "test_key",
      baseUrl: "https://api.example.com",
      maxRetries: 2
    });

    await client.payments.get("pay_123");
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it("does not retry POST requests", async () => {
    fetchMock.mockRejectedValue(new TypeError("offline"));

    const client = new DelopayClient({
      apiKey: "test_key",
      baseUrl: "https://api.example.com",
      maxRetries: 2
    });

    await expect(
      client.payments.create({
        clientOrderId: "order_1",
        provider: "STRIPE",
        amount: 10,
        currency: "EUR",
        successUrl: "https://shop.test/success",
        cancelUrl: "https://shop.test/cancel"
      })
    ).rejects.toBeInstanceOf(ApiError);

    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("maps API error fields", async () => {
    fetchMock.mockResolvedValue(
      new Response(JSON.stringify({ message: "Invalid request", code: "E_INVALID" }), {
        status: 400,
        headers: {
          "content-type": "application/json",
          "x-request-id": "req_123"
        }
      })
    );

    const client = new DelopayClient({
      apiKey: "test_key",
      baseUrl: "https://api.example.com"
    });

    await expect(client.payments.get("pay_123")).rejects.toMatchObject({
      status: 400,
      code: "E_INVALID",
      requestId: "req_123"
    });
  });

  it("has generated baseline directory", () => {
    const generatedReadme = resolve(__dirname, "..", "generated", "README.md");
    expect(existsSync(generatedReadme)).toBe(true);
  });
});
