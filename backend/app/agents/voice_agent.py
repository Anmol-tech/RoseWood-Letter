from app.agents.base import BaseAgent
from app.schemas import AgentOutput, PipelineRequest, VisitIntent


class VoiceAgent(BaseAgent):
    name = "Voice Agent"

    def run(
        self,
        request: PipelineRequest,
        intent: VisitIntent | None = None,
        context: dict | None = None,
    ) -> AgentOutput:
        tone = "quiet, unhurried, slightly poetic" if intent and intent.label == "Quiet Restoration" else "warm, ceremonial, restrained"
        return AgentOutput(
            agent=self.name,
            title="Editorial tone selected",
            summary=f"Letter voice is {tone}.",
            data={
                "tone": tone,
                "rules": ["short sentences", "no instructions", "offers that step back"],
            },
        )
