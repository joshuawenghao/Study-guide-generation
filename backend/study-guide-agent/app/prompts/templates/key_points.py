from __future__ import annotations

from app.types import Blueprint, GenerateRequest


def build_prompt(spec, blueprint: Blueprint, request: GenerateRequest) -> str:
    del spec, request

    key_points_schema = """{
    "title": "Key Points",
    "points": [
        {
            "number": 1,
            "sub_competency_id": "string",
            "sub_competency_label": "string",
            "statement": "string"
        }
    ]
}"""

    sub_competency_text = "\n".join(
        f"- {item.id}: {item.label}" for item in blueprint.sub_competencies
    )

    prompt_lines = [
        "Create the key points section for a K-12 study guide.",
        f"- Lesson title: {blueprint.title}",
        f"- Essential question: {blueprint.essential_question}",
        f"- Core concept: {blueprint.core_concept}",
        "- Sub-competencies:",
        sub_competency_text,
        "Requirements:",
        "- Write one numbered summary statement per sub-competency.",
        "- Keep statements concise, clear, and directly aligned to the listed sub-competencies.",
        "- Use the same order as the blueprint sub-competencies.",
        "- Make each statement suitable for quick review at the end of the lesson.",
        "Expected JSON schema:",
        key_points_schema,
        "Return only JSON.",
    ]

    return "\n".join(prompt_lines)
