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
		"Use college-preparatory academic language, precise subject terminology, and "
		"efficient explanations suitable for advanced secondary learners."
	)


def build_system_prompt(request: GenerateRequest) -> str:
	"""Build the shared system prompt for structured study guide generation."""

	metadata = request.lesson_metadata
	reading_level_guidance = _reading_level_guidance(metadata.grade_level)

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
			"Output discipline: Follow the requested structure exactly, keep every field "
			"machine-parseable, and do not invent extra top-level keys, side notes, or "
			"explanatory text outside the required JSON schema."
		),
	]

	return "\n".join(prompt_lines)