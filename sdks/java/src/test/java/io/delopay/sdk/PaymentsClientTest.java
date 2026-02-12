package io.delopay.sdk;

import io.delopay.sdk.model.CreatePaymentRequest;
import io.delopay.sdk.model.PaymentResponse;
import io.delopay.sdk.model.RefundPaymentRequest;
import io.delopay.sdk.model.RefundResponse;
import io.delopay.sdk.model.ResendCallbacksResponse;
import io.delopay.sdk.model.UpdatePaymentRequest;
import okhttp3.mockwebserver.MockResponse;
import okhttp3.mockwebserver.MockWebServer;
import okhttp3.mockwebserver.RecordedRequest;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.io.IOException;
import java.math.BigDecimal;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;

class PaymentsClientTest {
    private MockWebServer server;
    private DelopayClient client;

    @BeforeEach
    void setUp() throws IOException {
        server = new MockWebServer();
        server.start();
        client = new DelopayClient(new DelopayClientOptions(
                "test_api_key",
                server.url("/").toString(),
                10_000,
                0
        ));
    }

    @AfterEach
    void tearDown() throws IOException {
        server.shutdown();
    }

    private MockResponse createPaymentResponse(String paymentId, String status) {
        return new MockResponse()
                .setResponseCode(200)
                .setHeader("Content-Type", "application/json")
                .setBody("{" +
                        "\"paymentId\":\"" + paymentId + "\"," +
                        "\"clientOrderId\":\"order_123\"," +
                        "\"provider\":\"STRIPE\"," +
                        "\"status\":\"" + status + "\"," +
                        "\"amount\":100.00," +
                        "\"currency\":\"EUR\"," +
                        "\"description\":\"Test payment\"," +
                        "\"customerEmail\":\"test@example.com\"," +
                        "\"checkoutUrl\":\"https://checkout.example.com\"," +
                        "\"providerPaymentId\":\"pi_123\"," +
                        "\"createdAt\":\"2026-02-12T10:00:00Z\"," +
                        "\"metadata\":{\"orderId\":\"internal_123\"}}");
    }

    @Test
    void createPaymentWithAllFields() throws Exception {
        server.enqueue(createPaymentResponse("pay_new_123", "PENDING"));

        CreatePaymentRequest request = new CreatePaymentRequest(
                "order_123",
                "STRIPE",
                new BigDecimal("100.00"),
                "EUR",
                "Test payment",
                "customer@example.com",
                "https://shop.test/success",
                "https://shop.test/cancel",
                "https://shop.test/webhook",
                Map.of("orderId", "internal_123"),
                true
        );

        PaymentResponse response = client.payments().create(request);

        assertNotNull(response);
        assertEquals("pay_new_123", response.paymentId());
        assertEquals("PENDING", response.status());

        RecordedRequest recordedRequest = server.takeRequest();
        assertEquals("/api/payments/create", recordedRequest.getPath());
        assertEquals("POST", recordedRequest.getMethod());

        String body = recordedRequest.getBody().readUtf8();
        assertTrue(body.contains("\"clientOrderId\":\"order_123\""));
        assertTrue(body.contains("\"provider\":\"STRIPE\""));
        assertTrue(body.contains("\"amount\":100"));
        assertTrue(body.contains("\"autoCapture\":true"));
    }

    @Test
    void createPaymentWithMinimalFields() throws Exception {
        server.enqueue(createPaymentResponse("pay_minimal", "PENDING"));

        CreatePaymentRequest request = new CreatePaymentRequest(
                "minimal_order",
                "PAYPAL",
                new BigDecimal("50.00"),
                "USD",
                null,
                null,
                "https://test.com/success",
                "https://test.com/cancel",
                null,
                null,
                false
        );

        client.payments().create(request);

        RecordedRequest recordedRequest = server.takeRequest();
        String body = recordedRequest.getBody().readUtf8();
        // autoCapture is included with default value
        assertTrue(body.contains("\"autoCapture\":false"));
    }

    @Test
    void createPaymentValidationError() {
        server.enqueue(new MockResponse()
                .setResponseCode(400)
                .setHeader("x-request-id", "req_456")
                .setBody("{\"message\":\"Invalid currency\",\"code\":\"E_INVALID_CURRENCY\"}"));

        CreatePaymentRequest request = new CreatePaymentRequest(
                "order_test",
                "STRIPE",
                new BigDecimal("100.00"),
                "INVALID",
                null,
                null,
                "https://test.com/success",
                "https://test.com/cancel",
                null,
                null,
                false
        );

        ApiError error = assertThrows(ApiError.class, () -> client.payments().create(request));
        assertEquals(400, error.status());
        assertEquals("E_INVALID_CURRENCY", error.code());
    }

    @Test
    void getPaymentById() throws Exception {
        server.enqueue(new MockResponse()
                .setResponseCode(200)
                .setHeader("Content-Type", "application/json")
                .setBody("{" +
                        "\"paymentId\":\"pay_existing\"," +
                        "\"clientOrderId\":\"order_123\"," +
                        "\"provider\":\"STRIPE\"," +
                        "\"status\":\"COMPLETED\"," +
                        "\"amount\":100.00," +
                        "\"amountPaid\":100.00," +
                        "\"currency\":\"EUR\"," +
                        "\"completedAt\":\"2026-02-12T11:00:00Z\"}"));

        PaymentResponse response = client.payments().get("pay_existing");

        assertNotNull(response);
        assertEquals("pay_existing", response.paymentId());
        assertEquals("COMPLETED", response.status());
        assertEquals(new BigDecimal("100.00"), response.amountPaid());

        RecordedRequest request = server.takeRequest();
        assertEquals("/api/payments/pay_existing", request.getPath());
    }

    @Test
    void getPaymentNotFound() {
        server.enqueue(new MockResponse()
                .setResponseCode(404)
                .setHeader("x-request-id", "req_789")
                .setBody("{\"message\":\"Payment not found\",\"code\":\"E_NOT_FOUND\"}"));

        ApiError error = assertThrows(ApiError.class, () -> client.payments().get("pay_nonexistent"));
        assertEquals(404, error.status());
        assertEquals("E_NOT_FOUND", error.code());
    }

    @Test
    void getPaymentUrlEncoding() throws Exception {
        server.enqueue(new MockResponse()
                .setResponseCode(200)
                .setHeader("Content-Type", "application/json")
                .setBody("{\"paymentId\":\"pay_encoded\",\"status\":\"PENDING\"}"));

        client.payments().get("pay test/id");

        RecordedRequest request = server.takeRequest();
        assertEquals("/api/payments/pay+test%2Fid", request.getPath());
    }

    @Test
    void getPaymentByOrderId() throws Exception {
        server.enqueue(new MockResponse()
                .setResponseCode(200)
                .setHeader("Content-Type", "application/json")
                .setBody("{" +
                        "\"paymentId\":\"pay_by_order\"," +
                        "\"clientOrderId\":\"my_custom_order_123\"," +
                        "\"provider\":\"STRIPE\"," +
                        "\"status\":\"PENDING\"," +
                        "\"amount\":100.00," +
                        "\"currency\":\"EUR\"}"));

        PaymentResponse response = client.payments().getByOrder("my_custom_order_123");

        assertNotNull(response);
        assertEquals("my_custom_order_123", response.clientOrderId());

        RecordedRequest request = server.takeRequest();
        assertEquals("/api/payments/by-order/my_custom_order_123", request.getPath());
    }

    @Test
    void updatePayment() throws Exception {
        server.enqueue(new MockResponse()
                .setResponseCode(200)
                .setHeader("Content-Type", "application/json")
                .setBody("{" +
                        "\"paymentId\":\"pay_update\"," +
                        "\"clientOrderId\":\"order_123\"," +
                        "\"provider\":\"STRIPE\"," +
                        "\"status\":\"PENDING\"," +
                        "\"amount\":100.00," +
                        "\"currency\":\"EUR\"," +
                        "\"metadata\":{\"updated\":\"true\",\"orderId\":\"123\"}}"));

        UpdatePaymentRequest request = new UpdatePaymentRequest(
                Map.of("updated", "true"),
                null,
                "Updated description",
                null,
                null,
                null,
                null,
                null
        );

        PaymentResponse response = client.payments().update("pay_update", request);

        assertNotNull(response);
        assertEquals("pay_update", response.paymentId());

        RecordedRequest recordedRequest = server.takeRequest();
        assertEquals("/api/payments/pay_update", recordedRequest.getPath());
        assertEquals("PUT", recordedRequest.getMethod());

        String body = recordedRequest.getBody().readUtf8();
        assertTrue(body.contains("\"metadata\":{\"updated\":\"true\"}"));
        assertTrue(body.contains("\"description\":\"Updated description\""));
    }

    @Test
    void capturePayment() throws Exception {
        server.enqueue(new MockResponse()
                .setResponseCode(200)
                .setHeader("Content-Type", "application/json")
                .setBody("{" +
                        "\"paymentId\":\"pay_capture\"," +
                        "\"clientOrderId\":\"order_123\"," +
                        "\"provider\":\"STRIPE\"," +
                        "\"status\":\"NEEDS_CAPTURING\"," +
                        "\"amount\":100.00," +
                        "\"currency\":\"EUR\"}"));

        PaymentResponse response = client.payments().capture("pay_auth");

        assertNotNull(response);
        assertEquals("NEEDS_CAPTURING", response.status());

        RecordedRequest request = server.takeRequest();
        assertEquals("/api/payments/pay_auth/capture", request.getPath());
        assertEquals("POST", request.getMethod());
    }

    @Test
    void captureAlreadyCapturedPayment() {
        server.enqueue(new MockResponse()
                .setResponseCode(400)
                .setBody("{\"message\":\"Payment already captured\",\"code\":\"E_ALREADY_CAPTURED\"}"));

        ApiError error = assertThrows(ApiError.class, () -> client.payments().capture("pay_captured"));
        assertEquals(400, error.status());
        assertEquals("E_ALREADY_CAPTURED", error.code());
    }

    @Test
    void refundFullAmount() throws Exception {
        server.enqueue(new MockResponse()
                .setResponseCode(200)
                .setHeader("Content-Type", "application/json")
                .setBody("{" +
                        "\"refundId\":\"ref_123\"," +
                        "\"paymentId\":\"pay_refund\"," +
                        "\"providerRefundId\":\"re_123\"," +
                        "\"amount\":100.00," +
                        "\"originalAmount\":100.00," +
                        "\"remainingAmount\":0.00," +
                        "\"status\":\"PENDING\"," +
                        "\"reason\":\"Customer request\"," +
                        "\"createdAt\":\"2026-02-12T12:00:00Z\"}"));

        RefundPaymentRequest request = new RefundPaymentRequest(
                new BigDecimal("100.00"),
                "Customer request"
        );

        RefundResponse response = client.payments().refund("pay_refund", request);

        assertNotNull(response);
        assertEquals("ref_123", response.refundId());
        assertEquals(new BigDecimal("0.00"), response.remainingAmount());

        RecordedRequest recordedRequest = server.takeRequest();
        assertEquals("/api/payments/pay_refund/refund", recordedRequest.getPath());
        assertEquals("POST", recordedRequest.getMethod());

        String body = recordedRequest.getBody().readUtf8();
        assertTrue(body.contains("\"amount\":100"));
        assertTrue(body.contains("\"reason\":\"Customer request\""));
    }

    @Test
    void refundPartialAmount() throws Exception {
        server.enqueue(new MockResponse()
                .setResponseCode(200)
                .setHeader("Content-Type", "application/json")
                .setBody("{" +
                        "\"refundId\":\"ref_partial\"," +
                        "\"paymentId\":\"pay_partial\"," +
                        "\"amount\":50.00," +
                        "\"originalAmount\":100.00," +
                        "\"remainingAmount\":50.00," +
                        "\"status\":\"COMPLETED\"," +
                        "\"reason\":null," +
                        "\"createdAt\":\"2026-02-12T12:00:00Z\"," +
                        "\"completedAt\":\"2026-02-12T12:05:00Z\"}"));

        RefundPaymentRequest request = new RefundPaymentRequest(
                new BigDecimal("50.00"),
                null
        );

        RefundResponse response = client.payments().refund("pay_partial", request);

        assertEquals(new BigDecimal("50.00"), response.amount());
        assertEquals(new BigDecimal("50.00"), response.remainingAmount());
        // Note: Java may parse datetime without seconds
        assertNotNull(response.completedAt());
        assertTrue(response.completedAt().toString().contains("2026-02-12T12:05"));
    }

    @Test
    void refundExceedsAmount() {
        server.enqueue(new MockResponse()
                .setResponseCode(400)
                .setBody("{\"message\":\"Refund amount exceeds payment\",\"code\":\"E_REFUND_EXCEEDS\"}"));

        RefundPaymentRequest request = new RefundPaymentRequest(
                new BigDecimal("200.00"),
                null
        );

        ApiError error = assertThrows(ApiError.class, () -> client.payments().refund("pay_small", request));
        assertEquals(400, error.status());
        assertEquals("E_REFUND_EXCEEDS", error.code());
    }

    @Test
    void resendFailedCallbacks() throws Exception {
        server.enqueue(new MockResponse()
                .setResponseCode(200)
                .setHeader("Content-Type", "application/json")
                .setBody("{\"resent\":5}"));

        ResendCallbacksResponse response = client.payments().resendFailedCallbacks();

        assertNotNull(response);
        assertEquals(5, response.resent());

        RecordedRequest request = server.takeRequest();
        assertEquals("/api/payments/resend-failed-callbacks", request.getPath());
        assertEquals("POST", request.getMethod());
    }

    @Test
    void resendFailedCallbacksNone() throws Exception {
        server.enqueue(new MockResponse()
                .setResponseCode(200)
                .setHeader("Content-Type", "application/json")
                .setBody("{\"resent\":0}"));

        ResendCallbacksResponse response = client.payments().resendFailedCallbacks();

        assertEquals(0, response.resent());
    }
}
