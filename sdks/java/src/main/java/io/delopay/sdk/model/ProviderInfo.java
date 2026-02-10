package io.delopay.sdk.model;

import java.util.List;

public record ProviderInfo(
        String id,
        String name,
        boolean enabled,
        List<String> supportedCurrencies,
        List<String> features,
        List<String> supportedCrypto
) {
}
