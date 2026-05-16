from app.agents.base import BaseAgent
from app.schemas import AgentOutput, PipelineRequest, VisitIntent


class CompositorAgent(BaseAgent):
    name = "Compositor Agent"

    def run(
        self,
        request: PipelineRequest,
        intent: VisitIntent | None = None,
        context: dict | None = None,
    ) -> AgentOutput:
        return AgentOutput(
            agent=self.name,
            title="Print artifact prepared",
            summary="Letter content is ready for LaTeX composition and scented paper handoff.",
            data={
                "format": "latex-ready",
                "paper_scent": intent.scent_profile if intent else "unselected",
                "delivery_window": "06:00",
            },
        )
