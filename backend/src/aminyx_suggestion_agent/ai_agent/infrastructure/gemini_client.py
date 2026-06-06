"""Async client for Google Gemini generateContent API."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from google import genai
from google.genai import types

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class GenerationResult:
    text: str
    total_tokens: int | None = None


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
        result = await self.generate(
            prompt,
            system_instruction=None,
            max_output_tokens=None,
        )
        return result.text

    async def generate(
        self,
        prompt: str,
        *,
        system_instruction: str | None = None,
        max_output_tokens: int | None = None,
    ) -> GenerationResult:
        config_kwargs: dict = {
            "temperature": self._temperature,
            "max_output_tokens": max_output_tokens or self._max_output_tokens,
        }
        if system_instruction:
            config_kwargs["system_instruction"] = system_instruction

        response = await self._client.aio.models.generate_content(
            model=self._model,
            contents=prompt,
            config=types.GenerateContentConfig(**config_kwargs),
        )
        text = response.text
        if not text:
            raise RuntimeError("Gemini returned an empty response.")

        total_tokens = None
        usage = getattr(response, "usage_metadata", None)
        if usage is not None:
            total_tokens = getattr(usage, "total_token_count", None)

        return GenerationResult(text=text.strip(), total_tokens=total_tokens)

    async def aclose(self) -> None:
        try:
            await self._client.aio.aclose()
        except Exception:
            LOGGER.debug("Gemini client close skipped", exc_info=True)
