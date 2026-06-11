"""Shared helpers for study guide section nodes."""

from __future__ import annotations

import html
import json
import re
from collections.abc import Callable
from typing import Any

from app.nodes.base import (
    MAX_OUTPUT_TOKENS,
    TEMP_SECTION,
    JSONResponseParseError,
    call_gemini,
    call_gemini_and_parse_json,
)
from app.prompts.runtime import (
    build_runtime_section_prompt,
    build_runtime_system_prompt,
)
from app.types import Blueprint, GenerateRequest, StudyGuideRequest

_INVALID_JSON_ESCAPE_PATTERN = re.compile(r'(?<!\\)\\(?!["\\/bfnrtu])')
_INLINE_QUOTED_LIST_ANNOTATION_PATTERN = re.compile(
    r'(?<=[A-Za-z0-9.!?])\s+\[(?:"[^"\n]+"(?:,\s*"[^"\n]+")*)\]'
)
_CODE_LIKE_INLINE_ANNOTATION_PATTERN = re.compile(
    r"\[(?=[^\]\n]*\+)(?:\s*(?:\"(?:\\.|[^\"\n])*\"|'(?:\\.|[^'\n])*'|\+)\s*)+\]"
)
_MIXED_QUOTE_CONCATENATION_ANNOTATION_PATTERN = re.compile(
    r"\[\s*(?:(?:\"(?:\\.|[^\"\n])*\"|'(?:\\.|[^'\n])*')\s*\+\s*)+(?:\"(?:\\.|[^\"\n])*\"|'(?:\\.|[^'\n])*')\s*\]"
)
_UNMATCHED_MIXED_QUOTE_CONCATENATION_PREFIX_PATTERN = re.compile(
    r"\[\s*\"\s*\+\s*'\"'\s*\+\s*\"(?:\\.|[^\"\n])*\"\s*\+\s*'\"'\s*\+\s*\""
)
_UNMATCHED_QUOTE_CONCATENATION_PREFIX_PATTERN = re.compile(
    r'\[\s*(?:\\?")\s*\+\s*(?:\\?")'
)
_ESCAPED_QUOTE_CONCATENATION_ANNOTATION_PATTERN = re.compile(
    r"\[\\\"(?:\s*\+\s*'[^'\n]+'\s*\+\s*\\\")+\]"
)
_ADJACENT_ESCAPED_STRING_ANNOTATION_PATTERN = re.compile(
    r"\[\\\"(?:\s*\\\"[^\]\n]*)+\]"
)
_DOUBLE_QUOTE_PLACEHOLDER_ANNOTATION_PATTERN = re.compile(
    r'\[\s*(?:"\s*){2,}[^"\]\n]+(?:\s*"){2,}\s*\]'
)
_PARSED_STRING_PLACEHOLDER_ANNOTATION_PATTERN = re.compile(r'\s*\[\s*"[^\]\n]*\]')
_PARSED_UNMATCHED_QUOTE_CONCATENATION_PREFIX_PATTERN = re.compile(r'\s*\[\s*"\s*\+\s*"')
_CONCATENATED_QUOTED_LIST_ANNOTATION_PATTERN = re.compile(
    r'\[\s*"\s*(?:\+\s*"(?:\\.|[^"\n])*"\s*)+\+\s*"\s*\]'
)
_STANDALONE_QUOTED_LINE_PATTERN = re.compile(r'^\s*"[^"\n]*",?\s*$')
_HTML_LINE_BREAK_TAG_PATTERN = re.compile(r"(?is)<\s*(?:br|/p|/div|/li|/tr)\s*/?\s*>")
_HTML_TAG_PATTERN = re.compile(r"(?is)</?[a-z][^>]*>")
_LITERAL_DISPLAY_ESCAPES_PATTERN = re.compile(r"\\[nrt]")
_NON_LINEBREAK_CONTROL_ESCAPE_TO_PREFIX = {
    "\b": "b",
    "\f": "f",
}


def _repair_invalid_json_escapes(response_text: str) -> str:
    return _INVALID_JSON_ESCAPE_PATTERN.sub(r"\\\\", response_text)


def _strip_inline_quoted_list_annotations(response_text: str) -> str:
    return _INLINE_QUOTED_LIST_ANNOTATION_PATTERN.sub("", response_text)


def _strip_code_like_inline_annotations(response_text: str) -> str:
    return _CODE_LIKE_INLINE_ANNOTATION_PATTERN.sub("", response_text)


def _strip_mixed_quote_concatenation_annotations(response_text: str) -> str:
    return _MIXED_QUOTE_CONCATENATION_ANNOTATION_PATTERN.sub("", response_text)


def _strip_unmatched_mixed_quote_concatenation_prefixes(response_text: str) -> str:
    return _UNMATCHED_MIXED_QUOTE_CONCATENATION_PREFIX_PATTERN.sub("", response_text)


def _strip_unmatched_quote_concatenation_prefixes(response_text: str) -> str:
    return _UNMATCHED_QUOTE_CONCATENATION_PREFIX_PATTERN.sub("", response_text)


def _strip_escaped_quote_concatenation_annotations(response_text: str) -> str:
    return _ESCAPED_QUOTE_CONCATENATION_ANNOTATION_PATTERN.sub("", response_text)


def _strip_adjacent_escaped_string_annotations(response_text: str) -> str:
    return _ADJACENT_ESCAPED_STRING_ANNOTATION_PATTERN.sub("", response_text)


def _strip_double_quote_placeholder_annotations(response_text: str) -> str:
    return _DOUBLE_QUOTE_PLACEHOLDER_ANNOTATION_PATTERN.sub("", response_text)


def _strip_concatenated_quoted_list_annotations(response_text: str) -> str:
    return _CONCATENATED_QUOTED_LIST_ANNOTATION_PATTERN.sub("", response_text)


def _strip_multiline_quoted_list_annotations(response_text: str) -> str:
    lines = response_text.splitlines()
    repaired_lines: list[str] = []
    index = 0

    while index < len(lines):
        line = lines[index]
        annotation_start = line.find('["')
        if annotation_start == -1:
            repaired_lines.append(line)
            index += 1
            continue

        end_index = index + 1
        while end_index < len(lines) and '"]' not in lines[end_index]:
            end_index += 1

        if end_index >= len(lines):
            repaired_lines.append(line)
            index += 1
            continue

        annotation_lines = lines[index + 1 : end_index]
        closing_line = lines[end_index]
        closing_marker_index = closing_line.find('"]')
        if closing_marker_index == -1 or any(
            not _STANDALONE_QUOTED_LINE_PATTERN.match(annotation_line)
            for annotation_line in annotation_lines
        ):
            repaired_lines.append(line)
            index += 1
            continue

        repaired_line = (
            f"{line[:annotation_start]}{closing_line[closing_marker_index + 2 :]}"
        )
        repaired_line = re.sub(r"([.!?])\s+([.!?])", r"\1", repaired_line)
        repaired_lines.append(repaired_line)
        index = end_index + 1

    return "\n".join(repaired_lines)


def _repair_mismatched_json_closers(response_text: str) -> str:
    repaired: list[str] = []
    stack: list[str] = []
    in_string = False
    is_escaped = False

    for character in response_text:
        repaired.append(character)

        if in_string:
            if is_escaped:
                is_escaped = False
                continue
            if character == "\\":
                is_escaped = True
                continue
            if character == '"':
                in_string = False
            continue

        if character == '"':
            in_string = True
            continue
        if character in "[{":
            stack.append(character)
            continue
        if character == "]":
            while stack and stack[-1] == "{":
                repaired.insert(len(repaired) - 1, "}")
                stack.pop()
            if stack and stack[-1] == "[":
                stack.pop()
            continue
        if character == "}":
            while stack and stack[-1] == "[":
                repaired.insert(len(repaired) - 1, "]")
                stack.pop()
            if stack and stack[-1] == "{":
                stack.pop()

    while stack:
        repaired.append("}" if stack.pop() == "{" else "]")

    return "".join(repaired)


def _decode_literal_display_escapes(text: str) -> str:
    def _replace_escape(match: re.Match[str]) -> str:
        escape = match.group(0)
        if escape == r"\t":
            return " "
        return "\n"

    return _LITERAL_DISPLAY_ESCAPES_PATTERN.sub(_replace_escape, text)


def _restore_non_linebreak_control_escapes(text: str) -> str:
    restored: list[str] = []
    for index, character in enumerate(text):
        prefix = _NON_LINEBREAK_CONTROL_ESCAPE_TO_PREFIX.get(character)
        if prefix is not None and index + 1 < len(text) and text[index + 1].isalpha():
            restored.append("\\")
            restored.append(prefix)
            continue
        restored.append(character)
    return "".join(restored)


def _strip_html_like_markup(text: str) -> str:
    normalized = html.unescape(text)
    normalized = _HTML_LINE_BREAK_TAG_PATTERN.sub("\n", normalized)
    normalized = _HTML_TAG_PATTERN.sub("", normalized)
    normalized = re.sub(r"[ \t\f\v]+", " ", normalized)
    normalized = re.sub(r" *\n *", "\n", normalized)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip()


def _strip_parsed_string_placeholder_annotations(text: str) -> str:
    cleaned = _PARSED_STRING_PLACEHOLDER_ANNOTATION_PATTERN.sub("", text)
    cleaned = _PARSED_UNMATCHED_QUOTE_CONCATENATION_PREFIX_PATTERN.sub(" ", cleaned)
    cleaned = re.sub(r" {2,}", " ", cleaned)
    return cleaned.strip()


def _normalize_payload_value(value: Any) -> Any:
    if isinstance(value, str):
        return _strip_parsed_string_placeholder_annotations(
            _strip_html_like_markup(
                _restore_non_linebreak_control_escapes(
                    _decode_literal_display_escapes(value)
                )
            )
        )
    if isinstance(value, list):
        return [_normalize_payload_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _normalize_payload_value(item) for key, item in value.items()}
    return value


def _parse_section_response(response_text: str, context_label: str) -> dict[str, Any]:
    try:
        payload = json.loads(response_text)
    except json.JSONDecodeError as error:
        parse_error: json.JSONDecodeError = error
        repaired_response = _repair_invalid_json_escapes(response_text)
        if repaired_response != response_text:
            try:
                payload = json.loads(repaired_response)
            except json.JSONDecodeError as repaired_error:
                parse_error = repaired_error
                pass
            else:
                if isinstance(payload, dict):
                    normalized_payload = _normalize_payload_value(payload)
                    if isinstance(normalized_payload, dict):
                        return normalized_payload
        annotation_stripped_response = _strip_inline_quoted_list_annotations(
            repaired_response
        )
        annotation_stripped_response = _strip_code_like_inline_annotations(
            annotation_stripped_response
        )
        annotation_stripped_response = _strip_mixed_quote_concatenation_annotations(
            annotation_stripped_response
        )
        annotation_stripped_response = (
            _strip_unmatched_mixed_quote_concatenation_prefixes(
                annotation_stripped_response
            )
        )
        annotation_stripped_response = _strip_escaped_quote_concatenation_annotations(
            annotation_stripped_response
        )
        annotation_stripped_response = _strip_adjacent_escaped_string_annotations(
            annotation_stripped_response
        )
        annotation_stripped_response = _strip_double_quote_placeholder_annotations(
            annotation_stripped_response
        )
        annotation_stripped_response = _strip_concatenated_quoted_list_annotations(
            annotation_stripped_response
        )
        multiline_annotation_stripped_response = (
            _strip_multiline_quoted_list_annotations(annotation_stripped_response)
        )
        if multiline_annotation_stripped_response != repaired_response:
            try:
                payload = json.loads(multiline_annotation_stripped_response)
            except json.JSONDecodeError as multiline_error:
                parse_error = multiline_error
                pass
            else:
                if isinstance(payload, dict):
                    normalized_payload = _normalize_payload_value(payload)
                    if isinstance(normalized_payload, dict):
                        return normalized_payload
        balanced_response = _repair_mismatched_json_closers(
            multiline_annotation_stripped_response
        )
        if balanced_response != multiline_annotation_stripped_response:
            try:
                payload = json.loads(balanced_response)
            except json.JSONDecodeError as balanced_error:
                parse_error = balanced_error
                pass
            else:
                if isinstance(payload, dict):
                    normalized_payload = _normalize_payload_value(payload)
                    if isinstance(normalized_payload, dict):
                        return normalized_payload
        unmatched_prefix_stripped_response = (
            _strip_unmatched_quote_concatenation_prefixes(
                multiline_annotation_stripped_response
            )
        )
        if unmatched_prefix_stripped_response != multiline_annotation_stripped_response:
            try:
                payload = json.loads(unmatched_prefix_stripped_response)
            except json.JSONDecodeError as unmatched_prefix_error:
                parse_error = unmatched_prefix_error
                unmatched_balanced_response = _repair_mismatched_json_closers(
                    unmatched_prefix_stripped_response
                )
                if unmatched_balanced_response != unmatched_prefix_stripped_response:
                    try:
                        payload = json.loads(unmatched_balanced_response)
                    except json.JSONDecodeError as unmatched_balanced_error:
                        parse_error = unmatched_balanced_error
                        pass
                    else:
                        if isinstance(payload, dict):
                            normalized_payload = _normalize_payload_value(payload)
                            if isinstance(normalized_payload, dict):
                                return normalized_payload
            else:
                if isinstance(payload, dict):
                    normalized_payload = _normalize_payload_value(payload)
                    if isinstance(normalized_payload, dict):
                        return normalized_payload
        raise JSONResponseParseError(
            f"Failed to parse {context_label} response as JSON. "
            f"Raw response:\n{response_text}",
            response_text=response_text,
            source_error=parse_error,
        ) from error

    if not isinstance(payload, dict):
        raise RuntimeError(
            f"Failed to validate {context_label} response as a JSON object. "
            f"Raw response:\n{response_text}"
        )

    normalized_payload = _normalize_payload_value(payload)
    if not isinstance(normalized_payload, dict):
        raise RuntimeError(
            f"Failed to validate {context_label} response as a JSON object. "
            f"Raw response:\n{response_text}"
        )

    return normalized_payload


async def generate_section(
    *,
    request: StudyGuideRequest,
    blueprint: Blueprint,
    prompt_builder: Callable[[Any, Blueprint, GenerateRequest], str],
    context_label: str,
    spec: Any = None,
    max_output_tokens: int = MAX_OUTPUT_TOKENS,
) -> dict[str, Any]:
    system_prompt = build_runtime_system_prompt(request)
    user_prompt = build_runtime_section_prompt(
        request=request,
        blueprint=blueprint,
        prompt_builder=prompt_builder,
        context_label=context_label,
        spec=spec,
    )
    return await call_gemini_and_parse_json(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=TEMP_SECTION,
        parse_response=lambda response_text: _parse_section_response(
            response_text,
            context_label,
        ),
        call_model=call_gemini,
        max_output_tokens=max_output_tokens,
        context_label=context_label,
    )
