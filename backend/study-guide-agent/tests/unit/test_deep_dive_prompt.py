"""Unit tests for the deep dive prompt builder — subject-agnostic dimensions."""

from __future__ import annotations

from app.prompts.templates.deep_dive import build_prompt
from app.types import (
    Blueprint,
    Curriculum,
    GenerateRequest,
    InstructionalDesign,
    LearningTarget,
    LessonMetadata,
    OptionalInputs,
    SubCompetency,
    TopicDomains,
    VocabEntry,
)


def _make_blueprint(dimensions: list[str], subject_label: str = "Nursing") -> Blueprint:
    return Blueprint(
        lesson_id="HN12-U3-L2",
        title="Standard Precautions",
        essential_question="How do nurses protect patients?",
        introduction_hook="Nurses apply precautions in every interaction.",
        learning_targets=[
            LearningTarget(number=1, bloom_verb="identify", objective="Identify precautions.")
        ],
        vocabulary=[
            VocabEntry(
                word="PPE",
                definition="Personal protective equipment.",
                example_sentence="PPE protects nurses.",
            )
        ],
        topic_domains=TopicDomains(model_passage="triage", assessment_passage="wound care"),
        sub_competencies=[SubCompetency(id="sc-1", label="Hand hygiene")],
        core_concept="Infection prevention",
        deep_dive_dimensions=dimensions,
    )


def _make_request(subject: str = "Nursing", grade_level: int = 12) -> GenerateRequest:
    return GenerateRequest(
        lesson_metadata=LessonMetadata(
            subject=subject,
            grade_level=grade_level,
            market="PH",
            unit_number=3,
            unit_title="Infection Control",
            lesson_number=2,
            lesson_title="Standard Precautions",
            lesson_code="HN12-U3-L2",
        ),
        curriculum=Curriculum(
            competency_code="HN12-IP-1",
            competency_description="Apply standard precautions.",
            sub_competencies=[SubCompetency(id="sc-1", label="Hand hygiene")],
        ),
        instructional_design=InstructionalDesign(
            core_concept="Infection prevention",
            bloom_targets=("identify", "apply", "evaluate"),
            essential_question_seed="How do precautions protect?",
        ),
        optional=OptionalInputs(),
    )


def test_deep_dive_prompt_includes_all_dimensions() -> None:
    dimensions = ["assessment", "intervention", "evaluation"]
    prompt = build_prompt(None, _make_blueprint(dimensions), _make_request())
    for d in dimensions:
        assert d in prompt, f"Expected dimension '{d}' to appear in prompt"


def test_deep_dive_prompt_schema_uses_dimension_and_key_terms() -> None:
    prompt = build_prompt(None, _make_blueprint(["assessment", "intervention"]), _make_request())
    assert '"dimension"' in prompt
    assert '"key_terms"' in prompt
    assert '"signal_words"' not in prompt
    assert '"mode"' not in prompt


def test_deep_dive_prompt_has_no_hardcoded_ela_strings_for_nursing_subject() -> None:
    prompt = build_prompt(None, _make_blueprint(["assessment", "intervention", "evaluation"]), _make_request())
    # The ELA author-purpose labels must NOT appear as hardcoded strings in the generated prompt
    # (they may appear if the blueprint happens to use them, but must not be hardcoded)
    assert "entertain, inform, and persuade" not in prompt
    assert "entertain_example" not in prompt
    assert "inform_example" not in prompt
    assert "persuade_example" not in prompt


def test_deep_dive_prompt_schema_has_one_block_per_dimension() -> None:
    dimensions = ["assessment", "intervention", "evaluation"]
    prompt = build_prompt(None, _make_blueprint(dimensions), _make_request())
    for d in dimensions:
        assert f'"dimension": "{d}"' in prompt


def test_deep_dive_prompt_ela_dimensions_appear_for_ela_subject() -> None:
    dims = ["entertain", "inform", "persuade"]
    prompt = build_prompt(
        None,
        _make_blueprint(dims, subject_label="English"),
        _make_request(subject="English", grade_level=6),
    )
    for d in dims:
        assert d in prompt
