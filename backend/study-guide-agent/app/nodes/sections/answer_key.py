"""Answer key section node for the study guide workflow."""

# ruff: noqa: E402

from __future__ import annotations

import re
from collections.abc import Callable
from difflib import SequenceMatcher
from typing import Any, cast

from app.app_utils.adk_compat import ensure_google_adk_beta_compat

ensure_google_adk_beta_compat()

from google.adk.workflow import node

from app.nodes.base import TEMP_ANSWER_KEY, call_gemini
from app.nodes.sections import _parse_section_response
from app.prompts.system_prompt import build_system_prompt
from app.prompts.templates.answer_key import build_prompt as build_answer_key_prompt
from app.types import Blueprint, GenerateRequest

QUOTED_PHRASE_PATTERN = re.compile(r'"([^"\n]+)"|“([^”\n]+)”')


def _extract_quoted_phrases(value: str) -> list[str]:
    phrases: list[str] = []
    for straight_quote, curly_quote in QUOTED_PHRASE_PATTERN.findall(value):
        phrase = straight_quote or curly_quote
        if phrase:
            phrases.append(phrase)
    return phrases


def _normalize_evidence_quote(value: str) -> str:
    quoted_phrases = _extract_quoted_phrases(value)
    if quoted_phrases:
        return quoted_phrases[0]
    return value.strip()


def _collect_quote_candidates(assessment_passage: dict[str, Any]) -> list[str]:
    passage_lines = [
        str(item).strip()
        for item in assessment_passage.get("passage", [])
        if str(item).strip()
    ]
    passage_text = "\n".join(passage_lines)

    candidates: list[str] = []
    for clue in assessment_passage.get("evidence_clues", []):
        normalized_clue = str(clue).strip()
        if (
            normalized_clue
            and normalized_clue in passage_text
            and normalized_clue not in candidates
        ):
            candidates.append(normalized_clue)

    for paragraph in passage_lines:
        if paragraph and paragraph not in candidates:
            candidates.append(paragraph)

        for fragment in paragraph.replace(";", ",").split(","):
            normalized_fragment = fragment.strip()
            if (
                len(normalized_fragment.split()) >= 3
                and normalized_fragment in passage_text
                and normalized_fragment not in candidates
            ):
                candidates.append(normalized_fragment)

    return candidates


def _collect_evidence_clues(assessment_passage: dict[str, Any]) -> list[str]:
    passage_text = "\n".join(assessment_passage.get("passage", []))
    clues: list[str] = []
    for clue in assessment_passage.get("evidence_clues", []):
        normalized_clue = str(clue).strip()
        if (
            normalized_clue
            and normalized_clue in passage_text
            and normalized_clue not in clues
        ):
            clues.append(normalized_clue)
    return clues


def _fallback_quote_candidate(
    *,
    index: int,
    evidence_clues: list[str],
    quote_candidates: list[str],
    used_candidates: set[str],
) -> str | None:
    if index < len(evidence_clues) and evidence_clues[index] not in used_candidates:
        return evidence_clues[index]

    for clue in evidence_clues:
        if clue not in used_candidates:
            return clue

    for candidate in quote_candidates:
        if candidate not in used_candidates:
            return candidate

    return None


def _quote_token_overlap_score(candidate: str, target: str) -> float:
    candidate_tokens = {
        token for token in re.findall(r"[A-Za-z0-9']+", candidate.lower()) if token
    }
    target_tokens = {
        token for token in re.findall(r"[A-Za-z0-9']+", target.lower()) if token
    }
    if not candidate_tokens or not target_tokens:
        return 0.0
    return len(candidate_tokens & target_tokens) / len(candidate_tokens | target_tokens)


def _best_matching_quote_candidate(
    targets: list[str], quote_candidates: list[str]
) -> str | None:
    best_candidate: str | None = None
    best_score = 0.0

    for candidate in quote_candidates:
        for target in targets:
            normalized_target = target.strip()
            if not normalized_target:
                continue
            sequence_score = SequenceMatcher(
                None, candidate.lower(), normalized_target.lower()
            ).ratio()
            overlap_score = _quote_token_overlap_score(candidate, normalized_target)
            score = max(sequence_score, overlap_score)
            if score > best_score:
                best_score = score
                best_candidate = candidate

    if best_score >= 0.4:
        return best_candidate
    return None


def _quote_text(value: str) -> str:
    return f'"{value}"'


def _strip_nonverbatim_quotes(value: str, exact_quote: str | None) -> str:
    cleaned_value = value
    for phrase in _extract_quoted_phrases(value):
        if exact_quote is not None and phrase == exact_quote:
            continue
        cleaned_value = cleaned_value.replace(f'"{phrase}"', phrase).replace(
            f"“{phrase}”", phrase
        )
    return cleaned_value


def _find_assessment_answer_source(
    raw_answers: list[dict[str, Any]], index: int, question_spec: dict[str, Any]
) -> dict[str, Any]:
    question_number = question_spec.get("number")
    question_text = str(question_spec.get("question", "")).strip()

    for answer in raw_answers:
        if answer.get("question_number") == question_number:
            return answer

    for answer in raw_answers:
        if str(answer.get("question", "")).strip() == question_text:
            return answer

    if 0 <= index < len(raw_answers):
        return raw_answers[index]

    return {}


def _find_check_in_answer_source(
    raw_answers: list[dict[str, Any]], index: int, question_spec: dict[str, Any]
) -> dict[str, Any]:
    question_number = question_spec.get("number")
    question_text = str(question_spec.get("question", "")).strip()

    for answer in raw_answers:
        if str(answer.get("question", "")).strip() == question_text:
            return answer

    for answer in raw_answers:
        if answer.get("question_number") == question_number:
            return answer

    best_answer: dict[str, Any] | None = None
    best_score = 0.0

    for answer in raw_answers:
        candidate_question = str(answer.get("question", "")).strip()
        if not candidate_question or not question_text:
            continue
        score = SequenceMatcher(
            None, candidate_question.lower(), question_text.lower()
        ).ratio()
        if score > best_score:
            best_score = score
            best_answer = answer

    if best_answer is not None and best_score >= 0.6:
        return best_answer

    if 0 <= index < len(raw_answers):
        return raw_answers[index]

    return {}


def _build_assessment_possible_answer(
    *,
    answer_expectation: str,
    fallback_answer: str,
    quote_candidate: str | None,
) -> str:
    base_answer = answer_expectation.strip() or fallback_answer.strip()
    base_answer = _strip_nonverbatim_quotes(base_answer, quote_candidate)
    if quote_candidate is None:
        return base_answer

    if (
        _quote_text(quote_candidate) in base_answer
        or f"“{quote_candidate}”" in base_answer
    ):
        return base_answer

    trimmed_base = base_answer.rstrip(" .")
    if not trimmed_base:
        return f"Evidence from the passage: {_quote_text(quote_candidate)}."

    return f"{trimmed_base}. Evidence from the passage: {_quote_text(quote_candidate)}."


def _normalize_check_in_answers(
    answer_key: dict[str, Any],
    check_in: dict[str, Any],
    model_passage: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    normalized_answers: list[dict[str, Any]] = []
    raw_answers = [dict(answer) for answer in answer_key.get("check_in_answers", [])]
    model_passage_text = (
        "\n".join(model_passage.get("passage", [])) if model_passage else ""
    )
    quote_candidates = _collect_quote_candidates(model_passage or {})
    used_candidates: set[str] = set()

    for index, raw_question_spec in enumerate(check_in.get("questions", [])):
        question_spec = dict(raw_question_spec)
        answer = _find_check_in_answer_source(raw_answers, index, question_spec)
        possible_answer = str(answer.get("possible_answer", "")).strip()
        raw_evidence_quote = answer.get("evidence_quote")
        evidence_quote = (
            str(raw_evidence_quote).strip() if raw_evidence_quote is not None else ""
        )
        normalized_evidence_quote = _normalize_evidence_quote(evidence_quote)
        should_normalize_quote = bool(normalized_evidence_quote) and (
            normalized_evidence_quote != "N/A"
        )
        quoted_phrases = _extract_quoted_phrases(possible_answer)
        best_candidate = None

        if should_normalize_quote:
            best_candidate = next(
                (phrase for phrase in quoted_phrases if phrase in model_passage_text),
                None,
            )

        if (
            best_candidate is None
            and should_normalize_quote
            and normalized_evidence_quote in model_passage_text
        ):
            best_candidate = normalized_evidence_quote

        if best_candidate is None and should_normalize_quote and model_passage_text:
            match_targets = [
                str(question_spec.get("question", "")),
                possible_answer,
                str(question_spec.get("evidence_hint", "")),
                normalized_evidence_quote,
            ]
            best_candidate = _best_matching_quote_candidate(
                match_targets, quote_candidates
            )

        if best_candidate is None and should_normalize_quote:
            best_candidate = _fallback_quote_candidate(
                index=index,
                evidence_clues=[],
                quote_candidates=quote_candidates,
                used_candidates=used_candidates,
            )

        if best_candidate is not None:
            used_candidates.add(best_candidate)
        normalized_answers.append(
            {
                "question_number": question_spec.get(
                    "number", answer.get("question_number", index + 1)
                ),
                "question": str(question_spec.get("question", "")).strip()
                or str(answer.get("question", "")).strip(),
                "possible_answer": possible_answer,
                "evidence_quote": (
                    _quote_text(best_candidate)
                    if best_candidate is not None
                    else (evidence_quote if evidence_quote else "N/A")
                ),
            }
        )

    if normalized_answers:
        return normalized_answers

    for index, raw_answer in enumerate(answer_key.get("check_in_answers", [])):
        answer = dict(raw_answer)
        evidence_quote = answer.get("evidence_quote")
        normalized_answers.append(
            {
                "question_number": answer.get("question_number", index + 1),
                "question": str(answer.get("question", "")).strip(),
                "possible_answer": str(answer.get("possible_answer", "")).strip(),
                "evidence_quote": str(evidence_quote).strip()
                if evidence_quote
                else "N/A",
            }
        )

    return normalized_answers


def normalize_answer_key_payload(
    answer_key: dict[str, Any],
    check_in: dict[str, Any],
    assessment_passage: dict[str, Any],
    assessment_questions: dict[str, Any],
    model_passage: dict[str, Any] | None = None,
) -> dict[str, Any]:
    passage_text = "\n".join(assessment_passage.get("passage", []))
    quote_candidates = _collect_quote_candidates(assessment_passage)
    evidence_clues = _collect_evidence_clues(assessment_passage)
    raw_answers = [dict(answer) for answer in answer_key.get("assessment_answers", [])]
    normalized_answers: list[dict[str, Any]] = []
    used_candidates: set[str] = set()

    for index, raw_question_spec in enumerate(
        assessment_questions.get("questions", [])
    ):
        question_spec = dict(raw_question_spec)
        answer = _find_assessment_answer_source(raw_answers, index, question_spec)
        possible_answer = str(answer.get("possible_answer", "")).strip()
        evidence_quote = str(answer.get("evidence_quote", "")).strip()
        normalized_evidence_quote = _normalize_evidence_quote(evidence_quote)
        quoted_phrases = _extract_quoted_phrases(possible_answer)
        exact_quoted_phrase = next(
            (phrase for phrase in quoted_phrases if phrase in passage_text),
            None,
        )

        best_candidate = exact_quoted_phrase
        if (
            best_candidate is None
            and normalized_evidence_quote
            and normalized_evidence_quote in passage_text
        ):
            best_candidate = normalized_evidence_quote
        if best_candidate is None:
            match_targets = [
                str(question_spec.get("question", "")),
                str(question_spec.get("answer_expectation", "")),
                str(question_spec.get("evidence_requirement", "")),
            ]
            best_candidate = _best_matching_quote_candidate(
                match_targets, quote_candidates
            )
        if best_candidate is None:
            best_candidate = _fallback_quote_candidate(
                index=index,
                evidence_clues=evidence_clues,
                quote_candidates=quote_candidates,
                used_candidates=used_candidates,
            )
        if best_candidate is not None:
            used_candidates.add(best_candidate)

        normalized_answers.append(
            {
                "question_number": question_spec.get(
                    "number", answer.get("question_number", index + 1)
                ),
                "question": str(question_spec.get("question", "")).strip()
                or str(answer.get("question", "")).strip(),
                "possible_answer": _build_assessment_possible_answer(
                    answer_expectation=str(question_spec.get("answer_expectation", "")),
                    fallback_answer=possible_answer,
                    quote_candidate=best_candidate,
                ),
                "evidence_quote": (
                    _quote_text(best_candidate)
                    if best_candidate is not None
                    else evidence_quote
                ),
            }
        )

    normalized_check_in_answers = _normalize_check_in_answers(
        answer_key,
        check_in,
        model_passage,
    )

    if not normalized_answers:
        return {
            **answer_key,
            "check_in_answers": normalized_check_in_answers,
        }

    return {
        **answer_key,
        "check_in_answers": normalized_check_in_answers,
        "assessment_answers": normalized_answers,
    }


def _normalize_assessment_answer_quotes(
    answer_key: dict[str, Any],
    check_in: dict[str, Any],
    assessment_passage: dict[str, Any],
    assessment_questions: dict[str, Any],
    model_passage: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return normalize_answer_key_payload(
        answer_key,
        check_in,
        assessment_passage,
        assessment_questions,
        model_passage,
    )


async def generate_answer_key(
    request: GenerateRequest,
    blueprint: Blueprint,
    model_passage: dict[str, Any],
    check_in: dict[str, Any],
    assessment_passage: dict[str, Any],
    assessment_questions: dict[str, Any],
    step_up: dict[str, Any],
) -> dict[str, Any]:
    system_prompt = build_system_prompt(request)
    user_prompt = build_answer_key_prompt(
        {
            "model_passage": model_passage,
            "check_in": check_in,
            "assessment_passage": assessment_passage,
            "assessment_questions": assessment_questions,
            "step_up": step_up,
        },
        blueprint,
        request,
    )
    response_text = await call_gemini(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=TEMP_ANSWER_KEY,
        context_label="answer_key",
    )
    parsed_response = _parse_section_response(response_text, "answer_key")
    return _normalize_assessment_answer_quotes(
        parsed_response,
        check_in,
        assessment_passage,
        assessment_questions,
        model_passage,
    )


answer_key_node = cast(
    Callable[
        [
            GenerateRequest,
            Blueprint,
            dict[str, Any],
            dict[str, Any],
            dict[str, Any],
            dict[str, Any],
            dict[str, Any],
        ],
        Any,
    ],
    node(generate_answer_key),
)
