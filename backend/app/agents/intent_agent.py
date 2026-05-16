from app.agents.base import BaseAgent
from app.schemas import AgentOutput, PipelineRequest, VisitIntent


class IntentAgent(BaseAgent):
    name = "Intent Agent"

    def infer(self, request: PipelineRequest) -> VisitIntent:
        notes = request.profile.booking_notes.lower()
        occasion = (request.profile.occasion or "").lower()

        if "anniversary" in notes or "first trip" in notes or "milestone" in occasion:
            return VisitIntent(
                label="Milestone",
                confidence=88,
                emotional_state="Meaningful, expectant, hoping the stay feels remembered",
                engagement_style="Warm ceremony, fewer choices, one evening centerpiece",
                narrative_frame="The day should gather toward a moment worth keeping",
                scent_profile="White flowers, warm wood, soft amber",
            )

        return VisitIntent(
            label="Quiet Restoration",
            confidence=91,
            emotional_state="Overextended, private, seeking relief from decisions",
            engagement_style="Gentle offers, no crowded recommendations, low-friction opt-in",
            narrative_frame="The day should feel like permission to be unreachable",
            scent_profile="Cedar, damp earth, morning fog",
        )

    def run(
        self,
        request: PipelineRequest,
        intent: VisitIntent | None = None,
        context: dict | None = None,
    ) -> AgentOutput:
        inferred = self.infer(request)
        return AgentOutput(
            agent=self.name,
            title=inferred.label,
            summary=inferred.narrative_frame,
            data=inferred.model_dump(),
        )
