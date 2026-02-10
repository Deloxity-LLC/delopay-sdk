from __future__ import annotations

import io
import json
from pathlib import Path
from urllib.error import HTTPError, URLError

import pytest

from delopay import ApiError, CreatePaymentRequest, DelopayClient


class FakeResponse:
    def __init__(self, status: int, payload: dict | None = None, headers: dict | None = None) -> None:
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


def test_auth_header_is_set(monkeypatch):
    captured = {}

    def fake_urlopen(request, timeout=0):
        captured["authorization"] = request.headers.get("Authorization")
        return FakeResponse(
            200,
            {
                "paymentId": "pay_1",
                "clientOrderId": "order_1",
                "provider": "STRIPE",
                "status": "PENDING",
                "amount": 10,
                "currency": "EUR",
            },
        )

    monkeypatch.setattr("delopay.http.urlopen", fake_urlopen)

    client = DelopayClient(api_key="api_key", base_url="https://api.example.com")
    response = client.payments.get("pay_1")

    assert response.payment_id == "pay_1"
    assert captured["authorization"] == "Bearer api_key"


def test_retry_for_get_only(monkeypatch):
    calls = {"count": 0}

    def fake_urlopen(request, timeout=0):
        calls["count"] += 1
        if calls["count"] == 1:
            raise URLError("offline")
        return FakeResponse(
            200,
            {
                "paymentId": "pay_1",
                "clientOrderId": "order_1",
                "provider": "STRIPE",
                "status": "PENDING",
                "amount": 10,
                "currency": "EUR",
            },
        )

    monkeypatch.setattr("delopay.http.urlopen", fake_urlopen)

    client = DelopayClient(api_key="api_key", base_url="https://api.example.com", max_retries=2)
    client.payments.get("pay_1")

    assert calls["count"] == 2


def test_no_retry_for_post(monkeypatch):
    calls = {"count": 0}

    def fake_urlopen(request, timeout=0):
        calls["count"] += 1
        raise URLError("offline")

    monkeypatch.setattr("delopay.http.urlopen", fake_urlopen)

    client = DelopayClient(api_key="api_key", base_url="https://api.example.com", max_retries=2)

    with pytest.raises(ApiError) as exc:
        client.payments.create(
            CreatePaymentRequest(
                client_order_id="order_1",
                provider="STRIPE",
                amount=10,
                currency="EUR",
                success_url="https://ok",
                cancel_url="https://cancel",
            )
        )

    assert exc.value.status == 0
    assert calls["count"] == 1


def test_api_error_mapping(monkeypatch):
    def fake_urlopen(request, timeout=0):
        raise HTTPError(
            url=request.full_url,
            code=400,
            msg="Bad Request",
            hdrs={"x-request-id": "req_123"},
            fp=io.BytesIO(b'{"message":"Invalid request","code":"E_INVALID"}'),
        )

    monkeypatch.setattr("delopay.http.urlopen", fake_urlopen)

    client = DelopayClient(api_key="api_key", base_url="https://api.example.com")

    with pytest.raises(ApiError) as exc:
        client.payments.get("pay_1")

    assert exc.value.status == 400
    assert exc.value.code == "E_INVALID"
    assert exc.value.request_id == "req_123"


def test_generated_directory_exists():
    assert (Path(__file__).resolve().parents[1] / "generated" / "README.md").exists()
