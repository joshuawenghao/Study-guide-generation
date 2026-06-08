import type {
  GenerationStage,
  ProgressEvent,
  ProgressTrackerProps,
} from "@/lib/types";
import { isRetryPassActive } from "@/lib/progress";

type StepKey =
  | "blueprint"
  | "generation"
  | "validation"
  | "retry"
  | "render"
  | "done";

type StepStatus = "complete" | "active" | "pending";

interface TrackerStep {
  key: StepKey;
  title: string;
  detail: string;
  status: StepStatus;
}

const BLUEPRINT_NODES = new Set(["blueprint", "generate_blueprint"]);
const GENERATION_NODES = new Set([
  "intro",
  "learning_targets",
  "warmup",
  "vocabulary",
  "key_points",
  "self_assessment",
  "core_explainer",
  "subconcept",
  "strategy_list",
  "deep_dive",
  "model_passage",
  "assessment_passage",
  "check_in",
  "assessment_questions",
  "step_up",
  "answer_key",
  "_generate_intro_node",
  "_generate_learning_targets_node",
  "_generate_warmup_node",
  "_generate_vocabulary_node",
  "_generate_key_points_node",
  "_generate_self_assessment_node",
  "_generate_core_explainer_node",
  "_generate_subconcept_node",
  "_generate_strategy_list_node",
  "_generate_deep_dive_node",
  "_generate_model_passage_node",
  "_generate_assessment_passage_node",
  "_generate_check_in_node",
  "_generate_assessment_questions_node",
  "_generate_step_up_node",
  "_generate_answer_key_node",
]);
const VALIDATION_NODES = new Set([
  "validation",
  "validator",
  "_generate_validation_node",
]);
const RENDER_NODES = new Set(["render", "renderer", "_generate_render_node"]);

function formatElapsedTime(elapsedSeconds: number): string {
  const totalSeconds = Math.max(0, Math.floor(elapsedSeconds));
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;

  return `${minutes}:${seconds.toString().padStart(2, "0")}`;
}

function normalizeNode(node: string): string {
  return node.trim();
}

function isGenerationEvent(event: ProgressEvent): boolean {
  return GENERATION_NODES.has(normalizeNode(event.node));
}

function hasEvent(
  events: ProgressEvent[],
  predicate: (event: ProgressEvent) => boolean,
): boolean {
  return events.some(predicate);
}

function getLatestEvent(events: ProgressEvent[]): ProgressEvent | undefined {
  return events[events.length - 1];
}

function getLatestMatchingEvent(
  events: ProgressEvent[],
  predicate: (event: ProgressEvent) => boolean,
): ProgressEvent | undefined {
  return [...events].reverse().find(predicate);
}

function getActiveStep(
  stage: GenerationStage,
  events: ProgressEvent[],
): StepKey | null {
  const latestEvent = getLatestEvent(events);
  const retryActive = isRetryPassActive(events);

  if (stage === "error") {
    if (latestEvent?.type === "error") {
      if (latestEvent.node === "workflow") {
        return "done";
      }
      if (RENDER_NODES.has(normalizeNode(latestEvent.node))) {
        return "render";
      }
      if (VALIDATION_NODES.has(normalizeNode(latestEvent.node))) {
        return "validation";
      }
    }

    if (latestEvent && isGenerationEvent(latestEvent)) {
      return "generation";
    }
  }

  if (stage === "done") {
    return "done";
  }
  if (stage === "rendering") {
    return "render";
  }
  if (stage === "validating") {
    return retryActive ? "retry" : "validation";
  }
  if (stage === "generating") {
    if (retryActive) {
      return "retry";
    }
    if (latestEvent && BLUEPRINT_NODES.has(normalizeNode(latestEvent.node))) {
      return "blueprint";
    }
    return "generation";
  }
  if (stage === "planning") {
    return "blueprint";
  }

  return null;
}

export function buildSteps(
  stage: GenerationStage,
  events: ProgressEvent[],
): TrackerStep[] {
  const activeStep = getActiveStep(stage, events);
  const retryActive = isRetryPassActive(events);
  const blueprintComplete = hasEvent(
    events,
    (event) =>
      event.type === "node_complete" &&
      BLUEPRINT_NODES.has(normalizeNode(event.node)),
  );
  const generationStarted = hasEvent(events, isGenerationEvent);
  const validationStarted = hasEvent(
    events,
    (event) =>
      event.type === "validation_started" ||
      VALIDATION_NODES.has(normalizeNode(event.node)),
  );
  const retryStarted = hasEvent(
    events,
    (event) => event.type === "retry_started",
  );
  const renderStarted = hasEvent(
    events,
    (event) =>
      event.type === "render_started" ||
      RENDER_NODES.has(normalizeNode(event.node)),
  );
  const done =
    hasEvent(events, (event) => event.type === "done") || stage === "done";

  const statuses: Record<StepKey, StepStatus> = {
    blueprint: blueprintComplete
      ? "complete"
      : activeStep === "blueprint"
        ? "active"
        : "pending",
    generation:
      generationStarted &&
      (validationStarted ||
        renderStarted ||
        done ||
        stage === "validating" ||
        stage === "rendering")
        ? "complete"
        : activeStep === "generation"
          ? "active"
          : "pending",
    validation:
      validationStarted && (renderStarted || done || stage === "rendering")
        ? "complete"
        : activeStep === "validation"
          ? "active"
          : "pending",
    retry:
      retryStarted && !retryActive
        ? "complete"
        : activeStep === "retry"
          ? "active"
          : "pending",
    render:
      renderStarted && done
        ? "complete"
        : activeStep === "render"
          ? "active"
          : "pending",
    done: done ? "complete" : activeStep === "done" ? "active" : "pending",
  };

  const generatedCount = new Set(
    events
      .filter(
        (event) => event.type === "node_complete" && isGenerationEvent(event),
      )
      .map((event) => normalizeNode(event.node)),
  ).size;
  const latestValidation = getLatestMatchingEvent(
    events,
    (event) =>
      event.type === "validation_started" ||
      VALIDATION_NODES.has(normalizeNode(event.node)),
  );
  const latestRetry = getLatestMatchingEvent(
    events,
    (event) => event.type === "retry_started",
  );
  const latestRender = getLatestMatchingEvent(
    events,
    (event) =>
      event.type === "render_started" ||
      RENDER_NODES.has(normalizeNode(event.node)),
  );

  return [
    {
      key: "blueprint",
      title: "Blueprint",
      detail: blueprintComplete
        ? "Lesson plan scaffold resolved."
        : "Preparing lesson structure and section plan.",
      status: statuses.blueprint,
    },
    {
      key: "generation",
      title: "Section Generation",
      detail: generationStarted
        ? `${generatedCount} section node${generatedCount === 1 ? "" : "s"} completed.`
        : "Waiting for section nodes to start.",
      status: statuses.generation,
    },
    {
      key: "validation",
      title: "Validation",
      detail:
        latestValidation?.message ?? "Checking schema and curriculum rules.",
      status: statuses.validation,
    },
    {
      key: "retry",
      title: "Retry Pass",
      detail: latestRetry
        ? `Retrying ${latestRetry.node} after validator feedback.`
        : "Only runs when a hard validator fails.",
      status: statuses.retry,
    },
    {
      key: "render",
      title: "Render Output",
      detail: latestRender?.message ?? "Preparing preview data and PDF output.",
      status: statuses.render,
    },
    {
      key: "done",
      title: "Done",
      detail: done
        ? "Generation finished and results are ready."
        : "Waiting for the final response payload.",
      status: statuses.done,
    },
  ];
}

function getTrackerLabel(status: StepStatus): string {
  if (status === "complete") {
    return "Complete";
  }
  if (status === "active") {
    return "Active";
  }
  return "Pending";
}

function getTrackerClasses(status: StepStatus): string {
  if (status === "complete") {
    return "border-emerald-200 bg-emerald-50 text-emerald-700";
  }
  if (status === "active") {
    return "border-cyan-200 bg-cyan-50 text-cyan-800";
  }
  return "border-slate-200 bg-white text-slate-500";
}

export default function ProgressTracker({
  stage,
  events,
  elapsedSeconds,
}: ProgressTrackerProps) {
  const steps = buildSteps(stage, events);
  const latestEvent = getLatestEvent(events);
  const latestError = getLatestMatchingEvent(
    events,
    (event) => event.type === "error",
  );

  return (
    <section className="space-y-6 rounded-3xl border border-slate-200 bg-surface-strong p-6 shadow-sm sm:p-8">
      <div className="flex flex-col gap-4 border-b border-slate-200 pb-5 sm:flex-row sm:items-end sm:justify-between">
        <div className="space-y-2">
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-slate-500">
            Generation progress
          </p>
          <h2 className="text-2xl font-semibold tracking-tight text-slate-950">
            Track each workflow stage as events stream in.
          </h2>
          <p className="max-w-2xl text-sm leading-6 text-slate-600">
            Blueprint, section generation, validation, retry, render, and
            completion are shown as separate steps.
          </p>
        </div>

        <div className="grid grid-cols-2 gap-3 sm:min-w-[14rem]">
          <div className="rounded-2xl border border-slate-200 bg-surface px-4 py-3">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
              Stage
            </p>
            <p className="mt-2 text-sm font-medium capitalize text-slate-900">
              {stage}
            </p>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-surface px-4 py-3">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
              Elapsed
            </p>
            <p className="mt-2 text-sm font-medium text-slate-900">
              {formatElapsedTime(elapsedSeconds)}
            </p>
          </div>
        </div>
      </div>

      {latestError ? (
        <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
          {latestError.message ??
            `The workflow reported an error in ${latestError.node}.`}
        </div>
      ) : null}

      <ol className="space-y-4">
        {steps.map((step, index) => {
          const isLast = index === steps.length - 1;

          return (
            <li key={step.key} className="relative pl-16">
              {!isLast ? (
                <div className="absolute left-[1.45rem] top-11 h-[calc(100%+0.5rem)] w-px bg-slate-200" />
              ) : null}

              <div className="absolute left-0 top-1 flex h-12 w-12 items-center justify-center rounded-2xl border border-slate-200 bg-white text-sm font-semibold text-slate-700 shadow-sm">
                {index + 1}
              </div>

              <div
                className={`rounded-2xl border px-4 py-4 shadow-sm transition ${getTrackerClasses(step.status)}`}
              >
                <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                  <div className="space-y-1">
                    <h3 className="text-base font-semibold text-slate-950">
                      {step.title}
                    </h3>
                    <p className="text-sm leading-6 text-slate-600">
                      {step.detail}
                    </p>
                  </div>

                  <span className="inline-flex w-fit items-center rounded-full border border-current/15 bg-white/70 px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em]">
                    {getTrackerLabel(step.status)}
                  </span>
                </div>
              </div>
            </li>
          );
        })}
      </ol>

      <div className="rounded-2xl border border-dashed border-slate-300 bg-surface px-4 py-4 text-sm text-slate-600">
        <p className="font-medium text-slate-900">Latest event</p>
        <p className="mt-2 leading-6">
          {latestEvent
            ? `${latestEvent.type} on ${latestEvent.node}${latestEvent.message ? `: ${latestEvent.message}` : "."}`
            : "Waiting for the first progress event."}
        </p>
      </div>
    </section>
  );
}
