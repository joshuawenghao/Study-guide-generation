export default function Home() {
  return (
    <main className="px-6 py-12 sm:px-10 sm:py-16 lg:px-16 lg:py-20">
      <div className="mx-auto flex max-w-5xl flex-col gap-10">
        <div className="inline-flex w-fit items-center rounded-full border border-slate-200 bg-surface-strong px-3 py-1 text-sm font-medium text-slate-700 shadow-sm">
          Study Guide Generation
        </div>

        <section className="grid gap-8 rounded-3xl border border-slate-200 bg-surface-strong p-8 shadow-sm lg:grid-cols-[minmax(0,1.2fr)_minmax(18rem,0.8fr)] lg:p-12">
          <div className="space-y-5">
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-slate-500">
              Frontend shell
            </p>
            <h1 className="max-w-2xl text-4xl font-semibold tracking-tight text-slate-950 sm:text-5xl">
              Build teacher-ready study guides from one structured lesson input.
            </h1>
            <p className="max-w-2xl text-base leading-7 text-slate-600 sm:text-lg">
              The default starter page has been removed. This frontend is now
              ready for the teacher input form, progress tracking, and generated
              preview experience planned in the next tasks.
            </p>
          </div>

          <div className="rounded-2xl border border-dashed border-slate-300 bg-surface p-6">
            <h2 className="text-lg font-semibold text-slate-900">
              Next in queue
            </h2>
            <ul className="mt-4 space-y-3 text-sm leading-6 text-slate-600">
              <li>Teacher lesson input form</li>
              <li>Streaming generation progress</li>
              <li>Rendered study guide preview</li>
            </ul>
          </div>
        </section>
      </div>
    </main>
  );
}
