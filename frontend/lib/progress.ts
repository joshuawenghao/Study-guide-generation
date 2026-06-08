import type { GenerationStage, ProgressEvent } from "@/lib/types";

export function isRetryPassActive(events: ProgressEvent[]): boolean {
  const lastRetryIndex = events.findLastIndex(
    (event) => event.type === "retry_started",
  );
  if (lastRetryIndex === -1) {
    return false;
  }

  return !events
    .slice(lastRetryIndex + 1)
    .some((event) =>
      ["validation_started", "render_started", "done", "error"].includes(
        event.type,
      ),
    );
}

export function parseEventStage(
  event: ProgressEvent,
  previousEvents: ProgressEvent[] = [],
): GenerationStage | null {
  if (event.type === "error") {
    return "error";
  }
  if (event.type === "done") {
    return "done";
  }
  if (event.type === "render_started") {
    return "rendering";
  }
  if (event.type === "validation_started" || event.type === "retry_started") {
    return "validating";
  }
  if (event.type === "node_started" || event.type === "node_complete") {
    return isRetryPassActive(previousEvents) ? "validating" : "generating";
  }

  return null;
}
