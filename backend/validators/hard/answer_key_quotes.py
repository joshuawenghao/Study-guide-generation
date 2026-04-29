"""
Hard validator: answer_key_quotes

Rule: Each possible answer in the answer key must contain a verbatim phrase —
a contiguous sequence of at least MIN_PHRASE_WORDS consecutive words — that
also appears verbatim in the assessment passage text. Paraphrasing is not
permitted.

Match type: word-level n-gram matching. All n-grams of at least
MIN_PHRASE_WORDS consecutive words are extracted from the passage; the
answer must contain at least one of them as a contiguous substring.
Comparison is case-sensitive.

Failure unit: one failure message per possible answer that contains no
verbatim phrase from the assessment passage.
"""

from __future__ import annotations

import re

from backend.types import AnswerKeyOutput, AssessmentPassageOutput

# Minimum number of consecutive words that must appear verbatim in both the
# answer text and the assessment passage for the answer to be considered a
# valid verbatim quote. Three words balances precision against accidental
# common-word matches.
_MIN_PHRASE_WORDS = 3


def _tokenize(text: str) -> list[str]:
    """
    Split ``text`` into word tokens, stripping leading/trailing punctuation
    from each token so that, for example, ``"passage."`` and ``"passage"``
    are treated as the same word.
    """
    return [re.sub(r"^\W+|\W+$", "", w) for w in text.split() if re.sub(r"^\W+|\W+$", "", w)]


def _word_ngrams(text: str, n: int) -> set[str]:
    """
    Return the set of all contiguous n-word phrases extracted from ``text``.

    Returns an empty set when the text contains fewer than ``n`` word tokens.
    """
    words = _tokenize(text)
    if len(words) < n:
        return set()
    return {" ".join(words[i : i + n]) for i in range(len(words) - n + 1)}


def _contains_verbatim_phrase(answer_text: str, passage_text: str) -> bool:
    """
    Return True if ``answer_text`` contains at least one contiguous sequence
    of >= _MIN_PHRASE_WORDS words that also appears in ``passage_text``.
    """
    passage_ngrams = _word_ngrams(passage_text, _MIN_PHRASE_WORDS)
    answer_ngrams = _word_ngrams(answer_text, _MIN_PHRASE_WORDS)
    return bool(passage_ngrams & answer_ngrams)


def check_answer_key_quotes(
    answer_key: AnswerKeyOutput,
    assessment_passage: AssessmentPassageOutput,
) -> list[str]:
    """
    Hard validator — answer_key_quotes.

    Parameters
    ----------
    answer_key:
        The parsed output of the answer_key section node.
    assessment_passage:
        The parsed output of the assessment_passage section node.

    Returns
    -------
    list[str]
        Failure messages, one per possible answer that contains no verbatim
        phrase from the assessment passage.
        An empty list means all answers are valid.
    """
    passage_text = assessment_passage.text
    failures: list[str] = []

    for item in answer_key.items:
        for possible_answer in item.possible_answers:
            if not _contains_verbatim_phrase(possible_answer, passage_text):
                failures.append(
                    f"Answer key item {item.question_number}, possible answer "
                    f"'{possible_answer}' contains no verbatim phrase from the "
                    "assessment passage."
                )
    return failures
