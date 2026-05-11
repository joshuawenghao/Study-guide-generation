from __future__ import annotations

from app.types import (
    Blueprint,
    LearningTarget,
    SubCompetency,
    TopicDomains,
    VocabEntry,
)
from app.validators.hard.passage_domain_diff import validate_passage_domain_diff


def build_blueprint(*, model_domain: str, assessment_domain: str) -> Blueprint:
    return Blueprint(
        lesson_id="lesson-1",
        title="Author's Purpose",
        essential_question="Why does author purpose matter?",
        introduction_hook="Texts can approach the same skill through different topics.",
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
            model_passage=model_domain,
            assessment_passage=assessment_domain,
            entertain_example="games",
            inform_example="science",
            persuade_example="community",
        ),
        sub_competencies=[SubCompetency(id="sc-1", label="Purpose clues")],
        core_concept="Authors make choices that fit their purpose.",
    )


def test_validate_passage_domain_diff_passes_for_distinct_domains() -> None:
    result = validate_passage_domain_diff(
        blueprint=build_blueprint(
            model_domain="school talent show announcement",
            assessment_domain="mangrove forest protection article",
        )
    )

    assert result.passed is True
    assert result.failed_sections == []
    assert result.failures == {}


def test_validate_passage_domain_diff_fails_case_insensitive_match() -> None:
    result = validate_passage_domain_diff(
        blueprint=build_blueprint(
            model_domain="Mangrove Forest Protection",
            assessment_domain="mangrove forest protection",
        )
    )

    assert result.passed is False
    assert result.failed_sections == ["assessment_passage"]
    assert any(
        "must differ" in message for message in result.failures["assessment_passage"]
    )


def test_validate_passage_domain_diff_fails_when_domain_is_blank() -> None:
    result = validate_passage_domain_diff(
        blueprint=build_blueprint(
            model_domain="school talent show announcement",
            assessment_domain="   ",
        )
    )

    assert result.passed is False
    assert result.failed_sections == ["assessment_passage"]
    assert any(
        "must both be present" in message
        for message in result.failures["assessment_passage"]
    )
