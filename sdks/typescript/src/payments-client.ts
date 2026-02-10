import { HttpClient } from "./http";
import type {
  CreatePaymentRequest,
  PaymentResponse,
  RefundPaymentRequest,
  RefundResponse,
  ResendCallbacksResponse,
  UpdatePaymentRequest
} from "./types";

export class PaymentsClient {
  constructor(private readonly http: HttpClient) {}

  create(input: CreatePaymentRequest): Promise<PaymentResponse> {
    return this.http.request({
      method: "POST",
      path: "/api/payments/create",
      body: input
    });
  }

  get(paymentId: string): Promise<PaymentResponse> {
    return this.http.request({
      method: "GET",
      path: `/api/payments/${encodeURIComponent(paymentId)}`
    });
  }

  getByOrder(clientOrderId: string): Promise<PaymentResponse> {
    return this.http.request({
      method: "GET",
      path: `/api/payments/by-order/${encodeURIComponent(clientOrderId)}`
    });
  }

  update(paymentId: string, input: UpdatePaymentRequest): Promise<PaymentResponse> {
    return this.http.request({
      method: "PUT",
      path: `/api/payments/${encodeURIComponent(paymentId)}`,
      body: input
    });
  }

  capture(paymentId: string): Promise<PaymentResponse> {
    return this.http.request({
      method: "POST",
      path: `/api/payments/${encodeURIComponent(paymentId)}/capture`
    });
  }

  refund(paymentId: string, input: RefundPaymentRequest): Promise<RefundResponse> {
    return this.http.request({
      method: "POST",
      path: `/api/payments/${encodeURIComponent(paymentId)}/refund`,
      body: input
    });
  }

  resendFailedCallbacks(): Promise<ResendCallbacksResponse> {
    return this.http.request({
      method: "POST",
      path: "/api/payments/resend-failed-callbacks"
    });
  }
}
