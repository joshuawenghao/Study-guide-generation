"""Shared helpers for study guide section nodes."""

from __future__ import annotations

import html
import json
import re
from collections.abc import Callable
from typing import Any

from app.nodes.base import TEMP_SECTION, call_gemini
from app.prompts.system_prompt import build_system_prompt
from app.types import Blueprint, GenerateRequest

_INVALID_JSON_ESCAPE_PATTERN = re.compile(r'(?<!\\)\\(?!["\\/bfnrtu])')
_INLINE_QUOTED_LIST_ANNOTATION_PATTERN = re.compile(
    r'(?<=[A-Za-z0-9.!?])\s+\[(?:"[^"\n]+"(?:,\s*"[^"\n]+")*)\]'
)
_CODE_LIKE_INLINE_ANNOTATION_PATTERN = re.compile(
    r"\[(?=[^\]\n]*\+)(?:\s*(?:\"(?:\\.|[^\"\n])*\"|'(?:\\.|[^'\n])*'|\+)\s*)+\]"
)
_CONCATENATED_QUOTED_LIST_ANNOTATION_PATTERN = re.compile(
    r'\[\s*"\s*(?:\+\s*"(?:\\.|[^"\n])*"\s*)+\+\s*"\s*\]'
)
_STANDALONE_QUOTED_LINE_PATTERN = re.compile(r'^\s*"[^"\n]*",?\s*$')
_HTML_LINE_BREAK_TAG_PATTERN = re.compile(r"(?is)<\s*(?:br|/p|/div|/li|/tr)\s*/?\s*>")
_HTML_TAG_PATTERN = re.compile(r"(?is)</?[a-z][^>]*>")
_CONTROL_ESCAPE_TO_PREFIX = {
    "\b": "b",
    "\f": "f",
    "\n": "n",
    "\r": "r",
    "\t": "t",
}


def _repair_invalid_json_escapes(response_text: str) -> str:
    return _INVALID_JSON_ESCAPE_PATTERN.sub(r"\\\\", response_text)


def _strip_inline_quoted_list_annotations(response_text: str) -> str:
    return _INLINE_QUOTED_LIST_ANNOTATION_PATTERN.sub("", response_text)


def _strip_code_like_inline_annotations(response_text: str) -> str:
    return _CODE_LIKE_INLINE_ANNOTATION_PATTERN.sub("", response_text)


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


def _restore_control_escapes(text: str) -> str:
    restored: list[str] = []
    for index, character in enumerate(text):
        prefix = _CONTROL_ESCAPE_TO_PREFIX.get(character)
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


def _normalize_payload_value(value: Any) -> Any:
    if isinstance(value, str):
        return _strip_html_like_markup(_restore_control_escapes(value))
    if isinstance(value, list):
        return [_normalize_payload_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _normalize_payload_value(item) for key, item in value.items()}
    return value


def _parse_section_response(response_text: str, context_label: str) -> dict[str, Any]:
    try:
        payload = json.loads(response_text)
    except json.JSONDecodeError as error:
        repaired_response = _repair_invalid_json_escapes(response_text)
        if repaired_response != response_text:
            try:
                payload = json.loads(repaired_response)
            except json.JSONDecodeError:
                pass
            else:
                if isinstance(payload, dict):
                    return payload
        annotation_stripped_response = _strip_inline_quoted_list_annotations(
            repaired_response
        )
        annotation_stripped_response = _strip_code_like_inline_annotations(
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
            except json.JSONDecodeError:
                pass
            else:
                if isinstance(payload, dict):
                    normalized_payload = _normalize_payload_value(payload)
                    if isinstance(normalized_payload, dict):
                        return normalized_payload
        raise RuntimeError(
            f"Failed to parse {context_label} response as JSON. "
            f"Raw response:\n{response_text}"
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
    request: GenerateRequest,
    blueprint: Blueprint,
    prompt_builder: Callable[[Any, Blueprint, GenerateRequest], str],
    context_label: str,
    spec: Any = None,
) -> dict[str, Any]:
    system_prompt = build_system_prompt(request)
    user_prompt = prompt_builder(spec, blueprint, request)
    response_text = await call_gemini(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=TEMP_SECTION,
        context_label=context_label,
    )
    return _parse_section_response(response_text, context_label)
