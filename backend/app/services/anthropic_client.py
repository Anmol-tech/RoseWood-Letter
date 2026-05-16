import json
import os
from collections.abc import Mapping
from typing import Any

from app.config import load_env


class AnthropicClient:
    def __init__(self) -> None:
        load_env()
        self.api_key = os.getenv("ANTHROPIC_API_KEY", "")
        self.model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5")
        self.base_url = os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com")
        self.version = os.getenv("ANTHROPIC_VERSION", "2023-06-01")
        self.enabled = bool(self.api_key)

    def status(self) -> dict[str, str | bool]:
        try:
            import httpx  # noqa: F401
            httpx_installed = True
        except ImportError:
            httpx_installed = False

        return {
            "enabled": self.enabled,
            "api_key_present": bool(self.api_key),
            "httpx_installed": httpx_installed,
            "model": self.model,
        }

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

        return self._merge_with_fallback(fallback, parsed)

    def _merge_with_fallback(
        self,
        fallback: dict[str, Any],
        parsed: Mapping[str, Any],
    ) -> dict[str, Any]:
        merged = fallback.copy()

        for key, value in parsed.items():
            if key not in fallback:
                merged[key] = value
                continue

            fallback_value = fallback[key]
            merged[key] = self._coerce_to_fallback_type(value, fallback_value)

        return merged

    def _coerce_to_fallback_type(self, value: Any, fallback_value: Any) -> Any:
        if fallback_value is None:
            return value

        if isinstance(fallback_value, str):
            return value if isinstance(value, str) else fallback_value

        if isinstance(fallback_value, bool):
            return value if isinstance(value, bool) else fallback_value

        if isinstance(fallback_value, int) and not isinstance(fallback_value, bool):
            return value if isinstance(value, int) and not isinstance(value, bool) else fallback_value

        if isinstance(fallback_value, float):
            return value if isinstance(value, int | float) and not isinstance(value, bool) else fallback_value

        if isinstance(fallback_value, list):
            return value if isinstance(value, list) else fallback_value

        if isinstance(fallback_value, dict):
            return value if isinstance(value, dict) else fallback_value

        return value if isinstance(value, type(fallback_value)) else fallback_value


anthropic_client = AnthropicClient()
