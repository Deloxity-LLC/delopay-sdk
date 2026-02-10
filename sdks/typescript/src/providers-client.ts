import { HttpClient } from "./http";
import type { PaymentMethodsResponse, ProviderClientConfig, ProviderListResponse } from "./types";

export class ProvidersClient {
  constructor(private readonly http: HttpClient) {}

  list(): Promise<ProviderListResponse> {
    return this.http.request({
      method: "GET",
      path: "/api/providers"
    });
  }

  getClientConfig(providerId: string): Promise<ProviderClientConfig> {
    return this.http.request({
      method: "GET",
      path: `/api/providers/${encodeURIComponent(providerId)}/client-config`
    });
  }

  getStripePaymentMethods(params: {
    merchantCountry: string;
    customerCountry: string;
    currency?: string;
  }): Promise<PaymentMethodsResponse> {
    return this.http.request({
      method: "GET",
      path: "/api/providers/stripe/payment-methods",
      query: {
        merchantCountry: params.merchantCountry,
        customerCountry: params.customerCountry,
        currency: params.currency
      }
    });
  }
}
