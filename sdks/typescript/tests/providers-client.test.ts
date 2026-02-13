import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { DelopayClient } from "../src";

function createMockResponse(body: object, status = 200, headers?: Record<string, string>): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      "content-type": "application/json",
      ...headers
    }
  });
}

describe("ProvidersClient", () => {
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

  describe("list", () => {
    it("should list all available providers", async () => {
      const responseBody = {
        providers: [
          {
            id: "STRIPE",
            name: "Stripe",
            enabled: true,
            supportedCurrencies: ["EUR", "USD", "GBP"],
            features: ["cards", "sepa", "wallet"],
            supportedCrypto: []
          },
          {
            id: "PAYPAL",
            name: "PayPal",
            enabled: true,
            supportedCurrencies: ["EUR", "USD"],
            features: ["wallet", "paylater"],
            supportedCrypto: []
          },
          {
            id: "NOWPAYMENTS",
            name: "NOWPayments",
            enabled: true,
            supportedCurrencies: ["USD"],
            features: ["crypto"],
            supportedCrypto: ["BTC", "ETH", "USDT"]
          }
        ]
      };
      fetchMock.mockResolvedValue(createMockResponse(responseBody));

      const result = await client.providers.list();

      expect(fetchMock).toHaveBeenCalledTimes(1);
      const [url] = fetchMock.mock.calls[0] as [string, RequestInit];
      expect(url).toBe("https://api.test.com/api/providers");
      
      expect(result.providers).toHaveLength(3);
      expect(result.providers[0].id).toBe("STRIPE");
      expect(result.providers[0].supportedCurrencies).toContain("EUR");
      expect(result.providers[2].supportedCrypto).toContain("BTC");
    });

    it("should handle empty providers list", async () => {
      fetchMock.mockResolvedValue(createMockResponse({ providers: [] }));

      const result = await client.providers.list();
      expect(result.providers).toHaveLength(0);
    });
  });

  describe("getClientConfig", () => {
    it("should get Stripe client config", async () => {
      const responseBody = {
        provider: "STRIPE",
        publishableKey: "demo_publishable_token",
        clientId: null
      };
      fetchMock.mockResolvedValue(createMockResponse(responseBody));

      const result = await client.providers.getClientConfig("stripe");

      expect(fetchMock).toHaveBeenCalledTimes(1);
      const [url] = fetchMock.mock.calls[0] as [string, RequestInit];
      expect(url).toBe("https://api.test.com/api/providers/stripe/client-config");
      
      expect(result.provider).toBe("STRIPE");
      expect(result.publishableKey).toBe("demo_publishable_token");
    });

    it("should get PayPal client config", async () => {
      const responseBody = {
        provider: "PAYPAL",
        publishableKey: null,
        clientId: "paypal_client_id_123"
      };
      fetchMock.mockResolvedValue(createMockResponse(responseBody));

      const result = await client.providers.getClientConfig("paypal");

      expect(result.provider).toBe("PAYPAL");
      expect(result.clientId).toBe("paypal_client_id_123");
      expect(result.publishableKey).toBeNull();
    });

    it("should URL-encode provider ID", async () => {
      fetchMock.mockResolvedValue(createMockResponse({ provider: "TEST" }));

      await client.providers.getClientConfig("provider/test#1");

      const [url] = fetchMock.mock.calls[0] as [string, RequestInit];
      expect(url).toBe("https://api.test.com/api/providers/provider%2Ftest%231/client-config");
    });

    it("should handle unknown provider", async () => {
      fetchMock.mockResolvedValue(
        createMockResponse(
          { message: "Unknown provider", code: "E_UNKNOWN_PROVIDER" },
          400
        )
      );

      await expect(client.providers.getClientConfig("unknown")).rejects.toMatchObject({
        status: 400,
        code: "E_UNKNOWN_PROVIDER"
      });
    });
  });

  describe("getStripePaymentMethods", () => {
    it("should get payment methods for EUR in Germany", async () => {
      const responseBody = {
        success: true,
        merchantCountry: "DE",
        customerCountry: "DE",
        currency: "EUR",
        paymentMethods: [
          { type: "card", name: "Credit Card", icon: "card.png" },
          { type: "sepa_debit", name: "SEPA Direct Debit", icon: "sepa.png" },
          { type: "ideal", name: "iDEAL", icon: "ideal.png" },
          { type: "giropay", name: "giropay", icon: "giropay.png" }
        ]
      };
      fetchMock.mockResolvedValue(createMockResponse(responseBody));

      const result = await client.providers.getStripePaymentMethods({
        merchantCountry: "DE",
        customerCountry: "DE",
        currency: "EUR"
      });

      expect(fetchMock).toHaveBeenCalledTimes(1);
      const [url] = fetchMock.mock.calls[0] as [string, RequestInit];
      expect(url).toContain("/api/providers/stripe/payment-methods");
      expect(url).toContain("merchantCountry=DE");
      expect(url).toContain("customerCountry=DE");
      expect(url).toContain("currency=EUR");
      
      expect(result.success).toBe(true);
      expect(result.paymentMethods).toHaveLength(4);
      expect(result.paymentMethods.map(m => m.type)).toContain("ideal");
    });

    it("should get payment methods without currency parameter", async () => {
      const responseBody = {
        success: true,
        merchantCountry: "US",
        customerCountry: "US",
        currency: null,
        paymentMethods: [
          { type: "card", name: "Credit Card", icon: "card.png" },
          { type: "ach_debit", name: "ACH Direct Debit", icon: "ach.png" }
        ]
      };
      fetchMock.mockResolvedValue(createMockResponse(responseBody));

      const result = await client.providers.getStripePaymentMethods({
        merchantCountry: "US",
        customerCountry: "US"
      });

      const [url] = fetchMock.mock.calls[0] as [string, RequestInit];
      expect(url).toContain("merchantCountry=US");
      expect(url).toContain("customerCountry=US");
      expect(url).not.toContain("currency");
      
      expect(result.paymentMethods).toHaveLength(2);
    });

    it("should handle invalid country code", async () => {
      fetchMock.mockResolvedValue(
        createMockResponse(
          { message: "Invalid country code", code: "E_INVALID_COUNTRY" },
          400
        )
      );

      await expect(
        client.providers.getStripePaymentMethods({
          merchantCountry: "XX",
          customerCountry: "DE"
        })
      ).rejects.toMatchObject({
        status: 400,
        code: "E_INVALID_COUNTRY"
      });
    });
  });
});
