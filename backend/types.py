"""
Pydantic data models for the Study Guide Generation backend.

These models define the data contracts between all workflow nodes,
validators, and the renderer. The JSON schema derived from these models
is also mirrored as TypeScript interfaces in frontend/lib/types.ts.
"""

from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Input contracts
# ---------------------------------------------------------------------------


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
    sub_competencies: list[SubCompetency]


class InstructionalDesign(BaseModel):
    core_concept: str
    bloom_targets: list[str] = Field(min_length=3, max_length=3)
    essential_question_seed: str


class OptionalInputs(BaseModel):
    vocabulary_seeds: Optional[list[str]] = None
    topic_domains: Optional[dict[str, str]] = None
    tone_register: str = "warm-formal"
    length_preset: str = "standard"  # "short" | "standard" | "long"


class GenerateRequest(BaseModel):
    lesson_metadata: LessonMetadata
    curriculum: Curriculum
    instructional_design: InstructionalDesign
    optional: OptionalInputs = Field(default_factory=OptionalInputs)


# ---------------------------------------------------------------------------
# Blueprint (shared context for all section nodes)
# ---------------------------------------------------------------------------


class LearningTarget(BaseModel):
    number: int
    bloom_verb: str
    objective: str


class VocabEntry(BaseModel):
    word: str
    definition: str
    example_sentence: str


class TopicDomains(BaseModel):
    model_passage: str
    assessment_passage: str
    entertain_example: str
    inform_example: str
    persuade_example: str


class Blueprint(BaseModel):
    lesson_id: str
    title: str
    essential_question: str
    introduction_hook: str
    learning_targets: list[LearningTarget]
    vocabulary: list[VocabEntry]
    topic_domains: TopicDomains
    sub_competencies: list[SubCompetency]
    core_concept: str


# ---------------------------------------------------------------------------
# Section output models
# ---------------------------------------------------------------------------


class SelfAssessmentSkillRow(BaseModel):
    """One row in the self-assessment table."""
    skill: str
    can_do_independently: bool = False
    can_do_with_help: bool = False
    need_more_practice: bool = False


class SelfAssessmentOutput(BaseModel):
    skills: list[SelfAssessmentSkillRow]


class AnswerOption(BaseModel):
    label: str   # e.g. "A", "B", "C", "D"
    text: str


class AnswerKeyItem(BaseModel):
    question_number: int
    correct_label: str
    possible_answers: list[str]


class AnswerKeyOutput(BaseModel):
    items: list[AnswerKeyItem]


class AssessmentPassageOutput(BaseModel):
    title: str
    text: str
    domain: str


class ModelPassageOutput(BaseModel):
    title: str
    text: str
    domain: str


# ---------------------------------------------------------------------------
# Validation contracts
# ---------------------------------------------------------------------------


class ValidationResult(BaseModel):
    """
    Returned by validator_node after running all hard and soft validators.

    validator_node must never raise — all failures are captured here.
    """

    passed: bool
    """True only when all hard validators pass (soft warnings do not affect this)."""

    failures: dict[str, list[str]] = Field(default_factory=dict)
    """
    Maps section_key -> list of hard-validator failure messages.
    Empty list means no failures for that section.
    """

    failed_sections: list[str] = Field(default_factory=list)
    """Ordered list of section keys that failed at least one hard validator."""

    warnings: list[str] = Field(default_factory=list)
    """Soft-validator warning strings to surface in the web preview."""

    retried_sections: list[str] = Field(default_factory=list)
    """Section keys that were retried during the validation pass."""

    best_effort_sections: list[str] = Field(default_factory=list)
    """
    Section keys that failed after their one permitted retry.
    Assembled with a visible warning badge in the final document.
    """


# ---------------------------------------------------------------------------
# Output contracts
# ---------------------------------------------------------------------------


class PreviewSection(BaseModel):
    section_id: str
    section_type: str
    title: str
    content: Any
    warning: Optional[str] = None
    best_effort: bool = False


class WebPreviewPayload(BaseModel):
    sections: list[PreviewSection]


class GenerateResponse(BaseModel):
    success: bool
    pdf_base64: str = ""
    preview: Optional[WebPreviewPayload] = None
    validation: Optional[ValidationResult] = None
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Streaming progress events
# ---------------------------------------------------------------------------


class ProgressEvent(BaseModel):
    type: str  # "node_started" | "node_complete" | "validation_started"
               # | "retry_started" | "render_started" | "done" | "error"
    node: str
    message: Optional[str] = None
    timestamp: str
