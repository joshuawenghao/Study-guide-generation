from __future__ import annotations

from typing import Any

from app.types import Blueprint, GenerateRequest


def build_prompt(
    spec: dict[str, Any], blueprint: Blueprint, request: GenerateRequest
) -> str:
    passage_title = spec.get("title", "Model Passage")
    passage_text = "\n".join(spec.get("passage", []))
    evidence_focus = spec.get("evidence_focus", "")
    text_features = "\n".join(f"- {item}" for item in spec.get("text_features", []))

    check_in_schema = """{
    "title": "Check-In",
    "passage_title": "string",
    "questions": [
        {
            "number": 1,
            "question": "string",
            "evidence_hint": "string",
            "expected_response_type": "string"
        }
    ]
}"""

    prompt_lines = [
        "Create the check-in section for a K-12 study guide.",
        f"- Lesson title: {blueprint.title}",
        f"- Essential question: {blueprint.essential_question}",
        f"- Source passage title: {passage_title}",
        f"- Evidence focus: {evidence_focus}",
        "- Source passage text:",
        passage_text,
        "- Source text features:",
        text_features or "- none provided",
        "Requirements:",
        "- Write 3 short questions that require evidence from the provided passage text.",
        "- Make each evidence_hint point students toward a specific clue or phrase in the passage.",
        "- Keep the questions aligned to the lesson's core concept and author-purpose analysis.",
        f"- Keep the reading demand close to Grade {request.lesson_metadata.grade_level}.",
        "Expected JSON schema:",
        check_in_schema,
        "Return only JSON.",
    ]

    return "\n".join(prompt_lines)
