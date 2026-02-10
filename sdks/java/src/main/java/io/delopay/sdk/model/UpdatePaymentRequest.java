package io.delopay.sdk.model;

import java.math.BigDecimal;
import java.util.Map;

public record UpdatePaymentRequest(
        Map<String, Object> metadata,
        String callbackUrl,
        String description,
        String customerEmail,
        BigDecimal amount,
        BigDecimal amountPaid,
        String currency,
        String status
) {
}
