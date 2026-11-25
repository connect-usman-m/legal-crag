import type { ErrorResponse } from "../types/api";

export class ApiError extends Error {
  code: string;
  status: number;
  retryAfter: number | null;
  requestId: string;

  constructor(status: number, body: ErrorResponse) {
    super(body.message);
    this.name = "ApiError";
    this.code = body.error;
    this.status = status;
    this.retryAfter = body.retry_after_s;
    this.requestId = body.request_id;
  }
}

const baseUrl = () => import.meta.env.VITE_API_URL || "/api";
const demoKey = () => import.meta.env.VITE_DEMO_API_KEY || "";

export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set("Accept", "application/json");
  if (init.body) headers.set("Content-Type", "application/json");
  if (demoKey()) headers.set("X-API-Key", demoKey());

  let response: Response;
  try {
    response = await fetch(`${baseUrl()}${path}`, { ...init, headers });
  } catch {
    throw new ApiError(0, {
      error: "offline",
      message: "Cannot reach the API. Check your connection and try again.",
      request_id: "offline",
      retry_after_s: null,
    });
  }

  if (!response.ok) {
    const body = (await response.json().catch(() => ({}))) as Partial<ErrorResponse>;
    throw new ApiError(response.status, {
      error: body.error || "internal_error",
      message: body.message || `Request failed with ${response.status}`,
      request_id: body.request_id || response.headers.get("X-Request-ID") || "unknown",
      retry_after_s: body.retry_after_s ?? null,
    });
  }
  return (await response.json()) as T;
}

export function postJson<T>(path: string, body: unknown, signal?: AbortSignal): Promise<T> {
  return apiFetch<T>(path, {
    method: "POST",
    body: JSON.stringify(body),
    signal,
  });
}
