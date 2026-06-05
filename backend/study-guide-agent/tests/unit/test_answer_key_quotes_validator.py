from __future__ import annotations

from app.types import (
    AnswerKeyItem,
    AnswerKeySection,
    AssessmentPassageSection,
    ModelPassageSection,
    StepUpAnswer,
)
from app.validators.hard.answer_key_quotes import validate_answer_key_quotes


def build_answer_key(
    *, possible_answer: str, evidence_quote: str = '"protect coastlines"'
) -> AnswerKeySection:
    return AnswerKeySection(
        title="Answer Key",
        check_in_answers=[
            AnswerKeyItem(
                question_number=1,
                question="What clue shows the nurse used standard precautions?",
                possible_answer="She performs hand hygiene before touching the patient.",
                evidence_quote='"Before touching Mr. Reyes, Nurse Maria performs hand hygiene using an alcohol-based hand rub."',
            )
        ],
        assessment_answers=[
            AnswerKeyItem(
                question_number=2,
                question="What is the author's purpose in this article?",
                possible_answer=possible_answer,
                evidence_quote=evidence_quote,
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


def build_model_passage() -> ModelPassageSection:
    return ModelPassageSection(
        title="Model Passage",
        topic_domain="hospital admission",
        genre="narrative",
        passage=[
            "Before touching Mr. Reyes, Nurse Maria performs hand hygiene using an alcohol-based hand rub.",
            "She ensures that all used supplies are disposed of properly in designated containers after use, maintaining a clean and safe environment.",
            "Maintaining a sterile field when administering medications is another crucial aspect of infection prevention that Nurse Maria will consider later when administering medication.",
        ],
        text_features=["sequence"],
        evidence_focus="How standard precautions appear during routine care.",
    )


def test_validate_answer_key_quotes_passes_for_verbatim_assessment_quote() -> None:
    result = validate_answer_key_quotes(
        answer_key=build_answer_key(
            possible_answer="The author wants to inform readers about why mangroves matter."
        ),
        assessment_passage=build_assessment_passage(),
        model_passage=build_model_passage(),
    )

    assert result.passed is True
    assert result.failed_sections == []
    assert result.failures == {}


def test_validate_answer_key_quotes_fails_when_assessment_answer_has_no_evidence_quote() -> (
    None
):
    result = validate_answer_key_quotes(
        answer_key=build_answer_key(
            possible_answer="The author wants to inform readers because the passage explains why mangroves matter.",
            evidence_quote="",
        ),
        assessment_passage=build_assessment_passage(),
        model_passage=build_model_passage(),
    )

    assert result.passed is False
    assert result.failed_sections == ["answer_key"]
    assert any(
        "must include an evidence_quote" in message
        for message in result.failures["answer_key"]
    )


def test_validate_answer_key_quotes_fails_when_quote_is_not_verbatim() -> None:
    result = validate_answer_key_quotes(
        answer_key=build_answer_key(
            possible_answer="The author wants to inform readers about why mangroves matter.",
            evidence_quote='"protects coastlines"',
        ),
        assessment_passage=build_assessment_passage(),
        model_passage=build_model_passage(),
    )

    assert result.passed is False
    assert result.failed_sections == ["answer_key"]
    assert any(
        "protects coastlines" in message for message in result.failures["answer_key"]
    )


def test_validate_answer_key_quotes_fails_when_check_in_evidence_is_not_verbatim() -> (
    None
):
    answer_key = build_answer_key(
        possible_answer="The author wants to inform readers about why mangroves matter."
    )
    answer_key.check_in_answers = [
        AnswerKeyItem(
            question_number=1,
            question="What clue shows the nurse used standard precautions?",
            possible_answer="She washed her hands with soap and water before touching the patient.",
            evidence_quote='"Nurse Maria washes her hands with soap and water before touching the patient."',
        )
    ]

    result = validate_answer_key_quotes(
        answer_key=answer_key,
        assessment_passage=build_assessment_passage(),
        model_passage=build_model_passage(),
    )

    assert result.passed is False
    assert result.failed_sections == ["answer_key"]
    assert any(
        "does not appear verbatim in the model passage" in message
        for message in result.failures["answer_key"]
    )
