import React, { type JSX } from "react";

import type {
  PreviewSection as PreviewSectionData,
  PreviewSectionProps,
} from "@/lib/types";
import PreviewIcon, {
  hasPreviewIcon,
  PREVIEW_CALLOUT_ICON_KEYS,
} from "@/components/PreviewIcon";

type ContentRecord = Record<string, unknown>;

function isRecord(value: unknown): value is ContentRecord {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function getString(record: ContentRecord, key: string): string | null {
  const value = record[key];
  return typeof value === "string" && value.trim().length > 0 ? value : null;
}

function getNumber(record: ContentRecord, key: string): number | null {
  const value = record[key];
  return typeof value === "number" ? value : null;
}

function getStringArray(record: ContentRecord, key: string): string[] {
  const value = record[key];
  if (!Array.isArray(value)) {
    return [];
  }

  return value.filter(
    (item): item is string =>
      typeof item === "string" && item.trim().length > 0,
  );
}

function getRecordArray(record: ContentRecord, key: string): ContentRecord[] {
  const value = record[key];
  if (!Array.isArray(value)) {
    return [];
  }

  return value.filter(isRecord);
}

function getNestedRecord(
  record: ContentRecord,
  key: string,
): ContentRecord | null {
  const value = record[key];
  return isRecord(value) ? value : null;
}

function getNonEmptyEntries(record: ContentRecord): [string, unknown][] {
  return Object.entries(record).filter(([, value]) => {
    if (value === null || value === undefined) {
      return false;
    }

    if (typeof value === "string") {
      return value.trim().length > 0;
    }

    if (Array.isArray(value)) {
      return value.length > 0;
    }

    return true;
  });
}

function toSectionKey(sectionId: string): string {
  return sectionId.replace(/-\d+$/, "");
}

export function formatLabel(value: string): string {
  return value.replace(/_/g, " ");
}

function renderParagraphs(paragraphs: string[]): JSX.Element | null {
  if (paragraphs.length === 0) {
    return null;
  }

  return (
    <div className="space-y-4 text-sm leading-7 text-slate-700 sm:text-base">
      {paragraphs.map((paragraph) => (
        <p key={paragraph} className="break-words [overflow-wrap:anywhere]">
          {paragraph}
        </p>
      ))}
    </div>
  );
}

function renderBullets(items: string[]): JSX.Element | null {
  if (items.length === 0) {
    return null;
  }

  return (
    <ul className="grid gap-2 text-sm leading-6 text-slate-700 sm:text-base">
      {items.map((item) => (
        <li
          key={item}
          className="rounded-2xl border border-slate-200 bg-white px-4 py-3 break-words [overflow-wrap:anywhere]"
        >
          {item}
        </li>
      ))}
    </ul>
  );
}

function renderLabeledListSection(
  title: string,
  items: string[],
  sectionClassName = "rounded-[2rem] border border-slate-200 bg-slate-50 p-5",
  itemClassName = "rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm leading-6 text-slate-700 break-words [overflow-wrap:anywhere]",
): JSX.Element | null {
  if (items.length === 0) {
    return null;
  }

  return (
    <section className={sectionClassName}>
      <h3 className="text-sm font-semibold uppercase tracking-[0.18em] text-slate-500">
        {title}
      </h3>
      <ul className="mt-4 grid gap-3">
        {items.map((item) => (
          <li key={item} className={itemClassName}>
            {item}
          </li>
        ))}
      </ul>
    </section>
  );
}

function renderKeyValueGrid(
  record: ContentRecord,
  gridClassName = "grid gap-4",
): JSX.Element {
  const entries = getNonEmptyEntries(record);

  return (
    <dl className={gridClassName}>
      {entries.map(([key, value]) => (
        <div
          key={key}
          className="rounded-2xl border border-slate-200 bg-white px-4 py-4"
        >
          <dt className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
            {formatLabel(key)}
          </dt>
          <dd className="mt-2 text-sm leading-6 text-slate-700 break-words [overflow-wrap:anywhere]">
            {typeof value === "string" || typeof value === "number"
              ? String(value)
              : JSON.stringify(value)}
          </dd>
        </div>
      ))}
    </dl>
  );
}

function renderGenericArray(items: ContentRecord[]): JSX.Element | null {
  if (items.length === 0) {
    return null;
  }

  return (
    <div className="grid gap-4">
      {items.map((item, index) => (
        <article
          key={`${index}-${JSON.stringify(item)}`}
          className="rounded-3xl border border-slate-200 bg-white p-5"
        >
          {renderKeyValueGrid(item)}
        </article>
      ))}
    </div>
  );
}

function renderVocabulary(section: PreviewSectionData): JSX.Element {
  const entries = getRecordArray(section.content, "entries");

  return (
    <div className="grid gap-4 md:grid-cols-2">
      {entries.map((entry) => {
        const word = getString(entry, "word") ?? "Vocabulary";
        const partOfSpeech = getString(entry, "part_of_speech");
        const definition = getString(entry, "definition");
        const exampleSentence = getString(entry, "example_sentence");

        return (
          <article
            key={word}
            className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm"
          >
            <div className="flex items-start justify-between gap-3">
              <h3 className="text-lg font-semibold tracking-tight text-slate-950">
                {word}
              </h3>
              {partOfSpeech ? (
                <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] text-amber-800">
                  {partOfSpeech}
                </span>
              ) : null}
            </div>
            {definition ? (
              <p className="mt-4 text-sm leading-6 text-slate-700">
                {definition}
              </p>
            ) : null}
            {exampleSentence ? (
              <p className="mt-4 rounded-2xl bg-slate-50 px-4 py-3 text-sm italic leading-6 text-slate-600">
                {exampleSentence}
              </p>
            ) : null}
          </article>
        );
      })}
    </div>
  );
}

function renderLearningTargets(section: PreviewSectionData): JSX.Element {
  const targets = getRecordArray(section.content, "targets");
  const competencyFocus = isRecord(section.content.competency_focus)
    ? section.content.competency_focus
    : null;
  const lessonId = competencyFocus
    ? getString(competencyFocus, "lesson_id")
    : null;
  const coreConcept = competencyFocus
    ? getString(competencyFocus, "core_concept")
    : null;

  return (
    <div className="space-y-5">
      {competencyFocus ? (
        <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-sm">
          <h3 className="text-sm font-semibold uppercase tracking-[0.18em] text-slate-500">
            Competency focus
          </h3>
          <div className="mt-4 grid gap-4">
            {lessonId ? (
              <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4">
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                  Lesson ID
                </p>
                <p className="mt-2 text-sm leading-6 text-slate-700 break-words [overflow-wrap:anywhere]">
                  {lessonId}
                </p>
              </div>
            ) : null}
            {coreConcept ? (
              <div className="rounded-2xl border border-cyan-100 bg-cyan-50 px-4 py-4">
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-cyan-900">
                  Core concept
                </p>
                <p className="mt-2 text-sm leading-7 text-slate-700 break-words [overflow-wrap:anywhere] sm:text-base">
                  {coreConcept}
                </p>
              </div>
            ) : null}
          </div>
        </section>
      ) : null}
      <div className="grid gap-4">
        {targets.map((target) => {
          const number = getNumber(target, "number");
          const objective = getString(target, "objective");
          const bloomVerb = getString(target, "bloom_verb");
          const successLookFor = getString(target, "success_look_for");

          return (
            <article
              key={`${number ?? "target"}-${objective ?? "item"}`}
              className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm"
            >
              <div className="flex flex-wrap items-center gap-3">
                {number !== null ? (
                  <span className="rounded-full bg-cyan-100 px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] text-cyan-900">
                    Target {number}
                  </span>
                ) : null}
                {bloomVerb ? (
                  <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] text-slate-700">
                    {bloomVerb}
                  </span>
                ) : null}
              </div>
              {objective ? (
                <p className="mt-4 text-base font-semibold leading-7 text-slate-950">
                  {objective}
                </p>
              ) : null}
              {successLookFor ? (
                <p className="mt-3 text-sm leading-6 text-slate-700">
                  <span className="font-semibold text-slate-900">
                    Success looks like:
                  </span>{" "}
                  {successLookFor}
                </p>
              ) : null}
            </article>
          );
        })}
      </div>
    </div>
  );
}

function renderPassage(section: PreviewSectionData): JSX.Element {
  const passage = getStringArray(section.content, "passage");
  const topicDomain = getString(section.content, "topic_domain");
  const genre = getString(section.content, "genre");
  const evidenceFocus =
    getString(section.content, "evidence_focus") ??
    getString(section.content, "answerability_note");
  const textFeatures = getStringArray(section.content, "text_features");
  const evidenceClues = getStringArray(section.content, "evidence_clues");

  return (
    <div className="space-y-5">
      <div className="grid gap-4">
        {topicDomain ? (
          <div className="rounded-2xl border border-slate-200 bg-white px-4 py-4">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
              Topic domain
            </p>
            <p className="mt-2 text-sm leading-6 text-slate-700 break-words [overflow-wrap:anywhere]">
              {topicDomain}
            </p>
          </div>
        ) : null}
        {genre ? (
          <div className="rounded-2xl border border-slate-200 bg-white px-4 py-4">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
              Genre
            </p>
            <p className="mt-2 text-sm leading-6 text-slate-700 break-words [overflow-wrap:anywhere]">
              {genre}
            </p>
          </div>
        ) : null}
      </div>
      <div className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-sm">
        {renderParagraphs(passage)}
      </div>
      {renderLabeledListSection("Text features", textFeatures)}
      {evidenceFocus ? (
        <section className="rounded-[2rem] border border-cyan-100 bg-cyan-50 p-5 shadow-sm">
          <h3 className="text-sm font-semibold uppercase tracking-[0.18em] text-cyan-900">
            Evidence focus
          </h3>
          <p className="mt-4 text-sm leading-7 text-slate-700 break-words [overflow-wrap:anywhere] sm:text-base">
            {evidenceFocus}
          </p>
        </section>
      ) : null}
      {renderLabeledListSection(
        "Evidence clues",
        evidenceClues,
        "rounded-[2rem] border border-amber-200 bg-amber-50 p-5 shadow-sm",
        "rounded-2xl border border-amber-200 bg-white px-4 py-3 text-sm leading-6 text-slate-700 break-words [overflow-wrap:anywhere]",
      )}
    </div>
  );
}

function renderQuestionDetail(
  label: string,
  value: string,
  tone: "slate" | "amber" = "slate",
): JSX.Element {
  const toneClassName =
    tone === "amber"
      ? "border-amber-200 bg-amber-50 text-amber-950"
      : "border-slate-200 bg-slate-50 text-slate-700";

  return (
    <p
      className={`mt-4 rounded-2xl border px-4 py-3 text-sm leading-6 break-words [overflow-wrap:anywhere] ${toneClassName}`}
    >
      <span className="font-semibold text-slate-900">{label}:</span> {value}
    </p>
  );
}

function renderIntro(section: PreviewSectionData): JSX.Element {
  const hook = getString(section.content, "hook");
  const essentialQuestion = getString(section.content, "essential_question");
  const paragraphs = getStringArray(section.content, "paragraphs");
  const bridgeToLesson = getString(section.content, "bridge_to_lesson");

  return (
    <div className="space-y-5">
      {hook ? (
        <section className="rounded-[2rem] border border-cyan-100 bg-cyan-50 p-6 shadow-sm">
          <h3 className="text-sm font-semibold uppercase tracking-[0.18em] text-cyan-900">
            Hook
          </h3>
          <p className="mt-4 text-sm leading-7 text-slate-700 break-words [overflow-wrap:anywhere] sm:text-base">
            {hook}
          </p>
        </section>
      ) : null}
      {essentialQuestion ? (
        <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-sm">
          <h3 className="text-sm font-semibold uppercase tracking-[0.18em] text-slate-500">
            Essential question
          </h3>
          <p className="mt-4 text-sm leading-7 text-slate-700 break-words [overflow-wrap:anywhere] sm:text-base">
            {essentialQuestion}
          </p>
        </section>
      ) : null}
      {renderParagraphs(paragraphs)}
      {bridgeToLesson ? (
        <section className="rounded-[2rem] border border-dashed border-slate-300 bg-slate-50 px-5 py-4">
          <p className="text-sm leading-6 text-slate-700 break-words [overflow-wrap:anywhere] sm:text-base">
            <span className="font-semibold text-slate-900">
              Bridge to lesson:
            </span>{" "}
            {bridgeToLesson}
          </p>
        </section>
      ) : null}
    </div>
  );
}

function renderWarmup(section: PreviewSectionData): JSX.Element {
  const activityType = getString(section.content, "activity_type");
  const purpose = getString(section.content, "purpose");
  const instructions = getStringArray(section.content, "student_instructions");
  const teacherTip = getString(section.content, "teacher_tip");
  const estimatedMinutes = getNumber(section.content, "estimated_minutes");

  return (
    <div className="space-y-5">
      <div className="grid gap-4 md:grid-cols-2">
        {activityType ? (
          <div className="rounded-2xl border border-slate-200 bg-white px-4 py-4">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
              Activity type
            </p>
            <p className="mt-2 text-sm leading-6 text-slate-700 break-words [overflow-wrap:anywhere]">
              {activityType}
            </p>
          </div>
        ) : null}
        {estimatedMinutes !== null ? (
          <div className="rounded-2xl border border-slate-200 bg-white px-4 py-4">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
              Estimated time
            </p>
            <p className="mt-2 text-sm leading-6 text-slate-700">
              {estimatedMinutes} minutes
            </p>
          </div>
        ) : null}
      </div>
      {purpose ? (
        <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-sm">
          <h3 className="text-sm font-semibold uppercase tracking-[0.18em] text-slate-500">
            Purpose
          </h3>
          <p className="mt-4 text-sm leading-7 text-slate-700 break-words [overflow-wrap:anywhere] sm:text-base">
            {purpose}
          </p>
        </section>
      ) : null}
      {instructions.length > 0 ? (
        <section className="space-y-3">
          <h3 className="text-sm font-semibold uppercase tracking-[0.18em] text-slate-500">
            Student instructions
          </h3>
          <ol className="grid gap-3">
            {instructions.map((instruction, index) => (
              <li
                key={`${index}-${instruction}`}
                className="flex gap-3 rounded-2xl border border-slate-200 bg-white px-4 py-4"
              >
                <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-cyan-100 text-xs font-semibold text-cyan-900">
                  {index + 1}
                </span>
                <p className="min-w-0 text-sm leading-6 text-slate-700 break-words [overflow-wrap:anywhere]">
                  {instruction}
                </p>
              </li>
            ))}
          </ol>
        </section>
      ) : null}
      {teacherTip ? (
        <section className="rounded-[2rem] border border-amber-200 bg-amber-50 p-5 shadow-sm">
          <p className="text-sm leading-6 text-amber-950 break-words [overflow-wrap:anywhere]">
            <span className="font-semibold">Teacher tip:</span> {teacherTip}
          </p>
        </section>
      ) : null}
    </div>
  );
}

function renderCoreExplainer(section: PreviewSectionData): JSX.Element {
  const overview = getString(section.content, "overview");
  const explainedPoints = getRecordArray(section.content, "explained_points");
  const closingSummary = getString(section.content, "closing_summary");

  return (
    <div className="space-y-5">
      {overview ? (
        <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-sm">
          <h3 className="text-sm font-semibold uppercase tracking-[0.18em] text-slate-500">
            Overview
          </h3>
          <p className="mt-4 text-sm leading-7 text-slate-700 break-words [overflow-wrap:anywhere] sm:text-base">
            {overview}
          </p>
        </section>
      ) : null}
      <div className="grid gap-4">
        {explainedPoints.map((point, index) => {
          const label = getString(point, "sub_competency_label");
          const explanation = getString(point, "explanation");
          const realWorldConnection = getString(point, "real_world_connection");

          return (
            <article
              key={`${label ?? "point"}-${index}`}
              className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm"
            >
              {label ? (
                <h3 className="text-lg font-semibold tracking-tight text-slate-950">
                  {label}
                </h3>
              ) : null}
              {explanation ? (
                <p className="mt-4 text-sm leading-7 text-slate-700 break-words [overflow-wrap:anywhere] sm:text-base">
                  {explanation}
                </p>
              ) : null}
              {realWorldConnection ? (
                <p className="mt-4 rounded-2xl bg-slate-50 px-4 py-3 text-sm leading-6 text-slate-700 break-words [overflow-wrap:anywhere]">
                  <span className="font-semibold text-slate-900">
                    Real-world connection:
                  </span>{" "}
                  {realWorldConnection}
                </p>
              ) : null}
            </article>
          );
        })}
      </div>
      {closingSummary ? (
        <section className="rounded-[2rem] border border-dashed border-slate-300 bg-slate-50 px-5 py-4">
          <p className="text-sm leading-6 text-slate-700 break-words [overflow-wrap:anywhere] sm:text-base">
            <span className="font-semibold text-slate-900">
              Closing summary:
            </span>{" "}
            {closingSummary}
          </p>
        </section>
      ) : null}
    </div>
  );
}

function renderStrategyList(section: PreviewSectionData): JSX.Element {
  const strategies = getRecordArray(section.content, "strategies");

  return (
    <div className="grid gap-4">
      {strategies.map((strategy, index) => {
        const name = getString(strategy, "name") ?? `Strategy ${index + 1}`;
        const whenToUse = getString(strategy, "when_to_use");
        const steps = getStringArray(strategy, "steps");

        return (
          <article
            key={`${name}-${index}`}
            className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm"
          >
            <h3 className="text-lg font-semibold tracking-tight text-slate-950">
              {name}
            </h3>
            {whenToUse ? (
              <p className="mt-4 text-sm leading-7 text-slate-700 break-words [overflow-wrap:anywhere] sm:text-base">
                <span className="font-semibold text-slate-900">
                  When to use:
                </span>{" "}
                {whenToUse}
              </p>
            ) : null}
            {steps.length > 0 ? (
              <ol className="mt-4 grid gap-3">
                {steps.map((step, stepIndex) => (
                  <li
                    key={`${name}-${stepIndex}-${step}`}
                    className="flex gap-3 rounded-2xl bg-slate-50 px-4 py-4"
                  >
                    <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-cyan-100 text-xs font-semibold text-cyan-900">
                      {stepIndex + 1}
                    </span>
                    <p className="min-w-0 text-sm leading-6 text-slate-700 break-words [overflow-wrap:anywhere]">
                      {step}
                    </p>
                  </li>
                ))}
              </ol>
            ) : null}
          </article>
        );
      })}
    </div>
  );
}

function renderQuestionCards(
  title: string,
  questions: ContentRecord[],
  detailKey: string,
  detailLabel: string,
  extraDetailKey?: string,
  extraDetailLabel?: string,
  responseTypeMode: "badge" | "detail" = "badge",
): JSX.Element | null {
  if (questions.length === 0) {
    return null;
  }

  return (
    <section className="space-y-4">
      <h3 className="text-sm font-semibold uppercase tracking-[0.18em] text-slate-500">
        {title}
      </h3>
      <div className="grid gap-4">
        {questions.map((question, index) => {
          const number = getNumber(question, "number");
          const prompt = getString(question, "question");
          const detail = getString(question, detailKey);
          const extraDetail = extraDetailKey
            ? getString(question, extraDetailKey)
            : null;
          const expectedResponseType = getString(
            question,
            "expected_response_type",
          );
          const questionType = getString(question, "question_type");

          return (
            <article
              key={`${title}-${number ?? index}`}
              className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm"
            >
              <div className="flex flex-wrap items-center gap-3">
                {number !== null ? (
                  <span className="rounded-full bg-cyan-100 px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] text-cyan-900">
                    Question {number}
                  </span>
                ) : null}
                {questionType ? (
                  <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] text-slate-700">
                    {questionType}
                  </span>
                ) : null}
                {expectedResponseType && responseTypeMode === "badge" ? (
                  <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] text-slate-700">
                    {expectedResponseType}
                  </span>
                ) : null}
              </div>
              {prompt ? (
                <p className="mt-4 text-base font-semibold leading-7 text-slate-950 break-words [overflow-wrap:anywhere]">
                  {prompt}
                </p>
              ) : null}
              {expectedResponseType && responseTypeMode === "detail"
                ? renderQuestionDetail(
                    "Response type",
                    expectedResponseType,
                    "slate",
                  )
                : null}
              {detail
                ? renderQuestionDetail(
                    detailLabel,
                    detail,
                    detailLabel === "Evidence hint" ? "amber" : "slate",
                  )
                : null}
              {extraDetail && extraDetailLabel
                ? renderQuestionDetail(extraDetailLabel, extraDetail, "slate")
                : null}
            </article>
          );
        })}
      </div>
    </section>
  );
}

function renderCheckIn(section: PreviewSectionData): JSX.Element {
  const passageTitle = getString(section.content, "passage_title");
  const questions = getRecordArray(section.content, "questions");

  return (
    <div className="space-y-5">
      {passageTitle ? (
        <div className="rounded-2xl border border-slate-200 bg-white px-4 py-4">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
            Passage title
          </p>
          <p className="mt-2 text-sm leading-6 text-slate-700 break-words [overflow-wrap:anywhere]">
            {passageTitle}
          </p>
        </div>
      ) : null}
      {renderQuestionCards(
        "Questions",
        questions,
        "evidence_hint",
        "Evidence hint",
        undefined,
        undefined,
        "detail",
      )}
    </div>
  );
}

function renderKeyPoints(section: PreviewSectionData): JSX.Element {
  const points = getRecordArray(section.content, "points");

  return (
    <div className="grid gap-4">
      {points.map((point, index) => {
        const number = getNumber(point, "number");
        const label = getString(point, "sub_competency_label");
        const statement = getString(point, "statement");

        return (
          <article
            key={`${number ?? index}-${label ?? "point"}`}
            className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm"
          >
            <div className="flex flex-wrap items-center gap-3">
              {number !== null ? (
                <span className="rounded-full bg-cyan-100 px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] text-cyan-900">
                  Point {number}
                </span>
              ) : null}
              {label ? (
                <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold tracking-[0.14em] text-slate-700 break-words [overflow-wrap:anywhere]">
                  {label}
                </span>
              ) : null}
            </div>
            {statement ? (
              <p className="mt-4 text-sm leading-7 text-slate-700 break-words [overflow-wrap:anywhere] sm:text-base">
                {statement}
              </p>
            ) : null}
          </article>
        );
      })}
    </div>
  );
}

function renderAssessmentQuestions(section: PreviewSectionData): JSX.Element {
  const passageTitle = getString(section.content, "passage_title");
  const questions = getRecordArray(section.content, "questions");

  return (
    <div className="space-y-5">
      {passageTitle ? (
        <div className="rounded-2xl border border-slate-200 bg-white px-4 py-4">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
            Passage title
          </p>
          <p className="mt-2 text-sm leading-6 text-slate-700 break-words [overflow-wrap:anywhere]">
            {passageTitle}
          </p>
        </div>
      ) : null}
      {renderQuestionCards(
        "Questions",
        questions,
        "evidence_hint",
        "Evidence hint",
        undefined,
        undefined,
        "detail",
      )}
    </div>
  );
}

function renderStepUp(section: PreviewSectionData): JSX.Element {
  const challengePrompt = getString(section.content, "challenge_prompt");
  const requiredEvidence = getStringArray(section.content, "required_evidence");
  const successCriteria = getStringArray(section.content, "success_criteria");

  return (
    <div className="space-y-5">
      {challengePrompt ? (
        <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-sm">
          <h3 className="text-sm font-semibold uppercase tracking-[0.18em] text-slate-500">
            Challenge prompt
          </h3>
          <p className="mt-4 text-sm leading-7 text-slate-700 break-words [overflow-wrap:anywhere] sm:text-base">
            {challengePrompt}
          </p>
        </section>
      ) : null}
      {requiredEvidence.length > 0 ? (
        <section className="space-y-3">
          <h3 className="text-sm font-semibold uppercase tracking-[0.18em] text-slate-500">
            Required evidence
          </h3>
          <div className="flex flex-wrap gap-2">
            {requiredEvidence.map((item) => (
              <span
                key={item}
                className="max-w-full rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold text-amber-900 break-words [overflow-wrap:anywhere]"
              >
                {item}
              </span>
            ))}
          </div>
        </section>
      ) : null}
      {successCriteria.length > 0 ? (
        <section className="space-y-3">
          <h3 className="text-sm font-semibold uppercase tracking-[0.18em] text-slate-500">
            Success criteria
          </h3>
          {renderBullets(successCriteria)}
        </section>
      ) : null}
    </div>
  );
}

function renderSubconcept(section: PreviewSectionData): JSX.Element {
  const explanation = getString(section.content, "explanation");
  const workedExample = getString(section.content, "worked_example");
  const subCompetencyLabel = getString(section.content, "sub_competency_label");
  const quickCheck = getNestedRecord(section.content, "quick_check");
  const quickCheckQuestion = quickCheck
    ? getString(quickCheck, "question")
    : null;
  const quickCheckExpectedAnswer = quickCheck
    ? getString(quickCheck, "expected_answer")
    : null;

  return (
    <div className="space-y-5">
      {subCompetencyLabel ? (
        <div className="rounded-2xl border border-slate-200 bg-white px-4 py-4">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
            Sub-competency
          </p>
          <p className="mt-2 text-sm leading-6 text-slate-700 break-words [overflow-wrap:anywhere]">
            {subCompetencyLabel}
          </p>
        </div>
      ) : null}

      {explanation ? (
        <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-sm">
          <h3 className="text-sm font-semibold uppercase tracking-[0.18em] text-slate-500">
            Explanation
          </h3>
          <p className="mt-4 text-sm leading-7 text-slate-700 break-words [overflow-wrap:anywhere] sm:text-base">
            {explanation}
          </p>
        </section>
      ) : null}

      {workedExample ? (
        <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-sm">
          <h3 className="text-sm font-semibold uppercase tracking-[0.18em] text-slate-500">
            Worked example
          </h3>
          <p className="mt-4 text-sm leading-7 text-slate-700 break-words [overflow-wrap:anywhere] sm:text-base">
            {workedExample}
          </p>
        </section>
      ) : null}

      {quickCheckQuestion || quickCheckExpectedAnswer ? (
        <section className="rounded-[2rem] border border-amber-200 bg-amber-50 p-6 shadow-sm">
          <div className="flex items-start gap-3">
            <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-white/80 text-amber-900">
              <PreviewIcon
                iconKey={PREVIEW_CALLOUT_ICON_KEYS.default}
                className="h-5 w-5"
              />
            </span>
            <div className="min-w-0 flex-1 space-y-3">
              <h3 className="text-sm font-semibold uppercase tracking-[0.18em] text-amber-900">
                Quick check
              </h3>
              {quickCheckQuestion ? (
                <p className="text-sm leading-6 text-amber-950 break-words [overflow-wrap:anywhere] sm:text-base">
                  {quickCheckQuestion}
                </p>
              ) : null}
              {quickCheckExpectedAnswer ? (
                <p className="rounded-2xl bg-white/80 px-4 py-3 text-sm leading-6 text-amber-950 break-words [overflow-wrap:anywhere]">
                  <span className="font-semibold">Expected answer:</span>{" "}
                  {quickCheckExpectedAnswer}
                </p>
              ) : null}
            </div>
          </div>
        </section>
      ) : null}
    </div>
  );
}

function renderDeepDive(section: PreviewSectionData): JSX.Element {
  const compareFocus = getString(section.content, "compare_focus");
  const takeaway = getString(section.content, "takeaway");
  const examples = getRecordArray(section.content, "examples");

  return (
    <div className="space-y-5">
      {compareFocus ? (
        <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-sm">
          <h3 className="text-sm font-semibold uppercase tracking-[0.18em] text-slate-500">
            Compare focus
          </h3>
          <p className="mt-4 text-sm leading-7 text-slate-700 break-words [overflow-wrap:anywhere] sm:text-base">
            {compareFocus}
          </p>
        </section>
      ) : null}

      <div className="grid gap-4">
        {examples.map((example, index) => {
          const dimension =
            getString(example, "dimension") ?? `Example ${index + 1}`;
          const topicDomain = getString(example, "topic_domain");
          const explanation = getString(example, "explanation");
          const keyTerms = getStringArray(example, "key_terms");

          return (
            <article
              key={`${dimension}-${topicDomain ?? index}`}
              className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm"
            >
              <div className="flex flex-wrap items-center gap-3">
                <h3 className="text-lg font-semibold tracking-tight text-slate-950">
                  {dimension}
                </h3>
                {topicDomain ? (
                  <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold tracking-[0.14em] text-slate-700 break-words [overflow-wrap:anywhere]">
                    {topicDomain}
                  </span>
                ) : null}
              </div>

              {explanation ? (
                <p className="mt-4 text-sm leading-6 text-slate-700 break-words [overflow-wrap:anywhere] sm:text-base">
                  {explanation}
                </p>
              ) : null}

              {keyTerms.length > 0 ? (
                <div className="mt-4 space-y-2">
                  <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                    Key terms
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {keyTerms.map((word) => (
                      <span
                        key={`${dimension}-${word}`}
                        className="max-w-full rounded-full bg-cyan-100 px-3 py-1 text-xs font-semibold text-cyan-900 break-words [overflow-wrap:anywhere]"
                      >
                        {word}
                      </span>
                    ))}
                  </div>
                </div>
              ) : null}
            </article>
          );
        })}
      </div>

      {takeaway ? (
        <section className="rounded-[2rem] border border-dashed border-slate-300 bg-slate-50 px-5 py-4">
          <p className="text-sm leading-6 text-slate-700 break-words [overflow-wrap:anywhere] sm:text-base">
            <span className="font-semibold text-slate-900">Takeaway:</span>{" "}
            {takeaway}
          </p>
        </section>
      ) : null}
    </div>
  );
}

function renderSelfAssessment(section: PreviewSectionData): JSX.Element {
  const confidenceLevels = getStringArray(section.content, "confidence_levels");
  const rows = getRecordArray(section.content, "rows");

  return (
    <div className="space-y-5">
      {confidenceLevels.length > 0 ? (
        <div className="flex flex-wrap gap-2">
          {confidenceLevels.map((level) => (
            <span
              key={level}
              className="rounded-full bg-lime-100 px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] text-lime-900"
            >
              {level}
            </span>
          ))}
        </div>
      ) : null}
      <div className="grid gap-4">
        {rows.map((row) => {
          const skill = getString(row, "skill") ?? "Skill";
          const reflectionPrompt = getString(row, "reflection_prompt");

          return (
            <article
              key={skill}
              className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm"
            >
              <h3 className="text-base font-semibold leading-7 text-slate-950">
                {skill}
              </h3>
              {reflectionPrompt ? (
                <p className="mt-3 text-sm leading-6 text-slate-700">
                  {reflectionPrompt}
                </p>
              ) : null}
            </article>
          );
        })}
      </div>
    </div>
  );
}

function renderAnswerGroup(
  title: string,
  items: ContentRecord[],
): JSX.Element | null {
  if (items.length === 0) {
    return null;
  }

  return (
    <section className="space-y-4">
      <h3 className="text-sm font-semibold uppercase tracking-[0.18em] text-slate-500">
        {title}
      </h3>
      <div className="grid gap-4">
        {items.map((item) => {
          const questionNumber = getNumber(item, "question_number");
          const question = getString(item, "question");
          const possibleAnswer = getString(item, "possible_answer");
          const evidenceQuote = getString(item, "evidence_quote");

          return (
            <article
              key={`${title}-${questionNumber ?? question ?? "answer"}`}
              className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm"
            >
              <div className="flex flex-wrap items-center gap-3">
                {questionNumber !== null ? (
                  <span className="rounded-full bg-cyan-100 px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] text-cyan-900">
                    Question {questionNumber}
                  </span>
                ) : null}
              </div>
              {question ? (
                <p className="mt-4 text-base font-semibold leading-7 text-slate-950">
                  {question}
                </p>
              ) : null}
              {possibleAnswer ? (
                <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4">
                  <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                    Possible answer
                  </p>
                  <p className="mt-2 text-sm leading-6 text-slate-700 break-words [overflow-wrap:anywhere]">
                    {possibleAnswer}
                  </p>
                </div>
              ) : null}
              {evidenceQuote ? (
                <div className="mt-4 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-4">
                  <p className="text-xs font-semibold uppercase tracking-[0.18em] text-amber-900">
                    Evidence quote
                  </p>
                  <p className="mt-2 text-sm italic leading-6 text-slate-700 break-words [overflow-wrap:anywhere]">
                    {evidenceQuote}
                  </p>
                </div>
              ) : null}
            </article>
          );
        })}
      </div>
    </section>
  );
}

function renderAnswerKey(section: PreviewSectionData): JSX.Element {
  const checkInAnswers = getRecordArray(section.content, "check_in_answers");
  const assessmentAnswers = getRecordArray(
    section.content,
    "assessment_answers",
  );
  const teacherNote = getString(section.content, "teacher_note");
  const rawStepUpAnswer = section.content.step_up_answer;
  const stepUpAnswer = isRecord(rawStepUpAnswer) ? rawStepUpAnswer : null;
  const stepUpChallenge = stepUpAnswer
    ? getString(stepUpAnswer, "challenge_response")
    : typeof rawStepUpAnswer === "string"
      ? rawStepUpAnswer
      : null;
  const requiredEvidence = stepUpAnswer
    ? getStringArray(stepUpAnswer, "required_evidence")
    : [];

  return (
    <div className="space-y-6">
      {renderAnswerGroup("Check-in answers", checkInAnswers)}
      {renderAnswerGroup("Assessment answers", assessmentAnswers)}
      {stepUpChallenge || requiredEvidence.length > 0 ? (
        <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex items-start gap-3">
            <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-slate-100 text-slate-700">
              <PreviewIcon
                iconKey={PREVIEW_CALLOUT_ICON_KEYS.default}
                className="h-5 w-5"
              />
            </span>
            <div className="min-w-0 flex-1">
              <h3 className="text-sm font-semibold uppercase tracking-[0.18em] text-slate-500">
                Step-up response
              </h3>
              {stepUpChallenge ? (
                <p className="mt-4 text-sm leading-6 text-slate-700">
                  {stepUpChallenge}
                </p>
              ) : null}
              {requiredEvidence.length > 0 ? (
                <div className="mt-4 rounded-2xl border border-amber-200 bg-amber-50 p-4">
                  <p className="text-xs font-semibold uppercase tracking-[0.18em] text-amber-900">
                    Required evidence
                  </p>
                  <ul className="mt-3 grid gap-3">
                    {requiredEvidence.map((item) => (
                      <li
                        key={item}
                        className="rounded-2xl border border-amber-200 bg-white px-4 py-3 text-sm leading-6 text-slate-700 break-words [overflow-wrap:anywhere]"
                      >
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null}
            </div>
          </div>
        </section>
      ) : null}
      {teacherNote ? (
        <section className="rounded-[2rem] border border-dashed border-slate-300 bg-slate-50 px-5 py-4 text-sm leading-6 text-slate-700">
          <div className="flex items-start gap-3">
            <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-white text-slate-700">
              <PreviewIcon
                iconKey={PREVIEW_CALLOUT_ICON_KEYS.default}
                className="h-5 w-5"
              />
            </span>
            <p>
              <span className="font-semibold text-slate-900">
                Teacher note:
              </span>{" "}
              {teacherNote}
            </p>
          </div>
        </section>
      ) : null}
    </div>
  );
}

function renderGenericSection(section: PreviewSectionData): JSX.Element {
  const content = section.content;
  const leadFields = [
    "hook",
    "essential_question",
    "bridge_to_lesson",
    "purpose",
    "overview",
    "closing_summary",
    "compare_focus",
    "takeaway",
    "challenge_prompt",
  ]
    .map((key) => getString(content, key))
    .filter((value): value is string => value !== null);

  const listFields = [
    ...getStringArray(content, "paragraphs"),
    ...getStringArray(content, "student_instructions"),
    ...getStringArray(content, "required_evidence"),
    ...getStringArray(content, "success_criteria"),
  ];

  const nestedFields = [
    ...getRecordArray(content, "questions"),
    ...getRecordArray(content, "points"),
    ...getRecordArray(content, "explained_points"),
    ...getRecordArray(content, "strategies"),
    ...getRecordArray(content, "examples"),
  ];

  const topLevelEntries = Object.fromEntries(
    Object.entries(content).filter(([key, value]) => {
      if (
        [
          "title",
          "paragraphs",
          "student_instructions",
          "required_evidence",
          "success_criteria",
          "questions",
          "points",
          "explained_points",
          "strategies",
          "examples",
        ].includes(key)
      ) {
        return false;
      }

      return ![...leadFields, ...listFields].includes(
        typeof value === "string" ? value : "",
      );
    }),
  );

  return (
    <div className="space-y-5">
      {leadFields.length > 0 ? renderParagraphs(leadFields) : null}
      {listFields.length > 0 ? renderBullets(listFields) : null}
      {Object.keys(topLevelEntries).length > 0
        ? renderKeyValueGrid(topLevelEntries)
        : null}
      {renderGenericArray(nestedFields)}
    </div>
  );
}

function renderSectionBody(section: PreviewSectionData): JSX.Element {
  switch (section.section_type) {
    case "intro":
      return renderIntro(section);
    case "learning_targets":
      return renderLearningTargets(section);
    case "warmup":
      return renderWarmup(section);
    case "vocabulary":
      return renderVocabulary(section);
    case "core_explainer":
      return renderCoreExplainer(section);
    case "strategy_list":
      return renderStrategyList(section);
    case "model_passage":
    case "assessment_passage":
      return renderPassage(section);
    case "check_in":
      return renderCheckIn(section);
    case "key_points":
      return renderKeyPoints(section);
    case "assessment_questions":
      return renderAssessmentQuestions(section);
    case "step_up":
      return renderStepUp(section);
    case "subconcept":
      return renderSubconcept(section);
    case "deep_dive":
      return renderDeepDive(section);
    case "self_assessment":
      return renderSelfAssessment(section);
    case "answer_key":
      return renderAnswerKey(section);
    default:
      return renderGenericSection(section);
  }
}

export default function PreviewSection({
  section,
  validation,
}: PreviewSectionProps) {
  const sectionKey = toSectionKey(section.section_id);
  const failures = validation.failures[sectionKey] ?? [];
  const failed = validation.failed_sections.includes(sectionKey);
  const isBestEffort = validation.best_effort_sections.includes(sectionKey);
  const showSectionIcon = hasPreviewIcon(section.icon_key);

  return (
    <article
      id={`section-${section.section_type}`}
      className="scroll-mt-20 space-y-5 rounded-[2rem] border border-slate-200 bg-surface-strong p-6 shadow-sm sm:p-8"
    >
      <header className="flex flex-col gap-4 border-b border-slate-200 pb-5 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex items-start gap-4">
          {showSectionIcon ? (
            <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-amber-100 text-amber-900 shadow-sm">
              <PreviewIcon iconKey={section.icon_key} className="h-5 w-5" />
            </span>
          ) : null}
          <div className="space-y-2">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
              {formatLabel(section.section_type)}
            </p>
            <h2 className="text-2xl font-semibold tracking-tight text-slate-950">
              {section.title}
            </h2>
          </div>
        </div>

        <div className="flex flex-wrap gap-2">
          {failed ? (
            <span className="rounded-full bg-rose-100 px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] text-rose-800">
              Needs review
            </span>
          ) : null}
          {isBestEffort ? (
            <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] text-amber-900">
              Best effort
            </span>
          ) : null}
        </div>
      </header>

      {failures.length > 0 ? (
        <div className="flex gap-3 rounded-3xl border border-rose-200 bg-rose-50 px-5 py-4 text-sm leading-6 text-rose-700">
          <span className="mt-0.5 flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-white/80 text-rose-700">
            <PreviewIcon
              iconKey={PREVIEW_CALLOUT_ICON_KEYS.warning}
              className="h-5 w-5"
            />
          </span>
          <div className="space-y-2">
            {failures.map((failure) => (
              <p key={failure}>{failure}</p>
            ))}
          </div>
        </div>
      ) : null}

      {renderSectionBody(section)}
    </article>
  );
}
