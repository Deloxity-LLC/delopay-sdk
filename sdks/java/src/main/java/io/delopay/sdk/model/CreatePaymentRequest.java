package io.delopay.sdk.model;

import java.math.BigDecimal;
import java.util.Map;

public record CreatePaymentRequest(
        String clientOrderId,
        String provider,
        BigDecimal amount,
        String currency,
        String description,
        String customerEmail,
        String successUrl,
        String cancelUrl,
        String callbackUrl,
        Map<String, Object> metadata,
        Boolean autoCapture
) {
}
