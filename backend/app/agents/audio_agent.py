from app.agents.base import BaseAgent
from app.schemas import AgentOutput, PipelineRequest, VisitIntent


class AudioAgent(BaseAgent):
    name = "Audio Agent"

    def run(
        self,
        request: PipelineRequest,
        intent: VisitIntent | None = None,
        context: dict | None = None,
    ) -> AgentOutput:
        return AgentOutput(
            agent=self.name,
            title="Personal note script",
            summary="A spoken note distinct from the printed letter.",
            data={
                "voice": "soft and slow" if intent and intent.label == "Quiet Restoration" else "warm and ceremonial",
                "script": "There is no need to make much of the morning. The fog moved in low, and the day can begin without ceremony.",
            },
        )
