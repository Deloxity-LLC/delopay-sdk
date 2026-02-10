package io.delopay.sdk.model;

import java.math.BigDecimal;
import java.time.OffsetDateTime;
import java.util.Map;

public record PaymentResponse(
        String paymentId,
        String clientOrderId,
        String provider,
        String status,
        BigDecimal amount,
        BigDecimal amountPaid,
        String currency,
        String description,
        String customerEmail,
        String checkoutUrl,
        String providerPaymentId,
        OffsetDateTime createdAt,
        OffsetDateTime completedAt,
        OffsetDateTime expiresAt,
        Map<String, Object> metadata,
        String errorMessage
) {
}
