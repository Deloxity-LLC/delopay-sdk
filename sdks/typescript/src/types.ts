export type DelopayClientOptions = {
  apiKey: string;
  baseUrl?: string;
  timeoutMs?: number;
  maxRetries?: number;
};

export type PaymentProviderType = "STRIPE" | "PAYPAL" | "NOWPAYMENTS" | "PAYSAFE" | string;
export type PaymentStatus =
  | "PENDING"
  | "AUTHORIZED"
  | "COMPLETED"
  | "FAILED"
  | "CANCELED"
  | "REFUNDED"
  | string;

export type CreatePaymentRequest = {
  clientOrderId: string;
  provider: PaymentProviderType;
  amount: number;
  currency: string;
  description?: string;
  customerEmail?: string;
  successUrl: string;
  cancelUrl: string;
  callbackUrl?: string;
  metadata?: Record<string, unknown>;
  autoCapture?: boolean;
};

export type UpdatePaymentRequest = {
  metadata?: Record<string, unknown>;
  callbackUrl?: string;
  description?: string;
  customerEmail?: string;
  amount?: number;
  amountPaid?: number;
  currency?: string;
  status?: PaymentStatus;
};

export type RefundPaymentRequest = {
  amount?: number;
  reason?: string;
};

export type PaymentResponse = {
  paymentId: string;
  clientOrderId: string;
  provider: PaymentProviderType;
  status: PaymentStatus;
  amount: number;
  amountPaid?: number;
  currency: string;
  description?: string;
  customerEmail?: string;
  checkoutUrl?: string;
  providerPaymentId?: string;
  createdAt?: string;
  completedAt?: string;
  expiresAt?: string;
  metadata?: Record<string, unknown>;
  errorMessage?: string;
};

export type RefundResponse = {
  refundId: string;
  paymentId: string;
  providerRefundId?: string;
  amount: number;
  originalAmount?: number;
  remainingAmount?: number;
  status?: string;
  reason?: string;
  createdAt?: string;
  completedAt?: string;
  errorMessage?: string;
};

export type ResendCallbacksResponse = {
  resent: number;
};

export type ProviderInfo = {
  id: string;
  name: string;
  enabled: boolean;
  supportedCurrencies?: string[];
  features?: string[];
  supportedCrypto?: string[];
};

export type ProviderListResponse = {
  providers: ProviderInfo[];
};

export type ProviderClientConfig = {
  provider: string;
  publishableKey?: string;
  clientId?: string;
};

export type PaymentMethodDetail = {
  type: string;
  name: string;
  icon?: string;
};

export type PaymentMethodsResponse = {
  success: boolean;
  merchantCountry: string;
  customerCountry: string;
  currency?: string;
  paymentMethods: PaymentMethodDetail[];
};
