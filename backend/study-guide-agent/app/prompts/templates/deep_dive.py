from __future__ import annotations

from app.types import Blueprint, GenerateRequest


def _deep_dive_length_guidance(request: GenerateRequest) -> str:
    grade_level = request.lesson_metadata.grade_level

    if grade_level <= 5:
        return (
            "Keep compare_focus and takeaway to one short sentence each, and keep every "
            "example explanation to one short sentence followed by a brief key_terms list."
        )
    return (
        "Keep compare_focus brief, write each explanation in 1 or 2 short sentences, "
        "and keep the takeaway to one short summary sentence."
    )


def _build_schema(dimensions: list[str]) -> str:
    example_items = []
    for d in dimensions:
        example_items.append(
            "        {\n"
            f'            "dimension": "{d}",\n'
            '            "topic_domain": "string",\n'
            '            "explanation": "string",\n'
            '            "key_terms": ["string"]\n'
            "        }"
        )
    examples_block = ",\n".join(example_items)
    return (
        "{\n"
        '    "title": "Deep Dive",\n'
        '    "compare_focus": "string",\n'
        '    "examples": [\n' + examples_block + "\n"
        "    ],\n"
        '    "takeaway": "string"\n'
        "}"
    )


def build_prompt(spec, blueprint: Blueprint, request: GenerateRequest) -> str:
    del spec

    dimensions = blueprint.deep_dive_dimensions
    dimensions_text = "\n".join(f"  - {d}" for d in dimensions)

    prompt_lines = [
        "Create the deep dive section for a study guide.",
        f"- Lesson title: {blueprint.title}",
        f"- Core concept: {blueprint.core_concept}",
        f"- Subject: {request.lesson_metadata.subject}",
        "- Compare/contrast dimensions for this subject and lesson:",
        dimensions_text,
        "Requirements:",
        f"- Write one example block for each of the {len(dimensions)} dimensions listed above.",
        "- In each example, set dimension to the label exactly as listed above.",
        "- Choose a topic_domain that gives a concrete, subject-appropriate context for that dimension.",
        "- Write an explanation that shows how the core concept applies in that dimension.",
        "- List key_terms that help students recognize or apply that dimension.",
        f"- Keep the reading level close to Grade {request.lesson_metadata.grade_level}.",
        f"- {_deep_dive_length_guidance(request)}",
        "- Use plain language throughout.",
        "Expected JSON schema:",
        _build_schema(dimensions),
        "Return only JSON.",
    ]

    return "\n".join(prompt_lines)
