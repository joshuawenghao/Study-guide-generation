from __future__ import annotations

from typing import Any

from app.types import Blueprint, GenerateRequest


def _build_quote_bank(spec: dict[str, Any]) -> list[str]:
    passage_lines = [
        str(item).strip() for item in spec.get("passage", []) if str(item).strip()
    ]
    passage_text = "\n".join(passage_lines)

    quote_bank: list[str] = []
    for clue in spec.get("evidence_clues", []):
        normalized_clue = str(clue).strip().strip('"')
        if (
            normalized_clue
            and normalized_clue in passage_text
            and normalized_clue not in quote_bank
        ):
            quote_bank.append(normalized_clue)

    for paragraph in passage_lines:
        if paragraph not in quote_bank:
            quote_bank.append(paragraph)

    return quote_bank[:8]


def build_prompt(
    spec: dict[str, Any], blueprint: Blueprint, request: GenerateRequest
) -> str:
    passage_title = spec.get("title", "Assessment Passage")
    passage_text = "\n".join(spec.get("passage", []))
    evidence_clues = "\n".join(f"- {item}" for item in spec.get("evidence_clues", []))
    quote_bank = _build_quote_bank(spec)
    quote_bank_text = "\n".join(f'- "{item}"' for item in quote_bank)

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
        "- Exact quote bank for evidence requirements:",
        quote_bank_text or "- none provided",
        "Requirements:",
        "- Write 4 assessment questions that require evidence from the provided passage.",
        "- Make the questions answerable from the passage alone, not outside knowledge.",
        "- Do not introduce a new scenario, patient, procedure, or fact that is not explicitly present in the provided passage.",
        "- Use answer_expectation as guidance only: describe what a strong student answer should do, but do not provide the final answer.",
        "- Use evidence_requirement as guidance only: tell the student what kind of passage detail to quote or where to look, but do not reveal the exact quoted phrase itself.",
        "- Keep both guidance fields grounded in the provided passage. Do not mention details that are absent from the passage.",
        "- Keep the set suitable for downstream step-up and answer-key generation.",
        f"- Keep the reading demand close to Grade {request.lesson_metadata.grade_level}.",
        "Expected JSON schema:",
        assessment_questions_schema,
        "Return only JSON.",
    ]

    return "\n".join(prompt_lines)
