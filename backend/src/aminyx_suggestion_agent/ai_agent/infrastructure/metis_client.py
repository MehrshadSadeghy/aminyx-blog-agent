"""HTTP client for Metis chat session API."""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator
from typing import Any, Literal

import httpx
from pydantic import BaseModel, Field

LOGGER = logging.getLogger(__name__)

MetisRole = Literal["USER", "AI"]


class MetisUserRef(BaseModel):
    id: str
    name: str | None = None


class MetisMessagePayload(BaseModel):
    content: str
    type: MetisRole = "USER"
    attachments: list[dict[str, Any]] | None = None


class MetisMessageResponse(BaseModel):
    id: str | None = None
    type: str | None = None
    role: str | None = None
    content: str = ""
    finish_reason: str | None = Field(default=None, alias="finishReason")

    def normalized_role(self) -> str:
        raw = (self.type or self.role or "AI").upper()
        return "USER" if raw == "USER" else "AI"


class MetisStreamChunk(BaseModel):
    message: MetisMessageResponse | None = None
    finish_reason: str | None = Field(default=None, alias="finishReason")


class MetisSessionResponse(BaseModel):
    id: str
    bot_id: str | None = Field(default=None, alias="botId")
    user: MetisUserRef | None = None
    messages: list[MetisMessageResponse] = Field(default_factory=list)
    headline: str | None = None


class MetisChatClient:
    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        bot_id: str,
        timeout_seconds: float = 120.0,
    ) -> None:
        self._bot_id = bot_id
        self._client = httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=httpx.Timeout(timeout_seconds),
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def create_session(
        self,
        *,
        user: MetisUserRef | None = None,
        initial_messages: list[MetisMessagePayload] | None = None,
        bot_id: str | None = None,
    ) -> MetisSessionResponse:
        payload: dict[str, Any] = {"botId": bot_id or self._bot_id}
        if user is not None:
            payload["user"] = user.model_dump(exclude_none=True)
        if initial_messages:
            payload["initialMessages"] = [
                m.model_dump(by_alias=True, exclude_none=True) for m in initial_messages
            ]
        response = await self._client.post("/api/v1/chat/session", json=payload)
        response.raise_for_status()
        return MetisSessionResponse.model_validate(response.json())

    async def get_session(self, session_id: str) -> MetisSessionResponse:
        response = await self._client.get(f"/api/v1/chat/session/{session_id}")
        response.raise_for_status()
        return MetisSessionResponse.model_validate(response.json())

    async def list_sessions(
        self,
        *,
        bot_id: str | None = None,
        user_id: str | None = None,
        page: int = 0,
        size: int = 20,
    ) -> list[MetisSessionResponse]:
        params: dict[str, Any] = {"page": page, "size": size}
        if bot_id:
            params["botId"] = bot_id
        if user_id:
            params["userId"] = user_id
        response = await self._client.get("/api/v1/chat/session", params=params)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, list):
            return [MetisSessionResponse.model_validate(item) for item in data]
        if isinstance(data, dict) and "content" in data:
            return [
                MetisSessionResponse.model_validate(item)
                for item in data["content"]
            ]
        return []

    async def delete_session(self, session_id: str) -> None:
        response = await self._client.delete(f"/api/v1/chat/session/{session_id}")
        response.raise_for_status()

    async def send_message(
        self,
        session_id: str,
        content: str,
        *,
        message_system_instruction: str | None = None,
    ) -> MetisMessageResponse:
        body: dict[str, Any] = {
            "message": MetisMessagePayload(content=content, type="USER").model_dump(
                exclude_none=True
            ),
        }
        if message_system_instruction:
            body["messageSystemInstruction"] = message_system_instruction
        response = await self._client.post(
            f"/api/v1/chat/session/{session_id}/message",
            json=body,
        )
        response.raise_for_status()
        return MetisMessageResponse.model_validate(response.json())

    async def send_message_stream(
        self,
        session_id: str,
        content: str,
        *,
        message_system_instruction: str | None = None,
    ) -> AsyncIterator[str]:
        body: dict[str, Any] = {
            "message": MetisMessagePayload(content=content, type="USER").model_dump(
                exclude_none=True
            ),
        }
        if message_system_instruction:
            body["messageSystemInstruction"] = message_system_instruction

        async with self._client.stream(
            "POST",
            f"/api/v1/chat/session/{session_id}/message/stream",
            json=body,
        ) as response:
            response.raise_for_status()
            buffer = ""
            async for text_chunk in response.aiter_text():
                buffer += text_chunk
                while True:
                    extracted, buffer = _pop_json_object(buffer)
                    if extracted is None:
                        break
                    delta = _extract_stream_delta(extracted)
                    if delta:
                        yield delta

            if buffer.strip():
                extracted, _ = _pop_json_object(buffer.strip())
                if extracted:
                    delta = _extract_stream_delta(extracted)
                    if delta:
                        yield delta


def _pop_json_object(buffer: str) -> tuple[dict[str, Any] | None, str]:
    start = buffer.find("{")
    if start < 0:
        return None, buffer
    depth = 0
    for index in range(start, len(buffer)):
        char = buffer[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                raw = buffer[start : index + 1]
                try:
                    return json.loads(raw), buffer[index + 1 :]
                except json.JSONDecodeError:
                    return None, buffer
    return None, buffer


def _extract_stream_delta(payload: dict[str, Any]) -> str:
    try:
        chunk = MetisStreamChunk.model_validate(payload)
    except Exception:
        LOGGER.debug("Unrecognized Metis stream payload: %s", payload)
        return ""
    if chunk.message and chunk.message.content:
        return chunk.message.content
    return ""


def map_metis_role_to_app(role: str) -> Literal["user", "assistant"]:
    if role.upper() == "USER":
        return "user"
    return "assistant"
