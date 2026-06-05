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
                evidence_quote='"protect coastlines"',
            )
        ],
        step_up_answer=StepUpAnswer(
            challenge_response="Use details from the article to explain the purpose.",
            required_evidence=['"protect coastlines"'],
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
                    "An author may mention how mangroves protect coastlines before students answer the assessment.",
                ],
                bridge_to_lesson="You will study how details shape a reader's thinking.",
            )
        },
    )

    assert result.passed is True
    assert result.failed_sections == []
    assert result.failures == {}
    assert any("intro" in warning for warning in result.warnings)
    assert any("protect coastlines" in warning for warning in result.warnings)


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
