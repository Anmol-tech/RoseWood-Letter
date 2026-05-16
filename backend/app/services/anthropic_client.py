import json
import os
from typing import Any


class AnthropicClient:
    def __init__(self) -> None:
        self.api_key = os.getenv("ANTHROPIC_API_KEY", "")
        self.model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5")
        self.base_url = os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com")
        self.version = os.getenv("ANTHROPIC_VERSION", "2023-06-01")
        self.enabled = bool(self.api_key)

    async def complete_json(
        self,
        *,
        system: str,
        prompt: str,
        fallback: dict[str, Any],
        max_tokens: int = 900,
    ) -> dict[str, Any]:
        if not self.enabled:
            return fallback

        try:
            import httpx
        except ImportError:
            return fallback

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    f"{self.base_url}/v1/messages",
                    headers={
                        "x-api-key": self.api_key,
                        "anthropic-version": self.version,
                        "content-type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "max_tokens": max_tokens,
                        "system": system,
                        "messages": [{"role": "user", "content": prompt}],
                    },
                )
                response.raise_for_status()
        except httpx.HTTPError:
            return fallback

        data = response.json()
        text = "".join(
            block.get("text", "")
            for block in data.get("content", [])
            if block.get("type") == "text"
        ).strip()

        if text.startswith("```"):
            text = text.strip("`")
            if text.startswith("json"):
                text = text[4:].strip()

        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            return fallback

        if not isinstance(parsed, dict):
            return fallback

        return {**fallback, **parsed}


anthropic_client = AnthropicClient()
