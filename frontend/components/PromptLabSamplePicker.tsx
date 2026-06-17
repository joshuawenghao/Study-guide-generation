import type { PromptLabSamplePickerProps } from "@/lib/types";

export default function PromptLabSamplePicker({
  samples,
  selectedSampleId,
  onSelectedSampleIdChange,
  onApplySample,
  isLoading,
  errorMessage,
}: PromptLabSamplePickerProps) {
  const selectedSample = samples.find(
    (sample) => sample.id === selectedSampleId,
  );

  return (
    <section className="space-y-4 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="space-y-2">
        <p className="text-sm font-semibold uppercase tracking-[0.18em] text-cyan-800">
          Curated samples
        </p>
        <h2 className="text-2xl font-semibold tracking-tight text-slate-950">
          Start from a reviewer-ready lesson case
        </h2>
        <p className="text-sm leading-6 text-slate-600">
          Pick a sample input to preload the request editor, then adjust fields
          and prompts as needed.
        </p>
      </div>

      {errorMessage ? (
        <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
          {errorMessage}
        </div>
      ) : null}

      <div className="grid gap-4 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-start">
        <label className="space-y-2">
          <span className="text-sm font-medium text-slate-800">
            Sample case
          </span>
          <select
            className="w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-cyan-700 focus:ring-2 focus:ring-cyan-100"
            value={selectedSampleId}
            onChange={(event) => onSelectedSampleIdChange(event.target.value)}
            disabled={isLoading || samples.length === 0}
          >
            {samples.length === 0 ? (
              <option value="">No samples available</option>
            ) : null}
            {samples.map((sample) => (
              <option key={sample.id} value={sample.id}>
                {sample.label}
              </option>
            ))}
          </select>
          {selectedSample ? (
            <p className="rounded-2xl border border-slate-200 bg-surface px-4 py-3 text-sm leading-6 text-slate-600">
              {selectedSample.description}
            </p>
          ) : null}
        </label>

        <button
          type="button"
          className="mt-7 inline-flex items-center justify-center rounded-full border border-slate-300 px-5 py-3 text-sm font-semibold text-slate-700 transition hover:border-cyan-700 hover:text-cyan-800 disabled:cursor-not-allowed disabled:opacity-60"
          onClick={onApplySample}
          disabled={isLoading || samples.length === 0 || !selectedSampleId}
        >
          Load sample
        </button>
      </div>
    </section>
  );
}
