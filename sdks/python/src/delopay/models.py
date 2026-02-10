from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


def _drop_none(payload: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if value is not None}


@dataclass(slots=True)
class CreatePaymentRequest:
    client_order_id: str
    provider: str
    amount: float
    currency: str
    success_url: str
    cancel_url: str
    description: str | None = None
    customer_email: str | None = None
    callback_url: str | None = None
    metadata: dict[str, Any] | None = None
    auto_capture: bool | None = None

    def to_payload(self) -> dict[str, Any]:
        payload = {
            "clientOrderId": self.client_order_id,
            "provider": self.provider,
            "amount": self.amount,
            "currency": self.currency,
            "successUrl": self.success_url,
            "cancelUrl": self.cancel_url,
            "description": self.description,
            "customerEmail": self.customer_email,
            "callbackUrl": self.callback_url,
            "metadata": self.metadata,
            "autoCapture": self.auto_capture,
        }
        return _drop_none(payload)


@dataclass(slots=True)
class UpdatePaymentRequest:
    metadata: dict[str, Any] | None = None
    callback_url: str | None = None
    description: str | None = None
    customer_email: str | None = None
    amount: float | None = None
    amount_paid: float | None = None
    currency: str | None = None
    status: str | None = None

    def to_payload(self) -> dict[str, Any]:
        payload = {
            "metadata": self.metadata,
            "callbackUrl": self.callback_url,
            "description": self.description,
            "customerEmail": self.customer_email,
            "amount": self.amount,
            "amountPaid": self.amount_paid,
            "currency": self.currency,
            "status": self.status,
        }
        return _drop_none(payload)


@dataclass(slots=True)
class RefundPaymentRequest:
    amount: float | None = None
    reason: str | None = None

    def to_payload(self) -> dict[str, Any]:
        return _drop_none(asdict(self))


@dataclass(slots=True)
class PaymentResponse:
    payment_id: str | None = None
    client_order_id: str | None = None
    provider: str | None = None
    status: str | None = None
    amount: float | None = None
    amount_paid: float | None = None
    currency: str | None = None
    description: str | None = None
    customer_email: str | None = None
    checkout_url: str | None = None
    provider_payment_id: str | None = None
    created_at: str | None = None
    completed_at: str | None = None
    expires_at: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    error_message: str | None = None

    @staticmethod
    def from_dict(raw: dict[str, Any]) -> "PaymentResponse":
        return PaymentResponse(
            payment_id=raw.get("paymentId"),
            client_order_id=raw.get("clientOrderId"),
            provider=raw.get("provider"),
            status=raw.get("status"),
            amount=raw.get("amount"),
            amount_paid=raw.get("amountPaid"),
            currency=raw.get("currency"),
            description=raw.get("description"),
            customer_email=raw.get("customerEmail"),
            checkout_url=raw.get("checkoutUrl"),
            provider_payment_id=raw.get("providerPaymentId"),
            created_at=raw.get("createdAt"),
            completed_at=raw.get("completedAt"),
            expires_at=raw.get("expiresAt"),
            metadata=raw.get("metadata") or {},
            error_message=raw.get("errorMessage"),
        )


@dataclass(slots=True)
class RefundResponse:
    refund_id: str | None = None
    payment_id: str | None = None
    provider_refund_id: str | None = None
    amount: float | None = None
    original_amount: float | None = None
    remaining_amount: float | None = None
    status: str | None = None
    reason: str | None = None
    created_at: str | None = None
    completed_at: str | None = None
    error_message: str | None = None

    @staticmethod
    def from_dict(raw: dict[str, Any]) -> "RefundResponse":
        return RefundResponse(
            refund_id=raw.get("refundId"),
            payment_id=raw.get("paymentId"),
            provider_refund_id=raw.get("providerRefundId"),
            amount=raw.get("amount"),
            original_amount=raw.get("originalAmount"),
            remaining_amount=raw.get("remainingAmount"),
            status=raw.get("status"),
            reason=raw.get("reason"),
            created_at=raw.get("createdAt"),
            completed_at=raw.get("completedAt"),
            error_message=raw.get("errorMessage"),
        )


@dataclass(slots=True)
class ResendCallbacksResponse:
    resent: int = 0

    @staticmethod
    def from_dict(raw: dict[str, Any]) -> "ResendCallbacksResponse":
        return ResendCallbacksResponse(resent=int(raw.get("resent", 0)))


@dataclass(slots=True)
class ProviderInfo:
    id: str | None = None
    name: str | None = None
    enabled: bool = False
    supported_currencies: list[str] = field(default_factory=list)
    features: list[str] = field(default_factory=list)
    supported_crypto: list[str] = field(default_factory=list)

    @staticmethod
    def from_dict(raw: dict[str, Any]) -> "ProviderInfo":
        return ProviderInfo(
            id=raw.get("id"),
            name=raw.get("name"),
            enabled=bool(raw.get("enabled", False)),
            supported_currencies=list(raw.get("supportedCurrencies") or []),
            features=list(raw.get("features") or []),
            supported_crypto=list(raw.get("supportedCrypto") or []),
        )


@dataclass(slots=True)
class ProviderListResponse:
    providers: list[ProviderInfo] = field(default_factory=list)

    @staticmethod
    def from_dict(raw: dict[str, Any]) -> "ProviderListResponse":
        return ProviderListResponse(
            providers=[
                ProviderInfo.from_dict(item) for item in raw.get("providers") or []
            ]
        )


@dataclass(slots=True)
class ProviderClientConfig:
    provider: str | None = None
    publishable_key: str | None = None
    client_id: str | None = None

    @staticmethod
    def from_dict(raw: dict[str, Any]) -> "ProviderClientConfig":
        return ProviderClientConfig(
            provider=raw.get("provider"),
            publishable_key=raw.get("publishableKey"),
            client_id=raw.get("clientId"),
        )


@dataclass(slots=True)
class PaymentMethodDetail:
    type: str | None = None
    name: str | None = None
    icon: str | None = None

    @staticmethod
    def from_dict(raw: dict[str, Any]) -> "PaymentMethodDetail":
        return PaymentMethodDetail(
            type=raw.get("type"),
            name=raw.get("name"),
            icon=raw.get("icon"),
        )


@dataclass(slots=True)
class PaymentMethodsResponse:
    success: bool = False
    merchant_country: str | None = None
    customer_country: str | None = None
    currency: str | None = None
    payment_methods: list[PaymentMethodDetail] = field(default_factory=list)

    @staticmethod
    def from_dict(raw: dict[str, Any]) -> "PaymentMethodsResponse":
        return PaymentMethodsResponse(
            success=bool(raw.get("success", False)),
            merchant_country=raw.get("merchantCountry"),
            customer_country=raw.get("customerCountry"),
            currency=raw.get("currency"),
            payment_methods=[
                PaymentMethodDetail.from_dict(item)
                for item in raw.get("paymentMethods") or []
            ],
        )
