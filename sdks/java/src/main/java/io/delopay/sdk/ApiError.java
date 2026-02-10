package io.delopay.sdk;

public final class ApiError extends RuntimeException {
    private final int status;
    private final String code;
    private final String requestId;
    private final String responseBody;

    public ApiError(int status, String message, String code, String requestId, String responseBody) {
        super(message);
        this.status = status;
        this.code = code;
        this.requestId = requestId;
        this.responseBody = responseBody;
    }

    public int status() {
        return status;
    }

    public String code() {
        return code;
    }

    public String requestId() {
        return requestId;
    }

    public String responseBody() {
        return responseBody;
    }
}
