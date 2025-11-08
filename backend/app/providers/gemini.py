"""Lightweight Gemini chat wrapper."""

from __future__ import annotations

import asyncio
from typing import List

import google.generativeai as genai
from langchain.schema import AIMessage, BaseMessage, HumanMessage, SystemMessage

from app.providers.base import ProviderConfigurationError


class GeminiChatModel:
    """Minimal async wrapper compatible with LangChain prompt outputs."""

    def __init__(self, *, model: str, api_key: str, temperature: float = 0.1) -> None:
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)
        self.temperature = temperature

    async def ainvoke(self, messages: List[BaseMessage]) -> str:
        payload = self._convert_messages(messages)
        try:
            response = await asyncio.to_thread(
                self.model.generate_content,
                payload,
                generation_config={"temperature": self.temperature},
            )
        except Exception as exc:
            raise ProviderConfigurationError(f"Gemini request failed: {exc}") from exc

        try:
            return response.candidates[0].content.parts[0].text  # type: ignore[attr-defined,index]
        except Exception as exc:  # pragma: no cover - defensive guard
            raise ProviderConfigurationError("Gemini returned no content.") from exc

    def _convert_messages(self, messages: List[BaseMessage]):
        conversation = []
        system_buffer: list[str] = []

        for message in messages:
            if isinstance(message, SystemMessage):
                system_buffer.append(message.content)
                continue

            content = message.content
            if system_buffer:
                content = "\n\n".join(system_buffer + [content])
                system_buffer.clear()

            if isinstance(message, HumanMessage):
                conversation.append({"role": "user", "parts": [content]})
            elif isinstance(message, AIMessage):
                conversation.append({"role": "model", "parts": [content]})
            else:
                conversation.append({"role": "user", "parts": [content]})

        if system_buffer:
            conversation.append({"role": "user", "parts": ["\n\n".join(system_buffer)]})

        return conversation




