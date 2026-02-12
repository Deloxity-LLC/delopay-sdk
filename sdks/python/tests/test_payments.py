"""Comprehensive tests for PaymentsClient."""

from __future__ import annotations

import io
import json
from urllib.error import HTTPError

import pytest

from delopay import (
    ApiError,
    CreatePaymentRequest,
    DelopayClient,
    RefundPaymentRequest,
    UpdatePaymentRequest,
)


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


def create_payment_response(payment_id: str, **overrides) -> dict:
    """Create a standard payment response."""
    return {
        "paymentId": payment_id,
        "clientOrderId": "order_123",
        "provider": "STRIPE",
        "status": "PENDING",
        "amount": 100.0,
        "currency": "EUR",
        "description": "Test payment",
        "customerEmail": "test@example.com",
        "checkoutUrl": "https://checkout.example.com",
        "providerPaymentId": "pi_123",
        "createdAt": "2026-02-12T10:00:00Z",
        "metadata": {"orderId": "internal_123"},
        **overrides,
    }


class TestPaymentsCreate:
    """Test payment creation."""

    def test_create_payment_with_all_fields(self, monkeypatch):
        """Test creating a payment with all optional fields."""
        captured = {}

        def fake_urlopen(request, timeout=0):
            captured["url"] = request.full_url
            captured["method"] = request.method
            captured["body"] = json.loads(request.data) if request.data else None
            return FakeResponse(
                200,
                create_payment_response(
                    "pay_new_123",
                    status="PENDING",
                    checkoutUrl="https://checkout.stripe.com/test",
                ),
            )

        monkeypatch.setattr("delopay.http.urlopen", fake_urlopen)

        client = DelopayClient(api_key="test_key", base_url="https://api.test.com")
        result = client.payments.create(
            CreatePaymentRequest(
                client_order_id="order_123",
                provider="STRIPE",
                amount=100.0,
                currency="EUR",
                success_url="https://shop.test/success",
                cancel_url="https://shop.test/cancel",
                description="Test payment",
                customer_email="customer@test.com",
                callback_url="https://shop.test/webhook",
                metadata={"orderId": "internal_123"},
                auto_capture=True,
            )
        )

        assert captured["url"] == "https://api.test.com/api/payments/create"
        assert captured["method"] == "POST"
        assert captured["body"]["clientOrderId"] == "order_123"
        assert captured["body"]["provider"] == "STRIPE"
        assert captured["body"]["amount"] == 100.0
        assert captured["body"]["successUrl"] == "https://shop.test/success"
        assert captured["body"]["autoCapture"] is True

        assert result.payment_id == "pay_new_123"
        assert result.status == "PENDING"

    def test_create_payment_with_minimal_fields(self, monkeypatch):
        """Test creating a payment with only required fields."""
        captured = {}

        def fake_urlopen(request, timeout=0):
            captured["body"] = json.loads(request.data) if request.data else None
            return FakeResponse(200, create_payment_response("pay_minimal"))

        monkeypatch.setattr("delopay.http.urlopen", fake_urlopen)

        client = DelopayClient(api_key="test_key", base_url="https://api.test.com")
        client.payments.create(
            CreatePaymentRequest(
                client_order_id="minimal_order",
                provider="PAYPAL",
                amount=50.0,
                currency="USD",
                success_url="https://test.com/success",
                cancel_url="https://test.com/cancel",
            )
        )

        assert "autoCapture" not in captured["body"]
        assert "metadata" not in captured["body"]

    def test_create_payment_validation_error(self, monkeypatch):
        """Test validation error handling on create."""

        def fake_urlopen(request, timeout=0):
            raise HTTPError(
                url=request.full_url,
                code=400,
                msg="Bad Request",
                hdrs={"x-request-id": "req_456"},
                fp=io.BytesIO(
                    b'{"message":"Invalid currency","code":"E_INVALID_CURRENCY"}'
                ),
            )

        monkeypatch.setattr("delopay.http.urlopen", fake_urlopen)

        client = DelopayClient(api_key="test_key", base_url="https://api.test.com")
        with pytest.raises(ApiError) as exc:
            client.payments.create(
                CreatePaymentRequest(
                    client_order_id="order_test",
                    provider="STRIPE",
                    amount=100.0,
                    currency="INVALID",
                    success_url="https://test.com/success",
                    cancel_url="https://test.com/cancel",
                )
            )

        assert exc.value.status == 400
        assert exc.value.code == "E_INVALID_CURRENCY"


class TestPaymentsGet:
    """Test getting payments."""

    def test_get_payment_by_id(self, monkeypatch):
        """Test getting a payment by ID."""
        captured = {}

        def fake_urlopen(request, timeout=0):
            captured["url"] = request.full_url
            return FakeResponse(
                200,
                create_payment_response(
                    "pay_existing",
                    status="COMPLETED",
                    completedAt="2026-02-12T11:00:00Z",
                    amountPaid=100.0,
                ),
            )

        monkeypatch.setattr("delopay.http.urlopen", fake_urlopen)

        client = DelopayClient(api_key="test_key", base_url="https://api.test.com")
        result = client.payments.get("pay_existing")

        assert captured["url"] == "https://api.test.com/api/payments/pay_existing"
        assert result.payment_id == "pay_existing"
        assert result.status == "COMPLETED"
        assert result.completed_at == "2026-02-12T11:00:00Z"
        assert result.amount_paid == 100.0

    def test_get_payment_not_found(self, monkeypatch):
        """Test handling of non-existent payment."""

        def fake_urlopen(request, timeout=0):
            raise HTTPError(
                url=request.full_url,
                code=404,
                msg="Not Found",
                hdrs={"x-request-id": "req_789"},
                fp=io.BytesIO(b'{"message":"Payment not found","code":"E_NOT_FOUND"}'),
            )

        monkeypatch.setattr("delopay.http.urlopen", fake_urlopen)

        client = DelopayClient(api_key="test_key", base_url="https://api.test.com")
        with pytest.raises(ApiError) as exc:
            client.payments.get("pay_nonexistent")

        assert exc.value.status == 404
        assert exc.value.code == "E_NOT_FOUND"

    def test_get_payment_with_special_chars(self, monkeypatch):
        """Test getting a payment with special characters in ID."""
        captured = {}

        def fake_urlopen(request, timeout=0):
            captured["url"] = request.full_url
            return FakeResponse(200, create_payment_response("pay_special"))

        monkeypatch.setattr("delopay.http.urlopen", fake_urlopen)

        client = DelopayClient(api_key="test_key", base_url="https://api.test.com")
        client.payments.get("pay test/id")

        assert captured["url"] == "https://api.test.com/api/payments/pay%20test%2Fid"


class TestPaymentsGetByOrder:
    """Test getting payments by order ID."""

    def test_get_payment_by_order_id(self, monkeypatch):
        """Test getting a payment by client order ID."""
        captured = {}

        def fake_urlopen(request, timeout=0):
            captured["url"] = request.full_url
            return FakeResponse(
                200,
                create_payment_response(
                    "pay_by_order",
                    clientOrderId="my_custom_order_123",
                ),
            )

        monkeypatch.setattr("delopay.http.urlopen", fake_urlopen)

        client = DelopayClient(api_key="test_key", base_url="https://api.test.com")
        result = client.payments.get_by_order("my_custom_order_123")

        assert (
            captured["url"]
            == "https://api.test.com/api/payments/by-order/my_custom_order_123"
        )
        assert result.client_order_id == "my_custom_order_123"

    def test_get_payment_by_order_id_with_special_chars(self, monkeypatch):
        """Test URL encoding when order ID contains special characters."""
        captured = {}

        def fake_urlopen(request, timeout=0):
            captured["url"] = request.full_url
            return FakeResponse(
                200,
                create_payment_response(
                    "pay_by_order_encoded",
                    clientOrderId="order#123/test",
                ),
            )

        monkeypatch.setattr("delopay.http.urlopen", fake_urlopen)

        client = DelopayClient(api_key="test_key", base_url="https://api.test.com")
        result = client.payments.get_by_order("order#123/test")

        assert (
            captured["url"]
            == "https://api.test.com/api/payments/by-order/order%23123%2Ftest"
        )
        assert result.client_order_id == "order#123/test"


class TestPaymentsUpdate:
    """Test updating payments."""

    def test_update_payment_metadata(self, monkeypatch):
        """Test updating payment metadata."""
        captured = {}

        def fake_urlopen(request, timeout=0):
            captured["url"] = request.full_url
            captured["method"] = request.method
            captured["body"] = json.loads(request.data) if request.data else None
            return FakeResponse(
                200,
                create_payment_response(
                    "pay_update",
                    metadata={"updated": "true", "orderId": "123"},
                ),
            )

        monkeypatch.setattr("delopay.http.urlopen", fake_urlopen)

        client = DelopayClient(api_key="test_key", base_url="https://api.test.com")
        result = client.payments.update(
            "pay_update",
            UpdatePaymentRequest(
                metadata={"updated": "true"},
                description="Updated description",
            ),
        )

        assert captured["url"] == "https://api.test.com/api/payments/pay_update"
        assert captured["method"] == "PUT"
        assert captured["body"]["metadata"] == {"updated": "true"}
        assert captured["body"]["description"] == "Updated description"
        assert result.metadata == {"updated": "true", "orderId": "123"}


class TestPaymentsCapture:
    """Test capturing payments."""

    def test_capture_authorized_payment(self, monkeypatch):
        """Test capturing an authorized payment."""
        captured = {}

        def fake_urlopen(request, timeout=0):
            captured["url"] = request.full_url
            captured["method"] = request.method
            return FakeResponse(
                200,
                create_payment_response("pay_capture", status="NEEDS_CAPTURING"),
            )

        monkeypatch.setattr("delopay.http.urlopen", fake_urlopen)

        client = DelopayClient(api_key="test_key", base_url="https://api.test.com")
        result = client.payments.capture("pay_auth")

        assert captured["url"] == "https://api.test.com/api/payments/pay_auth/capture"
        assert captured["method"] == "POST"
        assert result.status == "NEEDS_CAPTURING"

    def test_capture_already_captured(self, monkeypatch):
        """Test capturing an already captured payment."""

        def fake_urlopen(request, timeout=0):
            raise HTTPError(
                url=request.full_url,
                code=400,
                msg="Bad Request",
                hdrs={},
                fp=io.BytesIO(
                    b'{"message":"Payment already captured",'
                    b'"code":"E_ALREADY_CAPTURED"}'
                ),
            )

        monkeypatch.setattr("delopay.http.urlopen", fake_urlopen)

        client = DelopayClient(api_key="test_key", base_url="https://api.test.com")
        with pytest.raises(ApiError) as exc:
            client.payments.capture("pay_captured")

        assert exc.value.status == 400
        assert exc.value.code == "E_ALREADY_CAPTURED"


class TestPaymentsRefund:
    """Test refunding payments."""

    def test_full_refund(self, monkeypatch):
        """Test processing a full refund."""
        captured = {}

        def fake_urlopen(request, timeout=0):
            captured["body"] = json.loads(request.data) if request.data else None
            return FakeResponse(
                200,
                {
                    "refundId": "ref_123",
                    "paymentId": "pay_refund",
                    "providerRefundId": "re_123",
                    "amount": 100.0,
                    "originalAmount": 100.0,
                    "remainingAmount": 0.0,
                    "status": "PENDING",
                    "reason": "Customer request",
                    "createdAt": "2026-02-12T12:00:00Z",
                },
            )

        monkeypatch.setattr("delopay.http.urlopen", fake_urlopen)

        client = DelopayClient(api_key="test_key", base_url="https://api.test.com")
        result = client.payments.refund(
            "pay_refund",
            RefundPaymentRequest(amount=100.0, reason="Customer request"),
        )

        assert captured["body"]["amount"] == 100.0
        assert captured["body"]["reason"] == "Customer request"
        assert result.refund_id == "ref_123"
        assert result.status == "PENDING"
        assert result.remaining_amount == 0.0

    def test_partial_refund(self, monkeypatch):
        """Test processing a partial refund."""

        def fake_urlopen(request, timeout=0):
            return FakeResponse(
                200,
                {
                    "refundId": "ref_partial",
                    "paymentId": "pay_partial",
                    "amount": 50.0,
                    "originalAmount": 100.0,
                    "remainingAmount": 50.0,
                    "status": "COMPLETED",
                    "reason": None,
                    "createdAt": "2026-02-12T12:00:00Z",
                    "completedAt": "2026-02-12T12:05:00Z",
                },
            )

        monkeypatch.setattr("delopay.http.urlopen", fake_urlopen)

        client = DelopayClient(api_key="test_key", base_url="https://api.test.com")
        result = client.payments.refund(
            "pay_partial",
            RefundPaymentRequest(amount=50.0),
        )

        assert result.amount == 50.0
        assert result.remaining_amount == 50.0
        assert result.completed_at == "2026-02-12T12:05:00Z"

    def test_refund_exceeds_amount(self, monkeypatch):
        """Test refund exceeding payment amount."""

        def fake_urlopen(request, timeout=0):
            raise HTTPError(
                url=request.full_url,
                code=400,
                msg="Bad Request",
                hdrs={},
                fp=io.BytesIO(
                    b'{"message":"Refund amount exceeds payment",'
                    b'"code":"E_REFUND_EXCEEDS"}'
                ),
            )

        monkeypatch.setattr("delopay.http.urlopen", fake_urlopen)

        client = DelopayClient(api_key="test_key", base_url="https://api.test.com")
        with pytest.raises(ApiError) as exc:
            client.payments.refund("pay_small", RefundPaymentRequest(amount=200.0))

        assert exc.value.status == 400
        assert exc.value.code == "E_REFUND_EXCEEDS"


class TestPaymentsResendCallbacks:
    """Test resending failed callbacks."""

    def test_resend_failed_callbacks(self, monkeypatch):
        """Test resending failed callbacks."""
        captured = {}

        def fake_urlopen(request, timeout=0):
            captured["url"] = request.full_url
            captured["method"] = request.method
            return FakeResponse(200, {"resent": 5})

        monkeypatch.setattr("delopay.http.urlopen", fake_urlopen)

        client = DelopayClient(api_key="test_key", base_url="https://api.test.com")
        result = client.payments.resend_failed_callbacks()

        assert (
            captured["url"]
            == "https://api.test.com/api/payments/resend-failed-callbacks"
        )
        assert captured["method"] == "POST"
        assert result.resent == 5

    def test_resend_no_failed_callbacks(self, monkeypatch):
        """Test when no failed callbacks exist."""

        def fake_urlopen(request, timeout=0):
            return FakeResponse(200, {"resent": 0})

        monkeypatch.setattr("delopay.http.urlopen", fake_urlopen)

        client = DelopayClient(api_key="test_key", base_url="https://api.test.com")
        result = client.payments.resend_failed_callbacks()

        assert result.resent == 0
