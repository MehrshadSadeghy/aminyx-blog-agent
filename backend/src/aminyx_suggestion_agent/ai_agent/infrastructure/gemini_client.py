"""Async client for Google Gemini generateContent API."""

from __future__ import annotations

import logging

from google import genai
from google.genai import types

LOGGER = logging.getLogger(__name__)


class GeminiClient:
    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        temperature: float = 0.7,
        max_output_tokens: int = 8192,
    ) -> None:
        self._model = model
        self._temperature = temperature
        self._max_output_tokens = max_output_tokens
        self._client = genai.Client(api_key=api_key)

    async def generate_text(self, prompt: str) -> str:
        response = await self._client.aio.models.generate_content(
            model=self._model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=self._temperature,
                max_output_tokens=self._max_output_tokens,
            ),
        )
        text = response.text
        if not text:
            raise RuntimeError("Gemini returned an empty response.")
        return text.strip()

    async def aclose(self) -> None:
        try:
            await self._client.aio.aclose()
        except Exception:
            LOGGER.debug("Gemini client close skipped", exc_info=True)
