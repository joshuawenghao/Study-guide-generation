"""Unit tests for the shared Gemini wrapper — retry backoff behaviour."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.nodes.base import _is_rate_limit_error, call_gemini


class TestIsRateLimitError:
    def test_detects_429_in_message(self) -> None:
        assert _is_rate_limit_error(RuntimeError("HTTP 429 Too Many Requests"))

    def test_detects_resource_exhausted(self) -> None:
        assert _is_rate_limit_error(RuntimeError("RESOURCE_EXHAUSTED quota exceeded"))

    def test_detects_ratelimitexceeded(self) -> None:
        assert _is_rate_limit_error(RuntimeError("RateLimitExceeded for model"))

    def test_case_insensitive(self) -> None:
        assert _is_rate_limit_error(RuntimeError("resource_Exhausted"))

    def test_ignores_generic_error(self) -> None:
        assert not _is_rate_limit_error(RuntimeError("Connection refused"))

    def test_ignores_timeout_error(self) -> None:
        assert not _is_rate_limit_error(TimeoutError("timed out"))


def _good_response(text: str = '{"ok": true}') -> MagicMock:
    r = MagicMock()
    r.text = text
    return r


class TestCallGeminiExponentialBackoff:
    @pytest.mark.asyncio
    async def test_generic_error_uses_exponential_backoff(self) -> None:
        """Generic failures sleep 1 s then 2 s (2^0, 2^1) before retrying."""
        sleep_calls: list[float] = []

        async def fake_sleep(s: float) -> None:
            sleep_calls.append(s)

        generate_mock = AsyncMock(
            side_effect=[
                RuntimeError("some transient error"),
                RuntimeError("some transient error"),
                _good_response(),
            ]
        )

        with (
            patch("app.nodes.base._get_client") as mock_get_client,
            patch("app.nodes.base.asyncio.sleep", side_effect=fake_sleep),
        ):
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client
            mock_client.aio.models.generate_content = generate_mock

            result = await call_gemini(
                system_prompt="sys",
                user_prompt="user",
                temperature=0.3,
                max_retries=2,
                context_label="test",
            )

        assert result == '{"ok": true}'
        assert sleep_calls == [1.0, 2.0]

    @pytest.mark.asyncio
    async def test_rate_limit_error_uses_longer_backoff(self) -> None:
        """Rate-limit failures sleep 4 s then 16 s (min(60, 4^1), min(60, 4^2))."""
        sleep_calls: list[float] = []

        async def fake_sleep(s: float) -> None:
            sleep_calls.append(s)

        generate_mock = AsyncMock(
            side_effect=[
                RuntimeError("HTTP 429 RESOURCE_EXHAUSTED"),
                RuntimeError("HTTP 429 RESOURCE_EXHAUSTED"),
                _good_response(),
            ]
        )

        with (
            patch("app.nodes.base._get_client") as mock_get_client,
            patch("app.nodes.base.asyncio.sleep", side_effect=fake_sleep),
        ):
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client
            mock_client.aio.models.generate_content = generate_mock

            result = await call_gemini(
                system_prompt="sys",
                user_prompt="user",
                temperature=0.3,
                max_retries=2,
                context_label="test-rate-limit",
            )

        assert result == '{"ok": true}'
        assert sleep_calls == [4.0, 16.0]

    @pytest.mark.asyncio
    async def test_rate_limit_backoff_capped_at_60s(self) -> None:
        """Rate-limit backoff is capped at 60 s (4^3 = 64 → capped to 60)."""
        sleep_calls: list[float] = []

        async def fake_sleep(s: float) -> None:
            sleep_calls.append(s)

        generate_mock = AsyncMock(
            side_effect=[
                RuntimeError("429 RESOURCE_EXHAUSTED"),
                RuntimeError("429 RESOURCE_EXHAUSTED"),
                RuntimeError("429 RESOURCE_EXHAUSTED"),
                _good_response(),
            ]
        )

        with (
            patch("app.nodes.base._get_client") as mock_get_client,
            patch("app.nodes.base.asyncio.sleep", side_effect=fake_sleep),
        ):
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client
            mock_client.aio.models.generate_content = generate_mock

            result = await call_gemini(
                system_prompt="sys",
                user_prompt="user",
                temperature=0.3,
                max_retries=3,
                context_label="test-cap",
            )

        assert result == '{"ok": true}'
        assert sleep_calls == [4.0, 16.0, 60.0]

    @pytest.mark.asyncio
    async def test_no_sleep_on_final_attempt(self) -> None:
        """Sleep is not called after the final failed attempt."""
        sleep_calls: list[float] = []

        async def fake_sleep(s: float) -> None:
            sleep_calls.append(s)

        generate_mock = AsyncMock(side_effect=RuntimeError("persistent failure"))

        with (
            patch("app.nodes.base._get_client") as mock_get_client,
            patch("app.nodes.base.asyncio.sleep", side_effect=fake_sleep),
        ):
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client
            mock_client.aio.models.generate_content = generate_mock

            with pytest.raises(RuntimeError, match="failed after 3 attempts"):
                await call_gemini(
                    system_prompt="sys",
                    user_prompt="user",
                    temperature=0.3,
                    max_retries=2,
                    context_label="test-no-sleep",
                )

        assert len(sleep_calls) == 2
