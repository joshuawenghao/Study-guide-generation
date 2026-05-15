"use client";

import { useEffect, useRef, useState } from "react";

import InputForm from "@/components/InputForm";
import ProgressTracker from "@/components/ProgressTracker";
import type {
  GenerateRequest,
  GenerateResponse,
  GenerationStage,
  ProgressEvent,
} from "@/lib/types";

function parseEventStage(event: ProgressEvent): GenerationStage | null {
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
    return "generating";
  }

  return null;
}

function parseSseBlock(
  block: string,
): { eventName: string; data: string } | null {
  const lines = block
    .split(/\r?\n/)
    .map((line) => line.trimEnd())
    .filter(Boolean);

  if (lines.length === 0) {
    return null;
  }

  let eventName = "message";
  const dataLines: string[] = [];

  for (const line of lines) {
    if (line.startsWith("event:")) {
      eventName = line.slice("event:".length).trim();
      continue;
    }

    if (line.startsWith("data:")) {
      dataLines.push(line.slice("data:".length).trim());
    }
  }

  if (dataLines.length === 0) {
    return null;
  }

  return {
    eventName,
    data: dataLines.join("\n"),
  };
}

function formatList(items: string[] | undefined): string {
  if (!items || items.length === 0) {
    return "Not provided";
  }

  return items.join(", ");
}

export default function Home() {
  const [stage, setStage] = useState<GenerationStage>("idle");
  const [pageError, setPageError] = useState<string | null>(null);
  const [pendingRequest, setPendingRequest] = useState<GenerateRequest | null>(
    null,
  );
  const [progressEvents, setProgressEvents] = useState<ProgressEvent[]>([]);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [result, setResult] = useState<GenerateResponse | null>(null);

  const abortControllerRef = useRef<AbortController | null>(null);
  const generationStartedAtRef = useRef<number | null>(null);

  useEffect(() => {
    const isActiveStage =
      stage === "planning" ||
      stage === "generating" ||
      stage === "validating" ||
      stage === "rendering";

    if (!isActiveStage) {
      generationStartedAtRef.current = null;
      return;
    }

    if (generationStartedAtRef.current === null) {
      generationStartedAtRef.current = Date.now();
      setElapsedSeconds(0);
    }

    const intervalId = window.setInterval(() => {
      if (generationStartedAtRef.current === null) {
        return;
      }

      setElapsedSeconds(
        Math.floor((Date.now() - generationStartedAtRef.current) / 1000),
      );
    }, 1000);

    return () => window.clearInterval(intervalId);
  }, [stage]);

  useEffect(() => {
    if (stage !== "planning" || !pendingRequest) {
      return;
    }

    const abortController = new AbortController();
    abortControllerRef.current = abortController;
    let streamCompleted = false;

    async function runGeneration() {
      setStage("generating");

      try {
        const response = await fetch("/api/generate", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(pendingRequest),
          signal: abortController.signal,
        });

        if (!response.body) {
          throw new Error("The generate response did not include a stream.");
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();

          if (done) {
            streamCompleted = true;
            break;
          }

          buffer += decoder.decode(value, { stream: true });
          const blocks = buffer.split(/\r?\n\r?\n/);
          buffer = blocks.pop() ?? "";

          for (const block of blocks) {
            const parsedBlock = parseSseBlock(block);
            if (!parsedBlock) {
              continue;
            }

            const { eventName, data } = parsedBlock;
            const payload = JSON.parse(data) as
              | ProgressEvent
              | GenerateResponse
              | { error?: string };

            if (eventName === "progress") {
              const progressEvent = payload as ProgressEvent;
              setProgressEvents((current) => [...current, progressEvent]);

              const nextStage = parseEventStage(progressEvent);
              if (nextStage) {
                setStage(nextStage);
              }

              if (progressEvent.type === "error") {
                setPageError(
                  progressEvent.message ??
                    "Generation stopped before the response completed.",
                );
              }

              continue;
            }

            if (eventName === "result") {
              setResult(payload as GenerateResponse);
              setPageError(null);
              setStage("done");
              continue;
            }

            if (eventName === "error") {
              const errorMessage =
                (payload as { error?: string }).error ??
                "The generate request failed.";
              setPageError(errorMessage);
              setStage("error");
            }
          }
        }

        if (buffer.trim().length > 0) {
          const parsedBlock = parseSseBlock(buffer);
          if (parsedBlock?.eventName === "result") {
            setResult(JSON.parse(parsedBlock.data) as GenerateResponse);
            setPageError(null);
            setStage("done");
          }
        }

        if (!streamCompleted && !abortController.signal.aborted) {
          throw new Error("The generate stream ended unexpectedly.");
        }
      } catch (error) {
        if (abortController.signal.aborted) {
          return;
        }

        setPageError(
          error instanceof Error
            ? error.message
            : "The generate request failed.",
        );
        setStage("error");
      } finally {
        if (abortControllerRef.current === abortController) {
          abortControllerRef.current = null;
        }
      }
    }

    void runGeneration();

    return () => {
      abortController.abort();
      if (abortControllerRef.current === abortController) {
        abortControllerRef.current = null;
      }
    };
  }, [pendingRequest, stage]);

  function handleFormSubmit(request: GenerateRequest) {
    try {
      setPendingRequest(request);
      setProgressEvents([]);
      setElapsedSeconds(0);
      setResult(null);
      setPageError(null);
      setStage("planning");
    } catch {
      setPageError("The request could not be prepared for generation.");
      setStage("error");
    }
  }

  function handleReset() {
    abortControllerRef.current?.abort();
    abortControllerRef.current = null;
    setPendingRequest(null);
    setProgressEvents([]);
    setElapsedSeconds(0);
    setResult(null);
    setPageError(null);
    setStage("idle");
  }

  const isGenerating =
    stage === "planning" ||
    stage === "generating" ||
    stage === "validating" ||
    stage === "rendering";
  const hasStarted = stage !== "idle" && pendingRequest !== null;
  const latestEvent = progressEvents[progressEvents.length - 1];
  const responseSummary = result
    ? {
        previewSections: result.preview.sections.length,
        warningCount: result.validation.warnings.length,
        failedSectionCount: result.validation.failed_sections.length,
        bestEffortCount: result.validation.best_effort_sections.length,
      }
    : null;

  const lessonSummary = pendingRequest
    ? [
        `${pendingRequest.lesson_metadata.subject} Grade ${pendingRequest.lesson_metadata.grade_level}`,
        pendingRequest.lesson_metadata.lesson_title,
        pendingRequest.curriculum.competency_code,
      ]
    : [];

  return (
    <main className="px-6 py-12 sm:px-10 sm:py-16 lg:px-16 lg:py-20">
      <div className="mx-auto flex max-w-6xl flex-col gap-10">
        <div className="inline-flex w-fit items-center rounded-full border border-slate-200 bg-surface-strong px-3 py-1 text-sm font-medium text-slate-700 shadow-sm">
          Study Guide Generation
        </div>

        <section className="grid gap-8 lg:grid-cols-[minmax(0,1.45fr)_minmax(18rem,0.85fr)] lg:items-start">
          <div className="space-y-6">
            <div className="space-y-4 rounded-3xl border border-slate-200 bg-surface-strong p-8 shadow-sm lg:p-10">
              <p className="text-sm font-semibold uppercase tracking-[0.2em] text-slate-500">
                Form stage
              </p>
              <h1 className="max-w-3xl text-4xl font-semibold tracking-tight text-slate-950 sm:text-5xl">
                Build a complete lesson request before generation begins.
              </h1>
              <p className="max-w-3xl text-base leading-7 text-slate-600 sm:text-lg">
                This page now owns the teacher input flow. It tracks form-stage
                state, captures the next `GenerateRequest`, and leaves the API
                submission path ready for the next task.
              </p>
            </div>

            {pageError ? (
              <div className="rounded-3xl border border-rose-200 bg-rose-50 px-5 py-4 text-sm text-rose-700 shadow-sm">
                {pageError}
              </div>
            ) : null}

            {stage === "idle" ? (
              <InputForm onSubmit={handleFormSubmit} isLoading={false} />
            ) : pendingRequest ? (
              <div className="space-y-6">
                <section className="space-y-6 rounded-3xl border border-slate-200 bg-surface-strong p-8 shadow-sm">
                  <div className="flex flex-col gap-3 border-b border-slate-200 pb-6 sm:flex-row sm:items-center sm:justify-between">
                    <div className="space-y-2">
                      <p className="text-sm font-semibold uppercase tracking-[0.2em] text-cyan-800">
                        Generation run
                      </p>
                      <h2 className="text-2xl font-semibold tracking-tight text-slate-950">
                        The page is now consuming the streamed generate route.
                      </h2>
                      <p className="max-w-2xl text-sm leading-6 text-slate-600">
                        Progress events, elapsed time, and the final response
                        are all tracked locally so the preview flow can land on
                        top of a stable streaming surface next.
                      </p>
                    </div>

                    <button
                      type="button"
                      className="inline-flex items-center justify-center rounded-full border border-slate-300 px-5 py-3 text-sm font-semibold text-slate-700 transition hover:border-cyan-700 hover:text-cyan-800"
                      onClick={handleReset}
                    >
                      {isGenerating ? "Cancel run" : "Edit request"}
                    </button>
                  </div>

                  <div className="grid gap-6 lg:grid-cols-2">
                    <div className="space-y-4 rounded-2xl border border-slate-200 bg-surface p-5">
                      <h3 className="text-sm font-semibold uppercase tracking-[0.18em] text-slate-500">
                        Request snapshot
                      </h3>
                      <ul className="space-y-3 text-sm leading-6 text-slate-700">
                        {lessonSummary.map((item) => (
                          <li key={item}>{item}</li>
                        ))}
                      </ul>
                    </div>

                    <div className="space-y-4 rounded-2xl border border-slate-200 bg-surface p-5">
                      <h3 className="text-sm font-semibold uppercase tracking-[0.18em] text-slate-500">
                        Stream state
                      </h3>
                      <dl className="space-y-3 text-sm leading-6 text-slate-700">
                        <div>
                          <dt className="font-medium text-slate-900">
                            Current stage
                          </dt>
                          <dd>{stage}</dd>
                        </div>
                        <div>
                          <dt className="font-medium text-slate-900">
                            Events received
                          </dt>
                          <dd>{progressEvents.length}</dd>
                        </div>
                        <div>
                          <dt className="font-medium text-slate-900">
                            Vocabulary seeds
                          </dt>
                          <dd>
                            {formatList(
                              pendingRequest.optional.vocabulary_seeds,
                            )}
                          </dd>
                        </div>
                        <div>
                          <dt className="font-medium text-slate-900">
                            Sub-competencies
                          </dt>
                          <dd>
                            {pendingRequest.curriculum.sub_competencies.length}
                          </dd>
                        </div>
                      </dl>
                    </div>
                  </div>
                </section>

                <ProgressTracker
                  stage={stage}
                  events={progressEvents}
                  elapsedSeconds={elapsedSeconds}
                />

                {result ? (
                  <section className="grid gap-6 rounded-3xl border border-emerald-200 bg-emerald-50/70 p-8 shadow-sm lg:grid-cols-[minmax(0,1.1fr)_minmax(18rem,0.9fr)]">
                    <div className="space-y-3">
                      <p className="text-sm font-semibold uppercase tracking-[0.2em] text-emerald-700">
                        Final response captured
                      </p>
                      <h2 className="text-2xl font-semibold tracking-tight text-slate-950">
                        Generation completed and the payload is ready for
                        preview wiring.
                      </h2>
                      <p className="max-w-2xl text-sm leading-6 text-slate-700">
                        The page now retains the backend result in local state,
                        including preview sections, PDF bytes, and validation
                        metadata for the next UI slice.
                      </p>
                    </div>

                    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-1 xl:grid-cols-2">
                      <div className="rounded-2xl border border-emerald-200 bg-white px-4 py-4">
                        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                          Preview sections
                        </p>
                        <p className="mt-2 text-2xl font-semibold text-slate-950">
                          {responseSummary?.previewSections}
                        </p>
                      </div>
                      <div className="rounded-2xl border border-emerald-200 bg-white px-4 py-4">
                        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                          Warnings
                        </p>
                        <p className="mt-2 text-2xl font-semibold text-slate-950">
                          {responseSummary?.warningCount}
                        </p>
                      </div>
                      <div className="rounded-2xl border border-emerald-200 bg-white px-4 py-4">
                        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                          Failed sections
                        </p>
                        <p className="mt-2 text-2xl font-semibold text-slate-950">
                          {responseSummary?.failedSectionCount}
                        </p>
                      </div>
                      <div className="rounded-2xl border border-emerald-200 bg-white px-4 py-4">
                        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                          Best-effort sections
                        </p>
                        <p className="mt-2 text-2xl font-semibold text-slate-950">
                          {responseSummary?.bestEffortCount}
                        </p>
                      </div>
                    </div>
                  </section>
                ) : null}
              </div>
            ) : null}
          </div>

          <aside className="space-y-5 rounded-3xl border border-slate-200 bg-surface-strong p-6 shadow-sm">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.18em] text-slate-500">
                Page state
              </p>
              <h2 className="mt-2 text-xl font-semibold tracking-tight text-slate-950">
                Live generation state
              </h2>
            </div>

            <div className="rounded-2xl border border-dashed border-slate-300 bg-surface p-4">
              <p className="text-sm font-medium text-slate-900">Stage</p>
              <p className="mt-2 text-sm leading-6 text-slate-600">{stage}</p>
            </div>

            <div className="rounded-2xl border border-dashed border-slate-300 bg-surface p-4">
              <p className="text-sm font-medium text-slate-900">Latest event</p>
              <p className="mt-2 text-sm leading-6 text-slate-600">
                {latestEvent
                  ? `${latestEvent.type} • ${latestEvent.node}`
                  : hasStarted
                    ? "Waiting for the first streamed event."
                    : "No generation started yet."}
              </p>
            </div>

            <div className="rounded-2xl border border-dashed border-slate-300 bg-surface p-4">
              <p className="text-sm font-medium text-slate-900">
                Response state
              </p>
              <p className="mt-2 text-sm leading-6 text-slate-600">
                {result
                  ? `Preview and PDF payload captured with ${result.preview.sections.length} preview sections.`
                  : "The final GenerateResponse will be stored here when the stream finishes."}
              </p>
            </div>

            <div className="space-y-3 text-sm leading-6 text-slate-600">
              <p>
                Idle renders the controlled teacher form. Once submitted, the
                page posts to the generate proxy and updates stage state from
                streamed progress events.
              </p>
              <p>
                This completes the page-level streaming boundary so the next
                frontend slice can focus on preview rendering and download UX.
              </p>
            </div>
          </aside>
        </section>
      </div>
    </main>
  );
}
