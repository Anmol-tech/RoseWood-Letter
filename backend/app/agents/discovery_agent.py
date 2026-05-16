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

        if label == "Milestone":
            return AgentOutput(
                agent=self.name,
                title="The private vineyard room",
                summary="A single local recommendation that turns the evening into a kept moment.",
                data={
                    "recommendation": "The small vineyard above the ridge can open its library room for two at dusk.",
                    "reason": "They still have a bottle from the year the couple first met.",
                    "guest_fit": label,
                },
            )

        if label == "Celebration Discovery":
            return AgentOutput(
                agent=self.name,
                title="The back-room design market",
                summary="A lively local discovery with enough specificity to feel unlocked.",
                data={
                    "recommendation": "A textile dealer behind the design market is opening her private archive at noon.",
                    "reason": "She keeps hand-dyed table linens from the same atelier dressing the chef's counter tonight.",
                    "guest_fit": label,
                },
            )

        return AgentOutput(
            agent=self.name,
            title="Mara Kito's studio",
            summary="A single local recommendation that feels whispered, not listed.",
            data={
                "recommendation": "Mara Kito opens her ceramics studio at two.",
                "reason": "She fires with clay from the same ridge visible from the suite.",
                "guest_fit": intent.label if intent else "Unknown",
            },
        )
