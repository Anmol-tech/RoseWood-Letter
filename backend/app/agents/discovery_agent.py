from app.agents.base import BaseAgent
from app.schemas import AgentOutput, PipelineRequest, VisitIntent


class DiscoveryAgent(BaseAgent):
    name = "Discovery Agent"

    def run(
        self,
        request: PipelineRequest,
        intent: VisitIntent | None = None,
        context: dict | None = None,
    ) -> AgentOutput:
        return AgentOutput(
            agent=self.name,
            title="Mara Kito's studio",
            summary="A single local recommendation that feels whispered, not listed.",
            data={
                "recommendation": "Mara Kito opens her ceramics studio at two.",
                "reason": "She fires with clay from the same ridge visible from the suite.",
                "guest_fit": intent.label if intent else "Unknown",
            },
        )
