from __future__ import annotations

from app.types import (
    AnswerKeyItem,
    AnswerKeySection,
    AssessmentPassageSection,
    StepUpAnswer,
)
from app.validators.hard.answer_key_quotes import validate_answer_key_quotes


def build_answer_key(*, possible_answer: str) -> AnswerKeySection:
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
                possible_answer=possible_answer,
                evidence_quote='"protect coastlines"',
            )
        ],
        step_up_answer=StepUpAnswer(
            challenge_response="Use details from the article to explain the purpose.",
            required_evidence=['"protect coastlines"'],
        ),
        teacher_note="Accept equivalent answers with direct evidence.",
    )


def build_assessment_passage() -> AssessmentPassageSection:
    return AssessmentPassageSection(
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


def test_validate_answer_key_quotes_passes_for_verbatim_assessment_quote() -> None:
    result = validate_answer_key_quotes(
        answer_key=build_answer_key(
            possible_answer='The author wants to inform readers because "protect coastlines" explains why mangroves matter.'
        ),
        assessment_passage=build_assessment_passage(),
    )

    assert result.passed is True
    assert result.failed_sections == []
    assert result.failures == {}


def test_validate_answer_key_quotes_fails_when_assessment_answer_has_no_quote() -> None:
    result = validate_answer_key_quotes(
        answer_key=build_answer_key(
            possible_answer="The author wants to inform readers because the passage explains why mangroves matter."
        ),
        assessment_passage=build_assessment_passage(),
    )

    assert result.passed is False
    assert result.failed_sections == ["answer_key"]
    assert any(
        "must include at least one quoted phrase" in message
        for message in result.failures["answer_key"]
    )


def test_validate_answer_key_quotes_fails_when_quote_is_not_verbatim() -> None:
    result = validate_answer_key_quotes(
        answer_key=build_answer_key(
            possible_answer='The author wants to inform readers because "protects coastlines" explains why mangroves matter.'
        ),
        assessment_passage=build_assessment_passage(),
    )

    assert result.passed is False
    assert result.failed_sections == ["answer_key"]
    assert any(
        "protects coastlines" in message for message in result.failures["answer_key"]
    )
