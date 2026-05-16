from abc import ABC, abstractmethod
from typing import Any

from app.schemas import AgentOutput, PipelineRequest, VisitIntent


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
