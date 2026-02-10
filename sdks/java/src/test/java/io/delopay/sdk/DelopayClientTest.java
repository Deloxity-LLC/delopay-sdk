package io.delopay.sdk;

import io.delopay.sdk.model.CreatePaymentRequest;
import okhttp3.mockwebserver.MockResponse;
import okhttp3.mockwebserver.MockWebServer;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.io.IOException;
import java.math.BigDecimal;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

class DelopayClientTest {
    private MockWebServer server;

    @BeforeEach
    void setUp() throws IOException {
        server = new MockWebServer();
        server.start();
    }

    @AfterEach
    void tearDown() throws IOException {
        server.shutdown();
    }

    @Test
    void sendsAuthorizationHeader() throws Exception {
        server.enqueue(new MockResponse()
                .setResponseCode(200)
                .setHeader("Content-Type", "application/json")
                .setBody("{" +
                        "\"paymentId\":\"pay_1\"," +
                        "\"clientOrderId\":\"order_1\"," +
                        "\"provider\":\"STRIPE\"," +
                        "\"status\":\"PENDING\"," +
                        "\"amount\":10," +
                        "\"currency\":\"EUR\"}"));

        DelopayClient client = new DelopayClient(new DelopayClientOptions(
                "api_key",
                server.url("/").toString(),
                10_000,
                2
        ));

        assertNotNull(client.payments().get("pay_1"));
        var request = server.takeRequest();
        assertEquals("Bearer api_key", request.getHeader("Authorization"));
    }

    @Test
    void retriesOnlyIdempotentGetRequests() {
        server.enqueue(new MockResponse().setResponseCode(500).setBody("{\"message\":\"temporary\"}"));
        server.enqueue(new MockResponse()
                .setResponseCode(200)
                .setHeader("Content-Type", "application/json")
                .setBody("{" +
                        "\"paymentId\":\"pay_1\"," +
                        "\"clientOrderId\":\"order_1\"," +
                        "\"provider\":\"STRIPE\"," +
                        "\"status\":\"PENDING\"," +
                        "\"amount\":10," +
                        "\"currency\":\"EUR\"}"));

        DelopayClient client = new DelopayClient(new DelopayClientOptions(
                "api_key",
                server.url("/").toString(),
                10_000,
                2
        ));

        assertNotNull(client.payments().get("pay_1"));
        assertEquals(2, server.getRequestCount());
    }

    @Test
    void doesNotRetryPostRequests() {
        server.enqueue(new MockResponse().setResponseCode(500).setBody("{\"message\":\"boom\"}"));

        DelopayClient client = new DelopayClient(new DelopayClientOptions(
                "api_key",
                server.url("/").toString(),
                10_000,
                2
        ));

        CreatePaymentRequest payload = new CreatePaymentRequest(
                "order_1",
                "STRIPE",
                BigDecimal.TEN,
                "EUR",
                null,
                null,
                "https://ok",
                "https://cancel",
                null,
                Map.of(),
                true
        );

        assertThrows(ApiError.class, () -> client.payments().create(payload));
        assertEquals(1, server.getRequestCount());
    }

    @Test
    void mapsApiErrorFields() {
        server.enqueue(new MockResponse()
                .setResponseCode(400)
                .setHeader("x-request-id", "req_123")
                .setBody("{\"message\":\"Invalid\",\"code\":\"E_INVALID\"}"));

        DelopayClient client = new DelopayClient(new DelopayClientOptions(
                "api_key",
                server.url("/").toString(),
                10_000,
                2
        ));

        ApiError error = assertThrows(ApiError.class, () -> client.payments().get("pay_1"));
        assertEquals(400, error.status());
        assertEquals("E_INVALID", error.code());
        assertEquals("req_123", error.requestId());
    }

    @Test
    void generatedDirectoryExists() {
        assertTrue(Files.exists(Path.of("generated", "README.md")));
    }
}
