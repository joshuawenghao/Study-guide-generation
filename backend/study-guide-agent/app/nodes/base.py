"""Shared Gemini utilities migrated from the legacy backend prototype."""

from __future__ import annotations

import asyncio
import json
import logging
import os
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import TypeVar

from dotenv import load_dotenv
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Local backend runs keep secrets in backend/study-guide-agent/.env.
load_dotenv(PROJECT_ROOT / ".env")

_client: genai.Client | None = None

TEMP_BLUEPRINT = 0.3
TEMP_SECTION = 0.7
TEMP_ANSWER_KEY = 0.3
TEMP_RETRY = 0.3

MAX_OUTPUT_TOKENS = 2048
MAX_BLUEPRINT_OUTPUT_TOKENS = 4096
MAX_STRATEGY_LIST_OUTPUT_TOKENS = 4096
MAX_ANSWER_KEY_OUTPUT_TOKENS = 8192
MAX_DYNAMIC_OUTPUT_TOKENS = 16384
DEFAULT_GEMINI_MODEL = "gemini-3.5-flash"
MODEL_NAME = os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL)

ParsedPayload = TypeVar("ParsedPayload")


class JSONResponseParseError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        response_text: str,
        source_error: Exception | None = None,
    ) -> None:
        super().__init__(message)
        self.response_text = response_text
        self.source_error = source_error


def _next_output_budget(current: int, ceiling: int) -> int | None:
    if current >= ceiling:
        return None
    return min(current * 2, ceiling)


def _is_likely_truncated_json(error: JSONResponseParseError) -> bool:
    stripped_response = error.response_text.rstrip()
    if not stripped_response:
        return False

    decode_error = error.source_error
    if isinstance(decode_error, json.JSONDecodeError):
        if decode_error.pos >= max(len(error.response_text) - 160, 0):
            return True
        if decode_error.msg in {
            "Unterminated string starting at",
            "Expecting ',' delimiter",
            "Expecting value",
        }:
            return True

    return stripped_response[-1] not in {"}", "]"}


def _get_client() -> genai.Client:
    global _client
    if _client is not None:
        return _client

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GOOGLE_API_KEY is not set. Expected it in the shell environment or "
            "in backend/study-guide-agent/.env."
        )
    _client = genai.Client(api_key=api_key)
    return _client


async def call_gemini(
    system_prompt: str,
    user_prompt: str,
    temperature: float,
    max_output_tokens: int = MAX_OUTPUT_TOKENS,
    max_retries: int = 2,
    context_label: str = "unknown",
) -> str:
    """Call Gemini with the JSON response mode used by section generators."""

    config = types.GenerateContentConfig.model_validate(
        {
            "system_instruction": system_prompt,
            "temperature": temperature,
            "max_output_tokens": max_output_tokens,
            "response_mime_type": "application/json",
        }
    )

    last_error: Exception | None = None
    total_attempts = max_retries + 1

    for attempt in range(1, total_attempts + 1):
        try:
            logger.debug(
                "[%s] Gemini call attempt %d/%d | temp=%.1f | prompt_chars=%d",
                context_label,
                attempt,
                total_attempts,
                temperature,
                len(user_prompt),
            )

            response = await _get_client().aio.models.generate_content(
                model=MODEL_NAME,
                contents=user_prompt,
                config=config,
            )

            response_text = getattr(response, "text", None)
            if isinstance(response_text, str) and response_text.strip():
                logger.debug(
                    "[%s] Gemini response received | chars=%d",
                    context_label,
                    len(response_text),
                )
                return response_text

            raise RuntimeError(
                f"[{context_label}] Gemini returned an empty response on attempt {attempt}"
            )
        except Exception as error:
            last_error = error
            logger.warning(
                "[%s] Gemini call failed on attempt %d/%d: %s",
                context_label,
                attempt,
                total_attempts,
                str(error),
            )
            if attempt < total_attempts:
                await asyncio.sleep(1.0)

    raise RuntimeError(
        f"[{context_label}] Gemini call failed after {total_attempts} attempts. "
        f"Last error: {last_error}"
    ) from last_error


async def call_gemini_and_parse_json(
    *,
    system_prompt: str,
    user_prompt: str,
    temperature: float,
    parse_response: Callable[[str], ParsedPayload],
    call_model: Callable[..., Awaitable[str]] | None = None,
    max_output_tokens: int = MAX_OUTPUT_TOKENS,
    max_output_tokens_ceiling: int = MAX_DYNAMIC_OUTPUT_TOKENS,
    max_retries: int = 2,
    context_label: str = "unknown",
) -> ParsedPayload:
    current_output_budget = max_output_tokens
    model_caller = call_model or call_gemini

    while True:
        response_text = await model_caller(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            max_output_tokens=current_output_budget,
            max_retries=max_retries,
            context_label=context_label,
        )

        try:
            return parse_response(response_text)
        except JSONResponseParseError as error:
            next_output_budget = _next_output_budget(
                current_output_budget,
                max_output_tokens_ceiling,
            )
            if next_output_budget is None or not _is_likely_truncated_json(error):
                raise

            logger.warning(
                "[%s] Response looks truncated at %d tokens; retrying with %d",
                context_label,
                current_output_budget,
                next_output_budget,
            )
            current_output_budget = next_output_budget
