export type ErrorClass = "quota" | "generic";

const QUOTA_SIGNALS = ["429", "resource_exhausted", "ratelimitexceeded"];

export const QUOTA_ERROR_MESSAGE =
  "Gemini quota reached — the AI service is temporarily unavailable. Please wait a few minutes and try again.";

export function classifyError(message: string): ErrorClass {
  const lower = message.toLowerCase();
  return QUOTA_SIGNALS.some((signal) => lower.includes(signal))
    ? "quota"
    : "generic";
}

export function resolveErrorMessage(
  raw: string,
  fallback: string = raw,
): string {
  return classifyError(raw) === "quota" ? QUOTA_ERROR_MESSAGE : fallback;
}
