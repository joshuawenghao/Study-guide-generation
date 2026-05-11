from __future__ import annotations

from app.types import (
    Blueprint,
    CoreExplainerPoint,
    CoreExplainerSection,
    IntroSection,
    LearningTarget,
    SubCompetency,
    TopicDomains,
    VocabEntry,
    VocabularyEntrySectionItem,
    VocabularySection,
)
from app.validators.hard.vocab_presence import validate_vocab_presence


def build_blueprint(*words: str) -> Blueprint:
    return Blueprint(
        lesson_id="lesson-1",
        title="Author's Purpose",
        essential_question="Why does an author make certain choices?",
        introduction_hook="Three texts can persuade, inform, or entertain in different ways.",
        learning_targets=[
            LearningTarget(
                number=1,
                bloom_verb="identify",
                objective="Identify how authors signal purpose.",
            )
        ],
        vocabulary=[
            VocabEntry(
                word=word,
                definition=f"Definition for {word}",
                example_sentence=f"An example sentence using {word}.",
            )
            for word in words
        ],
        topic_domains=TopicDomains(
            model_passage="animals",
            assessment_passage="space",
            entertain_example="games",
            inform_example="science",
            persuade_example="community",
        ),
        sub_competencies=[SubCompetency(id="sc-1", label="Purpose clues")],
        core_concept="Authors choose features that match their purpose.",
    )


def test_validate_vocab_presence_passes_when_words_appear_in_body_sections() -> None:
    blueprint = build_blueprint("audience", "evidence")

    result = validate_vocab_presence(
        blueprint=blueprint,
        section_payloads={
            "intro": IntroSection(
                title="Introduction",
                hook="Think about the audience for a school poster.",
                essential_question="Why do authors consider audience and purpose?",
                paragraphs=[
                    "An author chooses evidence to support the message.",
                ],
                bridge_to_lesson="You will analyze those choices today.",
            ),
            "core_explainer": CoreExplainerSection(
                title="Core Explainer",
                overview="Purpose shapes each detail in the text.",
                explained_points=[
                    CoreExplainerPoint(
                        sub_competency_id="sc-1",
                        sub_competency_label="Purpose clues",
                        explanation="Writers think about AUDIENCE before choosing details.",
                        real_world_connection="Posters and speeches both rely on evidence.",
                    )
                ],
                closing_summary="Purpose, audience, and evidence work together.",
            ),
        },
    )

    assert result.passed is True
    assert result.failed_sections == []
    assert result.failures == {}


def test_validate_vocab_presence_ignores_vocabulary_and_answer_key_text() -> None:
    blueprint = build_blueprint("inference")

    result = validate_vocab_presence(
        blueprint=blueprint,
        section_payloads={
            "intro": IntroSection(
                title="Introduction",
                hook="Start with a short scenario.",
                essential_question="How do readers explain purpose?",
                paragraphs=["Readers gather clues before answering questions."],
                bridge_to_lesson="The lesson builds toward evidence-based reading.",
            ),
            "vocabulary": VocabularySection(
                title="Vocabulary",
                entries=[
                    VocabularyEntrySectionItem(
                        word="inference",
                        part_of_speech="noun",
                        definition="A conclusion based on evidence.",
                        example_sentence="Your inference should come from clues in the text.",
                    )
                ],
            ),
            "answer_key": {
                "assessment_answers": [
                    {
                        "question_number": 1,
                        "question": "What is the answer?",
                        "possible_answer": "An inference explains the author's likely purpose.",
                        "evidence_quote": "supports the answer",
                    }
                ]
            },
        },
    )

    assert result.passed is False
    assert result.failed_sections == ["intro"]
    assert "intro" in result.failures
    assert any("inference" in message for message in result.failures["intro"])
