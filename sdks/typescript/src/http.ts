import { ApiError } from "./errors";

type QueryValue = string | number | boolean | undefined;

type RequestOptions = {
  method: "GET" | "POST" | "PUT" | "DELETE" | "PATCH" | "HEAD";
  path: string;
  body?: unknown;
  query?: Record<string, QueryValue>;
};

type HttpClientConfig = {
  apiKey: string;
  baseUrl: string;
  timeoutMs: number;
  maxRetries: number;
};

const IDEMPOTENT_METHODS = new Set(["GET", "HEAD"]);

export class HttpClient {
  private readonly config: HttpClientConfig;

  constructor(config: HttpClientConfig) {
    this.config = config;
  }

  async request<T>(options: RequestOptions): Promise<T> {
    const url = this.buildUrl(options.path, options.query);
    const retries = IDEMPOTENT_METHODS.has(options.method) ? this.config.maxRetries : 0;

    for (let attempt = 0; attempt <= retries; attempt += 1) {
      try {
        const response = await this.runFetch(url, options);
        if (response.ok) {
          if (response.status === 204) {
            return undefined as T;
          }

          const text = await response.text();
          return text ? (JSON.parse(text) as T) : (undefined as T);
        }

        const rawText = await response.text();
        const parsed = parseJson(rawText);
        const status = response.status;
        const requestId =
          response.headers.get("x-request-id") ??
          (isObject(parsed) && typeof parsed.requestId === "string" ? parsed.requestId : undefined);
        const code = extractCode(parsed);
        const message = extractMessage(parsed) ?? response.statusText ?? "Request failed";

        if (status >= 500 && attempt < retries) {
          await sleep(backoffMs(attempt));
          continue;
        }

        throw new ApiError({
          status,
          message,
          code,
          requestId,
          raw: parsed ?? rawText
        });
      } catch (error) {
        if (error instanceof ApiError) {
          throw error;
        }

        if (attempt < retries && isRetryableTransportError(error)) {
          await sleep(backoffMs(attempt));
          continue;
        }

        throw new ApiError({
          status: 0,
          message: "Network request failed",
          raw: error
        });
      }
    }

    throw new ApiError({
      status: 0,
      message: "Request exhausted retries"
    });
  }

  private async runFetch(url: string, options: RequestOptions): Promise<Response> {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), this.config.timeoutMs);

    try {
      const headers: Record<string, string> = {
        Authorization: `Bearer ${this.config.apiKey}`,
        Accept: "application/json"
      };

      if (options.body !== undefined) {
        headers["Content-Type"] = "application/json";
      }

      return await fetch(url, {
        method: options.method,
        headers,
        body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
        signal: controller.signal
      });
    } finally {
      clearTimeout(timeout);
    }
  }

  private buildUrl(path: string, query?: Record<string, QueryValue>): string {
    const url = new URL(path, ensureTrailingSlash(this.config.baseUrl));

    if (query) {
      for (const [key, value] of Object.entries(query)) {
        if (value !== undefined) {
          url.searchParams.set(key, String(value));
        }
      }
    }

    return url.toString();
  }
}

function parseJson(raw: string): unknown {
  if (!raw) {
    return undefined;
  }

  try {
    return JSON.parse(raw);
  } catch {
    return raw;
  }
}

function extractMessage(raw: unknown): string | undefined {
  if (!isObject(raw)) {
    return undefined;
  }

  if (typeof raw.message === "string") {
    return raw.message;
  }

  if (typeof raw.error === "string") {
    return raw.error;
  }

  return undefined;
}

function extractCode(raw: unknown): string | undefined {
  if (!isObject(raw)) {
    return undefined;
  }

  if (typeof raw.code === "string") {
    return raw.code;
  }

  if (typeof raw.errorCode === "string") {
    return raw.errorCode;
  }

  return undefined;
}

function isObject(input: unknown): input is Record<string, any> {
  return typeof input === "object" && input !== null;
}

function isRetryableTransportError(error: unknown): boolean {
  if (error instanceof TypeError) {
    return true;
  }

  if (typeof error === "object" && error !== null && "name" in error) {
    return (error as { name?: string }).name === "AbortError";
  }

  return false;
}

function backoffMs(attempt: number): number {
  return Math.min(1000, 100 * 2 ** attempt);
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function ensureTrailingSlash(input: string): string {
  return input.endsWith("/") ? input : `${input}/`;
}
