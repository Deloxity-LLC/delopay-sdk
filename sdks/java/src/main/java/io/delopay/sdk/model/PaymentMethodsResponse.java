package io.delopay.sdk.model;

import java.util.List;

public record PaymentMethodsResponse(
        boolean success,
        String merchantCountry,
        String customerCountry,
        String currency,
        List<PaymentMethodDetail> paymentMethods
) {
    public record PaymentMethodDetail(
            String type,
            String name,
            String icon
    ) {
    }
}
