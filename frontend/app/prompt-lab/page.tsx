"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import DownloadButton from "@/components/DownloadButton";
import ProgressTracker from "@/components/ProgressTracker";
import PromptLabEditor from "@/components/PromptLabEditor";
import PromptLabSamplePicker from "@/components/PromptLabSamplePicker";
import WebPreview from "@/components/WebPreview";
import {
  buildPdfFilename,
  buildPromptLabRequestPayload,
  createEmptySectionOverrides,
  parseEventStage,
  parseSseBlock,
} from "@/lib/promptLab";
import {
  type GenerateRequest,
  type GenerateResponse,
  type GenerationStage,
  type ProgressEvent,
  type PromptLabSampleInput,
  type PromptLabSectionKey,
} from "@/lib/types";

type ResultsView = "preview" | "download";

export default function PromptLabPage() {
  const [samples, setSamples] = useState<PromptLabSampleInput[]>([]);
  const [samplesError, setSamplesError] = useState<string | null>(null);
  const [isLoadingSamples, setIsLoadingSamples] = useState(true);
  const [selectedSampleId, setSelectedSampleId] = useState<string>("");

  const [baseRequestJson, setBaseRequestJson] = useState<string>("");
  const [systemPromptAppend, setSystemPromptAppend] = useState<string>("");
  const [sectionOverrides, setSectionOverrides] = useState<
    Record<PromptLabSectionKey, string>
  >(createEmptySectionOverrides());

  const [stage, setStage] = useState<GenerationStage>("idle");
  const [progressEvents, setProgressEvents] = useState<ProgressEvent[]>([]);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [result, setResult] = useState<GenerateResponse | null>(null);
  const [runError, setRunError] = useState<string | null>(null);
  const [resultsView, setResultsView] = useState<ResultsView>("preview");

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
    let ignore = false;

    async function loadSamples() {
      setIsLoadingSamples(true);

      try {
        const response = await fetch("/api/prompt-lab/samples", {
          method: "GET",
          cache: "no-store",
        });

        if (!response.ok) {
          const errorBody = await response.json().catch(() => null);
          const message =
            typeof errorBody?.error === "string"
              ? errorBody.error
              : "Could not load prompt-lab samples.";
          throw new Error(message);
        }

        const payload = (await response.json()) as PromptLabSampleInput[];

        if (ignore) {
          return;
        }

        setSamples(payload);
        setSamplesError(null);

        if (payload.length > 0) {
          setSelectedSampleId(payload[0].id);
          setBaseRequestJson(JSON.stringify(payload[0].request, null, 2));
        }
      } catch (error) {
        if (ignore) {
          return;
        }

        setSamples([]);
        setSamplesError(
          error instanceof Error
            ? error.message
            : "Could not load prompt-lab samples.",
        );
      } finally {
        if (!ignore) {
          setIsLoadingSamples(false);
        }
      }
    }

    void loadSamples();

    return () => {
      ignore = true;
    };
  }, []);

  function handleApplySample() {
    const sample = samples.find((entry) => entry.id === selectedSampleId);
    if (!sample) {
      return;
    }

    setBaseRequestJson(JSON.stringify(sample.request, null, 2));
    setRunError(null);
  }

  function handleSectionOverrideChange(
    section: PromptLabSectionKey,
    value: string,
  ) {
    setSectionOverrides((current) => ({ ...current, [section]: value }));
  }

  async function handleGenerate() {
    let baseRequest: GenerateRequest;

    try {
      baseRequest = JSON.parse(baseRequestJson) as GenerateRequest;
    } catch {
      setRunError(
        "Lesson request JSON must be valid before generation starts.",
      );
      setStage("error");
      return;
    }

    const payload = buildPromptLabRequestPayload({
      baseRequest,
      sectionOverrides,
      selectedSampleId,
      systemPromptAppend,
    });

    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    setRunError(null);
    setResult(null);
    setProgressEvents([]);
    setResultsView("preview");
    setElapsedSeconds(0);
    setStage("planning");

    try {
      setStage("generating");

      const response = await fetch("/api/prompt-lab/generate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
        signal: abortController.signal,
      });

      if (!response.body) {
        throw new Error("The prompt-lab response did not include a stream.");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();

        if (done) {
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
          const parsedPayload = JSON.parse(data) as
            | ProgressEvent
            | GenerateResponse
            | { error?: string };

          if (eventName === "progress") {
            const progressEvent = parsedPayload as ProgressEvent;
            setProgressEvents((current) => {
              const nextStage = parseEventStage(progressEvent, current);
              if (nextStage) {
                setStage(nextStage);
              }
              return [...current, progressEvent];
            });

            if (progressEvent.type === "error") {
              setRunError(
                progressEvent.message ??
                  "Generation stopped before the response completed.",
              );
            }

            continue;
          }

          if (eventName === "result") {
            setResult(parsedPayload as GenerateResponse);
            setRunError(null);
            setStage("done");
            continue;
          }

          if (eventName === "error") {
            const errorMessage =
              (parsedPayload as { error?: string }).error ??
              "The prompt-lab request failed.";
            setRunError(errorMessage);
            setStage("error");
          }
        }
      }
    } catch (error) {
      if (abortController.signal.aborted) {
        return;
      }

      setRunError(
        error instanceof Error
          ? error.message
          : "The prompt-lab request failed.",
      );
      setStage("error");
    } finally {
      if (abortControllerRef.current === abortController) {
        abortControllerRef.current = null;
      }
    }
  }

  function handleCancelRun() {
    abortControllerRef.current?.abort();
    abortControllerRef.current = null;
    setStage("idle");
    setRunError("Prompt-lab run canceled.");
  }

  const isGenerating =
    stage === "planning" ||
    stage === "generating" ||
    stage === "validating" ||
    stage === "rendering";
  const latestEvent = progressEvents[progressEvents.length - 1];

  const selectedSample = useMemo(
    () => samples.find((sample) => sample.id === selectedSampleId) ?? null,
    [samples, selectedSampleId],
  );

  const parsedBaseRequest = useMemo(() => {
    try {
      return JSON.parse(baseRequestJson) as GenerateRequest;
    } catch {
      return null;
    }
  }, [baseRequestJson]);

  const resultFilename = buildPdfFilename(parsedBaseRequest, selectedSampleId);

  return (
    <main className="px-6 py-12 sm:px-10 sm:py-16 lg:px-16 lg:py-20">
      <div className="mx-auto flex max-w-7xl flex-col gap-8">
        <div className="inline-flex w-fit items-center rounded-full border border-cyan-200 bg-cyan-50 px-3 py-1 text-sm font-medium text-cyan-800 shadow-sm">
          Prompt Lab (Internal)
        </div>

        <section className="space-y-3 rounded-3xl border border-slate-200 bg-surface-strong p-8 shadow-sm">
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-slate-500">
            Reviewer sandbox
          </p>
          <h1 className="max-w-4xl text-4xl font-semibold tracking-tight text-slate-950 sm:text-5xl">
            Tune prompt instructions and test study-guide output without
            touching code.
          </h1>
          <p className="max-w-4xl text-base leading-7 text-slate-600 sm:text-lg">
            This page is separate from the teacher workflow. Reviewers can load
            curated lesson samples, adjust request details and prompt overrides,
            and run generation in one place.
          </p>
        </section>

        <section className="grid gap-6 lg:grid-cols-[minmax(0,1.15fr)_minmax(20rem,0.85fr)]">
          <div className="space-y-6">
            <PromptLabSamplePicker
              samples={samples}
              selectedSampleId={selectedSampleId}
              onSelectedSampleIdChange={setSelectedSampleId}
              onApplySample={handleApplySample}
              isLoading={isLoadingSamples}
              errorMessage={samplesError ?? undefined}
            />

            <PromptLabEditor
              baseRequestJson={baseRequestJson}
              onBaseRequestJsonChange={setBaseRequestJson}
              systemPromptAppend={systemPromptAppend}
              onSystemPromptAppendChange={setSystemPromptAppend}
              sectionOverrides={sectionOverrides}
              onSectionOverrideChange={handleSectionOverrideChange}
              onGenerate={handleGenerate}
              isGenerating={isGenerating}
              errorMessage={runError ?? undefined}
            />

            {progressEvents.length > 0 ? (
              <ProgressTracker
                stage={stage}
                events={progressEvents}
                elapsedSeconds={elapsedSeconds}
              />
            ) : null}

            {result ? (
              <section className="space-y-6">
                <section className="space-y-4 rounded-3xl border border-slate-200 bg-surface-strong p-6 shadow-sm sm:p-8">
                  <div className="flex flex-col gap-4 border-b border-slate-200 pb-6 lg:flex-row lg:items-end lg:justify-between">
                    <div className="space-y-2">
                      <p className="text-sm font-semibold uppercase tracking-[0.18em] text-slate-500">
                        Prompt-lab results
                      </p>
                      <h2 className="text-2xl font-semibold tracking-tight text-slate-950">
                        Review preview output or download the generated PDF.
                      </h2>
                    </div>

                    <div className="inline-flex rounded-full border border-slate-200 bg-white p-1 shadow-sm">
                      <button
                        type="button"
                        onClick={() => setResultsView("preview")}
                        className={`rounded-full px-4 py-2 text-sm font-semibold transition ${
                          resultsView === "preview"
                            ? "bg-slate-950 text-white"
                            : "text-slate-600 hover:text-slate-950"
                        }`}
                      >
                        Web Preview
                      </button>
                      <button
                        type="button"
                        onClick={() => setResultsView("download")}
                        className={`rounded-full px-4 py-2 text-sm font-semibold transition ${
                          resultsView === "download"
                            ? "bg-slate-950 text-white"
                            : "text-slate-600 hover:text-slate-950"
                        }`}
                      >
                        Download PDF
                      </button>
                    </div>
                  </div>

                  {resultsView === "preview" ? (
                    <WebPreview
                      preview={result.preview}
                      validation={result.validation}
                    />
                  ) : (
                    <div className="rounded-2xl border border-slate-200 bg-white p-6">
                      <DownloadButton
                        pdfBase64={result.pdf_base64}
                        filename={resultFilename}
                      />
                    </div>
                  )}
                </section>
              </section>
            ) : null}
          </div>

          <aside className="space-y-5 rounded-3xl border border-slate-200 bg-surface-strong p-6 shadow-sm">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.18em] text-slate-500">
                Run state
              </p>
              <h2 className="mt-2 text-xl font-semibold tracking-tight text-slate-950">
                Live reviewer run details
              </h2>
            </div>

            <div className="rounded-2xl border border-dashed border-slate-300 bg-surface p-4">
              <p className="text-sm font-medium text-slate-900">Stage</p>
              <p className="mt-2 text-sm leading-6 text-slate-600">{stage}</p>
            </div>

            <div className="rounded-2xl border border-dashed border-slate-300 bg-surface p-4">
              <p className="text-sm font-medium text-slate-900">
                Selected sample
              </p>
              <p className="mt-2 text-sm leading-6 text-slate-600">
                {selectedSample ? selectedSample.label : "No sample selected."}
              </p>
            </div>

            <div className="rounded-2xl border border-dashed border-slate-300 bg-surface p-4">
              <p className="text-sm font-medium text-slate-900">Latest event</p>
              <p className="mt-2 text-sm leading-6 text-slate-600">
                {latestEvent
                  ? `${latestEvent.type} • ${latestEvent.node}`
                  : "No stream events yet."}
              </p>
            </div>

            {isGenerating ? (
              <button
                type="button"
                className="inline-flex w-full items-center justify-center rounded-full border border-slate-300 px-5 py-3 text-sm font-semibold text-slate-700 transition hover:border-cyan-700 hover:text-cyan-800"
                onClick={handleCancelRun}
              >
                Cancel run
              </button>
            ) : null}
          </aside>
        </section>
      </div>
    </main>
  );
}
