package io.delopay.sdk;

import io.delopay.sdk.internal.HttpExecutor;

public final class DelopayClient {
    private final PaymentsClient payments;
    private final ProvidersClient providers;

    public DelopayClient(String apiKey) {
        this(DelopayClientOptions.defaults(apiKey));
    }

    public DelopayClient(DelopayClientOptions options) {
        HttpExecutor httpExecutor = new HttpExecutor(options);
        this.payments = new PaymentsClient(httpExecutor);
        this.providers = new ProvidersClient(httpExecutor);
    }

    public PaymentsClient payments() {
        return payments;
    }

    public ProvidersClient providers() {
        return providers;
    }
}
