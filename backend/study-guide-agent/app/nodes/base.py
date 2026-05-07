"""Shared Gemini utilities migrated from the legacy backend prototype."""

from __future__ import annotations

import asyncio
import logging
import os

from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

TEMP_BLUEPRINT = 0.3
TEMP_SECTION = 0.7
TEMP_ANSWER_KEY = 0.3
TEMP_RETRY = 0.3

MAX_OUTPUT_TOKENS = 2048
MODEL_NAME = "gemini-2.0-flash"


def _get_client() -> genai.Client:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GOOGLE_API_KEY is not set. Expected it in the shell environment or "
            "in backend/study-guide-agent/.env."
        )
    return genai.Client(api_key=api_key)


async def call_gemini(
    system_prompt: str,
    user_prompt: str,
    temperature: float,
    max_retries: int = 2,
    context_label: str = "unknown",
) -> str:
    """Call Gemini with the JSON response mode used by section generators."""

    config = types.GenerateContentConfig.model_validate(
        {
            "system_instruction": system_prompt,
            "temperature": temperature,
            "max_output_tokens": MAX_OUTPUT_TOKENS,
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
