"use client";

import { useRef, useState } from "react";

import type {
  GenerateRequest,
  InputFormProps,
  LengthPreset,
  SubCompetency,
} from "@/lib/types";

const lengthOptions: { value: LengthPreset; label: string }[] = [
  { value: "short", label: "Short" },
  { value: "standard", label: "Standard" },
  { value: "long", label: "Long" },
];

const toneOptions = ["warm-formal", "encouraging", "academic", "direct"];

const initialSubCompetency: SubCompetency = {
  id: "SC-1",
  label: "",
};

function parseLineList(value: string): string[] | undefined {
  const items = value
    .split(/\r?\n|,/)
    .map((item) => item.trim())
    .filter(Boolean);

  return items.length > 0 ? items : undefined;
}

function parseTopicDomains(
  modelPassage: string,
  assessmentPassage: string,
): Record<string, string> | undefined {
  const entries = Object.entries({
    model_passage: modelPassage.trim(),
    assessment_passage: assessmentPassage.trim(),
  }).filter(([, value]) => value.length > 0);

  return entries.length > 0 ? Object.fromEntries(entries) : undefined;
}

export default function InputForm({ onSubmit, isLoading }: InputFormProps) {
  const [subject, setSubject] = useState("");
  const [gradeLevel, setGradeLevel] = useState("6");
  const [market, setMarket] = useState("PH");
  const [language, setLanguage] = useState("en");
  const [unitNumber, setUnitNumber] = useState("1");
  const [unitTitle, setUnitTitle] = useState("");
  const [lessonNumber, setLessonNumber] = useState("1");
  const [lessonTitle, setLessonTitle] = useState("");
  const [lessonCode, setLessonCode] = useState("");

  const [competencyCode, setCompetencyCode] = useState("");
  const [competencyDescription, setCompetencyDescription] = useState("");
  const [subCompetencies, setSubCompetencies] = useState<SubCompetency[]>([
    initialSubCompetency,
  ]);

  const [coreConcept, setCoreConcept] = useState("");
  const [bloomTargetOne, setBloomTargetOne] = useState("");
  const [bloomTargetTwo, setBloomTargetTwo] = useState("");
  const [bloomTargetThree, setBloomTargetThree] = useState("");
  const [essentialQuestionSeed, setEssentialQuestionSeed] = useState("");

  const [vocabularySeeds, setVocabularySeeds] = useState("");
  const [modelPassageDomain, setModelPassageDomain] = useState("");
  const [assessmentPassageDomain, setAssessmentPassageDomain] = useState("");
  const [toneRegister, setToneRegister] = useState("warm-formal");
  const [lengthPreset, setLengthPreset] = useState<LengthPreset>("standard");

  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [firstErrorField, setFirstErrorField] = useState<string | null>(null);

  const formRef = useRef<HTMLFormElement>(null);

  function fieldRingClass(fieldKey: string): string {
    return firstErrorField === fieldKey
      ? "border-rose-400 ring-2 ring-rose-100"
      : "border-slate-300";
  }

  function scrollToFirstError(fieldKey: string) {
    setFirstErrorField(fieldKey);
    const el = formRef.current?.querySelector<HTMLElement>(
      `[data-field="${fieldKey}"]`,
    );
    el?.scrollIntoView({ behavior: "smooth", block: "center" });
    el?.focus({ preventScroll: true });
  }

  function updateSubCompetency(
    index: number,
    key: keyof SubCompetency,
    value: string,
  ) {
    setSubCompetencies((current) =>
      current.map((entry, entryIndex) =>
        entryIndex === index ? { ...entry, [key]: value } : entry,
      ),
    );
  }

  function addSubCompetency() {
    setSubCompetencies((current) => [
      ...current,
      { id: `SC-${current.length + 1}`, label: "" },
    ]);
  }

  function removeSubCompetency(index: number) {
    setSubCompetencies((current) =>
      current.length === 1
        ? current
        : current.filter((_, entryIndex) => entryIndex !== index),
    );
  }

  function buildRequest(): GenerateRequest | null {
    const trimmedSubject = subject.trim();
    const trimmedMarket = market.trim();
    const trimmedLanguage = language.trim();
    const trimmedUnitTitle = unitTitle.trim();
    const trimmedLessonTitle = lessonTitle.trim();
    const trimmedLessonCode = lessonCode.trim();
    const trimmedCompetencyCode = competencyCode.trim();
    const trimmedCompetencyDescription = competencyDescription.trim();
    const trimmedCoreConcept = coreConcept.trim();
    const trimmedBloomTargetOne = bloomTargetOne.trim();
    const trimmedBloomTargetTwo = bloomTargetTwo.trim();
    const trimmedBloomTargetThree = bloomTargetThree.trim();
    const trimmedEssentialQuestionSeed = essentialQuestionSeed.trim();
    const trimmedToneRegister = toneRegister.trim();

    const parsedGradeLevel = Number.parseInt(gradeLevel, 10);
    const parsedUnitNumber = Number.parseInt(unitNumber, 10);
    const parsedLessonNumber = Number.parseInt(lessonNumber, 10);

    // Check required text fields in top-to-bottom form order
    const firstEmptyTextField = !trimmedSubject
      ? "subject"
      : !trimmedMarket
        ? "market"
        : !trimmedLanguage
          ? "language"
          : !trimmedUnitTitle
            ? "unitTitle"
            : !trimmedLessonTitle
              ? "lessonTitle"
              : !trimmedLessonCode
                ? "lessonCode"
                : !trimmedCompetencyCode
                  ? "competencyCode"
                  : !trimmedCompetencyDescription
                    ? "competencyDescription"
                    : !trimmedCoreConcept
                      ? "coreConcept"
                      : !trimmedBloomTargetOne
                        ? "bloomTargetOne"
                        : !trimmedBloomTargetTwo
                          ? "bloomTargetTwo"
                          : !trimmedBloomTargetThree
                            ? "bloomTargetThree"
                            : !trimmedEssentialQuestionSeed
                              ? "essentialQuestionSeed"
                              : !trimmedToneRegister
                                ? "toneRegister"
                                : null;

    if (firstEmptyTextField) {
      setErrorMessage(
        "Complete every required field before generating a study guide.",
      );
      scrollToFirstError(firstEmptyTextField);
      return null;
    }

    const firstInvalidNumber =
      Number.isNaN(parsedGradeLevel) ||
      parsedGradeLevel < 1 ||
      parsedGradeLevel > 12
        ? "gradeLevel"
        : Number.isNaN(parsedUnitNumber) || parsedUnitNumber < 1
          ? "unitNumber"
          : Number.isNaN(parsedLessonNumber) || parsedLessonNumber < 1
            ? "lessonNumber"
            : null;

    if (firstInvalidNumber) {
      setErrorMessage(
        "Grade, unit number, and lesson number must be valid positive numbers.",
      );
      scrollToFirstError(firstInvalidNumber);
      return null;
    }

    const normalizedSubCompetencies = subCompetencies.map((entry) => ({
      id: entry.id.trim(),
      label: entry.label.trim(),
    }));

    if (
      normalizedSubCompetencies.length === 0 ||
      normalizedSubCompetencies.some((entry) => !entry.id || !entry.label)
    ) {
      setErrorMessage(
        "Add at least one sub-competency and complete both its code and label.",
      );
      scrollToFirstError("subCompetencies");
      return null;
    }

    setErrorMessage(null);
    setFirstErrorField(null);

    return {
      lesson_metadata: {
        subject: trimmedSubject,
        grade_level: parsedGradeLevel,
        market: trimmedMarket,
        language: trimmedLanguage,
        unit_number: parsedUnitNumber,
        unit_title: trimmedUnitTitle,
        lesson_number: parsedLessonNumber,
        lesson_title: trimmedLessonTitle,
        lesson_code: trimmedLessonCode,
      },
      curriculum: {
        competency_code: trimmedCompetencyCode,
        competency_description: trimmedCompetencyDescription,
        sub_competencies: normalizedSubCompetencies,
      },
      instructional_design: {
        core_concept: trimmedCoreConcept,
        bloom_targets: [
          trimmedBloomTargetOne,
          trimmedBloomTargetTwo,
          trimmedBloomTargetThree,
        ],
        essential_question_seed: trimmedEssentialQuestionSeed,
      },
      optional: {
        vocabulary_seeds: parseLineList(vocabularySeeds),
        topic_domains: parseTopicDomains(
          modelPassageDomain,
          assessmentPassageDomain,
        ),
        tone_register: trimmedToneRegister,
        length_preset: lengthPreset,
      },
    };
  }

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const request = buildRequest();
    if (request) {
      onSubmit(request);
    }
  }

  return (
    <form
      ref={formRef}
      className="space-y-8 rounded-3xl border border-slate-200 bg-surface-strong p-6 shadow-sm sm:p-8"
      onSubmit={handleSubmit}
      onInput={() => setFirstErrorField(null)}
    >
      <div className="flex flex-col gap-3 border-b border-slate-200 pb-6">
        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-cyan-800">
          Teacher input
        </p>
        <div className="space-y-2">
          <h2 className="text-2xl font-semibold tracking-tight text-slate-950">
            Build the lesson request
          </h2>
          <p className="max-w-3xl text-sm leading-6 text-slate-600">
            Enter the structured lesson details the generator needs to create a
            curriculum-aligned study guide.
          </p>
        </div>
      </div>

      <section className="grid gap-4 md:grid-cols-2">
        <div className="md:col-span-2">
          <p className="text-sm font-semibold uppercase tracking-[0.18em] text-slate-500">
            Lesson details
          </p>
        </div>

        <label className="space-y-2">
          <span className="text-sm font-medium text-slate-800">Subject</span>
          <input
            data-field="subject"
            className={`w-full rounded-2xl border bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-cyan-700 focus:ring-2 focus:ring-cyan-100 ${fieldRingClass("subject")}`}
            value={subject}
            onChange={(event) => setSubject(event.target.value)}
            placeholder="English"
          />
        </label>

        <label className="space-y-2">
          <span className="text-sm font-medium text-slate-800">
            Grade level
          </span>
          <input
            data-field="gradeLevel"
            className={`w-full rounded-2xl border bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-cyan-700 focus:ring-2 focus:ring-cyan-100 ${fieldRingClass("gradeLevel")}`}
            value={gradeLevel}
            onChange={(event) => setGradeLevel(event.target.value)}
            inputMode="numeric"
            placeholder="6"
          />
        </label>

        <label className="space-y-2">
          <span className="text-sm font-medium text-slate-800">Market</span>
          <input
            data-field="market"
            className={`w-full rounded-2xl border bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-cyan-700 focus:ring-2 focus:ring-cyan-100 ${fieldRingClass("market")}`}
            value={market}
            onChange={(event) => setMarket(event.target.value)}
            placeholder="PH"
          />
        </label>

        <label className="space-y-2">
          <span className="text-sm font-medium text-slate-800">Language</span>
          <input
            data-field="language"
            className={`w-full rounded-2xl border bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-cyan-700 focus:ring-2 focus:ring-cyan-100 ${fieldRingClass("language")}`}
            value={language}
            onChange={(event) => setLanguage(event.target.value)}
            placeholder="en"
          />
        </label>

        <label className="space-y-2">
          <span className="text-sm font-medium text-slate-800">
            Unit number
          </span>
          <input
            data-field="unitNumber"
            className={`w-full rounded-2xl border bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-cyan-700 focus:ring-2 focus:ring-cyan-100 ${fieldRingClass("unitNumber")}`}
            value={unitNumber}
            onChange={(event) => setUnitNumber(event.target.value)}
            inputMode="numeric"
            placeholder="1"
          />
        </label>

        <label className="space-y-2">
          <span className="text-sm font-medium text-slate-800">Unit title</span>
          <input
            data-field="unitTitle"
            className={`w-full rounded-2xl border bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-cyan-700 focus:ring-2 focus:ring-cyan-100 ${fieldRingClass("unitTitle")}`}
            value={unitTitle}
            onChange={(event) => setUnitTitle(event.target.value)}
            placeholder="Reading Across Text Types"
          />
        </label>

        <label className="space-y-2">
          <span className="text-sm font-medium text-slate-800">
            Lesson number
          </span>
          <input
            data-field="lessonNumber"
            className={`w-full rounded-2xl border bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-cyan-700 focus:ring-2 focus:ring-cyan-100 ${fieldRingClass("lessonNumber")}`}
            value={lessonNumber}
            onChange={(event) => setLessonNumber(event.target.value)}
            inputMode="numeric"
            placeholder="4"
          />
        </label>

        <label className="space-y-2">
          <span className="text-sm font-medium text-slate-800">
            Lesson title
          </span>
          <input
            data-field="lessonTitle"
            className={`w-full rounded-2xl border bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-cyan-700 focus:ring-2 focus:ring-cyan-100 ${fieldRingClass("lessonTitle")}`}
            value={lessonTitle}
            onChange={(event) => setLessonTitle(event.target.value)}
            placeholder="Supporting Ideas With Evidence"
          />
        </label>

        <label className="space-y-2 md:col-span-2">
          <span className="text-sm font-medium text-slate-800">
            Lesson code
          </span>
          <input
            data-field="lessonCode"
            className={`w-full rounded-2xl border bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-cyan-700 focus:ring-2 focus:ring-cyan-100 ${fieldRingClass("lessonCode")}`}
            value={lessonCode}
            onChange={(event) => setLessonCode(event.target.value)}
            placeholder="ENG6-U1-L4"
          />
        </label>
      </section>

      <section className="space-y-4">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.18em] text-slate-500">
            Curriculum
          </p>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <label className="space-y-2">
            <span className="text-sm font-medium text-slate-800">
              Competency code
            </span>
            <input
              data-field="competencyCode"
              className={`w-full rounded-2xl border bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-cyan-700 focus:ring-2 focus:ring-cyan-100 ${fieldRingClass("competencyCode")}`}
              value={competencyCode}
              onChange={(event) => setCompetencyCode(event.target.value)}
              placeholder="EN6RC-Ia-2.4"
            />
          </label>

          <label className="space-y-2 md:col-span-1">
            <span className="text-sm font-medium text-slate-800">
              Competency description
            </span>
            <textarea
              data-field="competencyDescription"
              className={`min-h-28 w-full rounded-2xl border bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-cyan-700 focus:ring-2 focus:ring-cyan-100 ${fieldRingClass("competencyDescription")}`}
              value={competencyDescription}
              onChange={(event) => setCompetencyDescription(event.target.value)}
              placeholder="Explain how details in a text support the author's main idea."
            />
          </label>
        </div>

        <div
          data-field="subCompetencies"
          className={`space-y-3 rounded-2xl border p-4 transition ${
            firstErrorField === "subCompetencies"
              ? "border-rose-400 bg-rose-50/30 ring-2 ring-rose-100"
              : "border-slate-200 bg-surface"
          }`}
        >
          <div className="flex items-center justify-between gap-3">
            <div>
              <h3 className="text-sm font-semibold text-slate-900">
                Sub-competencies
              </h3>
              <p className="text-sm text-slate-600">
                Add the ordered sub-competency rows the lesson should target.
              </p>
            </div>
            <button
              type="button"
              className="rounded-full border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 transition hover:border-cyan-700 hover:text-cyan-800"
              onClick={addSubCompetency}
            >
              Add row
            </button>
          </div>

          <div className="space-y-3">
            {subCompetencies.map((entry, index) => (
              <div
                key={`${entry.id}-${index}`}
                className="grid gap-3 rounded-2xl border border-slate-200 bg-white p-4 md:grid-cols-[minmax(0,12rem)_minmax(0,1fr)_auto]"
              >
                <label className="space-y-2">
                  <span className="text-sm font-medium text-slate-800">
                    Code
                  </span>
                  <input
                    className="w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-cyan-700 focus:ring-2 focus:ring-cyan-100"
                    value={entry.id}
                    onChange={(event) =>
                      updateSubCompetency(index, "id", event.target.value)
                    }
                    placeholder={`SC-${index + 1}`}
                  />
                </label>

                <label className="space-y-2">
                  <span className="text-sm font-medium text-slate-800">
                    Label
                  </span>
                  <input
                    className="w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-cyan-700 focus:ring-2 focus:ring-cyan-100"
                    value={entry.label}
                    onChange={(event) =>
                      updateSubCompetency(index, "label", event.target.value)
                    }
                    placeholder="Distinguish a claim from supporting evidence"
                  />
                </label>

                <div className="flex items-end">
                  <button
                    type="button"
                    className="rounded-full border border-rose-200 px-4 py-2 text-sm font-medium text-rose-700 transition hover:border-rose-400"
                    onClick={() => removeSubCompetency(index)}
                    disabled={subCompetencies.length === 1}
                  >
                    Remove
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2">
        <div className="md:col-span-2">
          <p className="text-sm font-semibold uppercase tracking-[0.18em] text-slate-500">
            Instructional design
          </p>
        </div>

        <label className="space-y-2 md:col-span-2">
          <span className="text-sm font-medium text-slate-800">
            Core concept
          </span>
          <textarea
            data-field="coreConcept"
            className={`min-h-28 w-full rounded-2xl border bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-cyan-700 focus:ring-2 focus:ring-cyan-100 ${fieldRingClass("coreConcept")}`}
            value={coreConcept}
            onChange={(event) => setCoreConcept(event.target.value)}
            placeholder="Strong readers use details from a text to justify what they understand."
          />
        </label>

        <label className="space-y-2">
          <span className="text-sm font-medium text-slate-800">
            Bloom target 1
          </span>
          <input
            data-field="bloomTargetOne"
            className={`w-full rounded-2xl border bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-cyan-700 focus:ring-2 focus:ring-cyan-100 ${fieldRingClass("bloomTargetOne")}`}
            value={bloomTargetOne}
            onChange={(event) => setBloomTargetOne(event.target.value)}
            placeholder="identify"
          />
        </label>

        <label className="space-y-2">
          <span className="text-sm font-medium text-slate-800">
            Bloom target 2
          </span>
          <input
            data-field="bloomTargetTwo"
            className={`w-full rounded-2xl border bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-cyan-700 focus:ring-2 focus:ring-cyan-100 ${fieldRingClass("bloomTargetTwo")}`}
            value={bloomTargetTwo}
            onChange={(event) => setBloomTargetTwo(event.target.value)}
            placeholder="explain"
          />
        </label>

        <label className="space-y-2">
          <span className="text-sm font-medium text-slate-800">
            Bloom target 3
          </span>
          <input
            data-field="bloomTargetThree"
            className={`w-full rounded-2xl border bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-cyan-700 focus:ring-2 focus:ring-cyan-100 ${fieldRingClass("bloomTargetThree")}`}
            value={bloomTargetThree}
            onChange={(event) => setBloomTargetThree(event.target.value)}
            placeholder="justify"
          />
        </label>

        <label className="space-y-2 md:col-span-2">
          <span className="text-sm font-medium text-slate-800">
            Essential question seed
          </span>
          <textarea
            data-field="essentialQuestionSeed"
            className={`min-h-28 w-full rounded-2xl border bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-cyan-700 focus:ring-2 focus:ring-cyan-100 ${fieldRingClass("essentialQuestionSeed")}`}
            value={essentialQuestionSeed}
            onChange={(event) => setEssentialQuestionSeed(event.target.value)}
            placeholder="How do readers prove an idea is supported by the text?"
          />
        </label>
      </section>

      <section className="grid gap-4 md:grid-cols-2">
        <div className="md:col-span-2">
          <p className="text-sm font-semibold uppercase tracking-[0.18em] text-slate-500">
            Optional inputs
          </p>
        </div>

        <label className="space-y-2 md:col-span-2">
          <span className="text-sm font-medium text-slate-800">
            Vocabulary seeds
          </span>
          <textarea
            className="min-h-28 w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-cyan-700 focus:ring-2 focus:ring-cyan-100"
            value={vocabularySeeds}
            onChange={(event) => setVocabularySeeds(event.target.value)}
            placeholder="claim, evidence, support"
          />
          <p className="text-xs leading-5 text-slate-500">
            Separate entries with commas or line breaks.
          </p>
        </label>

        <label className="space-y-2">
          <span className="text-sm font-medium text-slate-800">
            Model passage domain
          </span>
          <input
            className="w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-cyan-700 focus:ring-2 focus:ring-cyan-100"
            value={modelPassageDomain}
            onChange={(event) => setModelPassageDomain(event.target.value)}
            placeholder="community gardening"
          />
        </label>

        <label className="space-y-2">
          <span className="text-sm font-medium text-slate-800">
            Assessment passage domain
          </span>
          <input
            className="w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-cyan-700 focus:ring-2 focus:ring-cyan-100"
            value={assessmentPassageDomain}
            onChange={(event) => setAssessmentPassageDomain(event.target.value)}
            placeholder="reef conservation"
          />
        </label>

        <label className="space-y-2">
          <span className="text-sm font-medium text-slate-800">
            Tone register
          </span>
          <select
            className="w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-cyan-700 focus:ring-2 focus:ring-cyan-100"
            value={toneRegister}
            onChange={(event) => setToneRegister(event.target.value)}
          >
            {toneOptions.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        </label>

        <label className="space-y-2">
          <span className="text-sm font-medium text-slate-800">
            Length preset
          </span>
          <select
            className="w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-cyan-700 focus:ring-2 focus:ring-cyan-100"
            value={lengthPreset}
            onChange={(event) =>
              setLengthPreset(event.target.value as LengthPreset)
            }
          >
            {lengthOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
      </section>

      <div className="flex flex-col gap-4 border-t border-slate-200 pt-6 sm:flex-row sm:items-center sm:justify-between">
        {errorMessage ? (
          <p className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
            {errorMessage}
          </p>
        ) : (
          <p className="text-sm leading-6 text-slate-500">
            Required fields are validated before the request is emitted.
          </p>
        )}

        <button
          type="submit"
          className="inline-flex items-center justify-center rounded-full bg-slate-950 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
          disabled={isLoading}
        >
          {isLoading ? "Preparing request..." : "Continue to generation"}
        </button>
      </div>
    </form>
  );
}
