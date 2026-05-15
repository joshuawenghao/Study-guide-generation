"use client";

import { useState } from "react";

import InputForm from "@/components/InputForm";
import type { GenerateRequest, GenerationStage } from "@/lib/types";

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

  function handleFormSubmit(request: GenerateRequest) {
    try {
      setPendingRequest(request);
      setPageError(null);
      setStage("planning");
    } catch {
      setPageError("The request could not be prepared for generation.");
      setStage("error");
    }
  }

  function handleReset() {
    setPendingRequest(null);
    setPageError(null);
    setStage("idle");
  }

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
            ) : (
              <section className="space-y-6 rounded-3xl border border-slate-200 bg-surface-strong p-8 shadow-sm">
                <div className="flex flex-col gap-3 border-b border-slate-200 pb-6 sm:flex-row sm:items-center sm:justify-between">
                  <div className="space-y-2">
                    <p className="text-sm font-semibold uppercase tracking-[0.2em] text-cyan-800">
                      Request staged
                    </p>
                    <h2 className="text-2xl font-semibold tracking-tight text-slate-950">
                      The form payload is ready for API wiring.
                    </h2>
                    <p className="max-w-2xl text-sm leading-6 text-slate-600">
                      The next task will connect this stored request to the
                      generate route and streaming progress states.
                    </p>
                  </div>

                  <button
                    type="button"
                    className="inline-flex items-center justify-center rounded-full border border-slate-300 px-5 py-3 text-sm font-semibold text-slate-700 transition hover:border-cyan-700 hover:text-cyan-800"
                    onClick={handleReset}
                  >
                    Edit request
                  </button>
                </div>

                {pendingRequest ? (
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
                        Next integration surface
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
                ) : null}
              </section>
            )}
          </div>

          <aside className="space-y-5 rounded-3xl border border-slate-200 bg-surface-strong p-6 shadow-sm">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.18em] text-slate-500">
                Page state
              </p>
              <h2 className="mt-2 text-xl font-semibold tracking-tight text-slate-950">
                Ready for backend submission
              </h2>
            </div>

            <div className="rounded-2xl border border-dashed border-slate-300 bg-surface p-4">
              <p className="text-sm font-medium text-slate-900">Stage</p>
              <p className="mt-2 text-sm leading-6 text-slate-600">{stage}</p>
            </div>

            <div className="space-y-3 text-sm leading-6 text-slate-600">
              <p>
                Idle renders the controlled teacher form. Planning stores the
                prepared request until the API proxy and streaming flow land in
                the next phase.
              </p>
              <p>
                The page now owns the request handoff boundary, so the generate
                route can plug into a stable local state surface next.
              </p>
            </div>
          </aside>
        </section>
      </div>
    </main>
  );
}
