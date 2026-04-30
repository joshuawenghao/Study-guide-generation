"""
backend/nodes/base.py

Shared utilities for all ADK 2.0 dynamic workflow nodes.

In ADK 2.0 dynamic workflows, nodes are plain @node-decorated functions.
There is no 'agent' object passed around — the Gemini client is initialised
once at module level from the GOOGLE_API_KEY environment variable and called
directly by call_gemini().

Usage in any section node:
    from nodes.base import call_gemini, TEMP_SECTION
    result_text = await call_gemini(system_prompt, user_prompt, TEMP_SECTION,
                                    context_label="intro")
"""

from __future__ import annotations

import asyncio
import logging
import os

from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

# ── Temperature presets ────────────────────────────────────────────────────────
# Match values in adk_config.yaml. Reference by name in node files,
# never use magic numbers.

TEMP_BLUEPRINT = 0.3
TEMP_SECTION = 0.7
TEMP_ANSWER_KEY = 0.3
TEMP_RETRY = 0.3     # retries always use lower temperature for conservative output

# ── Token limits ───────────────────────────────────────────────────────────────

MAX_OUTPUT_TOKENS = 2048

# ── Model name ─────────────────────────────────────────────────────────────────

MODEL_NAME = "gemini-2.0-flash"

# ── Gemini client — initialised once at module level ──────────────────────────
# All nodes share this client. It reads GOOGLE_API_KEY from the environment,
# which is set in backend/study_guide_agent/.env for local dev and via
# Cloud Run environment variables in production.

_client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])


# ── Core Gemini call wrapper ───────────────────────────────────────────────────

async def call_gemini(
    system_prompt: str,
    user_prompt: str,
    temperature: float,
    max_retries: int = 2,
    context_label: str = "unknown",   # section name or node name, for error messages
) -> str:
    """
    Calls Gemini 2.0 Flash with JSON output mode.

    Always sets response_mime_type to application/json — all generation calls
    in this project return structured JSON. Callers are responsible for parsing
    and validating the returned string.

    Args:
        system_prompt:  The system instruction string.
        user_prompt:    The user turn content string.
        temperature:    Sampling temperature. Use constants from this module.
        max_retries:    Number of retry attempts after the first failure.
        context_label:  Section or node name included in error messages.

    Returns:
        Raw response text (a JSON string).

    Raises:
        RuntimeError: After all retry attempts are exhausted.
    """
    config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        temperature=temperature,
        max_output_tokens=MAX_OUTPUT_TOKENS,
        response_mime_type="application/json",
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

            response = await _client.aio.models.generate_content(
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
