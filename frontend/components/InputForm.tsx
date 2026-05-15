"use client";

import { useState } from "react";

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
  entertainExample: string,
  informExample: string,
  persuadeExample: string,
): Record<string, string> | undefined {
  const entries = Object.entries({
    model_passage: modelPassage.trim(),
    assessment_passage: assessmentPassage.trim(),
    entertain_example: entertainExample.trim(),
    inform_example: informExample.trim(),
    persuade_example: persuadeExample.trim(),
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
  const [entertainExampleDomain, setEntertainExampleDomain] = useState("");
  const [informExampleDomain, setInformExampleDomain] = useState("");
  const [persuadeExampleDomain, setPersuadeExampleDomain] = useState("");
  const [toneRegister, setToneRegister] = useState("warm-formal");
  const [lengthPreset, setLengthPreset] = useState<LengthPreset>("standard");

  const [errorMessage, setErrorMessage] = useState<string | null>(null);

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

    if (
      !trimmedSubject ||
      !trimmedMarket ||
      !trimmedLanguage ||
      !trimmedUnitTitle ||
      !trimmedLessonTitle ||
      !trimmedLessonCode ||
      !trimmedCompetencyCode ||
      !trimmedCompetencyDescription ||
      !trimmedCoreConcept ||
      !trimmedBloomTargetOne ||
      !trimmedBloomTargetTwo ||
      !trimmedBloomTargetThree ||
      !trimmedEssentialQuestionSeed ||
      !trimmedToneRegister
    ) {
      setErrorMessage(
        "Complete every required field before generating a study guide.",
      );
      return null;
    }

    if (
      Number.isNaN(parsedGradeLevel) ||
      parsedGradeLevel < 1 ||
      parsedGradeLevel > 12 ||
      Number.isNaN(parsedUnitNumber) ||
      parsedUnitNumber < 1 ||
      Number.isNaN(parsedLessonNumber) ||
      parsedLessonNumber < 1
    ) {
      setErrorMessage(
        "Grade, unit number, and lesson number must be valid positive numbers.",
      );
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
      return null;
    }

    setErrorMessage(null);

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
          entertainExampleDomain,
          informExampleDomain,
          persuadeExampleDomain,
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
      className="space-y-8 rounded-3xl border border-slate-200 bg-surface-strong p-6 shadow-sm sm:p-8"
      onSubmit={handleSubmit}
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
            className="w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-cyan-700 focus:ring-2 focus:ring-cyan-100"
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
            className="w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-cyan-700 focus:ring-2 focus:ring-cyan-100"
            value={gradeLevel}
            onChange={(event) => setGradeLevel(event.target.value)}
            inputMode="numeric"
            placeholder="6"
          />
        </label>

        <label className="space-y-2">
          <span className="text-sm font-medium text-slate-800">Market</span>
          <input
            className="w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-cyan-700 focus:ring-2 focus:ring-cyan-100"
            value={market}
            onChange={(event) => setMarket(event.target.value)}
            placeholder="PH"
          />
        </label>

        <label className="space-y-2">
          <span className="text-sm font-medium text-slate-800">Language</span>
          <input
            className="w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-cyan-700 focus:ring-2 focus:ring-cyan-100"
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
            className="w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-cyan-700 focus:ring-2 focus:ring-cyan-100"
            value={unitNumber}
            onChange={(event) => setUnitNumber(event.target.value)}
            inputMode="numeric"
            placeholder="1"
          />
        </label>

        <label className="space-y-2">
          <span className="text-sm font-medium text-slate-800">Unit title</span>
          <input
            className="w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-cyan-700 focus:ring-2 focus:ring-cyan-100"
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
            className="w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-cyan-700 focus:ring-2 focus:ring-cyan-100"
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
            className="w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-cyan-700 focus:ring-2 focus:ring-cyan-100"
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
            className="w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-cyan-700 focus:ring-2 focus:ring-cyan-100"
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
              className="w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-cyan-700 focus:ring-2 focus:ring-cyan-100"
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
              className="min-h-28 w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-cyan-700 focus:ring-2 focus:ring-cyan-100"
              value={competencyDescription}
              onChange={(event) => setCompetencyDescription(event.target.value)}
              placeholder="Explain how details in a text support the author's main idea."
            />
          </label>
        </div>

        <div className="space-y-3 rounded-2xl border border-slate-200 bg-surface p-4">
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
            className="min-h-28 w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-cyan-700 focus:ring-2 focus:ring-cyan-100"
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
            className="w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-cyan-700 focus:ring-2 focus:ring-cyan-100"
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
            className="w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-cyan-700 focus:ring-2 focus:ring-cyan-100"
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
            className="w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-cyan-700 focus:ring-2 focus:ring-cyan-100"
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
            className="min-h-28 w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-cyan-700 focus:ring-2 focus:ring-cyan-100"
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
            Entertain example domain
          </span>
          <input
            className="w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-cyan-700 focus:ring-2 focus:ring-cyan-100"
            value={entertainExampleDomain}
            onChange={(event) => setEntertainExampleDomain(event.target.value)}
            placeholder="folktales"
          />
        </label>

        <label className="space-y-2">
          <span className="text-sm font-medium text-slate-800">
            Inform example domain
          </span>
          <input
            className="w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-cyan-700 focus:ring-2 focus:ring-cyan-100"
            value={informExampleDomain}
            onChange={(event) => setInformExampleDomain(event.target.value)}
            placeholder="science articles"
          />
        </label>

        <label className="space-y-2">
          <span className="text-sm font-medium text-slate-800">
            Persuade example domain
          </span>
          <input
            className="w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-cyan-700 focus:ring-2 focus:ring-cyan-100"
            value={persuadeExampleDomain}
            onChange={(event) => setPersuadeExampleDomain(event.target.value)}
            placeholder="school campaigns"
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
