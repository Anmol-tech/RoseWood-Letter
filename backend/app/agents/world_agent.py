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
        label = intent.label if intent else "Quiet Restoration"
        location = request.profile.property_location

        if label == "Milestone":
            return AgentOutput(
                agent=self.name,
                title=f"{location} evening light",
                summary="Weather, dining, and property details shaped around a private evening centerpiece.",
                data={
                    "weather_frame": f"Frame today's weather and light around {location}, with one detail that changes the guest's day.",
                    "property_detail": f"Surface one property-specific quiet space or service path at {location}.",
                    "chef_note": f"Offer one chef or bar note that belongs to {location}.",
                    "local_conditions": [
                        "Terrace sunset window begins at 19:42",
                        "Library garden can be held privately",
                        "Two-person tasting available off menu",
                    ],
                },
            )

        if label == "Celebration Discovery":
            return AgentOutput(
                agent=self.name,
                title=f"{location} local opening",
                summary="Weather, food, and cultural details filtered for a guest who wants discovery.",
                data={
                    "weather_frame": f"Describe the morning conditions immediately around {location}.",
                    "property_detail": f"Name one energizing property touchpoint at {location}.",
                    "chef_note": f"Name one celebratory culinary detail from {location}.",
                    "local_conditions": [
                        "Design market opens at ten",
                        "Vintage drive route clear after lunch",
                        "Chef counter has a hidden birthday pour",
                    ],
                },
            )

        if label == "Conference Event":
            return AgentOutput(
                agent=self.name,
                title=f"{location} event day conditions",
                summary="Weather, property, and service details shaped around a guest attending a scheduled event.",
                data={
                    "weather_frame": f"The morning around {location} leaves enough margin for a composed arrival.",
                    "property_detail": f"{location} can keep a quiet workspace and transfer buffer ready.",
                    "chef_note": "A light breakfast can arrive before the public part of the day begins.",
                    "local_conditions": [
                        "Morning transfer buffer held",
                        "Quiet workspace available before departure",
                        "Light post-event supper can be arranged",
                    ],
                },
            )

        return AgentOutput(
            agent=self.name,
            title=f"{location} morning conditions",
            summary="Weather, trail, and property details filtered for the guest's intent.",
            data={
                "weather_frame": f"Frame the morning weather around {location} as an experience, not a forecast.",
                "property_detail": f"Use one quiet property detail from {location}.",
                "chef_note": f"Offer one low-friction food or beverage option from {location}.",
                "local_conditions": [
                    "East trail cool until eleven",
                    "Garden path dry enough for soft shoes",
                    "Breakfast service can be contactless",
                ],
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
                "You are the Rosewood Letter World Agent. Filter weather, property, "
                "food, and local facts through the visit intent. Return only JSON "
                "with weather_frame, property_detail, chef_note, local_conditions. "
                "Use property_location as the property and neighborhood anchor."
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
            summary="World details filtered through the visit intent.",
            data=data,
        )
