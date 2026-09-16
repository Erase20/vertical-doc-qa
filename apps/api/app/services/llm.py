import json
from collections.abc import AsyncIterator

import httpx

from app.core.config import settings


class LlmNotConfigured(RuntimeError):
    pass


class OpenAICompatibleChatClient:
    def __init__(self) -> None:
        self.base_url = settings.llm_base_url.rstrip("/")
        self.api_key = settings.llm_api_key
        self.model = settings.llm_model

    async def stream(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> AsyncIterator[str]:
        if not self.api_key:
            raise LlmNotConfigured("LLM_API_KEY is not configured.")

        payload = {
            "model": self.model,
            "stream": True,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        headers = {"Authorization": f"Bearer {self.api_key}"}

        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=20.0)) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    data = line.removeprefix("data: ")
                    if data == "[DONE]":
                        break
                    parsed = json.loads(data)
                    delta = parsed["choices"][0].get("delta", {}).get("content")
                    if delta:
                        yield delta
