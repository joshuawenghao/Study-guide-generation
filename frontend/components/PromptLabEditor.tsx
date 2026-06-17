"use client";

import { useEffect, useState } from "react";

import {
  PROMPT_LAB_SECTION_KEYS,
  type PromptLabEditorProps,
  type PromptLabSectionKey,
} from "@/lib/types";

function formatSectionLabel(section: PromptLabSectionKey): string {
  return section
    .split("_")
    .map((chunk) => chunk.charAt(0).toUpperCase() + chunk.slice(1))
    .join(" ");
}

export default function PromptLabEditor({
  baseRequestJson,
  onBaseRequestJsonChange,
  systemPromptAppend,
  onSystemPromptAppendChange,
  sectionOverrides,
  onSectionOverrideChange,
  onGenerate,
  isGenerating,
  errorMessage,
}: PromptLabEditorProps) {
  const [jsonError, setJsonError] = useState<string | null>(null);

  useEffect(() => {
    if (!baseRequestJson.trim()) {
      setJsonError(null);
      return;
    }
    const timer = setTimeout(() => {
      try {
        JSON.parse(baseRequestJson);
        setJsonError(null);
      } catch {
        setJsonError("Invalid JSON — fix the syntax before generating.");
      }
    }, 500);
    return () => clearTimeout(timer);
  }, [baseRequestJson]);

  return (
    <section className="space-y-6 rounded-3xl border border-slate-200 bg-surface-strong p-6 shadow-sm sm:p-8">
      <div className="space-y-2">
        <p className="text-sm font-semibold uppercase tracking-[0.18em] text-cyan-800">
          Prompt lab editor
        </p>
        <h2 className="text-2xl font-semibold tracking-tight text-slate-950">
          Edit the request and prompt instructions
        </h2>
        <p className="text-sm leading-6 text-slate-600">
          Update the lesson request JSON, add optional system guidance, and tune
          supported section instructions before running generation.
        </p>
      </div>

      {errorMessage ? (
        <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
          {errorMessage}
        </div>
      ) : null}

      <label className="grid gap-2">
        <span className="text-sm font-medium text-slate-800">
          Lesson request (JSON)
        </span>
        <textarea
          className={`min-h-[16rem] w-full rounded-2xl border bg-white px-4 py-3 font-mono text-xs leading-6 text-slate-900 outline-none transition focus:ring-2 ${jsonError ? "border-rose-400 focus:border-rose-400 focus:ring-rose-100" : "border-slate-300 focus:border-cyan-700 focus:ring-cyan-100"}`}
          value={baseRequestJson}
          onChange={(event) => onBaseRequestJsonChange(event.target.value)}
          spellCheck={false}
        />
        {jsonError ? (
          <p className="text-xs text-rose-600">{jsonError}</p>
        ) : null}
      </label>

      <label className="grid gap-2">
        <span className="text-sm font-medium text-slate-800">
          Extra global prompt guidance (optional)
        </span>
        <textarea
          className="min-h-[6rem] w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm leading-6 text-slate-900 outline-none transition focus:border-cyan-700 focus:ring-2 focus:ring-cyan-100"
          value={systemPromptAppend}
          onChange={(event) => onSystemPromptAppendChange(event.target.value)}
          placeholder="Example: Prefer concise, classroom-ready wording with concrete examples."
        />
      </label>

      <section className="space-y-4 rounded-2xl border border-slate-200 bg-white px-4 py-5">
        <div className="space-y-1">
          <h3 className="text-sm font-semibold uppercase tracking-[0.16em] text-slate-500">
            Section override instructions
          </h3>
          <p className="text-sm leading-6 text-slate-600">
            Fill only the sections you want to override. Empty fields keep the
            default prompt behavior.
          </p>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          {PROMPT_LAB_SECTION_KEYS.map((section) => (
            <label key={section} className="grid gap-2">
              <span className="text-sm font-medium text-slate-800">
                {formatSectionLabel(section)}
              </span>
              <textarea
                className="min-h-[6rem] w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm leading-6 text-slate-900 outline-none transition focus:border-cyan-700 focus:ring-2 focus:ring-cyan-100"
                value={sectionOverrides[section]}
                onChange={(event) =>
                  onSectionOverrideChange(section, event.target.value)
                }
                placeholder="Optional section-specific guidance"
              />
            </label>
          ))}
        </div>
      </section>

      <div className="flex flex-wrap items-center gap-3">
        <button
          type="button"
          className="inline-flex items-center justify-center rounded-full bg-slate-950 px-6 py-3 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
          onClick={onGenerate}
          disabled={isGenerating}
        >
          {isGenerating ? "Generating..." : "Generate from prompt lab"}
        </button>
        <p className="text-sm text-slate-600">
          Internal reviewer sandbox. Not part of the teacher-facing page.
        </p>
      </div>
    </section>
  );
}
