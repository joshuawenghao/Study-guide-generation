from __future__ import annotations

from app.types import Blueprint, GenerateRequest


def build_prompt(spec, blueprint: Blueprint, request: GenerateRequest) -> str:
    del spec, request

    self_assessment_schema = """{
    "title": "Self-Assessment",
    "confidence_levels": [
        "Not yet",
        "Getting there",
        "Confident"
    ],
    "rows": [
        {
            "skill": "string",
            "reflection_prompt": "string"
        }
    ]
}"""

    target_text = "\n".join(
        f"- {target.objective}" for target in blueprint.learning_targets
    )

    prompt_lines = [
        "Create the self-assessment section for a K-12 study guide.",
        f"- Lesson title: {blueprint.title}",
        f"- Essential question: {blueprint.essential_question}",
        "- Learning target objectives that must be used verbatim as skill values:",
        target_text,
        "Requirements:",
        "- Create one row per blueprint learning target, in the same order.",
        "- Each rows.skill value must match the corresponding learning target objective verbatim.",
        "- Use exactly these confidence levels: Not yet, Getting there, Confident.",
        "- Add a brief reflection_prompt that helps a learner judge their own evidence of success.",
        "- Do not rewrite, shorten, or paraphrase the skill text.",
        "Expected JSON schema:",
        self_assessment_schema,
        "Return only JSON.",
    ]

    return "\n".join(prompt_lines)
