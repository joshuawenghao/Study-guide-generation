from __future__ import annotations

from app.types import Blueprint, GenerateRequest


def _deep_dive_length_guidance(request: GenerateRequest) -> str:
    grade_level = request.lesson_metadata.grade_level

    if grade_level <= 5:
        return (
            "Keep compare_focus and takeaway to one short sentence each, and keep every "
            "example explanation to one short sentence followed by simple signal words."
        )
    return (
        "Keep compare_focus brief, write each explanation in 1 or 2 short sentences, "
        "and keep the takeaway to one short summary sentence."
    )


def build_prompt(spec, blueprint: Blueprint, request: GenerateRequest) -> str:
    del spec

    deep_dive_schema = """{
    "title": "Deep Dive",
    "compare_focus": "string",
    "examples": [
        {
            "mode": "string",
            "topic_domain": "string",
            "explanation": "string",
            "signal_words": [
                "string"
            ]
        }
    ],
    "takeaway": "string"
}"""

    prompt_lines = [
        "Create the deep dive section for a K-12 study guide.",
        f"- Lesson title: {blueprint.title}",
        f"- Core concept: {blueprint.core_concept}",
        "- Topic domains for rhetorical examples:",
        f"  - entertain_example: {blueprint.topic_domains.entertain_example}",
        f"  - inform_example: {blueprint.topic_domains.inform_example}",
        f"  - persuade_example: {blueprint.topic_domains.persuade_example}",
        "Requirements:",
        "- Compare how entertain, inform, and persuade differ in purpose.",
        "- Use the blueprint example domains directly so the examples stay distinct.",
        "- Include signal_words lists that help students notice clues in texts.",
        f"- Keep the reading level close to Grade {request.lesson_metadata.grade_level}.",
        f"- {_deep_dive_length_guidance(request)}",
        "- Use plain language to contrast the three purposes.",
        "Expected JSON schema:",
        deep_dive_schema,
        "Return only JSON.",
    ]

    return "\n".join(prompt_lines)
