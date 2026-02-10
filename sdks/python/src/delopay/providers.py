from __future__ import annotations

from .http import HttpClient
from .models import PaymentMethodsResponse, ProviderClientConfig, ProviderListResponse


class ProvidersClient:
    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def list(self) -> ProviderListResponse:
        raw = self._http.request("GET", "/api/providers")
        return ProviderListResponse.from_dict(raw or {})

    def get_client_config(self, provider_id: str) -> ProviderClientConfig:
        raw = self._http.request("GET", f"/api/providers/{provider_id}/client-config")
        return ProviderClientConfig.from_dict(raw or {})

    def get_stripe_payment_methods(
        self,
        *,
        merchant_country: str,
        customer_country: str,
        currency: str | None = None,
    ) -> PaymentMethodsResponse:
        raw = self._http.request(
            "GET",
            "/api/providers/stripe/payment-methods",
            query={
                "merchantCountry": merchant_country,
                "customerCountry": customer_country,
                "currency": currency,
            },
        )
        return PaymentMethodsResponse.from_dict(raw or {})
