from __future__ import annotations

from app.types import Blueprint, GenerateRequest


def build_prompt(spec, blueprint: Blueprint, request: GenerateRequest) -> str:
    del spec, request

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
        "Expected JSON schema:",
        assessment_passage_schema,
        "Return only JSON.",
    ]

    return "\n".join(prompt_lines)
