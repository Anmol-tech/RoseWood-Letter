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
        label = intent.label if intent else "Quiet Restoration"
        voice = "soft and slow"
        script = "There is no need to make much of the morning. The fog moved in low, and the day can begin without ceremony."

        if label == "Milestone":
            voice = "warm and ceremonial"
            script = "Today does not need to announce itself loudly. It only needs to gather well, and we have kept the evening clear for that."
        elif label == "Celebration Discovery":
            voice = "bright and warm"
            script = "There is a small door open in town today that most visitors will miss. We thought this was the right morning to point you toward it."

        return AgentOutput(
            agent=self.name,
            title="Personal note script",
            summary="A spoken note distinct from the printed letter.",
            data={
                "voice": voice,
                "script": script,
                "provider": "elevenlabs",
                "audio_url": None,
                "status": "script_ready",
            },
        )
