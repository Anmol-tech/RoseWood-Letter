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
        restoration = intent and intent.label == "Quiet Restoration"
        summary = (
            "Leave the first hours untouched, then offer one gentle afternoon destination."
            if restoration
            else "Build lightly through the day toward a private evening centerpiece."
        )
        return AgentOutput(
            agent=self.name,
            title="A day with room in it",
            summary=summary,
            data={
                "morning": "Unstructured, quiet, no action required.",
                "afternoon": "One optional local discovery.",
                "evening": "Low-friction in-room or private dining path.",
            },
        )
