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

from app.nodes.base import (
    MAX_ANSWER_KEY_OUTPUT_TOKENS,
    TEMP_ANSWER_KEY,
    call_gemini,
    call_gemini_and_parse_json,
)
from app.nodes.sections import _parse_section_response
from app.prompts.runtime import (
    build_runtime_section_prompt,
    build_runtime_system_prompt,
)
from app.prompts.templates.answer_key import build_prompt as build_answer_key_prompt
from app.types import Blueprint, GenerateRequest, StudyGuideRequest

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


def _finalize_sentence(value: str) -> str:
    normalized = re.sub(r"\s+", " ", value).strip()
    if not normalized:
        return ""
    if normalized[-1] in ".!?":
        return normalized
    return f"{normalized}."


def _remove_inline_quote_reference(value: str, quote_candidate: str | None) -> str:
    cleaned_value = value
    if quote_candidate is not None:
        quoted_exact = re.escape(_quote_text(quote_candidate))
        curly_exact = re.escape(f"“{quote_candidate}”")
        cleaned_value = re.sub(
            rf"\s*(?:Evidence from the passage|Quoted evidence)\s*:\s*(?:{quoted_exact}|{curly_exact})[^.!?]*",
            "",
            cleaned_value,
            flags=re.IGNORECASE,
        )
        cleaned_value = re.sub(
            rf"\s*(?:because|since|as|by citing|by using|using|with)\s+(?:{quoted_exact}|{curly_exact})[^.!?]*",
            "",
            cleaned_value,
            flags=re.IGNORECASE,
        )
        cleaned_value = cleaned_value.replace(_quote_text(quote_candidate), "").replace(
            f"“{quote_candidate}”", ""
        )

    cleaned_value = re.sub(r"\s+", " ", cleaned_value).strip(" ,;:-")
    return cleaned_value


def _looks_like_guidance_not_answer(value: str) -> bool:
    normalized = value.casefold().strip()
    if not normalized:
        return True

    guidance_fragments = (
        "quote this exact phrase",
        "use one exact phrase",
        "use evidence from the passage",
        "support it with passage evidence",
        "support your answer",
        "look for the part of the passage",
        "look for the phrase",
        "look for the specific detail",
        "choose the best answer",
        "answer the question clearly",
    )
    return any(fragment in normalized for fragment in guidance_fragments)


def _default_assessment_possible_answer(question_text: str) -> str:
    normalized_question = question_text.casefold()
    if (
        "author's purpose" in normalized_question
        or "authors purpose" in normalized_question
    ):
        return "The author wants to inform the reader using details from the passage."
    if normalized_question.startswith("how ") or " how " in normalized_question:
        return "The passage details directly support the explanation in the answer."
    if normalized_question.startswith("why ") or " why " in normalized_question:
        return "The passage explains the reason directly in its details."
    return "The correct answer should respond directly to the question using the passage details."


def _collect_evidence_clues(assessment_passage: dict[str, Any]) -> list[str]:
    clues: list[str] = []
    for clue in assessment_passage.get("evidence_clues", []):
        normalized_clue = str(clue).strip()
        if normalized_clue and normalized_clue not in clues:
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
        candidate = raw_answers[index]
        candidate_question = str(candidate.get("question", "")).strip()
        if not candidate_question:
            return candidate
        similarity = SequenceMatcher(
            None, candidate_question.lower(), question_text.lower()
        ).ratio()
        if similarity >= 0.45:
            return candidate

    return {}


def _find_check_in_answer_source(
    raw_answers: list[dict[str, Any]],
    index: int,
    question_spec: dict[str, Any],
    used_indices: set[int],
) -> tuple[int | None, dict[str, Any]]:
    question_number = question_spec.get("number")
    question_text = str(question_spec.get("question", "")).strip()
    evidence_hint = str(question_spec.get("evidence_hint", "")).strip()

    for answer_index, answer in enumerate(raw_answers):
        if answer_index in used_indices:
            continue
        if str(answer.get("question", "")).strip() == question_text:
            return answer_index, answer

    best_answer_index: int | None = None
    best_answer: dict[str, Any] | None = None
    best_score = -1.0

    for answer_index, answer in enumerate(raw_answers):
        if answer_index in used_indices:
            continue

        candidate_question = str(answer.get("question", "")).strip()
        possible_answer = str(answer.get("possible_answer", "")).strip()
        evidence_quote = str(answer.get("evidence_quote", "")).strip()
        combined_source = " ".join(
            part
            for part in [candidate_question, possible_answer, evidence_quote]
            if part
        )

        score = 0.0
        if answer.get("question_number") == question_number:
            score += 0.2
        if candidate_question and question_text:
            score += SequenceMatcher(
                None, candidate_question.lower(), question_text.lower()
            ).ratio()
        if combined_source and question_text:
            score += _quote_token_overlap_score(combined_source, question_text) * 2.0
        if combined_source and evidence_hint:
            score += _quote_token_overlap_score(combined_source, evidence_hint) * 1.5

        if score > best_score:
            best_score = score
            best_answer = answer
            best_answer_index = answer_index

    if best_answer is not None and best_score >= 0.6:
        return best_answer_index, best_answer

    if 0 <= index < len(raw_answers) and index not in used_indices:
        return index, raw_answers[index]

    for answer_index, answer in enumerate(raw_answers):
        if answer_index not in used_indices:
            return answer_index, answer

    return None, {}


def _build_assessment_possible_answer(
    *,
    question_text: str,
    fallback_answer: str,
    quote_candidate: str | None,
    source_matches_question: bool,
) -> str:
    candidate_answers = [fallback_answer.strip() if source_matches_question else ""]

    for candidate in candidate_answers:
        if not candidate:
            continue
        cleaned_candidate = _strip_nonverbatim_quotes(candidate, quote_candidate)
        cleaned_candidate = _remove_inline_quote_reference(
            cleaned_candidate,
            quote_candidate,
        )
        cleaned_candidate = _finalize_sentence(cleaned_candidate)
        if cleaned_candidate and not _looks_like_guidance_not_answer(cleaned_candidate):
            return cleaned_candidate

    return _default_assessment_possible_answer(question_text)


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
    used_indices: set[int] = set()
    used_candidates: set[str] = set()

    for index, raw_question_spec in enumerate(check_in.get("questions", [])):
        question_spec = dict(raw_question_spec)
        answer_index, answer = _find_check_in_answer_source(
            raw_answers,
            index,
            question_spec,
            used_indices,
        )
        if answer_index is not None:
            used_indices.add(answer_index)
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
        source_question_number = answer.get("question_number")
        source_question_text = str(answer.get("question", "")).strip()
        upstream_question_text = str(question_spec.get("question", "")).strip()
        question_similarity = (
            SequenceMatcher(
                None,
                source_question_text.lower(),
                upstream_question_text.lower(),
            ).ratio()
            if source_question_text and upstream_question_text
            else 0.0
        )
        source_matches_question = (
            source_question_text == upstream_question_text
            or question_similarity >= 0.75
            or (
                not source_question_text
                and source_question_number == question_spec.get("number")
            )
        )
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
                str(question_spec.get("evidence_hint", "")),
                str(question_spec.get("expected_response_type", "")),
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
                    question_text=str(question_spec.get("question", "")),
                    fallback_answer=possible_answer,
                    quote_candidate=best_candidate,
                    source_matches_question=source_matches_question,
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
    request: StudyGuideRequest,
    blueprint: Blueprint,
    model_passage: dict[str, Any],
    check_in: dict[str, Any],
    assessment_passage: dict[str, Any],
    assessment_questions: dict[str, Any],
    step_up: dict[str, Any],
) -> dict[str, Any]:
    answer_key_spec = {
        "model_passage": model_passage,
        "check_in": check_in,
        "assessment_passage": assessment_passage,
        "assessment_questions": assessment_questions,
        "step_up": step_up,
    }
    system_prompt = build_runtime_system_prompt(request)
    user_prompt = build_runtime_section_prompt(
        request=request,
        blueprint=blueprint,
        prompt_builder=build_answer_key_prompt,
        context_label="answer_key",
        spec=answer_key_spec,
    )
    parsed_response = await call_gemini_and_parse_json(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=TEMP_ANSWER_KEY,
        parse_response=lambda response_text: _parse_section_response(
            response_text,
            "answer_key",
        ),
        call_model=call_gemini,
        max_output_tokens=MAX_ANSWER_KEY_OUTPUT_TOKENS,
        context_label="answer_key",
    )
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
