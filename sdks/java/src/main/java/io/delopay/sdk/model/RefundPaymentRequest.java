package io.delopay.sdk.model;

import java.math.BigDecimal;

public record RefundPaymentRequest(
        BigDecimal amount,
        String reason
) {
}
