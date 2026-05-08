from __future__ import annotations

from app.types import Blueprint, GenerateRequest


def build_prompt(spec, blueprint: Blueprint, request: GenerateRequest) -> str:
    del spec, request

    intro_schema = """{
    "title": "Introduction",
    "hook": "string",
    "essential_question": "string",
    "paragraphs": [
        "string"
    ],
    "bridge_to_lesson": "string"
}"""

    learning_target_text = "\n".join(
        f"- {target.number}. {target.objective}"
        for target in blueprint.learning_targets
    )

    prompt_lines = [
        "Create the introduction section for a K-12 study guide.",
        "Use the blueprint as the single source of truth.",
        f"- Lesson title: {blueprint.title}",
        f"- Essential question: {blueprint.essential_question}",
        f"- Introduction hook: {blueprint.introduction_hook}",
        f"- Core concept: {blueprint.core_concept}",
        "- Learning targets:",
        learning_target_text,
        "Requirements:",
        "- Write a warm, student-facing opening linked directly to the essential question.",
        "- Use the hook as the first attention-grabbing idea, but rewrite it as polished study-guide prose.",
        "- Provide exactly 2 short paragraphs that prepare students for the lesson.",
        "- Make the bridge_to_lesson explain how the opening connects to the study guide work ahead.",
        "Expected JSON schema:",
        intro_schema,
        "Return only JSON.",
    ]

    return "\n".join(prompt_lines)
