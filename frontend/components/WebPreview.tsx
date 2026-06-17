"use client";

import { useEffect, useState } from "react";

import PreviewSection, { formatLabel } from "@/components/PreviewSection";
import PreviewIcon, {
  PREVIEW_CALLOUT_ICON_KEYS,
} from "@/components/PreviewIcon";
import type { WebPreviewProps } from "@/lib/types";

function pluralize(count: number, singular: string, plural: string): string {
  return `${count} ${count === 1 ? singular : plural}`;
}

export default function WebPreview({ preview, validation }: WebPreviewProps) {
  const [showBackToTop, setShowBackToTop] = useState(false);

  useEffect(() => {
    function handleScroll() {
      setShowBackToTop(window.scrollY > 400);
    }
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const sectionCount = preview.sections.length;
  const warningCount = validation.warnings.length;
  const failedSectionCount = validation.failed_sections.length;
  const bestEffortCount = validation.best_effort_sections.length;

  return (
    <section className="space-y-6 rounded-[2rem] border border-slate-200 bg-surface-strong p-6 shadow-sm sm:p-8">
      <header className="space-y-4 border-b border-slate-200 pb-6">
        <div className="space-y-2">
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-slate-500">
            Web preview
          </p>
          <h2 className="text-3xl font-semibold tracking-tight text-slate-950">
            Review the generated study guide before downloading the PDF.
          </h2>
          <p className="max-w-3xl text-sm leading-6 text-slate-600 sm:text-base">
            Sections are shown in the canonical study-guide order returned by
            the backend renderer. Validation warnings and best-effort sections
            stay visible here so the teacher can review quality issues without
            leaving the preview.
          </p>
        </div>

        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <div className="rounded-2xl border border-slate-200 bg-white px-4 py-4">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
              Sections
            </p>
            <p className="mt-2 text-2xl font-semibold text-slate-950">
              {sectionCount}
            </p>
            <p className="mt-1 text-sm text-slate-600">
              {pluralize(sectionCount, "section", "sections")}
            </p>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-white px-4 py-4">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
              Warnings
            </p>
            <p className="mt-2 text-2xl font-semibold text-slate-950">
              {warningCount}
            </p>
            <p className="mt-1 text-sm text-slate-600">
              {warningCount === 0
                ? "No non-blocking warnings."
                : pluralize(warningCount, "warning", "warnings")}
            </p>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-white px-4 py-4">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
              Failed sections
            </p>
            <p className="mt-2 text-2xl font-semibold text-slate-950">
              {failedSectionCount}
            </p>
            <p className="mt-1 text-sm text-slate-600">
              {failedSectionCount === 0
                ? "No blocking section failures."
                : pluralize(
                    failedSectionCount,
                    "section needs review",
                    "sections need review",
                  )}
            </p>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-white px-4 py-4">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
              Best effort
            </p>
            <p className="mt-2 text-2xl font-semibold text-slate-950">
              {bestEffortCount}
            </p>
            <p className="mt-1 text-sm text-slate-600">
              {bestEffortCount === 0
                ? "No best-effort sections."
                : pluralize(
                    bestEffortCount,
                    "section kept after retry",
                    "sections kept after retry",
                  )}
            </p>
          </div>
        </div>
      </header>

      {validation.warnings.length > 0 ? (
        <section className="rounded-[2rem] border border-amber-200 bg-amber-50 px-5 py-5">
          <div className="flex items-start gap-3">
            <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-white/80 text-amber-900 shadow-sm">
              <PreviewIcon
                iconKey={PREVIEW_CALLOUT_ICON_KEYS.warning}
                className="h-5 w-5"
              />
            </span>
            <div className="space-y-2">
              <h3 className="text-sm font-semibold uppercase tracking-[0.18em] text-amber-900">
                Validation warnings
              </h3>
              <p className="text-sm leading-6 text-amber-950">
                These warnings did not block output generation, but they should
                be reviewed before the guide is shared.
              </p>
            </div>
          </div>
          <ul className="mt-4 grid gap-3 text-sm leading-6 text-amber-950">
            {validation.warnings.map((warning) => (
              <li
                key={warning}
                className="rounded-2xl border border-amber-200 bg-white/70 px-4 py-3"
              >
                {warning}
              </li>
            ))}
          </ul>
        </section>
      ) : (
        <section className="rounded-[2rem] border border-emerald-200 bg-emerald-50 px-5 py-5 text-sm leading-6 text-emerald-950">
          <div className="flex items-start gap-3">
            <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-white/80 text-emerald-800 shadow-sm">
              <PreviewIcon
                iconKey={PREVIEW_CALLOUT_ICON_KEYS.success}
                className="h-5 w-5"
              />
            </span>
            <p>No validation warnings were returned with this preview.</p>
          </div>
        </section>
      )}

      {sectionCount > 0 ? (
        <nav
          className="sticky top-0 z-10 -mx-6 bg-surface-strong px-6 py-3 shadow-sm sm:-mx-8 sm:px-8"
          aria-label="Jump to section"
        >
          <p className="mb-2 text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">
            Jump to
          </p>
          <div className="flex flex-wrap gap-2">
            {preview.sections.map((section) => (
              <a
                key={section.section_id}
                href={`#section-${section.section_type}`}
                className="whitespace-nowrap rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold capitalize text-slate-700 shadow-sm transition hover:border-cyan-700 hover:text-cyan-800"
              >
                {formatLabel(section.section_type)}
              </a>
            ))}
            {showBackToTop ? (
              <button
                type="button"
                onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}
                className="whitespace-nowrap rounded-full border border-slate-300 bg-white px-3 py-1.5 text-xs font-semibold text-slate-500 shadow-sm transition hover:border-cyan-700 hover:text-cyan-800"
              >
                ↑ Back to top
              </button>
            ) : null}
          </div>
        </nav>
      ) : null}

      {sectionCount > 0 ? (
        <div className="grid gap-6">
          {preview.sections.map((section) => (
            <PreviewSection
              key={section.section_id}
              section={section}
              validation={validation}
            />
          ))}
        </div>
      ) : (
        <section className="rounded-[2rem] border border-dashed border-slate-300 bg-white px-5 py-8 text-sm leading-6 text-slate-600">
          The backend returned an empty preview payload for this generation run.
        </section>
      )}
    </section>
  );
}
