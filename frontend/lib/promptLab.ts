import {
  PROMPT_LAB_SECTION_KEYS,
  type GenerateRequest,
  type GenerationStage,
  type ProgressEvent,
  type PromptLabGenerateRequest,
  type PromptLabSampleCaseId,
  type PromptLabSectionKey,
} from "@/lib/types";

export function parseEventStage(event: ProgressEvent): GenerationStage | null {
  if (event.type === "error") {
    return "error";
  }
  if (event.type === "done") {
    return "done";
  }
  if (event.type === "render_started") {
    return "rendering";
  }
  if (event.type === "validation_started" || event.type === "retry_started") {
    return "validating";
  }
  if (event.type === "node_started" || event.type === "node_complete") {
    return "generating";
  }

  return null;
}

export function parseSseBlock(
  block: string,
): { eventName: string; data: string } | null {
  const lines = block
    .split(/\r?\n/)
    .map((line) => line.trimEnd())
    .filter(Boolean);

  if (lines.length === 0) {
    return null;
  }

  let eventName = "message";
  const dataLines: string[] = [];

  for (const line of lines) {
    if (line.startsWith("event:")) {
      eventName = line.slice("event:".length).trim();
      continue;
    }

    if (line.startsWith("data:")) {
      dataLines.push(line.slice("data:".length).trim());
    }
  }

  if (dataLines.length === 0) {
    return null;
  }

  return {
    eventName,
    data: dataLines.join("\n"),
  };
}

export function buildPdfFilename(
  request: GenerateRequest | null,
  sampleId: string,
): string {
  if (!request) {
    return sampleId
      ? `${sampleId}-prompt-lab-study-guide.pdf`
      : "prompt-lab-study-guide.pdf";
  }

  const lessonTitle = request.lesson_metadata.lesson_title.trim();
  const subject = request.lesson_metadata.subject.trim();
  const gradeLevel = request.lesson_metadata.grade_level;

  return `${subject}-grade-${gradeLevel}-${lessonTitle}-prompt-lab-study-guide.pdf`;
}

export function createEmptySectionOverrides(): Record<
  PromptLabSectionKey,
  string
> {
  return Object.fromEntries(
    PROMPT_LAB_SECTION_KEYS.map((section) => [section, ""]),
  ) as Record<PromptLabSectionKey, string>;
}

export function buildPromptLabRequestPayload(options: {
  baseRequest: GenerateRequest;
  sectionOverrides: Record<PromptLabSectionKey, string>;
  selectedSampleId: string;
  systemPromptAppend: string;
}): PromptLabGenerateRequest {
  const {
    baseRequest,
    sectionOverrides,
    selectedSampleId,
    systemPromptAppend,
  } = options;

  const cleanedSectionOverrides = Object.fromEntries(
    Object.entries(sectionOverrides)
      .map(([section, instruction]) => [section, instruction.trim()])
      .filter(([, instruction]) => instruction.length > 0),
  ) as Partial<Record<PromptLabSectionKey, string>>;

  const payload: PromptLabGenerateRequest = {
    base_request: baseRequest,
    prompt_overrides: {
      section_overrides: cleanedSectionOverrides,
    },
    sample_case_id:
      selectedSampleId.length > 0
        ? (selectedSampleId as PromptLabSampleCaseId)
        : undefined,
    reviewer_label: "prompt-lab-reviewer",
  };

  const cleanedSystemPromptAppend = systemPromptAppend.trim();
  if (cleanedSystemPromptAppend.length > 0) {
    payload.prompt_overrides.system_prompt_append = cleanedSystemPromptAppend;
  }

  return payload;
}
