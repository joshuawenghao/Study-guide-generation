from __future__ import annotations

from app.types import Blueprint, GenerateRequest


def build_prompt(spec, blueprint: Blueprint, request: GenerateRequest) -> str:
    del spec

    strategy_list_schema = """{
    "title": "Strategy List",
    "strategies": [
        {
            "name": "string",
            "when_to_use": "string",
            "steps": [
                "string"
            ]
        }
    ]
}"""

    prompt_lines = [
        "Create the strategy list section for a K-12 study guide.",
        f"- Lesson title: {blueprint.title}",
        f"- Essential question: {blueprint.essential_question}",
        f"- Core concept: {blueprint.core_concept}",
        "Requirements:",
        "- Provide 3 practical reading or thinking strategies that help students succeed with this lesson.",
        "- Each strategy must include when_to_use and a short ordered steps list.",
        "- Keep the strategies directly tied to the lesson's core concept and purpose-identification work.",
        f"- Keep the reading level close to Grade {request.lesson_metadata.grade_level}.",
        "Expected JSON schema:",
        strategy_list_schema,
        "Return only JSON.",
    ]

    return "\n".join(prompt_lines)
