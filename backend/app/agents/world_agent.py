from app.agents.base import BaseAgent
from app.schemas import AgentOutput, PipelineRequest, VisitIntent


class WorldAgent(BaseAgent):
    name = "World Agent"

    def run(
        self,
        request: PipelineRequest,
        intent: VisitIntent | None = None,
        context: dict | None = None,
    ) -> AgentOutput:
        return AgentOutput(
            agent=self.name,
            title="Fog before eleven",
            summary="Weather, trail, and property details filtered for the guest's intent.",
            data={
                "weather_frame": "The fog came in overnight and will keep the east trail cool.",
                "property_detail": "The garden path is dry enough for soft shoes.",
                "chef_note": "A quiet breakfast can be sent without conversation.",
            },
        )
