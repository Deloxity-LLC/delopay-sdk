"""Comprehensive tests for ProvidersClient."""

from __future__ import annotations

import json
from urllib.error import HTTPError

import pytest

from delopay import DelopayClient


class FakeResponse:
    """Mock HTTP response."""

    def __init__(
        self,
        status: int,
        payload: dict | None = None,
        headers: dict | None = None,
    ) -> None:
        self.status = status
        self._payload = payload
        self.headers = headers or {}

    def read(self) -> bytes:
        if self._payload is None:
            return b""
        return json.dumps(self._payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class TestProvidersList:
    """Test listing providers."""

    def test_list_all_providers(self, monkeypatch):
        """Test listing all available providers."""
        captured = {}

        def fake_urlopen(request, timeout=0):
            captured["url"] = request.full_url
            return FakeResponse(
                200,
                {
                    "providers": [
                        {
                            "id": "STRIPE",
                            "name": "Stripe",
                            "enabled": True,
                            "supportedCurrencies": ["EUR", "USD", "GBP"],
                            "features": ["cards", "sepa", "wallet"],
                            "supportedCrypto": [],
                        },
                        {
                            "id": "PAYPAL",
                            "name": "PayPal",
                            "enabled": True,
                            "supportedCurrencies": ["EUR", "USD"],
                            "features": ["wallet", "paylater"],
                            "supportedCrypto": [],
                        },
                        {
                            "id": "NOWPAYMENTS",
                            "name": "NOWPayments",
                            "enabled": True,
                            "supportedCurrencies": ["USD"],
                            "features": ["crypto"],
                            "supportedCrypto": ["BTC", "ETH", "USDT"],
                        },
                    ]
                },
            )

        monkeypatch.setattr("delopay.http.urlopen", fake_urlopen)

        client = DelopayClient(api_key="test_key", base_url="https://api.test.com")
        result = client.providers.list()

        assert captured["url"] == "https://api.test.com/api/providers"
        assert len(result.providers) == 3
        assert result.providers[0].id == "STRIPE"
        assert "EUR" in result.providers[0].supported_currencies
        assert "BTC" in result.providers[2].supported_crypto

    def test_empty_providers_list(self, monkeypatch):
        """Test handling empty providers list."""

        def fake_urlopen(request, timeout=0):
            return FakeResponse(200, {"providers": []})

        monkeypatch.setattr("delopay.http.urlopen", fake_urlopen)

        client = DelopayClient(api_key="test_key", base_url="https://api.test.com")
        result = client.providers.list()

        assert len(result.providers) == 0


class TestProvidersGetClientConfig:
    """Test getting provider client config."""

    def test_get_stripe_config(self, monkeypatch):
        """Test getting Stripe client config."""
        captured = {}

        def fake_urlopen(request, timeout=0):
            captured["url"] = request.full_url
            return FakeResponse(
                200,
                {
                    "provider": "STRIPE",
                    "publishableKey": "pk_test_1234567890",
                    "clientId": None,
                },
            )

        monkeypatch.setattr("delopay.http.urlopen", fake_urlopen)

        client = DelopayClient(api_key="test_key", base_url="https://api.test.com")
        result = client.providers.get_client_config("stripe")

        assert (
            captured["url"] == "https://api.test.com/api/providers/stripe/client-config"
        )
        assert result.provider == "STRIPE"
        assert result.publishable_key == "pk_test_1234567890"

    def test_get_paypal_config(self, monkeypatch):
        """Test getting PayPal client config."""

        def fake_urlopen(request, timeout=0):
            return FakeResponse(
                200,
                {
                    "provider": "PAYPAL",
                    "publishableKey": None,
                    "clientId": "paypal_client_id_123",
                },
            )

        monkeypatch.setattr("delopay.http.urlopen", fake_urlopen)

        client = DelopayClient(api_key="test_key", base_url="https://api.test.com")
        result = client.providers.get_client_config("paypal")

        assert result.provider == "PAYPAL"
        assert result.client_id == "paypal_client_id_123"
        assert result.publishable_key is None

    def test_get_config_with_special_chars(self, monkeypatch):
        """Test URL encoding when provider ID contains special characters."""
        captured = {}

        def fake_urlopen(request, timeout=0):
            captured["url"] = request.full_url
            return FakeResponse(200, {"provider": "TEST"})

        monkeypatch.setattr("delopay.http.urlopen", fake_urlopen)

        client = DelopayClient(api_key="test_key", base_url="https://api.test.com")
        client.providers.get_client_config("provider/test#1")

        assert (
            captured["url"]
            == "https://api.test.com/api/providers/provider%2Ftest%231/client-config"
        )

    def test_get_config_unknown_provider(self, monkeypatch):
        """Test handling unknown provider."""
        import io

        def fake_urlopen(request, timeout=0):
            raise HTTPError(
                url=request.full_url,
                code=400,
                msg="Bad Request",
                hdrs={},
                fp=io.BytesIO(
                    b'{"message":"Unknown provider","code":"E_UNKNOWN_PROVIDER"}'
                ),
            )

        monkeypatch.setattr("delopay.http.urlopen", fake_urlopen)

        client = DelopayClient(api_key="test_key", base_url="https://api.test.com")
        from delopay import ApiError

        with pytest.raises(ApiError) as exc:
            client.providers.get_client_config("unknown")

        assert exc.value.status == 400
        assert exc.value.code == "E_UNKNOWN_PROVIDER"


class TestProvidersStripePaymentMethods:
    """Test getting Stripe payment methods."""

    def test_get_payment_methods_eur_germany(self, monkeypatch):
        """Test getting payment methods for EUR in Germany."""
        captured = {}

        def fake_urlopen(request, timeout=0):
            captured["url"] = request.full_url
            return FakeResponse(
                200,
                {
                    "success": True,
                    "merchantCountry": "DE",
                    "customerCountry": "DE",
                    "currency": "EUR",
                    "paymentMethods": [
                        {"type": "card", "name": "Credit Card", "icon": "card.png"},
                        {
                            "type": "sepa_debit",
                            "name": "SEPA Direct Debit",
                            "icon": "sepa.png",
                        },
                        {"type": "ideal", "name": "iDEAL", "icon": "ideal.png"},
                        {"type": "giropay", "name": "giropay", "icon": "giropay.png"},
                    ],
                },
            )

        monkeypatch.setattr("delopay.http.urlopen", fake_urlopen)

        client = DelopayClient(api_key="test_key", base_url="https://api.test.com")
        result = client.providers.get_stripe_payment_methods(
            merchant_country="DE",
            customer_country="DE",
            currency="EUR",
        )

        assert "stripe/payment-methods" in captured["url"]
        assert "merchantCountry=DE" in captured["url"]
        assert "customerCountry=DE" in captured["url"]
        assert "currency=EUR" in captured["url"]
        assert result.success is True
        assert len(result.payment_methods) == 4
        assert any(m.type == "ideal" for m in result.payment_methods)

    def test_get_payment_methods_without_currency(self, monkeypatch):
        """Test getting payment methods without currency parameter."""
        captured = {}

        def fake_urlopen(request, timeout=0):
            captured["url"] = request.full_url
            return FakeResponse(
                200,
                {
                    "success": True,
                    "merchantCountry": "US",
                    "customerCountry": "US",
                    "currency": None,
                    "paymentMethods": [
                        {"type": "card", "name": "Credit Card", "icon": "card.png"},
                        {
                            "type": "ach_debit",
                            "name": "ACH Direct Debit",
                            "icon": "ach.png",
                        },
                    ],
                },
            )

        monkeypatch.setattr("delopay.http.urlopen", fake_urlopen)

        client = DelopayClient(api_key="test_key", base_url="https://api.test.com")
        result = client.providers.get_stripe_payment_methods(
            merchant_country="US",
            customer_country="US",
        )

        assert "merchantCountry=US" in captured["url"]
        assert "customerCountry=US" in captured["url"]
        assert "currency" not in captured["url"]
        assert len(result.payment_methods) == 2

    def test_get_payment_methods_invalid_country(self, monkeypatch):
        """Test handling invalid country code."""
        import io

        def fake_urlopen(request, timeout=0):
            raise HTTPError(
                url=request.full_url,
                code=400,
                msg="Bad Request",
                hdrs={},
                fp=io.BytesIO(
                    b'{"message":"Invalid country code","code":"E_INVALID_COUNTRY"}'
                ),
            )

        monkeypatch.setattr("delopay.http.urlopen", fake_urlopen)

        client = DelopayClient(api_key="test_key", base_url="https://api.test.com")
        from delopay import ApiError

        with pytest.raises(ApiError) as exc:
            client.providers.get_stripe_payment_methods(
                merchant_country="XX",
                customer_country="DE",
            )

        assert exc.value.status == 400
        assert exc.value.code == "E_INVALID_COUNTRY"
