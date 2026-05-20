from __future__ import annotations

from app.types import Blueprint, GenerateRequest, LengthPreset


def _passage_length_guidance(request: GenerateRequest) -> str:
    grade_level = request.lesson_metadata.grade_level
    length_preset = request.optional.length_preset

    if length_preset is LengthPreset.SHORT or grade_level <= 4:
        return "Write 2 short paragraphs with direct wording and mostly simple sentence structures."
    if length_preset is LengthPreset.LONG or grade_level >= 9:
        return "Write 3 concise paragraphs with direct wording and clear sentence variety, while keeping the passage readable for the target grade."
    return "Write 2 or 3 concise paragraphs with direct wording and readable sentence structures."


def build_prompt(spec, blueprint: Blueprint, request: GenerateRequest) -> str:
    del spec

    assessment_passage_schema = """{
    "title": "Assessment Passage",
    "topic_domain": "string",
    "genre": "string",
    "passage": [
        "string"
    ],
    "evidence_clues": [
        "string"
    ],
    "answerability_note": "string"
}"""

    prompt_lines = [
        "Create the assessment passage section for a K-12 study guide.",
        f"- Lesson title: {blueprint.title}",
        f"- Essential question: {blueprint.essential_question}",
        f"- Topic domain for this passage: {blueprint.topic_domains.assessment_passage}",
        f"- Model passage topic domain to avoid: {blueprint.topic_domains.model_passage}",
        f"- Core concept: {blueprint.core_concept}",
        "Requirements:",
        "- Use the assigned assessment_passage topic domain exactly and keep it different from the model passage domain.",
        "- Write an evidence-friendly passage suitable for downstream assessment questions and answer-key quotation checks.",
        "- Include evidence_clues that point to phrases students can quote or cite.",
        "- Return the passage as an ordered list of paragraphs.",
        '- Do not append bracketed notes, clue lists, or inline annotations such as ["quote one", "quote two"] inside any passage paragraph.',
        f"- Keep the passage readable for Grade {request.lesson_metadata.grade_level} students.",
        f"- {_passage_length_guidance(request)}",
        "- Prefer familiar words, concrete details, and short sentences with one main idea each.",
        "- Avoid dense informational phrasing unless a lesson term requires it.",
        "Expected JSON schema:",
        assessment_passage_schema,
        "Return only JSON.",
    ]

    return "\n".join(prompt_lines)
