from abc import ABC, abstractmethod
import asyncio
from typing import Any

from app.schemas import AgentOutput, PipelineRequest, VisitIntent
from app.services import anthropic_client


class BaseAgent(ABC):
    name: str

    @abstractmethod
    def run(
        self,
        request: PipelineRequest,
        intent: VisitIntent | None = None,
        context: dict[str, Any] | None = None,
    ) -> AgentOutput:
        """Run one agent and return a structured output."""

    async def arun(
        self,
        request: PipelineRequest,
        intent: VisitIntent | None = None,
        context: dict[str, Any] | None = None,
    ) -> AgentOutput:
        return await asyncio.to_thread(self.run, request, intent, context)

    async def complete_data(
        self,
        *,
        system: str,
        prompt: str,
        fallback: dict[str, Any],
        max_tokens: int = 900,
    ) -> dict[str, Any]:
        style_guard = " Never use em dashes. Prefer commas, periods, or simple hyphens."
        return await anthropic_client.complete_json(
            system=f"{system}{style_guard}",
            prompt=prompt,
            fallback=fallback,
            max_tokens=max_tokens,
        )
