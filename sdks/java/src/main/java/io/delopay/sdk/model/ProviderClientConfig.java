package io.delopay.sdk.model;

public record ProviderClientConfig(
        String provider,
        String publishableKey,
        String clientId
) {
}
