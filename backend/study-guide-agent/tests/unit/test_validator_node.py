from __future__ import annotations

from typing import Any

import pytest

from app.nodes import validator as validator_module
from app.types import (
    Blueprint,
    GenerateRequest,
    LearningTarget,
    SubCompetency,
    TopicDomains,
    ValidationResult,
    VocabEntry,
)


def build_request() -> GenerateRequest:
    return GenerateRequest.model_validate(
        {
            "lesson_metadata": {
                "subject": "English",
                "grade_level": 6,
                "market": "PH",
                "language": "en",
                "unit_number": 1,
                "unit_title": "Reading",
                "lesson_number": 2,
                "lesson_title": "Author's Purpose",
                "lesson_code": "ENG6-U1-L2",
            },
            "curriculum": {
                "competency_code": "ENG6",
                "competency_description": "Explain author's purpose.",
                "sub_competencies": [{"id": "sc-1", "label": "Purpose clues"}],
            },
            "instructional_design": {
                "core_concept": "Authors choose details for a purpose.",
                "bloom_targets": ["identify", "explain", "analyze"],
                "essential_question_seed": "Why does author purpose matter?",
            },
            "optional": {},
        }
    )


def build_blueprint() -> Blueprint:
    return Blueprint(
        lesson_id="ENG6-U1-L2",
        title="Author's Purpose",
        essential_question="Why does author purpose matter?",
        introduction_hook="Texts can guide readers in different ways.",
        learning_targets=[
            LearningTarget(
                number=1,
                bloom_verb="identify",
                objective="Identify how authors signal purpose.",
            )
        ],
        vocabulary=[
            VocabEntry(
                word="audience",
                definition="The people a text is meant for.",
                example_sentence="The writer considered the audience before choosing details.",
            )
        ],
        topic_domains=TopicDomains(
            model_passage="school talent show announcement",
            assessment_passage="mangrove forest protection article",
            entertain_example="games",
            inform_example="science",
            persuade_example="community",
        ),
        sub_competencies=[SubCompetency(id="sc-1", label="Purpose clues")],
        core_concept="Authors choose details for a purpose.",
    )


def _success_result(*, warnings: list[str] | None = None) -> ValidationResult:
    return ValidationResult(
        passed=True,
        failed_sections=[],
        failures={},
        warnings=warnings or [],
        best_effort_sections=[],
    )


def _failure_result(section_key: str, message: str) -> ValidationResult:
    return ValidationResult(
        passed=False,
        failed_sections=[section_key],
        failures={section_key: [message]},
        warnings=[],
        best_effort_sections=[],
    )


@pytest.mark.asyncio
async def test_generate_validation_runs_schema_checks_for_each_section_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    schema_calls: list[tuple[str, Any]] = []

    def fake_validate_json_schema(
        *, section_key: str, payload: Any
    ) -> ValidationResult:
        schema_calls.append((section_key, payload))
        return _success_result()

    monkeypatch.setattr(
        validator_module, "validate_json_schema", fake_validate_json_schema
    )
    monkeypatch.setattr(
        validator_module,
        "validate_passage_domain_diff",
        lambda **_: _success_result(),
    )
    monkeypatch.setattr(
        validator_module,
        "validate_vocab_presence",
        lambda **_: _success_result(),
    )
    monkeypatch.setattr(
        validator_module,
        "validate_self_assess_targets",
        lambda **_: _success_result(),
    )
    monkeypatch.setattr(
        validator_module,
        "validate_assessment_question_grounding",
        lambda **_: _success_result(),
    )
    monkeypatch.setattr(
        validator_module,
        "validate_answer_key_quotes",
        lambda **_: _success_result(),
    )
    monkeypatch.setattr(
        validator_module,
        "validate_answer_leakage",
        lambda **_: _success_result(),
    )
    monkeypatch.setattr(
        validator_module,
        "validate_reading_level",
        lambda **_: _success_result(),
    )

    sections = {
        "intro": {"title": "Introduction"},
        "subconcept": [{"title": "One"}, {"title": "Two"}],
        "self_assessment": {
            "title": "Self-Assessment",
            "confidence_levels": ["Not yet", "Almost there", "Got it"],
            "rows": [
                {
                    "skill": "Identify how authors signal purpose.",
                    "reflection_prompt": "What clue helped you?",
                }
            ],
        },
        "assessment_passage": {
            "title": "Assessment Passage",
            "topic_domain": "mangrove forests",
            "genre": "article",
            "passage": ["Mangrove forests protect coastlines from strong waves."],
            "evidence_clues": ["protect coastlines"],
            "answerability_note": "Quote the text.",
        },
        "assessment_questions": {
            "title": "Assessment Questions",
            "passage_title": "Assessment Passage",
            "questions": [
                {
                    "number": 1,
                    "question": "What is the purpose?",
                    "expected_response_type": "short_response",
                    "evidence_hint": "Look for the part of the passage about protect coastlines.",
                }
            ],
        },
        "answer_key": {
            "title": "Answer Key",
            "check_in_answers": [],
            "assessment_answers": [
                {
                    "question_number": 1,
                    "question": "What is the purpose?",
                    "possible_answer": 'It informs because "protect coastlines" is explicit.',
                    "evidence_quote": '"protect coastlines"',
                }
            ],
            "step_up_answer": {
                "challenge_response": "Explain the purpose.",
                "required_evidence": ['"protect coastlines"'],
            },
            "teacher_note": "Accept equivalent direct-evidence answers.",
        },
    }

    result = await validator_module.generate_validation(
        build_request(),
        build_blueprint(),
        sections,
    )

    assert result.passed is True
    assert [section_key for section_key, _ in schema_calls].count("subconcept") == 2
    assert [section_key for section_key, _ in schema_calls] == [
        "intro",
        "subconcept",
        "subconcept",
        "self_assessment",
        "assessment_passage",
        "assessment_questions",
        "answer_key",
    ]


@pytest.mark.asyncio
async def test_generate_validation_aggregates_failures_and_skips_invalid_schema_slice(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    self_assessment_validator_called = False

    def fake_validate_json_schema(
        *, section_key: str, payload: Any
    ) -> ValidationResult:
        del payload
        if section_key == "self_assessment":
            return _failure_result(section_key, "schema failure")
        return _success_result()

    def fake_validate_self_assess_targets(**_: Any) -> ValidationResult:
        nonlocal self_assessment_validator_called
        self_assessment_validator_called = True
        return _success_result()

    monkeypatch.setattr(
        validator_module, "validate_json_schema", fake_validate_json_schema
    )
    monkeypatch.setattr(
        validator_module,
        "validate_passage_domain_diff",
        lambda **_: _failure_result("assessment_passage", "domains must differ"),
    )
    monkeypatch.setattr(
        validator_module,
        "validate_vocab_presence",
        lambda **_: _failure_result("intro", "missing vocabulary"),
    )
    monkeypatch.setattr(
        validator_module,
        "validate_self_assess_targets",
        fake_validate_self_assess_targets,
    )
    monkeypatch.setattr(
        validator_module,
        "validate_assessment_question_grounding",
        lambda **_: _success_result(),
    )
    monkeypatch.setattr(
        validator_module,
        "validate_answer_key_quotes",
        lambda **_: _success_result(),
    )
    monkeypatch.setattr(
        validator_module,
        "validate_answer_leakage",
        lambda **_: _success_result(warnings=["Potential answer leakage in intro"]),
    )
    monkeypatch.setattr(
        validator_module,
        "validate_reading_level",
        lambda **_: _success_result(warnings=["Reading level warning for intro"]),
    )

    sections = {
        "intro": {"title": "Introduction"},
        "self_assessment": {
            "title": "Self-Assessment",
            "confidence_levels": ["Not yet", "Almost there", "Got it"],
            "rows": [
                {
                    "skill": "Identify how authors signal purpose.",
                    "reflection_prompt": "What clue helped you?",
                }
            ],
        },
        "assessment_passage": {
            "title": "Assessment Passage",
            "topic_domain": "mangrove forests",
            "genre": "article",
            "passage": ["Mangrove forests protect coastlines from strong waves."],
            "evidence_clues": ["protect coastlines"],
            "answerability_note": "Quote the text.",
        },
        "assessment_questions": {
            "title": "Assessment Questions",
            "passage_title": "Assessment Passage",
            "questions": [
                {
                    "number": 1,
                    "question": "What is the purpose?",
                    "expected_response_type": "short_response",
                    "evidence_hint": "Look for the part of the passage about protect coastlines.",
                }
            ],
        },
        "answer_key": {
            "title": "Answer Key",
            "check_in_answers": [],
            "assessment_answers": [
                {
                    "question_number": 1,
                    "question": "What is the purpose?",
                    "possible_answer": 'It informs because "protect coastlines" is explicit.',
                    "evidence_quote": '"protect coastlines"',
                }
            ],
            "step_up_answer": {
                "challenge_response": "Explain the purpose.",
                "required_evidence": ['"protect coastlines"'],
            },
            "teacher_note": "Accept equivalent direct-evidence answers.",
        },
    }

    result = await validator_module.generate_validation(
        build_request(),
        build_blueprint(),
        sections,
    )

    assert result.passed is False
    assert result.failed_sections == ["self_assessment", "assessment_passage", "intro"]
    assert result.failures["self_assessment"] == ["schema failure"]
    assert result.failures["assessment_passage"] == ["domains must differ"]
    assert result.failures["intro"] == ["missing vocabulary"]
    assert result.warnings == [
        "Potential answer leakage in intro",
        "Reading level warning for intro",
    ]
    assert self_assessment_validator_called is False


def test_validate_assessment_question_grounding_fails_when_evidence_hint_is_off_passage() -> (
    None
):
    assessment_questions = validator_module.AssessmentQuestionsSection.model_validate(
        {
            "title": "Assessment Questions",
            "passage_title": "Assessment Passage",
            "questions": [
                {
                    "number": 1,
                    "question": "What is the purpose?",
                    "expected_response_type": "short_response",
                    "evidence_hint": "Look for the part of the passage about protecting every shoreline family during storms.",
                }
            ],
        }
    )
    assessment_passage = validator_module.AssessmentPassageSection.model_validate(
        {
            "title": "Assessment Passage",
            "topic_domain": "mangrove forests",
            "genre": "article",
            "passage": ["Mangrove forests protect coastlines from strong waves."],
            "evidence_clues": ["protect coastlines"],
            "answerability_note": "Quote the text.",
        }
    )

    result = validator_module.validate_assessment_question_grounding(
        assessment_questions=assessment_questions,
        assessment_passage=assessment_passage,
    )

    assert result.passed is False
    assert result.failed_sections == ["assessment_questions"]


def test_validate_assessment_question_grounding_accepts_location_style_hint_when_grounded() -> (
    None
):
    assessment_questions = validator_module.AssessmentQuestionsSection.model_validate(
        {
            "title": "Assessment Questions",
            "passage_title": "Assessment Passage",
            "questions": [
                {
                    "number": 1,
                    "question": "What is the author's primary purpose in this article?",
                    "expected_response_type": "Short answer",
                    "evidence_hint": "Look at the first paragraph where the article explains why mangroves protect coastlines.",
                }
            ],
        }
    )
    assessment_passage = validator_module.AssessmentPassageSection.model_validate(
        {
            "title": "Assessment Passage",
            "topic_domain": "mangrove forests",
            "genre": "article",
            "passage": ["Mangrove forests protect coastlines from strong waves."],
            "evidence_clues": ["protect coastlines"],
            "answerability_note": "Quote the text.",
        }
    )

    result = validator_module.validate_assessment_question_grounding(
        assessment_questions=assessment_questions,
        assessment_passage=assessment_passage,
    )

    assert result.passed is True
