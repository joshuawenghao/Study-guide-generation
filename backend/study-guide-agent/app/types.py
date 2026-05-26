"""Study guide data contracts migrated from the legacy backend prototype."""

from __future__ import annotations

from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class LengthPreset(StrEnum):
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


class PromptLabSectionKey(StrEnum):
    INTRO = "intro"
    LEARNING_TARGETS = "learning_targets"
    WARMUP = "warmup"
    VOCABULARY = "vocabulary"
    CORE_EXPLAINER = "core_explainer"
    SUBCONCEPT = "subconcept"
    STRATEGY_LIST = "strategy_list"
    DEEP_DIVE = "deep_dive"
    MODEL_PASSAGE = "model_passage"
    CHECK_IN = "check_in"
    KEY_POINTS = "key_points"
    ASSESSMENT_PASSAGE = "assessment_passage"
    ASSESSMENT_QUESTIONS = "assessment_questions"
    STEP_UP = "step_up"
    SELF_ASSESSMENT = "self_assessment"
    ANSWER_KEY = "answer_key"


PROMPT_LAB_SECTION_KEYS: tuple[PromptLabSectionKey, ...] = (
    PromptLabSectionKey.INTRO,
    PromptLabSectionKey.LEARNING_TARGETS,
    PromptLabSectionKey.WARMUP,
    PromptLabSectionKey.VOCABULARY,
    PromptLabSectionKey.CORE_EXPLAINER,
    PromptLabSectionKey.SUBCONCEPT,
    PromptLabSectionKey.STRATEGY_LIST,
    PromptLabSectionKey.DEEP_DIVE,
    PromptLabSectionKey.MODEL_PASSAGE,
    PromptLabSectionKey.CHECK_IN,
    PromptLabSectionKey.KEY_POINTS,
    PromptLabSectionKey.ASSESSMENT_PASSAGE,
    PromptLabSectionKey.ASSESSMENT_QUESTIONS,
    PromptLabSectionKey.STEP_UP,
    PromptLabSectionKey.SELF_ASSESSMENT,
    PromptLabSectionKey.ANSWER_KEY,
)


class PromptLabSampleCaseId(StrEnum):
    ENGLISH_GRADE6_PH = "english_grade6_ph"
    MATH_GRADE4_VN = "math_grade4_vn"


PROMPT_LAB_SAMPLE_CASE_IDS: tuple[PromptLabSampleCaseId, ...] = (
    PromptLabSampleCaseId.ENGLISH_GRADE6_PH,
    PromptLabSampleCaseId.MATH_GRADE4_VN,
)


class PromptLabPromptOverrides(BaseModel):
    model_config = ConfigDict(extra="forbid")

    system_prompt_append: str | None = Field(
        default=None,
        description=(
            "Optional request-scoped instructions appended to the default system "
            "prompt for a prompt-lab run."
        ),
    )
    section_overrides: dict[PromptLabSectionKey, str] = Field(
        default_factory=dict,
        description=(
            "Request-scoped prompt overrides keyed by the supported prompt-lab "
            "section allowlist. These overrides do not mutate the default prompt "
            "templates on disk."
        ),
    )


class PromptLabGenerateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    base_request: GenerateRequest
    prompt_overrides: PromptLabPromptOverrides = Field(
        default_factory=PromptLabPromptOverrides
    )
    sample_case_id: PromptLabSampleCaseId | None = Field(
        default=None,
        description=(
            "Optional stable identifier for the curated prompt-lab sample case "
            "that seeded this request."
        ),
    )
    reviewer_label: str | None = Field(
        default=None,
        description="Optional reviewer-supplied label used only for prompt-lab runs.",
    )


class PromptLabSampleInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: PromptLabSampleCaseId
    label: str
    description: str
    request: GenerateRequest


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
        description=(
            "Blueprint-derived learning targets used by downstream sections and validators."
        )
    )
    vocabulary: list[VocabEntry] = Field(
        description=(
            "Canonical vocabulary entries that must appear across the generated guide."
        )
    )
    topic_domains: TopicDomains = Field(
        description=(
            "Topic domains for passages and rhetorical examples; model and "
            "assessment domains must differ."
        )
    )
    sub_competencies: list[SubCompetency] = Field(
        description="Sub-competencies carried forward from the curriculum input."
    )
    core_concept: str


class IntroSection(BaseModel):
    title: str
    hook: str
    essential_question: str
    paragraphs: list[str]
    bridge_to_lesson: str


class LearningTargetsCompetencyFocus(BaseModel):
    lesson_id: str
    core_concept: str


class LearningTargetsItem(BaseModel):
    number: int
    bloom_verb: str
    objective: str
    success_look_for: str


class LearningTargetsSection(BaseModel):
    title: str
    competency_focus: LearningTargetsCompetencyFocus
    targets: list[LearningTargetsItem]


class WarmupSection(BaseModel):
    title: str
    activity_type: str
    purpose: str
    student_instructions: list[str]
    teacher_tip: str
    estimated_minutes: int


class VocabularyEntrySectionItem(BaseModel):
    word: str
    part_of_speech: str
    definition: str
    example_sentence: str


class VocabularySection(BaseModel):
    title: str
    entries: list[VocabularyEntrySectionItem]


class KeyPointsItem(BaseModel):
    number: int
    sub_competency_id: str
    sub_competency_label: str
    statement: str


class KeyPointsSection(BaseModel):
    title: str
    points: list[KeyPointsItem]


class SelfAssessmentRow(BaseModel):
    skill: str
    reflection_prompt: str


class SelfAssessmentSection(BaseModel):
    title: str
    confidence_levels: list[str]
    rows: list[SelfAssessmentRow]


class CoreExplainerPoint(BaseModel):
    sub_competency_id: str
    sub_competency_label: str
    explanation: str
    real_world_connection: str


class CoreExplainerSection(BaseModel):
    title: str
    overview: str
    explained_points: list[CoreExplainerPoint]
    closing_summary: str


class QuickCheck(BaseModel):
    question: str
    expected_answer: str


class SubconceptSection(BaseModel):
    title: str
    sub_competency_id: str
    sub_competency_label: str
    explanation: str
    worked_example: str
    quick_check: QuickCheck


class StrategyItem(BaseModel):
    name: str
    when_to_use: str
    steps: list[str]


class StrategyListSection(BaseModel):
    title: str
    strategies: list[StrategyItem]


class DeepDiveExample(BaseModel):
    mode: str
    topic_domain: str
    explanation: str
    signal_words: list[str]


class DeepDiveSection(BaseModel):
    title: str
    compare_focus: str
    examples: list[DeepDiveExample]
    takeaway: str


class ModelPassageSection(BaseModel):
    title: str
    topic_domain: str
    genre: str
    passage: list[str]
    text_features: list[str]
    evidence_focus: str


class AssessmentPassageSection(BaseModel):
    title: str
    topic_domain: str
    genre: str
    passage: list[str]
    evidence_clues: list[str]
    answerability_note: str


class CheckInQuestion(BaseModel):
    number: int
    question: str
    evidence_hint: str
    expected_response_type: str


class CheckInSection(BaseModel):
    title: str
    passage_title: str
    questions: list[CheckInQuestion]


class AssessmentQuestionItem(BaseModel):
    number: int
    question: str
    question_type: str
    answer_expectation: str
    evidence_requirement: str


class AssessmentQuestionsSection(BaseModel):
    title: str
    passage_title: str
    questions: list[AssessmentQuestionItem]


class StepUpSection(BaseModel):
    title: str
    challenge_prompt: str
    required_evidence: list[str]
    success_criteria: list[str]


class AnswerKeyItem(BaseModel):
    question_number: int
    question: str
    possible_answer: str
    evidence_quote: str


class StepUpAnswer(BaseModel):
    challenge_response: str
    required_evidence: list[str]


class AnswerKeySection(BaseModel):
    title: str
    check_in_answers: list[AnswerKeyItem]
    assessment_answers: list[AnswerKeyItem]
    step_up_answer: StepUpAnswer
    teacher_note: str


SECTION_PAYLOAD_MODELS: dict[str, type[BaseModel]] = {
    "blueprint": Blueprint,
    "intro": IntroSection,
    "learning_targets": LearningTargetsSection,
    "warmup": WarmupSection,
    "vocabulary": VocabularySection,
    "key_points": KeyPointsSection,
    "self_assessment": SelfAssessmentSection,
    "core_explainer": CoreExplainerSection,
    "subconcept": SubconceptSection,
    "strategy_list": StrategyListSection,
    "deep_dive": DeepDiveSection,
    "model_passage": ModelPassageSection,
    "assessment_passage": AssessmentPassageSection,
    "check_in": CheckInSection,
    "assessment_questions": AssessmentQuestionsSection,
    "step_up": StepUpSection,
    "answer_key": AnswerKeySection,
}


class PreviewSection(BaseModel):
    section_id: str
    section_type: str
    title: str
    icon_key: str | None = Field(
        default=None,
        description=(
            "Optional renderer-selected icon token used for presentation-only "
            "visual affordances in the PDF and web preview."
        ),
    )
    content: dict[str, Any] = Field(
        description=(
            "Structured section payload for the frontend preview; exact shape varies "
            "by section type."
        )
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
        description=(
            "Sections included in the final output despite unresolved validation "
            "failures after retry."
        )
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
