export type ApiErrorInput = {
  status: number;
  message: string;
  code?: string;
  requestId?: string;
  raw?: unknown;
};

export class ApiError extends Error {
  readonly status: number;
  readonly code?: string;
  readonly requestId?: string;
  readonly raw?: unknown;

  constructor(input: ApiErrorInput) {
    super(input.message);
    this.name = "ApiError";
    this.status = input.status;
    this.code = input.code;
    this.requestId = input.requestId;
    this.raw = input.raw;
  }
}
