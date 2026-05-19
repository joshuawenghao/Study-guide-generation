"""System prompt builder for study guide generation."""

from __future__ import annotations

from app.types import GenerateRequest


def _reading_level_guidance(grade_level: int) -> str:
    if grade_level <= 2:
        return (
            "Use very short sentences, concrete vocabulary, and direct explanations that "
            "support early readers."
        )
    if grade_level <= 5:
        return (
            "Use clear grade-appropriate vocabulary, mostly short-to-medium sentences, "
            "and concrete examples before abstraction."
        )
    if grade_level <= 8:
        return (
            "Use accessible academic language, varied sentence length, and explanations "
            "that assume developing independence with subject vocabulary."
        )
    if grade_level <= 10:
        return (
            "Use solid secondary-school academic language, precise terminology, and "
            "explanations that remain readable without becoming simplistic."
        )
    return (
        "Use advanced secondary-school academic language with precise subject terminology, "
        "but keep explanations plain, concrete, and efficient enough for first-pass student reading. "
        "When a technical term is necessary, define it in simpler words nearby instead of building long, dense sentences."
    )


def _subject_notation_guidance(subject: str) -> str | None:
    normalized_subject = subject.lower()
    if "math" not in normalized_subject:
        return None
    return (
        "Math notation rule: Use plain-text math notation such as 3/4, 1/2, 4 x 6, "
        "or x + 3. Do not use LaTeX commands, backslashes, or escaped control "
        "sequences in the JSON output."
    )


def build_system_prompt(request: GenerateRequest) -> str:
    """Build the shared system prompt for structured study guide generation."""

    metadata = request.lesson_metadata
    reading_level_guidance = _reading_level_guidance(metadata.grade_level)
    subject_notation_guidance = _subject_notation_guidance(metadata.subject)

    prompt_lines = [
        (
            "You are an expert curriculum-aligned study guide writer for "
            f"{metadata.market} Grade {metadata.grade_level} {metadata.subject}."
        ),
        (
            "Write for learners in the "
            f"{metadata.market} market and keep all explanations appropriate for "
            f"Grade {metadata.grade_level} {metadata.subject}."
        ),
        f"Reading level guidance: {reading_level_guidance}",
        (
            "Voice rules: Maintain a warm, clear, and encouraging teaching voice. "
            "Never sound condescending, sarcastic, or patronizing."
        ),
        (
            "Cultural relevance: Use names, situations, references, and examples that feel "
            f"natural and contextually appropriate for learners in {metadata.market}. Avoid "
            "irrelevant cultural assumptions from other markets unless the request explicitly "
            "requires them."
        ),
        (
            "Formatting rules: Return valid JSON only. Do not wrap the response in markdown "
            "code fences. Do not add commentary, headings, or prose outside the JSON object."
        ),
        (
            "Markup rule: Do not include HTML or XML tags such as <b>, <i>, <br>, or "
            "<p> anywhere in any JSON string value. Return plain text only."
        ),
        (
            "Readability target: Aim for a Flesch-Kincaid reading level close to "
            f"Grade {metadata.grade_level}. Prefer common everyday words when possible, "
            "keep most sentences to one clear idea, and avoid extra clauses or abstract "
            "academic phrasing unless a lesson term requires it."
        ),
        (
            "Age-fit rule: Keep the material intellectually appropriate for the target grade "
            "even when the language is simple. Do not make older-student content sound childish "
            "or written for much younger learners."
        ),
        (
            "Sentence discipline: Keep sentences concise. For upper elementary and middle "
            "school outputs, default to short-to-medium sentences and define new academic "
            "terms in plain language immediately when they first appear."
        ),
        (
            "Output discipline: Follow the requested structure exactly, keep every field "
            "machine-parseable, and do not invent extra top-level keys, side notes, or "
            "explanatory text outside the required JSON schema."
        ),
    ]

    if subject_notation_guidance is not None:
        prompt_lines.append(subject_notation_guidance)

    return "\n".join(prompt_lines)
