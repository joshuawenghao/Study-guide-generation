from __future__ import annotations

from app.types import Blueprint, GenerateRequest, LengthPreset


def _passage_length_guidance(request: GenerateRequest) -> str:
    grade_level = request.lesson_metadata.grade_level
    length_preset = request.optional.length_preset

    if length_preset is LengthPreset.SHORT or grade_level <= 4:
        return "Write 2 short paragraphs with mostly simple sentence structures."
    if length_preset is LengthPreset.LONG or grade_level >= 9:
        return "Write 3 concise paragraphs with clear sentence variety, while keeping the passage readable for the target grade."
    return "Write 2 or 3 concise paragraphs with clear, readable sentence structures."


def build_prompt(spec, blueprint: Blueprint, request: GenerateRequest) -> str:
    del spec

    model_passage_schema = """{
    "title": "Model Passage",
    "topic_domain": "string",
    "genre": "string",
    "passage": [
        "string"
    ],
    "text_features": [
        "string"
    ],
    "evidence_focus": "string"
}"""

    prompt_lines = [
        "Create the model passage section for a K-12 study guide.",
        f"- Lesson title: {blueprint.title}",
        f"- Essential question: {blueprint.essential_question}",
        f"- Topic domain for this passage: {blueprint.topic_domains.model_passage}",
        f"- Core concept: {blueprint.core_concept}",
        "Requirements:",
        "- Use the assigned model_passage topic domain exactly as the context for the passage.",
        "- Write an evidence-friendly passage that makes the author's purpose inferable from the text.",
        "- Return the passage as an ordered list of paragraphs.",
        "- Include text_features students can notice while reading.",
        f"- Keep the passage readable for Grade {request.lesson_metadata.grade_level} students.",
        f"- {_passage_length_guidance(request)}",
        "- Prefer familiar words and concrete details over descriptive flourish.",
        "- Keep most sentences to one clear idea and avoid long dependent clauses.",
        "Expected JSON schema:",
        model_passage_schema,
        "Return only JSON.",
    ]

    return "\n".join(prompt_lines)
