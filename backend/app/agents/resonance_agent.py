from app.agents.base import BaseAgent
from app.schemas import AgentOutput, PipelineRequest, VisitIntent


class ResonanceAgent(BaseAgent):
    name = "Temporal Resonance Layer"

    def run(
        self,
        request: PipelineRequest,
        intent: VisitIntent | None = None,
        context: dict | None = None,
    ) -> AgentOutput:
        return AgentOutput(
            agent=self.name,
            title="The fig orchard",
            summary="One true coincidence across land, date, property, and guest context.",
            data={
                "detail": "The fig orchard beyond the lower lawn is just beginning this week.",
                "verification_needed": True,
                "source_targets": ["property_records", "agricultural_calendar", "guest_profile"],
            },
        )
