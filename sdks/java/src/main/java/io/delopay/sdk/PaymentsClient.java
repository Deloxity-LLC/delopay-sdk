package io.delopay.sdk;

import io.delopay.sdk.internal.HttpExecutor;
import io.delopay.sdk.model.CreatePaymentRequest;
import io.delopay.sdk.model.PaymentResponse;
import io.delopay.sdk.model.RefundPaymentRequest;
import io.delopay.sdk.model.RefundResponse;
import io.delopay.sdk.model.ResendCallbacksResponse;
import io.delopay.sdk.model.UpdatePaymentRequest;

import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;

public final class PaymentsClient {
    private final HttpExecutor http;

    PaymentsClient(HttpExecutor http) {
        this.http = http;
    }

    public PaymentResponse create(CreatePaymentRequest input) {
        return http.send("POST", "/api/payments/create", input, PaymentResponse.class);
    }

    public PaymentResponse get(String paymentId) {
        return http.send("GET", "/api/payments/" + encode(paymentId), null, PaymentResponse.class);
    }

    public PaymentResponse getByOrder(String clientOrderId) {
        return http.send("GET", "/api/payments/by-order/" + encode(clientOrderId), null, PaymentResponse.class);
    }

    public PaymentResponse update(String paymentId, UpdatePaymentRequest input) {
        return http.send("PUT", "/api/payments/" + encode(paymentId), input, PaymentResponse.class);
    }

    public PaymentResponse capture(String paymentId) {
        return http.send("POST", "/api/payments/" + encode(paymentId) + "/capture", null, PaymentResponse.class);
    }

    public RefundResponse refund(String paymentId, RefundPaymentRequest input) {
        return http.send("POST", "/api/payments/" + encode(paymentId) + "/refund", input, RefundResponse.class);
    }

    public ResendCallbacksResponse resendFailedCallbacks() {
        return http.send("POST", "/api/payments/resend-failed-callbacks", null, ResendCallbacksResponse.class);
    }

    private static String encode(String value) {
        return URLEncoder.encode(value, StandardCharsets.UTF_8);
    }
}
