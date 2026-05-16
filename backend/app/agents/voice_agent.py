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
        label = intent.label if intent else "Quiet Restoration"
        tone = "quiet, unhurried, slightly poetic"
        rules = ["short sentences", "no instructions", "offers that step back"]

        if label == "Milestone":
            tone = "warm, ceremonial, restrained"
            rules = ["acknowledge significance", "avoid sentimentality", "build toward evening"]
        elif label == "Celebration Discovery":
            tone = "bright, elegant, conspiratorial"
            rules = ["one vivid invitation", "confident local specificity", "edited surprise"]

        return AgentOutput(
            agent=self.name,
            title="Editorial tone selected",
            summary=f"Letter voice is {tone}.",
            data={
                "tone": tone,
                "rules": rules,
                "forbidden_phrases": [
                    "we hope you enjoy your stay",
                    "do not miss",
                    "recommended for you",
                ],
            },
        )
