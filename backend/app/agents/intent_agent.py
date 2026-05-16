from app.agents.base import BaseAgent
from app.schemas import AgentOutput, PipelineRequest, VisitIntent
from app.services import anthropic_client


class IntentAgent(BaseAgent):
    name = "Intent Agent"

    def infer(self, request: PipelineRequest) -> VisitIntent:
        notes = request.profile.booking_notes.lower()
        occasion = (request.profile.occasion or "").lower()
        persona = request.profile.persona.segment.lower()

        if "anniversary" in notes or "first trip" in notes or "milestone" in occasion:
            return VisitIntent(
                label="Milestone",
                confidence=88,
                emotional_state="Meaningful, expectant, hoping the stay feels remembered",
                engagement_style="Warm ceremony, fewer choices, one evening centerpiece",
                narrative_frame="The day should gather toward a moment worth keeping",
                scent_profile="White flowers, warm wood, soft amber",
            )

        if (
            "conference" in notes
            or "summit" in notes
            or "keynote" in notes
            or "panel" in notes
            or "expo" in notes
            or "congress" in notes
            or "board meeting" in notes
            or "business meeting" in notes
            or "client meeting" in notes
            or "public engagement" in notes
            or "official visit" in notes
            or "conference" in occasion
            or "summit" in occasion
            or "event" in occasion
            or "official visit" in occasion
            or "executive" in persona
            or "delegate" in persona
            or "speaker" in persona
        ):
            return VisitIntent(
                label="Conference Event",
                confidence=87,
                emotional_state="Purposeful, time-bound, wanting the hotel to reduce friction around a public commitment",
                engagement_style="Precise support, recovery windows, smart local context, no excess",
                narrative_frame="The day should help the guest arrive prepared and quietly restored afterward",
                scent_profile="Green tea, vetiver, clean paper, rain-washed stone",
            )

        if (
            "birthday" in notes
            or "celebration" in occasion
            or "hidden local" in notes
            or "explorer" in persona
        ):
            return VisitIntent(
                label="Celebration Discovery",
                confidence=86,
                emotional_state="Open, energized, hoping the hotel unlocks the place",
                engagement_style="Edited surprises, confident local cues, one social invitation",
                narrative_frame="The day should feel like the property quietly opened a door",
                scent_profile="Neroli, fig leaf, chilled citrus, polished wood",
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

    async def arun(
        self,
        request: PipelineRequest,
        intent: VisitIntent | None = None,
        context: dict | None = None,
    ) -> AgentOutput:
        fallback = self.infer(request).model_dump()
        data = await anthropic_client.complete_json(
            system=(
                "You are the Rosewood Letter Intent Agent. Infer why a luxury hotel "
                "guest is here. Return only JSON matching: label, confidence, "
                "emotional_state, engagement_style, narrative_frame, scent_profile."
            ),
            prompt=(
                f"Guest profile: {request.profile.model_dump()}\n"
                f"Ambient signals: {[signal.model_dump() for signal in request.ambient_signals]}\n"
                "Classify as Quiet Restoration, Milestone, Celebration Discovery, or Conference Event unless "
                "the data clearly demands another concise label."
            ),
            fallback=fallback,
            max_tokens=700,
        )
        inferred = VisitIntent(**data)
        return AgentOutput(
            agent=self.name,
            title=inferred.label,
            summary=inferred.narrative_frame,
            data=inferred.model_dump(),
        )
