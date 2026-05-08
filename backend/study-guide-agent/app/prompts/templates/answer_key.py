from __future__ import annotations

from typing import Any

from app.types import Blueprint, GenerateRequest


def build_prompt(
    spec: dict[str, Any], blueprint: Blueprint, request: GenerateRequest
) -> str:
    del request

    check_in = spec.get("check_in", {})
    assessment_passage = spec.get("assessment_passage", {})
    assessment_questions = spec.get("assessment_questions", {})

    check_in_questions = "\n".join(
        f"- Q{item.get('number', '?')}: {item.get('question', '')}"
        for item in check_in.get("questions", [])
    )
    assessment_passage_text = "\n".join(assessment_passage.get("passage", []))
    assessment_questions_text = "\n".join(
        f"- Q{item.get('number', '?')}: {item.get('question', '')}"
        for item in assessment_questions.get("questions", [])
    )

    answer_key_schema = """{
    "title": "Answer Key",
    "check_in_answers": [
        {
            "question_number": 1,
            "question": "string",
            "possible_answer": "string",
            "evidence_quote": "string"
        }
    ],
    "assessment_answers": [
        {
            "question_number": 1,
            "question": "string",
            "possible_answer": "string",
            "evidence_quote": "string"
        }
    ],
    "teacher_note": "string"
}"""

    prompt_lines = [
        "Create the answer key section for a K-12 study guide.",
        f"- Lesson title: {blueprint.title}",
        f"- Essential question: {blueprint.essential_question}",
        "- Check-in questions:",
        check_in_questions or "- none provided",
        "- Assessment passage text:",
        assessment_passage_text,
        "- Assessment questions:",
        assessment_questions_text or "- none provided",
        "Requirements:",
        "- Provide one answer-key entry per check-in question and per assessment question.",
        "- Every possible_answer for assessment questions must contain at least one verbatim quoted phrase from the assessment passage.",
        "- Include an evidence_quote field that repeats the exact quoted phrase used from the assessment passage.",
        "- Keep answers concise, student-appropriate, and structurally ready for downstream quote validation.",
        "Expected JSON schema:",
        answer_key_schema,
        "Return only JSON.",
    ]

    return "\n".join(prompt_lines)
