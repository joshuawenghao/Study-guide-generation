import { describe, expect, it } from "vitest";

import {
  QUOTA_ERROR_MESSAGE,
  classifyError,
  resolveErrorMessage,
} from "@/lib/errors";

describe("classifyError", () => {
  it("classifies a bare 429 string as quota", () => {
    expect(classifyError("HTTP 429 Too Many Requests")).toBe("quota");
  });

  it("classifies RESOURCE_EXHAUSTED as quota (case-insensitive)", () => {
    expect(classifyError("RESOURCE_EXHAUSTED quota exceeded")).toBe("quota");
  });

  it("classifies resource_exhausted lowercase as quota", () => {
    expect(classifyError("resource_exhausted")).toBe("quota");
  });

  it("classifies RateLimitExceeded as quota", () => {
    expect(classifyError("RateLimitExceeded for model")).toBe("quota");
  });

  it("classifies a realistic backend retry-exhausted message containing 429 as quota", () => {
    expect(
      classifyError(
        "[intro] Gemini call failed after 3 attempts. Last error: RuntimeError('HTTP 429 RESOURCE_EXHAUSTED')",
      ),
    ).toBe("quota");
  });

  it("classifies a generic connection error as generic", () => {
    expect(classifyError("Connection refused")).toBe("generic");
  });

  it("classifies an unexpected stream-end message as generic", () => {
    expect(classifyError("The generate stream ended unexpectedly.")).toBe(
      "generic",
    );
  });

  it("classifies an empty string as generic", () => {
    expect(classifyError("")).toBe("generic");
  });
});

describe("resolveErrorMessage", () => {
  it("returns the quota message for a quota error", () => {
    expect(resolveErrorMessage("HTTP 429 Too Many Requests")).toBe(
      QUOTA_ERROR_MESSAGE,
    );
  });

  it("returns the raw message for a generic error when no fallback given", () => {
    expect(resolveErrorMessage("Connection refused")).toBe(
      "Connection refused",
    );
  });

  it("returns the fallback for a generic error when fallback is provided", () => {
    expect(
      resolveErrorMessage("Connection refused", "Something went wrong."),
    ).toBe("Something went wrong.");
  });
});
