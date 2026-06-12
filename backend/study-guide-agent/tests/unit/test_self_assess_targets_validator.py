from __future__ import annotations

from app.types import (
    Blueprint,
    LearningTarget,
    SelfAssessmentRow,
    SelfAssessmentSection,
    SubCompetency,
    TopicDomains,
    VocabEntry,
)
from app.validators.hard.self_assess_targets import validate_self_assess_targets


def build_blueprint() -> Blueprint:
    return Blueprint(
        lesson_id="lesson-1",
        title="Author's Purpose",
        essential_question="Why does author purpose matter?",
        introduction_hook="Texts shape reader thinking in different ways.",
        learning_targets=[
            LearningTarget(
                number=1,
                bloom_verb="identify",
                objective="Identify how authors signal purpose.",
            ),
            LearningTarget(
                number=2,
                bloom_verb="explain",
                objective="Explain how evidence supports the author's purpose.",
            ),
        ],
        vocabulary=[
            VocabEntry(
                word="audience",
                definition="The people a text is meant for.",
                example_sentence="The writer considered the audience before choosing details.",
            )
        ],
        topic_domains=TopicDomains(
            model_passage="animals",
            assessment_passage="space",
        ),
        sub_competencies=[SubCompetency(id="sc-1", label="Purpose clues")],
        core_concept="Authors make choices that fit their purpose.",
        deep_dive_dimensions=["entertain", "inform", "persuade"],
    )


def test_validate_self_assess_targets_passes_for_verbatim_objectives() -> None:
    blueprint = build_blueprint()
    self_assessment = SelfAssessmentSection(
        title="Self-Assessment",
        confidence_levels=["Not yet", "Almost there", "Got it"],
        rows=[
            SelfAssessmentRow(
                skill="Identify how authors signal purpose.",
                reflection_prompt="What clue helped you identify the purpose?",
            ),
            SelfAssessmentRow(
                skill="Explain how evidence supports the author's purpose.",
                reflection_prompt="Which evidence best supports your answer?",
            ),
        ],
    )

    result = validate_self_assess_targets(
        blueprint=blueprint,
        self_assessment=self_assessment,
    )

    assert result.passed is True
    assert result.failed_sections == []
    assert result.failures == {}


def test_validate_self_assess_targets_fails_for_non_verbatim_skill() -> None:
    blueprint = build_blueprint()
    self_assessment = SelfAssessmentSection(
        title="Self-Assessment",
        confidence_levels=["Not yet", "Almost there", "Got it"],
        rows=[
            SelfAssessmentRow(
                skill="Explain how evidence proves the author's purpose.",
                reflection_prompt="Which detail was strongest?",
            )
        ],
    )

    result = validate_self_assess_targets(
        blueprint=blueprint,
        self_assessment=self_assessment,
    )

    assert result.passed is False
    assert result.failed_sections == ["self_assessment"]
    assert "self_assessment" in result.failures
    assert any(
        "Explain how evidence proves the author's purpose." in message
        for message in result.failures["self_assessment"]
    )
