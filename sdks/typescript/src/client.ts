import { HttpClient } from "./http";
import { PaymentsClient } from "./payments-client";
import { ProvidersClient } from "./providers-client";
import type { DelopayClientOptions } from "./types";

const DEFAULT_BASE_URL = "https://sandbox-delopay.deloxity.com";
const DEFAULT_TIMEOUT_MS = 30_000;
const DEFAULT_MAX_RETRIES = 2;

export class DelopayClient {
  readonly payments: PaymentsClient;
  readonly providers: ProvidersClient;

  constructor(options: DelopayClientOptions) {
    if (!options.apiKey || options.apiKey.trim() === "") {
      throw new Error("apiKey is required");
    }

    const http = new HttpClient({
      apiKey: options.apiKey,
      baseUrl: options.baseUrl ?? DEFAULT_BASE_URL,
      timeoutMs: options.timeoutMs ?? DEFAULT_TIMEOUT_MS,
      maxRetries: options.maxRetries ?? DEFAULT_MAX_RETRIES
    });

    this.payments = new PaymentsClient(http);
    this.providers = new ProvidersClient(http);
  }
}
