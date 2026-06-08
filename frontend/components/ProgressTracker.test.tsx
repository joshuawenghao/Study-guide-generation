import { describe, expect, it } from "vitest";

import { buildSteps } from "@/components/ProgressTracker";
import type { ProgressEvent } from "@/lib/types";

function buildEvent(type: ProgressEvent["type"], node: string): ProgressEvent {
  return {
    type,
    node,
    message: undefined,
    timestamp: new Date().toISOString(),
  };
}

describe("ProgressTracker", () => {
  it("keeps retry active while downstream refresh nodes are running", () => {
    const steps = buildSteps("validating", [
      buildEvent("validation_started", "validation"),
      buildEvent("retry_started", "model_passage"),
      buildEvent("node_started", "check_in"),
    ]);

    expect(steps.find((step) => step.key === "retry")).toMatchObject({
      status: "active",
      detail: "Retrying model_passage after validator feedback.",
    });
    expect(steps.find((step) => step.key === "validation")).toMatchObject({
      status: "pending",
    });
  });

  it("returns to validation after the retry pass finishes", () => {
    const steps = buildSteps("validating", [
      buildEvent("validation_started", "validation"),
      buildEvent("retry_started", "assessment_passage"),
      buildEvent("node_started", "assessment_questions"),
      buildEvent("node_started", "answer_key"),
      buildEvent("validation_started", "validation"),
    ]);

    expect(steps.find((step) => step.key === "retry")).toMatchObject({
      status: "complete",
      detail: "Retrying assessment_passage after validator feedback.",
    });
    expect(steps.find((step) => step.key === "validation")).toMatchObject({
      status: "active",
      detail: "Checking schema and curriculum rules.",
    });
  });
});
