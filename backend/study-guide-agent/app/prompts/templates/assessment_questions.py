from __future__ import annotations

from typing import Any

from app.types import Blueprint, GenerateRequest


def build_prompt(
    spec: dict[str, Any], blueprint: Blueprint, request: GenerateRequest
) -> str:
    passage_title = spec.get("title", "Assessment Passage")
    passage_text = "\n".join(spec.get("passage", []))
    evidence_clues = "\n".join(f"- {item}" for item in spec.get("evidence_clues", []))

    assessment_questions_schema = """{
    "title": "Assessment Questions",
    "passage_title": "string",
    "questions": [
        {
            "number": 1,
            "question": "string",
            "question_type": "string",
            "answer_expectation": "string",
            "evidence_requirement": "string"
        }
    ]
}"""

    prompt_lines = [
        "Create the assessment questions section for a K-12 study guide.",
        f"- Lesson title: {blueprint.title}",
        f"- Essential question: {blueprint.essential_question}",
        f"- Source passage title: {passage_title}",
        "- Source passage text:",
        passage_text,
        "- Evidence clues provided with the passage:",
        evidence_clues or "- none provided",
        "Requirements:",
        "- Write 4 assessment questions that require evidence from the provided passage.",
        "- Make the questions answerable from the passage alone, not outside knowledge.",
        "- Use evidence_requirement to state what kind of quotation or clue the student should cite.",
        "- Keep the set suitable for downstream step-up and answer-key generation.",
        f"- Keep the reading demand close to Grade {request.lesson_metadata.grade_level}.",
        "Expected JSON schema:",
        assessment_questions_schema,
        "Return only JSON.",
    ]

    return "\n".join(prompt_lines)
