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

function toSectionKey(sectionId: string): string {
  return sectionId.replace(/-\d+$/, "");
}

function formatLabel(value: string): string {
  return value.replace(/_/g, " ");
}

function renderParagraphs(paragraphs: string[]): JSX.Element | null {
  if (paragraphs.length === 0) {
    return null;
  }

  return (
    <div className="space-y-4 text-sm leading-7 text-slate-700 sm:text-base">
      {paragraphs.map((paragraph) => (
        <p key={paragraph}>{paragraph}</p>
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
          className="rounded-2xl border border-slate-200 bg-white px-4 py-3"
        >
          {item}
        </li>
      ))}
    </ul>
  );
}

function renderKeyValueGrid(record: ContentRecord): JSX.Element {
  const entries = Object.entries(record).filter(([, value]) => {
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

  return (
    <dl className="grid gap-4 sm:grid-cols-2">
      {entries.map(([key, value]) => (
        <div
          key={key}
          className="rounded-2xl border border-slate-200 bg-white px-4 py-4"
        >
          <dt className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
            {formatLabel(key)}
          </dt>
          <dd className="mt-2 text-sm leading-6 text-slate-700">
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

  return (
    <div className="space-y-5">
      {competencyFocus ? (
        <div className="grid gap-4 sm:grid-cols-2">
          {renderKeyValueGrid(competencyFocus)}
        </div>
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
  const metadata = {
    topic_domain: getString(section.content, "topic_domain"),
    genre: getString(section.content, "genre"),
    evidence_focus:
      getString(section.content, "evidence_focus") ??
      getString(section.content, "answerability_note"),
  };
  const chips = [
    ...getStringArray(section.content, "text_features"),
    ...getStringArray(section.content, "evidence_clues"),
  ];

  return (
    <div className="space-y-5">
      <div className="grid gap-4 sm:grid-cols-3">
        {Object.entries(metadata)
          .filter(([, value]) => typeof value === "string" && value.length > 0)
          .map(([key, value]) => (
            <div
              key={key}
              className="rounded-2xl border border-slate-200 bg-white px-4 py-4"
            >
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                {formatLabel(key)}
              </p>
              <p className="mt-2 text-sm leading-6 text-slate-700">{value}</p>
            </div>
          ))}
      </div>
      <div className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-sm">
        {renderParagraphs(passage)}
      </div>
      {chips.length > 0 ? (
        <div className="flex flex-wrap gap-2">
          {chips.map((chip) => (
            <span
              key={chip}
              className="rounded-full bg-slate-200 px-3 py-1 text-xs font-semibold uppercase tracking-[0.14em] text-slate-700"
            >
              {chip}
            </span>
          ))}
        </div>
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
                <p className="mt-3 text-sm leading-6 text-slate-700">
                  {possibleAnswer}
                </p>
              ) : null}
              {evidenceQuote ? (
                <p className="mt-4 rounded-2xl bg-slate-50 px-4 py-3 text-sm italic leading-6 text-slate-600">
                  {evidenceQuote}
                </p>
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
                <div className="mt-4 flex flex-wrap gap-2">
                  {requiredEvidence.map((item) => (
                    <span
                      key={item}
                      className="rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] text-amber-900"
                    >
                      {item}
                    </span>
                  ))}
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
    case "learning_targets":
      return renderLearningTargets(section);
    case "vocabulary":
      return renderVocabulary(section);
    case "model_passage":
    case "assessment_passage":
      return renderPassage(section);
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
    <article className="space-y-5 rounded-[2rem] border border-slate-200 bg-surface-strong p-6 shadow-sm sm:p-8">
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
