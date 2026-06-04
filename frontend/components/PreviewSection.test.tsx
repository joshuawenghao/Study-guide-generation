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
});
