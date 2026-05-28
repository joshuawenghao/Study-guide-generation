import { describe, expect, it } from "vitest";

import {
  buildPromptLabRequestPayload,
  createEmptySectionOverrides,
  parseEventStage,
  parseSseBlock,
} from "@/lib/promptLab";
import type { GenerateRequest, ProgressEvent } from "@/lib/types";

function buildRequest(): GenerateRequest {
  return {
    lesson_metadata: {
      subject: "English",
      grade_level: 6,
      market: "PH",
      language: "en",
      unit_number: 1,
      unit_title: "Reading",
      lesson_number: 1,
      lesson_title: "Author Purpose",
      lesson_code: "EN6-AUTHOR-PURPOSE",
    },
    curriculum: {
      competency_code: "EN6RC-Ia-2.2",
      competency_description: "Identify the author's purpose.",
      sub_competencies: [{ id: "sc1", label: "Identify purpose" }],
    },
    instructional_design: {
      core_concept: "Authors write for a purpose.",
      bloom_targets: ["Remember", "Understand", "Apply"],
      essential_question_seed: "Why does purpose matter?",
    },
    optional: {
      vocabulary_seeds: [],
      topic_domains: {},
      tone_register: "supportive",
      length_preset: "standard",
    },
  };
}

describe("prompt lab utilities", () => {
  it("creates empty section override values for every supported section", () => {
    const overrides = createEmptySectionOverrides();

    expect(Object.keys(overrides).length).toBe(16);
    expect(overrides.intro).toBe("");
    expect(overrides.answer_key).toBe("");
  });

  it("builds payload with trimmed override values and optional fields", () => {
    const payload = buildPromptLabRequestPayload({
      baseRequest: buildRequest(),
      sectionOverrides: {
        ...createEmptySectionOverrides(),
        intro: "  Add one sentence hook.  ",
        model_passage: "   ",
      },
      selectedSampleId: "english_grade6_ph",
      systemPromptAppend: "  Prefer concise language. ",
    });

    expect(payload.sample_case_id).toBe("english_grade6_ph");
    expect(payload.reviewer_label).toBe("prompt-lab-reviewer");
    expect(payload.prompt_overrides.system_prompt_append).toBe(
      "Prefer concise language.",
    );
    expect(payload.prompt_overrides.section_overrides).toEqual({
      intro: "Add one sentence hook.",
    });
  });

  it("omits empty sample id and empty system append", () => {
    const payload = buildPromptLabRequestPayload({
      baseRequest: buildRequest(),
      sectionOverrides: createEmptySectionOverrides(),
      selectedSampleId: "",
      systemPromptAppend: "  ",
    });

    expect(payload.sample_case_id).toBeUndefined();
    expect(payload.prompt_overrides.system_prompt_append).toBeUndefined();
    expect(payload.prompt_overrides.section_overrides).toEqual({});
  });

  it("maps stream event types to generation stages", () => {
    const event: ProgressEvent = {
      type: "validation_started",
      node: "validator",
      message: undefined,
      timestamp: new Date().toISOString(),
    };

    expect(parseEventStage(event)).toBe("validating");
    expect(
      parseEventStage({
        ...event,
        type: "render_started",
      }),
    ).toBe("rendering");
    expect(
      parseEventStage({
        ...event,
        type: "done",
      }),
    ).toBe("done");
  });

  it("parses SSE blocks with event and data lines", () => {
    const parsed = parseSseBlock(
      'event: progress\ndata: {"type":"node_started"}\n\n',
    );

    expect(parsed).toEqual({
      eventName: "progress",
      data: '{"type":"node_started"}',
    });
  });
});
