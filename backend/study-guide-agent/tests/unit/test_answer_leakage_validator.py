from __future__ import annotations

from app.types import (
    AnswerKeyItem,
    AnswerKeySection,
    AssessmentPassageSection,
    AssessmentQuestionItem,
    AssessmentQuestionsSection,
    IntroSection,
    StepUpAnswer,
)
from app.validators.soft.answer_leakage import validate_answer_leakage


def build_answer_key() -> AnswerKeySection:
    return AnswerKeySection(
        title="Answer Key",
        check_in_answers=[
            AnswerKeyItem(
                question_number=1,
                question="What clue shows the author's tone?",
                possible_answer="The tone sounds encouraging.",
                evidence_quote='"encouraging tone"',
            )
        ],
        assessment_answers=[
            AnswerKeyItem(
                question_number=2,
                question="What is the author's purpose in this article?",
                possible_answer="The author wants to inform readers about why mangroves matter.",
                evidence_quote='"mangroves protect coastlines from storm surges"',
            )
        ],
        step_up_answer=StepUpAnswer(
            challenge_response="Use details from the article to explain the purpose.",
            required_evidence=['"mangroves protect coastlines from storm surges"'],
        ),
        teacher_note="Accept equivalent answers with direct evidence.",
    )


def test_validate_answer_leakage_ignores_assessment_passage_source_text() -> None:
    result = validate_answer_leakage(
        answer_key=build_answer_key(),
        section_payloads={
            "assessment_passage": AssessmentPassageSection(
                title="Assessment Passage",
                topic_domain="mangrove forests",
                genre="article",
                passage=[
                    "Mangrove forests protect coastlines from strong waves.",
                    "They help both people and wildlife stay safe.",
                ],
                evidence_clues=["protect coastlines", "stay safe"],
                answerability_note="Answers should cite exact wording from the passage.",
            )
        },
    )

    assert result.passed is True
    assert result.failed_sections == []
    assert result.failures == {}
    assert result.warnings == []


def test_validate_answer_leakage_warns_when_body_section_repeats_quote() -> None:
    result = validate_answer_leakage(
        answer_key=build_answer_key(),
        section_payloads={
            "intro": IntroSection(
                title="Introduction",
                hook="Think about why authors choose certain details.",
                essential_question="Why does author purpose matter?",
                paragraphs=[
                    "An author may explain how mangroves protect coastlines from storm surges before students answer the assessment.",
                ],
                bridge_to_lesson="You will study how details shape a reader's thinking.",
            )
        },
    )

    assert result.passed is True
    assert result.failed_sections == []
    assert result.failures == {}
    assert any("intro" in warning for warning in result.warnings)
    assert any(
        "mangroves protect coastlines from storm surges" in warning
        for warning in result.warnings
    )


def test_validate_answer_leakage_ignores_short_quoted_phrases() -> None:
    """Phrases under 5 words must not trigger leakage warnings."""
    short_phrase_key = AnswerKeySection(
        title="Answer Key",
        check_in_answers=[],
        assessment_answers=[
            AnswerKeyItem(
                question_number=1,
                question="What protects the coast?",
                possible_answer="Mangroves protect coastlines.",
                evidence_quote='"protect coastlines"',
            )
        ],
        step_up_answer=StepUpAnswer(
            challenge_response="Explain in your own words.",
            required_evidence=[],
        ),
        teacher_note="",
    )

    result = validate_answer_leakage(
        answer_key=short_phrase_key,
        section_payloads={
            "intro": IntroSection(
                title="Introduction",
                hook="Think about why authors choose certain details.",
                essential_question="Why does author purpose matter?",
                paragraphs=[
                    "Mangroves protect coastlines and support local wildlife in many regions."
                ],
                bridge_to_lesson="You will study those choices today.",
            )
        },
    )

    assert result.passed is True
    assert result.warnings == []


def test_validate_answer_leakage_ignores_newly_excluded_sections() -> None:
    """model_passage, check_in, learning_targets, strategy_list, self_assessment
    must not trigger leakage warnings even when they contain a quoted phrase."""
    answer_key = build_answer_key()
    leaking_text = "Mangroves protect coastlines from storm surges in coastal areas."

    result = validate_answer_leakage(
        answer_key=answer_key,
        section_payloads={
            "model_passage": {
                "passage": [leaking_text],
                "evidence_focus": "See above.",
            },
            "check_in": {"questions": [{"question": leaking_text}]},
            "learning_targets": {"skills": [{"description": leaking_text}]},
            "strategy_list": {
                "strategies": [{"title": "Strategy", "steps": [leaking_text]}]
            },
            "self_assessment": {"rows": [{"skill": leaking_text, "got_it": "Yes"}]},
        },
    )

    assert result.passed is True
    assert result.warnings == []


def test_validate_answer_leakage_ignores_assessment_questions_quotes() -> None:
    result = validate_answer_leakage(
        answer_key=build_answer_key(),
        section_payloads={
            "assessment_questions": AssessmentQuestionsSection(
                title="Assessment Questions",
                passage_title="Assessment Passage",
                questions=[
                    AssessmentQuestionItem(
                        number=1,
                        question="Why are mangroves important?",
                        expected_response_type="short_response",
                        evidence_hint="Look for the part of the passage about coastal protection.",
                    )
                ],
            )
        },
    )

    assert result.passed is True
    assert result.failed_sections == []
    assert result.failures == {}
    assert result.warnings == []
