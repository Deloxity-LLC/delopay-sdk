package io.delopay.sdk;

import io.delopay.sdk.internal.HttpExecutor;
import io.delopay.sdk.model.PaymentMethodsResponse;
import io.delopay.sdk.model.ProviderClientConfig;
import io.delopay.sdk.model.ProviderListResponse;

import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.LinkedHashMap;
import java.util.Map;

public final class ProvidersClient {
    private final HttpExecutor http;

    ProvidersClient(HttpExecutor http) {
        this.http = http;
    }

    public ProviderListResponse list() {
        return http.send("GET", "/api/providers", null, ProviderListResponse.class);
    }

    public ProviderClientConfig getClientConfig(String providerId) {
        return http.send("GET", "/api/providers/" + encode(providerId) + "/client-config", null, ProviderClientConfig.class);
    }

    public PaymentMethodsResponse getStripePaymentMethods(String merchantCountry, String customerCountry, String currency) {
        Map<String, String> query = new LinkedHashMap<>();
        query.put("merchantCountry", merchantCountry);
        query.put("customerCountry", customerCountry);
        if (currency != null && !currency.isBlank()) {
            query.put("currency", currency);
        }

        return http.send("GET", "/api/providers/stripe/payment-methods", query, null, PaymentMethodsResponse.class);
    }

    private static String encode(String value) {
        return URLEncoder.encode(value, StandardCharsets.UTF_8);
    }
}
