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

        if label == "Milestone":
            return AgentOutput(
                agent=self.name,
                title="Clear evening light",
                summary="Weather, dining, and property details shaped around a private evening centerpiece.",
                data={
                    "weather_frame": "The morning is clear and still; by evening the west terrace will hold the last light for nearly twelve minutes.",
                    "property_detail": "The library garden has been kept private after five.",
                    "chef_note": "The kitchen has a two-person tasting that can arrive without a menu.",
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
                title="A bright local opening",
                summary="Weather, food, and cultural details filtered for a guest who wants discovery.",
                data={
                    "weather_frame": "The fog will lift early, leaving the market streets bright by ten.",
                    "property_detail": "The front drive has vintage convertibles available after lunch.",
                    "chef_note": "The chef is holding back six sea urchin tartlets for the counter tonight.",
                    "local_conditions": [
                        "Design market opens at ten",
                        "Vintage drive route clear after lunch",
                        "Chef counter has a hidden birthday pour",
                    ],
                },
            )

        return AgentOutput(
            agent=self.name,
            title="Fog before eleven",
            summary="Weather, trail, and property details filtered for the guest's intent.",
            data={
                "weather_frame": "The fog came in overnight and will keep the east trail cool.",
                "property_detail": "The garden path is dry enough for soft shoes.",
                "chef_note": "A quiet breakfast can be sent without conversation.",
                "local_conditions": [
                    "East trail cool until eleven",
                    "Garden path dry enough for soft shoes",
                    "Breakfast service can be contactless",
                ],
            },
        )
