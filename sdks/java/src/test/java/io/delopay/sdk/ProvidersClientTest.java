package io.delopay.sdk;

import io.delopay.sdk.model.PaymentMethodsResponse;
import io.delopay.sdk.model.ProviderClientConfig;
import io.delopay.sdk.model.ProviderListResponse;
import okhttp3.mockwebserver.MockResponse;
import okhttp3.mockwebserver.MockWebServer;
import okhttp3.mockwebserver.RecordedRequest;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.io.IOException;

import static org.junit.jupiter.api.Assertions.*;

class ProvidersClientTest {
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

    @Test
    void listAllProviders() throws Exception {
        server.enqueue(new MockResponse()
                .setResponseCode(200)
                .setHeader("Content-Type", "application/json")
                .setBody("{" +
                        "\"providers\":[" +
                        "{\"id\":\"STRIPE\",\"name\":\"Stripe\",\"enabled\":true," +
                        "\"supportedCurrencies\":[\"EUR\",\"USD\",\"GBP\"]," +
                        "\"features\":[\"cards\",\"sepa\",\"wallet\"]," +
                        "\"supportedCrypto\":[]}," +
                        "{\"id\":\"PAYPAL\",\"name\":\"PayPal\",\"enabled\":true," +
                        "\"supportedCurrencies\":[\"EUR\",\"USD\"]," +
                        "\"features\":[\"wallet\",\"paylater\"]," +
                        "\"supportedCrypto\":[]}," +
                        "{\"id\":\"NOWPAYMENTS\",\"name\":\"NOWPayments\",\"enabled\":true," +
                        "\"supportedCurrencies\":[\"USD\"]," +
                        "\"features\":[\"crypto\"]," +
                        "\"supportedCrypto\":[\"BTC\",\"ETH\",\"USDT\"]}" +
                        "]}"));

        ProviderListResponse response = client.providers().list();

        assertNotNull(response);
        assertEquals(3, response.providers().size());
        assertEquals("STRIPE", response.providers().get(0).id());
        assertTrue(response.providers().get(0).supportedCurrencies().contains("EUR"));
        assertTrue(response.providers().get(2).supportedCrypto().contains("BTC"));

        RecordedRequest request = server.takeRequest();
        assertEquals("/api/providers", request.getPath());
    }

    @Test
    void listEmptyProviders() throws Exception {
        server.enqueue(new MockResponse()
                .setResponseCode(200)
                .setHeader("Content-Type", "application/json")
                .setBody("{\"providers\":[]}"));

        ProviderListResponse response = client.providers().list();

        assertNotNull(response);
        assertTrue(response.providers().isEmpty());
    }

    @Test
    void getStripeClientConfig() throws Exception {
        server.enqueue(new MockResponse()
                .setResponseCode(200)
                .setHeader("Content-Type", "application/json")
                .setBody("{" +
                        "\"provider\":\"STRIPE\"," +
                        "\"publishableKey\":\"pk_test_1234567890\"," +
                        "\"clientId\":null}"));

        ProviderClientConfig response = client.providers().getClientConfig("stripe");

        assertNotNull(response);
        assertEquals("STRIPE", response.provider());
        assertEquals("pk_test_1234567890", response.publishableKey());

        RecordedRequest request = server.takeRequest();
        assertEquals("/api/providers/stripe/client-config", request.getPath());
    }

    @Test
    void getPayPalClientConfig() throws Exception {
        server.enqueue(new MockResponse()
                .setResponseCode(200)
                .setHeader("Content-Type", "application/json")
                .setBody("{" +
                        "\"provider\":\"PAYPAL\"," +
                        "\"publishableKey\":null," +
                        "\"clientId\":\"paypal_client_id_123\"}"));

        ProviderClientConfig response = client.providers().getClientConfig("paypal");

        assertEquals("PAYPAL", response.provider());
        assertEquals("paypal_client_id_123", response.clientId());
        assertNull(response.publishableKey());
    }

    @Test
    void getClientConfigUrlEncoding() throws Exception {
        server.enqueue(new MockResponse()
                .setResponseCode(200)
                .setHeader("Content-Type", "application/json")
                .setBody("{\"provider\":\"TEST\"}"));

        client.providers().getClientConfig("provider/test#1");

        RecordedRequest request = server.takeRequest();
        assertEquals("/api/providers/provider%2Ftest%231/client-config", request.getPath());
    }

    @Test
    void getClientConfigUnknownProvider() {
        server.enqueue(new MockResponse()
                .setResponseCode(400)
                .setBody("{\"message\":\"Unknown provider\",\"code\":\"E_UNKNOWN_PROVIDER\"}"));

        ApiError error = assertThrows(ApiError.class, () -> client.providers().getClientConfig("unknown"));
        assertEquals(400, error.status());
        assertEquals("E_UNKNOWN_PROVIDER", error.code());
    }

    @Test
    void getStripePaymentMethodsEurGermany() throws Exception {
        server.enqueue(new MockResponse()
                .setResponseCode(200)
                .setHeader("Content-Type", "application/json")
                .setBody("{" +
                        "\"success\":true," +
                        "\"merchantCountry\":\"DE\"," +
                        "\"customerCountry\":\"DE\"," +
                        "\"currency\":\"EUR\"," +
                        "\"paymentMethods\":[" +
                        "{\"type\":\"card\",\"name\":\"Credit Card\",\"icon\":\"card.png\"}," +
                        "{\"type\":\"sepa_debit\",\"name\":\"SEPA Direct Debit\",\"icon\":\"sepa.png\"}," +
                        "{\"type\":\"ideal\",\"name\":\"iDEAL\",\"icon\":\"ideal.png\"}," +
                        "{\"type\":\"giropay\",\"name\":\"giropay\",\"icon\":\"giropay.png\"}" +
                        "]}"));

        PaymentMethodsResponse response = client.providers().getStripePaymentMethods("DE", "DE", "EUR");

        assertNotNull(response);
        assertTrue(response.success());
        assertEquals(4, response.paymentMethods().size());

        RecordedRequest request = server.takeRequest();
        String path = request.getPath();
        assertTrue(path.contains("merchantCountry=DE"));
        assertTrue(path.contains("customerCountry=DE"));
        assertTrue(path.contains("currency=EUR"));
    }

    @Test
    void getStripePaymentMethodsWithoutCurrency() throws Exception {
        server.enqueue(new MockResponse()
                .setResponseCode(200)
                .setHeader("Content-Type", "application/json")
                .setBody("{" +
                        "\"success\":true," +
                        "\"merchantCountry\":\"US\"," +
                        "\"customerCountry\":\"US\"," +
                        "\"currency\":null," +
                        "\"paymentMethods\":[" +
                        "{\"type\":\"card\",\"name\":\"Credit Card\",\"icon\":\"card.png\"}," +
                        "{\"type\":\"ach_debit\",\"name\":\"ACH Direct Debit\",\"icon\":\"ach.png\"}" +
                        "]}"));

        PaymentMethodsResponse response = client.providers().getStripePaymentMethods("US", "US", null);

        assertEquals(2, response.paymentMethods().size());

        RecordedRequest request = server.takeRequest();
        String path = request.getPath();
        assertTrue(path.contains("merchantCountry=US"));
        assertTrue(path.contains("customerCountry=US"));
        assertFalse(path.contains("currency"));
    }

    @Test
    void getStripePaymentMethodsInvalidCountry() {
        server.enqueue(new MockResponse()
                .setResponseCode(400)
                .setBody("{\"message\":\"Invalid country code\",\"code\":\"E_INVALID_COUNTRY\"}"));

        ApiError error = assertThrows(ApiError.class, 
                () -> client.providers().getStripePaymentMethods("XX", "DE", null));
        assertEquals(400, error.status());
        assertEquals("E_INVALID_COUNTRY", error.code());
    }
}
