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

        if label == "Milestone":
            return AgentOutput(
                agent=self.name,
                title="The terrace date",
                summary="One true coincidence across the couple's timing and the property's evening ritual.",
                data={
                    "detail": "The west terrace was dedicated on this date in 1998; tonight it catches the last light just as dinner begins.",
                    "verification_needed": True,
                    "source_targets": ["property_records", "sunset_table", "booking_notes"],
                },
            )

        if label == "Celebration Discovery":
            return AgentOutput(
                agent=self.name,
                title="The market anniversary",
                summary="One true coincidence between the local design scene and the guest's celebration.",
                data={
                    "detail": "The design market opens its fortieth season today, and the first stall belongs to the textile house setting tonight's chef counter.",
                    "verification_needed": True,
                    "source_targets": ["market_archive", "chef_counter_notes", "local_calendar"],
                },
            )

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
                "JSON with detail, verification_needed, source_targets."
            ),
            prompt=f"Intent: {intent.model_dump() if intent else {}}\nGuest: {request.profile.model_dump()}",
            fallback=fallback.data,
        )
        return AgentOutput(
            agent=self.name,
            title=fallback.title,
            summary=fallback.summary,
            data=data,
        )
