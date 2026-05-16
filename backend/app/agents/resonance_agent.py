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
        label = intent.label if intent else "Quiet Restoration"
        location = request.profile.property_location

        if label == "Milestone":
            return AgentOutput(
                agent=self.name,
                title=f"{location} date resonance",
                summary="One true coincidence across the couple's timing and the property's evening ritual.",
                data={
                    "detail": f"Find one true or verification-needed date, land, architecture, or cultural resonance tied to {location}.",
                    "verification_needed": True,
                    "source_targets": ["property_records", "sunset_table", "booking_notes"],
                },
            )

        if label == "Celebration Discovery":
            return AgentOutput(
                agent=self.name,
                title=f"{location} local resonance",
                summary="One true coincidence between the local design scene and the guest's celebration.",
                data={
                    "detail": f"Find one quietly uncanny local coincidence connected to {location} and the guest's celebration.",
                    "verification_needed": True,
                    "source_targets": ["market_archive", "chef_counter_notes", "local_calendar"],
                },
            )

        return AgentOutput(
            agent=self.name,
            title=f"{location} quiet resonance",
            summary="One true coincidence across land, date, property, and guest context.",
            data={
                "detail": f"Find one quiet resonance between today's date, the land, and {location}.",
                "verification_needed": True,
                "source_targets": ["property_records", "agricultural_calendar", "guest_profile"],
            },
        )

    async def arun(
        self,
        request: PipelineRequest,
        intent: VisitIntent | None = None,
        context: dict | None = None,
    ) -> AgentOutput:
        fallback = self.run(request, intent, context)
        data = await self.complete_data(
            system=(
                "You are the Rosewood Letter Temporal Resonance Layer. Surface one "
                "quietly uncanny but plausible connection across date, land, property, "
                "and guest context. Do not fabricate claims as verified. Return only "
                "JSON with detail, verification_needed, source_targets. Use property_location "
                "as the property/local history anchor."
            ),
            prompt=(
                f"Property location: {request.profile.property_location}\n"
                f"Intent: {intent.model_dump() if intent else {}}\n"
                f"Guest: {request.profile.model_dump()}"
            ),
            fallback=fallback.data,
        )
        return AgentOutput(
            agent=self.name,
            title=fallback.title,
            summary=fallback.summary,
            data=data,
        )
