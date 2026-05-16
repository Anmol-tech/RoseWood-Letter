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
        label = intent.label if intent else "Quiet Restoration"
        location = request.profile.property_location

        if label == "Milestone":
            return AgentOutput(
                agent=self.name,
                title=f"{location} private room",
                summary="A single local recommendation that turns the evening into a kept moment.",
                data={
                    "recommendation": f"Ask the {location} concierge to hold one private local room for two at dusk.",
                    "place_name": "",
                    "reason": f"The recommendation should be selected from the neighborhood around {location}, not a generic city list.",
                    "guest_fit": label,
                },
            )

        if label == "Celebration Discovery":
            return AgentOutput(
                agent=self.name,
                title=f"{location} local opening",
                summary="A lively local discovery with enough specificity to feel unlocked.",
                data={
                    "recommendation": f"Find one hidden food, design, or craft opening within reach of {location}.",
                    "place_name": "",
                    "reason": f"It must feel hyperlocal to {location} and suitable for a celebration guest.",
                    "guest_fit": label,
                },
            )

        if label == "Conference Event":
            return AgentOutput(
                agent=self.name,
                title=f"{location} event-day opening",
                summary="A single recommendation that helps the guest prepare, recover, or make the event feel worthwhile.",
                data={
                    "recommendation": f"A quiet post-event table or short walk near {location} can be held.",
                    "place_name": "",
                    "reason": "It keeps the evening private after the public part of the day.",
                    "guest_fit": label,
                },
            )

        return AgentOutput(
            agent=self.name,
            title=f"{location} quiet discovery",
            summary="A single local recommendation that feels whispered, not listed.",
            data={
                "recommendation": f"Select one quiet local studio, garden, trail, bookshop, or maker near {location}.",
                "place_name": "",
                "reason": f"The discovery should match the guest's intent and the real geography around {location}.",
                "guest_fit": intent.label if intent else "Unknown",
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
                "You are the Rosewood Letter Discovery Agent. Find exactly one "
                "non-obvious local recommendation that fits the visit intent. "
                "Use the property_location as the geographic anchor. The recommendation "
                "must be hyperlocal to that Rosewood property and not a generic city suggestion. "
                "Return only JSON with recommendation, place_name, reason, guest_fit. "
                "place_name must be the exact real venue, trail, studio, restaurant, or landmark name."
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
            summary="One local discovery selected for this guest.",
            data=data,
        )
