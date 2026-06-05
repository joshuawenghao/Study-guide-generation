import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import PreviewSection from "@/components/PreviewSection";
import type {
  PreviewSection as PreviewSectionData,
  ValidationResult,
} from "@/lib/types";

const validation: ValidationResult = {
  passed: true,
  failed_sections: [],
  failures: {},
  warnings: [],
  best_effort_sections: [],
};

describe("PreviewSection", () => {
  it("renders subconcept quick check content without raw JSON formatting", () => {
    const section: PreviewSectionData = {
      section_id: "subconcept-1",
      section_type: "subconcept",
      title: "Subconcept One",
      icon_key: "layers",
      content: {
        sub_competency_label: "Purpose clues",
        explanation: "Read the question and identify the clue.",
        worked_example: "A poster uses commands to persuade.",
        quick_check: {
          question: "What clue shows persuasion?",
          expected_answer: "The command tells the reader what to do.",
        },
      },
    };

    const markup = renderToStaticMarkup(
      createElement(PreviewSection, { section, validation }),
    );

    expect(markup).toContain("Quick check");
    expect(markup).toContain("Expected answer:");
    expect(markup).toContain("The command tells the reader what to do.");
    expect(markup).not.toContain("expected_answer");
    expect(markup).not.toContain("{&quot;question&quot;");
  });

  it("renders deep-dive signal words as wrapped chips instead of compact JSON", () => {
    const section: PreviewSectionData = {
      section_id: "deep_dive",
      section_type: "deep_dive",
      title: "Deep Dive",
      icon_key: "search",
      content: {
        compare_focus: "Compare how each text communicates purpose.",
        takeaway: "Purpose changes language choices.",
        examples: [
          {
            mode: "Inform",
            topic_domain: "science guide",
            explanation:
              "This example teaches the reader using factual language.",
            signal_words: ["for example", "according to", "in addition"],
          },
        ],
      },
    };

    const markup = renderToStaticMarkup(
      createElement(PreviewSection, { section, validation }),
    );

    expect(markup).toContain("Signal words");
    expect(markup).toContain("for example");
    expect(markup).toContain("according to");
    expect(markup).not.toContain(
      "[&quot;for example&quot;,&quot;according to&quot;",
    );
  });

  it("renders learning target competency focus as full-width stacked content", () => {
    const section: PreviewSectionData = {
      section_id: "learning_targets",
      section_type: "learning_targets",
      title: "Learning Targets",
      icon_key: "compass",
      content: {
        competency_focus: {
          lesson_id: "HN12-U3-L2",
          core_concept:
            "Standard precautions protect patients and healthcare workers by treating blood and body fluids as potentially infectious.",
        },
        targets: [
          {
            number: 1,
            bloom_verb: "identify",
            objective: "Identify situations that require standard precautions.",
            success_look_for: "I can name when the precautions apply.",
          },
        ],
      },
    };

    const markup = renderToStaticMarkup(
      createElement(PreviewSection, { section, validation }),
    );

    expect(markup).toContain("Competency focus");
    expect(markup).toContain("Lesson ID");
    expect(markup).toContain("Core concept");
    expect(markup).not.toContain("sm:grid-cols-2");
  });

  it("renders strategy list content without raw JSON formatting", () => {
    const section: PreviewSectionData = {
      section_id: "strategy_list",
      section_type: "strategy_list",
      title: "Strategy List",
      icon_key: "checklist",
      content: {
        strategies: [
          {
            name: "Spot the clue",
            when_to_use:
              "Use this when you need to identify purpose from signal words and details.",
            steps: [
              "Read the title and opening carefully.",
              "Highlight words that show what the writer wants the reader to think or do.",
            ],
          },
        ],
      },
    };

    const markup = renderToStaticMarkup(
      createElement(PreviewSection, { section, validation }),
    );

    expect(markup).toContain("Spot the clue");
    expect(markup).toContain("When to use:");
    expect(markup).toContain(
      "Highlight words that show what the writer wants the reader to think or do.",
    );
    expect(markup).not.toContain("{&quot;name&quot;");
    expect(markup).not.toContain("[&quot;Read the title");
  });

  it("renders assessment questions without nested JSON stringify output", () => {
    const section: PreviewSectionData = {
      section_id: "assessment_questions",
      section_type: "assessment_questions",
      title: "Assessment Questions",
      icon_key: "pencil",
      content: {
        passage_title: "Assessment Passage",
        questions: [
          {
            number: 1,
            question: "What is the author's purpose in this article?",
            question_type: "short_response",
            answer_expectation: "Explain the purpose using evidence.",
            evidence_requirement:
              "Quote a phrase that explains why mangroves matter.",
          },
        ],
      },
    };

    const markup = renderToStaticMarkup(
      createElement(PreviewSection, { section, validation }),
    );

    expect(markup).toContain("Passage title");
    expect(markup).toContain("Evidence requirement:");
    expect(markup).toContain("Answer expectation");
    expect(markup).not.toContain("{&quot;number&quot;");
    expect(markup).not.toContain("question_type");
  });
});
