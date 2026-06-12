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
            dimension: "Inform",
            topic_domain: "science guide",
            explanation:
              "This example teaches the reader using factual language.",
            key_terms: ["for example", "according to", "in addition"],
          },
        ],
      },
    };

    const markup = renderToStaticMarkup(
      createElement(PreviewSection, { section, validation }),
    );

    expect(markup).toContain("Key terms");
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
            expected_response_type: "short_response",
            evidence_hint:
              "Look for the line that explains why mangroves matter.",
          },
        ],
      },
    };

    const markup = renderToStaticMarkup(
      createElement(PreviewSection, { section, validation }),
    );

    expect(markup).toContain("Passage title");
    expect(markup).toContain("Response type:");
    expect(markup).toContain("Evidence hint:");
    expect(markup).not.toContain("{&quot;number&quot;");
    expect(markup).not.toContain("answer_expectation");
  });

  it("renders passage support details as labeled sections with evidence focus after text features", () => {
    const section: PreviewSectionData = {
      section_id: "assessment_passage",
      section_type: "assessment_passage",
      title: "Assessment Passage",
      icon_key: "book-open",
      content: {
        topic_domain: "Wetland conservation",
        genre: "informational article",
        passage: ["Mangroves reduce erosion and protect coastlines."],
        text_features: ["Cause-and-effect headings", "Captioned diagram"],
        evidence_focus: "Use the evidence to explain why mangroves matter.",
        evidence_clues: [
          "Look for phrases about coastline protection.",
          "Use the diagram caption as support.",
        ],
      },
    };

    const markup = renderToStaticMarkup(
      createElement(PreviewSection, { section, validation }),
    );

    expect(markup).toContain("Text features");
    expect(markup).toContain("Evidence focus");
    expect(markup).toContain("Evidence clues");
    expect(markup.indexOf("Text features")).toBeLessThan(
      markup.indexOf("Evidence focus"),
    );
    expect(markup).not.toContain("sm:grid-cols-3");
  });

  it("renders check-in response type below the question as a labeled detail", () => {
    const section: PreviewSectionData = {
      section_id: "check_in",
      section_type: "check_in",
      title: "Check In",
      icon_key: "chat-circle",
      content: {
        passage_title: "Model Passage",
        questions: [
          {
            number: 1,
            question: "Which sentence best shows the writer's purpose?",
            expected_response_type: "One-sentence explanation",
            evidence_hint: "Look at the final paragraph.",
          },
        ],
      },
    };

    const markup = renderToStaticMarkup(
      createElement(PreviewSection, { section, validation }),
    );

    expect(markup).toContain("Response type:");
    expect(
      markup.indexOf("Which sentence best shows the writer&#x27;s purpose?"),
    ).toBeLessThan(markup.indexOf("Response type:"));
    expect(markup).toContain("Evidence hint:");
  });

  it("keeps each assessment evidence hint with its corresponding question", () => {
    const section: PreviewSectionData = {
      section_id: "assessment_questions",
      section_type: "assessment_questions",
      title: "Assessment Questions",
      icon_key: "pencil",
      content: {
        questions: [
          {
            number: 1,
            question: "What is the author's purpose?",
            expected_response_type: "short_response",
            evidence_hint: "Look for one line about coastal protection.",
          },
          {
            number: 2,
            question: "How does the diagram support the article?",
            expected_response_type: "short_response",
            evidence_hint: "Refer to one diagram label.",
          },
        ],
      },
    };

    const markup = renderToStaticMarkup(
      createElement(PreviewSection, { section, validation }),
    );

    expect(
      markup.indexOf("Look for one line about coastal protection."),
    ).toBeLessThan(markup.indexOf("How does the diagram support the article?"));
    expect(markup).toContain("Evidence hint:");
  });

  it("labels answer key answer content and step-up evidence clearly", () => {
    const section: PreviewSectionData = {
      section_id: "answer_key",
      section_type: "answer_key",
      title: "Answer Key",
      icon_key: "check-square",
      content: {
        assessment_answers: [
          {
            question_number: 1,
            question: "What is the author's purpose?",
            possible_answer: "The author informs readers about mangroves.",
            evidence_quote: "Mangroves protect shorelines from erosion.",
          },
        ],
        step_up_answer: {
          challenge_response:
            "A strong response explains the passage purpose and cites the diagram.",
          required_evidence: [
            "A quoted sentence from the passage",
            "A reference to the diagram caption",
          ],
        },
      },
    };

    const markup = renderToStaticMarkup(
      createElement(PreviewSection, { section, validation }),
    );

    expect(markup).toContain("Possible answer");
    expect(markup).toContain("Evidence quote");
    expect(markup).toContain("Required evidence");
  });
});
