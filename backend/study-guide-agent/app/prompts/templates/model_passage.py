from __future__ import annotations

from app.types import Blueprint, GenerateRequest


def build_prompt(spec, blueprint: Blueprint, request: GenerateRequest) -> str:
    del spec, request

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
        "Expected JSON schema:",
        model_passage_schema,
        "Return only JSON.",
    ]

    return "\n".join(prompt_lines)
