from __future__ import annotations

from app.types import Blueprint, GenerateRequest


def build_prompt(spec, blueprint: Blueprint, request: GenerateRequest) -> str:
    del spec, request

    core_explainer_schema = """{
    "title": "Core Explainer",
    "overview": "string",
    "explained_points": [
        {
            "sub_competency_id": "string",
            "sub_competency_label": "string",
            "explanation": "string",
            "real_world_connection": "string"
        }
    ],
    "closing_summary": "string"
}"""

    sub_competency_text = "\n".join(
        f"- {item.id}: {item.label}" for item in blueprint.sub_competencies
    )

    prompt_lines = [
        "Create the core explainer section for a K-12 study guide.",
        f"- Lesson title: {blueprint.title}",
        f"- Essential question: {blueprint.essential_question}",
        f"- Core concept: {blueprint.core_concept}",
        "- Sub-competencies to cover:",
        sub_competency_text,
        "Requirements:",
        "- Write a clear overview that explains the lesson's core concept in student-friendly language.",
        "- Include one explained point per sub-competency in the same order as the blueprint.",
        "- Connect each explanation to a concrete real-world or classroom-relevant example.",
        "- Keep the section explanatory rather than quiz-like.",
        "Expected JSON schema:",
        core_explainer_schema,
        "Return only JSON.",
    ]

    return "\n".join(prompt_lines)
