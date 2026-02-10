package io.delopay.sdk.internal;

import com.fasterxml.jackson.databind.JsonNode;
import io.delopay.sdk.ApiError;
import io.delopay.sdk.DelopayClientOptions;

import java.io.IOException;
import java.net.URI;
import java.net.URLEncoder;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.Map;
import java.util.Objects;

public final class HttpExecutor {
    private final HttpClient client;
    private final DelopayClientOptions options;

    public HttpExecutor(DelopayClientOptions options) {
        this.options = options;
        this.client = HttpClient.newBuilder()
                .connectTimeout(Duration.ofMillis(options.timeoutMs()))
                .build();
    }

    public <T> T send(String method, String path, Object payload, Class<T> responseType) {
        return send(method, path, null, payload, responseType);
    }

    public <T> T send(String method, String path, Map<String, String> query, Object payload, Class<T> responseType) {
        int retries = isIdempotent(method) ? options.maxRetries() : 0;

        for (int attempt = 0; attempt <= retries; attempt++) {
            try {
                HttpRequest request = buildRequest(method, path, query, payload);
                HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());

                int status = response.statusCode();
                String body = response.body();

                if (status >= 200 && status < 300) {
                    if (responseType == Void.class || body == null || body.isBlank()) {
                        return null;
                    }
                    return Jsons.mapper().readValue(body, responseType);
                }

                if (status >= 500 && attempt < retries) {
                    sleep(attempt);
                    continue;
                }

                throw mapError(status, body, response.headers().firstValue("x-request-id").orElse(null));
            } catch (IOException ex) {
                if (attempt < retries && isIdempotent(method)) {
                    sleep(attempt);
                    continue;
                }
                throw new ApiError(0, "Network request failed", null, null, ex.getMessage());
            } catch (InterruptedException ex) {
                Thread.currentThread().interrupt();
                throw new ApiError(0, "Network request interrupted", null, null, ex.getMessage());
            }
        }

        throw new ApiError(0, "Request exhausted retries", null, null, null);
    }

    private HttpRequest buildRequest(String method, String path, Map<String, String> query, Object payload) throws IOException {
        URI uri = URI.create(buildUrl(path, query));

        HttpRequest.Builder builder = HttpRequest.newBuilder(uri)
                .timeout(Duration.ofMillis(options.timeoutMs()))
                .header("Authorization", "Bearer " + options.apiKey())
                .header("Accept", "application/json");

        if (payload != null) {
            String json = Jsons.mapper().writeValueAsString(payload);
            builder.header("Content-Type", "application/json");
            builder.method(method, HttpRequest.BodyPublishers.ofString(json));
        } else {
            builder.method(method, HttpRequest.BodyPublishers.noBody());
        }

        return builder.build();
    }

    private String buildUrl(String path, Map<String, String> query) {
        String normalizedBase = options.baseUrl().endsWith("/") ? options.baseUrl() : options.baseUrl() + "/";
        String normalizedPath = path.startsWith("/") ? path.substring(1) : path;
        StringBuilder url = new StringBuilder(normalizedBase).append(normalizedPath);

        if (query != null && !query.isEmpty()) {
            url.append("?");
            boolean first = true;
            for (Map.Entry<String, String> entry : query.entrySet()) {
                if (!first) {
                    url.append("&");
                }
                first = false;
                url.append(URLEncoder.encode(entry.getKey(), StandardCharsets.UTF_8));
                url.append("=");
                url.append(URLEncoder.encode(Objects.toString(entry.getValue(), ""), StandardCharsets.UTF_8));
            }
        }

        return url.toString();
    }

    private boolean isIdempotent(String method) {
        return "GET".equalsIgnoreCase(method) || "HEAD".equalsIgnoreCase(method);
    }

    private ApiError mapError(int status, String body, String requestIdHeader) {
        String message = "Request failed";
        String code = null;
        String requestId = requestIdHeader;

        if (body != null && !body.isBlank()) {
            try {
                JsonNode root = Jsons.mapper().readTree(body);
                if (root.hasNonNull("message")) {
                    message = root.get("message").asText();
                }
                if (root.hasNonNull("code")) {
                    code = root.get("code").asText();
                } else if (root.hasNonNull("errorCode")) {
                    code = root.get("errorCode").asText();
                }
                if (requestId == null && root.hasNonNull("requestId")) {
                    requestId = root.get("requestId").asText();
                }
            } catch (IOException ignored) {
                message = body;
            }
        }

        return new ApiError(status, message, code, requestId, body);
    }

    private void sleep(int attempt) {
        try {
            long delay = Math.min(1000L, 100L * (1L << attempt));
            Thread.sleep(delay);
        } catch (InterruptedException interruptedException) {
            Thread.currentThread().interrupt();
        }
    }
}
