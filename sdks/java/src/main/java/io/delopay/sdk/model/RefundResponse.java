package io.delopay.sdk.model;

import java.math.BigDecimal;
import java.time.OffsetDateTime;

public record RefundResponse(
        String refundId,
        String paymentId,
        String providerRefundId,
        BigDecimal amount,
        BigDecimal originalAmount,
        BigDecimal remainingAmount,
        String status,
        String reason,
        OffsetDateTime createdAt,
        OffsetDateTime completedAt,
        String errorMessage
) {
}
