from app.agents.base import BaseAgent
from app.schemas import AgentOutput, PipelineRequest, VisitIntent


class RhythmAgent(BaseAgent):
    name = "Rhythm Agent"

    def run(
        self,
        request: PipelineRequest,
        intent: VisitIntent | None = None,
        context: dict | None = None,
    ) -> AgentOutput:
        label = intent.label if intent else "Quiet Restoration"

        if label == "Milestone":
            summary = "Build lightly through the day toward a private evening centerpiece."
            return AgentOutput(
                agent=self.name,
                title="A day that gathers",
                summary=summary,
                data={
                    "morning": "Begin without pressure; breakfast can arrive late and warm.",
                    "afternoon": "Leave space for a short drive, then return before the light changes.",
                    "evening": "A private table, no menu, and one detail held until after dessert.",
                    "emotional_shape": summary,
                },
            )

        if label == "Celebration Discovery":
            summary = "Start bright, reveal one local door, then end at the chef's counter."
            return AgentOutput(
                agent=self.name,
                title="A day that opens",
                summary=summary,
                data={
                    "morning": "Begin with movement: market streets, coffee, and one design stop.",
                    "afternoon": "Offer a convertible route and a private studio visit.",
                    "evening": "Let the night become social, precise, and a little hidden.",
                    "emotional_shape": summary,
                },
            )

        summary = "Leave the first hours untouched, then offer one gentle afternoon destination."
        return AgentOutput(
            agent=self.name,
            title="A day with room in it",
            summary=summary,
            data={
                "morning": "Unstructured, quiet, no action required.",
                "afternoon": "One optional local discovery.",
                "evening": "Low-friction in-room or private dining path.",
                "emotional_shape": summary,
            },
        )
