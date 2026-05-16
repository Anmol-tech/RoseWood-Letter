from app.agents.base import BaseAgent
from app.schemas import AgentOutput, PipelineRequest, VisitIntent
from app.services import elevenlabs_client


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

    async def arun(
        self,
        request: PipelineRequest,
        intent: VisitIntent | None = None,
        context: dict | None = None,
    ) -> AgentOutput:
        fallback = self.run(request, intent, context)
        data = await self.complete_data(
            system=(
                "You are the Rosewood Letter Audio Script Agent. Write a distinct "
                "60 to 90 second voice-note script, conversational and warm, not a "
                "repeat of the printed letter. Return only JSON with voice and script."
            ),
            prompt=f"Intent: {intent.model_dump() if intent else {}}\nContext: {context or {}}",
            fallback={
                "voice": fallback.data["voice"],
                "script": fallback.data["script"],
            },
            max_tokens=800,
        )
        synthesis = await elevenlabs_client.synthesize(
            text=data["script"],
            intent_label=intent.label if intent else "Quiet Restoration",
            suite=request.profile.suite,
        )
        return AgentOutput(
            agent=self.name,
            title=fallback.title,
            summary=fallback.summary,
            data={
                "voice": data["voice"],
                "script": data["script"],
                "provider": "elevenlabs",
                "audio_url": synthesis["audio_url"],
                "status": synthesis["status"],
            },
        )
