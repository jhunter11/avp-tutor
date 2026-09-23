/** Framework-independent client. Copy with schema.d.ts into any TypeScript UI.
 * Authentication belongs to the integrating app/gateway, not to model providers.
 */
import type { components } from "./schema";

export type TutorRequest = components["schemas"]["TutorRequest"];
export type TutorResponse = components["schemas"]["TutorResponse"];
export type ExecutionContext = components["schemas"]["ExecutionContext"];
export type ValidationResult = components["schemas"]["ValidationResult"];
export type ChatTurn = components["schemas"]["ChatTurn"];
export type Source = components["schemas"]["Source"];
export type ExecutionEvent = components["schemas"]["ExecutionEvent"];

export class TutorApiError extends Error {
  readonly status: number;
  readonly retryAfterSeconds?: number;
  constructor(message: string, status: number, retryAfterSeconds?: number) {
    super(message);
    this.name = "TutorApiError";
    this.status = status;
    this.retryAfterSeconds = retryAfterSeconds;
  }
}

export function createTutorClient(
  options: { baseUrl?: string; fetcher?: typeof fetch } = {},
) {
  const base = (options.baseUrl ?? "").replace(/\/$/, "");
  const fetcher = options.fetcher ?? globalThis.fetch.bind(globalThis);
  async function post<T>(
    path: string,
    body: unknown,
    request: { signal?: AbortSignal } = {},
  ): Promise<T> {
    const response = await fetcher(`${base}${path}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify(body),
      signal: request.signal,
    });
    const data = await response.json().catch(() => null);
    if (!response.ok) {
      let detail = typeof data?.detail === "string" ? data.detail : "";
      if (Array.isArray(data?.detail))
        detail = data.detail
          .map(
            (item: { loc?: unknown[]; msg?: string }) =>
              `${item.loc?.join(".") ?? "request"}: ${item.msg ?? "invalid"}`,
          )
          .join("; ");
      const retry = Number(response.headers.get("Retry-After"));
      throw new TutorApiError(
        detail ||
          (response.status === 429
            ? "Too many questions. Wait a moment and retry."
            : `Tutor request failed (${response.status}).`),
        response.status,
        response.headers.has("Retry-After") && Number.isFinite(retry)
          ? retry
          : undefined,
      );
    }
    if (data === null)
      throw new TutorApiError(
        "The tutor returned an invalid JSON response.",
        502,
      );
    return data as T;
  }
  return {
    feedback: (
      body: components["schemas"]["FeedbackRequest"],
      request?: { signal?: AbortSignal },
    ) => post<{ saved: boolean }>("/api/feedback", body, request),
    usage: (
      body: components["schemas"]["UsageRequest"],
      request?: { signal?: AbortSignal },
    ) =>
      post<{ saved: boolean; quality_label: boolean }>(
        "/api/usage",
        body,
        request,
      ),
    ask: (body: TutorRequest, request?: { signal?: AbortSignal }) =>
      post<TutorResponse>("/api/tutor", body, request),
    validateContext: (
      body: ExecutionContext,
      request?: { signal?: AbortSignal },
    ) => post<ExecutionContext>("/api/context/validate", body, request),
    validateCode: (code: string, request?: { signal?: AbortSignal }) =>
      post<ValidationResult>("/api/validate", { code }, request),
  };
}
