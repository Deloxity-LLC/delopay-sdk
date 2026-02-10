from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any

from .http import HttpClient
from .models import (
    CreatePaymentRequest,
    PaymentResponse,
    RefundPaymentRequest,
    RefundResponse,
    ResendCallbacksResponse,
    UpdatePaymentRequest,
)


class PaymentsClient:
    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def create(self, request: CreatePaymentRequest | dict[str, Any]) -> PaymentResponse:
        raw = self._http.request("POST", "/api/payments/create", _to_payload(request))
        return PaymentResponse.from_dict(raw or {})

    def get(self, payment_id: str) -> PaymentResponse:
        raw = self._http.request("GET", f"/api/payments/{payment_id}")
        return PaymentResponse.from_dict(raw or {})

    def get_by_order(self, client_order_id: str) -> PaymentResponse:
        raw = self._http.request("GET", f"/api/payments/by-order/{client_order_id}")
        return PaymentResponse.from_dict(raw or {})

    def update(self, payment_id: str, request: UpdatePaymentRequest | dict[str, Any]) -> PaymentResponse:
        raw = self._http.request("PUT", f"/api/payments/{payment_id}", _to_payload(request))
        return PaymentResponse.from_dict(raw or {})

    def capture(self, payment_id: str) -> PaymentResponse:
        raw = self._http.request("POST", f"/api/payments/{payment_id}/capture")
        return PaymentResponse.from_dict(raw or {})

    def refund(self, payment_id: str, request: RefundPaymentRequest | dict[str, Any]) -> RefundResponse:
        raw = self._http.request("POST", f"/api/payments/{payment_id}/refund", _to_payload(request))
        return RefundResponse.from_dict(raw or {})

    def resend_failed_callbacks(self) -> ResendCallbacksResponse:
        raw = self._http.request("POST", "/api/payments/resend-failed-callbacks")
        return ResendCallbacksResponse.from_dict(raw or {})


def _to_payload(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value

    if hasattr(value, "to_payload"):
        return value.to_payload()

    if is_dataclass(value):
        return asdict(value)

    raise TypeError("Unsupported payload type")
