from __future__ import annotations

from app.types import Blueprint, GenerateRequest


def build_prompt(spec, blueprint: Blueprint, request: GenerateRequest) -> str:
    del spec, request

    warmup_schema = """{
    "title": "Warm-Up",
    "activity_type": "string",
    "purpose": "string",
    "student_instructions": [
        "string"
    ],
    "teacher_tip": "string",
    "estimated_minutes": 5
}"""

    prompt_lines = [
        "Create the warm-up section for a K-12 study guide.",
        f"- Lesson title: {blueprint.title}",
        f"- Essential question: {blueprint.essential_question}",
        f"- Introduction hook: {blueprint.introduction_hook}",
        f"- Core concept: {blueprint.core_concept}",
        "Requirements:",
        "- Design one short activation activity that can be completed in about 5 minutes.",
        "- Use the hook and essential question to activate prior knowledge.",
        "- Include a clear purpose statement explaining why the warm-up matters for the lesson.",
        "- Provide student_instructions as a short ordered sequence the learner can follow.",
        "- Keep the activity lightweight, classroom-ready, and aligned to the lesson focus.",
        "Expected JSON schema:",
        warmup_schema,
        "Return only JSON.",
    ]

    return "\n".join(prompt_lines)
