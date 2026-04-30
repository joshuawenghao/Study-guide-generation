"""Source-of-truth data contracts for the study guide backend.

This module defines all shared Pydantic v2 models used across the ADK backend.
These models are the canonical JSON contract for requests, blueprint outputs,
validation results, final responses, and streamed progress events. The frontend
TypeScript types must mirror these models exactly.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class LengthPreset(str, Enum):
	"""Supported output length presets for generation."""

	SHORT = "short"
	STANDARD = "standard"
	LONG = "long"


class TopicDomains(BaseModel):
	model_passage: str
	assessment_passage: str
	entertain_example: str
	inform_example: str
	persuade_example: str


class SubCompetency(BaseModel):
	id: str
	label: str


class LessonMetadata(BaseModel):
	subject: str
	grade_level: int = Field(ge=1, le=12)
	market: str
	language: str = "en"
	unit_number: int
	unit_title: str
	lesson_number: int
	lesson_title: str
	lesson_code: str


class Curriculum(BaseModel):
	competency_code: str
	competency_description: str
	sub_competencies: list[SubCompetency] = Field(
		description="Ordered list of sub-competencies that the lesson targets."
	)


class InstructionalDesign(BaseModel):
	core_concept: str
	bloom_targets: tuple[str, str, str] = Field(
		description="Exactly three Bloom-aligned target verbs used to shape objectives."
	)
	essential_question_seed: str


class OptionalInputs(BaseModel):
	vocabulary_seeds: list[str] | None = Field(
		default=None,
		description="Optional teacher-provided vocabulary hints to bias blueprint generation.",
	)
	topic_domains: dict[str, str] | None = Field(
		default=None,
		description="Optional topic domain hints keyed by passage or example role.",
	)
	tone_register: str = "warm-formal"
	length_preset: LengthPreset = LengthPreset.STANDARD


class GenerateRequest(BaseModel):
	lesson_metadata: LessonMetadata
	curriculum: Curriculum
	instructional_design: InstructionalDesign
	optional: OptionalInputs


class LearningTarget(BaseModel):
	number: int
	bloom_verb: str
	objective: str


class VocabEntry(BaseModel):
	word: str
	definition: str
	example_sentence: str


class Blueprint(BaseModel):
	lesson_id: str
	title: str
	essential_question: str
	introduction_hook: str
	learning_targets: list[LearningTarget] = Field(
		description="Blueprint-derived learning targets used by downstream sections and validators."
	)
	vocabulary: list[VocabEntry] = Field(
		description="Canonical vocabulary entries that must appear across the generated guide."
	)
	topic_domains: TopicDomains = Field(
		description="Topic domains for passages and rhetorical examples; model and assessment domains must differ."
	)
	sub_competencies: list[SubCompetency] = Field(
		description="Sub-competencies carried forward from the curriculum input."
	)
	core_concept: str


class PreviewSection(BaseModel):
	section_id: str
	section_type: str
	title: str
	content: dict[str, Any] = Field(
		description="Structured section payload for the frontend preview; exact shape varies by section type."
	)


class WebPreviewPayload(BaseModel):
	sections: list[PreviewSection] = Field(
		description="Ordered preview sections rendered by the frontend web preview."
	)


class ValidationResult(BaseModel):
	passed: bool
	failed_sections: list[str] = Field(
		description="Section keys that failed one or more validators in the latest validation pass."
	)
	failures: dict[str, list[str]] = Field(
		description="Per-section validation failure messages, keyed by section key."
	)
	warnings: list[str] = Field(
		description="Non-blocking validator warnings that should be surfaced in the UI."
	)
	best_effort_sections: list[str] = Field(
		description="Sections included in the final output despite unresolved validation failures after retry."
	)


class GenerateResponse(BaseModel):
	success: bool
	pdf_base64: str
	preview: WebPreviewPayload
	validation: ValidationResult
	error: str | None = None


ProgressEventType = Literal[
	"node_started",
	"node_complete",
	"validation_started",
	"retry_started",
	"render_started",
	"done",
	"error",
]


class ProgressEvent(BaseModel):
	type: ProgressEventType
	node: str
	message: str | None = None
	timestamp: str
