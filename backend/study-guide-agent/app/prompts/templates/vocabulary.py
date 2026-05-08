from __future__ import annotations

from app.types import Blueprint, GenerateRequest


def build_prompt(spec, blueprint: Blueprint, request: GenerateRequest) -> str:
    del spec, request

    vocabulary_schema = """{
    "title": "Vocabulary",
    "entries": [
        {
            "word": "string",
            "part_of_speech": "string",
            "definition": "string",
            "example_sentence": "string"
        }
    ]
}"""

    vocabulary_text = "\n".join(
        f"- {entry.word}: {entry.definition} Example: {entry.example_sentence}"
        for entry in blueprint.vocabulary
    )

    prompt_lines = [
        "Create the vocabulary section for a K-12 study guide.",
        f"- Lesson title: {blueprint.title}",
        f"- Core concept: {blueprint.core_concept}",
        "- Canonical vocabulary entries from the blueprint:",
        vocabulary_text,
        "Requirements:",
        "- Return exactly one entry for each blueprint vocabulary word, in the same order.",
        "- Copy each word exactly so downstream validators can track vocabulary usage across the guide.",
        "- Add a classroom-appropriate part_of_speech for each word.",
        "- Keep definitions and example sentences aligned to the lesson context.",
        "- Do not invent extra vocabulary words or omit any blueprint word.",
        "Expected JSON schema:",
        vocabulary_schema,
        "Return only JSON.",
    ]

    return "\n".join(prompt_lines)
