from __future__ import annotations

from app.types import Blueprint, GenerateRequest


def build_prompt(spec, blueprint: Blueprint, request: GenerateRequest) -> str:
    del spec, request

    learning_targets_schema = """{
    "title": "Learning Targets",
    "competency_focus": {
        "lesson_id": "string",
        "core_concept": "string"
    },
    "targets": [
        {
            "number": 1,
            "bloom_verb": "string",
            "objective": "string",
            "success_look_for": "string"
        }
    ]
}"""

    target_text = "\n".join(
        f"- {target.number}. {target.bloom_verb}: {target.objective}"
        for target in blueprint.learning_targets
    )

    prompt_lines = [
        "Create the learning targets section for a K-12 study guide.",
        "Use the blueprint learning targets directly and keep them student-facing.",
        f"- Lesson title: {blueprint.title}",
        f"- Lesson id: {blueprint.lesson_id}",
        f"- Core concept: {blueprint.core_concept}",
        "- Blueprint learning targets:",
        target_text,
        "Requirements:",
        "- Preserve the same number and order as the blueprint learning targets.",
        "- Keep each objective aligned to the blueprint wording and clearly usable as an 'I can' statement.",
        "- Add a short success_look_for that describes what evidence of learning would look like.",
        "- Keep the section focused on competency and student-facing goals only.",
        "Expected JSON schema:",
        learning_targets_schema,
        "Return only JSON.",
    ]

    return "\n".join(prompt_lines)
