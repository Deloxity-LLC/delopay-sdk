package io.delopay.sdk;

public record DelopayClientOptions(
        String apiKey,
        String baseUrl,
        int timeoutMs,
        int maxRetries
) {
    public DelopayClientOptions {
        if (apiKey == null || apiKey.isBlank()) {
            throw new IllegalArgumentException("apiKey is required");
        }
    }

    public static DelopayClientOptions defaults(String apiKey) {
        return new DelopayClientOptions(apiKey, "https://sandbox-delopay.deloxity.com", 30_000, 2);
    }
}
